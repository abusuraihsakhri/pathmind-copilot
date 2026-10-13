"""Regression tests for integrity, validation, API access and clinical rule boundaries."""
import csv
import os

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from agents.api import app
from agents.base import AuditLogger, AuditTrail
from agents.models import SystemTaskPayload
from cli import main as operations_main
from pathmind.agents import ImmunohistochemistryTriagerAgent, SlideQCAgent
from pathmind.models import SlideArtifact, SlideQCStatus, SynopticReportDraft


def test_hmac_verifies_each_signed_field():
    trail = AuditTrail(secret_key="test-only-signing-key")
    trail.log("worker", "tier", "CREATED", {"status": "OK"})
    assert trail.verify_integrity()

    trail.logs[0]["event_type"] = "ALTERED"
    assert trail.verify_integrity() is False


def test_hmac_rejects_forged_chain_and_missing_fields():
    trail = AuditTrail(secret_key="test-only-signing-key")
    trail.log("worker", "tier", "CREATED", {"status": "OK"})
    trail.log("worker", "tier", "UPDATED", {"status": "OK"})
    trail.logs[0]["current_hash"] = "0" * 64
    trail.logs[1]["prev_hash"] = "0" * 64
    assert trail.verify_integrity() is False

    trail.logs[0].pop("payload_hash")
    assert trail.verify_integrity() is False


def test_audit_readers_cannot_modify_ledger():
    trail = AuditTrail(secret_key="test-only-signing-key")
    trail.log("worker", "tier", "CREATED", {"status": "OK"})
    snapshot = trail.get_trail()
    snapshot[0]["event_type"] = "FORGED"
    snapshot.clear()
    assert trail.verify_integrity()
    assert len(trail.logs) == 1


@pytest.mark.parametrize("invalid", [float("nan"), float("inf"), float("-inf")])
def test_nonfinite_metrics_are_rejected(invalid):
    with pytest.raises(ValidationError):
        SystemTaskPayload(task_id="T", target_identifier="KEY", primary_metric=invalid)


def test_ledger_endpoint_requires_dedicated_token(monkeypatch):
    client = TestClient(app)
    monkeypatch.delenv("AUDIT_READ_TOKEN", raising=False)
    assert client.get("/api/audit/logs").status_code == 503
    monkeypatch.setenv("AUDIT_READ_TOKEN", "test-read-token")
    assert client.get("/api/audit/logs").status_code == 403
    assert client.get("/api/audit/logs", headers={"X-Audit-Token": "incorrect"}).status_code == 403
    assert client.get("/api/audit/logs", headers={"X-Audit-Token": "test-read-token"}).status_code == 200


def test_browser_console_served_locally():
    response = TestClient(app).get("/")
    assert response.status_code == 200
    assert "Pathmind Copilot" in response.text
    assert "LOCAL_BROWSER_RULES_NOT_A_SIGNED_AUDIT" in response.text


def test_repeated_slide_qc_recalculation():
    slide = SlideArtifact("S", "C", "H&E", blur_score=0.6)
    agent = SlideQCAgent()
    assert agent.evaluate(slide)
    assert slide.qc_status == SlideQCStatus.SUBOPTIMAL_BLUR
    slide.blur_score = 0.01
    assert agent.evaluate(slide) == []
    assert slide.qc_status == SlideQCStatus.PASS


def test_tnbc_requires_explicit_negative_breast_panel():
    agent = ImmunohistochemistryTriagerAgent()
    draft = SynopticReportDraft(
        case_id="S", organ_site="Breast", histologic_type="Invasive",
        histologic_grade="Nottingham Grade 3",
        biomarkers={"ER": "Negative", "PR": "Negative", "HER2": "2+ (Equivocal)"},
    )
    assert not any("Triple-Negative" in a.title for a in agent.evaluate(draft))
    draft.biomarkers["HER2"] = "1+"
    assert any("Triple-Negative" in a.title for a in agent.evaluate(draft))
    draft.organ_site = "Colon"
    assert not any("Triple-Negative" in a.title for a in agent.evaluate(draft))


def test_csv_formula_escaping_and_unique_columns(tmp_path, monkeypatch):
    monkeypatch.setenv("AUDIT_SECRET_KEY", "test-only-key")
    inp = tmp_path / "in.csv"
    out = tmp_path / "out.csv"
    inp.write_text("task_id,target_identifier,primary_metric,overall_urgency\n=2+2,KEY,2,CUSTOM\n", encoding="utf-8")
    assert operations_main(["batch", "-i", str(inp), "-o", str(out)]) == 0
    with out.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert rows[0]["task_id"] == "'=2+2"
    assert rows[0]["overall_urgency"] == "ROUTINE"
    assert out.read_text(encoding="utf-8").splitlines()[0].count("overall_urgency") == 1


def test_failed_verification_has_nonzero_exit(monkeypatch):
    monkeypatch.setenv("AUDIT_SECRET_KEY", "test-only-key")
    monkeypatch.setattr(AuditLogger, "verify_integrity", staticmethod(lambda: False))
    assert operations_main(["verify-audit"]) == 1

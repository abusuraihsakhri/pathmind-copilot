import io
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from pathmind.models import SlideArtifact, SlideQCStatus, SynopticReportDraft, SeverityLevel
from pathmind.agents import SlideQCAgent, SynopticValidatorAgent, ImmunohistochemistryTriagerAgent, PathMindCoordinator
from pathmind.cli import main


def test_slide_qc_agent():
    agent = SlideQCAgent(blur_threshold=0.20)
    good_slide = SlideArtifact("S1", "C1", "H&E", blur_score=0.04, tissue_fold_pct=0.0)
    alerts_good = agent.evaluate(good_slide)
    assert len(alerts_good) == 0

    blurry_slide = SlideArtifact("S2", "C1", "H&E", blur_score=0.35, tissue_fold_pct=0.0)
    alerts_bad = agent.evaluate(blurry_slide)
    assert len(alerts_bad) >= 1
    assert blurry_slide.qc_status == SlideQCStatus.SUBOPTIMAL_BLUR


def test_synoptic_validator_cap():
    agent = SynopticValidatorAgent()
    
    # Missing tumor size
    draft = SynopticReportDraft(
        case_id="C-101",
        organ_site="Breast",
        histologic_type="Invasive Carcinoma",
        tumor_size_cm=None,
    )
    alerts = agent.evaluate(draft)
    assert any("Tumor Dimension" in a.title for a in alerts)

    # Nodal count discordance
    draft_nodes = SynopticReportDraft(
        case_id="C-102",
        organ_site="Colon",
        histologic_type="Adenocarcinoma",
        tumor_size_cm=4.0,
        margins_status="Negative",
        lymph_nodes_positive=8,
        lymph_nodes_examined=5,
    )
    alerts_node = agent.evaluate(draft_nodes)
    assert any("Nodal Staging" in a.title for a in alerts_node)


def test_ihc_triager():
    agent = ImmunohistochemistryTriagerAgent()
    draft = SynopticReportDraft(
        case_id="C-103",
        organ_site="Breast",
        histologic_type="Invasive Carcinoma",
        biomarkers={"HER2": "2+ (Equivocal)"},
    )
    alerts = agent.evaluate(draft)
    assert any("HER2 Equivocal" in a.title for a in alerts)


def test_pathmind_coordinator():
    coord = PathMindCoordinator()
    draft = SynopticReportDraft(
        case_id="C-104",
        organ_site="Breast",
        histologic_type="Invasive Ductal Carcinoma",
        tumor_size_cm=2.5,
        margins_status="Negative",
        lymph_nodes_positive=1,
        lymph_nodes_examined=10,
        biomarkers={"ER": "Positive", "PR": "Positive", "HER2": "0"},
    )
    dossier = coord.audit_case(draft)
    assert dossier["signoff_readiness"] == "READY_FOR_SIGNOFF"

    ans = coord.query_assistant("What are the CAP guidelines?")
    assert "CAP" in ans


def test_cli():
    assert main(["audit"]) == 0
    assert main(["chat", "What", "is", "HER2?"]) == 0

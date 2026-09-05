"""
Automated Pytest Test Suite for Pathmind Copilot.
Domain: Clinical & Biomedical AI
Standard: CAP / CLSI / ISO Standards
"""
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set required environment variable for audit trail
os.environ.setdefault("AUDIT_SECRET_KEY", "test-audit-key-for-testing-only")

import pytest
from agents.base import PHIGuard, AuditLogger, SecurityException
from agents.models import SystemTaskPayload, UrgencyLevel, SystemIntegrityStatus
from agents.workers import InvariantQCWorker, SafetyEscalationWorker, ProtocolConformanceWorker
from agents.supervisor import SystemSupervisor
from cli import main


def test_phi_guard_enforcement():
    with pytest.raises(SecurityException):
        PHIGuard.assert_no_phi("Patient MRN-994827 blood culture positive for Staphylococcus")

    # Clean text passes
    PHIGuard.assert_no_phi("Analytical assay specimen KEY-001 optimal")


def test_specialized_workers():
    # Worker 1: QC Invariant
    p1 = SystemTaskPayload(task_id="T1", target_identifier="KEY-01", primary_metric=35.0)
    alerts1 = InvariantQCWorker.evaluate(p1)
    assert len(alerts1) == 1
    assert alerts1[0].urgency == UrgencyLevel.ELEVATED

    # Worker 2: Safety
    p2 = SystemTaskPayload(task_id="T2", target_identifier="KEY-02", primary_metric=10.0, is_critical_flag=True)
    alerts2 = SafetyEscalationWorker.evaluate(p2)
    assert len(alerts2) == 1
    assert alerts2[0].urgency == UrgencyLevel.CRITICAL_STAT

    # Worker 3: Protocol Conformance
    p3 = SystemTaskPayload(task_id="T3", target_identifier="KEY-03", primary_metric=10.0, status_descriptor="DISCORDANT_ANOMALY")
    alerts3 = ProtocolConformanceWorker.evaluate(p3)
    assert len(alerts3) == 1


def test_supervisor_consensus_and_audit():
    supervisor = SystemSupervisor(model_provider="mock")
    payload = SystemTaskPayload(
        task_id="TASK-PROD-01",
        target_identifier="KEY-PROD-01",
        primary_metric=12.0,
        secondary_metric=4.0,
        status_descriptor="NOMINAL"
    )
    dossier = supervisor.process_task(payload)
    assert dossier.overall_urgency == UrgencyLevel.ROUTINE
    assert dossier.integrity_status == SystemIntegrityStatus.VALIDATED
    assert dossier.audit_hash != ""

    # Verify cryptographic audit trail
    assert AuditLogger.verify_integrity() is True

    # CLI tests
    assert main(["audit", "--task-id", "CLI-TEST-01"]) == 0
    assert main(["chat", "Explain", "specifications"]) == 0
    assert main(["verify-audit"]) == 0


def test_phi_guard_blocks_various_patterns():
    """Test that PHI guard blocks various sensitive data patterns."""
    phi_samples = [
        "Patient MRN-12345678",
        "SSN: 123-45-6789",
        "Call 555-123-4567",
        "Email: patient@example.com",
        "DOB: 01/15/1985",
        "Patient Name John Smith",
    ]
    for sample in phi_samples:
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi(sample)


def test_phi_guard_allows_clean_text():
    """Test that PHI guard allows non-PHI text."""
    clean_samples = [
        "Analytical assay specimen KEY-001 optimal",
        "Task evaluation completed successfully",
        "Primary metric within normal bounds",
        "",
    ]
    for sample in clean_samples:
        PHIGuard.assert_no_phi(sample)  # Should not raise


def test_batch_missing_file():
    """Test batch command handles missing input file."""
    result = main(["batch", "-i", "nonexistent_file.csv"])
    assert result == 1


def test_audit_trail_tamper_detection():
    """Test that audit trail detects tampering."""
    from agents.base import AuditTrail
    trail = AuditTrail(secret_key="test-key")
    trail.log("test", "tier", "event", {"data": "value1"})
    trail.log("test", "tier", "event", {"data": "value2"})

    # Verify integrity is intact
    assert trail.verify_integrity() is True

    # Tamper with the prev_hash chain (breaks the chain)
    trail.logs[1]["prev_hash"] = "tampered_hash"

    # Integrity check should fail
    assert trail.verify_integrity() is False


def test_audit_trail_requires_secret_key():
    """Test that AuditTrail requires a secret key."""
    import os
    # Temporarily remove the env var
    original = os.environ.pop("AUDIT_SECRET_KEY", None)
    try:
        from agents.base import AuditTrail, SecurityException
        with pytest.raises(SecurityException):
            AuditTrail()
    finally:
        # Restore the env var
        if original:
            os.environ["AUDIT_SECRET_KEY"] = original

"""
Automated Pytest for pathmind-copilot Enrichment Modules.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from enrichment import (
    OverviewEngine,
    Enrichment1CapSynopticChecklistCompletionScoringEngine,
    FhirExportImplementationEngine,
    Enrichment2Hl7FhirR4DiagnosticreportResourceGenerationEngine,
    KappaTrackingImplementationEngine,
    Enrichment3InterobserverAgreementTrackingCohensKappaEngine,
    Enrichment4LongitudinalBiomarkerDeltaAnalysisEngine,
    PathmindcopilotEnrichmentSuite,
    enrichment_suite,
)

def test_enrichment_suite_execution():
    suite = PathmindcopilotEnrichmentSuite()
    res = suite.execute_all(primary_val=0.5, secondary_val=0.2)
    # 7 unique engines: Overview, Enrichment1, FhirExport, Enrichment2, KappaTracking, Enrichment3, Enrichment4
    assert len(res) == 7, f"Expected 7 engines, got {len(res)}"
    for k, v in res.items():
        assert v.status in ["OPTIMAL", "WARNING", "CRITICAL_ALERT"]
        assert isinstance(v.recommendations, list)

def test_enrichment_threshold_escalation():
    suite = PathmindcopilotEnrichmentSuite()
    res = suite.execute_all(primary_val=10.0, secondary_val=5.0)
    for k, v in res.items():
        assert v.status in ["WARNING", "CRITICAL_ALERT"]
        assert len(v.alerts) > 0

def test_implementation_engines_unique():
    """Verify that FHIR Export and Kappa Tracking implementation engines are distinct."""
    fhir_engine = FhirExportImplementationEngine()
    kappa_engine = KappaTrackingImplementationEngine()
    assert fhir_engine is not kappa_engine
    assert "FHIR" in fhir_engine.evaluate(1.0).feature_name
    assert "Kappa" in kappa_engine.evaluate(1.0).feature_name

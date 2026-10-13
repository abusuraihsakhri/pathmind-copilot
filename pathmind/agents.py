"""
PathMind Distributed Component Diagnostic Supervision Hierarchy.
Air-gapped, zero-PHI leakage, rule & local LLM compatible.
"""

import uuid
from typing import List, Dict, Any, Optional
from .models import (
    SlideArtifact,
    SlideQCStatus,
    SynopticReportDraft,
    AgentAlert,
    SeverityLevel,
)


class SlideQCAgent:
    """
    Supervises digital pathology slide scan quality before pathologist review.
    """
    def __init__(self, blur_threshold: float = 0.25, fold_threshold: float = 8.0):
        self.blur_threshold = blur_threshold
        self.fold_threshold = fold_threshold

    def evaluate(self, slide: SlideArtifact) -> List[AgentAlert]:
        alerts = []
        # A repeat assessment must clear stale quality status.
        slide.qc_status = SlideQCStatus.PASS
        if slide.blur_score > self.blur_threshold:
            slide.qc_status = SlideQCStatus.SUBOPTIMAL_BLUR
            alerts.append(
                AgentAlert(
                    alert_id=str(uuid.uuid4())[:8],
                    case_id=slide.case_id,
                    agent_name="SlideQCAgent",
                    severity=SeverityLevel.WARNING,
                    title="Suboptimal WSI Scan Focus (Blur Threshold Exceeded)",
                    description=f"Slide {slide.slide_id} ({slide.stain_type}) has a blur index of {slide.blur_score:.2f} (limit: {self.blur_threshold:.2f}). High-power diagnostic features may be obscured.",
                    remediation_recommendation="Request automated optical autofocus rescan at 40x on digital slide scanner.",
                )
            )

        if slide.tissue_fold_pct > self.fold_threshold:
            slide.qc_status = SlideQCStatus.TISSUE_FOLD
            alerts.append(
                AgentAlert(
                    alert_id=str(uuid.uuid4())[:8],
                    case_id=slide.case_id,
                    agent_name="SlideQCAgent",
                    severity=SeverityLevel.WARNING,
                    title="Extensive Tissue Folding Detected in Region of Interest",
                    description=f"Slide {slide.slide_id} exhibits {slide.tissue_fold_pct:.1f}% tissue fold area. Risk of artificial hyperchromasia and thickness artifacts.",
                    remediation_recommendation="Re-cut paraffin block with deeper serial section or recut floating ribbon.",
                )
            )

        return alerts


class SynopticValidatorAgent:
    """
    Audits surgical pathology synoptic reporting drafts against College of American Pathologists (CAP) protocols.
    """
    def evaluate(self, report: SynopticReportDraft) -> List[AgentAlert]:
        alerts = []

        # Rule 1: Mandatory Tumor Size
        if report.tumor_size_cm is None or report.tumor_size_cm <= 0:
            alerts.append(
                AgentAlert(
                    alert_id=str(uuid.uuid4())[:8],
                    case_id=report.case_id,
                    agent_name="SynopticValidatorAgent",
                    severity=SeverityLevel.CRITICAL_DISCORDANCE,
                    title="Missing CAP Mandatory Element: Greatest Tumor Dimension",
                    description=f"Synoptic report for {report.organ_site} ({report.histologic_type}) lacks tumor measurement.",
                    remediation_recommendation="Measure greatest macroscopic/microscopic tumor dimension in centimeters and record in synoptic item.",
                )
            )

        # Rule 2: Margin status completeness
        if not report.margins_status or report.margins_status.strip() == "":
            alerts.append(
                AgentAlert(
                    alert_id=str(uuid.uuid4())[:8],
                    case_id=report.case_id,
                    agent_name="SynopticValidatorAgent",
                    severity=SeverityLevel.WARNING,
                    title="Incomplete Surgical Margin Assessment",
                    description="Surgical resection margin clearance distance (mm) or ink status is not specified.",
                    remediation_recommendation="Document distance to closest deep, radial, and circumferential margins in millimeters.",
                )
            )

        # Rule 3: Lymph node tally consistency
        if report.lymph_nodes_positive is not None and report.lymph_nodes_examined is not None:
            if report.lymph_nodes_positive > report.lymph_nodes_examined:
                alerts.append(
                    AgentAlert(
                        alert_id=str(uuid.uuid4())[:8],
                        case_id=report.case_id,
                        agent_name="SynopticValidatorAgent",
                        severity=SeverityLevel.CRITICAL_DISCORDANCE,
                        title="Numerical Discordance in Nodal Staging",
                        description=f"Positive lymph nodes ({report.lymph_nodes_positive}) exceeds total nodes examined ({report.lymph_nodes_examined}).",
                        remediation_recommendation="Verify gross dissecting room cassette logs and adjust nodal numerator/denominator.",
                    )
                )

        # Rule 4: pT staging concordant with tumor size
        if report.organ_site.lower() == "breast" and report.tumor_size_cm is not None:
            if report.tumor_size_cm > 2.0 and report.tumor_size_cm <= 5.0:
                expected_pt = "pT2"
            elif report.tumor_size_cm > 5.0:
                expected_pt = "pT3"
            elif report.tumor_size_cm <= 2.0:
                expected_pt = "pT1"
            else:
                expected_pt = None

            if expected_pt and report.pT_stage and expected_pt not in report.pT_stage:
                alerts.append(
                    AgentAlert(
                        alert_id=str(uuid.uuid4())[:8],
                        case_id=report.case_id,
                        agent_name="SynopticValidatorAgent",
                        severity=SeverityLevel.WARNING,
                        title="Potential pTNM Staging Discrepancy",
                        description=f"Reported tumor size {report.tumor_size_cm} cm suggests {expected_pt}, but synoptic draft states '{report.pT_stage}'.",
                        remediation_recommendation=f"Review AJCC 8th Edition breast staging rules: confirm if clinical skin/chest wall involvement altered pT category.",
                    )
                )

        return alerts


class ImmunohistochemistryTriagerAgent:
    """
    Evaluates biomarker concordance (ER, PR, HER2, Ki-67, PD-L1, MMR) with histological morphology.
    """
    def evaluate(self, report: SynopticReportDraft) -> List[AgentAlert]:
        alerts = []
        bio = report.biomarkers

        # Rule 1: HER2 Equivocal (2+) requires reflex testing
        if report.organ_site.strip().lower() == "breast" and "HER2" in bio:
            her2_val = str(bio["HER2"]).upper()
            if "2+" in her2_val or "EQUIVOCAL" in her2_val:
                if "FISH" not in bio and "ISH" not in bio and "DUAL-ISH" not in bio:
                    alerts.append(
                        AgentAlert(
                            alert_id=str(uuid.uuid4())[:8],
                            case_id=report.case_id,
                            agent_name="ImmunohistochemistryTriagerAgent",
                            severity=SeverityLevel.WARNING,
                            title="HER2 Equivocal (2+) Reflex Testing Required",
                            description="HER2 IHC is scored 2+ (Equivocal). ASCO/CAP guidelines mandate reflex in-situ hybridization (FISH/D-ISH) prior to final sign-out.",
                            remediation_recommendation="Order reflex dual-probe HER2/CEP17 FISH testing on representative tumor block.",
                        )
                    )

        # Rule 2: High Grade TNBC check
        if (report.organ_site.strip().lower() == "breast"
                and report.histologic_grade and "3" in report.histologic_grade
                and all(marker in bio for marker in ("ER", "PR", "HER2"))):
            # Absent/indeterminate results are NOT evidence of marker negativity.
            er = str(bio["ER"]).strip().lower()
            pr = str(bio["PR"]).strip().lower()
            her2 = str(bio["HER2"]).strip().lower()
            def negative(value: str) -> bool:
                return value in {"0", "0%", "0+", "1+", "neg", "-"} or value.startswith("negative")
            if negative(er) and negative(pr) and negative(her2):
                alerts.append(
                    AgentAlert(
                        alert_id=str(uuid.uuid4())[:8],
                        case_id=report.case_id,
                        agent_name="ImmunohistochemistryTriagerAgent",
                        severity=SeverityLevel.ADVISORY,
                        title="Triple-Negative Breast Carcinoma (TNBC) Profile Identified",
                        description="Tumor demonstrates ER-/PR-/HER2- phenotype in Nottingham Grade 3 morphology.",
                        remediation_recommendation="Ensure internal positive controls (normal breast ducts) stained adequately; recommend consideration of PD-L1 (CPS) and germline BRCA evaluation.",
                    )
                )

        return alerts


class PathMindCoordinator:
    """
    Central orchestrator coordinating distributed component pathology workflow supervision.
    """
    def __init__(self):
        self.qc_agent = SlideQCAgent()
        self.synoptic_agent = SynopticValidatorAgent()
        self.ihc_agent = ImmunohistochemistryTriagerAgent()
        self.case_history: Dict[str, Dict[str, Any]] = {}

    def audit_case(
        self,
        report: SynopticReportDraft,
        slides: Optional[List[SlideArtifact]] = None,
    ) -> Dict[str, Any]:
        all_alerts: List[AgentAlert] = []

        # 1. Slide QC
        if slides:
            for s in slides:
                all_alerts.extend(self.qc_agent.evaluate(s))

        # 2. Synoptic Protocol Validation
        all_alerts.extend(self.synoptic_agent.evaluate(report))

        # 3. IHC & Biomarker Concordance
        all_alerts.extend(self.ihc_agent.evaluate(report))

        critical_count = sum(1 for a in all_alerts if a.severity == SeverityLevel.CRITICAL_DISCORDANCE)
        warning_count = sum(1 for a in all_alerts if a.severity == SeverityLevel.WARNING)
        is_ready = critical_count == 0

        dossier = {
            "case_id": report.case_id,
            "organ_site": report.organ_site,
            "histologic_type": report.histologic_type,
            "signoff_readiness": "READY_FOR_SIGNOFF" if is_ready else "SIGNOFF_BLOCKED",
            "total_alerts": len(all_alerts),
            "critical_discordances": critical_count,
            "warnings": warning_count,
            "alerts": [
                {
                    "alert_id": a.alert_id,
                    "agent": a.agent_name,
                    "severity": a.severity.value,
                    "title": a.title,
                    "description": a.description,
                    "recommendation": a.remediation_recommendation,
                }
                for a in all_alerts
            ],
        }

        self.case_history[report.case_id] = dossier
        return dossier

    def query_assistant(self, user_query: str) -> str:
        """
        Air-gapped supervisor chat assistant for pathology laboratory operations.
        """
        q = user_query.strip().lower()
        if "summary" in q or "status" in q or "cases" in q:
            total_cases = len(self.case_history)
            blocked_cases = sum(1 for c in self.case_history.values() if c["signoff_readiness"] == "SIGNOFF_BLOCKED")
            return f"PathMind Copilot has reviewed {total_cases} in-memory cases. {blocked_cases} have flags under this limited demonstration rule set."
        elif "cap" in q or "synoptic" in q:
            return "CAP synoptic protocols vary by organ, procedure, and edition. This demonstration only checks selected fields such as tumor size, margin presence and node count; it does not validate complete CAP compliance."
        elif "her2" in q:
            return "For breast carcinoma, an equivocal HER2 IHC result may require reflex ISH according to the applicable ASCO/CAP algorithm. This tool cannot interpret an individual case or replace current guidance."
        else:
            return "PathMind Copilot can review a submitted draft with limited rules. No background monitoring or continuous guideline updates occur."

"""
pathmind-copilot: Autonomous Digital Pathology Diagnostic Supervision & Synoptic Reporting Agent System.
Part of the Dr. Abu Suraih Sakhri clinical AI ecosystem.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any
import datetime


class SeverityLevel(str, Enum):
    INFO = "INFO"
    ADVISORY = "ADVISORY"
    WARNING = "WARNING"
    CRITICAL_DISCORDANCE = "CRITICAL_DISCORDANCE"


class SlideQCStatus(str, Enum):
    PASS = "PASS"
    SUBOPTIMAL_BLUR = "SUBOPTIMAL_BLUR"
    TISSUE_FOLD = "TISSUE_FOLD"
    AIR_BUBBLE = "AIR_BUBBLE"
    PEN_MARKING = "PEN_MARKING"
    RESCAN_REQUIRED = "RESCAN_REQUIRED"


@dataclass
class SlideArtifact:
    slide_id: str
    case_id: str
    stain_type: str  # "H&E", "ER", "PR", "HER2", "Ki-67", "PD-L1"
    magnification: str = "40x"
    blur_score: float = 0.05  # 0.0 to 1.0 (higher = blurrier)
    tissue_fold_pct: float = 0.0
    qc_status: SlideQCStatus = SlideQCStatus.PASS
    extracted_features: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SynopticReportDraft:
    case_id: str
    organ_site: str  # e.g., "Breast", "Colon", "Prostate", "Lung"
    histologic_type: str
    histologic_grade: Optional[str] = None  # e.g., "Nottingham Grade 3", "ISUP Grade Group 4"
    tumor_size_cm: Optional[float] = None
    margins_status: Optional[str] = None  # "Negative (>2mm)", "Positive (<1mm)"
    lymphovascular_invasion: Optional[bool] = None
    perineural_invasion: Optional[bool] = None
    lymph_nodes_positive: Optional[int] = None
    lymph_nodes_examined: Optional[int] = None
    pT_stage: Optional[str] = None
    pN_stage: Optional[str] = None
    biomarkers: Dict[str, str] = field(default_factory=dict)  # {"ER": "Positive (95%)", "HER2": "3+"}
    free_text_notes: str = ""


@dataclass
class AgentAlert:
    alert_id: str
    case_id: str
    agent_name: str
    severity: SeverityLevel
    title: str
    description: str
    remediation_recommendation: str
    timestamp: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())

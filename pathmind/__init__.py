"""
PathMind Copilot: Autonomous Digital Pathology Diagnostic Supervision Agent.
"""

from .models import (
    SlideArtifact,
    SlideQCStatus,
    SynopticReportDraft,
    AgentAlert,
    SeverityLevel,
)
from .agents import (
    SlideQCAgent,
    SynopticValidatorAgent,
    ImmunohistochemistryTriagerAgent,
    PathMindCoordinator,
)

__version__ = "1.0.0"
__all__ = [
    "SlideArtifact",
    "SlideQCStatus",
    "SynopticReportDraft",
    "AgentAlert",
    "SeverityLevel",
    "SlideQCAgent",
    "SynopticValidatorAgent",
    "ImmunohistochemistryTriagerAgent",
    "PathMindCoordinator",
]

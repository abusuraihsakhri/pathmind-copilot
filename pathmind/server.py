"""
FastAPI REST API & Event Server for PathMind Copilot.
"""

from typing import Dict, Any, List, Optional
from .models import SynopticReportDraft, SlideArtifact, SlideQCStatus
from .agents import PathMindCoordinator

coordinator = PathMindCoordinator()


def create_app():
    try:
        from fastapi import FastAPI, HTTPException
        from pydantic import BaseModel

        app = FastAPI(
            title="PathMind Copilot API",
            description="Autonomous Digital Pathology Diagnostic Supervision & Synoptic Reporting Agent System",
            version="1.0.0",
        )

        class AuditCaseRequest(BaseModel):
            case_id: str
            organ_site: str
            histologic_type: str
            histologic_grade: Optional[str] = None
            tumor_size_cm: Optional[float] = None
            margins_status: Optional[str] = None
            lymphovascular_invasion: Optional[bool] = None
            lymph_nodes_positive: Optional[int] = None
            lymph_nodes_examined: Optional[int] = None
            pT_stage: Optional[str] = None
            pN_stage: Optional[str] = None
            biomarkers: Dict[str, str] = {}
            slides: Optional[List[Dict[str, Any]]] = None

        class ChatRequest(BaseModel):
            query: str

        @app.get("/health")
        def health():
            return {"status": "HEALTHY", "system": "PathMind Copilot", "version": "1.0.0"}

        @app.post("/api/cases/audit")
        def audit_case(req: AuditCaseRequest):
            slides_objs = []
            if req.slides:
                for s in req.slides:
                    slides_objs.append(
                        SlideArtifact(
                            slide_id=s.get("slide_id", "SLIDE-01"),
                            case_id=req.case_id,
                            stain_type=s.get("stain_type", "H&E"),
                            blur_score=float(s.get("blur_score", 0.05)),
                            tissue_fold_pct=float(s.get("tissue_fold_pct", 0.0)),
                        )
                    )

            report = SynopticReportDraft(
                case_id=req.case_id,
                organ_site=req.organ_site,
                histologic_type=req.histologic_type,
                histologic_grade=req.histologic_grade,
                tumor_size_cm=req.tumor_size_cm,
                margins_status=req.margins_status,
                lymphovascular_invasion=req.lymphovascular_invasion,
                lymph_nodes_positive=req.lymph_nodes_positive,
                lymph_nodes_examined=req.lymph_nodes_examined,
                pT_stage=req.pT_stage,
                pN_stage=req.pN_stage,
                biomarkers=req.biomarkers,
            )

            dossier = coordinator.audit_case(report, slides_objs)
            return dossier

        @app.post("/api/chat")
        def chat(req: ChatRequest):
            answer = coordinator.query_assistant(req.query)
            return {"response": answer}

        return app

    except ImportError:
        return None

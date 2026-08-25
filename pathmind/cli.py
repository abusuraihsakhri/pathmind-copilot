"""
CLI for PathMind Copilot.
"""

import argparse
import json
import sys
from .models import SynopticReportDraft, SlideArtifact
from .agents import PathMindCoordinator


def get_sample_breast_case() -> SynopticReportDraft:
    return SynopticReportDraft(
        case_id="SP-2026-09412",
        organ_site="Breast",
        histologic_type="Invasive Ductal Carcinoma (NST)",
        histologic_grade="Nottingham Grade 3",
        tumor_size_cm=3.4,
        margins_status="Negative, closest deep margin 3.5 mm",
        lymphovascular_invasion=True,
        lymph_nodes_positive=2,
        lymph_nodes_examined=14,
        pT_stage="pT2",
        pN_stage="pN1a",
        biomarkers={
            "ER": "Positive (95%, strong)",
            "PR": "Positive (80%, strong)",
            "HER2": "2+ (Equivocal)",
            "Ki-67": "35%",
        },
    )


def get_sample_slides() -> list:
    return [
        SlideArtifact(
            slide_id="SLIDE-01-HE",
            case_id="SP-2026-09412",
            stain_type="H&E",
            blur_score=0.08,
            tissue_fold_pct=1.2,
        ),
        SlideArtifact(
            slide_id="SLIDE-02-HER2",
            case_id="SP-2026-09412",
            stain_type="HER2",
            blur_score=0.12,
            tissue_fold_pct=0.5,
        ),
    ]


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="pathmind",
        description="Autonomous Digital Pathology Diagnostic Supervision & Synoptic Reporting Agent System.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Audit command
    audit_parser = subparsers.add_parser("audit", help="Audit a surgical pathology synoptic draft")
    audit_parser.add_argument("-c", "--case-json", default=None, help="Path to JSON file with case details")

    # Chat command
    chat_parser = subparsers.add_parser("chat", help="Air-gapped supervisor chat query")
    chat_parser.add_argument("query", nargs="+", help="Natural language query for PathMind Copilot")

    # Sample command
    sample_parser = subparsers.add_parser("sample", help="Print sample synoptic case JSON")
    sample_parser.add_argument("-o", "--output", default=None, help="File to write")

    # Serve command
    serve_parser = subparsers.add_parser("serve", help="Launch FastAPI REST API server")
    serve_parser.add_argument("--host", default="127.0.0.1", help="Host binding")
    serve_parser.add_argument("--port", type=int, default=8001, help="Port binding")

    args = parser.parse_args(argv)
    coordinator = PathMindCoordinator()

    if args.command == "sample":
        case = get_sample_breast_case()
        slides = get_sample_slides()
        case_dict = {
            "case_id": case.case_id,
            "organ_site": case.organ_site,
            "histologic_type": case.histologic_type,
            "histologic_grade": case.histologic_grade,
            "tumor_size_cm": case.tumor_size_cm,
            "margins_status": case.margins_status,
            "lymphovascular_invasion": case.lymphovascular_invasion,
            "lymph_nodes_positive": case.lymph_nodes_positive,
            "lymph_nodes_examined": case.lymph_nodes_examined,
            "pT_stage": case.pT_stage,
            "pN_stage": case.pN_stage,
            "biomarkers": case.biomarkers,
            "slides": [
                {
                    "slide_id": s.slide_id,
                    "stain_type": s.stain_type,
                    "blur_score": s.blur_score,
                    "tissue_fold_pct": s.tissue_fold_pct,
                }
                for s in slides
            ],
        }
        json_text = json.dumps(case_dict, indent=2)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(json_text)
            print(f"Sample case written to: {args.output}")
        else:
            print(json_text)
        return 0

    if args.command == "audit":
        if args.case_json:
            with open(args.case_json, "r", encoding="utf-8") as f:
                data = json.load(f)
            slides_list = [
                SlideArtifact(
                    slide_id=s.get("slide_id", "SL-01"),
                    case_id=data.get("case_id", "CASE-01"),
                    stain_type=s.get("stain_type", "H&E"),
                    blur_score=float(s.get("blur_score", 0.05)),
                    tissue_fold_pct=float(s.get("tissue_fold_pct", 0.0)),
                )
                for s in data.get("slides", [])
            ]
            case = SynopticReportDraft(
                case_id=data.get("case_id", "CASE-01"),
                organ_site=data.get("organ_site", "Breast"),
                histologic_type=data.get("histologic_type", "Invasive Carcinoma"),
                histologic_grade=data.get("histologic_grade"),
                tumor_size_cm=data.get("tumor_size_cm"),
                margins_status=data.get("margins_status"),
                lymphovascular_invasion=data.get("lymphovascular_invasion"),
                lymph_nodes_positive=data.get("lymph_nodes_positive"),
                lymph_nodes_examined=data.get("lymph_nodes_examined"),
                pT_stage=data.get("pT_stage"),
                pN_stage=data.get("pN_stage"),
                biomarkers=data.get("biomarkers", {}),
            )
        else:
            case = get_sample_breast_case()
            slides_list = get_sample_slides()

        dossier = coordinator.audit_case(case, slides_list)

        print("=" * 80)
        print(f"  PATHMIND COPILOT DIAGNOSTIC SUPERVISION REPORT: {dossier['case_id']}")
        print(f"  Site: {dossier['organ_site']} | Type: {dossier['histologic_type']}")
        print(f"  Sign-Off Status: [{dossier['signoff_readiness']}] | Alerts: {dossier['total_alerts']}")
        print("=" * 80)

        if not dossier["alerts"]:
            print("\n  [PASS] No diagnostic discordances or CAP protocol deficiencies detected.")
        else:
            for alert in dossier["alerts"]:
                print(f"\n  [{alert['severity']}] from {alert['agent']}:")
                print(f"  Title: {alert['title']}")
                print(f"  Details: {alert['description']}")
                print(f"  Recommendation: {alert['recommendation']}")

        print("\n" + "=" * 80)
        return 0

    if args.command == "chat":
        query_str = " ".join(args.query)
        ans = coordinator.query_assistant(query_str)
        print(f"\n[PathMind Supervisor]:\n{ans}\n")
        return 0

    if args.command == "serve":
        try:
            import uvicorn
            from .server import create_app
            app = create_app()
            if app is None:
                print("FastAPI / uvicorn not installed. Please run pip install fastapi uvicorn")
                return 1
            print(f"Starting PathMind Copilot API on http://{args.host}:{args.port}")
            uvicorn.run(app, host=args.host, port=args.port)
        except ImportError:
            print("Uvicorn not installed. Run 'pip install uvicorn fastapi'")
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

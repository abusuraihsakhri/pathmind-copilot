# Pathmind Copilot

Rule-based digital pathology draft review and analytical task evaluation, with Python CLIs, two FastAPI interfaces, and a standalone browser demonstration.

**Research/education only.** These example rules and thresholds are not validated clinical decision support, do not implement complete current CAP protocols, and must not authorize diagnostic sign-out. Do not submit identifiable patient data.

## Features

- **Pathology workflow:** Review synoptic draft completeness, numeric lymph-node consistency, a limited breast size/stage heuristic, manually provided slide-quality metrics, and breast HER2/marker patterns.
- **Operations workflow:** Evaluate two synthetic metrics and a status descriptor against three deterministic rule workers; export single-task or batch CSV results.
- **Audit ledger:** Server-side in-memory HMAC-SHA256 linked records with cryptographic verification. Not persistent across restarts, and not a substitute for a validated clinical audit system.
- **Local REST APIs:** Separate clinical draft and operations APIs via FastAPI.
- **Browser demonstration:** `web/index.html` runs deterministic operations rules locally using JavaScript; no Python runtime or server required. JSON export is available. A local operations server can optionally handle evaluation when the console is opened on localhost.

The `enrichment.py` module is a set of generic threshold-based demonstrations; its names do **not** mean that FHIR export, Cohen's kappa, or complete CAP checklist scoring are implemented.

## Quick start

Python 3.9+ is supported by the package metadata. Use a virtual environment:

```sh
git clone https://github.com/abusuraihsakhri/pathmind-copilot.git
cd pathmind-copilot
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[server,test]"
```

Run the pathology CLI with the built-in synthetic sample:

```sh
pathmind audit
pathmind sample
pathmind sample -o example.json
pathmind audit -c sample_case.json
pathmind chat "What is HER2?"
```

Run the independent operations CLI with a **random, external secret** (required for the HMAC ledger):

```sh
export AUDIT_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
pathmind-ops audit --task-id TASK-001 --target SPECIMEN-01 --primary 28.5 --secondary 14.2 --status DISCORDANT
pathmind-ops verify-audit
pathmind-ops batch -i input.csv -o results.csv
```

CSV input requires at least `task_id`, `target_identifier`, and `primary_metric` columns for meaningful output. The audit ledger is process-local, so running `verify-audit` in a separate process starts a new empty ledger.

## Browser demonstration

Open `web/index.html` directly in a modern browser. The form runs entirely locally and lets you export the latest result as JSON. GitHub Pages may serve this same `web/` directory when Pages is enabled and the deployment workflow succeeds. **Local/browser evaluations are not cryptographically signed.** No network requests are made for evaluation on the standalone page.

When the operations API is started locally at `http://127.0.0.1:8000`, visiting that URL serves the same console and sends evaluations to the Python API. The browser displays server errors instead of fabricating success or a signature.

## Local APIs

```sh
# Operations API on port 8000 and browser console at /
pathmind-ops serve --host 127.0.0.1 --port 8000

# Separate pathology draft API on port 8001
pathmind serve --host 127.0.0.1 --port 8001
```

Operations endpoints: `GET /health`, `GET /metrics`, `POST /api/audit`, `POST /api/chat`, `GET /api/audit/logs`. Audit-log reads are **disabled unless** `AUDIT_READ_TOKEN` is set. Set a different random token from `AUDIT_SECRET_KEY` and pass it in the `X-Audit-Token` request header.

Pathology endpoints: `GET /health`, `POST /api/cases/audit`, `POST /api/chat`.

**Security boundary:** APIs other than audit-log retrieval have no built-in authentication. Bind to loopback for testing. Production use requires authenticated access, TLS, request limits, an appropriate data governance assessment, and qualified clinical validation. Regex-based identifier screening is incomplete and must not be relied on for HIPAA de-identification.

## Docker

Copy `.env.example` to `.env`, set `AUDIT_SECRET_KEY` to a randomly generated secret, then run:

```sh
docker compose up --build
```

The Compose configuration binds port 8000 to `127.0.0.1` by default.

## Tests

```sh
python -m pip install -e ".[server,test]"
AUDIT_SECRET_KEY=local-test-only python -m pytest -q
python -m compileall -q agents pathmind cli.py
```

GitHub Actions tests Python 3.10–3.12 and checks the browser script syntax. The browser demonstration needs JavaScript, `Blob` downloads, and standard DOM APIs; browser-engine compatibility and deployed-site smoke tests must be checked separately.

## Technology and privacy

Python standard library, dataclasses, Pydantic 2, optional FastAPI/Uvicorn, and dependency-free HTML/CSS/JavaScript. The standalone browser demonstration processes data locally and has no telemetry or external evaluation endpoint. Server mode sends form data to the local API and keeps an in-memory ledger/dossier registry; it has no persistence or access-control system for submitted records. Avoid real patient data.

## License

MIT. See [LICENSE](LICENSE).

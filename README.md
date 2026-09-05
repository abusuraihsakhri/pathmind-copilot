# Pathmind Copilot

> **Domain:** Clinical Decision Support & Biomedical Computing
> **Standards:** CAP / CLSI / ISO / HIPAA Safe Harbor

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

**Pathmind Copilot** is an advanced clinical decision support platform that provides:

- **Surgical Pathology Synoptic Reporting**: Automated validation of synoptic reports against CAP Cancer Protocols
- **Digital Pathology Slide QC**: Automated quality control for whole-slide imaging scans
- **Biomarker Concordance**: IHC triaging and HER2 reflex testing recommendations
- **Multi-Agent Consensus**: Distributed worker architecture for comprehensive analysis
- **Zero-PHI Protection**: AST and regex-based outbound guard preventing protected health information leakage

---

## 🚀 Quickstart

### Prerequisites
- Python 3.9+
- pip or virtual environment

### Installation

```bash
# Clone the repository
git clone https://github.com/abusuraihsakhri/pathmind-copilot.git
cd pathmind-copilot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install fastapi uvicorn pydantic pytest
```

### Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env and set your secure audit key
# Generate a strong key: python -c "import secrets; print(secrets.token_hex(32))"
```

---

## 💻 CLI Usage

### 1. Audit a Synoptic Report (Pathology Domain)
```bash
python -m pathmind.cli audit
```

### 2. Run Distributed Component Evaluation
```bash
python cli.py audit --task-id TASK-001 --target SPECIMEN-01 --primary 28.5 --secondary 14.2 --critical --status DISCORDANT
```

### 3. Batch Process CSV Records
```bash
python cli.py batch -i input.csv -o results.csv
```

### 4. Interactive Chat
```bash
python cli.py chat "What are the CAP guidelines?"
```

### 5. Verify Audit Trail Integrity
```bash
python cli.py verify-audit
```

### 6. Launch REST API Server
```bash
python cli.py serve --host 127.0.0.1 --port 8000
```

---

## 🛡️ Security Architecture

### Zero-PHI Outbound Interceptor
Active regex inspection blocking:
- Medical Record Numbers (MRN)
- Social Security Numbers
- Phone numbers and email addresses
- Dates of birth
- Patient names (common patterns)

### HMAC-SHA256 Audit Trail
- Cryptographically chained logs for every evaluation
- Tamper-evident verification via `verify-audit` command
- Requires `AUDIT_SECRET_KEY` environment variable

### Input Validation
- Pydantic v2 schemas with bounds checking
- Resource limit enforcement
- CSV parsing error handling

---

## 🧪 Testing

```bash
# Run all tests
pytest -v

# Run with coverage
pytest -v --cov=agents --cov=pathmind

# Run specific test modules
pytest tests/test_pathmind.py -v
pytest tests/test_enrichment.py -v
```

---

## 🐳 Docker Deployment

```bash
# Create .env file first
echo "AUDIT_SECRET_KEY=your-secure-key-here" > .env

# Build and run
docker-compose up --build

# Or manually
docker build -t pathmind-copilot .
docker run -p 8000:8000 --env-file .env pathmind-copilot
```

---

## 📁 Project Structure

```
pathmind-copilot/
├── agents/              # Enterprise distributed component system
│   ├── api.py           # FastAPI REST endpoints
│   ├── base.py          # Security, PHI guard, audit trail
│   ├── models.py        # Pydantic schemas
│   ├── supervisor.py    # Master orchestrator
│   ├── workers.py       # Specialized evaluation workers
│   ├── llm_factory.py   # LLM provider abstraction
│   ├── metrics.py       # Prometheus metrics
│   ├── learning.py      # Bayesian calibration engine
│   └── streamer.py      # WebSocket telemetry
├── pathmind/            # Pathology-specific domain modules
│   ├── agents.py        # Slide QC, Synoptic Validator, IHC Triager
│   ├── models.py        # Domain data models
│   ├── cli.py           # Domain-specific CLI
│   └── server.py        # FastAPI server factory
├── tests/               # Test suite
├── web/                 # Operations console (HTML)
├── cli.py               # Main CLI entry point
├── simulator.py         # High-throughput simulation
├── enrichment.py        # Extended feature engines
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

---

## 📝 License

MIT License. See [LICENSE](LICENSE) for details.

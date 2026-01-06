# SecureChat: AI-Powered Dependency Security Assistant

> **Project Update (Nov 2025)**: Pivoted from CVE feed aggregator to dependency security scanner with AI chat interface. See [PIVOT_SUMMARY.md](PIVOT_SUMMARY.md) for details.

Real-time dependency vulnerability scanner with conversational AI assistant powered by RAG-enhanced LLM.

---

## 🚀 **One-Command Launch**

```bash
./start.sh
```

**Then open**: http://localhost:3000

The script automatically:
- ✅ Starts FastAPI backend (port 8000)
- ✅ Starts Next.js frontend (port 3000)
- ✅ Opens browser
- ✅ Shows live logs

**Stop everything**: `./stop.sh` or press `Ctrl+C`

**See**: [QUICK_START.md](QUICK_START.md) for detailed instructions.

---

## Development Scripts

### Local Development

```bash
# Start API (port 8000) + Frontend (port 3000) in one command
./start.sh

# Stop all running services
./stop.sh
```

### Environment Management

```bash
# Switch to local development environment
./scripts/switch-env.sh local

# Switch to production configuration
./scripts/switch-env.sh production

# Validate your environment configuration
./scripts/check-env.sh
```

---

## Overview

SecureChat scans your project dependencies (npm, pip, Go, Ruby) for CVEs and provides an AI chat interface to understand risks, prioritize fixes, and get actionable remediation guidance tailored to YOUR specific stack.

## Features

### Core Capabilities
- **Dependency Scanning**: Upload package.json, requirements.txt, go.mod, Gemfile, or pom.xml
- **CVE Matching**: Automatically map dependencies to known vulnerabilities
- **AI Chat Assistant**: Ask questions about YOUR specific vulnerabilities
- **RAG-Enhanced Responses**: Context-aware answers grounded in real CVE data
- **Prioritization Guidance**: AI recommends which CVEs to fix first
- **Impact Analysis**: Understand how CVEs affect YOUR specific stack

### Technical Features
- **Multi-Source Data**: NVD CVE, CISA KEV, MITRE ATT&CK feeds
- **LLM Optimization**: LoRA fine-tuned model with 4-bit quantization
- **High Performance**: vLLM deployment with 3× throughput improvement
- **Real-Time Dashboard**: Streamlit UI with charts and reports
- **Production API**: FastAPI backend with WebSocket chat

## Project Status

**Phase 0 COMPLETE** ✅ - Security & Testing Foundation (Nov 2025)
- [x] Security infrastructure (pre-commit hooks, secret detection)
- [x] Testing framework with 55 passing tests
- [x] Mock CVE fixtures for fast unit tests
- [x] Integration tests for real NVD data
- [x] CI/CD pipeline configured

**Phase 1 COMPLETE** ✅ - Foundation & NVD Pipeline (Nov 2025)
- [x] Project structure and configuration
- [x] Database models and ORM
- [x] NVD API integration
- [x] CLI tool for data fetching
- [x] 100+ CVEs fetched and stored
- [x] Data exported (JSON, CSV)

**Phase 2 COMPLETE** ✅ - Dependency Scanner (100% for npm/pip)
- [x] npm and pip parsers with full test coverage (73.67%)
- [x] Lock file support (package-lock.json, Pipfile)
- [x] Security hardening (file size limits, path traversal prevention)
- [x] CPE matcher with 80 package mappings (50 npm + 30 pip)
- [x] Version comparator with semver support
- [x] CLI scanner with filters (severity, vulnerable-only)
- [x] HTML report output with Jinja2 templates
- [x] 70 passing tests
- [ ] Go, Ruby, Maven parsers (deferred to future)

**Phase 3 COMPLETE** ✅ - Web UI & Reports (Nov 2025)
- [x] Production-ready Next.js 15 frontend with TypeScript
- [x] FastAPI backend with 8 REST endpoints
- [x] Beautiful UI with shadcn/ui components + Framer Motion
- [x] Upload interface with drag-and-drop
- [x] Dashboard with scan history and statistics
- [x] Export functionality (JSON, CSV, HTML)
- [x] React Query for server state management
- [x] Responsive design with dark mode

**Phase 4 COMPLETE** ✅ - RAG Retrieval System (Nov 2025)
- [x] CVE Embedder (sentence-transformers, 384-dim)
- [x] Vector Store (ChromaDB with persistence)
- [x] RAG Retriever (general + project-specific queries)
- [x] REST API endpoints for semantic search
- [x] 28/28 tests passing (75%+ coverage)
- [x] Content-based file detection (arbitrary filenames)
- [x] Performance: <100ms query latency

**Current**: Phase 5 - AI Chat Interface

See [PHASE4_COMPLETE.md](PHASE4_COMPLETE.md) for detailed Phase 4 summary.

### Roadmap (Updated Nov 2025)

See [PROJECT_PLAN.md](PROJECT_PLAN.md) for full technical details.

| Phase | Status | Duration | Key Features |
|-------|--------|----------|--------------|
| **Phase 0**: Security & Testing | ✅ Complete | 1 week | Pre-commit hooks, 73% test coverage |
| **Phase 1**: NVD Pipeline | ✅ Complete | 2 weeks | Data ingestion, database, CLI |
| **Phase 2**: Dependency Scanner | ✅ Complete | 2 weeks | npm/pip parsers, CPE matching, reports |
| **Phase 3**: Web UI & Reports | ✅ Complete | 1 week | Next.js frontend, FastAPI backend |
| **Phase 4**: RAG System | ✅ Complete | 1.5 days | Embeddings, vector DB, semantic search |
| **Phase 5**: AI Chat | 🔄 Next | 2-3 weeks | Chat UI, LLM integration, WebSocket |
| **Phase 6**: Optimization | ⏳ Planned | 2 weeks | LoRA, quantization, vLLM, Docker |

**Progress**: 4/6 phases complete (67%)

## Quick Start

### Prerequisites

- Python 3.10 or higher
- pip and virtualenv

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd "CyberIntel Summarizer"

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# (Optional) Add your NVD API key to .env for higher rate limits
```

### Usage

#### Setup & Data Fetching

```bash
# Initialize database (first time only)
python -m scripts.init_db

# Verify setup
python -m scripts.verify_setup

# Fetch recent CVEs (last 7 days)
python -m scripts.fetch_nvd --days 7

# Fetch CVEs with limit
python -m scripts.fetch_nvd --days 30 --limit 200

# Fetch specific CVE
python -m scripts.fetch_nvd --cve-id CVE-2025-1234

# Verbose output
python -m scripts.fetch_nvd --days 7 --verbose
```

#### Dependency Scanning (NEW in Phase 2)

```bash
# Basic scan
python -m scripts.scan_dependencies --file package.json

# Scan Python dependencies
python -m scripts.scan_dependencies --file requirements.txt

# Scan lock files
python -m scripts.scan_dependencies --file package-lock.json
python -m scripts.scan_dependencies --file Pipfile

# Filter by severity
python -m scripts.scan_dependencies \
    --file package.json \
    --severity-min High

# Show only vulnerable packages
python -m scripts.scan_dependencies \
    --file requirements.txt \
    --vulnerable-only

# Generate HTML report
python -m scripts.scan_dependencies \
    --file package.json \
    --output html \
    --output-file report.html

# JSON output for CI/CD
python -m scripts.scan_dependencies \
    --file package.json \
    --output json > scan_results.json
```

## Architecture

```
cyberintel-summarizer/
├── data_ingestion/      # Data fetching from external APIs
├── database/            # SQLAlchemy models and connections
├── llm_engine/          # Model inference and optimization
├── api/                 # FastAPI backend
├── dashboard/           # Streamlit frontend
├── benchmarks/          # Performance testing
├── scripts/             # CLI tools and automation
└── configs/             # Configuration files
```

## Development Phases

See [PROJECT_PLAN.md](PROJECT_PLAN.md) for detailed implementation roadmap.

1. **Phase 1**: Foundation & NVD Pipeline ✅ *Complete*
2. **Phase 2**: Dependency Scanner → Parse package files, CPE matching
3. **Phase 3**: Web UI & Reports → Upload interface, vulnerability dashboard
4. **Phase 4**: RAG System → Embeddings, vector DB, semantic search
5. **Phase 5**: AI Chat Interface → Conversational UI, LLM integration
6. **Phase 6**: Optimization & Production → LoRA, quantization, vLLM, Docker

**Why the pivot?** See [PIVOT_SUMMARY.md](PIVOT_SUMMARY.md) for the full story of why we shifted from CVE summarization to dependency scanning + AI chat.

## Testing

Comprehensive test suite with 55 passing tests:

```bash
# Run fast unit tests (recommended for development)
pytest -m "not integration"

# Run all tests including integration tests
pytest

# Generate coverage report
pytest --cov=. --cov-report=html
```

See [TESTING.md](TESTING.md) for detailed testing strategy, mock data, and best practices.

## Performance Metrics

Current achievements:
- 55 unit tests running in <1 second
- 47% code coverage (Phase 0-2 modules)
- Mock CVE database with 20 comprehensive test scenarios

Target achievements (to be validated in Phase 5-6):
- 3× throughput improvement (vLLM vs baseline)
- 60% memory reduction (4-bit quantization)
- <500ms API response time
- 100+ daily CVE updates

## Contributing

This is a portfolio/research project. Contributions welcome via issues and pull requests.

## License

MIT License

## Contact

[Your contact information]

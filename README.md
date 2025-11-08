# SecureChat: AI-Powered Dependency Security Assistant

> **Project Update (Nov 2025)**: Pivoted from CVE feed aggregator to dependency security scanner with AI chat interface. See [PIVOT_SUMMARY.md](PIVOT_SUMMARY.md) for details.

Real-time dependency vulnerability scanner with conversational AI assistant powered by RAG-enhanced LLM.

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

**Phase 1 COMPLETE** ✅ - Foundation & NVD Pipeline (Nov 2025)
- [x] Project structure and configuration
- [x] Database models and ORM
- [x] NVD API integration
- [x] CLI tool for data fetching
- [x] 100+ CVEs fetched and stored
- [x] Data exported (JSON, CSV)

**Current**: Planning Phase 2 - Dependency Scanner

### Roadmap (Updated Nov 2025)

See [PROJECT_PLAN.md](PROJECT_PLAN.md) for full technical details.

| Phase | Status | Duration | Key Features |
|-------|--------|----------|--------------|
| **Phase 1**: NVD Pipeline | ✅ Complete | 2 weeks | Data ingestion, database, CLI |
| **Phase 2**: Dependency Scanner | 🔄 Next | 2-3 weeks | Parse files, CPE matching, reports |
| **Phase 3**: Web UI & Reports | ⏳ Planned | 2 weeks | Upload interface, dashboard, charts |
| **Phase 4**: RAG System | ⏳ Planned | 2-3 weeks | Embeddings, vector DB, retrieval |
| **Phase 5**: AI Chat | ⏳ Planned | 2-3 weeks | Chat UI, LLM integration, WebSocket |
| **Phase 6**: Optimization | ⏳ Planned | 2 weeks | LoRA, quantization, vLLM, Docker |

**Total Timeline**: 10-14 weeks (2.5-3.5 months)

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

## Performance Metrics

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

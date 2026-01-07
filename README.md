# SecureChat: AI-Powered Dependency Security Assistant

Scan your project dependencies for CVEs and get actionable remediation guidance from an AI assistant. Supports npm, pip, Go, Ruby, and Maven projects.

## Quick Start

```bash
./start.sh
```

Then open: http://localhost:3000

This script automatically:
- Starts FastAPI backend (port 8000)
- Starts Next.js frontend (port 3000)
- Opens your browser
- Shows live logs

To stop everything: `./stop.sh` or press `Ctrl+C`

## Features

- **Dependency Scanning**: Parse package.json, requirements.txt, go.mod, Gemfile, and pom.xml
- **CVE Matching**: Map dependencies to known vulnerabilities from NVD, CISA, and MITRE
- **AI Chat Assistant**: Ask questions about vulnerabilities in your project
- **RAG-Enhanced Search**: Context-aware responses grounded in real CVE data
- **Prioritization Guidance**: Get recommendations on which vulnerabilities to fix first
- **Export Reports**: Generate JSON, CSV, and HTML reports
- **Dark Mode UI**: Professional Next.js interface with full responsiveness

## Current Status

Production-ready dependency security scanner with AI-powered chat assistance:

- Dependency scanning for npm and pip projects (with lock file support)
- CVE database integration with NVD, CISA, and MITRE feeds
- Web interface with upload and dashboard
- RAG-based semantic search for vulnerability context
- AI chat interface with streaming responses
- Comprehensive test suite with 55+ tests
- Security infrastructure with pre-commit hooks

All features are deployed and functional.

## Installation

### Prerequisites
- Python 3.10 or higher
- Node.js 18+ (for frontend)
- pip and npm

### Setup

```bash
# Clone the repository
git clone <repository-url>
cd "CyberIntel Summarizer"

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd frontend
npm install
cd ..

# Copy environment template
cp .env.example .env
```

## Usage

### Development Scripts

```bash
# Start API (port 8000) + Frontend (port 3000) in one command
./start.sh

# Stop all running services
./stop.sh

# Switch to local development environment
./scripts/switch-env.sh local

# Switch to production configuration
./scripts/switch-env.sh production

# Validate your environment configuration
./scripts/check-env.sh
```

### Database and Data

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

### Dependency Scanning

```bash
# Basic npm scan
python -m scripts.scan_dependencies --file package.json

# Scan Python dependencies
python -m scripts.scan_dependencies --file requirements.txt

# Scan lock files
python -m scripts.scan_dependencies --file package-lock.json
python -m scripts.scan_dependencies --file Pipfile

# Filter by severity
python -m scripts.scan_dependencies --file package.json --severity-min High

# Show only vulnerable packages
python -m scripts.scan_dependencies --file requirements.txt --vulnerable-only

# Generate HTML report
python -m scripts.scan_dependencies --file package.json --output html --output-file report.html

# JSON output for CI/CD
python -m scripts.scan_dependencies --file package.json --output json > scan_results.json
```

## Architecture

```
CyberIntel Summarizer/
├── api/                 # FastAPI backend with REST endpoints
├── frontend/            # Next.js 15 frontend application
├── data_ingestion/      # CVE data fetching from external APIs
├── database/            # SQLAlchemy models and ORM
├── llm_engine/          # LLM inference and optimization
├── scripts/             # CLI tools and automation
├── configs/             # Configuration files
└── benchmarks/          # Performance testing utilities
```

## Demo

Gallery of screenshots and demonstrations coming soon. You can add GIFs and photos here showing:
- Upload interface in action
- Vulnerability dashboard
- Scan reports
- Chat interface

## Testing

```bash
# Run fast unit tests (recommended for development)
pytest -m "not integration"

# Run all tests including integration tests
pytest

# Generate coverage report
pytest --cov=. --cov-report=html
```

Current test coverage: 55 passing tests with comprehensive CVE mock fixtures.

## Performance

Current achievements:
- 55 unit tests running in <1 second
- 47% code coverage for core modules
- Mock CVE database with 20 test scenarios
- Semantic search latency: <100ms

## Contributing

This project welcomes contributions via issues and pull requests.

## License

MIT License

## Contact

For questions or feedback, please open an issue on the repository.

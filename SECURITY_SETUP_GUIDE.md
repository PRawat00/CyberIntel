# Security Setup Quick Reference

This guide helps you set up the security infrastructure for the CyberIntel Summarizer project.

## One-Time Setup

### 1. Install All Dependencies
```bash
pip install -r requirements.txt
```

### 2. Initialize Pre-commit Hooks
```bash
# Create secrets baseline
detect-secrets scan > .secrets.baseline

# Install git hooks
pre-commit install

# Verify installation
pre-commit run --all-files
```

### 3. Configure Environment Variables
```bash
# Copy template
cp .env.example .env

# Edit with your values
nano .env
```

Add your NVD API key (optional but recommended):
- Get one at: https://nvd.nist.gov/developers/request-an-api-key
- Add to `.env`: `NVD_API_KEY=your_key_here`

## Daily Development Workflow

### Before Starting Work
```bash
# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Pull latest changes
git pull

# Install any new dependencies
pip install -r requirements.txt
```

### While Coding
```bash
# Format code automatically
black .

# Check for linting issues
ruff check .

# Fix auto-fixable issues
ruff check --fix .
```

### Before Committing

Pre-commit hooks will run automatically, but you can test first:
```bash
# Run all checks
pre-commit run --all-files

# Run specific checks
pre-commit run black --all-files
pre-commit run ruff --all-files
pre-commit run detect-secrets --all-files
```

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_parsers.py

# Run tests matching a pattern
pytest -k "test_npm"

# Run only fast unit tests
pytest -m unit
```

## Security Checklist

### NEVER Commit
- `.env` files (actual values)
- API keys or passwords
- Database files (.db, .sqlite)
- Private keys (.key, .pem)
- Logs with sensitive data

### ALWAYS Commit
- `.env.example` (template only)
- Test files
- Documentation
- Configuration files

### If You Accidentally Commit a Secret

1. **Immediately** revoke/rotate the compromised key
2. Remove from git history:
```bash
# Install BFG Repo-Cleaner
brew install bfg  # Mac
# or download from https://rtyley.github.io/bfg-repo-cleaner/

# Remove secret from history
bfg --replace-text secrets.txt

# Force push (coordinate with team!)
git push --force
```

3. Update `.secrets.baseline`:
```bash
detect-secrets scan > .secrets.baseline
```

## Common Issues & Solutions

### Pre-commit Hook Failed
```bash
# See what failed
git commit -v

# Fix formatting issues
black .
ruff check --fix .

# Update secrets baseline if needed
detect-secrets scan --baseline .secrets.baseline

# Try again
git commit
```

### Test Failures
```bash
# Run with verbose output
pytest -v

# Run with print statements visible
pytest -s

# Drop into debugger on failure
pytest --pdb

# Run last failed tests only
pytest --lf
```

### Dependency Conflicts
```bash
# Clear pip cache
pip cache purge

# Reinstall from scratch
pip uninstall -r requirements.txt -y
pip install -r requirements.txt
```

### Secret Detected Incorrectly
```bash
# Audit detected secrets
detect-secrets audit .secrets.baseline

# Mark false positives as allowed
# Then commit the updated baseline
git add .secrets.baseline
git commit -m "Update secrets baseline"
```

## Security Best Practices

### API Key Management
1. Store in `.env` file (never commit!)
2. Use different keys for dev/staging/prod
3. Rotate keys regularly
4. Never hardcode in source files
5. Use key expiration when available

### Database Security
1. Use parameterized queries (SQLAlchemy does this)
2. Never store passwords in plaintext
3. Use connection pooling wisely
4. Keep database files out of git

### Testing Security
1. Never use real API keys in tests
2. Use mock data for sensitive info
3. Clean up test data after runs
4. Don't commit test databases

### Code Review
1. Check for hardcoded secrets
2. Verify .env usage
3. Look for SQL injection risks
4. Check file permission issues
5. Verify input validation

## Tools Reference

### Black (Code Formatter)
```bash
black .                    # Format all files
black --check .            # Check without modifying
black specific_file.py     # Format one file
```

### Ruff (Linter)
```bash
ruff check .              # Lint all files
ruff check --fix .        # Fix auto-fixable issues
ruff check --select S .   # Security checks only
```

### Bandit (Security Scanner)
```bash
bandit -r .               # Scan all files
bandit -r . -f json       # JSON output
bandit -c bandit.yml -r . # Use config file
```

### Safety (Dependency Scanner)
```bash
safety check              # Check for vulnerable deps
safety check --json       # JSON output
```

### Pytest (Testing)
```bash
pytest                    # Run all tests
pytest -v                 # Verbose output
pytest -s                 # Show print statements
pytest --cov=.            # With coverage
pytest -m unit            # Unit tests only
pytest -k "parser"        # Tests matching pattern
```

## Getting Help

### Pre-commit Issues
- Docs: https://pre-commit.com/
- Common errors: https://pre-commit.com/#common-errors

### Testing Help
- Pytest docs: https://docs.pytest.org/
- Coverage docs: https://coverage.readthedocs.io/

### Security Tools
- Bandit: https://bandit.readthedocs.io/
- Safety: https://pyup.io/safety/
- detect-secrets: https://github.com/Yelp/detect-secrets

## Emergency Contacts

If you discover a security vulnerability:
1. Do NOT commit the vulnerable code
2. Do NOT create a public GitHub issue
3. Contact the project maintainer directly
4. Document the issue privately

## Quick Commands Summary

```bash
# Daily workflow
pre-commit run --all-files  # Before committing
pytest                      # Run tests
black .                     # Format code
ruff check --fix .         # Fix linting issues

# Security scans
bandit -r .                # Security scan
safety check               # Dependency scan
detect-secrets scan        # Secret scan

# Testing
pytest -m unit             # Fast tests
pytest --cov=.             # With coverage
pytest -v -s               # Verbose with output
```

Remember: Security is everyone's responsibility!

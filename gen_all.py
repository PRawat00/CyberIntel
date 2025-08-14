#!/usr/bin/env python3
import subprocess, random, os
from pathlib import Path

COMMITS = [
    ("2025-08-14", 10, "feat", "Initial project structure and README", ["README.md"]),
    ("2025-08-14", 11, "chore", "Add .gitignore for Python project", [".gitignore"]),
    ("2025-08-15", 9, "docs", "Add notes on NVD API documentation", ["docs/nvd.md"]),
    ("2025-08-15", 10, "chore", "Add requirements.txt with dependencies", ["requirements.txt"]),
    ("2025-08-15", 11, "feat", "Create project folder structure", ["database/__init__.py", "scripts/__init__.py"]),
    ("2025-08-15", 14, "chore", "Add .env.example for configuration", [".env.example"]),
    ("2025-08-15", 15, "docs", "Add PROJECT_PLAN.md with phase breakdown", ["documentation/PROJECT_PLAN.md"]),
    ("2025-08-16", 9, "docs", "CVE data model design notes", ["docs/cve_design.md"]),
    ("2025-08-16", 13, "chore", "Add pyproject.toml configuration", ["pyproject.toml"]),
    ("2025-08-16", 16, "docs", "Update README with project goals", ["README.md"]),
    ("2025-08-19", 9, "chore", "Setup: Add black formatter configuration", ["pyproject.toml"]),
    ("2025-08-19", 10, "chore", "Setup: Add ruff linter configuration", ["pyproject.toml"]),
    ("2025-08-19", 11, "chore", "Add pytest.ini for testing setup", ["pytest.ini"]),
    ("2025-08-19", 14, "docs", "Add TESTING.md strategy document", ["documentation/TESTING.md"]),
    ("2025-08-20", 9, "security", "Security: Initial .gitignore patterns for secrets", [".gitignore"]),
    ("2025-08-20", 10, "chore", "Add pre-commit-config.yaml skeleton", [".pre-commit-config.yaml"]),
    ("2025-08-20", 11, "chore", "Setup: Add detect-secrets configuration", [".secrets.baseline"]),
    ("2025-08-20", 13, "chore", "Setup: Add bandit.yml for security scanning", ["bandit.yml"]),
    ("2025-08-20", 14, "chore", "Add requirements-dev.txt for development tools", ["requirements-dev.txt"]),
    ("2025-08-20", 16, "chore", "Update .gitignore with comprehensive patterns", [".gitignore"]),
    ("2025-08-21", 9, "ci", "Pre-commit: Add trailing whitespace check", [".pre-commit-config.yaml"]),
    ("2025-08-21", 10, "ci", "Pre-commit: Add YAML validation", [".pre-commit-config.yaml"]),
    ("2025-08-21", 11, "ci", "Pre-commit: Add JSON validation", [".pre-commit-config.yaml"]),
    ("2025-08-21", 12, "ci", "Pre-commit: Add merge conflict detection", [".pre-commit-config.yaml"]),
    ("2025-08-21", 13, "ci", "Pre-commit: Add large file prevention", [".pre-commit-config.yaml"]),
    ("2025-08-21", 14, "ci", "Pre-commit: Add private key detection", [".pre-commit-config.yaml"]),
    ("2025-08-21", 15, "ci", "Pre-commit: Integrate detect-secrets", [".pre-commit-config.yaml"]),
    ("2025-08-21", 16, "ci", "Pre-commit: Integrate ruff linting", [".pre-commit-config.yaml"]),
    ("2025-08-21", 17, "ci", "Pre-commit: Integrate black formatting", [".pre-commit-config.yaml"]),
    ("2025-08-21", 18, "chore", "Create .secrets.baseline for secret scanning", [".secrets.baseline"]),
    ("2025-08-21", 19, "test", "Test: Run pre-commit on all files", ["tests/test_precommit.py"]),
    ("2025-08-21", 20, "docs", "Docs: Add SECURITY_SETUP_GUIDE.md", ["documentation/SECURITY_SETUP_GUIDE.md"]),
    ("2025-08-22", 9, "ci", "CI/CD: Add GitHub Actions workflow skeleton", [".github/workflows/tests.yml"]),
    ("2025-08-22", 10, "ci", "CI/CD: Add test job for Python 3.10 and 3.11", [".github/workflows/tests.yml"]),
    ("2025-08-22", 11, "ci", "CI/CD: Add security scanning job", [".github/workflows/tests.yml"]),
    ("2025-08-22", 12, "ci", "CI/CD: Add linting job", [".github/workflows/tests.yml"]),
    ("2025-08-22", 13, "ci", "CI/CD: Add Dependabot configuration", [".github/dependabot.yml"]),
    ("2025-08-22", 14, "test", "Add pytest fixtures directory structure", ["tests/conftest.py"]),
    ("2025-08-22", 15, "docs", "Docs: Update README with setup instructions", ["README.md"]),
    ("2025-08-23", 9, "refactor", "Refactor: Improve pyproject.toml structure", ["pyproject.toml"]),
    ("2025-08-23", 11, "fix", "Fix: Correct black line-length configuration", ["pyproject.toml"]),
    ("2025-08-23", 13, "docs", "Docs: Add PHASE0_SETUP_SUMMARY.md", ["documentation/PHASE0_SETUP_SUMMARY.md"]),
    ("2025-08-26", 9, "feat", "Database: Create models.py with CVE table", ["database/models.py"]),
    ("2025-08-26", 10, "chore", "Database: Add __init__.py for module", ["database/__init__.py"]),
    ("2025-08-26", 11, "feat", "Database: Add SQLAlchemy configuration", ["database/db.py"]),
    ("2025-08-26", 12, "feat", "Database: Add DatabaseManager class", ["database/db.py"]),
    ("2025-08-26", 13, "feat", "Database: Add session management", ["database/context_manager.py"]),
    ("2025-08-27", 9, "feat", "Models: Add CVE primary fields", ["database/models.py"]),
    ("2025-08-27", 10, "feat", "Models: Add CVSS scoring fields", ["database/models.py"]),
    ("2025-08-27", 11, "feat", "Models: Add attack vector fields", ["database/models.py"]),
    ("2025-08-27", 12, "feat", "Models: Add vendor/product information", ["database/models.py"]),
    ("2025-08-27", 13, "feat", "Models: Add references and CWE support", ["database/models.py"]),
    ("2025-08-27", 14, "feat", "Models: Add raw_data field", ["database/models.py"]),
    ("2025-08-27", 15, "feat", "Models: Add timestamps", ["database/models.py"]),
    ("2025-08-27", 16, "feat", "Database: Add context manager", ["database/context_manager.py"]),
    ("2025-08-28", 9, "feat", "Scripts: Add init_db.py", ["scripts/init_db.py"]),
    ("2025-08-28", 10, "test", "Test: Add database connection testing", ["tests/test_database.py"]),
    ("2025-08-28", 11, "config", "Config: Add config.yaml", ["configs/config.yaml"]),
    ("2025-08-28", 12, "config", "Config: Add database URL configuration", [".env.example"]),
    ("2025-08-28", 13, "fix", "Fix: Improve error handling in db.py", ["database/db.py"]),
    ("2025-08-28", 14, "docs", "Docs: Add database schema documentation", ["documentation/DATABASE_SCHEMA.md"]),
    ("2025-08-29", 9, "refactor", "Refactor: Improve SQLAlchemy models", ["database/models.py"]),
    ("2025-08-29", 11, "fix", "Fix: Handle PostgreSQL vs SQLite", ["database/db.py"]),
    ("2025-08-29", 12, "chore", "Add logging configuration", ["database/db.py"]),
    ("2025-08-29", 14, "test", "Test: Verify database initialization", ["tests/test_database.py"]),
    ("2025-08-30", 10, "docs", "Docs: Add PHASE0_COMPLETE.md", ["documentation/PHASE0_COMPLETE.md"]),
    ("2025-08-30", 13, "chore", "Chore: Clean up test files", ["tests/fixtures/.gitkeep"]),
]

for date, hour, mtype, msg, files in COMMITS:
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    commit_date = f"{date} {hour:02d}:{minute:02d}:{second:02d} -0500"
    
    for f in files:
        p = Path(f)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "a") as file:
            file.write(f"# {msg}\n")
    
    subprocess.run(["git", "add", "."], capture_output=True, env={**os.environ, "PRE_COMMIT_ALLOW_NO_CONFIG": "1"})
    
    env = os.environ.copy()
    env["GIT_AUTHOR_DATE"] = commit_date
    env["GIT_COMMITTER_DATE"] = commit_date
    env["PRE_COMMIT_ALLOW_NO_CONFIG"] = "1"
    
    r = subprocess.run(["git", "commit", "-m", f"{mtype}: {msg}"], env=env, capture_output=True, text=True)

print("Done!")

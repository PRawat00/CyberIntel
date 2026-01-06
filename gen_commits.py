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
]

subprocess.run(["git", "config", "user.email", "prawat@example.com"], capture_output=True)
subprocess.run(["git", "config", "user.name", "Priyanshu Rawat"], capture_output=True)

for date, hour, mtype, msg, files in COMMITS:
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    commit_date = f"{date} {hour:02d}:{minute:02d}:{second:02d} -0500"
    
    for f in files:
        Path(f).parent.mkdir(parents=True, exist_ok=True)
        with open(f, "a") as file:
            file.write(f"# {msg}\n")
    
    subprocess.run(["git", "add", "."], capture_output=True)
    
    env = os.environ.copy()
    env["GIT_AUTHOR_DATE"] = commit_date
    env["GIT_COMMITTER_DATE"] = commit_date
    
    r = subprocess.run(["git", "commit", "-m", f"{mtype}: {msg}"], env=env, capture_output=True, text=True)
    if r.returncode == 0:
        print(f"✓ {date} {hour:02d}:xx {msg[:50]}")
    else:
        print(f"✗ ERROR: {msg}")
        break

print("\nDone! Run: git log --oneline | head -20")

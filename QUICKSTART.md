# Quick Start Guide - CyberIntel Summarizer

## Phase 1: Getting Started (10 minutes)

### Step 1: Clone and Navigate
```bash
cd "/Users/prawat/Local/Repositories/CyberIntel Summarizer"
```

### Step 2: Set Up Environment
```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # On macOS/Linux
# venv\Scripts\activate   # On Windows

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Configure (Optional)
```bash
# Copy environment template
cp .env.example .env

# Edit .env if you have an NVD API key (optional but recommended)
# This increases rate limit from 5 to 50 requests per 30 seconds
nano .env  # or use your favorite editor
```

To get an NVD API key (free): https://nvd.nist.gov/developers/request-an-api-key

### Step 4: Initialize Database
```bash
python -m scripts.init_db
```

**Expected output:**
```
╭─────────────────────────────────────────────────╮
│ CyberIntel Summarizer - Database Initialization │
╰─────────────────────────────────────────────────╯

Loading configuration...
Creating database tables...

✓ Database initialized successfully!
Database location: sqlite:///cyberintel.db
```

### Step 5: Verify Setup
```bash
python -m scripts.verify_setup
```

This checks that everything is working correctly.

### Step 6: Fetch CVEs
```bash
# Fetch CVEs from the last 7 days
python -m scripts.fetch_nvd --days 7
```

**Expected output:**
```
╭─────────────────────────────────────────╮
│ CyberIntel Summarizer - NVD CVE Fetcher │
╰─────────────────────────────────────────╯

Initializing database...
Initializing NVD fetcher...

Fetching CVEs from last 7 days...

✓ Fetched 100+ CVEs from NVD

Storing CVEs in database...

✓ Operation completed!
```

### Step 7: Explore Your Data

You can query the database directly:

```python
python -c "
from database.db import get_db_manager
from database.models import CVE

db = get_db_manager()
with db.session_scope() as session:
    # Get total count
    total = session.query(CVE).count()
    print(f'Total CVEs: {total}')

    # Get critical CVEs
    critical = session.query(CVE).filter(CVE.severity == 'CRITICAL').all()
    print(f'\nCritical CVEs ({len(critical)}):')
    for cve in critical[:5]:  # Show first 5
        print(f'  {cve.cve_id}: {cve.description[:60]}...')
"
```

## Common Commands

### Fetch Different Time Ranges
```bash
# Last 3 days
python -m scripts.fetch_nvd --days 3

# Last 30 days (with limit)
python -m scripts.fetch_nvd --days 30 --limit 500
```

### Fetch Specific CVE
```bash
python -m scripts.fetch_nvd --cve-id CVE-2025-1234
```

### Update Existing CVEs
```bash
# Re-run the fetch command - it will update modified CVEs automatically
python -m scripts.fetch_nvd --days 7
```

### Enable Verbose Logging
```bash
python -m scripts.fetch_nvd --days 7 --verbose
```

## Database Location

The SQLite database is stored at: `cyberintel.db` in the project root.

You can inspect it with:
```bash
sqlite3 cyberintel.db
```

SQLite commands:
```sql
-- View tables
.tables

-- Count CVEs
SELECT COUNT(*) FROM cves;

-- View critical CVEs
SELECT cve_id, severity, cvss_score, description
FROM cves
WHERE severity = 'CRITICAL'
LIMIT 10;

-- View by vendor
SELECT vendor, COUNT(*) as count
FROM cves
WHERE vendor IS NOT NULL
GROUP BY vendor
ORDER BY count DESC
LIMIT 10;

-- Exit
.quit
```

## Troubleshooting

### Issue: "Configuration file not found"
**Solution**: Make sure you're running commands from the project root directory.

### Issue: Rate limit errors
**Solution**:
1. Get an NVD API key (free): https://nvd.nist.gov/developers/request-an-api-key
2. Add it to `.env`: `NVD_API_KEY=your_key_here`
3. This increases limit from 5 to 50 requests per 30 seconds

### Issue: "No module named 'database'"
**Solution**: Make sure you're running commands with `python -m scripts.X` format, not `python scripts/X.py`

### Issue: Virtual environment not activated
**Solution**: Run `source venv/bin/activate` (macOS/Linux) or `venv\Scripts\activate` (Windows)

## Next Steps

Now that Phase 1 is complete, you can:

1. **Explore the data**: Query the database to understand CVE patterns
2. **Customize**: Modify `configs/config.yaml` for your needs
3. **Proceed to Phase 2**: Set up LLM summarization (see PROJECT_PLAN.md)

## Project Structure

```
CyberIntel Summarizer/
├── configs/              # Configuration files
├── data_ingestion/       # Data fetchers (NVD, CISA, etc.)
├── database/             # Database models and connection
├── scripts/              # CLI tools
├── logs/                 # Log files
├── cyberintel.db         # SQLite database (created after init)
├── requirements.txt      # Python dependencies
├── PROJECT_PLAN.md       # Full 6-phase plan
└── PHASE1_COMPLETE.md    # Phase 1 summary
```

## Help

For detailed implementation plan: See `PROJECT_PLAN.md`
For Phase 1 completion summary: See `PHASE1_COMPLETE.md`

For questions or issues, check the logs in `logs/fetch_nvd.log`

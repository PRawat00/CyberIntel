# Test Sample Files

This directory contains sample dependency files for testing the CyberIntel scanner.

## Files

### 1. vulnerable-package-lock.json (npm/Node.js)

**Contains 10 packages with known vulnerabilities:**

- **express 4.16.0** - Old version with security issues
- **lodash 4.17.19** - Has prototype pollution vulnerabilities
- **axios 0.18.0** - SSRF and other vulnerabilities
- **jquery 3.3.1** - XSS vulnerabilities
- **moment 2.24.0** - ReDoS vulnerabilities
- **node-fetch 2.6.0** - Has size limit vulnerabilities
- **minimist 1.2.0** - Prototype pollution
- **qs 6.5.2** - DoS vulnerabilities
- **debug 2.6.8** - ReDoS vulnerabilities
- **handlebars 4.0.11** - Template injection vulnerabilities

**Expected Results:**
- Multiple HIGH and CRITICAL severity CVEs
- Prototype pollution warnings
- XSS vulnerabilities
- Remote code execution risks
- Should show variety of severity levels

### 2. vulnerable-requirements.txt (Python/pip)

**Contains 15 packages with known vulnerabilities:**

- **django 2.2.0** - SQL injection, XSS, CSRF bypasses
- **requests 2.20.0** - SSRF vulnerabilities
- **flask 0.12.2** - Security bypasses
- **jinja2 2.10** - Sandbox escape
- **pyyaml 3.13** - Arbitrary code execution
- **urllib3 1.24.1** - Request smuggling
- **pillow 5.4.1** - Buffer overflow, DoS
- **cryptography 2.3** - Cryptographic issues
- **werkzeug 0.14.1** - Path traversal
- **sqlalchemy 1.2.0** - SQL injection
- **celery 4.2.0** - Command injection
- **paramiko 2.4.0** - Authentication bypass
- **beautifulsoup4 4.6.0** - ReDoS
- **lxml 4.2.1** - XXE vulnerabilities
- **simplejson 3.15.0** - DoS vulnerabilities

**Expected Results:**
- CRITICAL vulnerabilities (arbitrary code execution)
- HIGH severity issues (SQL injection, XSS)
- Mix of different vulnerability types
- Should demonstrate severity breakdown chart

### 3. package-lock.json (if exists)

**Your actual project dependencies** - May have few or no vulnerabilities depending on versions.

## How to Test

### Test 1: Clean File (Low/No Vulnerabilities)
```bash
# Upload your actual package-lock.json
# Expected: Few or no vulnerabilities found
```

### Test 2: Vulnerable npm File (HIGH/CRITICAL)
```bash
# Upload: vulnerable-package-lock.json
# Expected:
# - 10 dependencies scanned
# - Multiple CVEs found
# - Critical and High severity alerts
# - Prototype pollution warnings
# - XSS and injection vulnerabilities
```

### Test 3: Vulnerable Python File (CRITICAL)
```bash
# Upload: vulnerable-requirements.txt
# Expected:
# - 15 dependencies scanned
# - Many CVEs (20+)
# - Critical severity (arbitrary code execution)
# - SQL injection, XSS warnings
# - Cryptographic vulnerabilities
```

## What You'll See in the UI

### Upload Page
1. Drag and drop file
2. Progress bar
3. Success message with CVE count

### Dashboard
- Total scans count
- Total vulnerable dependencies
- Total CVEs found
- Critical CVE count
- Severity breakdown pie chart
- Recent scans list

### Scan Results Page
For each scan, you'll see:

**Summary Section:**
- File name and type
- Scan date
- Total dependencies
- Vulnerable count
- Total CVEs
- Severity counts (Critical, High, Medium, Low)

**Severity Breakdown:**
- Visual progress bars
- Percentage by severity
- Color-coded (red for critical, orange for high, etc.)

**Vulnerability Table:**
- Sortable columns (package name, version, severity)
- Filter by severity
- Search functionality
- Pagination
- CVE count per package
- Click CVE ID for details

**CVE Details Dialog:**
- CVE ID and description
- CVSS score
- Severity level
- Publication date
- Links to NVD database

**Export Options:**
- JSON (machine-readable)
- CSV (spreadsheet)
- HTML (printable report)

## Expected Severity Breakdown

### vulnerable-package-lock.json
- **Critical**: 2-5 CVEs (RCE, auth bypass)
- **High**: 5-10 CVEs (XSS, SSRF, prototype pollution)
- **Medium**: 10-15 CVEs (DoS, ReDoS)
- **Low**: 5-10 CVEs (information disclosure)

### vulnerable-requirements.txt
- **Critical**: 5-10 CVEs (arbitrary code execution, SQL injection)
- **High**: 10-20 CVEs (XSS, CSRF, XXE)
- **Medium**: 15-25 CVEs (DoS, path traversal)
- **Low**: 10-15 CVEs (information disclosure)

## Testing Workflow

1. **Start Application**
   ```bash
   ./start.sh
   ```

2. **Test Upload - Vulnerable npm File**
   - Go to http://localhost:3000/upload
   - Upload `vulnerable-package-lock.json`
   - Wait for scan to complete
   - Verify you see multiple critical vulnerabilities

3. **Test Dashboard**
   - Go to http://localhost:3000/dashboard
   - Check stats update (total scans, CVEs, etc.)
   - Verify severity chart shows data
   - Check recent scans list

4. **Test Scan Details**
   - Click on a scan from recent list
   - Verify vulnerability table loads
   - Test sorting (click column headers)
   - Test filtering (severity dropdown)
   - Test search (type package name)
   - Test pagination (if >10 items)

5. **Test CVE Details**
   - Click a CVE ID in the table
   - Verify dialog opens with details
   - Check external link works
   - Close dialog

6. **Test Export**
   - Click Export button
   - Try JSON format
   - Try CSV format
   - Try HTML format
   - Verify file downloads

7. **Test Upload - Vulnerable Python File**
   - Go back to Upload page
   - Upload `vulnerable-requirements.txt`
   - Compare results with npm file

8. **Test Navigation**
   - Use navbar to switch between pages
   - Verify active page highlighting
   - Test mobile menu (resize browser)

## Troubleshooting

### No CVEs Found
- Check if NVD database has data
- Run: `python scripts/update_nvd.py` to fetch latest CVEs
- Verify database file exists: `cyberintel.db`

### Upload Fails
- Check API logs: `tail -f /tmp/securechat-api.log`
- Verify file format is correct (valid JSON for npm, valid txt for pip)
- Check file size (max 1MB)

### Parsers Don't Recognize File
- Ensure filename matches expected patterns
- npm: must be named `package-lock.json` or `package.json`
- pip: must be named `requirements.txt` or `Pipfile`

## Notes

These test files use **intentionally old versions** with known vulnerabilities for testing purposes.

**DO NOT USE THESE VERSIONS IN PRODUCTION!**

The vulnerabilities include:
- Remote Code Execution (RCE)
- SQL Injection
- Cross-Site Scripting (XSS)
- Server-Side Request Forgery (SSRF)
- Prototype Pollution
- XML External Entity (XXE)
- Path Traversal
- Denial of Service (DoS)
- Authentication Bypass
- Cryptographic Weaknesses

These are real vulnerabilities that exist in these old versions. Always use the latest stable versions in production applications.

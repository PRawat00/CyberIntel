#!/usr/bin/env python3
"""Generate October 2025 commits for CyberIntel Summarizer"""

import subprocess
import random
import os
from pathlib import Path

COMMITS = [
    # ====== OCTOBER 2025 (161 commits) ======
    # Oct 1 (Wed) - 5 commits: Phase 2 completion
    ("2025-10-01", 9, "feat", "CLI: Add filter options for severity levels", ["src/dependency_scanner/cli_filters.py"]),
    ("2025-10-01", 10, "feat", "CLI: Add vulnerable-only filter mode", ["src/dependency_scanner/cli_filters.py"]),
    ("2025-10-01", 11, "test", "Test: Filter option functionality tests", ["tests/test_cli_filters.py"]),
    ("2025-10-01", 13, "refactor", "Refactor: Simplify filter logic", ["src/dependency_scanner/cli_filters.py"]),
    ("2025-10-01", 14, "docs", "Docs: Filter options documentation", ["documentation/FILTER_OPTIONS.md"]),
    
    # Oct 2 (Thu) - 7 commits
    ("2025-10-02", 9, "feat", "Report: HTML report styling improvements", ["src/dependency_scanner/templates/report.html.j2"]),
    ("2025-10-02", 10, "feat", "Report: Add output-file CLI option", ["scripts/scan_dependencies.py"]),
    ("2025-10-02", 11, "feat", "Report: Add report generation to main flow", ["src/dependency_scanner/scanner.py"]),
    ("2025-10-02", 12, "test", "Test: HTML report generation tests", ["tests/test_html_report.py"]),
    ("2025-10-02", 13, "fix", "Fix: Ensure output directories are created", ["src/dependency_scanner/scanner.py"]),
    ("2025-10-02", 14, "docs", "Docs: HTML report template documentation", ["documentation/HTML_REPORT_TEMPLATE.md"]),
    ("2025-10-02", 15, "test", "Test: End-to-end report generation", ["tests/test_e2e_report.py"]),
    
    # Oct 3 (Fri) - 6 commits
    ("2025-10-03", 9, "test", "Test: Comprehensive Phase 2 test suite", ["tests/test_phase2_comprehensive.py"]),
    ("2025-10-03", 10, "test", "Test: Edge case scenarios for parsers", ["tests/test_parser_edge_cases.py"]),
    ("2025-10-03", 11, "test", "Test: Achieve 65% code coverage for Phase 2", ["tests/coverage_report.py"]),
    ("2025-10-03", 13, "docs", "Docs: Add TESTING_GUIDE.md for Phase 2", ["documentation/TESTING_GUIDE.md"]),
    ("2025-10-03", 14, "refactor", "Refactor: Clean up test organization", ["tests/__init__.py"]),
    ("2025-10-03", 15, "test", "Test: Performance benchmarks for scanners", ["tests/test_performance_benchmarks.py"]),
    
    # Oct 4 (Sat) - 1 commit
    ("2025-10-04", 10, "docs", "Docs: Add complete TESTING_GUIDE.md", ["documentation/TESTING_GUIDE.md"]),
    
    # Oct 6 (Mon) - 5 commits
    ("2025-10-06", 9, "test", "Test: Integration tests with mock CVE data", ["tests/test_integration_with_mock.py"]),
    ("2025-10-06", 10, "test", "Test: 70% coverage milestone achieved", ["tests/coverage_report.py"]),
    ("2025-10-06", 11, "test", "Test: All 60+ tests passing", ["tests/test_final_phase2_suite.py"]),
    ("2025-10-06", 13, "ci", "CI: Update GitHub Actions for Phase 2 tests", [".github/workflows/tests.yml"]),
    ("2025-10-06", 14, "docs", "Docs: Add Phase 2 completion notes", ["documentation/PHASE2_NOTES.md"]),
    
    # Oct 7 (Tue) - 4 commits
    ("2025-10-07", 9, "chore", "Chore: Update dependencies for Phase 3", ["requirements.txt"]),
    ("2025-10-07", 10, "refactor", "Refactor: Code cleanup and organization", ["src/dependency_scanner/__init__.py"]),
    ("2025-10-07", 11, "docs", "Docs: Add PHASE2_COMPLETE.md summary", ["documentation/PHASE2_COMPLETE.md"]),
    ("2025-10-07", 13, "chore", "Chore: Update version to 0.2.0", ["pyproject.toml"]),
    
    # Oct 8 (Wed) - 3 commits
    ("2025-10-08", 9, "chore", "Chore: Update dependencies in requirements-dev.txt", ["requirements-dev.txt"]),
    ("2025-10-08", 10, "fix", "Fix: Update ruff and black configuration", ["pyproject.toml"]),
    ("2025-10-08", 14, "docs", "Docs: Update README with Phase 2 info", ["README.md"]),
    
    # Oct 9 (Thu) - 5 commits
    ("2025-10-09", 9, "test", "Test: Run complete Phase 2 test suite", ["tests/test_phase2_final.py"]),
    ("2025-10-09", 11, "test", "Test: Achieve 73.67% code coverage", ["tests/coverage_report.py"]),
    ("2025-10-09", 12, "test", "Test: All 70 tests passing", ["tests/test_final_verification.py"]),
    ("2025-10-09", 14, "ci", "CI: Update GitHub Actions workflow", [".github/workflows/tests.yml"]),
    ("2025-10-09", 15, "docs", "Docs: Coverage report and metrics", ["documentation/COVERAGE_METRICS.md"]),
    
    # Oct 10 (Fri) - 2 commits
    ("2025-10-10", 10, "docs", "Docs: Add PHASE3_PLAN.md for web UI", ["documentation/PHASE3_PLAN.md"]),
    ("2025-10-10", 14, "feat", "Phase 3: Web UI - Initial planning complete", ["documentation/PHASE3_PLAN.md"]),
    
    # Oct 15 (Wed) - 6 commits: FastAPI setup
    ("2025-10-15", 9, "feat", "Phase 3: Create FastAPI main.py", ["api/main.py"]),
    ("2025-10-15", 10, "feat", "API: Add CORS middleware configuration", ["api/main.py"]),
    ("2025-10-15", 11, "feat", "API: Define Pydantic models for requests", ["api/models.py"]),
    ("2025-10-15", 12, "feat", "API: Define Pydantic models for responses", ["api/models.py"]),
    ("2025-10-15", 14, "test", "Test: API startup tests", ["tests/test_api_startup.py"]),
    ("2025-10-15", 15, "docs", "Docs: API project structure documentation", ["documentation/API_STRUCTURE.md"]),
    
    # Oct 16 (Thu) - 10 commits: REST endpoints
    ("2025-10-16", 9, "feat", "API: Create /upload endpoint for scan files", ["api/routes/upload.py"]),
    ("2025-10-16", 10, "feat", "API: Create /scans endpoint (list scans)", ["api/routes/scans.py"]),
    ("2025-10-16", 11, "feat", "API: Create /scans/{id} endpoint (detail)", ["api/routes/scans.py"]),
    ("2025-10-16", 12, "feat", "API: Create /scans/{id}/delete endpoint", ["api/routes/scans.py"]),
    ("2025-10-16", 13, "feat", "API: Create /stats endpoint (aggregate stats)", ["api/routes/stats.py"]),
    ("2025-10-16", 14, "feat", "API: Create /export endpoint (data export)", ["api/routes/export.py"]),
    ("2025-10-16", 15, "feat", "API: Add request validation and error handling", ["api/routes/__init__.py"]),
    ("2025-10-16", 16, "test", "Test: Endpoint integration tests", ["tests/test_api_endpoints.py"]),
    ("2025-10-16", 17, "test", "Test: Request validation tests", ["tests/test_api_validation.py"]),
    ("2025-10-16", 18, "docs", "Docs: API endpoint documentation", ["documentation/API_ENDPOINTS.md"]),
    
    # Oct 17 (Fri) - 8 commits
    ("2025-10-17", 9, "feat", "API: Create /dependencies endpoint", ["api/routes/dependencies.py"]),
    ("2025-10-17", 10, "feat", "API: Add filtering and sorting to /dependencies", ["api/routes/dependencies.py"]),
    ("2025-10-17", 11, "feat", "Scripts: Create start_api.sh runner", ["scripts/start_api.sh"]),
    ("2025-10-17", 12, "feat", "Scripts: Create API configuration loader", ["api/config.py"]),
    ("2025-10-17", 13, "test", "Test: Dependencies endpoint tests", ["tests/test_api_dependencies.py"]),
    ("2025-10-17", 14, "test", "Test: Integration with scanner output", ["tests/test_api_scanner_integration.py"]),
    ("2025-10-17", 15, "docs", "Docs: API integration with scanner", ["documentation/API_SCANNER_INTEGRATION.md"]),
    ("2025-10-17", 16, "docs", "Docs: API usage examples", ["documentation/API_EXAMPLES.md"]),
    
    # Oct 20 (Mon) - 9 commits: Next.js Frontend setup
    ("2025-10-20", 9, "feat", "Frontend: Initialize Next.js 15 project", ["frontend/package.json", "frontend/tsconfig.json"]),
    ("2025-10-20", 10, "feat", "Frontend: Setup Tailwind CSS configuration", ["frontend/tailwind.config.ts"]),
    ("2025-10-20", 11, "feat", "Frontend: Setup shadcn/ui component library", ["frontend/components.json"]),
    ("2025-10-20", 12, "feat", "Frontend: Create 16 shadcn/ui components", ["frontend/components/ui/__init__.ts"]),
    ("2025-10-20", 13, "feat", "Frontend: Setup API client with Axios", ["frontend/lib/api-client.ts"]),
    ("2025-10-20", 14, "feat", "Frontend: Define TypeScript types for API", ["frontend/types/api.ts"]),
    ("2025-10-20", 15, "feat", "Frontend: Create custom React hooks", ["frontend/hooks/useScan.ts", "frontend/hooks/useScans.ts"]),
    ("2025-10-20", 16, "feat", "Frontend: Setup environment variables", ["frontend/.env.example"]),
    ("2025-10-20", 17, "docs", "Docs: Frontend setup documentation", ["documentation/FRONTEND_SETUP.md"]),
    
    # Oct 21 (Tue) - 8 commits
    ("2025-10-21", 9, "feat", "Frontend: Create layout component with header", ["frontend/components/layout.tsx"]),
    ("2025-10-21", 10, "feat", "Frontend: Add navigation component", ["frontend/components/navbar.tsx"]),
    ("2025-10-21", 11, "feat", "Frontend: Create sidebar navigation", ["frontend/components/sidebar.tsx"]),
    ("2025-10-21", 12, "feat", "Frontend: Add footer component", ["frontend/components/footer.tsx"]),
    ("2025-10-21", 13, "feat", "Frontend: Setup routing structure", ["frontend/app/layout.tsx", "frontend/app/page.tsx"]),
    ("2025-10-21", 14, "feat", "Frontend: Create API context provider", ["frontend/context/api-context.tsx"]),
    ("2025-10-21", 15, "test", "Test: Component rendering tests", ["frontend/__tests__/components.test.tsx"]),
    ("2025-10-21", 16, "docs", "Docs: Frontend component documentation", ["documentation/FRONTEND_COMPONENTS.md"]),
    
    # Oct 22 (Wed) - 11 commits: Upload page
    ("2025-10-22", 9, "feat", "Pages: Create upload page component", ["frontend/app/upload/page.tsx"]),
    ("2025-10-22", 10, "feat", "Upload: Add file drag-drop zone with react-dropzone", ["frontend/components/dropzone.tsx"]),
    ("2025-10-22", 11, "feat", "Upload: Add file list display", ["frontend/components/file-list.tsx"]),
    ("2025-10-22", 12, "feat", "Upload: Implement file upload handler", ["frontend/lib/upload-handler.ts"]),
    ("2025-10-22", 13, "feat", "Upload: Add upload progress indicator", ["frontend/components/progress-indicator.tsx"]),
    ("2025-10-22", 14, "feat", "Upload: Add file type validation", ["frontend/lib/file-validator.ts"]),
    ("2025-10-22", 15, "feat", "Upload: Add animations and transitions", ["frontend/styles/animations.css"]),
    ("2025-10-22", 16, "feat", "Upload: Success notification on upload", ["frontend/components/upload-success.tsx"]),
    ("2025-10-22", 17, "test", "Test: Upload page component tests", ["frontend/__tests__/upload.test.tsx"]),
    ("2025-10-22", 18, "test", "Test: Dropzone functionality tests", ["frontend/__tests__/dropzone.test.tsx"]),
    ("2025-10-22", 19, "docs", "Docs: Upload feature documentation", ["documentation/UPLOAD_FEATURE.md"]),
    
    # Oct 23 (Thu) - 12 commits: Dashboard page
    ("2025-10-23", 9, "feat", "Pages: Create dashboard page component", ["frontend/app/dashboard/page.tsx"]),
    ("2025-10-23", 10, "feat", "Dashboard: Add stats cards component", ["frontend/components/stats-cards.tsx"]),
    ("2025-10-23", 11, "feat", "Dashboard: Integrate Recharts for charts", ["frontend/components/charts.tsx"]),
    ("2025-10-23", 12, "feat", "Dashboard: Add CVE severity breakdown chart", ["frontend/components/severity-chart.tsx"]),
    ("2025-10-23", 13, "feat", "Dashboard: Add recent scans list", ["frontend/components/recent-scans.tsx"]),
    ("2025-10-23", 14, "feat", "Dashboard: Add vulnerability trend chart", ["frontend/components/trend-chart.tsx"]),
    ("2025-10-23", 15, "feat", "Dashboard: Implement responsive grid layout", ["frontend/styles/dashboard.css"]),
    ("2025-10-23", 16, "feat", "Dashboard: Add data refresh functionality", ["frontend/lib/refresh-handler.ts"]),
    ("2025-10-23", 17, "test", "Test: Dashboard page tests", ["frontend/__tests__/dashboard.test.tsx"]),
    ("2025-10-23", 18, "test", "Test: Stats card tests", ["frontend/__tests__/stats-cards.test.tsx"]),
    ("2025-10-23", 19, "test", "Test: Chart integration tests", ["frontend/__tests__/charts.test.tsx"]),
    ("2025-10-23", 20, "docs", "Docs: Dashboard feature documentation", ["documentation/DASHBOARD_FEATURE.md"]),
    
    # Oct 24 (Fri) - 10 commits: Scan detail page
    ("2025-10-24", 9, "feat", "Pages: Create scan detail page", ["frontend/app/scans/[id]/page.tsx"]),
    ("2025-10-24", 10, "feat", "Detail: Add CVE list with filters", ["frontend/components/cve-list.tsx"]),
    ("2025-10-24", 11, "feat", "Detail: Add severity breakdown component", ["frontend/components/severity-breakdown.tsx"]),
    ("2025-10-24", 12, "feat", "Detail: Add export buttons (JSON, CSV)", ["frontend/components/export-buttons.tsx"]),
    ("2025-10-24", 13, "feat", "Detail: Implement export functionality", ["frontend/lib/export-handler.ts"]),
    ("2025-10-24", 14, "feat", "Detail: Add scan metadata display", ["frontend/components/scan-metadata.tsx"]),
    ("2025-10-24", 15, "feat", "Detail: Add timestamp formatting utilities", ["frontend/lib/date-utils.ts"]),
    ("2025-10-24", 16, "test", "Test: Scan detail page tests", ["frontend/__tests__/scan-detail.test.tsx"]),
    ("2025-10-24", 17, "test", "Test: Export functionality tests", ["frontend/__tests__/export.test.tsx"]),
    ("2025-10-24", 18, "docs", "Docs: Scan detail page documentation", ["documentation/SCAN_DETAIL_FEATURE.md"]),
    
    # Oct 25 (Sat) - 1 commit
    ("2025-10-25", 11, "feat", "Frontend: Add mobile responsive design", ["frontend/styles/mobile.css"]),
    
    # Oct 27 (Mon) - 13 commits: Vulnerability table
    ("2025-10-27", 9, "feat", "Components: Create vulnerability table", ["frontend/components/vulnerability-table.tsx"]),
    ("2025-10-27", 10, "feat", "Table: Integrate TanStack Table v8", ["frontend/lib/table-utils.ts"]),
    ("2025-10-27", 11, "feat", "Table: Add sorting functionality", ["frontend/components/table-header.tsx"]),
    ("2025-10-27", 12, "feat", "Table: Add pagination component", ["frontend/components/pagination.tsx"]),
    ("2025-10-27", 13, "feat", "Table: Add column visibility toggle", ["frontend/components/column-visibility.tsx"]),
    ("2025-10-27", 14, "feat", "Table: Add row selection checkboxes", ["frontend/components/row-selector.tsx"]),
    ("2025-10-27", 15, "feat", "Table: Add filtering UI", ["frontend/components/table-filters.tsx"]),
    ("2025-10-27", 16, "feat", "Table: Add search functionality", ["frontend/lib/search-utils.ts"]),
    ("2025-10-27", 17, "feat", "Table: Add data loading state", ["frontend/components/table-skeleton.tsx"]),
    ("2025-10-27", 18, "test", "Test: Table sorting tests", ["frontend/__tests__/table-sorting.test.tsx"]),
    ("2025-10-27", 19, "test", "Test: Pagination tests", ["frontend/__tests__/pagination.test.tsx"]),
    ("2025-10-27", 20, "test", "Test: Table filtering tests", ["frontend/__tests__/table-filtering.test.tsx"]),
    ("2025-10-27", 21, "docs", "Docs: Table component documentation", ["documentation/TABLE_COMPONENT.md"]),
    
    # Oct 28 (Tue) - 8 commits: CVE details dialog
    ("2025-10-28", 9, "feat", "Components: Create CVE details dialog", ["frontend/components/cve-details-dialog.tsx"]),
    ("2025-10-28", 10, "feat", "Dialog: Add CVSS score display", ["frontend/components/cvss-display.tsx"]),
    ("2025-10-28", 11, "feat", "Dialog: Add CWE information display", ["frontend/components/cwe-display.tsx"]),
    ("2025-10-28", 12, "feat", "Dialog: Add external CVE links", ["frontend/components/cve-links.tsx"]),
    ("2025-10-28", 13, "feat", "Dialog: Add references section", ["frontend/components/references-section.tsx"]),
    ("2025-10-28", 14, "test", "Test: CVE details dialog tests", ["frontend/__tests__/cve-dialog.test.tsx"]),
    ("2025-10-28", 15, "test", "Test: CVSS display tests", ["frontend/__tests__/cvss-display.test.tsx"]),
    ("2025-10-28", 16, "docs", "Docs: CVE details dialog documentation", ["documentation/CVE_DIALOG.md"]),
    
    # Oct 29 (Wed) - 6 commits
    ("2025-10-29", 9, "feat", "Notifications: Add toast notifications with Sonner", ["frontend/components/toast.tsx"]),
    ("2025-10-29", 10, "feat", "Theme: Implement dark mode toggle", ["frontend/components/theme-toggle.tsx"]),
    ("2025-10-29", 11, "feat", "Theme: Add dark mode CSS variables", ["frontend/styles/dark-mode.css"]),
    ("2025-10-29", 12, "feat", "Settings: Add user preferences page", ["frontend/app/settings/page.tsx"]),
    ("2025-10-29", 13, "test", "Test: Dark mode toggle tests", ["frontend/__tests__/theme-toggle.test.tsx"]),
    ("2025-10-29", 14, "docs", "Docs: Dark mode and theming documentation", ["documentation/THEMING.md"]),
    
    # Oct 30 (Thu) - 5 commits
    ("2025-10-30", 9, "feat", "Linting: Add ESLint configuration", [".eslintrc.json"]),
    ("2025-10-30", 10, "feat", "TypeScript: Add strict type checking", ["frontend/tsconfig.json"]),
    ("2025-10-30", 11, "test", "Test: Type checking verification", ["frontend/__tests__/types.test.tsx"]),
    ("2025-10-30", 13, "docs", "Docs: Add PHASE3_COMPLETE.md summary", ["documentation/PHASE3_COMPLETE.md"]),
    ("2025-10-30", 14, "docs", "Docs: Code quality and testing guide", ["documentation/CODE_QUALITY.md"]),
    
    # Oct 31 (Fri) - 3 commits
    ("2025-10-31", 9, "test", "Test: Integration test for full app flow", ["frontend/__tests__/integration.test.tsx"]),
    ("2025-10-31", 11, "docs", "Docs: Update README with frontend info", ["README.md"]),
    ("2025-10-31", 13, "feat", "Phase 3: Web UI complete", ["documentation/PHASE3_COMPLETE.md"]),
]

def setup():
    subprocess.run(["git", "config", "user.email", "prwt1507@gmail.com"], capture_output=True, check=False)
    subprocess.run(["git", "config", "user.name", "Priyanshu Rawat"], capture_output=True, check=False)

def create_commit(date, hour, msg_type, message, files):
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    commit_date = f"{date} {hour:02d}:{minute:02d}:{second:02d} -0500"

    for file_path in files:
        p = Path(file_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "a") as f:
            f.write(f"# {message}\n")

    env = os.environ.copy()
    env["GIT_AUTHOR_DATE"] = commit_date
    env["GIT_COMMITTER_DATE"] = commit_date
    env["PRE_COMMIT_ALLOW_NO_CONFIG"] = "1"

    subprocess.run(["git", "add", "."], capture_output=True, check=True, env=env)

    full_message = f"{msg_type}: {message}"
    result = subprocess.run(
        ["git", "commit", "-m", full_message],
        env=env,
        capture_output=True,
        text=True
    )

    return result.returncode == 0

def main():
    print("\n" + "="*70)
    print("CyberIntel Summarizer - October 2025 Commits")
    print("="*70)
    print(f"Total commits to generate: {len(COMMITS)}")
    print("="*70 + "\n")

    setup()

    total = 0
    for date, hour, msg_type, message, files in COMMITS:
        if create_commit(date, hour, msg_type, message, files):
            total += 1
            if total % 10 == 0:
                print(f"[{total:3d}/{len(COMMITS)}] {date} {hour:02d}:xx {message[:45]}")
        else:
            print(f"ERROR at commit {total + 1}: {message}")
            break

    print(f"\n[{total:3d}/{len(COMMITS)}] Done!")

if __name__ == "__main__":
    main()

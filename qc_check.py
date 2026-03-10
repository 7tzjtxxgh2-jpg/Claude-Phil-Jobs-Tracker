#!/usr/bin/env python3
"""
Monthly Quality Control Check for PhilJobs Tracker.
Compares live PhilJobs data against our stored records, checks for
anomalies, and writes a report that GitHub Actions posts as an Issue.
"""

import json
import sys
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from pathlib import Path
from collections import Counter

DATA_FILE = Path("data/all_jobs.json")
REPORT_FILE = Path("data") / f"qc_report_{datetime.now().strftime('%Y-%m-%d')}.md"

DETAILED_URL = (
    "https://philjobs.org/jobQuery/execute"
    "?view=On+screen+-+detailed"
    "&typesToggler=Any+job+type"
    "&tenureTypesToggler=Any+contract+type"
    "&jobQuery.locationConstraint=NONE"
    "&jobQuery.institution.deleted=false"
    "&jobQuery.distance=50.0"
    "&topicListToggler=Any+AOS"
    "&aocListToggler=Any+AOC"
    "&jobQuery.orderBy=Creation+time"
    "&jobQuery.fromDate=date.struct"
    "&jobQuery.toDate=date.struct"
)

HEADERS = {'User-Agent': 'Mozilla/5.0 (compatible; PhilJobsQC/1.0)'}


def count_live_jobs():
    """Count job IDs currently listed on PhilJobs."""
    ids = set()
    page = 1
    while True:
        try:
            url = DETAILED_URL + f"&jobQuery.page={page}"
            r = requests.get(url, headers=HEADERS, timeout=30)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, 'html.parser')
            links = soup.find_all('a', href=lambda x: x and '/job/show/' in x)
            page_ids = {l['href'].rstrip('/').split('/')[-1] for l in links if l['href'].rstrip('/').split('/')[-1].isdigit()}
            if not page_ids or not (page_ids - ids):
                break
            ids |= page_ids
            next_link = soup.find('a', string=lambda t: t and 'next' in t.lower())
            if not next_link:
                break
            page += 1
        except Exception as e:
            return None, str(e)
    return len(ids), None


def check_stored_data(data):
    """Run quality checks on stored data. Returns list of (severity, message) tuples."""
    issues = []
    jobs = data.get('jobs', [])
    trends = data.get('weekly_trends', [])
    snapshots = data.get('weekly_snapshots', [])

    # 1. Zero-new-jobs weeks (possible silent failures)
    for t in trends:
        if t.get('new_jobs_count', 0) == 0:
            issues.append(('WARN', f"Week {t['date']}: 0 new jobs scraped — possible scrape failure"))

    # 2. Missing critical fields
    missing_institution = sum(1 for j in jobs if not j.get('institution') or j['institution'] == 'Unknown')
    missing_title = sum(1 for j in jobs if not j.get('title') or j['title'] == 'Unknown')
    missing_aos = sum(1 for j in jobs if not j.get('aos'))
    missing_job_category = sum(1 for j in jobs if not j.get('job_category'))

    if missing_institution > 0:
        issues.append(('WARN', f"{missing_institution} jobs missing institution name"))
    if missing_title > 0:
        issues.append(('WARN', f"{missing_title} jobs missing title"))
    if missing_aos > len(jobs) * 0.5:
        issues.append(('WARN', f"{missing_aos}/{len(jobs)} jobs missing AOS ({missing_aos/max(len(jobs),1)*100:.0f}%) — unusually high"))
    if missing_job_category > 0:
        issues.append(('INFO', f"{missing_job_category} jobs missing job_category field (may be older records)"))

    # 3. Duplicate hash check
    hashes = [j.get('hash') for j in jobs if j.get('hash')]
    dup_hashes = {h for h, n in Counter(hashes).items() if n > 1}
    if dup_hashes:
        issues.append(('WARN', f"{len(dup_hashes)} duplicate job hashes detected in stored data"))

    # 4. Gap detection — missing weeks
    if len(snapshots) >= 2:
        dates = sorted(datetime.strptime(s['date'], '%Y-%m-%d') for s in snapshots)
        for i in range(1, len(dates)):
            gap = (dates[i] - dates[i-1]).days
            if gap > 14:
                issues.append(('WARN', f"Gap of {gap} days between {dates[i-1].date()} and {dates[i].date()} — missed scrape?"))

    # 5. Data freshness
    if snapshots:
        last_date = max(datetime.strptime(s['date'], '%Y-%m-%d') for s in snapshots)
        days_since = (datetime.now() - last_date).days
        if days_since > 14:
            issues.append(('ERROR', f"Last scrape was {days_since} days ago ({last_date.date()}) — scraper may not be running"))

    return issues


def main():
    date_str = datetime.now().strftime('%Y-%m-%d')
    print(f"Running monthly QC check — {date_str}")

    # Load stored data
    if not DATA_FILE.exists():
        print("ERROR: data/all_jobs.json not found")
        sys.exit(1)

    with open(DATA_FILE) as f:
        data = json.load(f)

    jobs = data.get('jobs', [])
    trends = data.get('weekly_trends', [])
    snapshots = data.get('weekly_snapshots', [])

    # Count live jobs on PhilJobs
    print("Fetching live job count from PhilJobs...")
    live_count, live_error = count_live_jobs()

    # Run quality checks
    issues = check_stored_data(data)

    # Build report
    errors = [i for i in issues if i[0] == 'ERROR']
    warnings = [i for i in issues if i[0] == 'WARN']
    infos = [i for i in issues if i[0] == 'INFO']

    overall = "🔴 NEEDS ATTENTION" if errors else ("🟡 WARNINGS" if warnings else "🟢 ALL CLEAR")

    report_lines = [
        f"# PhilJobs Monthly QC Report — {date_str}",
        f"\n## Overall Status: {overall}\n",
        "## Stored Data Summary",
        f"- **Total unique jobs tracked:** {len(jobs)}",
        f"- **Weeks tracked:** {len(trends)}",
        f"- **Snapshots stored:** {len(snapshots)}",
    ]

    if snapshots:
        last_date = max(s['date'] for s in snapshots)
        report_lines.append(f"- **Last scrape:** {last_date}")

    report_lines.append("\n## Live PhilJobs Comparison")
    if live_error:
        report_lines.append(f"- ⚠️ Could not fetch live count: `{live_error}`")
    else:
        report_lines.append(f"- **Currently live on PhilJobs:** {live_count} jobs")
        if trends:
            last_week_new = trends[-1].get('new_jobs_count', 0)
            report_lines.append(f"- **New jobs last week:** {last_week_new}")

    report_lines.append("\n## Quality Check Results")
    if not issues:
        report_lines.append("✅ No issues found.")
    else:
        if errors:
            report_lines.append("\n### ❌ Errors")
            for _, msg in errors:
                report_lines.append(f"- {msg}")
        if warnings:
            report_lines.append("\n### ⚠️ Warnings")
            for _, msg in warnings:
                report_lines.append(f"- {msg}")
        if infos:
            report_lines.append("\n### ℹ️ Info")
            for _, msg in infos:
                report_lines.append(f"- {msg}")

    report_lines += [
        "\n## Recent Weekly Trend",
        "| Week | New Jobs |",
        "|------|----------|",
    ]
    for t in trends[-8:]:
        report_lines.append(f"| {t['date']} | {t.get('new_jobs_count', 0)} |")

    report = "\n".join(report_lines)

    # Save report
    REPORT_FILE.parent.mkdir(exist_ok=True)
    with open(REPORT_FILE, 'w') as f:
        f.write(report)

    print(report)
    print(f"\nReport saved to {REPORT_FILE}")

    # Exit with non-zero code if errors found (so GitHub Actions marks step as failed)
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()

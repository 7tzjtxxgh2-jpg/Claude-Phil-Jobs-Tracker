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

from scraper import position_type_from_category

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

    # 2b. Position-type cross-check: PhilJobs's own job_category vs Claude.
    # The dashboard uses the deterministic category mapping where decisive;
    # a disagreement with Claude's free-text reading is worth a look — it
    # usually means the ad text contradicts the poster's category choice.
    pt_mismatches = []
    for j in jobs:
        mapped = position_type_from_category(j.get('job_category'))
        claude = (j.get('classification') or {}).get('position_type')
        if mapped and claude and mapped != claude:
            pt_mismatches.append(
                f"{j.get('institution', '?')} — {j.get('title', '?')[:60]} "
                f"(category → {mapped!r}, Claude → {claude!r})"
            )
    if pt_mismatches:
        shown = '\n  '.join(pt_mismatches[:10])
        more = f"\n  ... and {len(pt_mismatches) - 10} more" if len(pt_mismatches) > 10 else ''
        issues.append(('INFO',
            f"{len(pt_mismatches)} jobs where PhilJobs's category and Claude's "
            f"position-type reading disagree (dashboard uses the category):\n  {shown}{more}"))

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

    # 6. Field-coverage report.
    # Scoped to jobs scraped in the last 35 days so we measure "is the
    # scraper currently capturing the fields it should?" rather than the
    # historical archive's completeness.
    #
    # `available_since` lets us silence false-positive warnings when a new
    # field has just been added to the scraper but hasn't had time to be
    # populated across many jobs yet — coverage only counts jobs scraped
    # after that date. If fewer than 10 such jobs exist, we report the
    # field as "not enough data yet" and skip the warning.
    if jobs:
        from datetime import timedelta
        recent_cutoff = datetime.now() - timedelta(days=35)
        recent = []
        for j in jobs:
            scraped = j.get('scraped_date', '')
            if not scraped:
                continue
            try:
                d = datetime.strptime(scraped[:19], '%Y-%m-%dT%H:%M:%S')
            except ValueError:
                continue
            if d >= recent_cutoff and j.get('status') != 'expired':
                recent.append((j, d))

        if recent:
            # field name : (minimum %, available_since YYYY-MM-DD or None for "always", note)
            expected_coverage = {
                'description':            (95, None,         'core posting text'),
                'posted_date':             (95, None,         'when listing went up'),
                'location':               (90, None,         'geographic location'),
                'application_url':        (60, None,         'apply link — some use email or web instructions instead'),
                'last_updated':           (80, '2026-05-27', 'PhilJobs edit timestamp (added 2026-05-27)'),
                'scheduled_expiry_date':  (80, '2026-05-27', 'PhilJobs auto-removal date (added 2026-05-27)'),
                'soft_deadline':          (40, '2026-05-27', '"Deadline for full consideration" (added 2026-05-27)'),
            }
            cov_lines = []
            for field, (min_pct, available_since_str, note) in expected_coverage.items():
                if available_since_str:
                    available_since = datetime.strptime(available_since_str, '%Y-%m-%d')
                    eligible = [(j, d) for (j, d) in recent if d >= available_since]
                else:
                    eligible = recent

                ne = len(eligible)
                if ne < 10:
                    cov_lines.append(f"⏳ {field}: {ne} eligible jobs — not enough data yet to evaluate ({note})")
                    continue

                have = sum(1 for (j, _) in eligible if j.get(field))
                pct = (have / ne) * 100
                marker = '🔴' if pct < min_pct else '🟢'
                cov_lines.append(f"{marker} {field}: {have}/{ne} ({pct:.0f}%, threshold {min_pct}%) — {note}")
                if pct < min_pct:
                    issues.append((
                        'WARN',
                        f"Field coverage low: {field} populated on only {have}/{ne} eligible jobs "
                        f"({pct:.0f}%, below {min_pct}% threshold)"
                    ))
            issues.append((
                'INFO',
                f'Field coverage on jobs scraped in the last 35 days (eligible = recent + after the field was introduced):\n  '
                + '\n  '.join(cov_lines)
            ))

    return issues


def check_live_count_drift(stored_total: int, live_count: int):
    """If the live PhilJobs listing count differs from our most recent
    snapshot's total by more than ~20% in either direction, flag — likely
    indicates the scraper is silently missing pages, or PhilJobs structure
    has changed.
    """
    if not live_count or not stored_total:
        return None
    drift = abs(live_count - stored_total) / max(live_count, stored_total)
    if drift < 0.20:
        return None
    direction = 'fewer' if stored_total < live_count else 'more'
    return (
        'WARN',
        f"Live-count drift: PhilJobs lists {live_count} active jobs but last "
        f"scrape captured {stored_total} ({drift*100:.0f}% {direction}). "
        f"Threshold is 20%. Could indicate scraper pagination issue or upstream change."
    )


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

    # Compare live PhilJobs count against our most recent scrape's total.
    # The 'total_jobs' on the latest snapshot reflects what was live when the
    # scrape ran; a big mismatch with the live count weeks later usually means
    # the scraper is silently dropping listings.
    if live_count and snapshots:
        last_snap = max(snapshots, key=lambda s: s['date'])
        drift_issue = check_live_count_drift(
            stored_total=last_snap.get('total_jobs', 0),
            live_count=live_count,
        )
        if drift_issue:
            issues.append(drift_issue)

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

#!/usr/bin/env python3
"""
Classifier regression test for the PhilJobs tracker.

Runs the live classifier (whatever model CLAUDE_MODEL points to) on a small,
hand-picked set of unambiguous postings stored in tests/regression_gold.json
and compares the output against expected labels. Exits non-zero if any case
fails.

Why this exists:
- The prompt and taxonomy change occasionally. A prompt edit that looks
  innocent can subtly shift behavior across hundreds of jobs.
- The semi-annual Opus QC catches drift after-the-fact, on production data.
  This catches breakage BEFORE a prompt change merges.

Why this isn't always run:
- Each run makes len(cases) Claude API calls. Currently 8 cases ≈ a few
  cents per run on Sonnet. Cheap, but not free, so wire it to a workflow
  triggered on prompt-touching PRs rather than every push.

Usage:
  ANTHROPIC_API_KEY=sk-ant-... python tests/test_classifier.py
  ANTHROPIC_API_KEY=sk-ant-... python tests/test_classifier.py --case pure_ai_ethics
  ANTHROPIC_API_KEY=sk-ant-... python tests/test_classifier.py --verbose

Exits 0 if all pass, 1 if any fail. Test output is a colored diff per failure.
"""

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scraper import PhilJobsScraper, CLAUDE_MODEL, TAXONOMY_VERSION  # noqa: E402

GOLD_FILE = Path(__file__).parent / "regression_gold.json"


# Tiny ANSI helpers — terminal output, no library dependency
def _red(s):   return f"\033[31m{s}\033[0m"
def _green(s): return f"\033[32m{s}\033[0m"
def _yellow(s):return f"\033[33m{s}\033[0m"
def _bold(s):  return f"\033[1m{s}\033[0m"


def check_case(case, actual):
    """Return list of failure messages (empty = pass)."""
    failures = []
    expected = case["expected"]

    # main_aos: exact-set match
    exp_main = set(expected.get("main_aos", []))
    act_main = set(actual.get("main_aos", []))
    if exp_main != act_main:
        missing = exp_main - act_main
        extra = act_main - exp_main
        msg = "main_aos mismatch"
        if missing:
            msg += f" — missing: {sorted(missing)}"
        if extra:
            msg += f" — extra: {sorted(extra)}"
        failures.append(msg)

    # position_type: exact match if specified
    exp_pt = expected.get("position_type")
    act_pt = actual.get("position_type")
    if exp_pt is not None and exp_pt != act_pt:
        failures.append(f"position_type mismatch — expected {exp_pt!r}, got {act_pt!r}")

    # Subcategory requirements
    act_details = actual.get("detail_aos", {}) or {}
    for main, must in (expected.get("subcategories_must_include") or {}).items():
        present = set(act_details.get(main, []) or [])
        for sub in must:
            if sub not in present:
                failures.append(f"subcategory missing — expected {main!r} to include {sub!r}, got {sorted(present) or 'nothing'}")
    for main, forbidden in (expected.get("subcategories_must_not_include") or {}).items():
        present = set(act_details.get(main, []) or [])
        # An empty 'forbidden' list means: this main category should not be tagged AT ALL.
        if not forbidden and main in (actual.get("main_aos") or []):
            failures.append(f"main category {main!r} should not be tagged at all")
            continue
        for sub in forbidden:
            if sub in present:
                failures.append(f"subcategory should be absent — {main!r} should NOT include {sub!r}")

    return failures


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--case", help="Run only the case with this test_id")
    p.add_argument("--verbose", "-v", action="store_true", help="Print classifier output for every case")
    args = p.parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print(_red("ERROR: ANTHROPIC_API_KEY not set — regression tests need API access."))
        sys.exit(2)

    if not GOLD_FILE.exists():
        print(_red(f"ERROR: {GOLD_FILE} not found."))
        sys.exit(2)

    with open(GOLD_FILE) as f:
        gold = json.load(f)
    cases = gold.get("cases", [])
    if args.case:
        cases = [c for c in cases if c["test_id"] == args.case]
        if not cases:
            print(_red(f"No case found with test_id={args.case!r}"))
            sys.exit(2)

    print(_bold(f"Running {len(cases)} regression cases"))
    print(f"  model = {CLAUDE_MODEL}")
    print(f"  taxonomy_version = {TAXONOMY_VERSION}")
    print()

    scraper = PhilJobsScraper()
    n_pass = 0
    n_fail = 0
    for c in cases:
        # Build a fake job dict with the gold inputs — classify_job_with_claude
        # reads via job.get(field) so the inputs dict structure works as-is.
        actual = scraper.classify_job_with_claude(c["inputs"])
        failures = check_case(c, actual)

        if failures:
            n_fail += 1
            print(_red(f"FAIL  {c['test_id']}  [{c.get('rule_tested', '—')}]"))
            print(f"      {c.get('note', '')}")
            for fm in failures:
                print(f"        - {fm}")
            print(f"      got main_aos     = {actual.get('main_aos')}")
            print(f"      got position_type = {actual.get('position_type')!r}")
            print(f"      got detail_aos    = {actual.get('detail_aos')}")
            if actual.get('reasoning'):
                print(f"      reasoning: {actual['reasoning'][:200]}")
            print()
        else:
            n_pass += 1
            print(_green(f"PASS  {c['test_id']}  [{c.get('rule_tested', '—')}]"))
            if args.verbose:
                print(f"      main_aos = {actual.get('main_aos')}")
                print(f"      position_type = {actual.get('position_type')!r}")
                print(f"      detail_aos = {actual.get('detail_aos')}")

    print()
    print(_bold(f"Summary: {_green(str(n_pass) + ' passed')}, {_red(str(n_fail) + ' failed')}"))
    sys.exit(0 if n_fail == 0 else 1)


if __name__ == "__main__":
    main()

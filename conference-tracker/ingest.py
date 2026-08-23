#!/usr/bin/env python3
"""Phase 1 — sweep PhilEvents into the local store.

No AI, no scoring, no ranking. This phase exists to prove the pipeline and
validate the source before anything is spent on classification: discover
events, parse them, filter by geography, persist them, and report honestly on
what failed.

Every degraded path is fatal by design. See philevents/errors.py.
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from philevents.config import Config
from philevents.detail import parse_event
from philevents.errors import FetchError, IngestAborted, StructureUnknown
from philevents.fetch import PoliteSession
from philevents.geo import Gazetteer
from philevents.listing import plausibility_gate, sweep_listing
from philevents.store import (connect, content_hash, events_due_for_recheck,
                              recent_sweep_sizes, record_run, upsert_event)

BASE = "https://philevents.org"
HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(HERE, "data", "events.db")
GAZETTEER_PATH = os.path.join(HERE, "data", "cities-na.txt")

# Confirmed in Phase 0 before this is trusted. Kept in one place so there is a
# single line to change when discovery reports the real listing URL.
LISTING_TEMPLATE = BASE + "/events/index?page={page}"

# If more than this fraction of detail pages fail to parse, the run is not
# "mostly fine with a few errors" -- the site has changed shape and we should
# stop rather than persist a mangled corpus.
MAX_PARSE_FAILURE_RATIO = 0.20


def build_event_row(event, gazetteer: Gazetteer, cfp_countries: list[str]) -> dict | None:
    """Turn a parsed Event into a DB row, or None if out of geographic scope.

    Geography is a filter here, never a score (plan section 2). Attend-only
    proximity filtering happens at digest time, where the home coordinate and
    the has_cfp flag are both known.
    """
    country = (event.country or "").upper()[:2]
    if country and country not in cfp_countries and not event.is_online:
        return None

    place = gazetteer.lookup(event.city, country=country or None, region=event.region)
    return {
        "event_id": event.event_id,
        "url": event.url,
        "title": event.title,
        "event_type": None,
        "has_cfp": 1 if event.deadline else 0,
        "start_date": event.start_date,
        "end_date": event.end_date,
        "deadline": event.deadline,
        "deadline_is_exact": 1 if event.deadline_is_exact else 0,
        "city": event.city,
        "region": event.region,
        "country": country or None,
        "lat": place.lat if place else None,
        "lon": place.lon if place else None,
        "is_online": 1 if event.is_online else 0,
        "topics": "|".join(event.topics),
        "body": event.body,
        "content_hash": content_hash(
            event.title, event.start_date, event.end_date, event.deadline,
            event.city, event.country, event.is_online, event.body,
        ),
        "status": "open",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=0,
                        help="cap detail fetches (for a smoke run)")
    parser.add_argument("--dry-run", action="store_true",
                        help="fetch and parse but write nothing")
    args = parser.parse_args()

    config = Config.load()
    session = PoliteSession(config.user_agent, config.request_delay_seconds)
    conn = connect(DB_PATH)
    gazetteer = Gazetteer.from_geonames(GAZETTEER_PATH, set(config.cfp_countries))
    if len(gazetteer) == 0:
        print(f"WARNING: no gazetteer at {GAZETTEER_PATH} — coordinates will be null "
              "and proximity filtering is unavailable until it is added.",
              file=sys.stderr)

    print("Sweeping listing pages...")
    try:
        found_ids, pages = sweep_listing(session.get, LISTING_TEMPLATE)
    except FetchError as exc:
        print(f"FATAL: listing sweep failed: {exc}", file=sys.stderr)
        return 1
    print(f"  {len(found_ids)} event IDs across {pages} page(s)")

    # Refuse to write a partial corpus. A silently short run is the failure
    # mode that makes a missed call for papers invisible.
    try:
        plausibility_gate(len(found_ids), recent_sweep_sizes(conn),
                          config.plausibility_floor_ratio)
    except IngestAborted as exc:
        print(f"FATAL: {exc}", file=sys.stderr)
        return 1

    recheck = set(events_due_for_recheck(conn, config.recheck_deadline_within_days))
    known = {r["event_id"] for r in conn.execute("SELECT event_id FROM events")}
    targets = [i for i in found_ids if i not in known or i in recheck]
    if args.limit:
        targets = targets[:args.limit]
    print(f"  {len(targets)} to fetch ({len(found_ids) - len(targets)} unchanged and not due)")

    counts = {"new": 0, "changed": 0, "unchanged": 0, "out_of_scope": 0}
    parse_errors: list[str] = []

    for n, event_id in enumerate(targets, 1):
        url = f"{BASE}/event/show/{event_id}"
        try:
            event = parse_event(session.get(url), event_id, url)
        except (StructureUnknown, FetchError) as exc:
            parse_errors.append(f"{event_id}: {exc}")
            continue

        row = build_event_row(event, gazetteer, config.cfp_countries)
        if row is None:
            counts["out_of_scope"] += 1
            continue
        if not args.dry_run:
            counts[upsert_event(conn, row)] += 1
        if n % 50 == 0:
            print(f"  ...{n}/{len(targets)}")

    if targets and len(parse_errors) > len(targets) * MAX_PARSE_FAILURE_RATIO:
        print(f"FATAL: {len(parse_errors)}/{len(targets)} detail pages failed to parse "
              f"(over the {MAX_PARSE_FAILURE_RATIO:.0%} threshold). The page structure has "
              "probably changed. Nothing was committed; run discover.py.", file=sys.stderr)
        for line in parse_errors[:5]:
            print(f"  {line}", file=sys.stderr)
        conn.rollback()
        return 1

    if args.dry_run:
        conn.rollback()
        print("\nDry run — nothing written.")
    else:
        record_run(conn, events_found=len(found_ids), events_new=counts["new"],
                   events_changed=counts["changed"], parse_errors=len(parse_errors))
        conn.commit()

    print(f"\nnew {counts['new']} · changed {counts['changed']} · "
          f"unchanged {counts['unchanged']} · out of scope {counts['out_of_scope']} · "
          f"parse errors {len(parse_errors)}")
    for line in parse_errors[:10]:
        print(f"  ! {line}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

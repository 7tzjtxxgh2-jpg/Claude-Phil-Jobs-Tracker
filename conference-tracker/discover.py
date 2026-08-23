#!/usr/bin/env python3
"""Phase 0 — find out what PhilEvents pages actually look like.

This exists because philevents.org is unreachable from the development
session that wrote this code, so no page has ever been inspected. Rather than
write speculative CSS selectors that would look finished and silently emit
nulls, this script goes and looks, then reports what it found.

It answers three open questions from the plan:

  1. Does the site emit schema.org JSON-LD? If so, most parsing is solved and
     we get structured dates and locations for free.
  2. Are submission deadlines structured dates, or free text ("end of
     September", "rolling")? Free text means an LLM normalisation step and a
     confidence flag on every date, which touches the whole digest design.
  3. How does pagination work, and are past events reachable? Recurrence
     forecasting needs history.

Writes discovery/report.md plus raw HTML samples. Reads nothing, writes no
database, and costs nothing -- it is safe to re-run.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from philevents.config import Config
from philevents.detail import deadline_candidates, extract_jsonld
from philevents.errors import FetchError
from philevents.fetch import PoliteSession
from philevents.listing import extract_event_ids

BASE = "https://philevents.org"
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "discovery")

# Candidate listing URLs. We do not know which of these exist or paginate; the
# point of this script is to find out, so each is tried and reported.
LISTING_CANDIDATES = [
    ("upcoming",      BASE + "/events/index?page={page}"),
    ("upcoming-alt",  BASE + "/?page={page}"),
    ("recent",        BASE + "/search/recent?page={page}"),
    ("cfp",           BASE + "/cfp/index?page={page}"),
]

TAG_RE = re.compile(r"<(\w+)[^>]*>")
TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.DOTALL | re.IGNORECASE)
META_RE = re.compile(r'<meta\s+[^>]*(?:name|property)=["\']([^"\']+)["\'][^>]*'
                     r'content=["\']([^"\']*)["\']', re.IGNORECASE)


def strip_tags(html: str) -> str:
    text = re.sub(r"<(script|style)\b.*?</\1>", " ", html, flags=re.DOTALL | re.IGNORECASE)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text)).strip()


def structural_dump(html: str) -> list[str]:
    """Describe the page's shape without assuming any particular markup."""
    lines: list[str] = []
    try:
        from bs4 import BeautifulSoup  # noqa: PLC0415 - optional, Actions-only
    except ImportError:
        lines.append("_(beautifulsoup4 not installed; tag census only)_")
        counts = Counter(TAG_RE.findall(html))
        lines.append("Tag census: " + ", ".join(
            f"{t}x{c}" for t, c in counts.most_common(15)))
        return lines

    soup = BeautifulSoup(html, "html.parser")

    dl_pairs = []
    for dl in soup.find_all("dl"):
        terms = [d.get_text(" ", strip=True) for d in dl.find_all("dt")]
        defs = [d.get_text(" ", strip=True) for d in dl.find_all("dd")]
        dl_pairs.extend(zip(terms, defs))
    if dl_pairs:
        lines.append("**Definition lists** (`<dt>` / `<dd>`) — likely the field table:")
        lines += [f"  - `{k}` = {v[:120]}" for k, v in dl_pairs[:25]]

    rows = []
    for table in soup.find_all("table"):
        for tr in table.find_all("tr"):
            cells = [c.get_text(" ", strip=True) for c in tr.find_all(["th", "td"])]
            if len(cells) >= 2:
                rows.append((cells[0], cells[1]))
    if rows:
        lines.append("**Table rows** — the PhilJobs-style field layout:")
        lines += [f"  - `{k}` = {v[:120]}" for k, v in rows[:25]]

    headings = [(h.name, h.get_text(" ", strip=True)[:100])
                for h in soup.find_all(["h1", "h2", "h3"])]
    if headings:
        lines.append("**Headings:**")
        lines += [f"  - `<{tag}>` {text}" for tag, text in headings[:15]]

    classes = Counter()
    for el in soup.find_all(class_=True):
        for cls in el.get("class", []):
            classes[cls] += 1
    if classes:
        lines.append("**Most common CSS classes** (selector candidates): "
                     + ", ".join(f"`{c}`x{n}" for c, n in classes.most_common(20)))
    return lines


def probe_listings(session: PoliteSession, report: list[str]) -> list[str]:
    report.append("## 1. Listing pages\n")
    best_ids: list[str] = []
    for label, template in LISTING_CANDIDATES:
        url = template.format(page=1)
        try:
            html = session.get(url)
        except FetchError as exc:
            report.append(f"- **{label}** `{url}` — FAILED: {exc}")
            continue
        ids = extract_event_ids(html)
        report.append(f"- **{label}** `{url}` — HTTP OK, "
                      f"**{len(ids)} event IDs** on page 1")
        if len(ids) > len(best_ids):
            best_ids = ids
            with open(os.path.join(OUT_DIR, f"listing-{label}.html"), "w") as fh:
                fh.write(html)

        if ids:
            try:
                html2 = session.get(template.format(page=2))
                ids2 = extract_event_ids(html2)
                overlap = len(set(ids) & set(ids2))
                verdict = ("**pagination works**" if ids2 and overlap < len(ids2) / 2
                           else "**page 2 looks identical to page 1** — this "
                                "template does not paginate")
                report.append(f"    - page 2: {len(ids2)} IDs, {overlap} overlapping — {verdict}")
            except FetchError as exc:
                report.append(f"    - page 2 fetch failed: {exc}")
    report.append("")
    return best_ids


def probe_events(session: PoliteSession, event_ids: list[str], report: list[str]) -> None:
    report.append("## 2. Event detail pages\n")
    jsonld_hits = 0
    for event_id in event_ids:
        url = f"{BASE}/event/show/{event_id}"
        report.append(f"### Event {event_id}\n\n`{url}`\n")
        try:
            html = session.get(url)
        except FetchError as exc:
            report.append(f"FAILED: {exc}\n")
            continue

        with open(os.path.join(OUT_DIR, f"event-{event_id}.html"), "w") as fh:
            fh.write(html)

        title = TITLE_RE.search(html)
        report.append(f"- `<title>`: {title.group(1).strip()[:150] if title else '(none)'}")

        blobs = extract_jsonld(html)
        if blobs:
            jsonld_hits += 1
            types = [b.get("@type") for b in blobs]
            report.append(f"- **JSON-LD present** — {len(blobs)} object(s), types: `{types}`")
            report.append(f"  - keys: `{sorted({k for b in blobs for k in b})}`")
        else:
            report.append("- **No JSON-LD.** An HTML fallback parser is required.")

        metas = META_RE.findall(html)
        interesting = [(n, v) for n, v in metas
                       if any(t in n.lower() for t in ("og:", "date", "event", "description"))]
        if interesting:
            report.append("- Meta tags: " + ", ".join(f"`{n}`={v[:60]}" for n, v in interesting[:8]))

        text = strip_tags(html)
        snippets = deadline_candidates(text)
        if snippets:
            report.append(f"- **Deadline-like text ({len(snippets)} hit(s)):**")
            report += [f"    - {s[:200]}" for s in snippets[:5]]
        else:
            report.append("- No deadline-like text found — check whether this event has a CFP.")

        report += ["- " + line if not line.startswith(("  ", "**", "_"))
                   else line for line in structural_dump(html)]
        report.append("")

    report.append(f"\n**JSON-LD coverage: {jsonld_hits}/{len(event_ids)} pages.**")
    if jsonld_hits == len(event_ids) and event_ids:
        report.append("Every page carries structured data — the parser can rely on it "
                      "and no HTML fallback is needed.")
    elif jsonld_hits:
        report.append("Partial coverage — JSON-LD first, HTML fallback for the rest.")
    else:
        report.append("No structured data anywhere — the HTML fallback is the only path. "
                      "Write it against the structure dumped above.")
    report.append("")


def probe_history(session: PoliteSession, report: list[str]) -> None:
    """Are past events reachable? Recurrence forecasting depends on it."""
    report.append("## 3. Past events (needed for recurrence forecasting)\n")
    for label, url in [
        ("archive", BASE + "/archive"),
        ("past search", BASE + "/search/past"),
        ("old event id", BASE + "/event/show/26594"),  # a 2017 event seen in research
    ]:
        try:
            html = session.get(url)
        except FetchError as exc:
            report.append(f"- **{label}** `{url}` — FAILED: {exc}")
            continue
        ids = extract_event_ids(html)
        report.append(f"- **{label}** `{url}` — HTTP OK, {len(ids)} event IDs, "
                      f"{len(html)} bytes")
    report.append("")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--events", type=int, default=6,
                        help="how many event detail pages to inspect")
    parser.add_argument("--event-id", action="append", default=[],
                        help="inspect a specific event ID (repeatable)")
    args = parser.parse_args()

    os.makedirs(OUT_DIR, exist_ok=True)
    config = Config.load()
    session = PoliteSession(config.user_agent, config.request_delay_seconds)

    report = [
        "# PhilEvents structure discovery",
        "",
        "Generated by `discover.py`. This is a Phase 0 artefact: it reports what the",
        "site actually looks like so the parsers can be written against observed",
        "markup rather than guesses. Raw HTML samples are saved alongside it.",
        "",
    ]

    listing_ids = probe_listings(session, report)
    chosen = args.event_id or listing_ids[:args.events]
    if not chosen:
        report.append("**No event IDs discovered — every listing candidate failed.** "
                      "Nothing further can be probed; fix listing discovery first.")
    else:
        probe_events(session, chosen, report)
    probe_history(session, report)

    out_path = os.path.join(OUT_DIR, "report.md")
    with open(out_path, "w") as fh:
        fh.write("\n".join(report) + "\n")
    print(f"Wrote {out_path} ({len(report)} lines)")
    print(f"Raw samples in {OUT_DIR}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

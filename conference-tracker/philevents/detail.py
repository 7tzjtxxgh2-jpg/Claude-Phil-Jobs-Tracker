"""Parsing a single event page.

STATUS: the structured-data path below is real and standards-based. The HTML
fallback is deliberately NOT written yet, because philevents.org is blocked by
this development session's network egress policy and no page has been
inspected. Writing speculative CSS selectors would produce code that looks
finished and silently emits nulls -- the exact failure this project is built
to avoid.

Phase 0 (`discover.py`) exists to close that gap: it dumps the real structure
of a handful of pages so the fallback can be written against observed markup.
Until then `parse_event` raises StructureUnknown rather than guessing.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

from .errors import StructureUnknown

JSONLD_RE = re.compile(
    r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.DOTALL | re.IGNORECASE,
)

# Lines that plausibly carry a submission deadline. Used by discovery to find
# where deadlines live, and later as a fallback signal.
DEADLINE_HINT_RE = re.compile(
    r"(submission deadline|deadline for submission|abstract deadline|"
    r"deadline|abstracts? due|papers? due|submit by|closing date)",
    re.IGNORECASE,
)


@dataclass
class Event:
    """One PhilEvents listing, as far as we can read it."""
    event_id: str
    url: str
    title: str = ""
    start_date: str | None = None
    end_date: str | None = None
    deadline: str | None = None
    deadline_is_exact: bool = False
    city: str | None = None
    region: str | None = None
    country: str | None = None
    is_online: bool = False
    topics: list[str] = field(default_factory=list)
    body: str = ""
    source: str = "unknown"


def extract_jsonld(html: str) -> list[dict[str, Any]]:
    """Return every JSON-LD object embedded in the page.

    Tolerates the two shapes that appear in the wild: a bare object, and a
    @graph array of them. Malformed blocks are skipped rather than fatal --
    a broken third-party analytics blob should not sink the run.
    """
    objects: list[dict[str, Any]] = []
    for raw in JSONLD_RE.findall(html):
        try:
            parsed = json.loads(raw.strip())
        except json.JSONDecodeError:
            continue
        candidates = parsed if isinstance(parsed, list) else [parsed]
        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            if "@graph" in candidate and isinstance(candidate["@graph"], list):
                objects.extend(g for g in candidate["@graph"] if isinstance(g, dict))
            else:
                objects.append(candidate)
    return objects


def _event_objects(objects: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Filter JSON-LD objects down to schema.org Event types."""
    found = []
    for obj in objects:
        type_field = obj.get("@type", "")
        types = type_field if isinstance(type_field, list) else [type_field]
        if any(isinstance(t, str) and "event" in t.lower() for t in types):
            found.append(obj)
    return found


def _place_fields(location: Any) -> tuple[str | None, str | None, str | None, bool]:
    """Pull (city, region, country, is_online) out of a schema.org location."""
    if isinstance(location, list):
        online = any(
            isinstance(item, dict)
            and "virtual" in str(item.get("@type", "")).lower()
            for item in location
        )
        for item in location:
            if isinstance(item, dict) and "virtual" not in str(item.get("@type", "")).lower():
                city, region, country, _ = _place_fields(item)
                return city, region, country, online
        return None, None, None, online

    if not isinstance(location, dict):
        return None, None, None, False

    if "virtual" in str(location.get("@type", "")).lower():
        return None, None, None, True

    address = location.get("address")
    if isinstance(address, str):
        return address, None, None, False
    if isinstance(address, dict):
        return (
            address.get("addressLocality"),
            address.get("addressRegion"),
            address.get("addressCountry") if isinstance(address.get("addressCountry"), str)
            else (address.get("addressCountry") or {}).get("name"),
            False,
        )
    return location.get("name"), None, None, False


def parse_event(html: str, event_id: str, url: str) -> Event:
    """Parse one event page.

    Prefers schema.org JSON-LD, which gives structured dates and location with
    no markup guessing. Raises StructureUnknown when the page carries no
    machine-readable event, so that a markup change fails the run loudly
    instead of yielding an empty record.
    """
    events = _event_objects(extract_jsonld(html))
    if not events:
        raise StructureUnknown(
            f"Event {event_id}: no schema.org Event JSON-LD found, and no HTML "
            "fallback parser has been written yet. Run discover.py against this "
            "page and implement the fallback against its observed structure."
        )

    data = events[0]
    city, region, country, is_online = _place_fields(data.get("location"))
    return Event(
        event_id=event_id,
        url=url,
        title=(data.get("name") or "").strip(),
        start_date=data.get("startDate"),
        end_date=data.get("endDate"),
        city=city,
        region=region,
        country=country,
        is_online=is_online,
        body=(data.get("description") or "").strip(),
        source="json-ld",
    )


def deadline_candidates(text: str, window: int = 160) -> list[str]:
    """Return text snippets around anything that looks like a deadline.

    Phase 0 uses this to answer the open question in the plan: are deadlines
    structured dates, or free text like "end of September" / "rolling"? That
    answer decides whether an LLM normalisation step and a per-date confidence
    flag are needed.
    """
    snippets = []
    for match in DEADLINE_HINT_RE.finditer(text):
        start = max(0, match.start() - window // 2)
        snippet = " ".join(text[start:match.end() + window].split())
        snippets.append(snippet)
    return snippets

"""Discovery: turn PhilEvents listing pages into a set of event IDs.

Deliberately regex-based rather than DOM-based. Event URLs have the stable
shape /event/show/{id}, so pulling IDs out of the raw HTML survives markup
changes that would break CSS selectors -- and it keeps this module free of a
BeautifulSoup dependency, so it is testable without a network or a parser.

What this module does NOT do is guess at pagination structure. The page
sequence is driven by the caller with an explicit URL template, and the loop
stops when a page yields no IDs it has not already seen.
"""
from __future__ import annotations

import re
from typing import Callable, Iterable

from .errors import IngestAborted

EVENT_ID_RE = re.compile(r"/event/show/(\d+)")

# A listing page that renders correctly holds many events. Far fewer than this
# means we are almost certainly looking at an error page, a login wall, or a
# redirect -- not a genuinely short page.
MIN_PLAUSIBLE_IDS_PER_PAGE = 5


def extract_event_ids(html: str) -> list[str]:
    """Return event IDs in first-seen order, deduplicated."""
    seen: dict[str, None] = {}
    for match in EVENT_ID_RE.finditer(html):
        seen.setdefault(match.group(1), None)
    return list(seen)


def sweep_listing(fetch: Callable[[str], str], url_template: str,
                  max_pages: int = 40) -> tuple[list[str], int]:
    """Page through a listing until it stops yielding new IDs.

    `url_template` must contain a `{page}` placeholder. Returns the ordered
    ID list and the number of pages actually fetched.

    Stops on the first page that contributes nothing new, which handles both
    a hard end-of-results and a site that clamps out-of-range pages back to
    the last real one (a loop that a naive `while True` would never exit).
    """
    if "{page}" not in url_template:
        raise ValueError("url_template must contain a {page} placeholder")

    all_ids: dict[str, None] = {}
    pages_fetched = 0
    for page in range(1, max_pages + 1):
        html = fetch(url_template.format(page=page))
        pages_fetched += 1
        page_ids = extract_event_ids(html)
        new_ids = [i for i in page_ids if i not in all_ids]
        if not new_ids:
            break
        for event_id in new_ids:
            all_ids[event_id] = None
    return list(all_ids), pages_fetched


def plausibility_gate(found_count: int, baseline_counts: Iterable[int],
                      floor_ratio: float = 0.70) -> None:
    """Abort the run if this sweep found implausibly few events.

    `baseline_counts` is the recent history of sweep sizes. With no history
    (a first run) any non-trivial count is accepted -- there is nothing to
    compare against, and refusing to bootstrap would be its own failure.

    Raises IngestAborted, which must fail the workflow. It must never be
    caught and downgraded to a warning: a run that writes 12 events where it
    should have written 700 is exactly the silent shortfall this exists to
    prevent.
    """
    baseline = [c for c in baseline_counts if c > 0]
    if not baseline:
        if found_count < MIN_PLAUSIBLE_IDS_PER_PAGE:
            raise IngestAborted(
                f"First sweep found only {found_count} events; refusing to "
                "treat that as a real corpus."
            )
        return

    average = sum(baseline) / len(baseline)
    floor = average * floor_ratio
    if found_count < floor:
        raise IngestAborted(
            f"Sweep found {found_count} events, below the floor of {floor:.0f} "
            f"({floor_ratio:.0%} of a {average:.0f}-event trailing average over "
            f"{len(baseline)} runs). Refusing to write a partial corpus. "
            "Check whether the listing markup or pagination changed."
        )

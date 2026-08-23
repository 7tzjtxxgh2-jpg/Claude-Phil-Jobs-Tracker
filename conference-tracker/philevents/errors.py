"""Failure modes that must be loud.

The PhilJobs audit's finding F-5 -- "a broken listing fetch silently degrades
to a homepage subset" -- is the single most important thing not to repeat here.
In an analytics tool a silent shortfall skews a trend line. In a deadline tool
it means a call for papers you would have submitted to never appears, and
nothing anywhere tells you it is missing.

So every degraded path in this package raises. There are no partial writes and
no quiet fallbacks.
"""


class PhilEventsError(Exception):
    """Base class for this package."""


class FetchError(PhilEventsError):
    """A network fetch failed after exhausting retries."""


class IngestAborted(PhilEventsError):
    """A run discovered implausibly little data and refused to write.

    Raised by the plausibility gate. The caller should surface this loudly
    (a failing workflow and a GitHub issue) and leave the store untouched.
    """


class StructureUnknown(PhilEventsError):
    """The page did not match any structure this parser knows how to read.

    Raised rather than returning nulls, so that a markup change on PhilEvents
    fails the run instead of quietly emitting empty events.
    """

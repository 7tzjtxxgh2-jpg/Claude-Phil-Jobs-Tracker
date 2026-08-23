"""Runtime configuration, loaded from config.yaml.

The home coordinate lives here rather than in code, and this file is
gitignored by default: the owner fills it in locally and it is never
transmitted anywhere.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field

import yaml

DEFAULT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.yaml")


@dataclass
class Home:
    """Where 'nearby' is measured from. Filled in by the owner."""
    lat: float | None = None
    lon: float | None = None
    label: str = ""

    @property
    def is_set(self) -> bool:
        return self.lat is not None and self.lon is not None


@dataclass
class Config:
    home: Home = field(default_factory=Home)

    # Attend-only events qualify if online or inside this radius. Great-circle
    # miles, which run ~1.3-1.5x shorter than driving miles -- so 120 here is
    # more permissive than "120 miles by road". Drop to ~90 to approximate it.
    attend_only_radius_mi: float = 120.0

    # Countries whose CFP events are in scope (presenting is fundable).
    cfp_countries: list[str] = field(default_factory=lambda: ["US", "CA", "MX"])

    # Digest shape. See plan section 8.
    digest_top_n: int = 10
    digest_deadline_horizon_days: int = 90
    # The 90-day section is gated on this so it does not run to 100+ entries
    # a week. Set to 0.0 for the literal ungated list; the digest always
    # reports how many events the floor removed.
    digest_min_fit: float = 6.0

    # Re-check cadence for mutable records (plan section 6.2).
    recheck_deadline_within_days: int = 45

    # Abort the run if a listing sweep finds less than this fraction of the
    # trailing average event count.
    plausibility_floor_ratio: float = 0.70

    request_delay_seconds: float = 0.5
    user_agent: str = (
        "Claude-Phil-Conferences-Tracker/0.1 (personal research tool; "
        "contact via GitHub)"
    )

    @classmethod
    def load(cls, path: str = DEFAULT_PATH) -> "Config":
        if not os.path.exists(path):
            return cls()
        with open(path) as fh:
            raw = yaml.safe_load(fh) or {}
        home = Home(**(raw.pop("home", None) or {}))
        known = {f for f in cls.__dataclass_fields__ if f != "home"}
        return cls(home=home, **{k: v for k, v in raw.items() if k in known})

"""SQLite persistence.

Two lessons from the PhilJobs audit are designed in here rather than
retrofitted:

  * Not one big JSON. The jobs tracker keeps a 1.7 MB all_jobs.json and
    rewrites it whole every ten records; the audit named that as the
    structural gate blocking its most valuable improvement.

  * Records are mutable. Finding F-3 -- job records are write-once, so status
    never updates -- is a wart there and would be fatal here, because
    deadlines are the product and CFP deadlines get extended routinely.
    Every event carries a content_hash and is re-checked on a cadence.

Scores are keyed by profile_version (a hash of profile.md), so revising the
research profile makes it computable exactly which events need rescoring --
the same idea as the jobs repo's taxonomy_version, applied to the input that
actually changes here.
"""
from __future__ import annotations

import hashlib
import sqlite3
from datetime import date, datetime, timezone

SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    event_id            TEXT PRIMARY KEY,
    url                 TEXT NOT NULL,
    title               TEXT NOT NULL DEFAULT '',
    event_type          TEXT,
    has_cfp             INTEGER NOT NULL DEFAULT 0,
    start_date          TEXT,
    end_date            TEXT,
    deadline            TEXT,
    deadline_is_exact   INTEGER NOT NULL DEFAULT 0,
    city                TEXT,
    region              TEXT,
    country             TEXT,
    lat                 REAL,
    lon                 REAL,
    is_online           INTEGER NOT NULL DEFAULT 0,
    topics              TEXT,
    body                TEXT,
    content_hash        TEXT NOT NULL,
    status              TEXT NOT NULL DEFAULT 'open',
    first_seen          TEXT NOT NULL,
    last_seen           TEXT NOT NULL,
    last_checked        TEXT
);
CREATE INDEX IF NOT EXISTS idx_events_deadline ON events(deadline);
CREATE INDEX IF NOT EXISTS idx_events_status   ON events(status);

CREATE TABLE IF NOT EXISTS event_changes (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id    TEXT NOT NULL REFERENCES events(event_id),
    field       TEXT NOT NULL,
    old_value   TEXT,
    new_value   TEXT,
    noticed_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS classifications (
    event_id         TEXT NOT NULL REFERENCES events(event_id),
    aos_main         TEXT NOT NULL,
    aos_detail       TEXT,
    taxonomy_version TEXT NOT NULL,
    source           TEXT NOT NULL,
    PRIMARY KEY (event_id, taxonomy_version)
);

CREATE TABLE IF NOT EXISTS papers (
    paper_id  TEXT PRIMARY KEY,
    title     TEXT NOT NULL,
    abstract  TEXT NOT NULL DEFAULT '',
    keywords  TEXT,
    status    TEXT
);

CREATE TABLE IF NOT EXISTS scores (
    event_id        TEXT NOT NULL REFERENCES events(event_id),
    paper_id        TEXT,
    fit_score       REAL NOT NULL,
    reasoning       TEXT,
    profile_version TEXT NOT NULL,
    model           TEXT,
    scored_at       TEXT NOT NULL,
    PRIMARY KEY (event_id, paper_id, profile_version)
);

CREATE TABLE IF NOT EXISTS submissions (
    submission_id TEXT PRIMARY KEY,
    paper_id      TEXT NOT NULL REFERENCES papers(paper_id),
    event_id      TEXT NOT NULL REFERENCES events(event_id),
    state         TEXT NOT NULL,
    submitted_on  TEXT,
    decision_on   TEXT,
    notes         TEXT
);

CREATE TABLE IF NOT EXISTS series (
    series_id             TEXT PRIMARY KEY,
    canonical_title       TEXT NOT NULL,
    host                  TEXT,
    cadence               TEXT,
    typical_cfp_month     INTEGER,
    typical_deadline_month INTEGER
);

CREATE TABLE IF NOT EXISTS series_members (
    series_id TEXT NOT NULL REFERENCES series(series_id),
    event_id  TEXT NOT NULL REFERENCES events(event_id),
    PRIMARY KEY (series_id, event_id)
);

-- One row per ingest run. Feeds the plausibility gate's trailing average and
-- gives the digest its parse-error accounting.
CREATE TABLE IF NOT EXISTS runs (
    run_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    ran_at        TEXT NOT NULL,
    events_found  INTEGER NOT NULL,
    events_new    INTEGER NOT NULL DEFAULT 0,
    events_changed INTEGER NOT NULL DEFAULT 0,
    parse_errors  INTEGER NOT NULL DEFAULT 0,
    notes         TEXT
);
"""

# Fields whose change is worth telling the owner about, rather than silently
# updating. A moved deadline is a headline, not a diff.
NOTABLE_FIELDS = ("deadline", "start_date", "end_date", "status", "title")


def content_hash(*parts: object) -> str:
    """Stable hash of the fields that decide whether an event has changed."""
    joined = "\x1f".join("" if p is None else str(p) for p in parts)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def connect(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    return conn


def upsert_event(conn: sqlite3.Connection, fields: dict) -> str:
    """Insert or update one event. Returns 'new', 'changed', or 'unchanged'.

    Changes to NOTABLE_FIELDS are recorded in event_changes so the digest can
    report them -- a deadline extension is something to act on, not something
    to overwrite quietly.
    """
    event_id = fields["event_id"]
    now = _now()
    existing = conn.execute(
        "SELECT * FROM events WHERE event_id = ?", (event_id,)
    ).fetchone()

    if existing is None:
        columns = list(fields) + ["first_seen", "last_seen", "last_checked"]
        values = [fields[c] for c in fields] + [now, now, now]
        conn.execute(
            f"INSERT INTO events ({','.join(columns)}) "
            f"VALUES ({','.join('?' * len(columns))})",
            values,
        )
        return "new"

    if existing["content_hash"] == fields.get("content_hash"):
        conn.execute(
            "UPDATE events SET last_seen = ?, last_checked = ? WHERE event_id = ?",
            (now, now, event_id),
        )
        return "unchanged"

    for field in NOTABLE_FIELDS:
        if field in fields and str(existing[field] or "") != str(fields[field] or ""):
            conn.execute(
                "INSERT INTO event_changes (event_id, field, old_value, new_value, noticed_at)"
                " VALUES (?,?,?,?,?)",
                (event_id, field, existing[field], fields[field], now),
            )

    assignments = ",".join(f"{c} = ?" for c in fields if c != "event_id")
    values = [fields[c] for c in fields if c != "event_id"]
    conn.execute(
        f"UPDATE events SET {assignments}, last_seen = ?, last_checked = ? WHERE event_id = ?",
        values + [now, now, event_id],
    )
    return "changed"


def recent_sweep_sizes(conn: sqlite3.Connection, limit: int = 6) -> list[int]:
    """Trailing event counts, newest first, for the plausibility gate."""
    rows = conn.execute(
        "SELECT events_found FROM runs ORDER BY run_id DESC LIMIT ?", (limit,)
    ).fetchall()
    return [r["events_found"] for r in rows]


def events_due_for_recheck(conn: sqlite3.Connection, within_days: int,
                           today: date | None = None) -> list[str]:
    """Open events whose deadline is near enough that a change would matter."""
    today = today or date.today()
    rows = conn.execute(
        "SELECT event_id, deadline FROM events WHERE status = 'open' AND deadline IS NOT NULL"
    ).fetchall()
    due = []
    for row in rows:
        try:
            deadline = date.fromisoformat(str(row["deadline"])[:10])
        except (ValueError, TypeError):
            due.append(row["event_id"])  # unparseable: re-check rather than assume
            continue
        if 0 <= (deadline - today).days <= within_days:
            due.append(row["event_id"])
    return due


def record_run(conn: sqlite3.Connection, *, events_found: int, events_new: int,
               events_changed: int, parse_errors: int, notes: str = "") -> None:
    conn.execute(
        "INSERT INTO runs (ran_at, events_found, events_new, events_changed,"
        " parse_errors, notes) VALUES (?,?,?,?,?,?)",
        (_now(), events_found, events_new, events_changed, parse_errors, notes),
    )

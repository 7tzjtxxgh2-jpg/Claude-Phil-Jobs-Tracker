#!/usr/bin/env python3
"""Build a weekly meal plan from the normalized Umami library.

Reads `umami_library.db` (produced by umami_ingest.py), picks recipes for the
week, and writes the plan as Markdown, JSON and an optional .ics calendar.

Selection policy is intentionally a placeholder -- see `select_recipes()`.
Everything around it (library access, filtering vocabulary, history tracking,
grocery roll-up, output formats) is the real machinery, so swapping in a
smarter chooser is a one-function change.

Usage:
    python3 plan_week.py --db umami_library.db
    python3 plan_week.py --db umami_library.db --days 5 --max-minutes 45 --ics
    python3 plan_week.py --db umami_library.db --start 2026-08-31 --commit

Standard library only.
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sqlite3
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

PLAN_SCHEMA = """
CREATE TABLE IF NOT EXISTS plans (
    plan_date  TEXT NOT NULL,
    recipe_id  TEXT NOT NULL,
    slot       TEXT NOT NULL DEFAULT 'dinner',
    created_at TEXT NOT NULL,
    PRIMARY KEY (plan_date, slot)
);
CREATE INDEX IF NOT EXISTS idx_plans_recipe ON plans(recipe_id);
"""

# Ingredient lines are "1 1/2 cups (350g) plain flour, sifted" -- strip the
# measurement noise so the grocery roll-up can spot duplicates across recipes.
QUANTITY_RE = re.compile(
    r"^\s*(?:\d+(?:[\s./-]\d+)*)?\s*"
    r"(?:cups?|tablespoons?|tbsps?|tbs|teaspoons?|tsps?|ounces?|oz"
    r"|pounds?|lbs?|grams?|kg|g|millilit(?:re|er)s?|ml|lit(?:re|er)s?|l"
    r"|cloves?|cans?|jars?|pinch(?:es)?|handfuls?|sprigs?|bunch(?:es)?"
    r"|slices?|packages?|pkgs?|pieces?)?\b\.?\s*",
    re.IGNORECASE,
)
PAREN_RE = re.compile(r"\([^)]*\)")


def open_library(db_path):
    path = Path(db_path).expanduser()
    if not path.exists():
        sys.exit(f"No library at {path}. Run umami_ingest.py first.")
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(PLAN_SCHEMA)
    return conn


# --------------------------------------------------------------------------
# reading the library
# --------------------------------------------------------------------------

def load_candidates(conn, max_minutes=None, books=None, include=None, exclude=None,
                    exclude_recipe_ids=()):
    """Every recipe that is eligible this week, with its tags attached."""
    where, params = ["1 = 1"], []
    if max_minutes:
        # Untimed recipes stay eligible; most libraries have patchy time data.
        where.append("(total_minutes IS NULL OR total_minutes <= ?)")
        params.append(max_minutes)
    if books:
        where.append("book IN (%s)" % ",".join("?" * len(books)))
        params.extend(books)
    if exclude_recipe_ids:
        where.append("id NOT IN (%s)" % ",".join("?" * len(exclude_recipe_ids)))
        params.extend(exclude_recipe_ids)
    for tag in include or []:
        where.append(
            "id IN (SELECT recipe_id FROM tags WHERE LOWER(value) = LOWER(?))"
        )
        params.append(tag)
    for tag in exclude or []:
        where.append(
            "id NOT IN (SELECT recipe_id FROM tags WHERE LOWER(value) = LOWER(?))"
        )
        params.append(tag)

    rows = conn.execute(
        f"SELECT * FROM recipes WHERE {' AND '.join(where)} ORDER BY title", params
    ).fetchall()

    recipes = []
    for row in rows:
        rid = row["id"]
        recipe = dict(row)
        recipe.pop("raw_json", None)
        recipe["tags"] = [
            r["value"] for r in conn.execute(
                "SELECT value FROM tags WHERE recipe_id = ?", (rid,)
            )
        ]
        recipe["ingredients"] = [
            r["text"] for r in conn.execute(
                "SELECT text FROM ingredients WHERE recipe_id = ? ORDER BY position",
                (rid,),
            )
        ]
        recipes.append(recipe)
    return recipes


def recently_planned(conn, days):
    """Recipe ids planned within the last `days` days, to avoid repeats."""
    if not days:
        return set()
    cutoff = (date.today() - timedelta(days=days)).isoformat()
    return {
        r["recipe_id"]
        for r in conn.execute(
            "SELECT DISTINCT recipe_id FROM plans WHERE plan_date >= ?", (cutoff,)
        )
    }


# --------------------------------------------------------------------------
# selection -- THE PLACEHOLDER
# --------------------------------------------------------------------------

def select_recipes(candidates, count, seed=None):
    """Choose `count` recipes for the week.

    ==================== REPLACE THIS FUNCTION ====================
    Right now it is a seeded random draw. It exists so the pipeline runs
    end to end; it is not the selection logic you actually want.

    Each candidate is a dict with: id, title, book, servings, prep_minutes,
    cook_minutes, total_minutes, calories, rating, tags[], ingredients[],
    description, url. Anything you want to weight on -- cuisine variety,
    protein rotation, effort budget per weeknight, pantry overlap between
    recipes, seasonality, ratings -- is already on the object.
    ===============================================================
    """
    if len(candidates) <= count:
        return list(candidates)
    rng = random.Random(seed)
    return rng.sample(candidates, count)


# --------------------------------------------------------------------------
# plan assembly and output
# --------------------------------------------------------------------------

def build_plan(recipes, start, days, slot="dinner"):
    return [
        {"date": (start + timedelta(days=i)).isoformat(), "slot": slot, "recipe": r}
        for i, r in enumerate(recipes[:days])
    ]


def normalize_ingredient(line):
    text = PAREN_RE.sub("", line).lower()
    text = QUANTITY_RE.sub("", text, count=1)
    text = re.split(r",| -- | – ", text)[0]
    return re.sub(r"\s+", " ", text).strip(" .,")


def grocery_list(plan):
    """Roll ingredients up across the week. Naive: matches on normalized text."""
    buckets = {}
    for entry in plan:
        for line in entry["recipe"]["ingredients"]:
            key = normalize_ingredient(line)
            if not key:
                continue
            buckets.setdefault(key, []).append((entry["recipe"]["title"], line))
    return dict(sorted(buckets.items()))


def render_markdown(plan, groceries, start, days):
    end = start + timedelta(days=days - 1)
    out = [
        f"# Meal plan: {start:%a %d %b} – {end:%a %d %b %Y}",
        "",
        "| Day | Meal | Time | Serves | Book |",
        "| --- | --- | --- | --- | --- |",
    ]
    for entry in plan:
        r = entry["recipe"]
        day = datetime.fromisoformat(entry["date"]).strftime("%a %d %b")
        title = f"[{r['title']}]({r['url']})" if r.get("url") else r["title"]
        minutes = f"{r['total_minutes']} min" if r.get("total_minutes") else "—"
        out.append(
            f"| {day} | {title} | {minutes} | {r.get('servings') or '—'} "
            f"| {r.get('book') or '—'} |"
        )

    out += ["", "## Grocery list", ""]
    for key, uses in groceries.items():
        if len(uses) > 1:
            recipes = ", ".join(sorted({t for t, _ in uses}))
            out.append(f"- **{key}** — {len(uses)}× ({recipes})")
            for _, original in uses:
                out.append(f"    - {original}")
        else:
            out.append(f"- {uses[0][1]}")

    out += ["", "## Recipes", ""]
    for entry in plan:
        r = entry["recipe"]
        day = datetime.fromisoformat(entry["date"]).strftime("%A")
        out.append(f"### {day} — {r['title']}")
        if r.get("description"):
            out.append(f"\n{r['description']}\n")
        for line in r["ingredients"]:
            out.append(f"- {line}")
        if r.get("url"):
            out.append(f"\n<{r['url']}>")
        out.append("")
    return "\n".join(out)


def render_ics(plan, calendar_name="Meal plan"):
    """Minimal iCalendar output, so the week can drop into Apple Calendar."""
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    def esc(text):
        return (
            str(text).replace("\\", "\\\\").replace(";", r"\;")
            .replace(",", r"\,").replace("\n", r"\n")
        )

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//umami-weekly-planner//EN",
        "CALSCALE:GREGORIAN",
        f"X-WR-CALNAME:{esc(calendar_name)}",
    ]
    for i, entry in enumerate(plan):
        r = entry["recipe"]
        day = entry["date"].replace("-", "")
        body = []
        if r.get("total_minutes"):
            body.append(f"{r['total_minutes']} min")
        if r.get("servings"):
            body.append(f"serves {r['servings']}")
        body.append("")
        body.extend(r["ingredients"])
        lines += [
            "BEGIN:VEVENT",
            f"UID:umami-{day}-{i}@weekly-planner",
            f"DTSTAMP:{stamp}",
            f"DTSTART;VALUE=DATE:{day}",
            f"DTEND;VALUE=DATE:{(date.fromisoformat(entry['date']) + timedelta(days=1)).isoformat().replace('-', '')}",
            f"SUMMARY:{esc(r['title'])}",
            f"DESCRIPTION:{esc(chr(10).join(body))}",
        ]
        if r.get("url"):
            lines.append(f"URL:{r['url']}")
        lines.append("END:VEVENT")
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"


def commit_plan(conn, plan):
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    conn.executemany(
        "INSERT INTO plans (plan_date, recipe_id, slot, created_at) VALUES (?, ?, ?, ?) "
        "ON CONFLICT(plan_date, slot) DO UPDATE SET "
        "recipe_id = excluded.recipe_id, created_at = excluded.created_at",
        [(e["date"], e["recipe"]["id"], e["slot"], now) for e in plan],
    )
    conn.commit()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--db", default="umami_library.db")
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--start", help="YYYY-MM-DD (default: next Monday)")
    parser.add_argument("--slot", default="dinner")
    parser.add_argument("--max-minutes", type=int, help="cap on total time")
    parser.add_argument("--book", action="append", dest="books", help="repeatable")
    parser.add_argument("--tag", action="append", dest="include", help="require tag")
    parser.add_argument("--not-tag", action="append", dest="exclude", help="exclude tag")
    parser.add_argument("--avoid-recent-days", type=int, default=28,
                        help="skip recipes planned this recently (0 to disable)")
    parser.add_argument("--seed", type=int, help="reproducible placeholder picks")
    parser.add_argument("--out", default=".", help="output directory")
    parser.add_argument("--ics", action="store_true", help="also write week.ics")
    parser.add_argument("--commit", action="store_true",
                        help="record the plan so future weeks avoid repeats")
    args = parser.parse_args(argv)

    if args.start:
        start = date.fromisoformat(args.start)
    else:
        today = date.today()
        start = today + timedelta(days=(7 - today.weekday()) % 7 or 7)

    conn = open_library(args.db)
    recent = recently_planned(conn, args.avoid_recent_days)
    candidates = load_candidates(
        conn,
        max_minutes=args.max_minutes,
        books=args.books,
        include=args.include,
        exclude=args.exclude,
        exclude_recipe_ids=tuple(recent),
    )
    total = conn.execute("SELECT COUNT(*) FROM recipes").fetchone()[0]
    print(f"Library: {total} recipes -> {len(candidates)} eligible"
          + (f" ({len(recent)} held back as recently planned)" if recent else ""))
    if not candidates:
        sys.exit("Nothing eligible. Loosen the filters or lower --avoid-recent-days.")
    if len(candidates) < args.days:
        print(f"  ! only {len(candidates)} eligible for {args.days} days; "
              "plan will be short.", file=sys.stderr)

    chosen = select_recipes(candidates, args.days, seed=args.seed)
    plan = build_plan(chosen, start, args.days, slot=args.slot)
    groceries = grocery_list(plan)

    out_dir = Path(args.out).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)
    md_path = out_dir / f"meal-plan-{start.isoformat()}.md"
    json_path = out_dir / f"meal-plan-{start.isoformat()}.json"
    md_path.write_text(render_markdown(plan, groceries, start, args.days), encoding="utf-8")
    json_path.write_text(
        json.dumps(
            {"start": start.isoformat(), "days": args.days, "plan": plan,
             "groceries": {k: [line for _, line in v] for k, v in groceries.items()}},
            indent=2, ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    written = [md_path, json_path]
    if args.ics:
        ics_path = out_dir / f"meal-plan-{start.isoformat()}.ics"
        ics_path.write_text(render_ics(plan), encoding="utf-8")
        written.append(ics_path)

    if args.commit:
        commit_plan(conn, plan)
        print("Recorded in the plans table; these recipes will be held back next time.")

    print()
    for entry in plan:
        day = datetime.fromisoformat(entry["date"]).strftime("%a %d %b")
        minutes = entry["recipe"].get("total_minutes")
        print(f"  {day}  {entry['recipe']['title']}"
              + (f"  ({minutes} min)" if minutes else ""))
    print(f"\n{len(groceries)} distinct grocery items")
    for path in written:
        print(f"Wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Ingest an Umami recipe export into a normalized, queryable SQLite library.

Umami (Strange Quark LLC) can export every recipe book from
Account -> "Export all recipe books". Choose the **Recipe JSON Schema**
format: that is schema.org/Recipe JSON-LD, which is structured enough to
plan against. This script turns that export into `umami_library.db`.

The parser is deliberately shape-tolerant. Umami's exact export container
(one JSON file, a file per recipe, a folder per book, or a zip) is not
documented, so instead of assuming a layout we walk every JSON structure we
are given and pick out anything that looks like a recipe. HTML exports are
also read, via their embedded <script type="application/ld+json"> blocks.

Usage:
    python3 umami_ingest.py ~/Downloads/UmamiExport --db umami_library.db
    python3 umami_ingest.py export.zip --db umami_library.db --stats

Standard library only. Runs on stock macOS python3.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sqlite3
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

JSON_SUFFIXES = {".json", ".jsonld", ".json-ld"}
HTML_SUFFIXES = {".html", ".htm"}
LDJSON_RE = re.compile(
    r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.IGNORECASE | re.DOTALL,
)
DURATION_RE = re.compile(
    r"^P(?:(?P<days>\d+(?:\.\d+)?)D)?"
    r"(?:T(?:(?P<hours>\d+(?:\.\d+)?)H)?"
    r"(?:(?P<minutes>\d+(?:\.\d+)?)M)?"
    r"(?:(?P<seconds>\d+(?:\.\d+)?)S)?)?$",
    re.IGNORECASE,
)
LOOSE_DURATION_RE = re.compile(
    r"(?:(?P<hours>\d+(?:\.\d+)?)\s*(?:hours?|hrs?|h)\b)?"
    r"\s*(?:(?P<minutes>\d+(?:\.\d+)?)\s*(?:minutes?|mins?|m)\b)?",
    re.IGNORECASE,
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS recipes (
    id            TEXT PRIMARY KEY,
    title         TEXT NOT NULL,
    description   TEXT,
    book          TEXT,
    url           TEXT,
    author        TEXT,
    image         TEXT,
    yield_text    TEXT,
    servings      INTEGER,
    prep_minutes  INTEGER,
    cook_minutes  INTEGER,
    total_minutes INTEGER,
    calories      REAL,
    rating        REAL,
    date_added    TEXT,
    source_file   TEXT,
    raw_json      TEXT NOT NULL,
    ingested_at   TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS ingredients (
    recipe_id TEXT NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
    position  INTEGER NOT NULL,
    text      TEXT NOT NULL,
    PRIMARY KEY (recipe_id, position)
);
CREATE TABLE IF NOT EXISTS instructions (
    recipe_id TEXT NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
    position  INTEGER NOT NULL,
    section   TEXT,
    text      TEXT NOT NULL,
    PRIMARY KEY (recipe_id, position)
);
CREATE TABLE IF NOT EXISTS tags (
    recipe_id TEXT NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
    kind      TEXT NOT NULL,
    value     TEXT NOT NULL,
    PRIMARY KEY (recipe_id, kind, value)
);
CREATE INDEX IF NOT EXISTS idx_tags_value ON tags(value);
CREATE INDEX IF NOT EXISTS idx_recipes_book ON recipes(book);
CREATE INDEX IF NOT EXISTS idx_recipes_total ON recipes(total_minutes);
"""


# --------------------------------------------------------------------------
# value normalization
# --------------------------------------------------------------------------

def as_text(value):
    """Flatten schema.org's many ways of saying 'a string'."""
    if value is None:
        return None
    if isinstance(value, str):
        return value.strip() or None
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, dict):
        for key in ("name", "text", "@value", "url", "title"):
            got = as_text(value.get(key))
            if got:
                return got
        return None
    if isinstance(value, list):
        parts = [as_text(v) for v in value]
        parts = [p for p in parts if p]
        return ", ".join(parts) or None
    return None


def as_list(value):
    """Normalize a category/cuisine/keyword field into a list of strings."""
    if value is None:
        return []
    if isinstance(value, str):
        return [p.strip() for p in value.split(",") if p.strip()]
    if isinstance(value, dict):
        got = as_text(value)
        return [got] if got else []
    if isinstance(value, list):
        out = []
        for item in value:
            out.extend(as_list(item))
        return out
    return []


def to_minutes(value):
    """ISO 8601 duration ('PT1H30M'), a loose string ('1 hr 30 min'), or a number."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return int(value) or None
    text = as_text(value)
    if not text:
        return None
    match = DURATION_RE.match(text.strip())
    if match and any(match.groupdict().values()):
        parts = {k: float(v) for k, v in match.groupdict().items() if v}
        minutes = (
            parts.get("days", 0) * 1440
            + parts.get("hours", 0) * 60
            + parts.get("minutes", 0)
            + parts.get("seconds", 0) / 60
        )
        return int(round(minutes)) or None
    match = LOOSE_DURATION_RE.search(text)
    if match and any(match.groupdict().values()):
        parts = {k: float(v) for k, v in match.groupdict().items() if v}
        minutes = parts.get("hours", 0) * 60 + parts.get("minutes", 0)
        return int(round(minutes)) or None
    digits = re.search(r"\d+", text)
    return int(digits.group()) if digits else None


def first_int(value):
    text = as_text(value)
    if not text:
        return None
    match = re.search(r"\d+", text)
    return int(match.group()) if match else None


def to_float(value):
    if isinstance(value, (int, float)):
        return float(value)
    text = as_text(value)
    if not text:
        return None
    match = re.search(r"\d+(?:\.\d+)?", text)
    return float(match.group()) if match else None


def norm_ingredients(recipe):
    raw = recipe.get("recipeIngredient")
    if raw is None:
        raw = recipe.get("ingredients")
    out = []
    for item in raw if isinstance(raw, list) else [raw]:
        if isinstance(item, dict):
            # Some exporters split quantity/unit/name into separate fields.
            composed = " ".join(
                str(item[k]).strip()
                for k in ("quantity", "amount", "unit", "name", "text", "item")
                if item.get(k) not in (None, "")
            ).strip()
            text = composed or as_text(item)
        else:
            text = as_text(item)
        if not text:
            continue
        # A single blob of newline-separated ingredients is common in plain exports.
        for line in text.splitlines():
            line = line.strip(" \t-*•")
            if line:
                out.append(line)
    return out


def norm_instructions(recipe):
    raw = recipe.get("recipeInstructions")
    if raw is None:
        for key in ("instructions", "directions", "steps", "method"):
            if key in recipe:
                raw = recipe[key]
                break
    out = []

    def walk(node, section=None):
        if node is None:
            return
        if isinstance(node, str):
            for line in re.split(r"[\r\n]+", node):
                line = line.strip()
                line = re.sub(r"^(?:step\s*)?\d+[.)]\s*", "", line, flags=re.IGNORECASE)
                if line:
                    out.append((section, line))
        elif isinstance(node, list):
            for item in node:
                walk(item, section)
        elif isinstance(node, dict):
            kind = str(node.get("@type") or node.get("type") or "")
            if "HowToSection" in kind or "itemListElement" in node:
                name = as_text(node.get("name"))
                walk(
                    node.get("itemListElement") or node.get("steps") or node.get("item"),
                    name or section,
                )
            else:
                text = as_text(node.get("text") or node.get("name") or node.get("description"))
                if text:
                    out.append((section, text))

    walk(raw)
    return out


def norm_tags(recipe):
    tags = []
    for kind, key in (
        ("category", "recipeCategory"),
        ("cuisine", "recipeCuisine"),
        ("keyword", "keywords"),
        ("keyword", "tags"),
        ("method", "cookingMethod"),
        ("diet", "suitableForDiet"),
    ):
        for value in as_list(recipe.get(key)):
            value = value.strip().lstrip("#")
            # suitableForDiet arrives as a schema.org URL, e.g. .../VeganDiet
            value = value.rsplit("/", 1)[-1]
            if value:
                tags.append((kind, value))
    # de-duplicate, case-insensitively, keeping first spelling
    seen, unique = set(), []
    for kind, value in tags:
        key = (kind, value.lower())
        if key not in seen:
            seen.add(key)
            unique.append((kind, value))
    return unique


def recipe_id(recipe, title, ingredients):
    for key in ("@id", "identifier", "id", "uuid", "recipeId"):
        got = as_text(recipe.get(key))
        if got:
            return got
    url = as_text(recipe.get("url"))
    if url:
        return url
    digest = hashlib.sha1(
        ("\n".join([title] + ingredients[:5])).encode("utf-8")
    ).hexdigest()
    return f"sha1:{digest}"


def normalize(recipe, book, source_file):
    title = as_text(recipe.get("name") or recipe.get("title")) or "Untitled"
    ingredients = norm_ingredients(recipe)
    nutrition = recipe.get("nutrition") if isinstance(recipe.get("nutrition"), dict) else {}
    rating = recipe.get("aggregateRating")
    rating_value = None
    if isinstance(rating, dict):
        rating_value = to_float(rating.get("ratingValue"))
    else:
        rating_value = to_float(rating)

    total = to_minutes(recipe.get("totalTime"))
    prep = to_minutes(recipe.get("prepTime"))
    cook = to_minutes(recipe.get("cookTime"))
    if total is None and (prep or cook):
        total = (prep or 0) + (cook or 0)

    return {
        "id": recipe_id(recipe, title, ingredients),
        "title": title,
        "description": as_text(recipe.get("description")),
        "book": book,
        "url": as_text(recipe.get("url")),
        "author": as_text(recipe.get("author")),
        "image": as_text(recipe.get("image")),
        "yield_text": as_text(recipe.get("recipeYield") or recipe.get("yield")),
        "servings": first_int(recipe.get("recipeYield") or recipe.get("yield")),
        "prep_minutes": prep,
        "cook_minutes": cook,
        "total_minutes": total,
        "calories": to_float(nutrition.get("calories")) if nutrition else None,
        "rating": rating_value,
        "date_added": as_text(recipe.get("dateCreated") or recipe.get("datePublished")),
        "source_file": source_file,
        "ingredients": ingredients,
        "instructions": norm_instructions(recipe),
        "tags": norm_tags(recipe),
        "raw_json": json.dumps(recipe, ensure_ascii=False, sort_keys=True),
    }


# --------------------------------------------------------------------------
# discovery
# --------------------------------------------------------------------------

def looks_like_recipe(node):
    if not isinstance(node, dict):
        return False
    types = node.get("@type") or node.get("type")
    for value in types if isinstance(types, list) else [types]:
        if isinstance(value, str) and value.strip().lower().endswith("recipe"):
            return True
    if "recipeIngredient" in node or "recipeInstructions" in node:
        return True
    has_ingredients = isinstance(node.get("ingredients"), (list, str))
    has_steps = any(k in node for k in ("instructions", "directions", "steps", "method"))
    return bool(has_ingredients and has_steps)


def iter_recipes(node, book=None):
    """Yield (recipe_dict, book_name) for every recipe anywhere in the structure."""
    if isinstance(node, dict):
        if looks_like_recipe(node):
            yield node, book
            return
        name = as_text(node.get("name") or node.get("title"))
        nested = any(isinstance(v, (list, dict)) for v in node.values())
        next_book = name if (name and nested) else book
        for value in node.values():
            yield from iter_recipes(value, next_book)
    elif isinstance(node, list):
        for item in node:
            yield from iter_recipes(item, book)


def load_documents(path: Path):
    """Yield (parsed_json, label) for every JSON document we can read from a file."""
    suffix = path.suffix.lower()
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        print(f"  ! unreadable {path}: {exc}", file=sys.stderr)
        return
    if suffix in JSON_SUFFIXES:
        try:
            yield json.loads(text), str(path)
        except json.JSONDecodeError:
            # Newline-delimited JSON is a plausible fallback shape.
            docs = []
            for line in text.splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    docs.append(json.loads(line))
                except json.JSONDecodeError:
                    docs = []
                    break
            if docs:
                yield docs, str(path)
            else:
                print(f"  ! not valid JSON: {path}", file=sys.stderr)
    elif suffix in HTML_SUFFIXES:
        for block in LDJSON_RE.findall(text):
            try:
                yield json.loads(block), str(path)
            except json.JSONDecodeError:
                continue


def walk_sources(sources, workdir):
    """Expand files, directories and zips into a flat list of candidate files."""
    files = []
    for source in sources:
        path = Path(source).expanduser()
        if not path.exists():
            print(f"  ! no such path: {path}", file=sys.stderr)
            continue
        if path.is_file() and path.suffix.lower() == ".zip":
            target = Path(workdir) / f"unzipped-{path.stem}"
            target.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(path) as archive:
                archive.extractall(target)
            files.extend(sorted(p for p in target.rglob("*") if p.is_file()))
        elif path.is_dir():
            files.extend(sorted(p for p in path.rglob("*") if p.is_file()))
        else:
            files.append(path)
    return [
        f
        for f in files
        if f.suffix.lower() in JSON_SUFFIXES | HTML_SUFFIXES
        and not f.name.startswith("._")
    ]


# --------------------------------------------------------------------------
# persistence
# --------------------------------------------------------------------------

def open_library(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    try:
        conn.executescript(
            "CREATE VIRTUAL TABLE IF NOT EXISTS recipes_fts "
            "USING fts5(id UNINDEXED, title, body);"
        )
    except sqlite3.OperationalError:
        pass  # FTS5 unavailable; plan_week falls back to LIKE queries.
    return conn


def has_fts(conn):
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE name = 'recipes_fts'"
    ).fetchone()
    return row is not None


def store(conn, recipe):
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    conn.execute(
        """INSERT INTO recipes (id, title, description, book, url, author, image,
                                yield_text, servings, prep_minutes, cook_minutes,
                                total_minutes, calories, rating, date_added,
                                source_file, raw_json, ingested_at)
           VALUES (:id, :title, :description, :book, :url, :author, :image,
                   :yield_text, :servings, :prep_minutes, :cook_minutes,
                   :total_minutes, :calories, :rating, :date_added,
                   :source_file, :raw_json, :ingested_at)
           ON CONFLICT(id) DO UPDATE SET
               title=excluded.title, description=excluded.description,
               book=excluded.book, url=excluded.url, author=excluded.author,
               image=excluded.image, yield_text=excluded.yield_text,
               servings=excluded.servings, prep_minutes=excluded.prep_minutes,
               cook_minutes=excluded.cook_minutes,
               total_minutes=excluded.total_minutes, calories=excluded.calories,
               rating=excluded.rating, date_added=excluded.date_added,
               source_file=excluded.source_file, raw_json=excluded.raw_json,
               ingested_at=excluded.ingested_at""",
        {k: recipe[k] for k in (
            "id", "title", "description", "book", "url", "author", "image",
            "yield_text", "servings", "prep_minutes", "cook_minutes",
            "total_minutes", "calories", "rating", "date_added", "source_file",
            "raw_json",
        )} | {"ingested_at": now},
    )
    rid = recipe["id"]
    for table in ("ingredients", "instructions", "tags"):
        conn.execute(f"DELETE FROM {table} WHERE recipe_id = ?", (rid,))
    conn.executemany(
        "INSERT INTO ingredients (recipe_id, position, text) VALUES (?, ?, ?)",
        [(rid, i, text) for i, text in enumerate(recipe["ingredients"])],
    )
    conn.executemany(
        "INSERT INTO instructions (recipe_id, position, section, text) VALUES (?, ?, ?, ?)",
        [(rid, i, sec, text) for i, (sec, text) in enumerate(recipe["instructions"])],
    )
    conn.executemany(
        "INSERT OR IGNORE INTO tags (recipe_id, kind, value) VALUES (?, ?, ?)",
        [(rid, kind, value) for kind, value in recipe["tags"]],
    )
    if has_fts(conn):
        body = " \n".join(
            [recipe["description"] or ""]
            + recipe["ingredients"]
            + [t for _, t in recipe["instructions"]]
            + [v for _, v in recipe["tags"]]
            + [recipe["book"] or ""]
        )
        conn.execute("DELETE FROM recipes_fts WHERE id = ?", (rid,))
        conn.execute(
            "INSERT INTO recipes_fts (id, title, body) VALUES (?, ?, ?)",
            (rid, recipe["title"], body),
        )


# --------------------------------------------------------------------------
# entry point
# --------------------------------------------------------------------------

def ingest(sources, db_path, verbose=False):
    counts = {"files": 0, "documents": 0, "recipes": 0, "skipped_empty": 0}
    conn = open_library(db_path)
    with tempfile.TemporaryDirectory() as workdir:
        files = walk_sources(sources, workdir)
        for path in files:
            counts["files"] += 1
            fallback_book = path.parent.name or path.stem
            for document, label in load_documents(path):
                counts["documents"] += 1
                for raw, book in iter_recipes(document):
                    recipe = normalize(raw, book or fallback_book, label)
                    if not recipe["ingredients"] and not recipe["instructions"]:
                        counts["skipped_empty"] += 1
                        continue
                    store(conn, recipe)
                    counts["recipes"] += 1
                    if verbose:
                        print(f"  + {recipe['title']}  [{recipe['book']}]")
        conn.commit()
    return conn, counts


def print_stats(conn):
    total = conn.execute("SELECT COUNT(*) FROM recipes").fetchone()[0]
    print(f"\nLibrary: {total} recipes")
    if not total:
        return
    print("\n  By book:")
    for row in conn.execute(
        "SELECT COALESCE(book,'(none)') AS book, COUNT(*) AS n "
        "FROM recipes GROUP BY book ORDER BY n DESC LIMIT 20"
    ):
        print(f"    {row['n']:>4}  {row['book']}")
    print("\n  Field coverage (how much the selector has to work with):")
    for label, expr in (
        ("total time", "total_minutes IS NOT NULL"),
        ("servings", "servings IS NOT NULL"),
        ("any tag", "id IN (SELECT recipe_id FROM tags)"),
        ("ingredients", "id IN (SELECT recipe_id FROM ingredients)"),
        ("instructions", "id IN (SELECT recipe_id FROM instructions)"),
    ):
        n = conn.execute(f"SELECT COUNT(*) FROM recipes WHERE {expr}").fetchone()[0]
        print(f"    {n:>4}/{total}  {label}  ({100 * n // total}%)")
    print("\n  Top tags:")
    for row in conn.execute(
        "SELECT kind, value, COUNT(*) AS n FROM tags "
        "GROUP BY kind, value ORDER BY n DESC LIMIT 15"
    ):
        print(f"    {row['n']:>4}  {row['kind']}: {row['value']}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("sources", nargs="+", help="export file, folder, or .zip")
    parser.add_argument("--db", default="umami_library.db", help="library database path")
    parser.add_argument("--stats", action="store_true", help="print a library summary")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    conn, counts = ingest(args.sources, args.db, verbose=args.verbose)
    print(
        f"Read {counts['files']} files -> {counts['documents']} JSON documents "
        f"-> {counts['recipes']} recipes"
        + (f" ({counts['skipped_empty']} skipped as empty)" if counts["skipped_empty"] else "")
    )
    print(f"Wrote {args.db}")
    if args.stats:
        print_stats(conn)
    if not counts["recipes"]:
        print(
            "\nNo recipes found. Check the export format is 'Recipe JSON Schema'\n"
            "and point this script at the folder/zip Umami produced.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

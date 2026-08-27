# Umami → weekly meal plan

**Short answer: yes, this is buildable, and the reading half is already built and
tested here.** The pieces in this folder read a Umami recipe library into a
normalized SQLite database and emit a weekly plan (Markdown + JSON + `.ics`),
with recipe *selection* left as a deliberate stub for you to fill in.

Umami is Strange Quark LLC's recipe manager (App Store id `1597523594`, Android
`app.umami.umami`, web at `umami.recipes`). It is an account-synced app, not a
local-file app — which shapes everything below.

---

## The three ways in, ranked

### Path A — the official export ✅ *recommended, works today*

Umami has a documented bulk export: **Account → "Export all recipe books"**, with
a choice of PDF, Markdown, HTML, Plain Text, or **Recipe JSON Schema**. That last
one is [schema.org/Recipe](https://schema.org/Recipe) JSON-LD, which is exactly
the structured shape a planner needs — `name`, `recipeIngredient[]`,
`recipeInstructions[]`, `recipeYield`, `prepTime`/`cookTime`/`totalTime` as ISO
durations, `recipeCategory`, `recipeCuisine`, `keywords`, `nutrition`.

The export also survives a lapsed subscription — Umami's own FAQ says you can
view and export your recipes even after the trial expires.

- **Cost:** one manual tap whenever you want to refresh the library.
- **Risk:** essentially zero. It is a supported, documented feature that the
  vendor intends you to use for exactly this.
- **Status here:** implemented and tested (`umami_ingest.py`).

This is the path to start on. One export gets you a full library; re-export
whenever you have added enough recipes to care.

### Path B — read the app's local store 🔍 *needs one check on your Mac*

The Mac app almost certainly keeps a local cache of your synced library
somewhere under `~/Library/Containers/<bundle-id>/Data/` or
`~/Library/Group Containers/`. If that cache is a SQLite/Core Data store, a
script can snapshot and query it directly and the manual export step disappears
entirely — fully automated, run it from `cron`/`launchd` every Sunday morning.

I cannot confirm this from here; it depends on how the app is built, and nothing
public documents it. **`probe_umami.sh` answers it in about ten seconds** — see
below.

- **Cost:** none once working.
- **Risk:** it is undocumented, so an app update can change the schema without
  warning. Worth having Path A as the fallback either way.
- **If the store turns out to be Realm or encrypted:** dead end, use Path A.

### Path C — the web API behind `umami.recipes` ⚠️ *not recommended for reading*

The web app implies an HTTP API carrying your account's recipes. It is
undocumented and unversioned, using it means handling your own session
credentials, and it can change silently. It buys nothing over Path A for
*reading*.

The one thing it could do that neither A nor B can is **write** a generated plan
back into Umami's own meal calendar. See the limitation below.

---

## The one open question, and how to close it

Run this on your Mac:

```bash
bash probe_umami.sh
```

It is strictly read-only — it copies any database it finds to a scratch folder
before looking at it, so the app's live files are never touched. It reports:

- where Umami is installed and its real bundle identifier
- whether it is a native, Catalyst, or iOS-on-Apple-silicon build
- every data directory and candidate store file it can find
- the full table list and row counts of any SQLite store, plus the Core Data
  recipe entity's columns if there is one
- whether the app ships **AppIntents metadata** — i.e. whether it publishes
  Shortcuts actions, which would open a fourth, fully-supported automation route
- any URL schemes it registers, useful for deep-linking from a plan back into
  the app

If sections come back "Operation not permitted", grant Full Disk Access to your
terminal under System Settings → Privacy & Security.

Send me that report and I can point the ingester at whatever it finds.

---

## Using what's here

```bash
# 1. Export from Umami: Account -> "Export all recipe books" -> Recipe JSON Schema

# 2. Build the library (accepts a file, a folder, or a .zip)
python3 umami_ingest.py ~/Downloads/UmamiExport --db umami_library.db --stats

# 3. Build a week
python3 plan_week.py --db umami_library.db --days 5 --max-minutes 60 --ics --commit
```

Everything is standard-library Python 3 — no `pip install`, runs on stock macOS.

### What ingest produces

A SQLite database you can query directly, with `recipes`, `ingredients`,
`instructions`, `tags`, and a `recipes_fts` full-text index:

```sql
SELECT title, total_minutes FROM recipes
WHERE total_minutes <= 30
  AND id IN (SELECT recipe_id FROM tags WHERE value = 'vegetarian');
```

`--stats` prints a field-coverage report — how many of your recipes actually
carry times, servings and tags. **Read this first.** It tells you what the
selector has to work with; if only 20% of your library has `totalTime`, a
selection policy built on cooking time will not work well.

### Useful `plan_week.py` flags

| Flag | Effect |
| --- | --- |
| `--days N` | plan length (default 7) |
| `--start YYYY-MM-DD` | default is next Monday |
| `--max-minutes N` | cap total time (untimed recipes stay eligible) |
| `--tag / --not-tag` | require or exclude a tag, repeatable |
| `--book` | restrict to given recipe books, repeatable |
| `--avoid-recent-days N` | hold back recently-planned recipes (default 28) |
| `--commit` | record the plan so future weeks avoid repeats |
| `--ics` | also emit a calendar file for Apple Calendar |

### The selection stub

`select_recipes()` in `plan_week.py` is a seeded random draw behind a
`REPLACE THIS FUNCTION` banner. Per your note, I have not tried to make it
smart. Everything it needs is already attached to each candidate — `tags`,
`ingredients`, `total_minutes`, `servings`, `rating`, `book`, `calories` — so
swapping in real logic (protein rotation, effort budget per weeknight, pantry
overlap between recipes, seasonality) is a one-function change with the rest of
the pipeline untouched.

The demo run makes the point: with a naive selector, week two cheerfully
scheduled Focaccia and Banana Bread as dinners.

---

## The honest limitation

**Reading is solved. Writing back into Umami's own meal-plan calendar is not.**

Umami has a scheduling calendar built in, but I found no documented automation
hook — no published API, no confirmed Shortcuts actions. So the plan lands as
Markdown / JSON / `.ics` rather than inside Umami. In practice that means either
living with the plan in Calendar and Umami as the recipe source, or spending a
minute a week tapping the picks into Umami's scheduler.

Two things could change that, both surfaced by `probe_umami.sh`: AppIntents
metadata in the app bundle (Shortcuts actions, fully supported), or a URL scheme
that deep-links to a recipe. Path C is the other option, with the caveats above.

---

## Files

| File | What it does |
| --- | --- |
| `probe_umami.sh` | read-only macOS reconnaissance — run this first |
| `umami_ingest.py` | export → normalized SQLite library |
| `plan_week.py` | library → weekly plan (Markdown, JSON, `.ics`) |
| `tests/test_umami_pipeline.py` | 28 tests, `python3 tests/test_umami_pipeline.py` |

### A note on the parser

Umami's exact export container is not publicly documented, so `umami_ingest.py`
does not assume one. It walks whatever JSON it is handed and pulls out anything
recipe-shaped, which means it copes with a single array, a book-wrapped object,
one file per recipe, newline-delimited JSON, a `@graph`, an HTML export with
embedded JSON-LD, or a zip of any of those. The test suite exercises all of
them. Non-recipe files in the export (settings, README) are ignored.

If your real export has a shape none of these cover, the ingester will say it
found zero recipes rather than fail silently — send me a sample and it is a
small change.

# PhilEvents Conference Tracker

A private project-management tool for philosophy conferences and calls for
papers. It watches [PhilEvents](https://philevents.org), ranks events by fit
against a personal research profile, tracks submission deadlines, and manages a
paper-to-venue submission pipeline.

Companion to the PhilJobs Market Analytics dashboard, with which it shares an
area-of-specialization taxonomy — so conference activity and hiring activity
can be sliced along identical axes.

**Design document:** `CONFERENCE-TRACKER-PLAN-2026-08-21.md` in the PhilJobs
repo. Read it first; it carries the reasoning behind most of what follows.

---

## Status: Phase 0/1 scaffold

| Phase | State |
|---|---|
| **0 — Page structure discovery** | Ready to run |
| **1 — Ingest → SQLite → geography filter** | Written; listing URL unconfirmed |
| 2 — Research profile + fit scoring | Not started |
| 3 — Paper inventory + per-paper matching + pipeline | Not started |
| 4 — History backfill + recurrence forecasting | Not started |
| 5 — Local HTML dashboard | Not started |

### Read this before trusting the parsers

**No PhilEvents page has ever been inspected by the code in this repository.**
`philevents.org` is blocked by the network egress policy of the development
session that wrote it.

Rather than write speculative CSS selectors — which would look finished and
silently emit nulls — the parsers do one of two things:

* Parse **schema.org JSON-LD** where it exists. That path is real, tested, and
  standards-based.
* Otherwise **raise `StructureUnknown`** and fail the run.

`discover.py` exists to close the gap. Run it first.

---

## Quick start

```bash
pip install -r requirements.txt
cp config.example.yaml config.yaml   # fill in your home coordinate
python discover.py --events 6        # Phase 0: go look at the site
python -m unittest discover -s tests -t .
python ingest.py --dry-run --limit 20
```

Or run **Actions → "Phase 0 — structure discovery"** and read the committed
`discovery/report.md` from your phone.

### What discovery answers

1. **Does the site emit JSON-LD?** If yes, most parsing is already solved and
   dates and locations come structured.
2. **Are deadlines structured dates or free text?** "End of September" and
   "rolling" mean an LLM normalisation step and a per-date confidence flag —
   this touches the whole digest design, and it is the largest open unknown.
3. **How does pagination work, and are past events reachable?** Recurrence
   forecasting needs history.

After it reports, fix `LISTING_TEMPLATE` in `ingest.py`, write the HTML
fallback in `philevents/detail.py` if needed, then enable the schedule in
`.github/workflows/weekly-ingest.yml`.

---

## Design commitments

Three things are load-bearing and should not be quietly relaxed.

**Failure is loud.** The PhilJobs audit's finding F-5 — *"a broken listing
fetch silently degrades to a homepage subset"* — is the failure this project
most needs to avoid. In an analytics tool a silent shortfall skews a trend
line. Here it means a call for papers you would have submitted to never
appears, and nothing tells you it is missing. So: a plausibility gate that
aborts without writing, a parse-failure ratio that aborts the run, no silent
fallbacks, and parse errors reported in every digest.

**Records are mutable.** Audit finding F-3 — job records are write-once, so
`status` never updates — is a wart in the jobs tracker and would be fatal here,
because deadlines *are* the product and CFP deadlines get extended routinely.
Events carry a `content_hash`, are re-checked on a cadence, and changes to
notable fields are recorded so the digest can report them.

**The digest is the product; the dashboard is packaging.** The audit found that
63% of the jobs scraper is presentation code, and that this weight kept
crowding out the actual analysis — for an audience of one person. So the
ranked weekly digest ships first and the dashboard ships last, fetching its
data rather than inlining it.

### Two filters, one score

Geography is a **filter and a facet**, never a term in the score. A blended
score that quietly demotes a perfect-fit event for being in Boston is a score
you stop trusting. Ranking is topical fit alone.

The university funds travel only for presenting, which splits geography by
event class:

| Event class | Rule |
|---|---|
| CFP conferences, workshops, special issues, summer schools | US, Canada, Mexico |
| Attend-only (talks, colloquia) | Online **or** within 120 mi of home |

### Taxonomy does not do ranking

`philevents/taxonomy.py` is a verbatim copy of the jobs repo's 8 main and 62
detail AOS categories. It drives faceting, aggregate views, and cross-dashboard
comparison. It does **not** drive relevance: even the detail categories cannot
tell an AI-alignment workshop from a business-ethics conference. Ranking is
semantic matching against the research profile.

Keep the two copies in sync deliberately. If the jobs taxonomy is revised,
mirror it here, or cross-dashboard comparisons stop being apples-to-apples.

---

## Layout

```
philevents/
  config.py      Runtime config; home coordinate lives outside git
  errors.py      The failure modes that must stay loud
  fetch.py       Rate-limited, identified HTTP client
  listing.py     Event-ID discovery + the plausibility gate  (regex, no bs4)
  detail.py      Event page parsing (JSON-LD; HTML fallback pending Phase 0)
  geo.py         Gazetteer lookup + haversine proximity
  store.py       SQLite schema, mutable upserts, change tracking
  taxonomy.py    AOS categories, shared with the jobs tracker
discover.py      Phase 0 — report the site's real structure
ingest.py        Phase 1 — sweep, filter, persist
tests/           33 stdlib unittest cases, network-free
```

`data/cities-na.txt` is not committed yet: a
[GeoNames](https://download.geonames.org/export/dump/) `cities5000` extract
filtered to US/CA/MX. Ingest runs without it, leaving coordinates null and
proximity filtering unavailable, and says so. GeoNames is CC BY 4.0 and needs
an attribution line when added.

---

## Data use

PhilEvents, PhilJobs and PhilPapers are all run by the PhilPapers Foundation,
whose [terms](https://philpapers.org/help/terms.html) severely restrict
redistribution of their data. This repository is private and stores event IDs,
URLs, dates and derived scores rather than mirroring their corpus. The client
identifies itself and rate-limits to one request every 0.5s. Their API docs
invite contact before building on their data, which is worth doing.

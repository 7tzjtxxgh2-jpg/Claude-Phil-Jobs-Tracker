# PhilEvents Conference Tracker — Design & Implementation Plan

**Status:** Draft for review. Brainstorming session 2026-08-21.
**Target:** a new, separate, **private** repository (proposed name `Claude-Phil-Conferences-Tracker`).
**Relationship to this repo:** shares taxonomy and geography code; shares no data and no hosting.

---

## 1. What this is, and why it is not a second jobs dashboard

The PhilJobs tracker is a **retrospective analytics** product. It answers *"how is the market
moving across years?"* Trend lines, co-occurrence matrices and choropleths are the right shape
for that question, and its organizing axis is the week an ad was posted.

This is a **prospective decision** product. It answers *"what do I submit to, and by when?"*
Its organizing axis is **time-to-deadline**. Its output is a short ranked queue of things you
can act on, not a wall of charts.

That difference drives nearly every decision below.

### The lesson carried over from the jobs audit

[`AUDIT-2026-08-21.md`](AUDIT-2026-08-21.md) found that 63% of `scraper.py` is presentation
code, that `docs/index.html` inlines the entire corpus as a 1.15 MB JavaScript blob (92% of the
page, at only 275 jobs), and that this presentation weight is what kept crowding out the actual
analysis — for an audience of one person.

**So: the digest ships before the dashboard.** The weekly ranked digest is the product. The
dashboard is packaging, and it gets built last, from data it fetches rather than data inlined
into it.

---

## 2. Decisions locked in this session

| Decision | Choice |
|---|---|
| Hosting | Private repo, no public surface |
| Delivery | Weekly Markdown digest (committed, read on GitHub mobile) + local HTML dashboard |
| Scope | CFP conferences & workshops, journal special issues & edited volumes, summer schools / grad conferences / fellowships, and attend-only events |
| Core model | Paper-centric: a paper inventory, matched to events, with submission tracking |
| Research profile | Free-text summary in a file, authored by your local AI |
| Geography | North America, in person; West Coast as a distinct view |
| History | Yes — primarily for recurrence prediction |
| Ranking | Topical fit only |

### The geography/ranking tension, resolved

You asked for fit-only ranking *and* gave geographic constraints. These are reconciled by
putting them at different stages:

- **Geography is a filter and a facet.** North America in-person is a hard pre-filter. West
  Coast is a saved view. The digest reports what it hid ("14 events filtered: 11 international,
  3 online-only") so the filter never silently costs you something.
- **Fit is the only score.** Within what survives the filter, ranking is pure topical relevance
  to your work.

This keeps the score interpretable. A blended score that quietly demotes a perfect-fit event
for being in Boston is a score you would stop trusting after the third time it surprised you.

---

## 3. Data source

### The good news: there is a sanctioned export

PhilEvents documents an export interface at [`philevents.org/code`](https://philevents.org/code).
Every search on the site produces a numeric ID, and that search can be re-fetched on demand:

```
https://philevents.org/search/format/{search_id}?format=csv       # CSV
https://philevents.org/search/format/{search_id}?format=calendar  # iCal
https://philevents.org/search/format/{search_id}?format=rss       # RSS
```

This is materially better than the PhilJobs approach, which parses `<h1>`/`<h2>` tags and table
rows and breaks whenever the markup shifts. We build discovery on the supported export and only
fall back to HTML for fields the export omits.

### Open item: the CSV schema is unverified

**I could not confirm the CSV's actual columns.** `philevents.org` and `philpapers.org` are both
blocked by this session's network egress policy. Production is unaffected — GitHub Actions
runners have open internet, exactly as your PhilJobs scraper does — but it means the field list
below is inferred from search results and event pages, not observed.

Expected per event, to be confirmed:

| Field | Confidence | Notes |
|---|---|---|
| Event ID | High | `philevents.org/event/show/{id}` — the natural primary key |
| Title | High | |
| Start / end date | High | iCal export implies structured dates |
| Location (city, country) | High | Browsable by city |
| Topics (PhilPapers categories) | High | Browsable by topic; see §5 |
| Submission deadline | **Medium** | Shown on event pages; may be free text, not a column |
| CFP body text | **Low** | Probably requires fetching the detail page |
| Event type | Medium | Conference / workshop / special issue distinction |
| Custom tags | Medium | Site supports free tags alongside topics |

**Resolution, one of:** (a) you run one export and paste me the header row, or (b) Phase 1 ships
a schema-discovery run in Actions that dumps the header and one sample row. (a) is faster.

### Terms of service — a real constraint

PhilPapers' [terms](https://philpapers.org/help/terms.html) and
[API documentation](https://philpapers.org/help/api) state that use is subject to conditions that
"severely restrict the redistribution of PhilPapers' data," and encourage contacting them before
building on it. PhilJobs, PhilEvents and PhilPapers are all run by the same foundation.

Consequences for this design:

1. **Store references, not mirrors.** Persist event IDs, URLs, dates, our own derived scores and
   short quoted excerpts. Do not build a public copy of their listing corpus.
2. **The private-repo choice already satisfies this** — nothing is republished.
3. **Rate-limit politely.** Match the PhilJobs scraper's 0.5s inter-request delay, identify the
   client in a User-Agent string, and prefer the export endpoint over page fetches wherever it
   suffices.
4. **Worth an email.** Their docs invite it. A one-paragraph note describing a private,
   personal-use tool costs nothing and removes ambiguity.

### Why not just use PhilEvents' own topic-following?

PhilEvents [already lets you follow topics and filter by distance](https://philevents.org/help/).
So topic filtering is not the value this tool adds. Its edge is:

- **Ranking, not filtering.** A relevance-ordered shortlist, not an unordered feed.
- **Matching against your actual work.** Your research profile and your specific papers, not a
  checkbox list of topic tags.
- **Per-paper routing.** *Which* of your papers belongs at this event.
- **Recurrence forecasting.** When next year's CFP is expected to open (§7).
- **Pipeline state.** What you submitted where, and what you're waiting on.

If the tool ever reduces to "a filtered feed," PhilEvents already does that better. These five
things are the reason it exists.

---

## 4. Cost — not the constraint

PhilEvents lists ~765 upcoming events at any time and takes in
[100+ new listings a month](https://feedreader.com/observe/philevents.org): call it
**1,500–2,500 new events/year** across all four scope categories.

Estimated at ~1,500 cached input tokens (profile + taxonomy + instructions), ~1,000 fresh input
tokens (event text) and ~300 output tokens per event, with prompt caching and the Batch API's
50% discount: **roughly $8–16/year.** Same order as the jobs tracker's $14/yr.

**This kills a design I had intended to propose.** I was going to suggest a cheap taxonomy-based
pre-filter so we only spend tokens on plausibly-relevant events. At these prices that is
premature optimization, and it would cost recall precisely on the odd interdisciplinary events
that are often the interesting ones. We can afford to score everything properly.

The scarce resource is **your attention**. Spend freely on scoring; be ruthless about what
reaches the digest.

---

## 5. Taxonomy — answering the "too granular?" question

Your instinct was that the jobs AOS taxonomy might be too granular. My finding is that the
problem is **inverted**, and that one taxonomy cannot do both jobs here.

For trend aggregation, 8 main categories is right. For conference *fit*, the 8 categories are
nearly useless — "Ethics" is likely a third of all philosophy events. But even the 62
subcategories are too coarse to separate *"a workshop on AI alignment and moral status"* from
*"a business ethics conference"*; both land in one or two buckets. **What determines fit is
finer-grained than any fixed taxonomy** — it is the specific themes in the CFP against the
specific themes in your work.

So: **two mechanisms, two purposes.**

| Purpose | Mechanism |
|---|---|
| Faceted browsing, "what's happening in my field," cross-dashboard comparison | Reuse the 8 main + 62 detail AOS categories from this repo |
| Actual ranking | Semantic match of CFP text against your research profile and paper abstracts |

### Reuse plan

Events arrive **pre-tagged with PhilPapers categories** (5 top clusters, ~40 broad areas, a
5-level tree) — unlike PhilJobs, which gives free-text AOS that Claude must normalize.

This lets us copy the single best design decision in the jobs project: **publisher-supplied
category as ground truth.** Just as `position_type_from_category()` derives position type
deterministically from PhilJobs's own category and only falls back to Claude when ambiguous, we
build a static **PhilPapers-topic → AOS-category mapping table** and fall back to Claude only for
unmapped or absent topics. Deterministic, free, auditable, and stable across model changes.

Directly reusable from `scraper.py`:

- `MAIN_AOS_CATEGORIES`, `DETAIL_AOS`, `MAIN_AOS_COLORS` (lines ~184–280)
- `US_STATES`, `WEST_COAST_CITIES`, `WEST_COAST_METROS`, `get_west_coast_metro()` (lines ~22–120)
- `write_json_atomic()`, `js_json()` escaping discipline
- The taxonomy-versioning + archive-on-bump pattern

**Bonus:** shared taxonomy makes a genuinely novel question askable — *"ethics hiring is
declining, but is ethics conference volume rising?"* You'd be well placed to answer that.

---

## 6. Architecture

```
PhilEvents saved-search CSV exports
  │
  ▼
ingest.py
  ├── fetch new + changed event IDs via export endpoint
  ├── fetch detail pages for CFP text (0.5s delay, polite UA)
  ├── upsert into SQLite  ← NOT write-once; see §6.2
  ├── geography filter (North America, in person)
  ├── map PhilPapers topics → AOS (deterministic table, Claude fallback)
  ├── score NEW/CHANGED events only (Batch API, structured outputs)
  └── detect recurrence series
       │
       ├──► digest_YYYY-MM-DD.md   (committed — read on phone)
       ├──► data/events.db          (SQLite)
       └──► docs/index.html + docs/events.json  (local dashboard, data NOT inlined)
```

### 6.1 Storage: SQLite, not one large JSON

The jobs project keeps a single 1.7 MB `all_jobs.json` and rewrites it whole every 10 jobs during
reclassification. The audit named this as the structural gate blocking its most valuable
improvement. We do not repeat it.

```
events         (id PK, title, url, start_date, end_date, deadline, city, state,
                country, is_online, event_type, raw_topics, first_seen, last_seen,
                status, content_hash)
classifications(event_id, aos_main, aos_detail, taxonomy_version, source)
scores         (event_id, paper_id, fit_score, reasoning, profile_version,
                model, scored_at)
papers         (id PK, title, abstract, keywords, status)
submissions    (id PK, paper_id, event_id, state, submitted_on, decision_on, notes)
series         (id PK, canonical_title, host, member_event_ids, cadence,
                typical_cfp_month, typical_deadline_month)
```

Scores are keyed by **`profile_version`** — a hash of `profile.md`. When you revise your research
summary, the system knows exactly what needs rescoring. This is the same idea as the jobs
project's `taxonomy_version`, applied to the thing that actually changes here.

### 6.2 Records must be mutable — this one is critical

Audit finding **F-3**: job records are write-once, so `status` never updates and 130 of 275 jobs
carry past deadlines while all 275 still read `active`.

In the jobs tracker that is a wart. **Here it would be fatal**, because deadlines *are* the
product. And deadline changes are demonstrably common in this domain — one event surfaced during
research is literally titled *"CFP: EXTENDED DEADLINE — Towards Comparative Philosophy of Science."*

So every run re-checks all events whose deadline has not yet passed, compares a `content_hash`,
and updates on change. Deadline extensions, date changes and cancellations are first-class
events that the digest reports:

> ⏰ **Deadline extended** — *Comparative Philosophy of Science* moved from Sep 1 → Oct 15.

### 6.3 Modern API usage

The audit found three things that break on current models, all of which we simply build correctly
from the start:

1. **No `temperature=0`.** The parameter was removed on current models and returns a 400. Use
   `output_config: {effort: ...}`. Note this means the README cannot claim determinism the way
   the jobs README does — the claim gets rewritten, not just the code.
2. **Do not read `response.content[0].text`.** Thinking is on by default, so block 0 is typically
   a thinking block. Iterate and select `block.type == "text"`.
3. **Structured outputs** replace hand-rolled JSON sanitization entirely.
4. **Prompt caching** for the static profile + taxonomy + instructions block.
5. **Batch API** for scoring and for the history backfill.
6. **Pin every dependency** (audit F-10: nothing is pinned anywhere today).

---

## 7. Recurrence forecasting

The highest-value use of history, and the thing that makes this tool *anticipatory* rather than
reactive.

**Problem it solves:** you currently learn a conference exists when its CFP appears — often too
late to write something new for it.

**Method:**
1. Normalize titles: strip years, ordinals ("Sixth International Workshop on X" → "International
   Workshop on X"), and boilerplate ("CFP:", "Call for Abstracts —").
2. Group by normalized title + host institution + organizing society.
3. Require ≥2 past instances to declare a series.
4. From member events, derive typical CFP-open month, typical deadline month, typical event month.
5. Forecast the next instance, with an explicit confidence based on how regular the series is.

**Output:** a *writing calendar*.

> 📅 **Expected to open in the next 60 days**
> - *Pacific APA* — CFP typically opens late Aug, deadline ~Sep 1. 4/4 years regular.
> - *SPEP Annual* — CFP typically opens Dec, deadline ~Jan 15. 3/3 years regular.

That converts the tool from "here's what's open now" into "here's what to be writing for."

---

## 8. The weekly digest — the actual product

Committed Markdown, read on your phone in the GitHub app. Ordered so the top of the file is
always the most time-critical thing.

```markdown
# Conference Digest — 2026-08-24

## 🔴 Closing in 21 days
- **Deadline Sep 3** — Workshop on Moral Status and AI (Portland, OR)
  Best match: "Paper title" (fit 8.7/10) · [event](…)

## ⭐ New this week — top matches
1. **Fit 9.1** — Title (Seattle, WA) · deadline Nov 1
   Matches: "Paper title". Why: …one or two sentences…
2. …

## ⏰ Changed
- Deadline extended: … (Sep 1 → Oct 15)

## 📅 Expected to open soon  (recurrence forecast)
- Pacific APA — CFP usually opens late Aug

## 📋 Your pipeline
- "Paper A" → submitted to X on Jul 2 · awaiting decision (50 days)

## 🔇 Filtered out
14 events hidden: 11 international, 3 online-only. [see all]
```

**Cadence:** weekly, Monday, matching the jobs scraper. The 21-day deadline horizon guarantees
nothing can slip through between runs, so a second daily workflow isn't needed.

### Pipeline updates

You edit `submissions.yaml` in the repo — workable from the GitHub mobile app, no extra
infrastructure, no database to host, and full version history for free.

---

## 9. Phasing

Deliberately ordered so you have something useful early, and so the presentation layer cannot
eat the project.

| Phase | Deliverable | Notes |
|---|---|---|
| **0** | Confirm CSV schema | Blocked on a live fetch — needs one export from you, or a discovery run in Actions |
| **1** | Ingest → SQLite → geography filter → plain listing digest. **No AI.** | Proves the pipeline end to end and validates the source before any spend |
| **2** | `profile.md` + fit scoring + ranked digest | The core value. Useful on its own |
| **3** | Paper inventory + per-paper matching + `submissions.yaml` | Completes the paper-centric model |
| **4** | History backfill + recurrence forecasting | The writing calendar |
| **5** | Local HTML dashboard | Last. Data fetched from `events.json`, never inlined |

Phase 1 is a hard gate: if the export doesn't carry deadlines and topics, the design changes and
it is much cheaper to learn that before Phase 2.

---

## 10. Open items

1. **CSV schema** — the one true blocker. Paste me a header row, or approve a discovery run.
2. **Repo name** — proposed `Claude-Phil-Conferences-Tracker`.
3. **Paper inventory format** — proposal: one Markdown file per paper in `papers/`, with
   YAML front matter (title, status, keywords) and the abstract as body. Keeps drafts readable
   and diffable.
4. **"North America" precision** — US + Canada? Mexico? Any hard travel-time cutoff?
5. **Digest volume** — how many new events per week do you actually want to see? Proposal: top 5
   by fit, plus everything with a deadline inside 21 days, plus anything scoring above a
   threshold you can tune.
6. **Attend-only events** — you included these in scope. They can't be submitted to, so they need
   a separate, quieter digest section rather than competing with CFPs for ranking. Confirm?
7. **Emailing PhilPapers** about the personal-use tool.

---

## 11. Summary of research findings

| Finding | Impact |
|---|---|
| Sanctioned CSV/iCal/RSS export exists | No fragile HTML scraping for discovery |
| ToS severely restricts redistribution | Private repo; store references, not mirrors |
| Events arrive pre-tagged with PhilPapers categories | Deterministic topic→AOS mapping; Claude only for gaps |
| PhilEvents already does topic-following | The edge must be ranking, per-paper matching, recurrence, pipeline |
| GitHub Pages can't be private outside Enterprise Cloud | Digest + local dashboard instead |
| Full scoring costs ~$8–16/yr | No pre-filter needed; attention is the constraint, not money |
| Deadline extensions are common | Records must be mutable — the jobs project's F-3 bug would be fatal here |
| `philevents.org` blocked in this session | Schema unverified; Phase 0 exists to close this |

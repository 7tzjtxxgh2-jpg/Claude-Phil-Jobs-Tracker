# PhilJobs Market Analytics Dashboard

An automated system that scrapes philosophy job postings from [PhilJobs.org](https://philjobs.org) every week, classifies them using the Claude AI API, and generates an interactive analytics dashboard hosted on GitHub Pages. The goal is to track multi-year trends in the academic philosophy job market to inform research specialization and career planning decisions.

**Owner:** PhD student, Philosophy 
**Timeline:** 3-year longitudinal data collection (until job market entry)
**Primary goal:** Understand which AOS categories and position types are growing or declining, with particular interest in West Coast institutions

**Live dashboard (US):** `https://[your-github-username].github.io/Claude-Phil-Jobs-Tracker/`
**Live dashboard (International):** `https://[your-github-username].github.io/Claude-Phil-Jobs-Tracker/international.html`

---

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Automation & Schedule](#automation--schedule)
3. [Data Collection](#data-collection)
4. [Deduplication Strategy](#deduplication-strategy)
5. [AI Classification Methodology](#ai-classification-methodology)
6. [AOS Taxonomy](#aos-taxonomy)
7. [Position Type Taxonomy](#position-type-taxonomy)
8. [Geographic Methodology](#geographic-methodology)
9. [Dashboard Features](#dashboard-features)
10. [Data Files](#data-files)
11. [Setup & Configuration](#setup--configuration)
12. [Running Manually](#running-manually)
13. [Known Issues & Roadmap](#known-issues--roadmap)

---

## System Architecture

```
PhilJobs.org
    │
    ▼
scraper.py  (Python)
    ├── Fetches all active job IDs from listing page
    ├── Scrapes full details for each job
    ├── Deduplicates against historical data (MD5 hash)
    ├── Classifies NEW jobs only via Claude API
    ├── Resolves missing US states via Claude API
    ├── Calculates weekly trend aggregates
    ├── Computes co-occurrence matrix
    ├── Generates docs/index.html (US dashboard)
    └── Generates docs/international.html (International dashboard)
         │
         ▼
    GitHub Actions (commits data/ and docs/ to repo)
         │
         ▼
    GitHub Pages (serves docs/ as live website)
```

**Core files:**
| File | Purpose |
|------|---------|
| `scraper.py` | Main script — scraping, classification, trend calculation, HTML generation |
| `.github/workflows/weekly-scrape.yml` | GitHub Actions automation |
| `data/all_jobs.json` | Master historical record of all jobs and trends |
| `data/co_occurrence.json` | Computed AOS co-occurrence matrix |
| `data/snapshot_YYYY-MM-DD.json` | Weekly scrape snapshots |
| `docs/index.html` | US market dashboard (served via GitHub Pages) |
| `docs/international.html` | International market dashboard |

---

## Automation & Schedule

The scraper runs automatically via **GitHub Actions** every **Monday at 14:00 UTC (9:00 AM Central Time during CDT)**.

**Cron expression:** `0 14 * * 1`

On each run, GitHub Actions:
1. Checks out the repository
2. Installs Python dependencies (`requests`, `beautifulsoup4`, `anthropic`)
3. Runs `scraper.py`
4. Commits any changes to `data/` and `docs/` with message `Weekly scrape: YYYY-MM-DD`
5. Pushes to `main` branch (GitHub Pages auto-updates)
6. On failure: automatically opens a GitHub Issue titled `⚠️ Weekly scrape FAILED — YYYY-MM-DD` with a link to the failed run log

**Manual trigger:** Go to repository → Actions tab → "Weekly PhilJobs Scraper" → "Run workflow"

**Required secret:** The repository must have `CLAUDE` set as a GitHub Actions secret containing a valid Anthropic API key. Without it, new jobs will receive fallback classifications and will be reclassified on the next successful run.

---

## Data Collection

### How jobs are found

The scraper uses PhilJobs's detailed query view (`/jobQuery/execute?view=On+screen+-+detailed`) to retrieve all currently active listings. It paginates through all result pages, collecting job IDs. If this endpoint fails, it falls back to scraping job links from the homepage.

A 0.5-second delay is inserted between each individual job page request to avoid overloading the PhilJobs server.

### Fields collected per job

| Field | Source | Notes |
|-------|--------|-------|
| `id` | PhilJobs URL | Numeric job ID |
| `url` | Constructed | `philjobs.org/job/show/{id}` |
| `institution` | `<h2>` tag | Hiring institution name |
| `title` | `<h1>` tag | Job title |
| `job_category` | Table row | PhilJobs's own category label |
| `aos` | Table row | Raw AOS text from posting |
| `aoc` | Table row | Raw AOC (Area of Competence) text |
| `location` | Table row | Free-text location string |
| `state` | Parsed from location | 2-letter US state code, or `null` |
| `country` | Parsed from location | Country name |
| `city` | Parsed from location | City name (first part before comma) |
| `deadline` | Table row | Hard application deadline |
| `posted_date` | Table row | "Time created" on PhilJobs |
| `description` | Table row | Full job description text |
| `workload` | Table row | Full-time / part-time |
| `vacancies` | Table row | Number of positions |
| `start_date` | Table row | Anticipated start date |
| `application_type` | Table row | How to apply |
| `application_url` | Table row | Link to application portal |
| `contact_email` | Table row | Contact email if provided |
| `hash` | Computed | MD5 of `institution_title` — used for deduplication |
| `scraped_date` | System clock | ISO datetime when this job was first scraped |
| `status` | Title text | `active` or `expired` (if title contains "(EXPIRED)") |
| `classification` | Claude API | Full classification object — see [AI Classification](#ai-classification-methodology) |
| `job_type` | Synced from classification | Top-level copy of `position_type` for backward compatibility |
| `institution_type` | Synced from classification | Top-level copy |

---

## Deduplication Strategy

A job is considered unique based on its **PhilJobs numeric job ID**. The hash stored in `all_jobs.json` is:

```python
hash = MD5(job_id)
```

On each run, only jobs whose hash is **not** in the existing `all_jobs.json` are treated as new. This means:
- The same posting appearing multiple weeks on PhilJobs is counted **only once** (when first seen)
- Two genuinely separate openings at the same institution with identical titles are correctly counted as two distinct jobs (they have different PhilJobs IDs)
- "New jobs this week" in the dashboard = genuinely new market entries, not total active listings

Weekly trend data reflects new entries per week, not the total active job pool size.

**Migration note:** Prior to March 2026, hashes were computed from `MD5(institution_title)`. The scraper automatically migrates all existing records to the new ID-based format on first run — this is a one-time, safe operation that does not alter any other job data.

---

## AI Classification Methodology

### Why Claude API?

Raw PhilJobs data includes free-text AOS descriptions (e.g., "Ethics, broadly construed; Philosophy of Mind") that are too varied for simple keyword matching. Claude Haiku is used to normalize these into a controlled taxonomy, classify position types from job titles and descriptions, and identify institution types — tasks that benefit from linguistic understanding.

### Model and settings

- **Model:** `claude-haiku-4-5-20251001`
- **Temperature:** `0` (deterministic — same input always produces same output)
- **Max tokens:** `1000`
- **Retries:** 3 attempts per job on API failure, with 1-second backoff

### What gets classified

**Only new jobs are classified** on each weekly run. Jobs already in `all_jobs.json` with a valid `classification` object are never re-sent to the API. This keeps API costs low and preserves consistency of historical data.

### Classification output

Each job receives a `classification` object with these fields:

```json
{
  "main_aos": ["Ethics", "Social & Political Philosophy"],
  "detail_aos": {
    "Ethics": ["Biomedical Ethics / Bioethics"],
    "Social & Political Philosophy": ["Philosophy of Law"]
  },
  "position_type": "Tenure-Track",
  "institution_type": "Research University",
  "state_us": "NY",
  "reasoning": "Job title and AOS explicitly indicate a tenure-track position in bioethics and philosophy of law."
}
```

### Validation

After receiving Claude's response, the scraper validates and sanitizes every field:
- `main_aos` entries not in the canonical 8-category list are dropped; if none remain, falls back to `["Open"]`
- `detail_aos` subcategories not in the defined list for that main category are dropped
- `position_type` must be one of the 5 canonical values; old legacy labels (e.g., `"Tenure-track"`, `"Postdoc"`) are automatically migrated
- `state_us` must be a 2-letter alpha code; anything else becomes `"INTERNATIONAL"`

### Fallback behavior

If the API key is missing, the `anthropic` package is not installed, or all 3 retry attempts fail, the job receives a fallback classification:

```json
{
  "main_aos": ["Open"],
  "detail_aos": {"Open": []},
  "position_type": "Other",
  "institution_type": "Other",
  "reasoning": "classification_failed"
}
```

Jobs with `reasoning: "classification_failed"` are detected on subsequent runs and reclassified automatically once the API is available.

### Checkpoint saves

During bulk reclassification, the data file is saved to disk every 10 jobs as a checkpoint. This prevents data loss if a long reclassification run is interrupted.

---

## AOS Taxonomy

The taxonomy has two levels: 8 **main categories** and fine-grained **subcategories** within each.

### Main AOS Categories

| Category | Color |
|----------|-------|
| Ethics | `#ef4444` (red) |
| Social & Political Philosophy | `#3b82f6` (blue) |
| Value Theory / Aesthetics | `#06b6d4` (cyan) |
| History of Philosophy | `#8b5cf6` (purple) |
| Non-Western & Cross-Cultural Philosophy | `#ec4899` (pink) |
| Metaphysics & Epistemology | `#10b981` (green) |
| Science, Logic, & Mathematics | `#f59e0b` (amber) |
| Open | `#6b7280` (gray) |

"Open" means the posting explicitly accepts any AOS — the position is not specialized. This is distinct from a classification failure.

**A single job can belong to multiple main AOS categories** (e.g., a position in "Philosophy of Law" might be classified under both Ethics and Social & Political Philosophy). The main chart counts each main-category assignment, not each unique job, so weekly totals across categories will exceed the total new job count.

### Subcategories

**Taxonomy version:** `2026-05-16` — revised from the original to add Virtue Ethics, Philosophy of Disability, Public Philosophy, and Phenomenology, and to remove a redundant "Social & Political Philosophy (General)" duplicate. When this version changes, the scraper backs up the prior classification on each job under `classification_v1` / `_v2` / etc. and re-classifies under the new taxonomy.

<details>
<summary>Ethics (12 subcategories)</summary>

- Meta-Ethics
- Normative Ethics
- **Virtue Ethics** *(added 2026-05-16)*
- Biomedical Ethics / Bioethics
- Neuroethics
- AI, Technology, and Information Ethics
- Environmental Ethics
- Animal Ethics
- Food and Agricultural Ethics
- Business Ethics
- Ethics of Population, Future Generations, and Global Justice
- Ethics (General / Applied Ethics, Broadly Construed)
</details>

<details>
<summary>Social & Political Philosophy (10 subcategories)</summary>

- Social and Political Philosophy (General / Political Theory)
- Philosophy of Law
- Philosophy of Race
- Philosophy of Gender
- **Philosophy of Disability** *(added 2026-05-16)*
- Feminist Philosophy
- Philosophy of Sexuality and Queer Theory
- PPE (Politics, Philosophy, and Economics)
- Philosophy of Education
- **Public Philosophy** *(added 2026-05-16)*
</details>

<details>
<summary>Value Theory / Aesthetics (7 subcategories)</summary>

- Aesthetics (General)
- Philosophy of Art
- Philosophy of Music
- Philosophy of Film and Media
- Philosophy of Literature
- Value Theory / Axiology
- Value Theory / Aesthetics (General)
</details>

<details>
<summary>History of Philosophy (8 subcategories)</summary>

- Ancient Greek and Roman Philosophy
- Medieval and Renaissance Philosophy
- Early Modern Philosophy (17th/18th Century)
- 19th/20th Century Philosophy
- American Philosophy
- Continental Philosophy
- **Phenomenology** *(added 2026-05-16)*
- History of Philosophy (General)
</details>

<details>
<summary>Non-Western & Cross-Cultural Philosophy (7 subcategories)</summary>

- Asian Philosophy
- African/Africana Philosophy
- Arabic and Islamic Philosophy
- Latin American Philosophy
- Native American / Indigenous Philosophy
- Comparative Philosophy / Cross-Cultural
- Non-Western Philosophy (General)
</details>

<details>
<summary>Metaphysics & Epistemology (7 subcategories)</summary>

- Metaphysics
- Epistemology
- Philosophy of Mind
- Philosophy of Language
- Philosophy of Action
- Philosophy of Religion
- Metaphysics & Epistemology (General)
</details>

<details>
<summary>Science, Logic, & Mathematics (10 subcategories)</summary>

- Philosophy of Science (General)
- Philosophy of Biology
- Philosophy of Physics
- Philosophy of Cognitive Science
- Philosophy of Computing / Philosophy of AI
- Logic
- Philosophy of Mathematics
- Philosophy of Social Science
- Decision Theory
- Science, Logic, & Mathematics (General)
</details>

### Cross-Cutting Areas

Four subcategories are designated as "cross-cutting" because they appear across multiple main categories and have particular sociological significance in the job market: **Feminist Philosophy**, **Philosophy of Race**, **Philosophy of Gender**, and **Philosophy of Law**. These are tracked separately in the dashboard to reveal patterns that pure main-category analysis would miss.

---

## Position Type Taxonomy

Every job is assigned exactly one of these five position types:

| Type | Description |
|------|-------------|
| **Tenure-Track** | Explicitly described as tenure-track; "Assistant Professor (tenure-track)" or any TT position |
| **Postdoc / Fellowship** | Postdoctoral positions, postdoc fellowships, named fellowships (Mellon, ACLS, etc.), research fellowships — fixed-term but research-focused |
| **Visiting / Adjunct / Lecturer (Fixed-Term)** | Visiting Assistant Professor, Visiting Lecturer, Adjunct, Instructor, fixed-term Lecturer — teaching-focused with no path to permanence |
| **Tenured / Continuing / Permanent** | Associate Professor (tenured), Full Professor, Senior Lecturer (permanent/continuing), any explicitly permanent or continuing non-tenure-track position |
| **Other** | Department chairs with no faculty component, deans, purely administrative or non-academic positions |

The Position Type Trends chart in the dashboard shows how the volume of each type has changed over time. Within each type, the chart also shows the AOS breakdown — for example, what proportion of tenure-track jobs in a given week were in Ethics vs. Metaphysics.

---

## Geographic Methodology

### US vs. International determination

A job is classified as **US** if its `state` field is set (a 2-letter state code). It is classified as **International** if `state` is null. The two dashboards (`index.html` and `international.html`) filter on this field.

### State parsing

The scraper first attempts to identify a US state from the raw location string using a lookup table of all 50 states, D.C., and common variants (e.g., "Washington D.C.", "Washington, DC"). If a match is found, the state code is set directly.

For jobs where state could not be parsed from the location string (e.g., the location is just an institution name, or uses an unusual format), the Claude API is used as a secondary resolver. It is asked to return only a 2-letter state code or "INTERNATIONAL" based on its training knowledge of the institution's location. It is **not** given access to browse the web — it uses only what it already knows about the institution.

### US Regions

States are grouped into four regions for the Regional Trends chart:

| Region | States |
|--------|--------|
| **West** | CA, OR, WA, AK, HI, NV, ID, MT, WY, UT, CO, AZ, NM |
| **Northeast** | ME, NH, VT, MA, RI, CT, NY, NJ, PA, DC |
| **South** | DE, MD, VA, WV, NC, SC, GA, FL, KY, TN, AL, MS, AR, LA, OK, TX |
| **Midwest** | OH, IN, IL, MI, WI, MN, IA, MO, ND, SD, NE, KS |

Note: Washington D.C. is grouped with the Northeast on cultural grounds.

### West Coast city tracking

For jobs in CA, OR, or WA, the scraper attempts to match the city field against a list of tracked West Coast cities. City matching is substring-based (case-insensitive). Tracked cities:

- **Bay Area / NorCal:** Berkeley, Stanford, San Francisco, Oakland, San Jose, Santa Cruz, Davis
- **SoCal:** Los Angeles, San Diego, Irvine, Claremont, Riverside
- **Pacific Northwest:** Seattle, Portland, Eugene, Tacoma, Olympia

Each city has associated latitude/longitude coordinates for potential map plotting.

### Hiring season

Philosophy has a well-defined hiring cycle. The scraper marks weeks falling between **September and January** (months 9, 10, 11, 12, 1) as "hiring season." These weeks are highlighted with background shading on trend charts.

---

## Dashboard Features

Both dashboards (`index.html` for US, `international.html` for International) contain the same set of charts and interactive elements.

### Summary statistics bar
- New jobs this week
- Total unique jobs tracked
- Most active AOS category this week
- Number of weeks tracked

### Market Overview chart
- Line chart: one line per main AOS category + one "Total New Jobs" line
- X-axis: weeks (ISO date)
- Y-axis: count of new job classifications (jobs with multiple AOS count once per AOS)
- Hiring season highlighted with background shading
- Interactive: hover for exact values; click legend to show/hide categories

### Category cards
- One card per main AOS category
- Shows: total jobs in that category, current-week count, week-over-week change indicator
- Click any card to open the **drill-down modal**

### Drill-down modal (per category)
- Subcategory breakdown table with counts
- Trend chart showing the parent category line plus all subcategory lines
- Job type pie chart (how many in this category are TT vs. postdoc vs. visiting, etc.)
- Institution type pie chart (research university vs. teaching college)
- US states breakdown (top states by job count)
- Key insights (auto-generated text summaries)

### Position Type Trends chart
- Separate from Market Overview — tracks the 5 position types over time
- Each line = one position type; shows its volume per week
- Click any line to see its AOS breakdown

### AOS Co-occurrence matrix
- Heatmap showing how often pairs of main AOS categories appear in the same job posting
- Helps identify which specializations are commonly bundled together

### Solo vs. Joint postings chart
- For each main category: how many jobs listed it as their *only* AOS vs. alongside other categories
- Reveals which specializations tend to appear as pure hires vs. cross-disciplinary

### Cross-cutting areas chart
- Trend lines for Feminist Philosophy, Philosophy of Race, Philosophy of Gender, Philosophy of Law
- Shows their frequency over time and which main categories they appear with most often

### US Geographic Overview (US dashboard only)
- Interactive D3.js choropleth map of the US — states shaded by job count
- Hover tooltip showing state name and count
- Click a state to open a detail panel showing jobs in that state
- Regional trend lines: West, Northeast, South, Midwest

### West Coast detail chart
- Bar chart showing city-level job counts for tracked West Coast cities

---

## Data Files

### `data/all_jobs.json`

The master data file. Structure:

```json
{
  "jobs": [ { ...job object... } ],
  "weekly_snapshots": [
    {
      "date": "2026-03-17",
      "total_jobs": 125,
      "new_jobs": 12,
      "new_job_ids": ["1234", "5678"]
    }
  ],
  "weekly_trends": [
    {
      "date": "2026-03-17",
      "new_jobs_count": 12,
      "main_aos_counts": { "Ethics": 3, "Metaphysics & Epistemology": 2 },
      "detail_aos_counts": { "Ethics::Biomedical Ethics / Bioethics": 1 },
      "position_type_counts": { "Tenure-Track": 5, "Postdoc / Fellowship": 4 },
      "position_type_by_aos": { "Ethics": { "Tenure-Track": 2 } },
      "institution_type_counts": { "Research University": 8 },
      "state_counts": { "NY": 2, "CA": 3 },
      "country_counts": { "United States": 12 },
      "west_coast_city_counts": { "Berkeley": 1 }
    }
  ]
}
```

### `data/co_occurrence.json`

Computed from all classified jobs. Contains:
- `main_aos_matrix`: how many times each pair of main categories co-occurs in a single job
- `main_aos_solo_vs_joint`: for each category, solo vs. multi-category postings
- `detail_aos_by_context`: for each detail subcategory, what main categories it appeared in (solo vs. with others)
- `cross_cutting_areas`: per-week counts and main-category breakdowns for the 4 cross-cutting areas

### `data/snapshot_YYYY-MM-DD.json`

One file per run. Contains all currently active jobs on PhilJobs at that moment and which ones were new. Useful for auditing.

---

## Setup & Configuration

### First-time setup

1. Fork or clone the repository
2. Enable GitHub Pages: Settings → Pages → Source: `Deploy from a branch` → Branch: `main`, Folder: `/docs`
3. Add the Anthropic API key as a repository secret:
   - Settings → Secrets and variables → Actions → New repository secret
   - Name: `CLAUDE`
   - Value: your Anthropic API key
4. Enable Actions write permissions: Settings → Actions → General → Workflow permissions → Read and write

### Dependencies

Python packages (installed automatically by GitHub Actions):
- `requests` — HTTP requests to PhilJobs
- `beautifulsoup4` — HTML parsing
- `anthropic` — Claude API client

JavaScript (loaded from CDN, no installation needed):
- [Tailwind CSS](https://tailwindcss.com) — utility-first CSS framework
- [Chart.js](https://www.chartjs.org) — interactive line/bar/pie charts
- [D3.js v7](https://d3js.org) — US choropleth map
- [TopoJSON client](https://github.com/topojson/topojson-client) — geographic data format for maps

---

## Running Manually

To run locally (useful for testing or forcing a reclassification):

```bash
# Install dependencies
pip install requests beautifulsoup4 anthropic

# Set your API key
export ANTHROPIC_API_KEY=your_key_here
# OR on Windows:
# set ANTHROPIC_API_KEY=your_key_here

# Run the scraper
python scraper.py
```

The scraper will:
1. Scrape PhilJobs for all active jobs
2. Identify new ones (not in `data/all_jobs.json`)
3. Classify new jobs via Claude API
4. Resolve any missing US states via Claude API
5. Rebuild weekly trends if any jobs needed reclassification
6. Generate `docs/index.html` and `docs/international.html`

Open either HTML file directly in a browser to preview the dashboard.

---

## Known Issues & Roadmap

### Current known issues

- **West Coast city detail in modal:** The category drill-down modal has a "West Coast Detail" section that is not yet wired up with data — it remains hidden. The underlying data (`westCoastData`) is collected and available; the JS to populate the display has not been implemented.
- **Cross-cutting chart X-axis:** The cross-cutting areas chart derives its week labels from the cross-cutting data itself rather than the global `data.dates` array. If a cross-cutting area had no jobs in early weeks, its X-axis will appear to start later than other charts.

### Roadmap

- **International dashboard:** A second page (`international.html`) for non-US jobs is in active development, including a world choropleth map and continent/region trend lines.
- **US/International navigation:** Once the international dashboard is built, both pages will have navigation links between them.
- **West Coast city modal wiring:** Populate `#westCoastCities` in the drill-down modal for West Coast-relevant categories.
- **Cross-cutting chart alignment:** Standardize X-axis to use global `data.dates`.
- **Accessibility improvements:** Add ARIA roles/labels to modals and chart canvas elements, ESC key handler for modals.
- **Meta tags:** Add `<meta name="description">` and Open Graph tags for link sharing.

### Design decisions and rationale

**Why weekly scrapes and not daily?** The philosophy job market is slow-moving; new postings appear in clusters, and weekly granularity is sufficient to track hiring season patterns. Weekly also keeps API costs and GitHub Actions minutes low.

**Why count new jobs, not active jobs?** The total active listing count fluctuates with expirations and removals. New job entries per week is a cleaner signal of actual market activity.

**Why Claude Haiku and not a more powerful model?** Haiku is fast, cheap, and sufficiently accurate for structured extraction tasks with a well-defined taxonomy. Temperature=0 ensures deterministic and consistent classification across runs.

**Why separate US and International dashboards?** The US and international markets have different structures (e.g., UK REF cycles, European fellowship structures vs. US tenure track), different geographic visualizations, and potentially different user interests. Keeping them separate allows each to be developed independently.

---

## Contact & Maintenance

**Repository:** `https://github.com/[your-username]/Claude-Phil-Jobs-Tracker`
**Primary maintainer:** Owner (PhD student in Philosophy, Marquette University)
**Last README update:** March 2026

For scrape failures, check the automatically-opened GitHub Issue in the Issues tab for a link to the failed run log.

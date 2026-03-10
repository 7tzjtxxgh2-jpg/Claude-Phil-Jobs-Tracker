# PhilJobs Market Analytics - Project Specification

## Project Overview

An automated system that scrapes philosophy job postings from PhilJobs.org weekly, tracks market trends over time, and provides interactive analytics to inform academic career planning decisions.

**Owner:** PhD student in Philosophy (Existentialism/Sartre) at Marquette University  
**Timeline:** 3-year data collection period (until job market entry)  
**Primary Goal:** Identify which philosophy specializations have the best job prospects, particularly on the West Coast

---

## System Architecture

### 1. Automated Scraper (`scraper.py`)
- **Runs:** Every Monday at 9 AM UTC via GitHub Actions
- **Scrapes:** PhilJobs.org for all active job listings
- **Extracts:** Full details from each job posting page
- **Tracks:** Only NEW unique jobs each week (not total active jobs)

### 2. Data Storage
- **Location:** `data/` folder in GitHub repository
- **Format:** JSON files with weekly snapshots
- **Files:**
  - `all_jobs.json` - Complete historical record of all unique jobs
  - `snapshot_YYYY-MM-DD.json` - Each week's scrape
  - `report_YYYY-MM-DD.md` - Human-readable weekly summary
  - `trends_dashboard.html` - Interactive analytics dashboard

### 3. GitHub Actions Workflow
- **File:** `.github/workflows/weekly-scrape.yml`
- **Schedule:** Cron job every Monday 9 AM UTC
- **Process:** Scrape → Deduplicate → Calculate trends → Generate dashboard → Commit to repo

---

## Data Collection Specifications

### Job Data Fields Collected

**Basic Information:**
- Institution name
- Job title
- Job ID and PhilJobs URL
- Posted date
- Application deadline

**Categorization:**
- **AOS (Area of Specialization)** - Raw text + normalized categories
- **AOC (Area of Competence)** - Raw text + normalized categories
- **Job Type:** Tenure-track, Postdoc, Adjunct/Visiting, Tenured, Other
- **Institution Type:** Research University, Teaching College, Other

**Location Data:**
- Full location string
- US State (if applicable)
- City (if applicable, especially West Coast cities)
- Country (including Latin American countries)

**Other:**
- Workload (full-time/part-time)
- Number of vacancies
- Start date
- Full job description text
- Application details (type, URL, contact)

### Deduplication Strategy

Jobs are deduplicated using MD5 hash of: `institution_title_jobID`

This ensures:
- Same job posting counted only once across weeks
- Expired and re-posted jobs counted as new if substantively different
- Accurate "new jobs per week" metrics

---

## Specialization Categorization System

### Category Hierarchy

Jobs are organized into **8 major categories** with **subcategories**:

#### 1. Ethics
- ethics (general)
- applied ethics
- bioethics
- environmental ethics
- ai ethics

#### 2. Social & Political
- social and political philosophy
- philosophy of race
- philosophy of gender
- philosophy of law

#### 3. History of Philosophy
- ancient philosophy
- medieval philosophy
- early modern philosophy
- continental philosophy
- american philosophy
- history of philosophy (general)

#### 4. Non-Western Philosophy
- asian philosophy
- african/africana philosophy
- latin american philosophy
- islamic philosophy
- indigenous philosophy

#### 5. Metaphysics & Epistemology
- metaphysics
- epistemology
- philosophy of mind
- philosophy of language
- philosophy of action
- philosophy of religion

#### 6. Science & Logic
- philosophy of science
- philosophy of physics
- logic
- philosophy of mathematics
- philosophy of technology
- philosophy of artificial intelligence

#### 7. Value Theory/Aesthetics
- aesthetics
- value theory

#### 8. Other
- PPE (Politics, Philosophy, Economics)
- public philosophy
- critical thinking

### Normalization Rules

Raw AOS/AOC text is parsed and normalized:
- Split on: commas, semicolons, slashes, "and", "or"
- Filter out: noise words ("broadly construed", "open", "and", "or", etc.)
- Map to canonical forms (e.g., "AI Ethics" = "ethics of AI" = "ai ethics")
- Long sentences (>15 chars) are discarded as noise

---

## Dashboard Requirements

### Core Functionality

**✅ IMPLEMENTED:**
1. **Overview Chart** - Line graph showing new jobs per week for all major categories
2. **Seasonal Markers** - Visual indicators for hiring season (Sept-Jan)
3. **Category Cards** - Clickable cards for each major category showing current week stats
4. **Drill-Down Modals** - Click category → see detailed view with:
   - Subcategory breakdown
   - Trend chart (parent + all subcategories)
   - Week-over-week change indicators
   - Job type pie chart (Tenure-track vs Postdoc vs Adjunct, etc.)
   - Institution type pie chart (Research vs Teaching)
   - Key insights (auto-generated)

**❌ NOT IMPLEMENTED (NEEDS WORK):**
5. **Interactive Maps** - Currently shows placeholder lists, needs:
   - US State-level SVG map with color intensity by job count
   - West Coast detail view (CA, OR, WA) with city-level markers
   - Latin America country-level SVG map
   - Maps should update when category is selected (integrated filtering)

### Geographic Features (HIGH PRIORITY)

**West Coast Focus:**
User specifically wants West Coast positions (San Francisco Bay Area, Pacific Northwest)

**City-level tracking for:**
- **Bay Area:** Berkeley, Stanford, San Francisco, Oakland, San Jose, Santa Cruz, Davis
- **SoCal:** Los Angeles, San Diego, Irvine, Claremont, Riverside
- **Pacific Northwest:** Seattle, Portland, Eugene, Tacoma, Olympia

**Map Behavior:**
- Main US map: state-level choropleth (darker = more jobs)
- Hover CA/OR/WA: Highlight as special region
- Click CA/OR/WA: Show zoomed detail with city markers
- All maps filter by selected category (e.g., click "Ethics" → maps show only Ethics jobs)

**Latin America:**
- Separate country-level map
- Track: Mexico, Brazil, Argentina, Chile, Colombia, Peru, Venezuela, Ecuador, Guatemala, Cuba, Bolivia, Haiti, Dominican Republic, Honduras, Paraguay, El Salvador, Nicaragua, Costa Rica, Panama, Puerto Rico, Uruguay

### Visual Design

- **Framework:** Tailwind CSS
- **Charts:** Chart.js
- **Color Scheme:**
  - Ethics: `#ef4444` (red)
  - Social & Political: `#3b82f6` (blue)
  - History of Philosophy: `#8b5cf6` (purple)
  - Non-Western: `#ec4899` (pink)
  - M&E: `#10b981` (green)
  - Science & Logic: `#f59e0b` (amber)
  - Value Theory/Aesthetics: `#06b6d4` (cyan)
  - Other: `#6b7280` (gray)

- **Typography:** Inter font family
- **Cards:** Hover effects, smooth transitions
- **Gradient header:** Indigo to purple
- **Modern, clean aesthetic** suitable for sharing with advisors/colleagues

---

## Current Implementation Status

### ✅ Working Features

1. **Automated weekly scraping** - Runs every Monday via GitHub Actions
2. **Full job detail extraction** - All fields captured from PhilJobs
3. **Smart categorization** - Job types and institution types auto-detected
4. **Location parsing** - US states, West Coast cities, Latin American countries
5. **Deduplication** - Only new unique jobs counted each week
6. **Trend tracking** - New jobs per week by category
7. **Dashboard generation** - HTML file with interactive charts
8. **Category drill-down** - Modal popups with detailed breakdowns
9. **Job type charts** - Pie charts showing TT vs Postdoc distribution
10. **Institution type charts** - Research vs Teaching breakdown
11. **Seasonal indicators** - Hiring season markers on charts
12. **Subcategory trends** - Individual trend lines for AI Ethics, Bioethics, etc.

### ❌ Missing/Broken Features

1. **Interactive SVG maps** - Currently shows text lists instead of visual maps
   - Need: US state choropleth map
   - Need: West Coast zoom with city markers
   - Need: Latin America country map
   - Need: Maps integrated with category filtering

2. **Potential improvements for future:**
   - Export to CSV functionality
   - Multi-year comparison view
   - Search/filter jobs by keyword
   - Email notifications for specific specializations
   - Salary data extraction (if available in descriptions)

---

## Technical Details

### Dependencies

**Python packages:**
- `requests` - HTTP requests to PhilJobs
- `beautifulsoup4` - HTML parsing
- `json` - Data serialization
- `datetime` - Date handling
- `hashlib` - Deduplication hashing
- `re` - Text parsing

**JavaScript libraries (CDN):**
- Tailwind CSS - UI framework
- Chart.js - Interactive charts
- (Need to add: D3.js or similar for SVG maps)

### Key Functions

**`scrape_jobs()`** - Main scraping loop  
**`scrape_job_details(job_id)`** - Extract full details from individual job page  
**`normalize_specialization(raw_area)`** - Clean and categorize AOS/AOC text  
**`categorize_job_type()`** - Detect TT vs Postdoc vs Adjunct  
**`extract_location_data()`** - Parse location into state/country/city  
**`calculate_weekly_trends(new_jobs, timestamp)`** - Aggregate new jobs by category  
**`generate_trend_dashboard()`** - Create HTML dashboard with all visualizations  

### Data Flow

```
PhilJobs.org 
  → scraper.py scrapes all listings
  → Extract full details for each job
  → Normalize categories
  → Compare with historical data (all_jobs.json)
  → Identify new unique jobs
  → Calculate weekly trends
  → Generate dashboard HTML
  → Commit to GitHub
```

---

## Usage Instructions

### First-Time Setup

1. Repository created: `Claude-Phil-Jobs-Tracker`
2. Files added:
   - `scraper.py` - Main scraper script
   - `.github/workflows/weekly-scrape.yml` - Automation
   - `data/.gitkeep` - Placeholder for data folder
3. GitHub Actions permissions set to "Read and write"

### Weekly Workflow (Automated)

Every Monday at 9 AM UTC:
1. GitHub Actions triggers workflow
2. Scraper runs, collects new jobs
3. Data files updated in `data/` folder
4. Changes automatically committed to repo

### Manual Run

Can be triggered anytime via GitHub Actions UI:
1. Go to repository → Actions tab
2. Click "Weekly PhilJobs Scraper"
3. Click "Run workflow"

### Viewing Results

1. Navigate to `data/` folder
2. Download `trends_dashboard.html`
3. Open in web browser (Chrome, Safari, Firefox)
4. Click category cards to drill down
5. View reports in `.md` files for text summary

---

## Future Enhancements (After Maps Are Fixed)

1. **Export functionality** - Download data as CSV/Excel
2. **Filters** - Filter by job type, location, institution type
3. **Search** - Search job descriptions by keyword
4. **Alerts** - Email/notification when West Coast + specific specialization appears
5. **Comparative analytics** - Compare this year vs last year trends
6. **Salary tracking** - Extract salary info from job descriptions
7. **Application tracking** - Track which jobs you've applied to

---

## Critical Notes for Future Development

### Map Implementation Requirements

When implementing the SVG maps, ensure:

1. **Integration with category filtering**
   - When user clicks "Ethics" category card → modal opens
   - Maps in modal show ONLY Ethics jobs
   - Click "AI Ethics" subcategory → maps update to show only AI Ethics
   - This is critical - maps must stay in sync with selected category

2. **West Coast priority**
   - CA, OR, WA states should be visually distinct (different border, highlight)
   - Clicking these states reveals city-level detail
   - City markers sized by number of jobs

3. **Data structure**
   - Map data already collected in `state_counts`, `west_coast_city_counts`, `country_counts`
   - Available in JavaScript as `data.stateData`, `data.westCoastData`, `data.latinData`
   - Each is a dictionary: `{location: [count_week1, count_week2, ...]}`

4. **Visual requirements**
   - Use color intensity (choropleth) for state/country maps
   - Tooltip on hover showing exact count
   - Clickable for detail view
   - Responsive design (works on mobile)

### West Coast Cities Coordinates

Already defined in Python (`WEST_COAST_CITIES` dict) with lat/lon for accurate mapping:
- Berkeley, Stanford, SF, Oakland, San Jose, Santa Cruz, Davis
- LA, San Diego, Irvine, Claremont, Riverside
- Seattle, Portland, Eugene, Tacoma, Olympia

### Seasonal Logic

Hiring season = September through January (months 9, 10, 11, 12, 1)
Should be visually indicated on trend charts with background shading or markers

---

## Key User Requirements Summary

**User Profile:**
- PhD student, Philosophy (Sartre/Existentialism)
- Marquette University
- 3 years until job market
- Target: West Coast (SF Bay Area or Pacific Northwest)

**Primary Questions to Answer:**
1. Which specializations consistently have the most jobs?
2. Which are growing vs declining?
3. Are there West Coast opportunities in my areas of interest?
4. What's the TT vs Postdoc ratio in different fields?
5. Should I pivot my research focus based on market demand?

**Data Needs:**
- Weekly new job counts (not total active)
- 3-year longitudinal trends
- Geographic distribution (especially West Coast)
- Job type breakdown (TT critical)
- Subcategory granularity (e.g., AI Ethics within Ethics)

**Sharing:**
Dashboard should look professional enough to share with:
- Dissertation advisor
- Department colleagues
- Other grad students
- Potential employers (showing market analysis skills)

---

## Contact & Maintenance

**Repository:** https://github.com/[username]/Claude-Phil-Jobs-Tracker  
**Primary maintainer:** User (PhD student)  
**Created:** January 2026  
**Last updated:** [Current date]

For questions or issues, refer to this specification document.

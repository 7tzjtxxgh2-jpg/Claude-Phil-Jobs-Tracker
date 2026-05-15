# Keyword Explorer — Methodology

**Last updated:** 2026-05-15
**Corpus size at this writing:** 192 jobs
**Vocabulary size eligible for synonym lookup:** 2132 terms
**Synonym groups in current map:** 0

---

## What This Tool Measures

The Keyword Explorer searches the **full text of job descriptions**
posted on PhilJobs.org. It does NOT search:

- AOS (Area of Specialization) labels
- AOC (Area of Competence) labels
- Job titles
- Institution names

This choice is deliberate. Labels reflect institutional and political
choices about how to frame a position; descriptions reflect the actual
work the position is asking for. The two can diverge — for example,
a department may hire someone whose research is on philosophy of race
but avoid labeling the AOS that way for political reasons. By
searching description text only, this tool measures content rather
than framing.

---

## Pipeline Overview

1. **Scrape** PhilJobs.org weekly. Job description text is stored
   per-job in `data/all_jobs.json` under the `description` field.
2. **Strip EEO boilerplate** from descriptions before tokenizing.
3. **Tokenize** descriptions into lowercase word lists.
4. **Filter stopwords** — both generic English stopwords and academic
   job-board boilerplate ("application", "candidates", "faculty",
   etc.).
5. **Identify corpus-frequent terms** (in >80% of descriptions) for
   the bubble-display stopword list. These remain searchable but are
   filtered from the bubble chart to avoid noise.
6. **Generate synonym map** via Claude Haiku (see Synonym Expansion).
7. **Embed** the per-job term index, synonym map, and stopword list
   into the dashboard HTML.
8. **Search runs client-side** in the browser: stems the query,
   expands via the synonym map, matches against per-job stem sets.

---

## Key Methodological Choices

### 1. EEO / Equal-Opportunity-Employer Statement Stripping

Almost every academic job description ends with an EEO statement like:

> "The University is an equal opportunity employer and considers
> applicants without regard to race, color, religion, national origin,
> age, sex, gender identity, sexual orientation, veteran status, or
> disability."

Without filtering, these sentences flood the keyword search. Searching
`race` for example would surface 40+ jobs whose only mention of "race"
is in the EEO statement — not actual philosophy-of-race openings.

**Algorithm:** Each sentence is checked against a list of EEO trigger
words: `equal`, `opportunity`, `affirmative`, `regardless`, `protected`,
`veterans`, `disabilities`, `ancestry`, `ethnicity`, `origin`,
`orientation`, `nondiscrimination`, `discrimination`, `harassment`,
`pregnancy`, `citizenship`, `genetic`, `creed`, `nationality`. Any
sentence containing **2 or more** trigger words is stripped before
tokenization.

**Verified impact:** During development, searching `race` dropped from
42 noisy matches (mostly EEO statements) to 9 substantive philosophy-
of-race jobs.

**Known trade-off:** Some legitimate content can be lost. A sentence
like "We welcome applications from diverse candidates including those
from historically excluded groups" might be stripped if it contains
2+ triggers. The trade-off was deemed acceptable because clean signal
on philosophical content matters more than capturing every diversity
statement.

### 2. Stopword Filtering

Three layers of filtering are applied:

1. **Generic English stopwords**: the, and, our, etc.
2. **Academic job-board boilerplate**: application, candidates,
   faculty, university, department, professor, qualification,
   experience, etc. The full list lives in `KEYWORD_STOPWORDS` near
   the top of `scraper.py`.
3. **Corpus-frequency bubble stopwords**: terms appearing in >80% of
   job descriptions get filtered from the bubble chart display (but
   remain searchable). In the current corpus: `philosophy`, `research`.

### 3. Stemming (Recursive)

A rule-based stemmer applies suffix rules repeatedly until the word
stops changing. This lets "feminists" → "feminist" → "femin" all
collapse to a single stem, which keeps morphological variants from
fragmenting bubble groups.

| Suffix | Replacement | Example |
|--------|-------------|---------|
| -ies   | -y          | studies → study |
| -ism   | (drop)      | feminism → femin |
| -ist   | (drop)      | feminist → femin |
| -ing   | (drop)      | teaching → teach |
| -ed    | (drop)      | tested → test |
| -es    | (drop)      | classes → class |
| -s     | (drop)      | ethics → ethic |

Words 3 characters or shorter are not stemmed. The same stemmer runs
in Python (at scrape time, for vocab building) and in JavaScript (at
search time, for query expansion). The Python implementation lives in
`_keyword_stem`; the JS implementation in `kwStem` — they are kept
in lockstep.

### 4. Synonym Expansion (Claude Haiku)

Each Monday, the top 150 most frequent corpus terms are sent to Claude
Haiku (`claude-haiku-4-5-20251001`, temperature=0) in batches of 25.
The prompt explicitly asks for FIELD-DEFINING terms only — alternative
names the academic discipline uses for the same subfield — and not
broadly related or co-occurring concepts:

> For each keyword below, list 4-10 FIELD-DEFINING synonyms —
> alternative names the academic discipline uses for the same
> subfield, research area, or concept.
>
> INCLUDE: morphological variants (feminism / feminist); alternative
> names for the same subfield (gay / queer / LGBTQ; AI / artificial
> intelligence / machine learning); standard academic terminology
> that NAMES this area.
>
> EXCLUDE: broadly related concepts that aren't field names (e.g.
> 'patriarchy' or 'intersectional' for feminism — these are concepts
> WITHIN feminism, not names FOR it); co-occurring topics (e.g.
> 'ethics' for race — they appear in the same postings but aren't
> synonyms); generic adjectives or institutional jargon.

This selective framing matters because the synonym map is the *only*
source for the bubble chart (see Section 5). Loosely-related terms
would produce noisy bubbles.

The response is parsed, validated (must be valid JSON; non-list values
are dropped), and cached to `data/synonym_map.json` and re-embedded
in the dashboard. If the API call fails or the API key is missing,
the dashboard still works — search falls back to stemming only.

The current synonym map is documented in human-readable form at
[SYNONYMS.md](SYNONYMS.md).

### 5. Bubble Chart Construction

When a user searches for a term, the bubble chart displays **the
field-defining synonyms from the map (Section 4)**, each sized by how
many jobs in the corpus contain that specific term. The bubble chart
is NOT a co-occurrence visualization.

1. Look up the search term in the synonym map to get its field-defining
   alternatives.
2. For each candidate (the query plus each synonym), stem it and count
   jobs in the corpus whose stem set contains that stem.
3. Display each as a bubble: the search term at the center, synonyms
   around it. Bubble size is proportional to per-term job count.
4. Render as a D3 force-directed simulation. Each bubble is clickable
   to re-search with that term.

**Why synonyms, not co-occurrence?** The purpose of the chart is to
help users discover the field's vocabulary — "what other words does
the discipline use for this concept?" — not to surface every word that
happens to appear in the same job descriptions. A prior co-occurrence
design produced noisy bubbles ("three" from "three letters of
reference"; "online" from teaching modality; "ethics" merely because
philosophy of race jobs often mention ethics). Sourcing strictly from
the synonym map gives a clean signal about field-defining alternatives.

**Bubble sizes are per-synonym corpus counts**, not match-set
co-occurrence counts. This answers the question "how many jobs in
the corpus list this specific word?" which is what the user typically
wants when assessing a field's market presence.

### 6. Trend Chart Construction

Raw count of matching jobs per week. Not normalized to total job
volume — the absolute count reflects market activity in that area.
Shaded background indicates the September-through-January hiring
season.

---

## Known Limitations

- **Static synonyms**: refreshed weekly, not real-time. A search for
  a brand-new term will fall back to stemming only until the next
  scrape.
- **Small corpus in early years**: with N≈200 jobs total, individual
  bubble suggestions can be statistical noise. Signal-to-noise should
  improve as the dataset grows over 3 years.
- **EEO false positives**: occasional substantive sentences may get
  stripped if they happen to contain 2+ EEO trigger words.
- **Description quality varies**: some PhilJobs postings have minimal
  description text. Those jobs simply contribute fewer terms.
- **Stemming is rule-based, not lexical**: words like "race" and
  "racial" do NOT stem to the same form. The synonym map is intended
  to bridge these gaps for important terms.
- **Bubble suggestions are co-occurrence, not lift**: a term appearing
  with high frequency in matching jobs may be common in *all* jobs
  rather than specifically associated with the search term. A future
  improvement is lift-based scoring (term overrepresentation relative
  to corpus baseline).

---

## How to Audit a Specific Result

1. **Inspect a specific job description**: open `data/all_jobs.json`,
   find the job by ID, read the `description` field. This is the raw
   text the keyword pipeline operates on.
2. **Inspect the synonym map**: open `data/synonym_map.json` for raw
   JSON, or [SYNONYMS.md](SYNONYMS.md) for a human-readable version.
3. **Verify a search result**: search for any term in the live
   dashboard, then check whether the listed match-count is plausible
   given the corpus size and the topic.
4. **Re-run locally**: clone the repo, set `ANTHROPIC_API_KEY`, run
   `python scraper.py`. Everything is reproducible.
5. **Inspect the code**: relevant methods in `scraper.py` are
   `_strip_eeo_boilerplate`, `_extract_description_terms`,
   `build_keyword_index`, `generate_synonym_map`, `_keyword_stem`.

---

## Change Log

- **2026-05-15**: Bubble chart rewritten to source from the Claude-
  generated synonym map (field-defining alternatives) rather than from
  corpus co-occurrence. Each bubble is now sized by per-term corpus
  count. The Claude synonym prompt was tightened to ask only for
  field-defining names (gay/queer/LGBTQ) and exclude broadly related
  concepts (patriarchy/intersectional for feminism). Stemmer changed
  from single-pass to recursive so morphological variants collapse
  to a single stem ("feminists" → "feminist" → "femin"). Rationale:
  the prior co-occurrence approach surfaced noise like "three" (from
  "three letters of reference") and "ethics" merely because race-
  related jobs often also discuss ethics. The new approach answers a
  more focused question — "what are the field's alternative names
  for this concept, and how many jobs use each?"
- **2026-05-15**: Initial documented version of the methodology.

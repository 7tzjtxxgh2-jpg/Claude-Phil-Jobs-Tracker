# Keyword Explorer — Synonym Map

**Last updated:** 2026-07-20
**Source data:** [`data/synonym_map.json`](../data/synonym_map.json)
**Terms in map:** 150

---

## About This List

When you type a search term into the Keyword Explorer on the dashboard,
your query is expanded to include the synonyms listed below before
matching against job description text. Example: searching `feminism`
will also find jobs mentioning `feminist`, `patriarchy`, `gender`, etc.

This map is regenerated automatically every Monday by claude-sonnet-4-5
based on the most frequent terms in the corpus of philosophy job
descriptions collected so far. As the corpus grows over time, more
terms will appear here and existing groups may shift.

For the full methodology behind how these synonyms are generated and
used, see [KEYWORD_EXPLORER_METHODOLOGY.md](KEYWORD_EXPLORER_METHODOLOGY.md).

---

## Synonym Groups (Alphabetical)

- **american** → americanist, americanism, american philosophy
- **applied** → applied philosophy, applied ethics, practical philosophy
- **critical** → critical theory, critical thinking, critique
- **discipline** → disciplinary, interdisciplinary, multidisciplinary, cross-disciplinary
- **education** → educational, pedagogy, pedagogical, philosophy of education
- **educational** → education, pedagogy, pedagogical, philosophy of education
- **eligible** → eligibility
- **environment** → environmental, ecology, ecological, environmental philosophy, environmental ethics
- **ethical** → ethics, metaethics, meta-ethics, normative ethics, applied ethics, moral philosophy, moral theory
- **ethics** → ethical, metaethics, meta-ethics, normative ethics, applied ethics, moral philosophy, moral theory
- **health** → medical, medicine, biomedical, healthcare, public health, health care
- **history** → historical, historiography, history of philosophy
- **humanities** → humanistic, liberal arts
- **interdisciplinary** → multidisciplinary, cross-disciplinary, transdisciplinary
- **introductory** → introduction, intro, foundational, elementary
- **knowledge** → epistemology, epistemological, epistemic
- **liberal** → liberal arts
- **logic** → logical, logics, formal logic, symbolic logic, mathematical logic
- **philosophical** → philosophy, philosophic
- **political** → politics, political philosophy, political theory
- **postdoctoral** → postdoc, post-doctoral, post-doc
- **scholars** → scholarship, scholarly
- **science** → philosophy of science, scientific
- **sciences** → philosophy of science, scientific
- **specialization** → specialty, specializations, area of specialization
- **syllabi** → syllabus, curriculum, curricula
- **system** → systems, systematic, systems theory
- **technology** → technological, technologies, technoscience, digital technology, information technology
- **visit** → visiting
- **visiting** → visit, visitor

---

## How to Inspect Raw Data

- **Machine-readable JSON:** [`data/synonym_map.json`](../data/synonym_map.json)
- **Raw job description text:** [`data/all_jobs.json`](../data/all_jobs.json) — each job has a `description` field with the full posting text.
- **Source code:** the synonym generation lives in `scraper.py` under the `generate_synonym_map` method.

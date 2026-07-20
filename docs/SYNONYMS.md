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

- **access** → accessibility
- **american** → american philosophy, americanist, pragmatism
- **applied** → applied ethics, applied philosophy, practical ethics
- **arts** → liberal arts, humanities
- **assistant** → assistant professor
- **critical** → critical theory, critical philosophy, frankfurt school
- **curriculum** → curricular, syllabus, course design
- **education** → educational, pedagogy, pedagogical, teaching
- **educational** → philosophy of education, educational philosophy
- **environment** → environmental, ecology, ecological
- **ethical** → ethics, moral philosophy, metaethics, normative ethics
- **ethics** → ethical, metaethics, meta-ethics, normative ethics, moral philosophy, moral theory
- **health** → medical, biomedical, healthcare, medicine
- **history** → historical, historiography
- **humanities** → humanistic
- **interdisciplinary** → multidisciplinary, cross-disciplinary, transdisciplinary
- **knowledge** → epistemology, theory of knowledge, epistemic
- **letters** → letter, humanities
- **liberal** → liberal arts
- **life** → philosophy of life, bioethics
- **logic** → logical, logics, formal logic, philosophical logic, mathematical logic, modal logic
- **open** → open rank
- **person** → personal identity, personhood, philosophy of persons
- **philosophical** → philosophy, philosophic
- **political** → political philosophy, political theory
- **postdoctoral** → postdoc, post-doctoral
- **public** → public philosophy
- **research** → scholarship, scholarly, investigation
- **science** → scientific, philosophy of science
- **sciences** → philosophy of science, scientific
- **social** → social philosophy, social theory
- **specialization** → specializations, specialism, area of specialization, aos
- **system** → systems theory, systematic philosophy
- **technology** → philosophy of technology, technoscience, digital philosophy, philosophy of computing
- **vision** → philosophy of perception, visual perception
- **visiting** → visitor, visiting scholar, visiting professor, visiting faculty
- **vitae** → cv, curriculum vitae

---

## How to Inspect Raw Data

- **Machine-readable JSON:** [`data/synonym_map.json`](../data/synonym_map.json)
- **Raw job description text:** [`data/all_jobs.json`](../data/all_jobs.json) — each job has a `description` field with the full posting text.
- **Source code:** the synonym generation lives in `scraper.py` under the `generate_synonym_map` method.

# Keyword Explorer — Synonym Map

**Last updated:** 2026-08-10
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

- **american** → americanist, americanism
- **arts** → humanities, liberal arts
- **center** → centre
- **city** → urban
- **critical** → critical theory, critical philosophy
- **curriculum** → curricular, syllabus
- **discipline** → disciplinary, interdisciplinary, multidisciplinary, cross-disciplinary
- **diverse** → diversity
- **education** → educational, pedagogy, pedagogical, teaching
- **eligible** → eligibility
- **environment** → environmental, ecology, ecological
- **ethical** → ethics, metaethics, meta-ethics, normative ethics, moral philosophy, moral theory
- **ethics** → ethical, metaethics, normative ethics, moral philosophy, applied ethics
- **health** → healthcare, medical, medicine, bioethics
- **history** → historical, history of philosophy
- **humanities** → humanistic
- **interdisciplinary** → multidisciplinary, cross-disciplinary, transdisciplinary
- **knowledge** → epistemology, epistemological, epistemic
- **liberal** → liberal arts
- **logic** → logical, formal logic, philosophical logic, symbolic logic, mathematical logic
- **online** → digital, distance
- **person** → personal, personhood, persons
- **philosophical** → philosophy, philosophic
- **political** → politics, political philosophy, political theory
- **postdoctoral** → postdoc, post-doctoral
- **research** → scholarship, scholarly, investigation
- **scholars** → scholar, scholarship, scholarly
- **science** → scientific, sciences, philosophy of science
- **sciences** → science, scientific
- **specialization** → specialize, specialized, specializations, specialty, specialties, area of specialization, aos
- **system** → systems, systematic
- **technology** → technological, technologies, philosophy of technology
- **visit** → visiting
- **vitae** → cv, curriculum vitae

---

## How to Inspect Raw Data

- **Machine-readable JSON:** [`data/synonym_map.json`](../data/synonym_map.json)
- **Raw job description text:** [`data/all_jobs.json`](../data/all_jobs.json) — each job has a `description` field with the full posting text.
- **Source code:** the synonym generation lives in `scraper.py` under the `generate_synonym_map` method.

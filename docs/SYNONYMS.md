# Keyword Explorer — Synonym Map

**Last updated:** 2026-06-29
**Source data:** [`data/synonym_map.json`](../data/synonym_map.json)
**Terms in map:** 125

---

## About This List

When you type a search term into the Keyword Explorer on the dashboard,
your query is expanded to include the synonyms listed below before
matching against job description text. Example: searching `feminism`
will also find jobs mentioning `feminist`, `patriarchy`, `gender`, etc.

This map is regenerated automatically every Monday by Claude Haiku
based on the most frequent terms in the corpus of philosophy job
descriptions collected so far. As the corpus grows over time, more
terms will appear here and existing groups may shift.

For the full methodology behind how these synonyms are generated and
used, see [KEYWORD_EXPLORER_METHODOLOGY.md](KEYWORD_EXPLORER_METHODOLOGY.md).

---

## Synonym Groups (Alphabetical)

- **access** → accessibility
- **american** → americanist, american philosophy
- **applied** → applied philosophy, applied ethics, practical philosophy
- **arts** → humanities, liberal arts
- **center** → centre
- **collaboration** → collaborative
- **continue** → continuing
- **critical** → critical theory, critical thinking, critique
- **curriculum** → curricular, syllabus, course design
- **discipline** → disciplinary, interdisciplinary, multidisciplinary, cross-disciplinary
- **education** → educational, pedagogy, pedagogical, teaching
- **eligible** → eligibility
- **environment** → environmental, ecology, ecological
- **ethics** → ethical, metaethics, normative ethics, moral philosophy, applied ethics
- **health** → healthcare, medicine, medical, bioethics, biomedical ethics
- **history** → historical, historian, historians
- **humanities** → humanistic
- **interdisciplinary** → multidisciplinary, cross-disciplinary, transdisciplinary
- **knowledge** → epistemology, epistemological, epistemic
- **liberal** → liberal arts
- **life** → philosophy of life
- **logic** → logical, logics, formal logic, mathematical logic, philosophical logic
- **names** → naming, reference, proper names
- **participate** → participation
- **person** → personal identity, personhood, persons, philosophy of person
- **philosophical** → philosophy, philosophic
- **policy** → public policy
- **political** → political philosophy, political theory
- **postdoctoral** → postdoc, post-doctoral, post-doc
- **public** → public philosophy
- **recommendation** → recommendations, reference, references, letter of recommendation, letters of recommendation
- **research** → scholarship, scholarly, investigation
- **scholars** → scholarship, scholarly
- **science** → scientific, sciences, philosophy of science
- **social** → social philosophy, social theory
- **specialization** → specializations, specialism, specialisms, area of specialization, areas of specialization
- **syllabi** → syllabus
- **system** → systems, systematic
- **technology** → technological, technologies, technoscience, philosophy of technology
- **vision** → philosophy of vision, visual perception
- **visit** → visiting
- **vitae** → cv, curriculum vitae

---

## How to Inspect Raw Data

- **Machine-readable JSON:** [`data/synonym_map.json`](../data/synonym_map.json)
- **Raw job description text:** [`data/all_jobs.json`](../data/all_jobs.json) — each job has a `description` field with the full posting text.
- **Source code:** the synonym generation lives in `scraper.py` under the `generate_synonym_map` method.

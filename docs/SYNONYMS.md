# Keyword Explorer — Synonym Map

**Last updated:** 2026-07-06
**Source data:** [`data/synonym_map.json`](../data/synonym_map.json)
**Terms in map:** 150

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

- **american** → americanist, american philosophy
- **applied** → applied ethics, practical ethics, applied philosophy
- **associate** → assistant, adjunct, lecturer
- **critical** → critical theory, critical thinking
- **curriculum** → curricular, syllabus, course design
- **discipline** → disciplinary, disciplines
- **education** → educational, pedagogy, pedagogical, teaching
- **environment** → environmental, environmental philosophy, environmental ethics, ecology
- **ethical** → ethics, metaethics, meta-ethics, normative ethics, moral philosophy
- **ethics** → ethical, metaethics, normative ethics, moral philosophy, applied ethics
- **health** → healthcare, medical, biomedical, medicine, health ethics, bioethics
- **history** → historical, historian, historians, history of philosophy
- **humanities** → humanistic, liberal arts
- **interdisciplinary** → multidisciplinary, cross-disciplinary, transdisciplinary
- **knowledge** → epistemology, epistemological, theory of knowledge
- **liberal** → liberal arts
- **logic** → logical, formal logic, symbolic logic, philosophical logic, mathematical logic
- **person** → persons, personal identity, personhood
- **philosophical** → philosophy, philosophic
- **political** → politics, political philosophy, political theory
- **postdoctoral** → postdoc, post-doctoral, post-doc
- **recommendation** → recommendations, reference, references, letter of recommendation, letters of recommendation
- **research** → scholarship, scholarly, investigation
- **scholars** → scholarship, scholarly
- **science** → sciences, scientific
- **sciences** → science, scientific
- **specialization** → specialty, specializations, specialism, area of specialization, aos
- **syllabi** → syllabus, curriculum, curricula
- **technology** → technological, technologies, technoscience, philosophy of technology
- **visiting** → visitor, visit
- **vitae** → cv, curriculum vitae

---

## How to Inspect Raw Data

- **Machine-readable JSON:** [`data/synonym_map.json`](../data/synonym_map.json)
- **Raw job description text:** [`data/all_jobs.json`](../data/all_jobs.json) — each job has a `description` field with the full posting text.
- **Source code:** the synonym generation lives in `scraper.py` under the `generate_synonym_map` method.

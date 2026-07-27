# Keyword Explorer — Synonym Map

**Last updated:** 2026-07-27
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

- **american** → americanist
- **applied** → practical
- **center** → centre, institute, lab, laboratory
- **chair** → chairperson, chair position, department chair
- **city** → urban
- **critical** → critical theory
- **curriculum** → curricular, syllabus, course design
- **departmental** → department
- **diverse** → diversity
- **education** → educational, pedagogy, pedagogical, teaching
- **educational** → education, pedagogy, pedagogical
- **eligible** → eligibility
- **environment** → environmental, ecology, ecological
- **ethical** → ethics, metaethics, metaethical, normative ethics
- **ethics** → ethical, metaethics, normative ethics, moral philosophy, applied ethics
- **fellows** → fellowship, fellowships
- **health** → medical, medicine, biomedical, healthcare
- **history** → historical, historiography, historian
- **humanities** → humanistic
- **interdisciplinary** → multidisciplinary, cross-disciplinary, transdisciplinary
- **knowledge** → epistemology, epistemological, epistemic
- **letters** → humanities, liberal arts, belles-lettres
- **liberal** → liberal arts
- **logic** → logical, formal logic, philosophical logic, symbolic logic
- **online** → distance, remote, digital
- **person** → personal identity, personhood, philosophy of persons
- **philosophical** → philosophy, philosophic
- **policy** → public policy
- **political** → politics, political philosophy, political theory
- **postdoctoral** → postdoc, post-doctoral
- **research** → scholarship, scholarly, investigation
- **scholars** → scholarship, scholarly
- **science** → scientific, sciences
- **sciences** → science, scientific
- **specialization** → specialize, specializations, specialty, specialties, area of specialization, aos
- **study** → studies
- **syllabi** → syllabus, curriculum, curricula
- **system** → systems, systematic
- **technology** → philosophy of technology, technoscience, digital philosophy
- **visit** → visiting
- **vitae** → cv, curriculum vitae

---

## How to Inspect Raw Data

- **Machine-readable JSON:** [`data/synonym_map.json`](../data/synonym_map.json)
- **Raw job description text:** [`data/all_jobs.json`](../data/all_jobs.json) — each job has a `description` field with the full posting text.
- **Source code:** the synonym generation lives in `scraper.py` under the `generate_synonym_map` method.

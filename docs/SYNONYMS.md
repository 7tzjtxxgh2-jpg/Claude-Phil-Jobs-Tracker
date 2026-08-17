# Keyword Explorer — Synonym Map

**Last updated:** 2026-08-17
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

- **american** → americanist, americas
- **applied** → applied philosophy, applied ethics, practical philosophy, practical ethics
- **arts** → humanities, liberal arts
- **associate** → associate professor, associate rank
- **center** → centre
- **collaboration** → collaborative
- **competence** → area of competence, aoc, secondary area, secondary specialization
- **continue** → continuing
- **critical** → critical theory, critical philosophy, frankfurt school
- **curriculum** → curricular, syllabus
- **diverse** → diversity
- **education** → educational, pedagogy, pedagogical, teaching
- **eligible** → eligibility
- **environment** → environmental, ecology, ecological
- **ethical** → ethics, metaethics, meta-ethics, normative ethics, applied ethics, moral philosophy, moral theory
- **ethics** → ethical, metaethics, normative ethics, moral philosophy, applied ethics
- **expertise** → specialization, specializations, aos, area of specialization
- **health** → healthcare, medical, medicine, biomedical
- **history** → historical, history of philosophy
- **humanities** → humanistic
- **interdisciplinary** → interdisciplinarity, cross-disciplinary, multidisciplinary, transdisciplinary
- **introductory** → intro, lower division, undergraduate survey
- **knowledge** → epistemology, epistemological, epistemic
- **liberal** → liberal arts
- **logic** → logical, formal logic, philosophical logic, symbolic logic, mathematical logic, modal logic
- **online** → digital, distance
- **philosophical** → philosophy
- **policy** → public policy, policy studies, science policy, social policy
- **political** → politics, political philosophy, political theory
- **postdoctoral** → postdoc, post-doctoral, postdoctoral fellowship, postdoctoral researcher
- **process** → process philosophy, process metaphysics, process thought
- **research** → scholarship, scholarly, investigation
- **scholars** → scholarship, scholarly
- **science** → scientific, sciences, philosophy of science
- **sciences** → science, scientific
- **specialization** → specializations, aos, area of specialization, expertise
- **system** → systematic, systems
- **technology** → philosophy of technology, technoscience, digital humanities, computational
- **training** → pedagogy, pedagogical, teaching preparation, instructional development
- **visit** → visiting
- **visiting** → visiting scholar, visiting professor, visiting faculty, visiting appointment
- **vitae** → cv, curriculum vitae

---

## How to Inspect Raw Data

- **Machine-readable JSON:** [`data/synonym_map.json`](../data/synonym_map.json)
- **Raw job description text:** [`data/all_jobs.json`](../data/all_jobs.json) — each job has a `description` field with the full posting text.
- **Source code:** the synonym generation lives in `scraper.py` under the `generate_synonym_map` method.

# Keyword Explorer — Synonym Map

**Last updated:** 2026-08-03
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

- **additional** → addition, additionally
- **american** → americanist, american studies, americas
- **arts** → humanities, liberal arts
- **center** → centre, centers, centres
- **city** → urban, urbanism
- **collaboration** → collaborative
- **committed** → commitment, commit
- **contribute** → contribution, contributions, contributing, contributor
- **critical** → critical theory, critical philosophy
- **curriculum** → curricular, syllabus
- **demonstrated** → demonstrate, demonstrable, demonstration
- **develop** → development
- **discipline** → disciplinary, interdisciplinary, multidisciplinary, cross-disciplinary
- **diverse** → diversity, diversification
- **education** → educational, pedagogy, pedagogical, teaching
- **educational** → pedagogy, pedagogical, teaching, instruction, instructional
- **engagement** → engage, engaged, engaging, engages
- **environment** → environmental, environments
- **ethical** → ethics, metaethics, metaethical, normative ethics, moral philosophy, moral theory
- **ethics** → ethical, metaethics, normative ethics, moral philosophy, applied ethics
- **evidence** → evidenced, evidential
- **filled** → fill, filling
- **health** → healthcare, wellbeing, well-being, wellness
- **history** → history of philosophy, historical
- **humanities** → humanistic
- **includes** → include, included, including, inclusion, inclusive
- **interdisciplinary** → interdisciplinarity, multidisciplinary, multidisciplinarity, transdisciplinary, transdisciplinarity, cross-disciplinary
- **knowledge** → epistemology, epistemic, epistemological, theory of knowledge
- **learning** → learn, learned
- **letters** → letter
- **liberal** → liberal arts
- **life** → philosophy of life, bioethics, medical ethics
- **logic** → logical, formal logic, symbolic logic, mathematical logic, philosophical logic
- **member** → membership
- **mission** → missions
- **online** → digital, remote, distance
- **participate** → participation
- **person** → personal, persons, personhood
- **philosophical** → philosophy, philosophic
- **political** → political philosophy, political theory
- **postdoctoral** → postdoc, post-doctoral
- **public** → public philosophy
- **research** → scholarship, scholarly, investigation
- **scholars** → scholarship, scholarly
- **science** → scientific, sciences, philosophy of science
- **sciences** → science, scientific
- **seeks** → seek, seeking
- **semester** → semesterly, semesters
- **social** → social philosophy, social theory
- **specialization** → specializations, area of specialization, aos
- **staff** → staffing, staffed
- **strong** → strength, strongly
- **system** → systems, systematic
- **technology** → technologies, technological, philosophy of technology, technoscience
- **visit** → visiting
- **vitae** → cv, curriculum vitae
- **world** → worlds, worldly

---

## How to Inspect Raw Data

- **Machine-readable JSON:** [`data/synonym_map.json`](../data/synonym_map.json)
- **Raw job description text:** [`data/all_jobs.json`](../data/all_jobs.json) — each job has a `description` field with the full posting text.
- **Source code:** the synonym generation lives in `scraper.py` under the `generate_synonym_map` method.

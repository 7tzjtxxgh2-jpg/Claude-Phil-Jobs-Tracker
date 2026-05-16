# Keyword Explorer — Synonym Map

**Last updated:** 2026-05-16
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

- **active** → actively, activity
- **activities** → activity
- **addition** → additional
- **applied** → applied ethics, applied philosophy
- **associate** → assistant, adjunct, lecturer
- **background** → backgrounds
- **competence** → competency, competencies, competent
- **continue** → continuing
- **critical** → critical theory, critical thinking, critique
- **description** → describe, described, describing
- **discipline** → disciplinary, disciplines, field
- **educational** → education, philosophy of education
- **eligible** → eligibility, qualified, qualification
- **environment** → environmental, environmental philosophy, environmental ethics
- **ethical** → ethics, metaethics, meta-ethics, normative ethics, applied ethics, moral philosophy, moral theory
- **ethics** → ethical, metaethics, meta-ethics, normative ethics, moral philosophy, moral theory
- **health** → healthcare, medical, biomedical, medicine, public health, health ethics
- **highly** → high, strong, strongly, excellent
- **history** → historical, history of philosophy
- **includes** → include, including
- **intellectual** → scholarly, academic
- **interdisciplinary** → multidisciplinary, cross-disciplinary, transdisciplinary
- **knowledge** → knowledgeable
- **liberal** → liberal arts
- **located** → location, based
- **logic** → logical, formal logic, philosophical logic, symbolic logic, mathematical logic
- **medical** → medicine, biomedical, bioethics, medical ethics, clinical ethics, healthcare ethics
- **names** → named, naming
- **opportunities** → opportunity
- **person** → personal identity, personhood
- **philosophical** → philosophy, philosophic
- **policy** → policies
- **political** → politics, political philosophy, political theory
- **postdoctoral** → postdoc, post-doctoral, post-doc
- **prior** → previous, earlier, formerly
- **received** → receive, receiving, obtained
- **recommendation** → recommendations
- **relevant** → relevance
- **renewal** → renewable, reappointment
- **scholars** → scholar, scholarship, scholarly
- **science** → sciences, scientific, philosophy of science
- **sciences** → science, scientific, philosophy of science
- **serve** → service, serving
- **specialization** → specializations, specialize, specialty, specialties
- **studies** → study
- **submitted** → submit, submission, submitting
- **syllabi** → syllabus, syllabuses
- **system** → systems, systematic
- **technology** → technologies, technological, philosophy of technology
- **term** → terms, temporary, fixed-term
- **training** → trained, preparation, formation
- **visit** → visiting
- **visiting** → visitor, guest
- **vitae** → cv, curriculum vitae

---

## How to Inspect Raw Data

- **Machine-readable JSON:** [`data/synonym_map.json`](../data/synonym_map.json)
- **Raw job description text:** [`data/all_jobs.json`](../data/all_jobs.json) — each job has a `description` field with the full posting text.
- **Source code:** the synonym generation lives in `scraper.py` under the `generate_synonym_map` method.

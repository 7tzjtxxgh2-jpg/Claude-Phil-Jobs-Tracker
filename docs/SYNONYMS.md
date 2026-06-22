# Keyword Explorer — Synonym Map

**Last updated:** 2026-06-22
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

- **able** → ability
- **access** → accessible, accessibility
- **active** → actively, activism, activist
- **addition** → additional, plus, supplementary
- **american** → americanist, american philosophy, pragmatism, pragmatist
- **applied** → apply, applying, application
- **arts** → humanities, liberal arts
- **assistant** → assistant professor
- **associate** → assistant, adjunct, lecturer, instructor
- **collaboration** → collaborative, cooperate, cooperation, partnership
- **competence** → competency, competencies, competent
- **critical** → critical theory, critical thinking, critique
- **curriculum** → curricular, syllabus, course design
- **demonstrate** → demonstrated, demonstrates, demonstrating, show, evidence
- **description** → descriptive, descriptivist
- **discipline** → field, area, subject, disciplinary
- **diverse** → diversity
- **education** → educational, pedagogy, pedagogical, teaching
- **educational** → education, philosophy of education, pedagogy, pedagogical
- **employees** → employee, employment
- **engage** → engagement, engaging
- **environment** → environmental, ecology, ecological, environmental philosophy, environmental ethics
- **ethical** → ethics, moral, morality, normative ethics, metaethics
- **ethics** → ethical, metaethics, meta-ethics, normative ethics, moral philosophy, moral theory
- **health** → medical, medicine, bioethics, biomedical, healthcare
- **high** → strong, excellent, superior
- **history** → historical, historian, historians, history of philosophy
- **hours** → credit hours, contact hours, teaching hours
- **interdisciplinary** → multidisciplinary, cross-disciplinary, transdisciplinary
- **introduction** → introductory
- **introductory** → introduction
- **knowledge** → expertise, familiarity, competence, understanding
- **located** → based, situated, housed
- **logic** → logical, logics
- **member** → membership
- **mind** → philosophy of mind, mental, cognitive science, consciousness
- **online** → distance, remote, virtual, digital
- **participate** → participation, participatory
- **person** → individual, candidate, applicant
- **policy** → policies, governance, regulation, administration
- **political** → political philosophy, political theory
- **postdoctoral** → postdoc, post-doctoral, post-doc, postdoctorate
- **prior** → previous, earlier, preceding
- **process** → process philosophy, process metaphysics, process thought
- **projects** → project, initiatives, programs
- **public** → public philosophy
- **received** → obtained, earned, awarded, conferred
- **renewal** → reappointment, extension, continuation
- **research** → scholarship, scholarly, investigation
- **scholars** → scholar, researchers, academics, faculty
- **science** → scientific, philosophy of science
- **sciences** → scientific, philosophy of science
- **serve** → teach, instruct, contribute
- **skills** → competencies, abilities, expertise, proficiencies
- **social** → social philosophy, social theory
- **studies** → study, scholarship, inquiry, research
- **subject** → subjectivity
- **submitted** → submit, submitting, submission
- **syllabi** → syllabus, curriculum, curricula
- **system** → systems, systematic
- **technology** → digital, computational, informatics, technoscience
- **training** → preparation, education, formation, pedagogy
- **vision** → visual perception, perception, visual experience, visual cognition, philosophy of perception
- **visiting** → visitor, guest, adjunct visiting

---

## How to Inspect Raw Data

- **Machine-readable JSON:** [`data/synonym_map.json`](../data/synonym_map.json)
- **Raw job description text:** [`data/all_jobs.json`](../data/all_jobs.json) — each job has a `description` field with the full posting text.
- **Source code:** the synonym generation lives in `scraper.py` under the `generate_synonym_map` method.

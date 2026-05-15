# Keyword Explorer — Synonym Map

**Last updated:** 2026-05-15
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

- **access** → accessible, accessibility
- **active** → actively, activity
- **activities** → activity
- **addition** → additional
- **applied** → applied ethics, applied philosophy, practical ethics
- **associate** → associated, association
- **background** → backgrounds
- **competence** → competent, competency
- **continue** → continuing
- **critical** → critical theory, critical thinking, frankfurt school
- **discipline** → disciplinary, disciplines
- **eligible** → eligibility
- **environment** → environmental, ecology, ecological, environmental philosophy, environmental ethics
- **ethical** → ethics, metaethics, meta-ethics, normative ethics, applied ethics, moral philosophy, moral
- **ethics** → ethical, metaethics, meta-ethics, normative ethics, moral philosophy, moral theory
- **general** → generalist
- **health** → healthcare, medical, biomedical, medicine, public health, health care
- **higher** → higher education
- **history** → historical, history of philosophy
- **includes** → include, including
- **intellectual** → intellectuals
- **interdisciplinary** → multidisciplinary, cross-disciplinary, transdisciplinary
- **introductory** → introduction, intro, survey
- **knowledge** → knowledgeable
- **liberal** → liberal arts
- **located** → location, locate
- **logic** → logical, formal logic, symbolic logic, mathematical logic, philosophical logic
- **names** → name, named
- **opportunities** → opportunity
- **philosophical** → philosophy, philosophic
- **policy** → policies
- **political** → politics, political philosophy, political theory
- **postdoctoral** → postdoc, postdoctorate, post-doctoral, post-doc
- **potential** → potentiality, potency, dunamis
- **process** → process philosophy, processual, whitehead, whiteheadian
- **received** → receive, receiving
- **recommendation** → recommendations
- **relevant** → relevance
- **renewal** → renewable, renewed, renew
- **scholars** → scholar, scholarly, scholarship
- **science** → sciences, scientific, philosophy of science
- **sciences** → science, scientific, philosophy of science
- **serve** → service, serving
- **specialization** → specializations, specialize, specialty, specialties
- **studies** → study
- **submitted** → submit, submission, submitting
- **syllabi** → syllabus
- **system** → systems, systematic, systemic
- **technology** → technologies, technological, philosophy of technology
- **term** → terms
- **training** → trained
- **visit** → visiting
- **visiting** → visitor, visit
- **vitae** → cv, curriculum vitae

---

## How to Inspect Raw Data

- **Machine-readable JSON:** [`data/synonym_map.json`](../data/synonym_map.json)
- **Raw job description text:** [`data/all_jobs.json`](../data/all_jobs.json) — each job has a `description` field with the full posting text.
- **Source code:** the synonym generation lives in `scraper.py` under the `generate_synonym_map` method.

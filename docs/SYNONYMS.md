# Keyword Explorer — Synonym Map

**Last updated:** 2026-06-15
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

- **addition** → additional, additionally
- **american** → americanist, americas
- **arts** → humanities, liberal arts
- **associate** → associated, association
- **center** → centre
- **competence** → competent, competency, competencies
- **critical** → critique, criticism
- **curriculum** → curricular, syllabus, course design
- **demonstrate** → demonstrated, demonstrates, demonstrable
- **discipline** → disciplinary, disciplines
- **education** → educational, pedagogy, pedagogical, teaching
- **eligible** → eligibility
- **environment** → environmental, ecology, ecological, environmental philosophy, environmental ethics
- **ethical** → ethics, metaethics, normative ethics, applied ethics, moral philosophy, moral theory
- **ethics** → ethical, metaethics, meta-ethics, normative ethics, moral philosophy, applied ethics
- **general** → generalist, broadly
- **health** → healthcare, medical, medicine, biomedical, public health, health humanities
- **history** → historical, historian, historians, history of philosophy
- **hours** → hour, hourly
- **humanities** → humanistic, liberal arts, studia humanitatis
- **intellectual** → intellect, intellectuals
- **interdisciplinary** → multidisciplinary, cross-disciplinary, transdisciplinary
- **knowledge** → knowledgeable
- **liberal** → liberal arts
- **located** → location, locate
- **logic** → logical, logics, formal logic, philosophical logic, mathematical logic, modal logic, non-classical logic
- **medical** → medicine, biomedical, clinical
- **names** → name, named
- **online** → distance learning, remote, digital
- **person** → persons, personnel
- **philosophical** → philosophy, philosophic
- **policy** → policies
- **political** → politics, political philosophy, political theory
- **postdoctoral** → postdoc, post-doctoral, post-doc
- **prior** → previous, previously
- **received** → receive, receiving
- **recommendation** → recommendations
- **renewal** → renewable, reappointment, reappointed
- **research** → scholarship, scholarly, investigation
- **scholars** → scholar, scholarly, scholarship
- **science** → sciences, scientific, natural science, natural sciences
- **sciences** → science, scientific, natural science, natural sciences
- **serve** → serving, served, service
- **skills** → skill
- **specialization** → specializations, specialism, specialisms, area of specialization, aos
- **studies** → study
- **syllabi** → syllabus
- **technology** → technological, philosophy of technology, technoscience
- **term** → terms
- **vitae** → cv, curriculum vitae

---

## How to Inspect Raw Data

- **Machine-readable JSON:** [`data/synonym_map.json`](../data/synonym_map.json)
- **Raw job description text:** [`data/all_jobs.json`](../data/all_jobs.json) — each job has a `description` field with the full posting text.
- **Source code:** the synonym generation lives in `scraper.py` under the `generate_synonym_map` method.

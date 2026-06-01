# Keyword Explorer — Synonym Map

**Last updated:** 2026-06-01
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

- **access** → accessibility
- **across** → cross, inter, between
- **activities** → activity
- **additional** → supplementary, extra, further
- **american** → american philosophy, american pragmatism, pragmatism
- **applied** → practical, practice
- **arts** → humanities, liberal arts
- **assistant** → assistant professor
- **center** → centre, institute, center for, centre for
- **collaboration** → collaborative
- **committed** → commit, commits, commitment, commitments
- **consideration** → consider, considered, considers
- **considered** → consider, considers, consideration
- **continue** → continuing, continuation
- **contribute** → contributes, contributed, contribution, contributions
- **critical** → critical theory
- **curriculum** → curricular, syllabus
- **demonstrated** → demonstrate, demonstrates, demonstrable, demonstration
- **development** → developmental, develop, develops, developing
- **diverse** → diversity, diversities, diversification
- **education** → educational, pedagogy, pedagogical, teaching
- **eligible** → eligibility
- **engage** → engagement
- **engagement** → engage, engaged, engages, engaging
- **environment** → environmental, ecology, ecological
- **ethical** → ethics, metaethics, meta-ethics, normative ethics, moral philosophy, moral theory
- **ethics** → ethical, metaethics, meta-ethics, normative ethics, moral philosophy, moral theory
- **evidence** → evidential, evidentiary, evidenced
- **expertise** → expert, specialization, specialty
- **first** → primary, initial, premier
- **health** → healthcare, medical, medicine, clinical
- **history** → historical, historian, historians, historiography
- **humanities** → humanistic, liberal arts, studia humanitatis
- **interdisciplinary** → multidisciplinary, transdisciplinary, cross-disciplinary, pluridisciplinary
- **interested** → interest
- **introductory** → introduction
- **knowledge** → epistemology, epistemic, epistemological, theory of knowledge
- **learning** → learn, learns, learned, pedagogy, pedagogical
- **life** → living, vital, biological
- **logic** → logical, formal logic, symbolic logic, philosophical logic
- **medical** → bioethics, biomedical ethics, medical ethics, clinical ethics, healthcare ethics
- **members** → member, membership
- **online** → distance, remote, virtual, digital
- **opportunities** → opportunity
- **participate** → participation
- **philosophical** → philosophy, philosophic
- **political** → politics, political philosophy, political theory
- **postdoctoral** → postdoc, post-doctoral, post-doc
- **process** → process philosophy, process metaphysics, process thought
- **recommendation** → recommendations, reference, references
- **relevant** → relevance
- **renewal** → renewable, reappointment
- **research** → scholarship, scholarly, investigation
- **scholars** → scholar, scholarship
- **science** → scientific, philosophy of science
- **sciences** → science, scientific
- **seeks** → seek, seeking, sought
- **semester** → term, quarter, academic term
- **specialization** → specializations, specialty, specialties, area of specialization, aos
- **staff** → faculty, personnel
- **syllabi** → syllabus
- **system** → systems, systematic
- **technology** → technological, technologies, tech
- **thinking** → thought, reasoning, cognition, cognitive
- **vision** → visual, perception, philosophy of perception
- **visit** → visiting, visitor
- **vitae** → cv, curriculum vitae, resume

---

## How to Inspect Raw Data

- **Machine-readable JSON:** [`data/synonym_map.json`](../data/synonym_map.json)
- **Raw job description text:** [`data/all_jobs.json`](../data/all_jobs.json) — each job has a `description` field with the full posting text.
- **Source code:** the synonym generation lives in `scraper.py` under the `generate_synonym_map` method.

# Keyword Explorer — Synonym Map

**Last updated:** 2026-06-09
**Source data:** [`data/synonym_map.json`](../data/synonym_map.json)
**Terms in map:** 125

---

## About This List

When you type a search term into the Keyword Explorer on the dashboard,
your query is expanded to include the synonyms listed below before
matching against job description text. Example: searching `feminism`
will also find jobs mentioning `feminist`, `patriarchy`, `gender`, etc.

This map is regenerated automatically every Monday by `claude-sonnet-4-5`
based on the most frequent terms in the corpus of philosophy job
descriptions collected so far. As the corpus grows over time, more
terms will appear here and existing groups may shift.

For the full methodology behind how these synonyms are generated and
used, see [KEYWORD_EXPLORER_METHODOLOGY.md](KEYWORD_EXPLORER_METHODOLOGY.md).

---

## Synonym Groups (Alphabetical)

- **able** → ability, enable
- **access** → accessible, accessibility, accessing
- **active** → actively, activate, activity
- **activities** → activity
- **american** → american philosophy, american pragmatism, pragmatism
- **applied** → apply, application, applications
- **arts** → humanities, liberal arts
- **assistant** → assistant professor
- **center** → centre, institute, center for, centre for
- **chair** → chairs, chaired
- **collaboration** → collaborative, cooperate, cooperation, cooperative
- **comprehensive** → comprehensively
- **continue** → continuing, continuation
- **curriculum** → curricular, syllabus, course design
- **education** → educational, pedagogy, pedagogical, teaching
- **eligible** → eligibility
- **employees** → employee, employment, employ
- **engage** → engagement, engaging, engaged
- **ethical** → ethics, metaethics, meta-ethics, normative ethics, applied ethics, moral philosophy, moral theory
- **ethics** → ethical, metaethics, meta-ethics, normative ethics, moral philosophy, moral theory
- **expertise** → expert, specialization, specialism
- **focus** → focused, focusing, foci
- **global** → global justice, cosmopolitanism, cosmopolitan
- **high** → higher, highly
- **highly** → high
- **hours** → hour
- **humanities** → humanistic, liberal arts, studia humanitatis
- **interested** → interest
- **introductory** → introduction, intro, introductions
- **leadership** → leader, lead, leading
- **liberal** → liberal arts
- **logic** → logical, logics, logician
- **medical** → bioethics, biomedical ethics, medical ethics, clinical ethics, healthcare ethics
- **month** → monthly, months
- **opportunities** → opportunity
- **participate** → participation, participatory, participant
- **philosophical** → philosophy, philosophic
- **political** → political philosophy, political theory
- **postdoctoral** → postdoc, post-doctoral, post-doc
- **process** → process philosophy, process metaphysics, process thought
- **projects** → project
- **public** → public philosophy
- **recommendation** → recommendations, reference, references
- **record** → records, recording
- **relevant** → relevance
- **renewal** → renewable, reappointment
- **research** → scholarship, scholarly, investigation
- **science** → scientific, sciences, philosophy of science
- **social** → social philosophy
- **specialization** → specialisation, specialty, speciality, area of specialization, aos
- **success** → successful, successfully, succeed
- **syllabi** → syllabus
- **system** → systems, systematic, systematically
- **technology** → technological, tech, digital technology
- **thinking** → think, thought
- **vision** → visionary
- **visit** → visiting, visitor

---

## How to Inspect Raw Data

- **Machine-readable JSON:** [`data/synonym_map.json`](../data/synonym_map.json)
- **Raw job description text:** [`data/all_jobs.json`](../data/all_jobs.json) — each job has a `description` field with the full posting text.
- **Source code:** the synonym generation lives in `scraper.py` under the `generate_synonym_map` method.

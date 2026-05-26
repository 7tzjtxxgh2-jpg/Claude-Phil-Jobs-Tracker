# Keyword Explorer — Synonym Map

**Last updated:** 2026-05-26
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

- **access** → accessibility, accessible
- **active** → engaged, engagement, activity
- **applied** → practical, application, praxis
- **arts** → humanities, liberal arts
- **chair** → chairperson, chaired
- **collaboration** → collaborative, collaborator, collaborating
- **comprehensive** → comprehensively
- **critical** → critique, criticism
- **curriculum** → curricular, syllabus, course design
- **description** → describe, described, descriptive
- **education** → educational, pedagogy, pedagogical, teaching
- **employees** → employee, employment, employer
- **engage** → engagement, engaged, engaging
- **environment** → environmental, ecology, ecological, environmental philosophy, environmental ethics
- **ethics** → ethical, metaethics, meta-ethics, normative ethics, moral philosophy, moral theory
- **focus** → focused, focusing, foci
- **health** → medical, medicine, bioethics, biomedical, healthcare, clinical
- **high** → higher, highest
- **highly** → high
- **history** → historical, historiography, historian
- **interdisciplinary** → multidisciplinary, cross-disciplinary, transdisciplinary
- **interests** → interest, interested, interesting
- **introductory** → introduction, intro, elementary, foundational
- **leadership** → leader, lead, leading
- **liberal** → liberal arts
- **member** → membership, members
- **month** → monthly, months
- **participate** → participation, participatory, participant
- **philosophical** → philosophy
- **political** → political philosophy, political theory
- **postdoctoral** → postdoc, post-doctoral, post-doc
- **potential** → potentially
- **projects** → project
- **public** → public philosophy
- **research** → scholarship, scholarly, investigation
- **scholars** → scholar, scholarship
- **science** → sciences, scientific, philosophy of science
- **sciences** → science, scientific, philosophy of science
- **social** → social philosophy
- **success** → successful, successfully
- **syllabi** → syllabus
- **system** → systems, systematic, systemic
- **technology** → philosophy of technology, tech ethics, digital ethics
- **thinking** → thought, think

---

## How to Inspect Raw Data

- **Machine-readable JSON:** [`data/synonym_map.json`](../data/synonym_map.json)
- **Raw job description text:** [`data/all_jobs.json`](../data/all_jobs.json) — each job has a `description` field with the full posting text.
- **Source code:** the synonym generation lives in `scraper.py` under the `generate_synonym_map` method.

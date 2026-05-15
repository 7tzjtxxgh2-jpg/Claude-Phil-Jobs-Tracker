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

- **access** → accessibility, accessible, open access, equity of access
- **active** → active
- **activities** → work, research, scholarship, teaching
- **addition** → additionally, furthermore, also
- **additional** → supplementary, further, extra
- **applied** → application, applied ethics, practical
- **arts** → humanities, liberal arts, fine arts
- **associate** → assistant, junior, affiliated, collaborative
- **background** → training, preparation, credentials, qualifications
- **center** → institute, lab, laboratory, research center, program, hub
- **chair** → department chair, chairperson, department head, chair position
- **city** → urban, urbanism
- **collaboration** → collaborative, interdisciplinary, cross-disciplinary, teamwork
- **commitment** → commitments, committed
- **committed** → commitment, commitments
- **competence** → competence, competency, expertise
- **consideration** → considered, consider
- **considered** → consideration, consider
- **continue** → ongoing, continuing, sustained
- **contribute** → contribution, contributions, contributor
- **core** → foundational, central, essential
- **creative** → creativity
- **critical** → critical theory, critique, critical analysis
- **curriculum** → course design, program, syllabus, coursework
- **description** → description, job description
- **development** → developmental
- **discipline** → discipline, field, subdiscipline, specialization
- **diverse** → diversity, diversification
- **education** → pedagogy, teaching, instruction, learning, educational, academic
- **educational** → education, pedagogy, teaching
- **eligible** → qualified, eligible, eligible
- **employees** → employment, labor
- **engage** → engagement, engaged
- **engagement** → engaged, community engagement, public engagement
- **environment** → environmental, ecology, ecological
- **ethical** → ethics, moral, normative
- **ethics** → moral philosophy, normative ethics, applied ethics, ethical theory
- **evidence** → empirical
- **expertise** → specialization, competence, knowledge, proficiency, research focus
- **first** → inaugural
- **focus** → focal, focused
- **funding** → grant, financial support, endowment, fellowship, scholarship
- **general** → generalist, broad, interdisciplinary
- **health** → healthcare, medical
- **higher** → higher education, academic
- **highly** → highly
- **history** → historical, historian
- **humanities** → humanistic, liberal arts, letters, human sciences
- **includes** → encompasses, comprises, covers, spans
- **innovative** → innovation
- **intellectual** → intellectual
- **interdisciplinary** → interdisciplinarity, cross-disciplinary, multidisciplinary
- **interest** → interests, interested
- **interested** → interested in, focused on, working in
- **interests** → interest-based
- **introductory** → intro, survey, foundational
- **knowledge** → knowledge, expertise, specialization
- **leadership** → leader, leading
- **leading** → prominent, preeminent
- **learning** → pedagogy, pedagogical, teaching
- **least** → minimum, minimal
- **liberal** → liberal arts, general education
- **limited** → restricted, constrained, finite
- **located** → located
- **logic** → logical, formal logic, symbolic logic
- **major** → primary, principal
- **member** → membership, affiliation
- **members** → membership
- **mission** → mandate, vision, purpose, goals, objectives
- **names** → names
- **needs** → requires, demands, seeks
- **online** → digital, virtual, distance
- **opportunities** → positions, openings, appointments, roles
- **participate** → participation, participatory
- **person** → personal, personhood
- **philosophical** → philosophy, philosophic
- **plan** → planning
- **policy** → policies, governance, institutional policy
- **political** → political philosophy, political theory, politics
- **postdoctoral** → postdoc, postdoctorate
- **prior** → previous, prior
- **process** → methodology, method, procedural, procedures
- **professional** → professionalism
- **projects** → project-based, research projects
- **public** → public philosophy, public intellectual
- **received** → received
- **recommendation** → reference, letter of recommendation, referral
- **relevant** → pertinent, applicable, germane
- **renewable** → sustainability, sustainable
- **renewal** → renewal, reappointment
- **research** → empirical, inquiry, investigation, scholarship, academic research, research methods
- **role** → position, appointment
- **scholars** → scholars, academics, researchers
- **science** → scientific, natural science, empirical science, stem
- **sciences** → natural sciences, scientific disciplines, stem
- **seeks** → seeking
- **semester** → term, academic year
- **serve** → support, advance, promote
- **skills** → skill-based
- **social** → social philosophy, social theory, sociology
- **specialization** → specialty, subspecialty, area of focus, research area, subfield
- **staff** → staffing
- **state** → status, condition
- **studies** → studies, research area, subfield
- **subject** → discipline, field, area
- **submitted** → submitted
- **success** → successful
- **syllabi** → syllabus, course materials, curricula
- **system** → system
- **technology** → technological, digital, computational
- **term** → term, appointment term
- **thinking** → thought, intellectual
- **training** → pedagogy, instruction, teaching, curriculum, educational development
- **visit** → visiting, visiting position, visiting appointment, sabbatical, temporary appointment
- **visiting** → visiting, temporary, short-term
- **vitae** → cv, curriculum vitae
- **world** → global, international, worldwide

---

## How to Inspect Raw Data

- **Machine-readable JSON:** [`data/synonym_map.json`](../data/synonym_map.json)
- **Raw job description text:** [`data/all_jobs.json`](../data/all_jobs.json) — each job has a `description` field with the full posting text.
- **Source code:** the synonym generation lives in `scraper.py` under the `generate_synonym_map` method.

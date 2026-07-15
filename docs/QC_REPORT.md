# Semi-Annual Opus QC Report

**Generated:** 2026-07-15
**Reference model (live dashboard):** `claude-sonnet-4-5`
**QC model:** `claude-opus-4-5`
**Jobs evaluated:** 244

---

## Purpose

Twice a year (January 15 and July 15), the more capable Opus model
independently re-classifies the corpus using the same prompt and
taxonomy as the live Sonnet pipeline.
This report compares Opus against the live Sonnet labels to:

1. Quantify how often the two models agree (a sanity check on Sonnet quality)
2. Surface specific jobs where they disagree (for spot-review)
3. Create a defensible audit trail: "we periodically verify with the
   most capable available model"

Sonnet labels remain authoritative on the dashboard. This QC does not
change any live classifications. Raw Opus output is saved to
`data/qc_opus_2026-07-15.json` for full reproducibility.

---

## Agreement Summary

| Field | Agreement rate |
|---|---|
| `main_aos` (exact set match) | **86.1%** (210/244) |
| `position_type` | 89.3% (218/244) |
| `institution_type` | 95.5% (233/244) |

## Per-Main-Category Agreement

"Match" means both models tagged the job with this category.

| Category | Match / Total | Rate |
|---|---|---|
| Ethics | 75 / 89 | 84.3% |
| Social & Political Philosophy | 48 / 55 | 87.3% |
| Value Theory / Aesthetics | 5 / 10 | 50.0% |
| History of Philosophy | 35 / 40 | 87.5% |
| Non-Western & Cross-Cultural Philosophy | 3 / 8 | 37.5% |
| Metaphysics & Epistemology | 35 / 42 | 83.3% |
| Science, Logic, & Mathematics | 71 / 78 | 91.0% |
| Open | 47 / 61 | 77.0% |

## Disagreements (59 jobs)

Jobs where Sonnet's `main_aos` or `position_type` differs from Opus's.
Inspect each manually if needed — Opus output is stored in
`data/qc_opus_2026-07-15.json`.

### University of Texas at El Paso — Visiting Assistant Professor of Philosophy
- **Sonnet main_aos:** Open
- **Opus main_aos:** History of Philosophy, Social & Political Philosophy
- **Sonnet position_type:** Visiting / Adjunct / Lecturer (Fixed-Term)
- **Opus position_type:** Visiting / Adjunct / Lecturer (Fixed-Term)
- **Sonnet reasoning:** The AOS is explicitly 'Open' with no stated preference, only teaching needs mentioned in AOC (Social-Political Philosophy and History of Philosophy), which does not constitute an AOS preference. The p
- **Opus reasoning:** While AOS is listed as Open, the description specifies teaching needs in Social-Political Philosophy and History of Philosophy (Ancient, Modern, Twentieth Century), indicating a preference. The positi

### Department of Philosophy, University College London — Postdoctoral Research Fellow
- **Sonnet main_aos:** History of Philosophy, Metaphysics & Epistemology, Value Theory / Aesthetics
- **Opus main_aos:** Ethics, History of Philosophy, Metaphysics & Epistemology, Social & Political Philosophy, Value Theory / Aesthetics
- **Sonnet position_type:** Postdoc / Fellowship
- **Opus position_type:** Postdoc / Fellowship
- **Sonnet reasoning:** The posting explicitly lists four distinct areas: value theory (broadly construed to include ethics, political philosophy, jurisprudence, aesthetics, and moral psychology), history of philosophy, phen
- **Opus reasoning:** The posting explicitly lists multiple distinct AOS areas: value theory (ethics, political philosophy, jurisprudence, aesthetics, moral psychology), history of philosophy, phenomenology, and philosophy

### Department of Philosophy and Religious Studies, Peking University — Assistant Professor/ Tenure-Track Associate Professor/ Tenured Associate Profess
- **Sonnet main_aos:** Ethics, History of Philosophy, Metaphysics & Epistemology, Non-Western & Cross-Cultural Philosophy, Science, Logic, & Mathematics, Social & Political Philosophy, Value Theory / Aesthetics
- **Opus main_aos:** Ethics, History of Philosophy, Metaphysics & Epistemology, Non-Western & Cross-Cultural Philosophy, Science, Logic, & Mathematics, Social & Political Philosophy, Value Theory / Aesthetics
- **Sonnet position_type:** Other
- **Opus position_type:** Tenure-Track
- **Sonnet reasoning:** The posting states 'Open but... preferred' with seven distinct philosophical areas listed (Chinese Philosophy, Foreign Philosophy, Marxist Philosophy, Logic, Ethics, Aesthetics, Philosophy of Science 
- **Opus reasoning:** The posting lists multiple distinct preferred areas spanning nearly all main categories: Marxist Philosophy and Foreign Philosophy (History), Chinese Philosophy (Non-Western/Asian), Logic and Philosop

### Department of Philosophy, University of Bristol — PhD in Political and Social Philosophy
- **Sonnet main_aos:** Social & Political Philosophy
- **Opus main_aos:** Social & Political Philosophy
- **Sonnet position_type:** Other
- **Opus position_type:** Postdoc / Fellowship
- **Sonnet reasoning:** This is a PhD studentship (graduate fellowship) in political and social philosophy, focusing on migration, borders, and displacement. Position type is 'Other' because it is a graduate student position
- **Opus reasoning:** This is a funded PhD studentship (graduate fellowship) at the University of Bristol in the UK, focused on political philosophy, social epistemology, and migration studies as part of an ERC-funded rese

### International Centre for Neuroscience and Ethics (CINET) — Call for applications for a pre-doctoral scholarship in Neuroscience and Humanit
- **Sonnet main_aos:** Ethics
- **Opus main_aos:** Ethics
- **Sonnet position_type:** Other
- **Opus position_type:** Postdoc / Fellowship
- **Sonnet reasoning:** This is a pre-doctoral (graduate) scholarship in neuroscience and humanities at a neuroscience and ethics center, strongly suggesting neuroethics focus. Position type is 'Other' because it is a gradua
- **Opus reasoning:** Pre-doctoral scholarship at a Neuroscience and Ethics center with AOS in 'Neuroscience and humanities' indicates neuroethics focus. The position is a graduate fellowship (pre-doctoral scholarship), wh

### Department of Historical, Philosophical and Religious Studies, Umeå University,  — Doctoral student in Philosophy, specialization in Ethics in Teacher Education
- **Sonnet main_aos:** Ethics, Social & Political Philosophy
- **Opus main_aos:** Ethics
- **Sonnet position_type:** Other
- **Opus position_type:** Postdoc / Fellowship
- **Sonnet reasoning:** This is a doctoral student position (PhD program), which does not fit the standard categories of tenure-track, postdoc, visiting, or tenured positions. The AOS focuses on ethics in teacher education, 
- **Opus reasoning:** This is a doctoral student position (PhD fellowship) specializing in Ethics in Teacher Education, focusing on ethical issues in educational contexts such as ethics education, professional ethics for t

### Department of Philosophy, Goethe University Frankfurt am Main — Doctoral Researcher
- **Sonnet main_aos:** Ethics
- **Opus main_aos:** Ethics
- **Sonnet position_type:** Other
- **Opus position_type:** Postdoc / Fellowship
- **Sonnet reasoning:** The position is explicitly for Ethics or Metaethics AOS with AOC in Metaethics and Normative Ethics. Classified as 'Other' because it is a doctoral/graduate fellowship for a PhD student (not a postdoc
- **Opus reasoning:** The posting explicitly lists AOS as 'Ethics or Metaethics' and AOC as 'Metaethics, Normative Ethics'. This is a doctoral researcher position (graduate fellowship/fixed-term) focused on independent res

### Center for Inquirynot BA-granting — Editor of Free Inquiry Magazine and Executive Director of the Council for Secula
- **Sonnet main_aos:** Ethics, Metaphysics & Epistemology
- **Opus main_aos:** Metaphysics & Epistemology
- **Sonnet position_type:** Other
- **Opus position_type:** Other
- **Sonnet reasoning:** This is an editorial and executive director position at a nonprofit organization, not a faculty position, making it 'Other'. The AOS states 'Open, but philosophy of religion preferred' and AOC states 
- **Opus reasoning:** This is a non-academic position (Editor/Executive Director at a nonprofit organization), explicitly categorized as 'Other (non-academic)'. The AOS states 'Open, but philosophy of religion preferred', 

### Dpeartment of Philosophy , University of Edinburgh — PhD position in AI Ethics and Philosophy of Science
- **Sonnet main_aos:** Ethics, Science, Logic, & Mathematics
- **Opus main_aos:** Ethics, Science, Logic, & Mathematics
- **Sonnet position_type:** Other
- **Opus position_type:** Postdoc / Fellowship
- **Sonnet reasoning:** This PhD position explicitly requires work in both AI Ethics AND Philosophy of Science as independent research areas (examining epistemic value of ML models and concepts of idealization, representatio
- **Opus reasoning:** The AOS explicitly lists both 'Ethics of AI' and 'Philosophy of Science' as distinct areas. This is not merely applied ethics but genuinely spans both domains—the description emphasizes researching co

### The Department of Historical, Philosophical and Religious Studies, Umeå Universi — PhD position in philosophy (4-year salaried), open to all areas of philosophy
- **Sonnet main_aos:** Open
- **Opus main_aos:** Open
- **Sonnet position_type:** Other
- **Opus position_type:** Postdoc / Fellowship
- **Sonnet reasoning:** This is a PhD student position (graduate fellowship) in Sweden, which does not fit the standard US academic position types (tenure-track, postdoc, visiting, tenured). The AOS is genuinely open with no
- **Opus reasoning:** This is a 4-year salaried PhD position explicitly open to all areas of philosophy with no stated preference. The title and AOS both indicate 'open to all areas of philosophy' with no preference mentio

### Technion, Israel Institute of Technology — Funded PhD Positions in Philosophy
- **Sonnet main_aos:** History of Philosophy, Metaphysics & Epistemology, Science, Logic, & Mathematics
- **Opus main_aos:** History of Philosophy, Metaphysics & Epistemology, Science, Logic, & Mathematics
- **Sonnet position_type:** Other
- **Opus position_type:** Postdoc / Fellowship
- **Sonnet reasoning:** This is a funded PhD student position, which does not fit any of the five standard faculty position types (it is neither a postdoc, nor a faculty appointment). The AOS spans three distinct areas: phil
- **Opus reasoning:** This is a funded PhD fellowship position at Technion in Israel. The AOS explicitly covers philosophy of science (life sciences, cognitive science, pharmacy/medicine), philosophy of mind and perception

### Philosophy, Skidmore College — Visiting Assistant Professor
- **Sonnet main_aos:** Open
- **Opus main_aos:** Ethics, Non-Western & Cross-Cultural Philosophy
- **Sonnet position_type:** Visiting / Adjunct / Lecturer (Fixed-Term)
- **Opus position_type:** Visiting / Adjunct / Lecturer (Fixed-Term)
- **Sonnet reasoning:** The AOS is explicitly 'Open' with no stated preference (AOC mentions non-European philosophy or ethics as areas of competence, not specialization). This is a one-year sabbatical replacement Visiting A
- **Opus reasoning:** While AOS is listed as open, the AOC specifies 'non-European philosophy or ethics,' indicating a clear preference for candidates in these areas. The position is a one-year Visiting Assistant Professor

### Fakultät für Wirtschafts- und Sozialwissenschaften,  Universität Hamburg — Doctoral researchers in the DFG Graduate Program “Collective Decision-Making” (1
- **Sonnet main_aos:** Ethics, Science, Logic, & Mathematics, Social & Political Philosophy
- **Opus main_aos:** Science, Logic, & Mathematics, Social & Political Philosophy
- **Sonnet position_type:** Postdoc / Fellowship
- **Opus position_type:** Postdoc / Fellowship
- **Sonnet reasoning:** This is a DFG-funded doctoral fellowship program focused on collective decision-making across Economics, Philosophy, and Political Science, involving both descriptive and normative dimensions. The int
- **Opus reasoning:** This is a doctoral fellowship program focused on 'Collective Decision-Making' spanning Economics, Philosophy, and Political Science. The research program addresses 'descriptive and normative dimension

### Department of Philosophy, University at Buffalo — Postdoctoral Associate (Research)
- **Sonnet main_aos:** Metaphysics & Epistemology, Science, Logic, & Mathematics, Social & Political Philosophy
- **Opus main_aos:** Science, Logic, & Mathematics, Social & Political Philosophy
- **Sonnet position_type:** Postdoc / Fellowship
- **Opus position_type:** Postdoc / Fellowship
- **Sonnet reasoning:** The posting explicitly lists PPE as primary AOS along with empirical/experimental methods, and AOC includes social epistemology, social and political philosophy, and philosophy of science—three genuin
- **Opus reasoning:** The AOS explicitly lists PPE and Empirical/Experimental Methods, with AOC including Social Epistemology, Social and Political Philosophy, and Philosophy of Science. The position involves research with

### Philosophy, Carnegie Mellon University — Head of Philosophy Department
- **Sonnet main_aos:** Open
- **Opus main_aos:** Open
- **Sonnet position_type:** Other
- **Opus position_type:** Tenured / Continuing / Permanent
- **Sonnet reasoning:** This is a department head position with substantial administrative responsibilities (budget oversight, hiring, strategic leadership) rather than a standard faculty appointment, making it 'Other'. Whil
- **Opus reasoning:** This is a Department Head position at the full professor level with tenure. While the description mentions the department's research strengths (logic, formal epistemology, philosophy of science, ethic

### Department of Philosophy, Davidson College — Visiting Assistant Professor of Philosophy
- **Sonnet main_aos:** Open
- **Opus main_aos:** History of Philosophy, Metaphysics & Epistemology, Social & Political Philosophy
- **Sonnet position_type:** Visiting / Adjunct / Lecturer (Fixed-Term)
- **Opus position_type:** Visiting / Adjunct / Lecturer (Fixed-Term)
- **Sonnet reasoning:** The AOS is explicitly 'Open' with no stated preference (the 'teaching needs' mentioned are anticipated course coverage areas, not AOS preferences for hiring). This is a two-year Visiting Assistant Pro
- **Opus reasoning:** Although AOS/AOC are listed as open, the description specifies anticipated teaching needs in early modern philosophy, political philosophy, epistemology, and philosophy of language, which constitute s

### History and Philosophy , The University of Texas Dallas — Assistant Professor of Philosophy
- **Sonnet main_aos:** History of Philosophy, Non-Western & Cross-Cultural Philosophy
- **Opus main_aos:** History of Philosophy
- **Sonnet position_type:** Tenure-Track
- **Opus position_type:** Tenure-Track
- **Sonnet reasoning:** The position explicitly requires expertise in Early or Late Modern Philosophy (Descartes to Hegel) and especially welcomes candidates working at intersections with Non-Western or underrepresented phil
- **Opus reasoning:** The AOS explicitly specifies Early or Late Modern Philosophy (Descartes to Hegel), which spans 17th-19th century philosophy. While Non-Western traditions are mentioned as welcome intersections, the pr

### The Prindle Institute for Ethics, DePauw University — Manager, Campus Ethics Programs
- **Sonnet main_aos:** Open
- **Opus main_aos:** Ethics, Social & Political Philosophy
- **Sonnet position_type:** Other
- **Opus position_type:** Other
- **Sonnet reasoning:** This is a non-academic administrative position managing student programs and co-curricular activities, not a faculty role. While the AOS lists Ethics and Public Philosophy, the position is for a progr
- **Opus reasoning:** This is explicitly an administrative (non-academic) position for a 'Manager' of campus ethics programs, not a faculty role. The AOS lists Ethics and Public Philosophy, which maps to Ethics and Social 

### School of Humanities, the University of Hong Kong — Professor/Associate Professor on tenure terms or tenure-track Assistant Professo
- **Sonnet main_aos:** Ethics, Science, Logic, & Mathematics
- **Opus main_aos:** Ethics
- **Sonnet position_type:** Tenure-Track
- **Opus position_type:** Tenure-Track
- **Sonnet reasoning:** Although the AOS is listed as 'Open', the posting explicitly requires 'an interest in – and commitment to – pursuing teaching and research in philosophy or ethics of AI', which constitutes a clear sta
- **Opus reasoning:** While the AOS field says 'Open', the description explicitly states applicants 'must have an interest in – and commitment to – pursuing teaching and research in philosophy or ethics of AI.' This stated

### Parr Center for Ethics, Philosophy Department, University of North Carolina, Cha — Postdoctoral Fellow, Educating for the Virtues of Attention (EVA)
- **Sonnet main_aos:** Ethics
- **Opus main_aos:** Ethics, Metaphysics & Epistemology
- **Sonnet position_type:** Postdoc / Fellowship
- **Opus position_type:** Postdoc / Fellowship
- **Sonnet reasoning:** The position focuses on philosophy of attention, intellectual virtue, and character development, all of which fall under virtue ethics within the Ethics category. This is a postdoctoral fellowship pos
- **Opus reasoning:** The posting focuses on philosophy of attention (which falls under Philosophy of Mind) and intellectual virtue/character development (Virtue Ethics). The emphasis on attentional virtues and virtue cult

### Department of History and Philosophy, Kennesaw State University — Chair of the Department of History and Philosophy
- **Sonnet main_aos:** Open
- **Opus main_aos:** Open
- **Sonnet position_type:** Other
- **Opus position_type:** Tenured / Continuing / Permanent
- **Sonnet reasoning:** This is a department chair position that is primarily administrative rather than a faculty appointment with a chair component. While it includes some teaching and research expectations, the posting is
- **Opus reasoning:** This is a department chair position with tenured Professor rank. The AOS and AOC are both listed as 'Open' with no stated preferences for philosophy specialization - the position accepts candidates wi

### Philosophy Department, Rhode Island College — Assistant Professor of Philosophy
- **Sonnet main_aos:** Open
- **Opus main_aos:** Ethics, Social & Political Philosophy
- **Sonnet position_type:** Tenure-Track
- **Opus position_type:** Tenure-Track
- **Sonnet reasoning:** The AOS is explicitly 'Open' with no stated preference, while the AOC (areas of competence) are Ethics and Social/Political Philosophy. Since AOC represents teaching competence rather than research sp
- **Opus reasoning:** While AOS is listed as 'Open', the AOC explicitly requires Ethics and Social/Political Philosophy, and the description states they seek candidates with 'teaching strengths in Ethics and Social/Politic

### School of Humanities, University of West Georgia — Limited-Term Instructor of Philosophy
- **Sonnet main_aos:** Ethics, Non-Western & Cross-Cultural Philosophy, Science, Logic, & Mathematics
- **Opus main_aos:** Open
- **Sonnet position_type:** Visiting / Adjunct / Lecturer (Fixed-Term)
- **Opus position_type:** Visiting / Adjunct / Lecturer (Fixed-Term)
- **Sonnet reasoning:** The posting states AOS/AOC are open but explicitly prefers teaching competence in Professional Ethics (Business Ethics), Technology and Human Values (Science/Technology), and Introduction to World Rel
- **Opus reasoning:** The posting explicitly states 'Area of specialization and area of competence open' with only teaching competence preferences (Professional Ethics, Technology and Human Values, World Religions) rather 

### School of Civic Leadership, University of Texas at Austin — Great Books (Assistant Professor)
- **Sonnet main_aos:** History of Philosophy, Social & Political Philosophy
- **Opus main_aos:** History of Philosophy, Social & Political Philosophy, Value Theory / Aesthetics
- **Sonnet position_type:** Tenure-Track
- **Opus position_type:** Tenure-Track
- **Sonnet reasoning:** This Great Books position explicitly focuses on political thought, philosophy, literature, and religious studies with emphasis on foundational texts from Athens, Jerusalem, and Roman law, as well as A
- **Opus reasoning:** This Great Books position spans multiple areas: political thought and civic leadership (Social & Political Philosophy), engagement with foundational texts from Athens, Jerusalem, and Roman law (Histor

### Department of Philosophy, University of Bristol — Senior Research Associate in Metaethics/Value Theory
- **Sonnet main_aos:** Ethics
- **Opus main_aos:** Ethics, Value Theory / Aesthetics
- **Sonnet position_type:** Postdoc / Fellowship
- **Opus position_type:** Postdoc / Fellowship
- **Sonnet reasoning:** This is a three-year postdoctoral research position focused on metaethics and value theory, investigating evaluative language as part of an ERC-funded project. While philosophy of language is mentione
- **Opus reasoning:** The position explicitly focuses on metaethics and value theory as stated in the AOS and title. Metaethics falls under Ethics, while value theory (investigating moral and non-moral value, evaluative ad

### Department of Philosophy, University of Bristol — Senior Research Associate in Philosophy of Language/Linguistics
- **Sonnet main_aos:** Ethics, Metaphysics & Epistemology
- **Opus main_aos:** Metaphysics & Epistemology
- **Sonnet position_type:** Postdoc / Fellowship
- **Opus position_type:** Postdoc / Fellowship
- **Sonnet reasoning:** This is a three-year postdoctoral research position focused on philosophy of language/linguistics investigating evaluative adjectives, with explicit connections to metaethics and value theory. The pos
- **Opus reasoning:** This is a three-year postdoctoral research position explicitly focused on Philosophy of Language/Linguistics as part of an ERC project on evaluative adjectives. The job category states 'Postdoc or sim

### Law School, King's College London — YTL Early Career Research Fellow
- **Sonnet main_aos:** Social & Political Philosophy
- **Opus main_aos:** Ethics, Social & Political Philosophy
- **Sonnet position_type:** Postdoc / Fellowship
- **Opus position_type:** Postdoc / Fellowship
- **Sonnet reasoning:** This is a 12-month early career research fellowship at the Yeoh Tiong Lay Centre for Politics, Philosophy and Law, clearly a postdoctoral position. The AOS is explicitly stated as 'Politics, Philosoph
- **Opus reasoning:** This is a 12-month Early Career Research Fellowship at King's College London for researchers in 'Politics, Philosophy and Law' (PPL), which spans political philosophy and philosophy of law. The positi

### Department of Philosophy and Institute for Logic, Language and Computation, Univ — Two PhD positions in Philosophical Logic
- **Sonnet main_aos:** Science, Logic, & Mathematics
- **Opus main_aos:** Science, Logic, & Mathematics
- **Sonnet position_type:** Other
- **Opus position_type:** Postdoc / Fellowship
- **Sonnet reasoning:** The positions are PhD fellowships in philosophical logic, focusing on property theory and modal logic within a formal logic research project. PhD positions are graduate student positions, not postdoct
- **Opus reasoning:** The position is explicitly for PhD candidates in Philosophical Logic within the GOOD INTENSIONS project, focusing on the logic of property talk and modal talk. This falls squarely under Logic in Scien

### School of Historical and Philosophical Studies, University of Melbourne — Two funded PhD Positions
- **Sonnet main_aos:** Metaphysics & Epistemology, Science, Logic, & Mathematics
- **Opus main_aos:** Metaphysics & Epistemology, Science, Logic, & Mathematics
- **Sonnet position_type:** Other
- **Opus position_type:** Postdoc / Fellowship
- **Sonnet reasoning:** Two PhD scholarships focusing on (1) metaphysics of causation, space, and time in physics, and (2) explainable AI using interventionist causation frameworks. This is a graduate fellowship position at 
- **Opus reasoning:** This posting offers two PhD scholarships with explicit AOS in Metaphysics, Philosophy of Science, and Philosophy of AI. The first position focuses on metaphysics of causation, space, and time (Metaphy

### School of Civic Leadership, University of Texas at Austin — Great Books (Associate/Full Professor)
- **Sonnet main_aos:** History of Philosophy, Social & Political Philosophy
- **Opus main_aos:** History of Philosophy, Social & Political Philosophy, Value Theory / Aesthetics
- **Sonnet position_type:** Tenured / Continuing / Permanent
- **Opus position_type:** Tenured / Continuing / Permanent
- **Sonnet reasoning:** This is a senior faculty position (Associate/Full Professor) at a research university focused on Great Books pedagogy spanning political thought, philosophy, literature, and religious studies. The emp
- **Opus reasoning:** This Great Books position at associate/full professor level spans multiple areas: political thought and civic leadership (Social & Political Philosophy), engagement with foundational texts from Athens

### Philosophy, CNRS, Archives Poincaré — Doctoral position, M/F, Philosophy of Science, Nancy, France. Explanatory progre
- **Sonnet main_aos:** Science, Logic, & Mathematics
- **Opus main_aos:** Science, Logic, & Mathematics
- **Sonnet position_type:** Other
- **Opus position_type:** Postdoc / Fellowship
- **Sonnet reasoning:** This is a doctoral/PhD student position in philosophy of science focusing on explanation, understanding, and mathematical methods in physics. Classified as 'Other' because it is a graduate student pos
- **Opus reasoning:** This is a doctoral fellowship position at CNRS in France focused on philosophy of science, specifically examining explanatory progress and understanding in mathematical/mathematized sciences with exam

### Baruch College — Assistant Professor - Jewish Studies
- **Sonnet main_aos:** Non-Western & Cross-Cultural Philosophy
- **Opus main_aos:** Open
- **Sonnet position_type:** Tenure-Track
- **Opus position_type:** Tenure-Track
- **Sonnet reasoning:** This is a tenure-track position in Jewish Studies with possible appointment in Philosophy (among other departments). While AOS is listed as 'Open,' the posting clearly requires expertise in Jewish phi
- **Opus reasoning:** The AOS is listed as 'Open' with no stated preference for a specific philosophical area. While Jewish philosophy is mentioned as one possible area of expertise among several interdisciplinary options 

### Department of Philosophy, Virginia Tech — Visiting Assistant Professor
- **Sonnet main_aos:** Value Theory / Aesthetics
- **Opus main_aos:** Ethics, Value Theory / Aesthetics
- **Sonnet position_type:** Visiting / Adjunct / Lecturer (Fixed-Term)
- **Opus position_type:** Visiting / Adjunct / Lecturer (Fixed-Term)
- **Sonnet reasoning:** The AOS is explicitly 'Value Theory (broadly construed)', which maps to the Value Theory / Aesthetics main category. This is a one-year Visiting Assistant Professor position with possibility of renewa
- **Opus reasoning:** The AOS is explicitly 'value theory (broadly construed)' which falls under Value Theory / Aesthetics. However, the teaching examples (Morality and Justice, Global Ethics, Ethical Theory) indicate stro

### Department of Philosophy I, Ruhr University Bochum — 1 Postdoc Position, History and Philosophy of Science, Digital Humanities
- **Sonnet main_aos:** History of Philosophy, Science, Logic, & Mathematics
- **Opus main_aos:** Science, Logic, & Mathematics
- **Sonnet position_type:** Postdoc / Fellowship
- **Opus position_type:** Postdoc / Fellowship
- **Sonnet reasoning:** This is a 3-year postdoctoral position within an ERC-funded project on history and philosophy of science (specifically botanical research and virtual herbaria), combining philosophy of biology with hi
- **Opus reasoning:** The position is explicitly for History and Philosophy of Science within an ERC project on virtual herbaria. The AOS specifies History of Science and Digital Humanities, with AOC in History and Philoso

### Department of Philosophy, University of Tartu — 3 Fully-Funded Junior Research Fellowships (Doctoral positions)
- **Sonnet main_aos:** Open
- **Opus main_aos:** Open
- **Sonnet position_type:** Other
- **Opus position_type:** Postdoc / Fellowship
- **Sonnet reasoning:** This is a doctoral/PhD fellowship position with student status, which does not fit the standard categories of faculty positions, postdocs, or pure fellowships. The AOS is genuinely open with no stated
- **Opus reasoning:** This is a doctoral fellowship position (Junior Research Fellowship) with AOS and AOC both listed as Open, with no stated preferences for any specific philosophical area. The position is research-focus

### Department of Philosophy, McMaster University — Assistant Professor (Contractually Limited Appointment)
- **Sonnet main_aos:** Ethics
- **Opus main_aos:** Ethics, Value Theory / Aesthetics
- **Sonnet position_type:** Visiting / Adjunct / Lecturer (Fixed-Term)
- **Opus position_type:** Visiting / Adjunct / Lecturer (Fixed-Term)
- **Sonnet reasoning:** Though AOS is listed as 'Open', the posting explicitly seeks applicants qualified to teach bioethics and ethics, with AOC in Ethics and Applied Ethics, making Ethics the clear main category. This is a
- **Opus reasoning:** While AOS is listed as Open, the AOC specifies Ethics and Applied Ethics, and the description explicitly seeks candidates to teach bioethics, ethics, and 'value theory, broadly construed.' The mention

### Center for Public Engagement with Science, University of Cincinnati — Postdoctoral Fellow, Center for Public Engagement with Science
- **Sonnet main_aos:** Science, Logic, & Mathematics
- **Opus main_aos:** Open
- **Sonnet position_type:** Postdoc / Fellowship
- **Opus position_type:** Postdoc / Fellowship
- **Sonnet reasoning:** This is a postdoctoral fellowship at the Center for Public Engagement with Science. While the AOS is listed as 'Open,' the position explicitly requires a PhD 'in a field relevant to public engagement 
- **Opus reasoning:** This is a postdoctoral fellowship at the Center for Public Engagement with Science. Both AOS and AOC are listed as 'Open' with no stated preference for any specific philosophical area. The position ac

### Discipline of Philosophy, UWA India — Assistant Professor / Senior Assistant Professor - Philosophy
- **Sonnet main_aos:** Ethics, Science, Logic, & Mathematics
- **Opus main_aos:** Ethics, Science, Logic, & Mathematics
- **Sonnet position_type:** Tenured / Continuing / Permanent
- **Opus position_type:** Tenure-Track
- **Sonnet reasoning:** While the AOS is listed as 'Open', the description explicitly requires 'expertise in the philosophy of artificial intelligence and in professional ethics,' making this a dual-area position spanning bo
- **Opus reasoning:** While the AOS is listed as 'Open,' the description explicitly states 'the appointee must demonstrate expertise in the philosophy of artificial intelligence and in professional ethics.' This requires b

### Centre Gilles Gaston Granger, Université Aix-Marseille — PhD Position (3+1 years) in Philosophy of Physics
- **Sonnet main_aos:** Metaphysics & Epistemology, Science, Logic, & Mathematics
- **Opus main_aos:** Metaphysics & Epistemology, Science, Logic, & Mathematics
- **Sonnet position_type:** Other
- **Opus position_type:** Postdoc / Fellowship
- **Sonnet reasoning:** This is a PhD student position (graduate fellowship), which does not fit the standard categories of faculty positions, postdocs, or administrative roles, hence 'Other'. The AOS explicitly lists Philos
- **Opus reasoning:** The position explicitly lists Philosophy of Physics, Metaphysics, and Philosophy of Science as AOS areas. The description emphasizes both philosophy of physics topics and metaphysics of levels/non-fun

### Department of Philosophy, the University of Hong Kong — Professor/Associate Professor on tenure terms or tenure-track Assistant Professo
- **Sonnet main_aos:** Ethics
- **Opus main_aos:** Ethics, Science, Logic, & Mathematics
- **Sonnet position_type:** Tenure-Track
- **Opus position_type:** Tenure-Track
- **Sonnet reasoning:** The position explicitly requires interest in and commitment to teaching and research in philosophy or ethics of AI. While the AOS is technically open, the mandatory AI ethics requirement makes this an
- **Opus reasoning:** The AOS explicitly lists 'Ethics of AI, Philosophy' and the description states the position is 'open to all areas of specialization' but requires 'interest in pursuing teaching and research in philoso

### Department of Philosophy and Ethics, Eindhoven University of Technology — Lecturer
- **Sonnet main_aos:** Ethics
- **Opus main_aos:** Open
- **Sonnet position_type:** Tenured / Continuing / Permanent
- **Opus position_type:** Tenured / Continuing / Permanent
- **Sonnet reasoning:** The position is explicitly described as 'Junior faculty / Tenured, continuing or permanent' with a permanent contract after probation. While AOS is listed as 'Open', the AOC and description clearly em
- **Opus reasoning:** The AOS is explicitly listed as 'Open' with no stated preference for any specific area. While the AOC mentions applied ethics and ethics of technology, and the teaching focuses on engineering ethics c

### Department of Philosophy and Religious Studies, Norwegian University of Science  — Fully funded PhD fellowship (3 years) in metaphysics of physics
- **Sonnet main_aos:** Metaphysics & Epistemology, Science, Logic, & Mathematics
- **Opus main_aos:** Metaphysics & Epistemology, Science, Logic, & Mathematics
- **Sonnet position_type:** Other
- **Opus position_type:** Postdoc / Fellowship
- **Sonnet reasoning:** This PhD fellowship focuses on interdisciplinary research combining philosophy of physics (quantum mechanics, spacetime, entanglement) with metaphysics (nature of worlds, individuation, laws of nature
- **Opus reasoning:** The AOS explicitly lists Philosophy of physics, Philosophy of science, and Metaphysics, spanning two main categories. The position is a fully funded 3-year PhD fellowship focused on interdisciplinary 

### Magdalen College, Oxford — Postdoctoral Researcher:  The Ethics of Social Punishment
- **Sonnet main_aos:** Ethics, Social & Political Philosophy
- **Opus main_aos:** Social & Political Philosophy
- **Sonnet position_type:** Postdoc / Fellowship
- **Opus position_type:** Postdoc / Fellowship
- **Sonnet reasoning:** This is a postdoctoral research position focused on 'The Ethics of Social Punishment,' which spans both social/political philosophy (punishment as a social and political institution) and normative eth
- **Opus reasoning:** The posting explicitly seeks a political theorist, political philosopher, or social philosopher to work on 'The Ethics of Social Punishment.' While the project involves ethics, the AOS specifies polit

### Department of Philosophy, Bowling Green State University — Assistant Teaching Professor
- **Sonnet main_aos:** Open
- **Opus main_aos:** Open
- **Sonnet position_type:** Tenured / Continuing / Permanent
- **Opus position_type:** Visiting / Adjunct / Lecturer (Fixed-Term)
- **Sonnet reasoning:** The AOS is listed as 'Open' with no stated preferences in the description, which mentions teaching across multiple areas (history, ethics, formal methods, PPEL) but does not indicate hiring preference
- **Opus reasoning:** Both AOS and AOC are explicitly listed as 'Open' with no stated preferences in the description. The position is a fixed-term teaching role (Assistant Teaching Professor, Junior faculty / Fixed term) f

### Department of Philosophy and Political Science, Fort Lewis College — Visiting Assistant Professor
- **Sonnet main_aos:** Open
- **Opus main_aos:** Metaphysics & Epistemology, Non-Western & Cross-Cultural Philosophy
- **Sonnet position_type:** Visiting / Adjunct / Lecturer (Fixed-Term)
- **Opus position_type:** Visiting / Adjunct / Lecturer (Fixed-Term)
- **Sonnet reasoning:** The AOS is listed as 'Open' with no stated preference in the AOS field or description. The AOC mentions Indigenous Philosophy, Metaphysics, and Philosophy of Mind as preferred competencies, but these 
- **Opus reasoning:** While AOS is listed as 'Open', the preferred qualifications explicitly state 'Area of specialization or competence in metaphysics, philosophy of mind, or indigenous philosophy,' and the AOC lists thes

### Department of Philosophy and Religious Studies, Norwegian University of Science  — Fully funded PhD fellowship (3 years) in Foundations and Philosophy of Entanglem
- **Sonnet main_aos:** Metaphysics & Epistemology, Science, Logic, & Mathematics
- **Opus main_aos:** Metaphysics & Epistemology, Science, Logic, & Mathematics
- **Sonnet position_type:** Other
- **Opus position_type:** Postdoc / Fellowship
- **Sonnet reasoning:** This PhD fellowship focuses on philosophy of physics (quantum entanglement) and metaphysics (fundamental ontology, world structure), clearly spanning both main categories as stated in the AOS field. I
- **Opus reasoning:** The AOS explicitly lists Philosophy of physics, Philosophy of science, Metaphysics, and quantum physics. The project focuses on foundations of quantum theory and metaphysical implications of entanglem

### Department of Philosophy, Purdue University — Visiting Assistant Professor
- **Sonnet main_aos:** Open
- **Opus main_aos:** History of Philosophy, Science, Logic, & Mathematics
- **Sonnet position_type:** Visiting / Adjunct / Lecturer (Fixed-Term)
- **Opus position_type:** Visiting / Adjunct / Lecturer (Fixed-Term)
- **Sonnet reasoning:** The AOS is explicitly 'Open' with teaching competencies (AOC) in Philosophy of Science, History of Philosophy, and Philosophy of AI. Since these are AOC (areas of competence) rather than AOS (areas of
- **Opus reasoning:** Although AOS is listed as 'Open', the posting requires demonstrated ability to teach Philosophy of Science, History of Philosophy, and Philosophy of AI, making these the effective areas of specializat

### School of Historical, Philosophical, and Religious Studies, Arizona State Univer — Director, School of Historical, Philosophical, and Religious Studies
- **Sonnet main_aos:** Open
- **Opus main_aos:** Open
- **Sonnet position_type:** Other
- **Opus position_type:** Tenured / Continuing / Permanent
- **Sonnet reasoning:** This is a School Director position with administrative leadership responsibilities over History, Philosophy, and Religious Studies. While it includes a concurrent tenured Professor appointment, the pr
- **Opus reasoning:** This is a Director position with concurrent tenured Professor appointment. The AOS and AOC are both listed as 'Open' with no stated preferences for any specific philosophical area - the position requi

### Department of Philosophy, University of Alabama — Instructor
- **Sonnet main_aos:** Open
- **Opus main_aos:** Ethics, Science, Logic, & Mathematics
- **Sonnet position_type:** Visiting / Adjunct / Lecturer (Fixed-Term)
- **Opus position_type:** Visiting / Adjunct / Lecturer (Fixed-Term)
- **Sonnet reasoning:** The AOS is explicitly 'Open' with philosophy of medicine listed only as AOC (area of competence, not specialization). Since AOS is genuinely open with no stated preference, this qualifies for the 'Ope
- **Opus reasoning:** The posting lists AOS as Open but specifies AOC in Philosophy of Medicine, with courses including Medical Ethics and Philosophy of Medicine. Philosophy of Medicine is a distinct field from Biomedical 

### Philosophy Program, La Trobe University — Research Officer (Philosophy)
- **Sonnet main_aos:** Metaphysics & Epistemology
- **Opus main_aos:** Open
- **Sonnet position_type:** Postdoc / Fellowship
- **Opus position_type:** Postdoc / Fellowship
- **Sonnet reasoning:** This is a fixed-term research position on an ARC Discovery Project focused on 'Virtual Reality and Knowing What It Is Like,' which clearly falls under epistemology (knowledge) and philosophy of mind (
- **Opus reasoning:** This is a fixed-term Research Officer position on an ARC Discovery Project about virtual reality and phenomenal knowledge, which is a postdoctoral research role. Both AOS and AOC are listed as Open wi

*(9 additional disagreements omitted from this report; see raw JSON for the full list.)*

---

## How to Read This Report

- **High agreement rates** (>90% on main_aos) suggest Sonnet is reliable
  for this corpus — no methodological concern.
- **Lower agreement** on specific categories may indicate either
  taxonomy ambiguity, prompt issues, or genuinely-hard-to-classify jobs.
  Spot-check the disagreement list to identify the cause.
- **If Opus consistently disagrees in one direction** (e.g., almost
  always adds an additional main_aos), consider revising the prompt to
  match Opus's more conservative or more liberal labeling style.

## Change History

New report files are written each QC run with the date in the filename
(`docs/QC_REPORT.md` always reflects the most recent; raw outputs at
`data/qc_opus_*.json` preserve every historical run).

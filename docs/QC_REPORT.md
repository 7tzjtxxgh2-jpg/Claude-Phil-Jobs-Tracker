# Quarterly Opus QC Report

**Generated:** 2026-05-16
**Reference model (live dashboard):** `claude-sonnet-4-5`
**QC model:** `claude-opus-4-5`
**Jobs evaluated:** 191

---

## Purpose

Every ~2 months, the more capable Opus model independently re-classifies
the corpus using the same prompt and taxonomy as the live Sonnet pipeline.
This report compares Opus against the live Sonnet labels to:

1. Quantify how often the two models agree (a sanity check on Sonnet quality)
2. Surface specific jobs where they disagree (for spot-review)
3. Create a defensible audit trail: "we periodically verify with the
   most capable available model"

Sonnet labels remain authoritative on the dashboard. This QC does not
change any live classifications. Raw Opus output is saved to
`data/qc_opus_2026-05-16.json` for full reproducibility.

---

## Agreement Summary

| Field | Agreement rate |
|---|---|
| `main_aos` (exact set match) | **80.6%** (154/191) |
| `position_type` | 90.6% (173/191) |
| `institution_type` | 95.3% (182/191) |

## Per-Main-Category Agreement

"Match" means both models tagged the job with this category.

| Category | Match / Total | Rate |
|---|---|---|
| Ethics | 47 / 53 | 88.7% |
| Social & Political Philosophy | 20 / 28 | 71.4% |
| Value Theory / Aesthetics | 4 / 7 | 57.1% |
| History of Philosophy | 27 / 28 | 96.4% |
| Non-Western & Cross-Cultural Philosophy | 0 / 2 | 0.0% |
| Metaphysics & Epistemology | 25 / 34 | 73.5% |
| Science, Logic, & Mathematics | 54 / 68 | 79.4% |
| Open | 58 / 70 | 82.9% |

## Disagreements (53 jobs)

Jobs where Sonnet's `main_aos` or `position_type` differs from Opus's.
Inspect each manually if needed — Opus output is stored in
`data/qc_opus_2026-05-16.json`.

### Worcester Polytechnic Institute — Visiting Assistant Teaching Professor in Philosophy and Religion
- **Sonnet main_aos:** Ethics, Value Theory / Aesthetics
- **Opus main_aos:** Ethics
- **Sonnet position_type:** Visiting / Adjunct / Lecturer (Fixed-Term)
- **Opus position_type:** Visiting / Adjunct / Lecturer (Fixed-Term)
- **Sonnet reasoning:** This is explicitly a 'Visiting Assistant Teaching Professor' position categorized as 'Junior faculty / Fixed term', making it a temporary teaching-focused role. The AOS is environmental philosophy and
- **Opus reasoning:** The AOS specifies environmental philosophy, which maps to Environmental Ethics. The title 'Visiting Assistant Teaching Professor' with job category 'Junior faculty / Fixed term' indicates a fixed-term

### Department of Philosophy, University College London — Postdoctoral Research Fellow
- **Sonnet main_aos:** History of Philosophy, Metaphysics & Epistemology, Value Theory / Aesthetics
- **Opus main_aos:** Ethics, History of Philosophy, Metaphysics & Epistemology, Social & Political Philosophy, Value Theory / Aesthetics
- **Sonnet position_type:** Postdoc / Fellowship
- **Opus position_type:** Postdoc / Fellowship
- **Sonnet reasoning:** This is a postdoctoral research fellowship at UCL working on a specific ERC-funded research project. The AOS explicitly lists value theory (broadly construed to include ethics, political philosophy, j
- **Opus reasoning:** The AOS explicitly lists value theory (broadly construed to include ethics, political philosophy, jurisprudence, aesthetics, moral psychology), history of philosophy, phenomenology, and philosophy of 

### Department of Philosophy, University of Bristol — PhD in Political and Social Philosophy
- **Sonnet main_aos:** Social & Political Philosophy
- **Opus main_aos:** Social & Political Philosophy
- **Sonnet position_type:** Other
- **Opus position_type:** Postdoc / Fellowship
- **Sonnet reasoning:** This is a funded PhD studentship, which is a graduate student position rather than a faculty or postdoctoral position. Since it doesn't fit the categories of tenure-track, postdoc, visiting/adjunct, o
- **Opus reasoning:** This is a funded PhD studentship (graduate fellowship) in Political and Social Philosophy at the University of Bristol, UK. The AOS explicitly lists Social and Political Philosophy, with interests in 

### Department of Philosophy, Stanford University — Lecturer in Philosophy and COLLEGE (Intro Gen Ed) - 3 yr
- **Sonnet main_aos:** Ethics
- **Opus main_aos:** Ethics, Open
- **Sonnet position_type:** Visiting / Adjunct / Lecturer (Fixed-Term)
- **Opus position_type:** Visiting / Adjunct / Lecturer (Fixed-Term)
- **Sonnet reasoning:** This is a 3-year fixed-term lecturer position focused on teaching introductory general education and ethics courses with no tenure track. Stanford is a major research university, and the position is e
- **Opus reasoning:** The AOS specifies 'Core Philosophy and Ethics' with teaching in ethics and introductory curriculum, indicating a general ethics focus alongside broad introductory philosophy. The position is a 3-year 

### International Centre for Neuroscience and Ethics (CINET) — Call for applications for a pre-doctoral scholarship in Neuroscience and Humanit
- **Sonnet main_aos:** Ethics, Science, Logic, & Mathematics
- **Opus main_aos:** Ethics, Science, Logic, & Mathematics
- **Sonnet position_type:** Other
- **Opus position_type:** Postdoc / Fellowship
- **Sonnet reasoning:** This is a pre-doctoral (graduate) scholarship in neuroscience and humanities at a research center in Spain, which does not fit the standard academic position categories (it's for graduate students, no
- **Opus reasoning:** The position is a pre-doctoral scholarship at a neuroscience and ethics center, focusing on neuroscience and humanities. The AOS clearly indicates neuroethics and cognitive science-related philosophy.

### Department of Historical, Philosophical and Religious Studies, Umeå University,  — Doctoral student in Philosophy, specialization in Ethics in Teacher Education
- **Sonnet main_aos:** Ethics
- **Opus main_aos:** Ethics
- **Sonnet position_type:** Other
- **Opus position_type:** Postdoc / Fellowship
- **Sonnet reasoning:** This is a doctoral student position (PhD student), which does not fit the standard categories of faculty positions, postdocs, or administrative roles. The AOS is ethics in teacher education, which fal
- **Opus reasoning:** This is a doctoral student position (graduate fellowship) focused on Ethics in Teacher Education, which falls under applied ethics. The job category explicitly states 'Graduate fellowship / Fixed term

### Department of Philosophy, Goethe University Frankfurt am Main — Doctoral Researcher
- **Sonnet main_aos:** Ethics
- **Opus main_aos:** Ethics
- **Sonnet position_type:** Other
- **Opus position_type:** Postdoc / Fellowship
- **Sonnet reasoning:** This is a doctoral researcher position (PhD student fellowship) at a German university, which is a graduate-level research position that doesn't fit the standard US academic categories of tenure-track
- **Opus reasoning:** The position is a doctoral researcher (graduate fellowship) with AOS in Ethics or Metaethics and AOC in Metaethics and Normative Ethics. As a fixed-term doctoral/graduate fellowship focused on indepen

### Computer Science, University College London — Lecturer/Associate Professor in Programming Principles, Logic, and Verification 
- **Sonnet main_aos:** Science, Logic, & Mathematics
- **Opus main_aos:** Open
- **Sonnet position_type:** Tenured / Continuing / Permanent
- **Opus position_type:** Tenured / Continuing / Permanent
- **Sonnet reasoning:** This is a permanent faculty position (Lecturer/Associate Professor) at University College London in Computer Science, focused on programming principles, logic, and verification with joint teaching res
- **Opus reasoning:** The posting explicitly states AOS and AOC as 'Open' with no specific philosophical area requirements. The position is listed as 'Senior faculty / Tenured, continuing or permanent' at Lecturer/Associat

### Center for Inquirynot BA-granting — Editor of Free Inquiry Magazine and Executive Director of the Council for Secula
- **Sonnet main_aos:** Open
- **Opus main_aos:** Metaphysics & Epistemology
- **Sonnet position_type:** Other
- **Opus position_type:** Other
- **Sonnet reasoning:** This is an editorial and executive director position at a nonprofit organization, not a faculty position at an academic institution. While it involves philosophical work, it is explicitly non-academic
- **Opus reasoning:** This is a non-academic editorial/executive director position at a nonprofit organization (Center for Inquiry), not a faculty role. The AOS specifies philosophy of religion as preferred, placing it in 

### Division of the Humanities and Social Sciences, California Institute of Technolo — Postdoctoral Scholar Teaching Fellow in the Linde Center for Science, Society, a
- **Sonnet main_aos:** Ethics
- **Opus main_aos:** Ethics, Science, Logic, & Mathematics
- **Sonnet position_type:** Postdoc / Fellowship
- **Opus position_type:** Postdoc / Fellowship
- **Sonnet reasoning:** This is a postdoctoral teaching fellowship position at Caltech's Linde Center. The AOS explicitly lists applied ethics, environmental ethics, and biomedical ethics, making Ethics the primary category 
- **Opus reasoning:** The AOS explicitly lists Applied Ethics, Environmental Ethics, and Biomedical Ethics, placing this in Ethics with relevant subcategories. The AOC in Philosophy of Science adds the Science, Logic, & Ma

### Dpeartment of Philosophy , University of Edinburgh — PhD position in AI Ethics and Philosophy of Science
- **Sonnet main_aos:** Ethics, Science, Logic, & Mathematics
- **Opus main_aos:** Ethics, Science, Logic, & Mathematics
- **Sonnet position_type:** Other
- **Opus position_type:** Postdoc / Fellowship
- **Sonnet reasoning:** This is a PhD position (graduate student fellowship), which does not fit any of the five standard position types as it is neither a faculty position nor a postdoctoral fellowship. The University of Ed
- **Opus reasoning:** The posting explicitly lists AOS as 'Ethics of AI' and 'Philosophy of Science,' mapping to AI, Technology, and Information Ethics and Philosophy of Science subcategories. Though titled 'PhD position,'

### The Department of Historical, Philosophical and Religious Studies, Umeå Universi — PhD position in philosophy (4-year salaried), open to all areas of philosophy
- **Sonnet main_aos:** Open
- **Opus main_aos:** Open
- **Sonnet position_type:** Other
- **Opus position_type:** Postdoc / Fellowship
- **Sonnet reasoning:** This is a PhD student position (graduate fellowship), which does not fit the standard faculty categories of tenure-track, postdoc, visiting, or tenured positions. PhD positions are classified as 'Othe
- **Opus reasoning:** This is a 4-year salaried PhD position (graduate fellowship) in Sweden, explicitly open to all areas of philosophy. The job category is 'Graduate fellowship / Fixed term' and the AOS is listed as 'Ope

### Technion, Israel Institute of Technology — Funded PhD Positions in Philosophy
- **Sonnet main_aos:** History of Philosophy, Metaphysics & Epistemology, Science, Logic, & Mathematics
- **Opus main_aos:** History of Philosophy, Metaphysics & Epistemology, Science, Logic, & Mathematics
- **Sonnet position_type:** Other
- **Opus position_type:** Postdoc / Fellowship
- **Sonnet reasoning:** This is a funded PhD student position, which does not fit any of the five standard categories (not faculty, postdoc, or administrative). The Technion is a research university in Israel, and the AOS cl
- **Opus reasoning:** This is a funded PhD position (graduate fellowship) at a research university in Israel. The AOS explicitly lists philosophy of science (life sciences, cognitive science, pharmacy/medicine), philosophy

### Department of Philosophy, University of Poitiers (France) — PhD Position (3 years) -- Improving collective decisions in expert committees
- **Sonnet main_aos:** Science, Logic, & Mathematics
- **Opus main_aos:** Metaphysics & Epistemology, Science, Logic, & Mathematics
- **Sonnet position_type:** Other
- **Opus position_type:** Postdoc / Fellowship
- **Sonnet reasoning:** This is a PhD student position (graduate fellowship), not a faculty position, postdoc, or other standard academic job category. The AOS clearly focuses on philosophy of science, formal epistemology, a
- **Opus reasoning:** The AOS explicitly lists philosophy of science, formal epistemology, and decision theory. This is a 3-year PhD position (graduate fellowship), which falls under the Postdoc / Fellowship category as a 

### Center for Cyclone Civics , Iowa State University — Post Doctoral Research Associate
- **Sonnet main_aos:** Social & Political Philosophy
- **Opus main_aos:** Non-Western & Cross-Cultural Philosophy, Social & Political Philosophy
- **Sonnet position_type:** Postdoc / Fellowship
- **Opus position_type:** Postdoc / Fellowship
- **Sonnet reasoning:** This is a postdoctoral research position focused on civic education and civic engagement, which falls under philosophy of education and public philosophy within social and political philosophy. Iowa S
- **Opus reasoning:** The AOS specifies Civic Education, Civic Engagement, and Citizenship, which align with Philosophy of Education and Public Philosophy under Social & Political Philosophy. The AOC mentions American Phil

### Seton Hall University — Lecturer in the Core Curriculum
- **Sonnet main_aos:** History of Philosophy
- **Opus main_aos:** History of Philosophy, Metaphysics & Epistemology
- **Sonnet position_type:** Visiting / Adjunct / Lecturer (Fixed-Term)
- **Opus position_type:** Visiting / Adjunct / Lecturer (Fixed-Term)
- **Sonnet reasoning:** This is a fixed-term Lecturer position (explicitly labeled 'Junior faculty / Fixed term') focused on teaching the Catholic Intellectual Tradition, which primarily falls under medieval and Renaissance 
- **Opus reasoning:** The AOS specifies Catholic Intellectual Tradition, which relates to Philosophy of Religion and the historical tradition of Catholic philosophy. The position is a fixed-term Lecturer (Junior faculty / 

### Health Humanities and Bioethics, University of Rochester School of Medicine and  — Assistant, Associate, or Full Professor
- **Sonnet main_aos:** Ethics
- **Opus main_aos:** Ethics, Science, Logic, & Mathematics
- **Sonnet position_type:** Tenure-Track
- **Opus position_type:** Tenure-Track
- **Sonnet reasoning:** This is an open-rank tenure-eligible position at the University of Rochester School of Medicine focused on bioethics with specific areas including ELSI genetics, neuroethics, AI ethics, transplant eth
- **Opus reasoning:** The AOS explicitly lists Bioethics, Neuroethics, AI ethics, ELSI Genetics, Transplant Ethics, and Clinical Ethics, which fall primarily under Ethics subcategories. AI ethics also connects to Philosoph

### Department of Philosophy, University at Buffalo — Postdoctoral Associate (Teaching)
- **Sonnet main_aos:** Science, Logic, & Mathematics, Social & Political Philosophy
- **Opus main_aos:** Metaphysics & Epistemology, Social & Political Philosophy
- **Sonnet position_type:** Postdoc / Fellowship
- **Opus position_type:** Postdoc / Fellowship
- **Sonnet reasoning:** This is a postdoctoral teaching fellowship position at University at Buffalo, explicitly labeled as 'Postdoctoral Associate' and 'Postdoc or similar / Fixed term'. The AOS includes PPE, Social and Pol
- **Opus reasoning:** The AOS explicitly lists PPE, Social and Political Philosophy, and Formal and Social Epistemology. The position is titled 'Postdoctoral Associate' and categorized as 'Postdoc or similar / Fixed term,'

### Department of Philosophy, McMaster University — Bertrand Russell Visiting Professorship
- **Sonnet main_aos:** History of Philosophy, Metaphysics & Epistemology, Science, Logic, & Mathematics
- **Opus main_aos:** History of Philosophy, Science, Logic, & Mathematics
- **Sonnet position_type:** Visiting / Adjunct / Lecturer (Fixed-Term)
- **Opus position_type:** Visiting / Adjunct / Lecturer (Fixed-Term)
- **Sonnet reasoning:** This is a fixed-term Visiting Professorship focused on Bertrand Russell and early analytic philosophy, which spans history of philosophy, logic, mathematics, and core areas like metaphysics and episte
- **Opus reasoning:** The position focuses on Bertrand Russell and early analytic philosophy, which falls under 19th/20th Century Philosophy. Given Russell's foundational work in logic, this also relates to Logic. The job 

### Philosophy, Carnegie Mellon University — Head of Philosophy Department
- **Sonnet main_aos:** Open
- **Opus main_aos:** Open
- **Sonnet position_type:** Other
- **Opus position_type:** Tenured / Continuing / Permanent
- **Sonnet reasoning:** This is a department head position, which is an administrative role. While it may include a faculty component, the primary classification is as a department chair/head, making it 'Other' according to 
- **Opus reasoning:** The posting is for a Department Head position with AOS listed as Open. As a senior faculty leadership role at a research university, this is a tenured/permanent position. Carnegie Mellon is located in

### History and Philosophy , The University of Texas Dallas — Assistant Professor of Philosophy
- **Sonnet main_aos:** History of Philosophy, Non-Western & Cross-Cultural Philosophy
- **Opus main_aos:** History of Philosophy
- **Sonnet position_type:** Tenure-Track
- **Opus position_type:** Tenure-Track
- **Sonnet reasoning:** The position explicitly requires expertise in Early or Late Modern Philosophy (Descartes to Hegel) with special interest in intersections with Non-Western traditions. The posting clearly states 'tenur
- **Opus reasoning:** The AOS explicitly specifies Early or Late Modern Philosophy from Descartes to Hegel, which spans 17th/18th century and into 19th century philosophy. The position is explicitly described as tenure-tra

### University of Texas at San Antonio — Associate or Full Professor, Artificial Intelligence for Education Cluster
- **Sonnet main_aos:** Ethics, Science, Logic, & Mathematics
- **Opus main_aos:** Science, Logic, & Mathematics
- **Sonnet position_type:** Tenured / Continuing / Permanent
- **Opus position_type:** Tenured / Continuing / Permanent
- **Sonnet reasoning:** The position is for Associate or Full Professor, which are tenured ranks. The AOS is Artificial Intelligence, which falls under both Philosophy of Computing/AI and AI Ethics subcategories.
- **Opus reasoning:** The AOS specifies Artificial Intelligence, which maps to Philosophy of Computing / Philosophy of AI. The position is for Associate or Full Professor (senior faculty), indicating a tenured/permanent po

### Research & Training Alliance, University of Toronto – Hebrew University of Jerus — Postdoctoral Fellowships in Practical Philosophy, Normativity, and Law
- **Sonnet main_aos:** Ethics, Social & Political Philosophy
- **Opus main_aos:** Open
- **Sonnet position_type:** Postdoc / Fellowship
- **Opus position_type:** Postdoc / Fellowship
- **Sonnet reasoning:** This is a postdoctoral fellowship position focused on practical philosophy, normativity, and law at two international universities (Toronto and Jerusalem). While the AOS is listed as 'Open', the title
- **Opus reasoning:** The posting explicitly states AOS and AOC as 'Open' with focus on practical philosophy, normativity, and law but no specific area requirements. Position is clearly a postdoctoral fellowship at interna

### The Prindle Institute for Ethics, DePauw University — Manager, Campus Ethics Programs
- **Sonnet main_aos:** Ethics, Social & Political Philosophy
- **Opus main_aos:** Ethics
- **Sonnet position_type:** Other
- **Opus position_type:** Other
- **Sonnet reasoning:** This is a program management position focused on coordinating ethics programming and supervising student internships, which is administrative rather than a faculty teaching or research role. DePauw Un
- **Opus reasoning:** The job category explicitly states 'Administration (non-academic)' and the title is 'Manager, Campus Ethics Programs,' indicating this is an administrative position focused on coordinating ethics prog

### The Center for Practical Ethics, University of Mississippi — Postdoc in the Ethics of AI and Emerging Technologies
- **Sonnet main_aos:** Ethics
- **Opus main_aos:** Ethics, Science, Logic, & Mathematics
- **Sonnet position_type:** Postdoc / Fellowship
- **Opus position_type:** Postdoc / Fellowship
- **Sonnet reasoning:** This is explicitly a postdoctoral research associate position at the Center for Practical Ethics focusing on AI and emerging technologies ethics. The University of Mississippi is a research university
- **Opus reasoning:** The AOS specifies Applied Ethics and Philosophy of Technology, with the title explicitly focusing on Ethics of AI and Emerging Technologies. The position is clearly a postdoctoral research associate a

### Department of Philosophy and Religion, Northeastern University — Assistant Professor/ Associate Professor/ Full Professor
- **Sonnet main_aos:** Ethics
- **Opus main_aos:** Ethics, Science, Logic, & Mathematics
- **Sonnet position_type:** Tenure-Track
- **Opus position_type:** Tenure-Track
- **Sonnet reasoning:** This is an open-rank tenure-track position (explicitly stated as 'T/TT Position' and 'tenure-track Assistant Professor') focused on Ethics and Health, including research ethics, clinical ethics, and p
- **Opus reasoning:** The AOS explicitly mentions Bioethics and Science and Technology Studies, with AOC in Health. The description emphasizes research ethics, clinical ethics, and public health ethics. Position is explici

### Parr Center for Ethics, Philosophy Department, University of North Carolina, Cha — Postdoctoral Fellow, Educating for the Virtues of Attention (EVA)
- **Sonnet main_aos:** Ethics
- **Opus main_aos:** Ethics, Metaphysics & Epistemology
- **Sonnet position_type:** Postdoc / Fellowship
- **Opus position_type:** Postdoc / Fellowship
- **Sonnet reasoning:** This is a postdoctoral fellowship position at UNC Chapel Hill's Parr Center for Ethics, focused on philosophy of attention, intellectual virtue, and character development. The position is explicitly d
- **Opus reasoning:** The posting explicitly seeks expertise in philosophy of attention, intellectual virtue, and character development, which spans virtue ethics and epistemology (intellectual virtues). The position is cl

### The Smith Institute for Political Economy and Philosophy, Chapman University — Postdoctoral Fellowship in the Smith Institute
- **Sonnet main_aos:** Open
- **Opus main_aos:** Open, Social & Political Philosophy
- **Sonnet position_type:** Postdoc / Fellowship
- **Opus position_type:** Postdoc / Fellowship
- **Sonnet reasoning:** This is explicitly a postdoctoral fellowship position at the Smith Institute. The AOS is listed as 'Open' with a preference for PPE-complementary specializations, but no specific requirements, so it q
- **Opus reasoning:** The posting explicitly states AOS is Open but notes a preference for specializations complementary to PPE (Politics, Philosophy, and Economics). The position is clearly a two-year postdoctoral fellows

### Department of History and Philosophy, Kennesaw State University — Chair of the Department of History and Philosophy
- **Sonnet main_aos:** Open
- **Opus main_aos:** Open
- **Sonnet position_type:** Other
- **Opus position_type:** Tenured / Continuing / Permanent
- **Sonnet reasoning:** This is a department chair position that is primarily administrative in nature, with a twelve-month contract focused on leadership responsibilities. While it includes a tenured Professor appointment, 
- **Opus reasoning:** This is a tenured Professor and Chair position with AOS listed as Open. The job category explicitly states 'Senior faculty / Tenured, continuing or permanent' and the description confirms it is a tenu

### Florida International University — Assistant Professor, Associate Professor, Professor
- **Sonnet main_aos:** Ethics, Science, Logic, & Mathematics
- **Opus main_aos:** Ethics
- **Sonnet position_type:** Tenure-Track
- **Opus position_type:** Tenure-Track
- **Sonnet reasoning:** The position is explicitly described as 'Tenure-track or similar' and is open rank (Assistant, Associate, or Professor). The AOS is AI Ethics with AOC in philosophy of science, technology, and data et
- **Opus reasoning:** The AOS explicitly specifies AI Ethics, which maps directly to the AI, Technology, and Information Ethics subcategory under Ethics. The position is open rank (Assistant/Associate/Professor) but listed

### School of Civic Leadership, University of Texas at Austin — Great Books (Assistant Professor)
- **Sonnet main_aos:** History of Philosophy, Open, Social & Political Philosophy
- **Opus main_aos:** History of Philosophy, Social & Political Philosophy, Value Theory / Aesthetics
- **Sonnet position_type:** Tenure-Track
- **Opus position_type:** Tenure-Track
- **Sonnet reasoning:** This is explicitly a tenure-track assistant professor position at UT Austin. The AOS encompasses political thought, philosophy, literature, religious studies, and liberal arts broadly for a Great Book
- **Opus reasoning:** The position is explicitly tenure-track at the assistant professor level. The AOS mentions political thought, philosophy, literature, and religious studies within a Great Books curriculum, suggesting 

### Department of Philosophy, CPNSS, London School of Economics — Research Officer
- **Sonnet main_aos:** Ethics, Science, Logic, & Mathematics, Social & Political Philosophy
- **Opus main_aos:** Science, Logic, & Mathematics, Social & Political Philosophy
- **Sonnet position_type:** Postdoc / Fellowship
- **Opus position_type:** Postdoc / Fellowship
- **Sonnet reasoning:** This is a postdoctoral research position (Research Officer) on a specific funded project about AI and worker autonomy. The job category explicitly states 'Postdoc or similar / Fixed term' and the desc
- **Opus reasoning:** The AOS explicitly lists Philosophy of AI and Philosophy of Social Science (under Science, Logic, & Mathematics) and Social and Political Philosophy. The position is clearly a postdoctoral research ro

### Law School, King's College London — YTL Early Career Research Fellow
- **Sonnet main_aos:** Social & Political Philosophy
- **Opus main_aos:** Ethics, Social & Political Philosophy
- **Sonnet position_type:** Postdoc / Fellowship
- **Opus position_type:** Postdoc / Fellowship
- **Sonnet reasoning:** This is a 12-month early career research fellowship at King's College London focused on politics, philosophy and law, clearly fitting the postdoc/fellowship category. The AOS explicitly mentions PPE a
- **Opus reasoning:** The AOS specifies 'Politics, Philosophy and Law,' which maps to Social & Political Philosophy (particularly Philosophy of Law and PPE). This is an Early Career Research Fellowship requiring a PhD with

### Department of Philosophy and Institute for Logic, Language and Computation, Univ — Postdoctoral Researcher in Philosophical Logic (Propositions)
- **Sonnet main_aos:** Science, Logic, & Mathematics
- **Opus main_aos:** Metaphysics & Epistemology, Science, Logic, & Mathematics
- **Sonnet position_type:** Postdoc / Fellowship
- **Opus position_type:** Postdoc / Fellowship
- **Sonnet reasoning:** This is a three-year postdoctoral researcher position in philosophical logic at the University of Amsterdam, funded by an ERC Advanced Grant. The AOS is explicitly philosophical logic with focus on pr
- **Opus reasoning:** The AOS is explicitly Philosophical Logic, which maps to Logic. The project focuses on propositional talk and intensionality, which involves philosophy of language and semantics. The position is clear

### Department of Philosophy and Institute for Logic, Language and Computation, Univ — Two PhD positions in Philosophical Logic
- **Sonnet main_aos:** Science, Logic, & Mathematics
- **Opus main_aos:** Science, Logic, & Mathematics
- **Sonnet position_type:** Other
- **Opus position_type:** Postdoc / Fellowship
- **Sonnet reasoning:** This is a PhD student position (graduate fellowship) in philosophical logic, which does not fit the standard faculty categories of tenure-track, postdoc, visiting, or tenured positions. PhD positions 
- **Opus reasoning:** The AOS is explicitly Philosophical Logic, which falls under Logic in the Science, Logic, & Mathematics category. The position is a four-year PhD fellowship funded by an ERC grant, which qualifies as 

### University of California San Diego — Lecturer in Political Science
- **Sonnet main_aos:** Open
- **Opus main_aos:** Social & Political Philosophy
- **Sonnet position_type:** Visiting / Adjunct / Lecturer (Fixed-Term)
- **Opus position_type:** Visiting / Adjunct / Lecturer (Fixed-Term)
- **Sonnet reasoning:** This is a fixed-term Lecturer position in Political Science (not Philosophy) at UC San Diego. The job category explicitly states 'Junior faculty / Fixed term' and the title is Lecturer, which is a tem
- **Opus reasoning:** The position is a Lecturer in Political Science at UC San Diego, a fixed-term teaching position as indicated by the 'Junior faculty / Fixed term' job category. The AOS is Political Science, which maps

### Advanced Institute of Humanities and Social Sciences, University of Electronic S — Tenure-Track Associate Professor/ Tenured Associate Professor/ Professor
- **Sonnet main_aos:** Ethics, Science, Logic, & Mathematics
- **Opus main_aos:** Ethics, History of Philosophy, Open, Science, Logic, & Mathematics
- **Sonnet position_type:** Tenure-Track
- **Opus position_type:** Tenure-Track
- **Sonnet reasoning:** The posting lists multiple rank options including tenure-track associate professor, but the job category explicitly states 'Tenure-track or similar' and includes tenure-track positions. The AOS prefer
- **Opus reasoning:** The posting explicitly lists preferences for Applied Ethics (Bioethics, AI Ethics), Philosophy of Logic, Philosophy of Science, and History of Science and Technology, while stating AOS is 'Open.' The 

### School of Historical and Philosophical Studies, University of Melbourne — Two funded PhD Positions
- **Sonnet main_aos:** Metaphysics & Epistemology, Science, Logic, & Mathematics
- **Opus main_aos:** Metaphysics & Epistemology, Science, Logic, & Mathematics
- **Sonnet position_type:** Other
- **Opus position_type:** Postdoc / Fellowship
- **Sonnet reasoning:** These are funded PhD scholarship positions for graduate students, not faculty or postdoctoral positions. The University of Melbourne is located in Australia.
- **Opus reasoning:** This is a funded PhD scholarship (graduate fellowship) at the University of Melbourne in Australia. The AOS explicitly lists Metaphysics, Philosophy of Science, and Philosophy of AI, with the descript

### School of Civic Leadership, University of Texas at Austin — Great Books (Associate/Full Professor)
- **Sonnet main_aos:** History of Philosophy, Open, Social & Political Philosophy
- **Opus main_aos:** History of Philosophy, Social & Political Philosophy, Value Theory / Aesthetics
- **Sonnet position_type:** Tenure-Track
- **Opus position_type:** Tenured / Continuing / Permanent
- **Sonnet reasoning:** This is a tenure-track position at associate or full professor level at UT Austin. The AOS encompasses political thought, philosophy, literature, religious studies, and liberal arts broadly, with a fo
- **Opus reasoning:** The position seeks expertise in political thought, philosophy, literature, and liberal arts broadly for a Great Books program, suggesting History of Philosophy, Social & Political Philosophy, and Valu

### Philosophy, CNRS, Archives Poincaré — Doctoral position, M/F, Philosophy of Science, Nancy, France. Explanatory progre
- **Sonnet main_aos:** Science, Logic, & Mathematics
- **Opus main_aos:** Science, Logic, & Mathematics
- **Sonnet position_type:** Other
- **Opus position_type:** Postdoc / Fellowship
- **Sonnet reasoning:** This is a doctoral/PhD student position at CNRS in France, which does not fit the standard categories of postdoc, tenure-track, or teaching positions. The AOS focuses on philosophy of science with emp
- **Opus reasoning:** This is a doctoral fellowship position at CNRS in France focused on philosophy of science, specifically concerning explanatory progress in mathematical/mathematized sciences with examples preferably f

### Department of Philosophy, The Ohio State University — Post Doctoral Scholar - AI in Arts & Humanities
- **Sonnet main_aos:** Ethics
- **Opus main_aos:** Ethics, Science, Logic, & Mathematics
- **Sonnet position_type:** Postdoc / Fellowship
- **Opus position_type:** Postdoc / Fellowship
- **Sonnet reasoning:** This is a two-year fixed-term postdoctoral position focused on AI and ethics research. The AOS explicitly states 'Philosophy and AI Ethics,' which clearly falls under AI, Technology, and Information E
- **Opus reasoning:** The AOS explicitly specifies 'Philosophy and AI Ethics,' which maps to AI, Technology, and Information Ethics under Ethics and Philosophy of Computing / Philosophy of AI under Science, Logic, & Mathem

### School of Philos Anthro & Film Studies, University of St. Andrews — AR3263
- **Sonnet main_aos:** Open
- **Opus main_aos:** Metaphysics & Epistemology
- **Sonnet position_type:** Postdoc / Fellowship
- **Opus position_type:** Postdoc / Fellowship
- **Sonnet reasoning:** This is a fixed-term postdoctoral research fellowship position at the University of St. Andrews in Scotland, working on an EPSRC-funded research project. The AOS is listed as Open, indicating no speci
- **Opus reasoning:** Although the AOS is listed as Open, the project description clearly focuses on metaphysical questions about unity, wholes, and composition (working with Aaron Cotnoir, known for work in mereology). Th

### Philosophy, Politics and Economics Program, University of Pennsylvania — Postdoctoral Fellowship in Philosophy, Politics and Economics
- **Sonnet main_aos:** Science, Logic, & Mathematics, Social & Political Philosophy
- **Opus main_aos:** Open
- **Sonnet position_type:** Postdoc / Fellowship
- **Opus position_type:** Postdoc / Fellowship
- **Sonnet reasoning:** This is a postdoctoral fellowship in PPE at University of Pennsylvania. While AOS is listed as Open, the AOC and description clearly indicate focus on political philosophy, philosophy of social scienc
- **Opus reasoning:** The AOS is explicitly listed as 'Open,' though the AOC and description indicate interest in PPE-related topics including philosophy of social science and political philosophy. The position is clearly 

### Department of Philosophy, Virginia Tech — Visiting Assistant Professor
- **Sonnet main_aos:** Value Theory / Aesthetics
- **Opus main_aos:** Ethics, Social & Political Philosophy, Value Theory / Aesthetics
- **Sonnet position_type:** Visiting / Adjunct / Lecturer (Fixed-Term)
- **Opus position_type:** Visiting / Adjunct / Lecturer (Fixed-Term)
- **Sonnet reasoning:** This is explicitly a Visiting Assistant Professor position with fixed-term job category. The AOS is value theory broadly construed, which falls under the Value Theory / Aesthetics main category.
- **Opus reasoning:** The AOS is explicitly 'Value Theory (broadly construed)' which maps directly to the Value Theory / Aesthetics category, though value theory broadly construed can also encompass ethics and social/polit

### Minnesota Center for Philosophy of Science, University of Minnestoa — Post-Doctoral Associate
- **Sonnet main_aos:** Open
- **Opus main_aos:** Science, Logic, & Mathematics
- **Sonnet position_type:** Postdoc / Fellowship
- **Opus position_type:** Postdoc / Fellowship
- **Sonnet reasoning:** This is a three-year postdoctoral associate position at the Minnesota Center for Philosophy of Science, clearly a postdoc fellowship. The AOS is listed as Open with no specific area restrictions menti
- **Opus reasoning:** Although the AOS is listed as Open, the position is at the Minnesota Center for Philosophy of Science and is associated with the 'Consortium for Advancing a Science of Purpose' project focused on biol

### Department of Philosophy, University of Exeter — Postdoctoral Research Associate/Fellow
- **Sonnet main_aos:** Metaphysics & Epistemology, Science, Logic, & Mathematics
- **Opus main_aos:** Open
- **Sonnet position_type:** Postdoc / Fellowship
- **Opus position_type:** Postdoc / Fellowship
- **Sonnet reasoning:** This is a postdoctoral research position on a Leverhulme-funded project about autonomous AI scientists and agents that can err, clearly involving philosophy of AI and epistemology. The University of E
- **Opus reasoning:** The posting explicitly lists AOS as 'Open' with no specific philosophical area requirements. The position is clearly a Postdoctoral Research Associate/Fellow on a Leverhulme-funded project about auton

### Department of Philosophy, University of Tartu — 3 Fully-Funded Junior Research Fellowships (Doctoral positions)
- **Sonnet main_aos:** Open
- **Opus main_aos:** Open
- **Sonnet position_type:** Other
- **Opus position_type:** Postdoc / Fellowship
- **Sonnet reasoning:** These are doctoral student positions (junior research fellowships with student status) at the University of Tartu in Estonia. Doctoral positions do not fit the standard categories of tenure-track, pos
- **Opus reasoning:** This is a doctoral/junior research fellowship position with open AOS/AOC requirements. Though it involves student status, it is a funded research fellowship position at the University of Tartu in Esto

### Discipline of Philosophy, UWA India — Assistant Professor / Senior Assistant Professor - Philosophy
- **Sonnet main_aos:** Open
- **Opus main_aos:** Open
- **Sonnet position_type:** Tenured / Continuing / Permanent
- **Opus position_type:** Tenure-Track
- **Sonnet reasoning:** The position is explicitly described as 'on a tenurable basis' and listed under 'Tenured, continuing or permanent' job category, indicating a permanent track position rather than entry-level tenure-tr
- **Opus reasoning:** The posting explicitly states AOS and AOC as 'Open' with no specific requirements. The position is described as 'tenurable basis' (tenure-track) at Assistant/Senior Assistant Professor level. UWA Indi

### Centre Gilles Gaston Granger, Université Aix-Marseille — PhD Position (3+1 years) in Philosophy of Physics
- **Sonnet main_aos:** Metaphysics & Epistemology, Science, Logic, & Mathematics
- **Opus main_aos:** Metaphysics & Epistemology, Science, Logic, & Mathematics
- **Sonnet position_type:** Other
- **Opus position_type:** Postdoc / Fellowship
- **Sonnet reasoning:** This is a PhD student position (graduate fellowship), not a faculty position, postdoc, or other standard academic employment category. The AOS clearly specifies philosophy of physics, metaphysics, and
- **Opus reasoning:** The AOS explicitly lists Philosophy of Physics, Metaphysics, and Philosophy of Science. This is a PhD position (graduate fellowship) at a French university, which falls under Postdoc / Fellowship as a

### Department of Philosophy, Universität des Saarlandes — Professorship "Ethics of AI“
- **Sonnet main_aos:** Ethics
- **Opus main_aos:** Ethics, Science, Logic, & Mathematics
- **Sonnet position_type:** Tenure-Track
- **Opus position_type:** Tenure-Track
- **Sonnet reasoning:** The position focuses specifically on Ethics of AI, which falls under the Ethics category. Despite starting at associate professor level, it is explicitly described as 'tenure-tracked' in the descripti
- **Opus reasoning:** The position explicitly focuses on 'Ethics of AI' with AOS in 'Philosophy and Ethics of AI,' clearly fitting AI/Technology Ethics and Philosophy of AI subcategories. The posting states it is 'tenure-t

*(3 additional disagreements omitted from this report; see raw JSON for the full list.)*

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

"""Area-of-specialization taxonomy, shared with the PhilJobs tracker.

Copied verbatim from Claude-Phil-Jobs-Tracker/scraper.py (taxonomy version
2026-07-20-sonnet-v5) so that conference data and job-market data can be
sliced along identical axes. Keep the two in sync deliberately: if the jobs
taxonomy is revised, mirror the change here and bump TAXONOMY_VERSION, or
cross-dashboard comparisons silently stop being apples-to-apples.

Note the division of labour (see plan §5): this taxonomy drives faceting,
aggregate views and cross-dashboard comparison. It does NOT drive relevance
ranking -- even the detail categories are too coarse to tell an AI-alignment
workshop from a business-ethics conference. Ranking is semantic matching
against the research profile.
"""

MAIN_AOS_CATEGORIES = [
    "Ethics",
    "Social & Political Philosophy",
    "Value Theory / Aesthetics",
    "History of Philosophy",
    "Non-Western & Cross-Cultural Philosophy",
    "Metaphysics & Epistemology",
    "Science, Logic, & Mathematics",
    "Open",
]

DETAIL_AOS = {
    "Ethics": [
        "Meta-Ethics", "Normative Ethics", "Virtue Ethics",
        "Feminist Ethics",
        "Biomedical Ethics / Bioethics",
        "Neuroethics", "AI, Technology, and Information Ethics",
        "Environmental Ethics", "Animal Ethics", "Food and Agricultural Ethics",
        "Business Ethics", "Ethics of Population, Future Generations, and Global Justice",
        "Ethics (General / Applied Ethics, Broadly Construed)",
    ],
    "Social & Political Philosophy": [
        "Social and Political Philosophy (General / Political Theory)",
        "Philosophy of Law", "Philosophy of Race", "Philosophy of Gender",
        "Philosophy of Disability",
        "Feminist Philosophy", "Philosophy of Sexuality and Queer Theory",
        "PPE (Politics, Philosophy, and Economics)", "Philosophy of Education",
        "Public Philosophy",
    ],
    "Value Theory / Aesthetics": [
        "Aesthetics (General)", "Philosophy of Art", "Philosophy of Music",
        "Philosophy of Film and Media", "Philosophy of Literature",
        "Value Theory / Axiology", "Value Theory / Aesthetics (General)",
    ],
    "History of Philosophy": [
        "Ancient Greek and Roman Philosophy", "Medieval and Renaissance Philosophy",
        "Early Modern Philosophy (17th/18th Century)", "19th/20th Century Philosophy",
        "American Philosophy", "Continental Philosophy", "Phenomenology",
        "History of Philosophy (General)",
    ],
    "Non-Western & Cross-Cultural Philosophy": [
        "Asian Philosophy", "African/Africana Philosophy",
        "Arabic and Islamic Philosophy", "Latin American Philosophy",
        "Native American / Indigenous Philosophy",
        "Comparative Philosophy / Cross-Cultural", "Non-Western Philosophy (General)",
    ],
    "Metaphysics & Epistemology": [
        "Metaphysics", "Epistemology", "Philosophy of Mind",
        "Philosophy of Language", "Philosophy of Action", "Philosophy of Religion",
        "Metaphysics & Epistemology (General)",
    ],
    "Science, Logic, & Mathematics": [
        "Philosophy of Science (General)", "Philosophy of Biology",
        "Philosophy of Physics", "Philosophy of Cognitive Science",
        "Philosophy of Computing / Philosophy of AI", "Logic",
        "Philosophy of Mathematics", "Philosophy of Social Science",
        "Decision Theory", "Science, Logic, & Mathematics (General)",
    ],
    "Open": [],
}

# Mirrors the jobs repo's taxonomy version. Bump only in lockstep with it.
TAXONOMY_VERSION = "2026-07-20-sonnet-v5"

MAIN_AOS_SET = set(MAIN_AOS_CATEGORIES)

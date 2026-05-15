#!/usr/bin/env python3
"""
PhilJobs Comprehensive Market Analytics Dashboard
Tracks new job postings, job types, locations, and institution types.
Uses Claude API (Haiku) for intelligent AOS classification.
"""

import os
import json
import time
import re
import csv
import hashlib
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from pathlib import Path
from collections import defaultdict

# US States for mapping
US_STATES = {
    'Alabama': 'AL', 'Alaska': 'AK', 'Arizona': 'AZ', 'Arkansas': 'AR', 'California': 'CA',
    'Colorado': 'CO', 'Connecticut': 'CT', 'Delaware': 'DE', 'Florida': 'FL', 'Georgia': 'GA',
    'Hawaii': 'HI', 'Idaho': 'ID', 'Illinois': 'IL', 'Indiana': 'IN', 'Iowa': 'IA',
    'Kansas': 'KS', 'Kentucky': 'KY', 'Louisiana': 'LA', 'Maine': 'ME', 'Maryland': 'MD',
    'Massachusetts': 'MA', 'Michigan': 'MI', 'Minnesota': 'MN', 'Mississippi': 'MS',
    'Missouri': 'MO', 'Montana': 'MT', 'Nebraska': 'NE', 'Nevada': 'NV', 'New Hampshire': 'NH',
    'New Jersey': 'NJ', 'New Mexico': 'NM', 'New York': 'NY', 'North Carolina': 'NC',
    'North Dakota': 'ND', 'Ohio': 'OH', 'Oklahoma': 'OK', 'Oregon': 'OR', 'Pennsylvania': 'PA',
    'Rhode Island': 'RI', 'South Carolina': 'SC', 'South Dakota': 'SD', 'Tennessee': 'TN',
    'Texas': 'TX', 'Utah': 'UT', 'Vermont': 'VT', 'Virginia': 'VA', 'Washington': 'WA',
    'West Virginia': 'WV', 'Wisconsin': 'WI', 'Wyoming': 'WY',
    'District of Columbia': 'DC', 'Washington DC': 'DC', 'Washington, DC': 'DC', 'Washington D.C.': 'DC'
}

# West Coast cities for detailed view
WEST_COAST_CITIES = {
    'Berkeley': {'lat': 37.8715, 'lon': -122.2730, 'state': 'CA'},
    'Stanford': {'lat': 37.4275, 'lon': -122.1697, 'state': 'CA'},
    'San Francisco': {'lat': 37.7749, 'lon': -122.4194, 'state': 'CA'},
    'Oakland': {'lat': 37.8044, 'lon': -122.2712, 'state': 'CA'},
    'San Jose': {'lat': 37.3382, 'lon': -121.8863, 'state': 'CA'},
    'Santa Cruz': {'lat': 36.9741, 'lon': -122.0308, 'state': 'CA'},
    'Davis': {'lat': 38.5449, 'lon': -121.7405, 'state': 'CA'},
    'Los Angeles': {'lat': 34.0522, 'lon': -118.2437, 'state': 'CA'},
    'San Diego': {'lat': 32.7157, 'lon': -117.1611, 'state': 'CA'},
    'Irvine': {'lat': 33.6846, 'lon': -117.8265, 'state': 'CA'},
    'Claremont': {'lat': 34.0967, 'lon': -117.7198, 'state': 'CA'},
    'Riverside': {'lat': 33.9533, 'lon': -117.3962, 'state': 'CA'},
    'Seattle': {'lat': 47.6062, 'lon': -122.3321, 'state': 'WA'},
    'Portland': {'lat': 45.5152, 'lon': -122.6784, 'state': 'OR'},
    'Eugene': {'lat': 44.0521, 'lon': -123.0868, 'state': 'OR'},
    'Tacoma': {'lat': 47.2529, 'lon': -122.4443, 'state': 'WA'},
    'Olympia': {'lat': 47.0379, 'lon': -122.9007, 'state': 'WA'},
}

# West Coast Metro Areas — maps individual cities to their metro grouping.
# Used by the West Coast Spotlight chart for cumulative AOS-by-metro breakdowns.
# Based loosely on OMB Combined Statistical Areas; Davis is grouped with SF Bay
# Area (academically) rather than Sacramento (geographically) per user pref.
WEST_COAST_METROS = {
    # San Francisco Bay Area
    'San Francisco': 'SF Bay Area', 'Oakland': 'SF Bay Area', 'Berkeley': 'SF Bay Area',
    'Stanford': 'SF Bay Area', 'Palo Alto': 'SF Bay Area', 'San Jose': 'SF Bay Area',
    'Santa Clara': 'SF Bay Area', 'Santa Cruz': 'SF Bay Area', 'San Mateo': 'SF Bay Area',
    'Mountain View': 'SF Bay Area', 'Davis': 'SF Bay Area', 'Hayward': 'SF Bay Area',
    'Fremont': 'SF Bay Area', 'Redwood City': 'SF Bay Area', 'San Rafael': 'SF Bay Area',
    'Moraga': 'SF Bay Area', 'Sonoma': 'SF Bay Area', 'Napa': 'SF Bay Area',
    # Greater Los Angeles (includes Inland Empire & Orange County)
    'Los Angeles': 'Greater Los Angeles', 'Long Beach': 'Greater Los Angeles',
    'Pasadena': 'Greater Los Angeles', 'Claremont': 'Greater Los Angeles',
    'Irvine': 'Greater Los Angeles', 'Riverside': 'Greater Los Angeles',
    'San Bernardino': 'Greater Los Angeles', 'Anaheim': 'Greater Los Angeles',
    'Orange': 'Greater Los Angeles', 'Santa Ana': 'Greater Los Angeles',
    'Fullerton': 'Greater Los Angeles', 'Northridge': 'Greater Los Angeles',
    'Malibu': 'Greater Los Angeles', 'Santa Monica': 'Greater Los Angeles',
    'Westwood': 'Greater Los Angeles', 'Pomona': 'Greater Los Angeles',
    'Redlands': 'Greater Los Angeles', 'Glendale': 'Greater Los Angeles',
    'Burbank': 'Greater Los Angeles', 'Thousand Oaks': 'Greater Los Angeles',
    'Whittier': 'Greater Los Angeles',
    # San Diego
    'San Diego': 'San Diego', 'La Jolla': 'San Diego', 'Carlsbad': 'San Diego',
    'Oceanside': 'San Diego', 'Escondido': 'San Diego', 'Chula Vista': 'San Diego',
    # Sacramento
    'Sacramento': 'Sacramento', 'Roseville': 'Sacramento',
    # Seattle-Tacoma
    'Seattle': 'Seattle-Tacoma', 'Tacoma': 'Seattle-Tacoma', 'Bellevue': 'Seattle-Tacoma',
    'Everett': 'Seattle-Tacoma', 'Olympia': 'Seattle-Tacoma', 'Bellingham': 'Seattle-Tacoma',
    # Portland
    'Portland': 'Portland', 'Beaverton': 'Portland', 'Hillsboro': 'Portland',
    'Salem': 'Portland', 'Vancouver': 'Portland',
}

# For West Coast cities not in WEST_COAST_METROS, group by state.
WEST_COAST_FALLBACK_METRO = {
    'CA': 'Other California',
    'OR': 'Other Oregon',
    'WA': 'Other Washington',
}


def get_west_coast_metro(city, state):
    """Map a (city, state) tuple to its West Coast metro area. Returns None if not on West Coast."""
    if state not in WEST_COAST_FALLBACK_METRO:
        return None
    if not city:
        return WEST_COAST_FALLBACK_METRO[state]
    city_lower = city.lower().strip()
    # Try exact match first
    for known_city, metro in WEST_COAST_METROS.items():
        if known_city.lower() == city_lower:
            return metro
    # Then substring match (handles "San Francisco, CA" or "South San Francisco")
    for known_city, metro in WEST_COAST_METROS.items():
        if known_city.lower() in city_lower:
            return metro
    return WEST_COAST_FALLBACK_METRO[state]


US_REGIONS = {
    'West': ['CA', 'OR', 'WA', 'AK', 'HI', 'NV', 'ID', 'MT', 'WY', 'UT', 'CO', 'AZ', 'NM'],
    'Northeast': ['ME', 'NH', 'VT', 'MA', 'RI', 'CT', 'NY', 'NJ', 'PA', 'DC'],
    'South': ['DE', 'MD', 'VA', 'WV', 'NC', 'SC', 'GA', 'FL', 'KY', 'TN', 'AL', 'MS', 'AR', 'LA', 'OK', 'TX'],
    'Midwest': ['OH', 'IN', 'IL', 'MI', 'WI', 'MN', 'IA', 'MO', 'ND', 'SD', 'NE', 'KS'],
}

INTL_REGIONS = {
    'Europe': [
        'United Kingdom', 'Germany', 'France', 'Netherlands', 'Belgium', 'Switzerland',
        'Austria', 'Sweden', 'Norway', 'Denmark', 'Finland', 'Italy', 'Spain', 'Portugal',
        'Ireland', 'Czech Republic', 'Poland', 'Hungary', 'Greece', 'Romania', 'Russia',
        'Ukraine', 'Slovakia', 'Slovenia', 'Croatia', 'Serbia', 'Estonia', 'Latvia',
        'Lithuania', 'Luxembourg', 'Malta', 'Iceland',
    ],
    'Canada': ['Canada'],
    'Asia-Pacific': [
        'Australia', 'New Zealand', 'Japan', 'Singapore', 'South Korea', 'China',
        'Hong Kong', 'Taiwan', 'India', 'Thailand', 'Malaysia', 'Philippines',
        'Indonesia', 'Vietnam', 'Pakistan',
    ],
    'Latin America': [
        'Mexico', 'Brazil', 'Argentina', 'Chile', 'Colombia', 'Peru', 'Venezuela',
        'Ecuador', 'Guatemala', 'Cuba', 'Bolivia', 'Haiti', 'Dominican Republic',
        'Honduras', 'Paraguay', 'El Salvador', 'Nicaragua', 'Costa Rica', 'Panama',
        'Puerto Rico', 'Uruguay',
    ],
    'Middle East & Africa': [
        'Israel', 'United Arab Emirates', 'UAE', 'Saudi Arabia', 'Qatar', 'Turkey',
        'Jordan', 'Lebanon', 'Kuwait', 'Bahrain', 'Oman', 'South Africa', 'Egypt',
        'Nigeria', 'Kenya', 'Ghana', 'Ethiopia', 'Morocco', 'Tunisia',
    ],
}

COUNTRY_NUMERIC = {
    'United Kingdom': '826', 'Germany': '276', 'France': '250', 'Netherlands': '528',
    'Belgium': '056', 'Switzerland': '756', 'Austria': '040', 'Sweden': '752',
    'Norway': '578', 'Denmark': '208', 'Finland': '246', 'Italy': '380', 'Spain': '724',
    'Portugal': '620', 'Ireland': '372', 'Czech Republic': '203', 'Poland': '616',
    'Hungary': '348', 'Greece': '300', 'Romania': '642', 'Russia': '643',
    'Ukraine': '804', 'Slovakia': '703', 'Slovenia': '705', 'Croatia': '191',
    'Serbia': '688', 'Estonia': '233', 'Latvia': '428', 'Lithuania': '440',
    'Luxembourg': '442', 'Malta': '470', 'Iceland': '352',
    'Canada': '124',
    'Mexico': '484', 'Brazil': '076', 'Argentina': '032', 'Chile': '152',
    'Colombia': '170', 'Peru': '604', 'Venezuela': '862', 'Ecuador': '218',
    'Guatemala': '320', 'Cuba': '192', 'Bolivia': '068', 'Haiti': '332',
    'Dominican Republic': '214', 'Honduras': '340', 'Paraguay': '600',
    'El Salvador': '222', 'Nicaragua': '558', 'Costa Rica': '188',
    'Panama': '591', 'Uruguay': '858',
    'Australia': '036', 'New Zealand': '554', 'Japan': '392', 'Singapore': '702',
    'South Korea': '410', 'China': '156', 'Hong Kong': '344', 'Taiwan': '158',
    'India': '356', 'Thailand': '764', 'Malaysia': '458', 'Philippines': '608',
    'Indonesia': '360', 'Vietnam': '704', 'Pakistan': '586',
    'Israel': '376', 'Turkey': '792', 'Jordan': '400', 'Lebanon': '422',
    'Kuwait': '414', 'Bahrain': '048', 'Oman': '512',
    'United Arab Emirates': '784', 'UAE': '784', 'Saudi Arabia': '682', 'Qatar': '634',
    'South Africa': '710', 'Egypt': '818', 'Nigeria': '566', 'Kenya': '404',
    'Ghana': '288', 'Ethiopia': '231', 'Morocco': '504', 'Tunisia': '788',
}

# ── New Taxonomy ────────────────────────────────────────────────────────────

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

# Bump this when DETAIL_AOS changes. The scraper detects a version mismatch
# and forces re-classification of all stored jobs under the new taxonomy.
# Prior classifications get preserved on each job under `classification_v1`
# (or `classification_v<N>`) so we can audit how labels shifted.
TAXONOMY_VERSION = "2026-05-16"

CROSS_CUTTING_AREAS = [
    "Feminist Philosophy",
    "Philosophy of Race",
    "Philosophy of Gender",
    "Philosophy of Law",
]

MAIN_AOS_COLORS = {
    "Ethics": "#ef4444",
    "Social & Political Philosophy": "#3b82f6",
    "Value Theory / Aesthetics": "#06b6d4",
    "History of Philosophy": "#8b5cf6",
    "Non-Western & Cross-Cultural Philosophy": "#ec4899",
    "Metaphysics & Epistemology": "#10b981",
    "Science, Logic, & Mathematics": "#f59e0b",
    "Open": "#6b7280",
}

POSITION_TYPES = [
    "Tenure-Track",
    "Postdoc / Fellowship",
    "Visiting / Adjunct / Lecturer (Fixed-Term)",
    "Tenured / Continuing / Permanent",
    "Other",
]

# Stopwords for the Keyword Explorer description-text search. Words that appear
# in nearly every philosophy job description ("philosophy", "professor", etc.)
# get filtered out by a corpus-frequency check at build time; this list handles
# generic English noise.
KEYWORD_STOPWORDS = set("""
about above after again against all also although among and another any are around as
because been before being below both but came come could doing during each either
every few from further had has have having here hers herself him himself his how
into itself just like make many may might more most much must never new now off
once only other our ours ourselves out over own people please pleas same shall
should some such take than that the their theirs them themselves then there these
they this those through too under unt until upon used using very was way well were
what when where which while who whom whose why will with within without would year
years your yours yourself yourselves you youre weve theyre theyve wont wouldnt
position positions university department job apply application applications applicant
applicants candidate candidates required preferred include including encourage encouraged
must will please send submit letter cover review begin will should review reviews
who can have any questions any letter writing also include they each other position
the are this for and our but with all you have can will any our its
academic college institution school faculty professor professors instructor lecturer
hire hiring opportunity employer employment equal qualified qualifications experience
seeking seek invite invites invited search appointment full part time work works working
salary range commensurate competitive benefits package complete completed information
contact email phone office address mail materials material reference references provide
provided support supports supported program programs offering offers offer accept accepts
accepted appointed available beginning starts start august september fall spring summer
course courses teach teaches teaching graduate undergraduate level levels load loads
service committee committees diversity inclusion inclusive welcomes welcome valuing values
ph dissertation degree academic year evaluation evaluations performance based duties
responsibilities responsibility requirement requirements aim aims must minimum maximum
ensure ensures ensured rank professorial tenure track preferred area areas successful
candidates candidate must following provide statement statements writing sample samples
detail details detailed details classes class effective effectively related similar
broadly broad scholarly scholarship recognized national international community communities
field fields university universities student students department departments
""".split())

POSITION_TYPE_COLORS = {
    "Tenure-Track": "#10b981",
    "Postdoc / Fellowship": "#3b82f6",
    "Visiting / Adjunct / Lecturer (Fixed-Term)": "#f59e0b",
    "Tenured / Continuing / Permanent": "#8b5cf6",
    "Other": "#6b7280",
}

# Map old Claude-assigned job_type labels → new position_type labels
JOB_TYPE_MIGRATION = {
    "Tenure-track": "Tenure-Track",
    "Postdoc": "Postdoc / Fellowship",
    "Adjunct/Visiting": "Visiting / Adjunct / Lecturer (Fixed-Term)",
    "Tenured": "Tenured / Continuing / Permanent",
    "Other": "Other",
}

CLASSIFICATION_PROMPT = """You are classifying a philosophy job posting using a two-level area of specialization (AOS) taxonomy.

MAIN AOS CATEGORIES (8 total):
Ethics, Social & Political Philosophy, Value Theory / Aesthetics, History of Philosophy, Non-Western & Cross-Cultural Philosophy, Metaphysics & Epistemology, Science, Logic, & Mathematics, Open

DETAIL AOS SUBCATEGORIES (by main category):
Ethics: Meta-Ethics, Normative Ethics, Virtue Ethics, Biomedical Ethics / Bioethics, Neuroethics, AI, Technology, and Information Ethics, Environmental Ethics, Animal Ethics, Food and Agricultural Ethics, Business Ethics, Ethics of Population, Future Generations, and Global Justice, Ethics (General / Applied Ethics, Broadly Construed)
Social & Political Philosophy: Social and Political Philosophy (General / Political Theory), Philosophy of Law, Philosophy of Race, Philosophy of Gender, Philosophy of Disability, Feminist Philosophy, Philosophy of Sexuality and Queer Theory, PPE (Politics, Philosophy, and Economics), Philosophy of Education, Public Philosophy
Value Theory / Aesthetics: Aesthetics (General), Philosophy of Art, Philosophy of Music, Philosophy of Film and Media, Philosophy of Literature, Value Theory / Axiology, Value Theory / Aesthetics (General)
History of Philosophy: Ancient Greek and Roman Philosophy, Medieval and Renaissance Philosophy, Early Modern Philosophy (17th/18th Century), 19th/20th Century Philosophy, American Philosophy, Continental Philosophy, Phenomenology, History of Philosophy (General)
Non-Western & Cross-Cultural Philosophy: Asian Philosophy, African/Africana Philosophy, Arabic and Islamic Philosophy, Latin American Philosophy, Native American / Indigenous Philosophy, Comparative Philosophy / Cross-Cultural, Non-Western Philosophy (General)
Metaphysics & Epistemology: Metaphysics, Epistemology, Philosophy of Mind, Philosophy of Language, Philosophy of Action, Philosophy of Religion, Metaphysics & Epistemology (General)
Science, Logic, & Mathematics: Philosophy of Science (General), Philosophy of Biology, Philosophy of Physics, Philosophy of Cognitive Science, Philosophy of Computing / Philosophy of AI, Logic, Philosophy of Mathematics, Philosophy of Social Science, Decision Theory, Science, Logic, & Mathematics (General)

INSTRUCTIONS:
Return ONLY a JSON object with these fields:
- main_aos: array of main category names that apply (at least one; use ["Open"] if open/unclear)
- detail_aos: object mapping each main_aos entry to array of applicable detail subcategories (use [] if none clearly apply)
- position_type: exactly one of the five values below — read the title, job category, and description carefully
- institution_type: one of "Research University", "Teaching College", "Other"
- state_us: 2-letter US state code if the institution is in the United States (e.g. "NY", "CA"), or "INTERNATIONAL" if outside the US
- reasoning: 1-2 sentence explanation

POSITION TYPE — pick exactly one:
- "Tenure-Track": explicitly described as tenure-track; includes "Assistant Professor (tenure-track)", any TT position
- "Postdoc / Fellowship": postdoctoral positions, postdoc fellowships, named fellowships (Mellon, ACLS, etc.), research fellowships — fixed-term but research-focused
- "Visiting / Adjunct / Lecturer (Fixed-Term)": Visiting Assistant Professor, Visiting Lecturer, Adjunct, Instructor, fixed-term Lecturer, temporary teaching positions — teaching-focused with no path to permanence at that institution
- "Tenured / Continuing / Permanent": Associate Professor (tenured), Full Professor, Professor, Senior Lecturer (permanent/continuing), any position that is explicitly permanent or continuing non-tenure-track
- "Other": department chairs with no faculty component, deans, purely administrative positions, non-academic positions, anything that does not fit the above

Rules:
1. A job can belong to multiple main AOS categories
2. Open means any area of philosophy is acceptable; use ["Open"] only if the posting has no specific AOS requirements
3. Base AOS classification primarily on the AOS field; use title and description as context
4. For detail_aos, only include subcategories clearly mentioned or strongly implied
5. For position_type, prioritize explicit wording in the title and job category over inferred meaning
6. Return only valid JSON — no markdown, no code fences

JOB POSTING:
Institution: {institution}
Title: {title}
Job Category: {job_category}
AOS: {aos_text}
AOC: {aoc_text}
Location: {location}
Description (excerpt): {description}"""


class PhilJobsScraper:
    def __init__(self):
        self.base_url = "https://philjobs.org"
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

    # ── Location helpers ──────────────────────────────────────────────────

    def extract_location_data(self, location_string):
        """Extract state, country, and city from location string."""
        if not location_string:
            return None, None, None

        # Always extract city from the first comma-separated part if available.
        # Previously this only ran when a full state name matched, which missed
        # cases like "Stanford, Ca, United States" (uses 'Ca' not 'California').
        parts = [p.strip() for p in location_string.split(',')]
        city = parts[0] if len(parts) > 1 and parts[0] else None

        for state_name, state_code in US_STATES.items():
            if re.search(r'\b' + re.escape(state_name) + r'\b', location_string):
                return state_code, 'United States', city

        latin_american_countries = [
            'Mexico', 'Brazil', 'Argentina', 'Chile', 'Colombia', 'Peru', 'Venezuela',
            'Ecuador', 'Guatemala', 'Cuba', 'Bolivia', 'Haiti', 'Dominican Republic',
            'Honduras', 'Paraguay', 'El Salvador', 'Nicaragua', 'Costa Rica', 'Panama',
            'Puerto Rico', 'Uruguay'
        ]
        for country in latin_american_countries:
            if country in location_string:
                return None, country, None

        country_name = parts[-1] if parts and parts[-1] else 'Other International'
        return None, country_name, None

    # ── Scraping ──────────────────────────────────────────────────────────

    def get_job_ids_from_listing(self):
        """Get all job IDs using the detailed query view, with fallback."""
        DETAILED_URL = (
            "https://philjobs.org/jobQuery/execute"
            "?view=On+screen+-+detailed"
            "&typesToggler=Any+job+type"
            "&tenureTypesToggler=Any+contract+type"
            "&jobQuery.locationConstraint=NONE"
            "&jobQuery.institution.deleted=false"
            "&jobQuery.distance=50.0"
            "&topicListToggler=Any+AOS"
            "&aocListToggler=Any+AOC"
            "&jobQuery.orderBy=Creation+time"
            "&jobQuery.fromDate=date.struct"
            "&jobQuery.toDate=date.struct"
        )

        def extract_ids_from_soup(soup):
            ids = []
            for link in soup.find_all('a', href=lambda x: x and '/job/show/' in x):
                job_id = link['href'].rstrip('/').split('/')[-1]
                if job_id.isdigit() and job_id not in ids:
                    ids.append(job_id)
            return ids

        try:
            job_ids = []
            page = 1
            while True:
                url = DETAILED_URL + f"&jobQuery.page={page}"
                response = requests.get(url, headers=self.headers, timeout=30)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                page_ids = extract_ids_from_soup(soup)
                if not page_ids:
                    break
                new_ids = [i for i in page_ids if i not in job_ids]
                if not new_ids:
                    break
                job_ids.extend(new_ids)
                next_link = soup.find('a', string=lambda t: t and 'next' in t.lower())
                if not next_link:
                    break
                page += 1

            if job_ids:
                print(f"Found {len(job_ids)} job listings (detailed view)")
                return job_ids

            raise ValueError("No jobs found in detailed view — falling back")

        except Exception as e:
            print(f"Detailed URL fetch failed ({e}), falling back to main listing...")
            try:
                response = requests.get(f"{self.base_url}/", headers=self.headers, timeout=30)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                job_ids = extract_ids_from_soup(soup)
                print(f"Found {len(job_ids)} job listings (fallback)")
                return job_ids
            except Exception as e2:
                print(f"Error fetching job listing: {e2}")
                return []

    def scrape_job_details(self, job_id):
        """Scrape detailed information from a single job posting."""
        url = f"{self.base_url}/job/show/{job_id}"
        try:
            time.sleep(0.5)
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            job = {'id': job_id, 'url': url}

            h2 = soup.find('h2')
            h1 = soup.find('h1')
            job['institution'] = h2.get_text(strip=True) if h2 else "Unknown"
            job['title'] = h1.get_text(strip=True) if h1 else "Unknown"

            for row in soup.find_all('tr'):
                cells = row.find_all('td')
                if len(cells) == 2:
                    key = cells[0].get_text(strip=True)
                    value = cells[1].get_text(strip=True)
                    if key == "Job category":
                        job['job_category'] = value
                    elif key == "AOS":
                        job['aos'] = value
                    elif key == "AOC":
                        job['aoc'] = value
                    elif key == "Workload":
                        job['workload'] = value
                    elif key == "Vacancies":
                        job['vacancies'] = value
                    elif key == "Location":
                        job['location'] = value
                        state, country, city = self.extract_location_data(value)
                        job['state'] = state
                        job['country'] = country
                        job['city'] = city
                    elif key == "Start date":
                        job['start_date'] = value
                    elif key == "Job description":
                        job['description'] = value
                    elif key == "Hard deadline":
                        job['deadline'] = value
                    elif key == "Application type":
                        job['application_type'] = value
                    elif key == "Web address to apply":
                        job['application_url'] = value
                    elif key == "Contact email":
                        job['contact_email'] = value
                    elif key == "Time created":
                        job['posted_date'] = value

            # Basic job_type from job_category + title (Claude will refine via classification)
            combined = f"{job.get('job_category', '')} {job.get('title', '')}".lower()
            if any(w in combined for w in ['tenure-track', 'tenure track', 'assistant professor']):
                job['job_type'] = 'Tenure-Track'
            elif any(w in combined for w in ['postdoc', 'post-doc', 'postdoctoral', 'fellowship']):
                job['job_type'] = 'Postdoc / Fellowship'
            elif any(w in combined for w in ['adjunct', 'visiting', 'lecturer', 'instructor']):
                job['job_type'] = 'Visiting / Adjunct / Lecturer (Fixed-Term)'
            elif any(w in combined for w in ['tenured', 'associate professor', 'full professor', 'professor']):
                job['job_type'] = 'Tenured / Continuing / Permanent'
            else:
                job['job_type'] = 'Other'

            job['institution_type'] = 'Other'  # refined by Claude
            job['classification'] = None        # filled by classify_job_with_claude()

            if "(EXPIRED)" in job.get('title', ''):
                job['status'] = 'expired'
                job['title'] = job['title'].replace('(EXPIRED)', '').strip()
            else:
                job['status'] = 'active'

            # Use PhilJobs job ID as the deduplication key — more reliable than
            # institution+title, which fails when titles have minor variations or
            # when a school posts two identical-titled roles in the same cycle.
            job['hash'] = hashlib.md5(job_id.encode()).hexdigest()
            job['scraped_date'] = datetime.now().isoformat()

            return job

        except Exception as e:
            print(f"Error scraping job {job_id}: {e}")
            return None

    def scrape_jobs(self):
        """Scrape all jobs with full details."""
        print("Fetching job IDs from listing page...")
        job_ids = self.get_job_ids_from_listing()
        jobs = []
        total = len(job_ids)
        print(f"Scraping details for {total} jobs...")
        for i, job_id in enumerate(job_ids, 1):
            print(f"  [{i}/{total}] Scraping job {job_id}...")
            job = self.scrape_job_details(job_id)
            if job:
                jobs.append(job)
        print(f"Successfully scraped {len(jobs)} jobs")
        return jobs

    # ── Data persistence ──────────────────────────────────────────────────

    def load_historical_data(self):
        """Load all historical job data."""
        all_data_file = self.data_dir / "all_jobs.json"
        if all_data_file.exists():
            with open(all_data_file, 'r') as f:
                data = json.load(f)
                data.setdefault('weekly_trends', [])
                data.setdefault('weekly_snapshots', [])
                data.setdefault('jobs', [])
                return data
        return {'jobs': [], 'weekly_snapshots': [], 'weekly_trends': []}

    def migrate_hashes_to_job_id(self, historical_data) -> int:
        """One-time migration: recompute all existing job hashes using PhilJobs job ID.

        Previously hashes were MD5(institution_title). Switching to MD5(job_id) is
        more reliable. This runs on every scrape but is a no-op once all jobs have
        been migrated (detected by checking whether the stored hash matches the
        ID-based hash).
        """
        jobs = historical_data.get('jobs', [])
        migrated = 0
        for job in jobs:
            job_id = job.get('id', '')
            if not job_id:
                continue
            expected_hash = hashlib.md5(job_id.encode()).hexdigest()
            if job.get('hash') != expected_hash:
                job['hash'] = expected_hash
                migrated += 1

        if migrated:
            print(f"  Migrated {migrated} job hashes to PhilJobs-ID-based deduplication")
            all_data_file = self.data_dir / "all_jobs.json"
            with open(all_data_file, 'w') as f:
                json.dump(historical_data, f, indent=2)
        else:
            print("  Hash format already up to date — no migration needed")

        return migrated

    def migrate_to_current_taxonomy(self, historical_data) -> int:
        """If the stored taxonomy_version differs from the current TAXONOMY_VERSION,
        clear classifications on all jobs so they get re-classified under the new
        subcategory structure. Preserves prior labels under `classification_v1`
        (or v2, v3, etc.) so we can audit how labels shifted between revisions.

        Idempotent: safe to call on every scrape. No-op when versions match.
        """
        stored = historical_data.get('taxonomy_version')
        if stored == TAXONOMY_VERSION:
            return 0

        print(f"  Taxonomy version change detected: '{stored}' → '{TAXONOMY_VERSION}'")
        cleared = 0
        for job in historical_data.get('jobs', []):
            cls = job.get('classification')
            if not cls:
                continue
            # Pick the next available `classification_vN` slot so re-runs don't overwrite
            n = 1
            while f'classification_v{n}' in job:
                n += 1
            job[f'classification_v{n}'] = cls
            job['classification'] = None  # forces re-classification on next pass
            cleared += 1

        historical_data['taxonomy_version'] = TAXONOMY_VERSION
        all_data_file = self.data_dir / "all_jobs.json"
        with open(all_data_file, 'w') as f:
            json.dump(historical_data, f, indent=2)
        print(f"  Cleared classification on {cleared} jobs; prior labels preserved under classification_v* keys")
        return cleared

    def backfill_city_field(self, historical_data) -> int:
        """Re-parse city from location for jobs that have a location string but no city.

        The original extract_location_data() only populated 'city' when a full
        state NAME was matched in the location string. Jobs whose location used
        a 2-letter state code (e.g. "Stanford, Ca, United States") got city=None
        even though state was later resolved by Claude. This backfill re-derives
        city from the first comma-separated segment of the location string.
        """
        fixed = 0
        for job in historical_data.get('jobs', []):
            if job.get('city'):
                continue
            location = job.get('location', '')
            if not location:
                continue
            parts = [p.strip() for p in location.split(',')]
            if len(parts) > 1 and parts[0]:
                job['city'] = parts[0]
                fixed += 1

        if fixed:
            all_data_file = self.data_dir / "all_jobs.json"
            with open(all_data_file, 'w') as f:
                json.dump(historical_data, f, indent=2)
            print(f"  Backfilled city field for {fixed} jobs")
        else:
            print("  No city fields needed backfilling")
        return fixed

    def save_data(self, jobs, historical_data):
        """Save job data and update historical records."""
        timestamp = datetime.now().strftime("%Y-%m-%d")
        existing_hashes = {job['hash'] for job in historical_data['jobs']}
        new_jobs = [job for job in jobs if job['hash'] not in existing_hashes]
        historical_data['jobs'].extend(new_jobs)

        weekly_trend = self.calculate_weekly_trends(new_jobs, timestamp)
        historical_data['weekly_trends'].append(weekly_trend)

        snapshot = {
            'date': timestamp,
            'total_jobs': len(jobs),
            'new_jobs': len(new_jobs),
            'new_job_ids': [job['id'] for job in new_jobs]
        }
        historical_data['weekly_snapshots'].append(snapshot)

        all_data_file = self.data_dir / "all_jobs.json"
        with open(all_data_file, 'w') as f:
            json.dump(historical_data, f, indent=2)

        weekly_file = self.data_dir / f"snapshot_{timestamp}.json"
        with open(weekly_file, 'w') as f:
            json.dump({'date': timestamp, 'jobs': jobs, 'new_jobs': new_jobs}, f, indent=2)

        return new_jobs, snapshot, weekly_trend

    # ── Claude API classification ─────────────────────────────────────────

    def _classification_fallback(self):
        return {
            "main_aos": ["Open"],
            "detail_aos": {"Open": []},
            "position_type": "Other",
            "institution_type": "Other",
            "reasoning": "classification_failed"
        }

    def classify_job_with_claude(self, job) -> dict:
        """Classify a single job using Claude Haiku. Returns classification dict."""
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            return self._classification_fallback()

        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
        except ImportError:
            print("  Warning: anthropic package not installed — skipping classification")
            return self._classification_fallback()

        prompt_text = CLASSIFICATION_PROMPT.format(
            institution=job.get('institution', ''),
            title=job.get('title', ''),
            job_category=job.get('job_category', ''),
            aos_text=job.get('aos', ''),
            aoc_text=job.get('aoc', ''),
            location=job.get('location', ''),
            description=(job.get('description', '') or '')[:500]
        )

        for attempt in range(3):
            try:
                response = client.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=1000,
                    temperature=0,
                    messages=[{"role": "user", "content": prompt_text}]
                )
                text = response.content[0].text
                # Strip markdown code fences if present
                text = re.sub(r'^```(?:json)?\s*\n?', '', text.strip())
                text = re.sub(r'\n?```\s*$', '', text.strip())
                result = json.loads(text)

                # Validate and clean main_aos
                valid_main = [m for m in result.get('main_aos', []) if m in MAIN_AOS_CATEGORIES]
                if not valid_main:
                    valid_main = ['Open']
                result['main_aos'] = valid_main

                # Ensure detail_aos is a dict
                if not isinstance(result.get('detail_aos'), dict):
                    result['detail_aos'] = {m: [] for m in valid_main}

                # Validate detail values
                for main, details in result['detail_aos'].items():
                    valid_details = [d for d in (details or []) if d in DETAIL_AOS.get(main, [])]
                    result['detail_aos'][main] = valid_details

                # Validate position_type — migrate old labels if needed
                raw_pt = result.get('position_type') or result.get('job_type', 'Other')
                if raw_pt in POSITION_TYPES:
                    result['position_type'] = raw_pt
                elif raw_pt in JOB_TYPE_MIGRATION:
                    result['position_type'] = JOB_TYPE_MIGRATION[raw_pt]
                else:
                    result['position_type'] = 'Other'
                result.pop('job_type', None)  # remove old field

                # Validate state_us
                raw_state = (result.get('state_us') or '').strip().upper()
                if len(raw_state) == 2 and raw_state.isalpha():
                    result['state_us'] = raw_state
                else:
                    result['state_us'] = 'INTERNATIONAL'

                time.sleep(0.5)
                return result

            except Exception as e:
                print(f"  Classification attempt {attempt + 1} failed: {e}")
                if attempt < 2:
                    time.sleep(1)

        return self._classification_fallback()

    def reclassify_all_jobs(self, historical_data) -> int:
        """Classify all jobs that don't have a classification yet. Migrates old labels. Saves checkpoints."""
        jobs = historical_data.get('jobs', [])

        # Migrate already-classified jobs from old job_type labels to new position_type labels
        migrated = 0
        for job in jobs:
            cls = job.get('classification')
            if cls and not cls.get('position_type'):
                old = cls.get('job_type', 'Other')
                cls['position_type'] = JOB_TYPE_MIGRATION.get(old, 'Other')
                cls.pop('job_type', None)
                job['job_type'] = cls['position_type']  # sync top-level
                migrated += 1
        if migrated:
            print(f"  Migrated {migrated} jobs to new position_type labels")

        unclassified = [
            j for j in jobs
            if not j.get('classification')
            or j['classification'].get('reasoning') == 'classification_failed'
        ]
        total = len(unclassified)

        if total == 0:
            if migrated:
                all_data_file = self.data_dir / "all_jobs.json"
                with open(all_data_file, 'w') as f:
                    json.dump(historical_data, f, indent=2)
            print("All jobs already classified.")
            return 0

        print(f"Classifying {total} jobs with Claude API...")
        classified_count = 0

        for i, job in enumerate(unclassified, 1):
            label = f"{job.get('institution', '?')} — {job.get('title', '?')[:50]}"
            print(f"  [{i}/{total}] {label}")
            classification = self.classify_job_with_claude(job)
            job['classification'] = classification
            # Sync top-level fields for backward compatibility
            job['job_type'] = classification.get('position_type', 'Other')
            job['institution_type'] = classification.get('institution_type', 'Other')
            # Populate state from Claude if scraper couldn't parse it
            if not job.get('state'):
                state_us = classification.get('state_us', '')
                if state_us and state_us != 'INTERNATIONAL':
                    job['state'] = state_us
            classified_count += 1

            # Checkpoint save every 10 jobs
            if classified_count % 10 == 0:
                all_data_file = self.data_dir / "all_jobs.json"
                with open(all_data_file, 'w') as f:
                    json.dump(historical_data, f, indent=2)
                print(f"  Checkpoint saved ({classified_count}/{total})")

        # Final save
        all_data_file = self.data_dir / "all_jobs.json"
        with open(all_data_file, 'w') as f:
            json.dump(historical_data, f, indent=2)

        print(f"✓ Classified {classified_count} jobs")
        return classified_count

    def resolve_missing_states(self, historical_data) -> int:
        """Use Claude to resolve the US state for jobs where state is missing."""
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            return 0
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
        except ImportError:
            return 0

        jobs_needing_state = [j for j in historical_data.get('jobs', []) if not j.get('state')]
        if not jobs_needing_state:
            return 0

        print(f"Resolving state for {len(jobs_needing_state)} jobs via Claude...")
        resolved = 0
        for job in jobs_needing_state:
            prompt = (
                f"What US state is this institution located in?\n"
                f"Reply with ONLY the 2-letter state code (e.g. \"NY\") "
                f"or \"INTERNATIONAL\" if not in the United States.\n\n"
                f"Institution: {job.get('institution', '')}\n"
                f"Location: {job.get('location', '')}"
            )
            for attempt in range(3):
                try:
                    response = client.messages.create(
                        model="claude-haiku-4-5-20251001",
                        max_tokens=10,
                        temperature=0,
                        messages=[{"role": "user", "content": prompt}]
                    )
                    answer = response.content[0].text.strip().upper().strip('"\'')
                    if answer == 'INTERNATIONAL':
                        job['state'] = None  # already None, mark as confirmed international
                        break
                    elif len(answer) == 2 and answer.isalpha():
                        job['state'] = answer
                        resolved += 1
                        break
                except Exception:
                    if attempt < 2:
                        time.sleep(1)
            time.sleep(0.3)

        if resolved:
            all_data_file = self.data_dir / "all_jobs.json"
            with open(all_data_file, 'w') as f:
                json.dump(historical_data, f, indent=2)
            print(f"✓ Resolved state for {resolved} jobs")
        return resolved

    def rebuild_weekly_trends(self, historical_data):
        """Rebuild weekly_trends from classified jobs grouped by scraped_date."""
        jobs = historical_data.get('jobs', [])
        date_groups = defaultdict(list)
        for job in jobs:
            date = job.get('scraped_date', '')[:10]
            if date:
                date_groups[date].append(job)

        new_trends = []
        for date in sorted(date_groups.keys()):
            trend = self.calculate_weekly_trends(date_groups[date], date)
            new_trends.append(trend)

        historical_data['weekly_trends'] = new_trends

        all_data_file = self.data_dir / "all_jobs.json"
        with open(all_data_file, 'w') as f:
            json.dump(historical_data, f, indent=2)

        print(f"✓ Rebuilt {len(new_trends)} weekly trend entries from classified data")

    # ── Trends calculation ────────────────────────────────────────────────

    def calculate_weekly_trends(self, new_jobs, timestamp):
        """Calculate trends based on new jobs, using Claude classification."""
        main_aos_counts = defaultdict(int)
        detail_aos_counts = defaultdict(int)
        position_type_counts = defaultdict(int)
        position_type_by_aos = defaultdict(lambda: defaultdict(int))
        job_category_counts = defaultdict(int)
        institution_type_counts = defaultdict(int)
        state_counts = defaultdict(int)
        country_counts = defaultdict(int)
        west_coast_city_counts = defaultdict(int)

        for job in new_jobs:
            classification = job.get('classification') or {}

            main_list = classification.get('main_aos', ['Open'])
            for main in main_list:
                main_aos_counts[main] += 1

            for main, details in classification.get('detail_aos', {}).items():
                for detail in details:
                    detail_aos_counts[f"{main}::{detail}"] += 1

            # position_type: new 5-category field; fall back to migrated job_type if needed
            raw_pt = (classification.get('position_type')
                      or JOB_TYPE_MIGRATION.get(classification.get('job_type', ''), None)
                      or job.get('job_type', 'Other'))
            pos_type = raw_pt if raw_pt in POSITION_TYPES else 'Other'
            position_type_counts[pos_type] += 1

            # Track position_type broken down by main AOS
            for main in main_list:
                position_type_by_aos[main][pos_type] += 1

            inst_type = classification.get('institution_type') or job.get('institution_type', 'Other')
            institution_type_counts[inst_type] += 1

            job_category = job.get('job_category', 'Other')
            job_category_counts[job_category] += 1

            state = job.get('state')
            country = job.get('country')
            city = job.get('city')

            if state:
                state_counts[state] += 1
                # Capture every CA/OR/WA city that appears in our data — not just
                # a hardcoded allowlist. This lets the West Coast Spotlight chart
                # include Pasadena, La Jolla, Long Beach, etc. automatically.
                if state in ['CA', 'OR', 'WA'] and city:
                    west_coast_city_counts[city] += 1

            if country:
                country_counts[country] += 1

        return {
            'date': timestamp,
            'new_jobs_count': len(new_jobs),
            'main_aos_counts': dict(main_aos_counts),
            'detail_aos_counts': dict(detail_aos_counts),
            'position_type_counts': dict(position_type_counts),
            'position_type_by_aos': {k: dict(v) for k, v in position_type_by_aos.items()},
            'job_category_counts': dict(job_category_counts),
            'institution_type_counts': dict(institution_type_counts),
            'state_counts': dict(state_counts),
            'country_counts': dict(country_counts),
            'west_coast_city_counts': dict(west_coast_city_counts),
        }

    # ── Co-occurrence ─────────────────────────────────────────────────────

    def compute_cooccurrence(self, historical_data) -> dict:
        """Compute co-occurrence matrix and related stats from classified jobs."""
        main_aos_matrix = defaultdict(lambda: defaultdict(int))
        main_aos_solo_vs_joint = defaultdict(lambda: {'solo': 0, 'joint': 0})
        detail_aos_by_context = defaultdict(
            lambda: {'solo': defaultdict(int), 'with_others': defaultdict(int), 'total': 0}
        )
        cc_totals = {area: 0 for area in CROSS_CUTTING_AREAS}
        cc_by_main = {area: defaultdict(int) for area in CROSS_CUTTING_AREAS}
        cc_weekly = {area: defaultdict(int) for area in CROSS_CUTTING_AREAS}

        for job in historical_data.get('jobs', []):
            classification = job.get('classification')
            if not classification:
                continue

            main_list = classification.get('main_aos', [])
            detail_dict = classification.get('detail_aos', {})
            week = job.get('scraped_date', '')[:10]

            # Matrix: count each pair
            for m1 in main_list:
                for m2 in main_list:
                    if m1 != m2:
                        main_aos_matrix[m1][m2] += 1

            # Solo vs. joint
            if len(main_list) == 1:
                main_aos_solo_vs_joint[main_list[0]]['solo'] += 1
            elif len(main_list) > 1:
                for m in main_list:
                    main_aos_solo_vs_joint[m]['joint'] += 1

            # Detail AOS by context
            for main, details in detail_dict.items():
                for detail in details:
                    ctx = detail_aos_by_context[detail]
                    ctx['total'] += 1
                    if len(main_list) == 1:
                        ctx['solo'][main] += 1
                    else:
                        for other_main in main_list:
                            if other_main != main:
                                ctx['with_others'][other_main] += 1

            # Cross-cutting areas
            for main, details in detail_dict.items():
                for detail in details:
                    if detail in CROSS_CUTTING_AREAS:
                        cc_totals[detail] += 1
                        cc_by_main[detail][main] += 1
                        if week:
                            cc_weekly[detail][week] += 1

        all_weeks = sorted({t['date'] for t in historical_data.get('weekly_trends', [])})

        cross_cutting_final = {}
        for area in CROSS_CUTTING_AREAS:
            cross_cutting_final[area] = {
                'total': cc_totals[area],
                'by_main_aos': dict(cc_by_main[area]),
                'trend': [{'week': w, 'count': cc_weekly[area].get(w, 0)} for w in all_weeks],
            }

        result = {
            'main_aos_matrix': {k: dict(v) for k, v in main_aos_matrix.items()},
            'detail_aos_by_context': {
                k: {
                    'solo': dict(v['solo']),
                    'with_others': dict(v['with_others']),
                    'total': v['total'],
                }
                for k, v in detail_aos_by_context.items()
            },
            'main_aos_solo_vs_joint': {k: dict(v) for k, v in main_aos_solo_vs_joint.items()},
            'cross_cutting_areas': cross_cutting_final,
        }

        cooc_file = self.data_dir / 'co_occurrence.json'
        with open(cooc_file, 'w') as f:
            json.dump(result, f, indent=2)

        print(f"✓ Co-occurrence data saved to {cooc_file}")
        return result

    # ── Dashboard helpers ──────────────────────────────────────────────────

    def _compute_cooc_from_jobs(self, jobs):
        """Compute co-occurrence data from a filtered list of jobs (no file I/O).

        Cross-cutting data is tracked three ways (all / solo / joint) based on
        whether the job's main_aos list has exactly one entry (solo) or more
        than one (joint). Solo + Joint = All for every cell.
        """
        modes = ('all', 'solo', 'joint')
        main_aos_matrix = defaultdict(lambda: defaultdict(int))
        main_aos_solo_vs_joint = defaultdict(lambda: {'solo': 0, 'joint': 0})
        detail_aos_by_context = defaultdict(
            lambda: {'solo': defaultdict(int), 'with_others': defaultdict(int), 'total': 0}
        )
        cc_totals = {m: {area: 0 for area in CROSS_CUTTING_AREAS} for m in modes}
        cc_by_main = {m: {area: defaultdict(int) for area in CROSS_CUTTING_AREAS} for m in modes}
        cc_weekly = {m: {area: defaultdict(int) for area in CROSS_CUTTING_AREAS} for m in modes}

        for job in jobs:
            classification = job.get('classification')
            if not classification:
                continue
            main_list = classification.get('main_aos', [])
            detail_dict = classification.get('detail_aos', {})
            week = job.get('scraped_date', '')[:10]
            job_mode = 'solo' if len(main_list) == 1 else 'joint'

            for m1 in main_list:
                for m2 in main_list:
                    if m1 != m2:
                        main_aos_matrix[m1][m2] += 1

            if len(main_list) == 1:
                main_aos_solo_vs_joint[main_list[0]]['solo'] += 1
            elif len(main_list) > 1:
                for m in main_list:
                    main_aos_solo_vs_joint[m]['joint'] += 1

            for main, details in detail_dict.items():
                for detail in details:
                    ctx = detail_aos_by_context[detail]
                    ctx['total'] += 1
                    if len(main_list) == 1:
                        ctx['solo'][main] += 1
                    else:
                        for other_main in main_list:
                            if other_main != main:
                                ctx['with_others'][other_main] += 1

            for main, details in detail_dict.items():
                for detail in details:
                    if detail in CROSS_CUTTING_AREAS:
                        cc_totals['all'][detail] += 1
                        cc_totals[job_mode][detail] += 1
                        cc_weekly['all'][detail][week] += 1
                        cc_weekly[job_mode][detail][week] += 1
                        for other_main in main_list:
                            cc_by_main['all'][detail][other_main] += 1
                            cc_by_main[job_mode][detail][other_main] += 1

        # Use the union of all weeks seen, regardless of mode
        all_weeks = sorted({w for m in modes for area in CROSS_CUTTING_AREAS for w in cc_weekly[m][area]})
        cross_cutting_final = {}
        for area in CROSS_CUTTING_AREAS:
            cross_cutting_final[area] = {
                m: {
                    'total': cc_totals[m][area],
                    'by_main': dict(cc_by_main[m][area]),
                    'weekly': {w: cc_weekly[m][area].get(w, 0) for w in all_weeks},
                }
                for m in modes
            }

        return {
            'main_aos_matrix': {k: dict(v) for k, v in main_aos_matrix.items()},
            'main_aos_solo_vs_joint': {k: dict(v) for k, v in main_aos_solo_vs_joint.items()},
            'detail_aos_by_context': {
                k: {'solo': dict(v['solo']), 'with_others': dict(v['with_others']), 'total': v['total']}
                for k, v in detail_aos_by_context.items()
            },
            'cross_cutting_areas': cross_cutting_final,
        }

    # ── Keyword Explorer helpers ──────────────────────────────────────────

    @staticmethod
    def _keyword_stem(word):
        """Recursive morphological stemmer. Mirrors the JS kwStem function so
        Python-side and browser-side stemming stay in lockstep. Applies suffix
        rules repeatedly until the word stops changing, which lets "feminists"
        → "feminist" → "femin" all collapse to a single stem."""
        prev = None
        while prev != word and len(word) > 3:
            prev = word
            if word.endswith('ies'):
                word = word[:-3] + 'y'
            elif word.endswith('ism'):
                word = word[:-3]
            elif word.endswith('ist'):
                word = word[:-3]
            elif word.endswith('ing'):
                word = word[:-3]
            elif word.endswith('ed'):
                word = word[:-2]
            elif word.endswith('es'):
                word = word[:-2]
            elif word.endswith('s'):
                word = word[:-1]
        return word

    @staticmethod
    def _strip_eeo_boilerplate(text):
        """Remove sentences that are EEO / equal-opportunity-employer statements.

        Almost every academic job description ends with a paragraph like:
            "The University is an equal opportunity employer and considers
            applicants without regard to race, color, religion, national
            origin, age, sex, gender identity, sexual orientation, veteran
            status, or disability."
        These sentences flood the keyword search with terms ("race",
        "religion", "veterans") that aren't substantively about those topics.

        Heuristic: any sentence with 2+ EEO trigger words is stripped.
        Some real content may be lost; the trade-off is meaningful philosophy
        terms not getting drowned in legal boilerplate.
        """
        if not text:
            return text
        triggers = {
            'equal', 'opportunity', 'opportunities', 'employer', 'affirmative',
            'regardless', 'protected', 'veterans', 'veteran', 'disabilities',
            'disability', 'ancestry', 'ethnicity', 'origin', 'orientation',
            'nondiscrimination', 'discriminate', 'discrimination', 'harassment',
            'pregnancy', 'citizenship', 'genetic', 'creed', 'nationality',
        }
        sentences = re.split(r'(?<=[.!?])\s+', text)
        kept = []
        for s in sentences:
            words = set(re.findall(r'[a-z]+', s.lower()))
            if len(words & triggers) >= 2:
                continue
            kept.append(s)
        return ' '.join(kept)

    def _extract_description_terms(self, text):
        """Tokenize a job description into a deduplicated list of substantive
        raw words. Strips EEO boilerplate sentences first, then filters
        stopwords and short words. JS-side handles stemming at search time.
        """
        if not text:
            return []
        text = self._strip_eeo_boilerplate(text)
        text = text.lower()
        text = re.sub(r"[^a-z]", ' ', text)
        words = text.split()
        terms = set()
        for w in words:
            if len(w) < 4 or w in KEYWORD_STOPWORDS:
                continue
            terms.add(w)
        return sorted(terms)

    def build_keyword_index(self, jobs):
        """Build the per-job keyword index for the Keyword Explorer.

        Returns (index, vocab, bubble_stopwords):
          - index:           list of {terms, scraped_date} per job. Includes
                             ALL terms (boilerplate included) so search remains
                             permissive — a search for "ethics" still hits all
                             jobs that mention ethics, even if "ethics" is in
                             many descriptions.
          - vocab:           top corpus terms for synonym generation
          - bubble_stopwords: terms appearing in >80% of descriptions. Filtered
                             out of the bubble chart display only (where they'd
                             be noise) but NOT out of search.
        """
        term_doc_freq = defaultdict(int)
        per_job_terms = []
        for job in jobs:
            description = job.get('description', '') or ''
            terms = self._extract_description_terms(description)
            per_job_terms.append((job, terms))
            for t in set(terms):
                term_doc_freq[t] += 1

        total_jobs = max(len(jobs), 1)
        bubble_stopwords = sorted({
            t for t, n in term_doc_freq.items() if n / total_jobs > 0.80
        })
        if bubble_stopwords:
            print(f"  Bubble stopwords ({len(bubble_stopwords)} terms in >80% of descriptions): {bubble_stopwords[:10]}")

        index = []
        for job, terms in per_job_terms:
            scraped = (job.get('scraped_date') or '')[:10]
            index.append({'terms': terms, 'scraped_date': scraped})

        vocab = sorted(
            [t for t, n in term_doc_freq.items()
             if n >= 3 and len(t) >= 4 and t not in set(bubble_stopwords)],
            key=lambda t: -term_doc_freq[t]
        )
        return index, vocab, bubble_stopwords

    def generate_synonym_map(self, vocab, max_terms=150):
        """Use Claude Haiku to generate synonyms / related terms for the top
        `max_terms` corpus vocabulary. Returns dict {term: [synonyms]}. Fails
        gracefully — if the API or package is unavailable, returns {} and the
        client-side search still works (just without synonym expansion).

        Cached for the lifetime of the scraper instance, so calling once from
        the US dashboard and once from the Intl dashboard only hits the API
        once. Synonym mappings are universal — they don't depend on whether
        the vocab came from US or Intl jobs.
        """
        if not vocab:
            return {}
        if hasattr(self, '_synonym_map_cache'):
            print(f"  Using cached synonym map ({len(self._synonym_map_cache)} terms)")
            return self._synonym_map_cache

        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            print("  No ANTHROPIC_API_KEY — synonym map will be empty")
            return {}
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
        except ImportError:
            return {}

        terms_to_expand = vocab[:max_terms]
        synonym_map = {}
        batch_size = 25

        prompt_template = (
            "You're helping build a search tool for an academic philosophy job board. "
            "For each keyword below, list 4-10 FIELD-DEFINING synonyms — alternative "
            "names the academic discipline uses for the same subfield, research area, "
            "or concept.\n\n"
            "INCLUDE:\n"
            "- Morphological variants (feminism / feminist / feminists; race / racial / racism)\n"
            "- Alternative names for the same subfield (gay / queer / LGBTQ; AI / artificial intelligence / machine learning; environmental / ecology)\n"
            "- Standard academic terminology that NAMES this area (queer theory, critical race theory)\n\n"
            "EXCLUDE:\n"
            "- Broadly related concepts that aren't field names (e.g. 'patriarchy' or "
            "'intersectional' for feminism — these are concepts WITHIN feminism, not "
            "names FOR it)\n"
            "- Co-occurring topics (e.g. 'ethics' for race, 'social' for feminism — "
            "they often appear in the same job posting but aren't synonyms)\n"
            "- Generic adjectives or institutional jargon\n\n"
            "Output ONLY valid JSON — no prose, no markdown — as an object mapping "
            "each input keyword to an array of related terms. Keep all output "
            "lowercase. Example:\n"
            '{{"feminism": ["feminist", "feminists", "womens studies"], '
            '"race": ["racial", "racism", "antiracism", "ethnicity", "critical race theory"], '
            '"gay": ["queer", "lgbtq", "homosexuality", "sexuality"]}}\n\n'
            "Keywords to expand: {keywords}"
        )

        for i in range(0, len(terms_to_expand), batch_size):
            batch = terms_to_expand[i:i + batch_size]
            prompt = prompt_template.format(keywords=", ".join(batch))
            for attempt in range(3):
                try:
                    response = client.messages.create(
                        model="claude-haiku-4-5-20251001",
                        max_tokens=2000,
                        temperature=0,
                        messages=[{"role": "user", "content": prompt}]
                    )
                    text = response.content[0].text.strip()
                    text = re.sub(r'^```(?:json)?\s*', '', text)
                    text = re.sub(r'\s*```\s*$', '', text)
                    parsed = json.loads(text)
                    if isinstance(parsed, dict):
                        for k, v in parsed.items():
                            if isinstance(v, list):
                                synonym_map[k.lower().strip()] = [
                                    s.lower().strip() for s in v
                                    if isinstance(s, str) and s.strip()
                                ]
                    time.sleep(0.4)
                    break
                except Exception as e:
                    print(f"  Synonym batch {i // batch_size + 1} attempt {attempt + 1} failed: {e}")
                    if attempt < 2:
                        time.sleep(1)

        # Cache to disk so we can inspect / debug, and in memory for cross-dashboard reuse
        out_file = self.data_dir / 'synonym_map.json'
        with open(out_file, 'w') as f:
            json.dump(synonym_map, f, indent=2, sort_keys=True)
        print(f"  Synonym map written: {len(synonym_map)} terms → {out_file}")
        self._synonym_map_cache = synonym_map
        return synonym_map

    # ── Keyword Explorer audit documents ──────────────────────────────────

    def write_keyword_docs(self, historical_data):
        """Write two human-readable audit documents alongside the dashboard:

        - docs/SYNONYMS.md: alphabetical list of the current week's synonym
          expansions. Refreshed every Monday when the scraper runs.
        - docs/KEYWORD_EXPLORER_METHODOLOGY.md: a full writeup of how the
          Keyword Explorer is built, including the EEO-stripping algorithm,
          stopword layers, stemming rules, and synonym-generation prompt.

        These are intended for anyone (committee, advisor, peer reviewer)
        who asks "how does this work?" or "show me the synonym list."
        """
        all_jobs = historical_data.get('jobs', [])
        # Pull synonym map from in-memory cache, or load from disk as fallback
        synonym_map = getattr(self, '_synonym_map_cache', None)
        if synonym_map is None:
            sm_file = self.data_dir / 'synonym_map.json'
            if sm_file.exists():
                with open(sm_file) as f:
                    synonym_map = json.load(f)
            else:
                synonym_map = {}

        # Recompute vocab + stopwords for documentation context
        _, vocab, bubble_stopwords = self.build_keyword_index(all_jobs)
        self._write_synonyms_doc(synonym_map)
        self._write_methodology_doc(synonym_map, vocab, bubble_stopwords, len(all_jobs))

    def _write_synonyms_doc(self, synonym_map):
        """Write docs/SYNONYMS.md — alphabetical synonym listing."""
        docs_dir = Path('docs')
        docs_dir.mkdir(exist_ok=True)
        date_str = datetime.now().strftime('%Y-%m-%d')
        n_terms = len(synonym_map)

        lines = [
            '# Keyword Explorer — Synonym Map',
            '',
            f'**Last updated:** {date_str}',
            f'**Source data:** [`data/synonym_map.json`](../data/synonym_map.json)',
            f'**Terms in map:** {n_terms}',
            '',
            '---',
            '',
            '## About This List',
            '',
            'When you type a search term into the Keyword Explorer on the dashboard,',
            'your query is expanded to include the synonyms listed below before',
            'matching against job description text. Example: searching `feminism`',
            'will also find jobs mentioning `feminist`, `patriarchy`, `gender`, etc.',
            '',
            'This map is regenerated automatically every Monday by Claude Haiku',
            'based on the most frequent terms in the corpus of philosophy job',
            'descriptions collected so far. As the corpus grows over time, more',
            'terms will appear here and existing groups may shift.',
            '',
            'For the full methodology behind how these synonyms are generated and',
            'used, see [KEYWORD_EXPLORER_METHODOLOGY.md](KEYWORD_EXPLORER_METHODOLOGY.md).',
            '',
            '---',
            '',
            '## Synonym Groups (Alphabetical)',
            '',
        ]
        if synonym_map:
            for term in sorted(synonym_map.keys()):
                syns = synonym_map.get(term, [])
                if not syns:
                    continue
                lines.append(f'- **{term}** → {", ".join(syns)}')
        else:
            lines.append('_No synonym map available yet — will populate on the next scrape with a valid Claude API key._')

        lines.extend([
            '',
            '---',
            '',
            '## How to Inspect Raw Data',
            '',
            '- **Machine-readable JSON:** [`data/synonym_map.json`](../data/synonym_map.json)',
            '- **Raw job description text:** [`data/all_jobs.json`](../data/all_jobs.json) — each job has a `description` field with the full posting text.',
            '- **Source code:** the synonym generation lives in `scraper.py` under the `generate_synonym_map` method.',
            '',
        ])
        out_file = docs_dir / 'SYNONYMS.md'
        out_file.write_text('\n'.join(lines))
        print(f"  Synonym doc written → {out_file}")

    def _write_methodology_doc(self, synonym_map, vocab, bubble_stopwords, n_jobs):
        """Write docs/KEYWORD_EXPLORER_METHODOLOGY.md — full audit writeup."""
        docs_dir = Path('docs')
        docs_dir.mkdir(exist_ok=True)
        date_str = datetime.now().strftime('%Y-%m-%d')
        n_vocab = len(vocab)
        n_syns = len(synonym_map)
        bubble_stop_sample = ', '.join(f'`{w}`' for w in bubble_stopwords[:8]) if bubble_stopwords else '_none yet_'

        lines = [
            '# Keyword Explorer — Methodology',
            '',
            f'**Last updated:** {date_str}',
            f'**Corpus size at this writing:** {n_jobs} jobs',
            f'**Vocabulary size eligible for synonym lookup:** {n_vocab} terms',
            f'**Synonym groups in current map:** {n_syns}',
            '',
            '---',
            '',
            '## What This Tool Measures',
            '',
            'The Keyword Explorer searches the **full text of job descriptions**',
            'posted on PhilJobs.org. It does NOT search:',
            '',
            '- AOS (Area of Specialization) labels',
            '- AOC (Area of Competence) labels',
            '- Job titles',
            '- Institution names',
            '',
            'This choice is deliberate. Labels reflect institutional and political',
            'choices about how to frame a position; descriptions reflect the actual',
            'work the position is asking for. The two can diverge — for example,',
            'a department may hire someone whose research is on philosophy of race',
            'but avoid labeling the AOS that way for political reasons. By',
            'searching description text only, this tool measures content rather',
            'than framing.',
            '',
            '---',
            '',
            '## Pipeline Overview',
            '',
            '1. **Scrape** PhilJobs.org weekly. Job description text is stored',
            '   per-job in `data/all_jobs.json` under the `description` field.',
            '2. **Strip EEO boilerplate** from descriptions before tokenizing.',
            '3. **Tokenize** descriptions into lowercase word lists.',
            '4. **Filter stopwords** — both generic English stopwords and academic',
            '   job-board boilerplate ("application", "candidates", "faculty",',
            '   etc.).',
            '5. **Identify corpus-frequent terms** (in >80% of descriptions) for',
            '   the bubble-display stopword list. These remain searchable but are',
            '   filtered from the bubble chart to avoid noise.',
            '6. **Generate synonym map** via Claude Haiku (see Synonym Expansion).',
            '7. **Embed** the per-job term index, synonym map, and stopword list',
            '   into the dashboard HTML.',
            '8. **Search runs client-side** in the browser: stems the query,',
            '   expands via the synonym map, matches against per-job stem sets.',
            '',
            '---',
            '',
            '## Key Methodological Choices',
            '',
            '### 1. EEO / Equal-Opportunity-Employer Statement Stripping',
            '',
            'Almost every academic job description ends with an EEO statement like:',
            '',
            '> "The University is an equal opportunity employer and considers',
            '> applicants without regard to race, color, religion, national origin,',
            '> age, sex, gender identity, sexual orientation, veteran status, or',
            '> disability."',
            '',
            'Without filtering, these sentences flood the keyword search. Searching',
            '`race` for example would surface 40+ jobs whose only mention of "race"',
            'is in the EEO statement — not actual philosophy-of-race openings.',
            '',
            '**Algorithm:** Each sentence is checked against a list of EEO trigger',
            'words: `equal`, `opportunity`, `affirmative`, `regardless`, `protected`,',
            '`veterans`, `disabilities`, `ancestry`, `ethnicity`, `origin`,',
            '`orientation`, `nondiscrimination`, `discrimination`, `harassment`,',
            '`pregnancy`, `citizenship`, `genetic`, `creed`, `nationality`. Any',
            'sentence containing **2 or more** trigger words is stripped before',
            'tokenization.',
            '',
            '**Verified impact:** During development, searching `race` dropped from',
            '42 noisy matches (mostly EEO statements) to 9 substantive philosophy-',
            'of-race jobs.',
            '',
            '**Known trade-off:** Some legitimate content can be lost. A sentence',
            'like "We welcome applications from diverse candidates including those',
            'from historically excluded groups" might be stripped if it contains',
            '2+ triggers. The trade-off was deemed acceptable because clean signal',
            'on philosophical content matters more than capturing every diversity',
            'statement.',
            '',
            '### 2. Stopword Filtering',
            '',
            'Three layers of filtering are applied:',
            '',
            '1. **Generic English stopwords**: the, and, our, etc.',
            '2. **Academic job-board boilerplate**: application, candidates,',
            '   faculty, university, department, professor, qualification,',
            '   experience, etc. The full list lives in `KEYWORD_STOPWORDS` near',
            '   the top of `scraper.py`.',
            '3. **Corpus-frequency bubble stopwords**: terms appearing in >80% of',
            '   job descriptions get filtered from the bubble chart display (but',
            f'   remain searchable). In the current corpus: {bubble_stop_sample}.',
            '',
            '### 3. Stemming (Recursive)',
            '',
            'A rule-based stemmer applies suffix rules repeatedly until the word',
            'stops changing. This lets "feminists" → "feminist" → "femin" all',
            'collapse to a single stem, which keeps morphological variants from',
            'fragmenting bubble groups.',
            '',
            '| Suffix | Replacement | Example |',
            '|--------|-------------|---------|',
            '| -ies   | -y          | studies → study |',
            '| -ism   | (drop)      | feminism → femin |',
            '| -ist   | (drop)      | feminist → femin |',
            '| -ing   | (drop)      | teaching → teach |',
            '| -ed    | (drop)      | tested → test |',
            '| -es    | (drop)      | classes → class |',
            '| -s     | (drop)      | ethics → ethic |',
            '',
            'Words 3 characters or shorter are not stemmed. The same stemmer runs',
            'in Python (at scrape time, for vocab building) and in JavaScript (at',
            'search time, for query expansion). The Python implementation lives in',
            '`_keyword_stem`; the JS implementation in `kwStem` — they are kept',
            'in lockstep.',
            '',
            '### 4. Synonym Expansion (Claude Haiku)',
            '',
            'Each Monday, the top 150 most frequent corpus terms are sent to Claude',
            'Haiku (`claude-haiku-4-5-20251001`, temperature=0) in batches of 25.',
            'The prompt explicitly asks for FIELD-DEFINING terms only — alternative',
            'names the academic discipline uses for the same subfield — and not',
            'broadly related or co-occurring concepts:',
            '',
            '> For each keyword below, list 4-10 FIELD-DEFINING synonyms —',
            '> alternative names the academic discipline uses for the same',
            '> subfield, research area, or concept.',
            '>',
            '> INCLUDE: morphological variants (feminism / feminist); alternative',
            '> names for the same subfield (gay / queer / LGBTQ; AI / artificial',
            '> intelligence / machine learning); standard academic terminology',
            '> that NAMES this area.',
            '>',
            "> EXCLUDE: broadly related concepts that aren't field names (e.g.",
            "> 'patriarchy' or 'intersectional' for feminism — these are concepts",
            "> WITHIN feminism, not names FOR it); co-occurring topics (e.g.",
            "> 'ethics' for race — they appear in the same postings but aren't",
            "> synonyms); generic adjectives or institutional jargon.",
            '',
            'This selective framing matters because the synonym map is the *only*',
            'source for the bubble chart (see Section 5). Loosely-related terms',
            'would produce noisy bubbles.',
            '',
            'The response is parsed, validated (must be valid JSON; non-list values',
            'are dropped), and cached to `data/synonym_map.json` and re-embedded',
            'in the dashboard. If the API call fails or the API key is missing,',
            'the dashboard still works — search falls back to stemming only.',
            '',
            'The current synonym map is documented in human-readable form at',
            '[SYNONYMS.md](SYNONYMS.md).',
            '',
            '### 5. Bubble Chart Construction',
            '',
            'When a user searches for a term, the bubble chart displays **the',
            'field-defining synonyms from the map (Section 4)**, each sized by how',
            'many jobs in the corpus contain that specific term. The bubble chart',
            'is NOT a co-occurrence visualization.',
            '',
            '1. Look up the search term in the synonym map to get its field-defining',
            '   alternatives.',
            '2. For each candidate (the query plus each synonym), stem it and count',
            '   jobs in the corpus whose stem set contains that stem.',
            '3. Display each as a bubble: the search term at the center, synonyms',
            '   around it. Bubble size is proportional to per-term job count.',
            '4. Render as a D3 force-directed simulation. Each bubble is clickable',
            '   to re-search with that term.',
            '',
            '**Why synonyms, not co-occurrence?** The purpose of the chart is to',
            'help users discover the field\'s vocabulary — "what other words does',
            'the discipline use for this concept?" — not to surface every word that',
            'happens to appear in the same job descriptions. A prior co-occurrence',
            'design produced noisy bubbles ("three" from "three letters of',
            'reference"; "online" from teaching modality; "ethics" merely because',
            'philosophy of race jobs often mention ethics). Sourcing strictly from',
            'the synonym map gives a clean signal about field-defining alternatives.',
            '',
            '**Bubble sizes are per-synonym corpus counts**, not match-set',
            "co-occurrence counts. This answers the question \"how many jobs in",
            'the corpus list this specific word?" which is what the user typically',
            'wants when assessing a field\'s market presence.',
            '',
            '### 6. Trend Chart Construction',
            '',
            'Raw count of matching jobs per week. Not normalized to total job',
            'volume — the absolute count reflects market activity in that area.',
            'Shaded background indicates the September-through-January hiring',
            'season.',
            '',
            '---',
            '',
            '## Known Limitations',
            '',
            '- **Static synonyms**: refreshed weekly, not real-time. A search for',
            '  a brand-new term will fall back to stemming only until the next',
            '  scrape.',
            '- **Small corpus in early years**: with N≈200 jobs total, individual',
            '  bubble suggestions can be statistical noise. Signal-to-noise should',
            '  improve as the dataset grows over 3 years.',
            '- **EEO false positives**: occasional substantive sentences may get',
            '  stripped if they happen to contain 2+ EEO trigger words.',
            '- **Description quality varies**: some PhilJobs postings have minimal',
            '  description text. Those jobs simply contribute fewer terms.',
            '- **Stemming is rule-based, not lexical**: words like "race" and',
            '  "racial" do NOT stem to the same form. The synonym map is intended',
            '  to bridge these gaps for important terms.',
            '- **Bubble suggestions are co-occurrence, not lift**: a term appearing',
            '  with high frequency in matching jobs may be common in *all* jobs',
            '  rather than specifically associated with the search term. A future',
            '  improvement is lift-based scoring (term overrepresentation relative',
            '  to corpus baseline).',
            '',
            '---',
            '',
            '## How to Audit a Specific Result',
            '',
            '1. **Inspect a specific job description**: open `data/all_jobs.json`,',
            '   find the job by ID, read the `description` field. This is the raw',
            '   text the keyword pipeline operates on.',
            '2. **Inspect the synonym map**: open `data/synonym_map.json` for raw',
            '   JSON, or [SYNONYMS.md](SYNONYMS.md) for a human-readable version.',
            '3. **Verify a search result**: search for any term in the live',
            '   dashboard, then check whether the listed match-count is plausible',
            '   given the corpus size and the topic.',
            '4. **Re-run locally**: clone the repo, set `ANTHROPIC_API_KEY`, run',
            '   `python scraper.py`. Everything is reproducible.',
            '5. **Inspect the code**: relevant methods in `scraper.py` are',
            '   `_strip_eeo_boilerplate`, `_extract_description_terms`,',
            '   `build_keyword_index`, `generate_synonym_map`, `_keyword_stem`.',
            '',
            '---',
            '',
            '## Change Log',
            '',
            f'- **{date_str}**: Taxonomy revised to add four subcategories from a',
            '  cross-source review against PhilPapers and APA submission tracks:',
            '  Virtue Ethics (under Ethics), Philosophy of Disability and Public',
            '  Philosophy (under Social & Political), and Phenomenology (under',
            '  History of Philosophy). One redundant duplicate removed: "Social',
            '  & Political Philosophy (General)" — the unified "Social and',
            '  Political Philosophy (General / Political Theory)" remains as the',
            '  catchall. All existing jobs were reclassified under the new',
            '  taxonomy; prior classifications preserved on each job under',
            '  `classification_v1`. Taxonomy version bumped to `2026-05-16`.',
            f'- **{date_str}**: Bubble chart rewritten to source from the Claude-',
            '  generated synonym map (field-defining alternatives) rather than from',
            '  corpus co-occurrence. Each bubble is now sized by per-term corpus',
            '  count. The Claude synonym prompt was tightened to ask only for',
            '  field-defining names (gay/queer/LGBTQ) and exclude broadly related',
            '  concepts (patriarchy/intersectional for feminism). Stemmer changed',
            '  from single-pass to recursive so morphological variants collapse',
            '  to a single stem ("feminists" → "feminist" → "femin"). Rationale:',
            '  the prior co-occurrence approach surfaced noise like "three" (from',
            '  "three letters of reference") and "ethics" merely because race-',
            '  related jobs often also discuss ethics. The new approach answers a',
            '  more focused question — "what are the field\'s alternative names',
            '  for this concept, and how many jobs use each?"',
            f'- **{date_str}**: Initial documented version of the methodology.',
            '',
        ]
        out_file = docs_dir / 'KEYWORD_EXPLORER_METHODOLOGY.md'
        out_file.write_text('\n'.join(lines))
        print(f"  Methodology doc written → {out_file}")

    def _compute_weekly_series(self, jobs_by_date, dates):
        """Compute per-week chart series from jobs grouped by date key (YYYY-MM-DD).

        AOS-based series carry three parallel slices so charts can filter by
        AOS-listing pattern:
            all   = every main_aos tag on every job contributes +1
            solo  = +1 only when a job has exactly one main_aos category
            joint = +1 for each main_aos tag when the job has >1 main_aos
        By construction: solo + joint = all for any cell.
        """
        modes = ('all', 'solo', 'joint')
        parent_categories = {
            cat: {
                'dataAll': [], 'dataSolo': [], 'dataJoint': [],
                'subcategories': DETAIL_AOS.get(cat, []),
                'color': MAIN_AOS_COLORS.get(cat, '#6b7280')
            }
            for cat in MAIN_AOS_CATEGORIES
        }
        subcategory_data = {
            detail: {'all': [], 'solo': [], 'joint': []}
            for cat in MAIN_AOS_CATEGORIES
            for detail in DETAIL_AOS.get(cat, [])
        }
        # Per-week position-type counts, sliced by AOS-listing pattern
        job_type_series = {
            pt: {'all': [], 'solo': [], 'joint': []} for pt in POSITION_TYPES
        }
        position_type_by_aos_weekly = {
            aos: {pt: {'all': [], 'solo': [], 'joint': []} for pt in POSITION_TYPES}
            for aos in MAIN_AOS_CATEGORIES
        }
        inst_type_series = {'Research University': [], 'Teaching College': [], 'Other': []}
        total_new_jobs_weekly = {'all': [], 'solo': [], 'joint': []}

        for date in dates:
            date_key = date[:10]
            week_jobs = jobs_by_date.get(date_key, [])

            main_counts = {m: defaultdict(int) for m in modes}
            detail_counts = {m: defaultdict(int) for m in modes}
            week_totals = {'all': 0, 'solo': 0, 'joint': 0}
            # Per-week position-type counters, also three-way sliced
            pt_counts = {m: defaultdict(int) for m in modes}
            pt_by_aos = {m: defaultdict(lambda: defaultdict(int)) for m in modes}
            it_counts = defaultdict(int)

            for job in week_jobs:
                cls = job.get('classification') or {}
                main_list = cls.get('main_aos', ['Open'])
                mode_key = 'solo' if len(main_list) == 1 else 'joint'
                week_totals['all'] += 1
                week_totals[mode_key] += 1
                for main in main_list:
                    main_counts['all'][main] += 1
                    main_counts[mode_key][main] += 1
                for main, details in cls.get('detail_aos', {}).items():
                    for detail in details:
                        key = f"{main}::{detail}"
                        detail_counts['all'][key] += 1
                        detail_counts[mode_key][key] += 1
                raw_pt = (cls.get('position_type')
                          or JOB_TYPE_MIGRATION.get(cls.get('job_type', ''), None)
                          or job.get('job_type', 'Other'))
                pos_type = raw_pt if raw_pt in POSITION_TYPES else 'Other'
                pt_counts['all'][pos_type] += 1
                pt_counts[mode_key][pos_type] += 1
                for main in main_list:
                    pt_by_aos['all'][main][pos_type] += 1
                    pt_by_aos[mode_key][main][pos_type] += 1
                it = cls.get('institution_type') or job.get('institution_type', 'Other')
                it_counts[it] += 1

            for m in modes:
                total_new_jobs_weekly[m].append(week_totals[m])
            for cat in MAIN_AOS_CATEGORIES:
                parent_categories[cat]['dataAll'].append(main_counts['all'].get(cat, 0))
                parent_categories[cat]['dataSolo'].append(main_counts['solo'].get(cat, 0))
                parent_categories[cat]['dataJoint'].append(main_counts['joint'].get(cat, 0))
            for cat in MAIN_AOS_CATEGORIES:
                for detail in DETAIL_AOS.get(cat, []):
                    key = f"{cat}::{detail}"
                    subcategory_data[detail]['all'].append(detail_counts['all'].get(key, 0))
                    subcategory_data[detail]['solo'].append(detail_counts['solo'].get(key, 0))
                    subcategory_data[detail]['joint'].append(detail_counts['joint'].get(key, 0))
            for pt in POSITION_TYPES:
                for m in modes:
                    job_type_series[pt][m].append(pt_counts[m].get(pt, 0))
            for aos in MAIN_AOS_CATEGORIES:
                for pt in POSITION_TYPES:
                    for m in modes:
                        position_type_by_aos_weekly[aos][pt][m].append(pt_by_aos[m].get(aos, {}).get(pt, 0))
            for it in ['Research University', 'Teaching College', 'Other']:
                inst_type_series[it].append(it_counts.get(it, 0))

        return {
            'parent_categories': parent_categories,
            'subcategory_data': subcategory_data,
            'job_type_series': job_type_series,
            'position_type_by_aos_weekly': position_type_by_aos_weekly,
            'inst_type_series': inst_type_series,
            'total_new_jobs_weekly': total_new_jobs_weekly,
        }

    # ── Dashboard ─────────────────────────────────────────────────────────

    def is_hiring_season(self, date_str):
        date = datetime.strptime(date_str, "%Y-%m-%d")
        return date.month >= 9 or date.month <= 1

    def generate_trend_dashboard(self, historical_data):
        """Generate US-only HTML dashboard (docs/index.html)."""
        trends = historical_data.get('weekly_trends', [])
        if not trends:
            print("No data available yet for dashboard visualization")
            return

        all_jobs = historical_data.get('jobs', [])
        dates = [t['date'] for t in trends]

        # ── Filter to US jobs only ───────────────────────────────────────
        us_jobs = [j for j in all_jobs if j.get('state')]

        # Group US jobs by date key (YYYY-MM-DD)
        jobs_by_date = defaultdict(list)
        for job in us_jobs:
            date_key = job.get('scraped_date', '')[:10]
            jobs_by_date[date_key].append(job)

        # ── Weekly series ────────────────────────────────────────────────
        series = self._compute_weekly_series(jobs_by_date, dates)
        parent_categories    = series['parent_categories']
        subcategory_data     = series['subcategory_data']
        job_type_series      = series['job_type_series']
        position_type_by_aos_weekly = series['position_type_by_aos_weekly']
        inst_type_series     = series['inst_type_series']
        total_new_jobs_weekly = series['total_new_jobs_weekly']

        # ── Geographic data (US-specific) ────────────────────────────────
        # State-level weekly counts sliced by AOS-listing pattern so the
        # state-click popup can filter by All / Solo / Joint.
        state_data = {state: {'all': [], 'solo': [], 'joint': []} for state in US_STATES.values()}
        for date in dates:
            date_key = date[:10]
            week_jobs = jobs_by_date.get(date_key, [])
            sc = {m: defaultdict(int) for m in ('all', 'solo', 'joint')}
            for job in week_jobs:
                s = job.get('state')
                if not s:
                    continue
                cls = job.get('classification') or {}
                main_list = cls.get('main_aos', ['Open'])
                mode_key = 'solo' if len(main_list) == 1 else 'joint'
                sc['all'][s] += 1
                sc[mode_key][s] += 1
            for state_code in US_STATES.values():
                state_data[state_code]['all'].append(sc['all'].get(state_code, 0))
                state_data[state_code]['solo'].append(sc['solo'].get(state_code, 0))
                state_data[state_code]['joint'].append(sc['joint'].get(state_code, 0))

        # West Coast Spotlight — cumulative AOS breakdown by city and by metro,
        # tracked three ways so the chart can toggle between All / Solo / Joint.
        #   _all   = every main_aos tag on every job contributes +1
        #   _solo  = +1 only when a job has exactly one main_aos category
        #   _joint = +1 for each main_aos category when the job has more than one
        # By construction: solo + joint = all
        wc_city_aos = {'all': defaultdict(lambda: defaultdict(int)),
                       'solo': defaultdict(lambda: defaultdict(int)),
                       'joint': defaultdict(lambda: defaultdict(int))}
        wc_metro_aos = {'all': defaultdict(lambda: defaultdict(int)),
                        'solo': defaultdict(lambda: defaultdict(int)),
                        'joint': defaultdict(lambda: defaultdict(int))}
        west_coast_metro_cities = defaultdict(set)

        for job in us_jobs:
            state = job.get('state')
            city = job.get('city')
            if state not in ('CA', 'OR', 'WA') or not city:
                continue
            metro = get_west_coast_metro(city, state)
            if not metro:
                continue
            classification = job.get('classification') or {}
            main_list = classification.get('main_aos', ['Open'])
            mode_key = 'solo' if len(main_list) == 1 else 'joint'
            for main in main_list:
                wc_city_aos['all'][city][main] += 1
                wc_metro_aos['all'][metro][main] += 1
                wc_city_aos[mode_key][city][main] += 1
                wc_metro_aos[mode_key][metro][main] += 1
            west_coast_metro_cities[metro].add(city)

        def _serialize_aos(d):
            return {mode: {loc: dict(aos) for loc, aos in d[mode].items()} for mode in ('all', 'solo', 'joint')}

        west_coast_city_aos = _serialize_aos(wc_city_aos)
        west_coast_metro_aos = _serialize_aos(wc_metro_aos)
        west_coast_metro_cities = {k: sorted(list(v)) for k, v in west_coast_metro_cities.items()}

        # Regional trends — three parallel slices (all/solo/joint) so the chart
        # can filter by AOS-listing pattern just like Market Overview.
        # Build state→region lookup for O(1) classification.
        state_to_region = {s: r for r, states in US_REGIONS.items() for s in states}
        region_data = {region: {'all': [0] * len(dates), 'solo': [0] * len(dates), 'joint': [0] * len(dates)}
                       for region in US_REGIONS}
        for i, date in enumerate(dates):
            date_key = date[:10]
            for job in jobs_by_date.get(date_key, []):
                state = job.get('state')
                region = state_to_region.get(state)
                if not region:
                    continue
                cls = job.get('classification') or {}
                main_list = cls.get('main_aos', ['Open'])
                mode_key = 'solo' if len(main_list) == 1 else 'joint'
                region_data[region]['all'][i] += 1
                region_data[region][mode_key][i] += 1

        # state_alltime drives map color shading — use the 'all' slice for total
        state_alltime = {s: sum(v['all']) for s, v in state_data.items() if sum(v['all']) > 0}

        # ── State → AOS breakdown (with solo/joint slicing) ──────────────
        state_cat_map = {m: defaultdict(lambda: defaultdict(int)) for m in ('all', 'solo', 'joint')}
        for job in us_jobs:
            s = job.get('state')
            cls = job.get('classification')
            if not s or not cls:
                continue
            main_list = cls.get('main_aos', [])
            mode_key = 'solo' if len(main_list) == 1 else 'joint'
            for main in main_list:
                state_cat_map['all'][s][main] += 1
                state_cat_map[mode_key][s][main] += 1
        state_category_data = {m: {k: dict(v) for k, v in state_cat_map[m].items()}
                               for m in ('all', 'solo', 'joint')}

        # ── Subcategory → job IDs + full job details (for PDF download) ──
        # Per-subcategory list of matching jobs and an id-keyed dict with all
        # the fields the download report needs. Used by the Browse by Category
        # modal's "Download report" button per subcategory.
        subcategory_job_ids = defaultdict(list)
        job_details_map = {}
        for job in us_jobs:
            jid = job.get('id')
            if not jid:
                continue
            cls = job.get('classification') or {}
            for main, details in cls.get('detail_aos', {}).items():
                for detail in details:
                    if jid not in subcategory_job_ids[detail]:
                        subcategory_job_ids[detail].append(jid)
            job_details_map[jid] = {
                'id': jid,
                'url': job.get('url', ''),
                'institution': job.get('institution', ''),
                'title': job.get('title', ''),
                'job_category': job.get('job_category', ''),
                'aos': job.get('aos', ''),
                'aoc': job.get('aoc', ''),
                'location': job.get('location', ''),
                'workload': job.get('workload', ''),
                'vacancies': job.get('vacancies', ''),
                'deadline': job.get('deadline', ''),
                'start_date': job.get('start_date', ''),
                'posted_date': job.get('posted_date', ''),
                'application_type': job.get('application_type', ''),
                'application_url': job.get('application_url', ''),
                'contact_email': job.get('contact_email', ''),
                'description': job.get('description', ''),
                'job_type': job.get('job_type', ''),
            }
        subcategory_job_ids = {k: list(v) for k, v in subcategory_job_ids.items()}

        # ── Position type × AOS all-time (with solo/joint slicing) ───────
        pos_type_x_aos_map = {m: defaultdict(lambda: defaultdict(int)) for m in ('all', 'solo', 'joint')}
        for job in us_jobs:
            cls = job.get('classification')
            if not cls:
                continue
            raw_pt = (cls.get('position_type')
                      or JOB_TYPE_MIGRATION.get(cls.get('job_type', ''), None)
                      or job.get('job_type', 'Other'))
            pos_type = raw_pt if raw_pt in POSITION_TYPES else 'Other'
            main_list = cls.get('main_aos', [])
            mode_key = 'solo' if len(main_list) == 1 else 'joint'
            for main in main_list:
                pos_type_x_aos_map['all'][main][pos_type] += 1
                pos_type_x_aos_map[mode_key][main][pos_type] += 1
        pos_type_x_aos = {m: {k: dict(v) for k, v in pos_type_x_aos_map[m].items()} for m in ('all', 'solo', 'joint')}

        # ── Co-occurrence ─────────────────────────────────────────────────
        cooc = self._compute_cooc_from_jobs(us_jobs)

        # ── Keyword Explorer index + synonym map (US) ────────────────────
        print("Building US keyword index + synonym map...")
        keyword_index, kw_vocab, bubble_stopwords = self.build_keyword_index(us_jobs)
        synonym_map = self.generate_synonym_map(kw_vocab)

        # ── Summary stats ─────────────────────────────────────────────────
        last_date_key = dates[-1][:10] if dates else ''
        last_week_jobs = jobs_by_date.get(last_date_key, [])
        current_week_new_jobs = len(last_week_jobs)
        total_unique_jobs = len(us_jobs)
        weeks_tracked = len(dates)

        last_main = defaultdict(int)
        for job in last_week_jobs:
            cls = job.get('classification') or {}
            for main in cls.get('main_aos', ['Open']):
                last_main[main] += 1
        most_active = max(last_main, key=last_main.get) if last_main else "—"

        seasonal_markers = []
        for i, date in enumerate(dates):
            if self.is_hiring_season(date):
                seasonal_markers.append({'index': i, 'label': 'Hiring Season'})

        # ── Pre-serialise complex JS objects ─────────────────────────────
        categories_js = json.dumps({
            k: {
                'name': k,
                'dataAll': v['dataAll'], 'dataSolo': v['dataSolo'], 'dataJoint': v['dataJoint'],
                'subcategories': v['subcategories'],
                'color': v['color']
            }
            for k, v in parent_categories.items()
        })

        # ── Build HTML ────────────────────────────────────────────────────
        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>US Philosophy Job Market Analytics</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/d3@7"></script>
    <script src="https://cdn.jsdelivr.net/npm/topojson-client@3"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        body {{ font-family: 'Inter', sans-serif; }}
        .category-card:hover {{ transform: translateY(-2px); transition: all 0.3s; }}
        .stat-card {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }}
        .chart-container {{ min-height: 400px; }}
        #mapTooltip {{ display:none; position:fixed; background:rgba(0,0,0,0.8); color:white; padding:6px 10px; border-radius:6px; font-size:13px; pointer-events:none; z-index:1000; line-height:1.5; }}
        #stateDetailPanel {{ transition: transform 0.2s; }}
    </style>
</head>
<body class="bg-gray-50">
    <!-- Tab Navigation -->
    <div class="bg-white border-b border-gray-200 sticky top-0 z-40 shadow-sm">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex gap-1 py-2">
                <a href="index.html" class="px-5 py-2 text-sm font-semibold rounded-lg bg-indigo-600 text-white">🇺🇸 US Market</a>
                <a href="international.html" class="px-5 py-2 text-sm font-semibold rounded-lg text-gray-600 hover:bg-gray-100 transition-colors">🌍 International</a>
            </div>
        </div>
    </div>
    <div class="bg-gradient-to-r from-indigo-600 to-purple-600 text-white">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
            <h1 class="text-4xl font-bold mb-2">US Philosophy Job Market Analytics</h1>
            <p class="text-indigo-100">Real-time trends from PhilJobs — U.S. institutions only</p>
            <div class="mt-6 text-sm text-indigo-100">Last updated: {datetime.now().strftime("%B %d, %Y")}</div>
        </div>
    </div>

    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">

        <!-- Stats Cards -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-6 mb-8">
            <div class="stat-card rounded-xl shadow-lg p-6 text-white col-span-2 md:col-span-1">
                <div class="text-3xl font-bold">{current_week_new_jobs}</div>
                <div class="text-indigo-100">New US Jobs This Week</div>
            </div>
            <div class="bg-white rounded-xl shadow-lg p-6">
                <div class="text-3xl font-bold text-gray-800">{total_unique_jobs}</div>
                <div class="text-gray-600">Total US Jobs Tracked</div>
            </div>
            <div class="bg-white rounded-xl shadow-lg p-6">
                <div class="text-2xl font-bold text-gray-800 truncate">{most_active}</div>
                <div class="text-gray-600">Most Active This Week</div>
            </div>
            <div class="bg-white rounded-xl shadow-lg p-6">
                <div class="text-3xl font-bold text-gray-800">{weeks_tracked}</div>
                <div class="text-gray-600">Weeks Tracked</div>
            </div>
        </div>

        <!-- Market Overview -->
        <div class="bg-white rounded-xl shadow-lg p-6 mb-8">
            <div class="flex items-start justify-between mb-3 flex-wrap gap-3">
                <div>
                    <h2 class="text-2xl font-bold text-gray-800 mb-1">Market Overview</h2>
                    <p class="text-sm text-gray-500">New US jobs per week by main AOS category — shaded areas = hiring season (Sept–Jan). Toggle filters by solo (single-AOS) vs. joint (multi-AOS) listings.</p>
                </div>
                <div class="flex flex-col items-end gap-2">
                    <div class="inline-flex rounded-lg overflow-hidden border border-gray-300 bg-white">
                        <button id="marketModeAll" type="button" onclick="setMarketMode('all')" class="px-3 py-1.5 text-sm font-medium bg-indigo-600 text-white">All</button>
                        <button id="marketModeSolo" type="button" onclick="setMarketMode('solo')" class="px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-indigo-50">Solo</button>
                        <button id="marketModeJoint" type="button" onclick="setMarketMode('joint')" class="px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-indigo-50">Joint</button>
                    </div>
                    <div id="marketModeNote" class="text-xs text-gray-500 italic"></div>
                </div>
            </div>
            <div class="chart-container">
                <canvas id="mainChart"></canvas>
            </div>
        </div>

        <!-- Regional Trends -->
        <div class="bg-white rounded-xl shadow-lg p-6 mb-8">
            <div class="flex items-start justify-between mb-3 flex-wrap gap-3">
                <div>
                    <h2 class="text-2xl font-bold text-gray-800 mb-1">Regional Trends</h2>
                    <p class="text-sm text-gray-500">New jobs per week by US region — West highlighted in blue. Toggle filters by solo (single-AOS) vs. joint (multi-AOS) listings.</p>
                </div>
                <div class="flex flex-col items-end gap-2">
                    <div class="inline-flex rounded-lg overflow-hidden border border-gray-300 bg-white">
                        <button id="regionModeAll" type="button" onclick="setRegionMode('all')" class="px-3 py-1.5 text-sm font-medium bg-indigo-600 text-white">All</button>
                        <button id="regionModeSolo" type="button" onclick="setRegionMode('solo')" class="px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-indigo-50">Solo</button>
                        <button id="regionModeJoint" type="button" onclick="setRegionMode('joint')" class="px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-indigo-50">Joint</button>
                    </div>
                    <div id="regionModeNote" class="text-xs text-gray-500 italic"></div>
                </div>
            </div>
            <div class="chart-container">
                <canvas id="regionalChart"></canvas>
            </div>
        </div>

        <!-- Co-Occurrence Matrix -->
        <div class="bg-white rounded-xl shadow-lg p-6 mb-8">
            <h2 class="text-2xl font-bold text-gray-800 mb-1">AOS Co-Occurrence Matrix</h2>
            <p class="text-sm text-gray-500 mb-4">How often main AOS categories appear together in the same job posting (all-time counts). Darker = more frequent co-occurrence.</p>
            <div id="coocMatrixTable" class="overflow-x-auto text-sm"></div>
        </div>

        <!-- Solo vs. Joint -->
        <div class="bg-white rounded-xl shadow-lg p-6 mb-8">
            <h2 class="text-2xl font-bold text-gray-800 mb-1">Solo vs. Joint Hiring</h2>
            <p class="text-sm text-gray-500 mb-4">For each main AOS, jobs listing it as the <em>only</em> area (solo) versus alongside other areas (joint) — after Lassiter (2023)</p>
            <div style="min-height:300px;">
                <canvas id="soloJointChart"></canvas>
            </div>
        </div>

        <!-- Keyword Explorer -->
        <div class="bg-white rounded-xl shadow-lg p-6 mb-8">
            <div class="flex items-start justify-between mb-2 flex-wrap gap-3">
                <div class="flex items-center gap-2">
                    <h2 class="text-2xl font-bold text-gray-800">Keyword Explorer</h2>
                    <span class="relative inline-block group" tabindex="0">
                        <span class="inline-flex items-center justify-center w-5 h-5 rounded-full bg-gray-200 text-gray-600 text-xs font-bold cursor-help">i</span>
                        <span class="invisible group-hover:visible group-focus-within:visible absolute left-7 top-0 z-30 w-72 bg-gray-900 text-white text-xs rounded-lg p-3 shadow-lg leading-relaxed">
                            <strong>What this searches:</strong> the full job description text only. AOS / AOC labels and titles are <em>not</em> searched. This is intentional — it measures what jobs describe themselves as doing, not how they're labeled, which can diverge under political and institutional pressure.
                        </span>
                    </span>
                </div>
            </div>
            <p class="text-sm text-gray-500 mb-4">Search any term to see (1) related vocabulary used in matching jobs, and (2) how often that area appears in postings over time. Synonyms expand automatically (e.g. "feminism" matches "feminist").</p>
            <div class="flex items-center gap-3 mb-4 flex-wrap">
                <input id="kwInput" type="text" placeholder="Try: feminism, queer, AI, race, environmental, history..." class="flex-1 min-w-[200px] px-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400" />
                <button id="kwSearchBtn" type="button" class="px-5 py-2 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-700">Search</button>
                <div id="kwMatchCount" class="text-sm text-gray-600"></div>
            </div>
            <div id="kwEmptyState" class="text-center py-12 text-gray-400 text-sm">
                Type a term above to begin. Click any bubble to explore related searches.
            </div>
            <div id="kwResults" class="hidden grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div>
                    <h3 class="text-sm font-semibold text-gray-700 mb-2">Vocabulary Neighborhood</h3>
                    <p class="text-xs text-gray-500 mb-2">Terms commonly appearing in matching descriptions. Click any bubble to search that term.</p>
                    <div id="kwBubble" style="height:340px;"></div>
                </div>
                <div>
                    <h3 class="text-sm font-semibold text-gray-700 mb-2">Trend Over Time</h3>
                    <p class="text-xs text-gray-500 mb-2">Matching jobs per week. Shaded areas = hiring season.</p>
                    <div style="height:340px;"><canvas id="kwTrendChart"></canvas></div>
                </div>
            </div>
            <div class="text-xs text-gray-400 mt-4 text-right">
                <a href="SYNONYMS.md" target="_blank" class="hover:underline">Full synonym list</a>
                &middot;
                <a href="KEYWORD_EXPLORER_METHODOLOGY.md" target="_blank" class="hover:underline">Methodology &amp; audit</a>
            </div>
        </div>

        <!-- Geographic Overview -->
        <div class="bg-white rounded-xl shadow-lg p-6 mb-8">
            <div class="flex flex-wrap justify-between items-center mb-6 gap-4">
                <div>
                    <h2 class="text-2xl font-bold text-gray-800">Geographic Overview</h2>
                    <p class="text-sm text-gray-500 mt-1">Click any state for a detailed breakdown — West Coast highlighted in blue</p>
                </div>
                <div class="flex gap-2">
                    <button id="mapModeNew" onclick="setMapMode('current')" class="px-4 py-2 text-sm font-medium rounded-lg bg-indigo-600 text-white">New This Week</button>
                    <button id="mapModeAll" onclick="setMapMode('alltime')" class="px-4 py-2 text-sm font-medium rounded-lg bg-gray-200 text-gray-700">All-Time</button>
                </div>
            </div>
            <div id="usMapEl" class="bg-gray-50 rounded-lg overflow-hidden" style="height:400px;">
                <div class="flex items-center justify-center h-full text-gray-400 text-sm">Loading map...</div>
            </div>
        </div>

        <!-- Position Type Trends -->
        <div class="bg-white rounded-xl shadow-lg p-6 mb-8">
            <div class="flex flex-wrap justify-between items-start mb-2 gap-4">
                <div>
                    <h2 class="text-2xl font-bold text-gray-800">Position Type Trends</h2>
                    <p class="text-sm text-gray-500 mt-1">New jobs per week by position type — filter by AOS to see hiring patterns within each area. Toggle filters by solo (single-AOS) vs. joint (multi-AOS) listings.</p>
                </div>
                <div class="flex flex-col items-end gap-2">
                    <div class="flex flex-wrap gap-2 justify-end">
                        <select id="posTypeAosFilter" onchange="updatePositionTypeChart()" class="text-sm border border-gray-300 rounded-lg px-3 py-2 text-gray-700 bg-white focus:outline-none focus:ring-2 focus:ring-cyan-400">
                            <option value="__all__">All AOS</option>
                        </select>
                        <div class="inline-flex rounded-lg overflow-hidden border border-gray-300 bg-white">
                            <button id="posTypeModeAll" type="button" onclick="setPosTypeMode('all')" class="px-3 py-1.5 text-sm font-medium bg-indigo-600 text-white">All</button>
                            <button id="posTypeModeSolo" type="button" onclick="setPosTypeMode('solo')" class="px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-indigo-50">Solo</button>
                            <button id="posTypeModeJoint" type="button" onclick="setPosTypeMode('joint')" class="px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-indigo-50">Joint</button>
                        </div>
                    </div>
                    <div id="posTypeModeNote" class="text-xs text-gray-500 italic"></div>
                </div>
            </div>
            <div class="chart-container mb-6">
                <canvas id="posTypeChart"></canvas>
            </div>
            <div id="posTypeTable" class="overflow-x-auto text-sm mt-4"></div>
        </div>

        <!-- West Coast Spotlight -->
        <div class="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl shadow-lg p-6 mb-8 border border-blue-100">
            <div class="flex items-start justify-between mb-3 flex-wrap gap-3">
                <div>
                    <h2 class="text-2xl font-bold text-gray-800 mb-1">🌊 West Coast Spotlight</h2>
                    <p class="text-sm text-gray-500">Cumulative AOS breakdown for CA, OR, WA. Toggle between metro areas and individual cities; filter by solo (single-AOS) vs. joint (multi-AOS) listings. Click any metro bar to drill into its cities.</p>
                </div>
                <div class="flex flex-col items-end gap-2">
                    <div class="flex gap-2 flex-wrap justify-end">
                        <div class="inline-flex rounded-lg overflow-hidden border border-blue-200 bg-white">
                            <button id="wcViewMetro" type="button" onclick="setWcView('metro')" class="px-4 py-1.5 text-sm font-medium bg-blue-600 text-white">Metro</button>
                            <button id="wcViewCity" type="button" onclick="setWcView('city')" class="px-4 py-1.5 text-sm font-medium text-gray-700 hover:bg-blue-50">City</button>
                        </div>
                        <div class="inline-flex rounded-lg overflow-hidden border border-blue-200 bg-white">
                            <button id="wcModeAll" type="button" onclick="setWcMode('all')" class="px-3 py-1.5 text-sm font-medium bg-blue-600 text-white">All</button>
                            <button id="wcModeSolo" type="button" onclick="setWcMode('solo')" class="px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-blue-50">Solo</button>
                            <button id="wcModeJoint" type="button" onclick="setWcMode('joint')" class="px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-blue-50">Joint</button>
                        </div>
                    </div>
                    <div id="wcFilterIndicator" class="text-xs text-gray-600 hidden"></div>
                    <div id="wcModeNote" class="text-xs text-gray-500 italic"></div>
                </div>
            </div>
            <div class="chart-container" style="min-height: 380px;">
                <canvas id="westCoastChart"></canvas>
            </div>
        </div>

        <!-- Category Cards -->
        <div class="bg-white rounded-xl shadow-lg p-6 mb-8">
            <h2 class="text-2xl font-bold text-gray-800 mb-6">Browse by Category</h2>
            <div id="categoryGrid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"></div>
        </div>

        <!-- Category Detail Modal -->
        <div id="detailModal" class="hidden fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
            <div class="bg-white rounded-xl shadow-2xl max-w-6xl w-full max-h-[90vh] overflow-y-auto">
                <div class="sticky top-0 bg-white border-b px-6 py-4 flex justify-between items-center z-10">
                    <h3 id="modalTitle" class="text-2xl font-bold text-gray-800"></h3>
                    <button onclick="closeModal()" class="text-gray-400 hover:text-gray-600">
                        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                        </svg>
                    </button>
                </div>
                <div class="p-6">
                    <div id="subcategorySection" class="mb-6">
                        <h4 class="text-lg font-semibold text-gray-700 mb-4">Subcategories</h4>
                        <div id="subcategoryGrid" class="grid grid-cols-2 md:grid-cols-3 gap-3 mb-6"></div>
                    </div>
                    <div class="mb-6">
                        <h4 class="text-lg font-semibold text-gray-700 mb-4">Trend Over Time</h4>
                        <div class="chart-container"><canvas id="detailChart"></canvas></div>
                    </div>
                    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                        <div class="bg-gray-50 rounded-lg p-4">
                            <div class="text-2xl font-bold text-indigo-600" id="modalCurrentJobs">0</div>
                            <div class="text-sm text-gray-600">New Jobs This Week</div>
                        </div>
                        <div class="bg-gray-50 rounded-lg p-4">
                            <div class="text-2xl font-bold text-green-600" id="modalChange">+0</div>
                            <div class="text-sm text-gray-600">vs Last Week</div>
                        </div>
                        <div class="bg-gray-50 rounded-lg p-4">
                            <div class="text-2xl font-bold text-purple-600" id="modalAverage">0</div>
                            <div class="text-sm text-gray-600">Weekly Average</div>
                        </div>
                        <div class="bg-gray-50 rounded-lg p-4">
                            <div class="text-2xl font-bold text-blue-600" id="modalTotal">0</div>
                            <div class="text-sm text-gray-600">Total All-Time</div>
                        </div>
                    </div>
                    <div id="lassiterSection" class="mb-6">
                        <h4 class="text-lg font-semibold text-gray-700 mb-3">Solo vs. Joint by Subcategory</h4>
                        <div id="lassiterChart" class="overflow-x-auto text-sm"></div>
                    </div>
                    <div class="mb-6 max-w-md">
                        <h4 class="text-lg font-semibold text-gray-700 mb-4">Institution Types</h4>
                        <canvas id="institutionChart"></canvas>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <div id="mapTooltip"></div>

    <!-- State Detail Panel -->
    <div id="stateDetailPanel" class="hidden fixed top-0 right-0 h-full w-80 bg-white shadow-2xl z-50 overflow-y-auto border-l border-gray-200">
        <div class="p-5">
            <div class="flex justify-between items-center mb-4">
                <h3 id="statePanelTitle" class="text-xl font-bold text-gray-800"></h3>
                <button onclick="closeStatePanel()" class="text-gray-400 hover:text-gray-600 text-2xl leading-none">&times;</button>
            </div>
            <div class="inline-flex w-full rounded-lg overflow-hidden border border-gray-300 bg-white mb-3">
                <button id="stateModeAll" type="button" onclick="setStateMode('all')" class="flex-1 px-3 py-1.5 text-sm font-medium bg-indigo-600 text-white">All</button>
                <button id="stateModeSolo" type="button" onclick="setStateMode('solo')" class="flex-1 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-indigo-50">Solo</button>
                <button id="stateModeJoint" type="button" onclick="setStateMode('joint')" class="flex-1 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-indigo-50">Joint</button>
            </div>
            <div id="stateModeNote" class="text-xs text-gray-500 italic mb-3"></div>
            <div class="grid grid-cols-2 gap-3 mb-4">
                <div class="bg-indigo-50 rounded-lg p-3 text-center">
                    <div class="text-2xl font-bold text-indigo-600" id="stateNewJobs">0</div>
                    <div class="text-xs text-gray-500 mt-1">New This Week</div>
                </div>
                <div class="bg-gray-50 rounded-lg p-3 text-center">
                    <div class="text-2xl font-bold text-gray-800" id="stateTotalJobs">0</div>
                    <div class="text-xs text-gray-500 mt-1">All-Time Total</div>
                </div>
            </div>
            <h4 class="text-sm font-semibold text-gray-700 mb-2">Weekly Trend</h4>
            <div style="height:140px;" class="mb-4"><canvas id="stateTrendChart"></canvas></div>
            <h4 class="text-sm font-semibold text-gray-700 mb-2">By Category (All-Time)</h4>
            <div id="stateCategoryBreakdown" class="space-y-1"></div>
        </div>
    </div>

    <script>
        const data = {{
            dates: {json.dumps(dates)},
            totalNewJobsWeekly: {json.dumps(total_new_jobs_weekly)},
            categories: {categories_js},
            subcategoryData: {json.dumps(subcategory_data)},
            jobTypeData: {json.dumps(job_type_series)},
            institutionTypeData: {json.dumps(inst_type_series)},
            stateData: {json.dumps(state_data)},
            westCoastCityAos: {json.dumps(west_coast_city_aos)},
            westCoastMetroAos: {json.dumps(west_coast_metro_aos)},
            westCoastMetroCities: {json.dumps(west_coast_metro_cities)},
            seasonalMarkers: {json.dumps(seasonal_markers)},
            regionData: {json.dumps(region_data)},
            stateAlltime: {json.dumps(state_alltime)},
            stateCategoryData: {json.dumps(state_category_data)},
            positionTypeByAosWeekly: {json.dumps(position_type_by_aos_weekly)},
            positionTypeXAos: {json.dumps(pos_type_x_aos)},
            positionTypes: {json.dumps(POSITION_TYPES)},
            positionTypeColors: {json.dumps(POSITION_TYPE_COLORS)},
            mainAosColors: {json.dumps(MAIN_AOS_COLORS)},
            mainAosCategories: {json.dumps(MAIN_AOS_CATEGORIES)},
            coocMatrix: {json.dumps(cooc.get('main_aos_matrix', {}))},
            soloVsJoint: {json.dumps(cooc.get('main_aos_solo_vs_joint', {}))},
            crossCutting: {json.dumps(cooc.get('cross_cutting_areas', {}))},
            detailAosByContext: {json.dumps(cooc.get('detail_aos_by_context', {}))},
            jobsForKeyword: {json.dumps(keyword_index)},
            synonymMap: {json.dumps(synonym_map)},
            bubbleStopwords: {json.dumps(bubble_stopwords)},
            subcategoryJobIds: {json.dumps(subcategory_job_ids)},
            jobDetails: {json.dumps(job_details_map)}
        }};

        // ===== SEASON PLUGIN =====
        const seasonPlugin = {{
            id: 'seasonBackground',
            beforeDraw(chart) {{
                const {{ ctx, chartArea, scales }} = chart;
                if (!chartArea || !scales.x) return;
                ctx.save();
                data.seasonalMarkers.forEach(m => {{
                    const x0 = scales.x.getPixelForValue(m.index - 0.5);
                    const x1 = scales.x.getPixelForValue(m.index + 0.5);
                    ctx.fillStyle = 'rgba(251, 191, 36, 0.15)';
                    ctx.fillRect(x0, chartArea.top, x1 - x0, chartArea.bottom - chartArea.top);
                }});
                ctx.restore();
            }}
        }};

        // ===== MARKET OVERVIEW MODE STATE =====
        // 'all' = every AOS tag counts; 'solo' = single-AOS jobs only;
        // 'joint' = multi-AOS jobs only (each tag still counts).
        let marketMode = 'all';
        let mainChart = null;
        let currentModalKey = null;

        function catDataFor(cat, mode) {{
            mode = mode || marketMode;
            if (mode === 'solo') return cat.dataSolo;
            if (mode === 'joint') return cat.dataJoint;
            return cat.dataAll;
        }}
        function subDataFor(sub, mode) {{
            mode = mode || marketMode;
            const slot = data.subcategoryData[sub] || {{}};
            return slot[mode] || [];
        }}
        function totalDataFor(mode) {{
            mode = mode || marketMode;
            return data.totalNewJobsWeekly[mode] || [];
        }}

        // ===== MAIN CHART =====
        function renderMainChart() {{
            const mainCtx = document.getElementById('mainChart').getContext('2d');
            if (mainChart) mainChart.destroy();
            const totalLabel = marketMode === 'all' ? 'Total (All US)'
                             : marketMode === 'solo' ? 'Total (Solo-AOS)'
                             : 'Total (Joint-AOS)';
            const totalDataset = {{
                label: totalLabel,
                data: totalDataFor(),
                borderColor: '#111827',
                backgroundColor: 'transparent',
                borderWidth: 2.5,
                borderDash: [6, 3],
                tension: 0.4,
                fill: false,
                pointRadius: 4,
                pointBackgroundColor: '#111827',
                order: 0
            }};
            const datasets = [totalDataset, ...Object.entries(data.categories).map(([key, cat]) => ({{
                label: cat.name,
                data: catDataFor(cat),
                borderColor: cat.color,
                backgroundColor: cat.color + '20',
                tension: 0.4,
                fill: true,
                order: 1
            }}))];
            mainChart = new Chart(mainCtx, {{
                type: 'line',
                data: {{ labels: data.dates, datasets: datasets }},
                plugins: [seasonPlugin],
                options: {{
                    responsive: true, maintainAspectRatio: false,
                    interaction: {{ mode: 'index', intersect: false }},
                    plugins: {{
                        legend: {{ position: 'bottom', labels: {{ usePointStyle: true, padding: 15, font: {{ size: 12 }} }} }},
                        tooltip: {{
                            backgroundColor: 'rgba(0,0,0,0.8)', padding: 12,
                            callbacks: {{
                                afterLabel: function(context) {{
                                    return data.seasonalMarkers.some(m => m.index === context.dataIndex) ? '🌟 Hiring Season' : '';
                                }}
                            }}
                        }}
                    }},
                    scales: {{
                        y: {{ beginAtZero: true, ticks: {{ font: {{ size: 12 }} }}, grid: {{ color: 'rgba(0,0,0,0.05)' }} }},
                        x: {{ ticks: {{ font: {{ size: 12 }} }}, grid: {{ display: false }} }}
                    }}
                }}
            }});
        }}

        // ===== CATEGORY CARDS =====
        function renderCategoryCards() {{
            const categoryGrid = document.getElementById('categoryGrid');
            categoryGrid.innerHTML = '';
            Object.entries(data.categories).forEach(([key, cat]) => {{
                const series = catDataFor(cat);
                const currentJobs = series[series.length - 1] || 0;
                const previousJobs = series[series.length - 2] || 0;
                const change = currentJobs - previousJobs;
                const changePercent = previousJobs > 0 ? ((change / previousJobs) * 100).toFixed(1) : 0;
                const card = document.createElement('div');
                card.className = 'category-card bg-white rounded-lg shadow hover:shadow-lg cursor-pointer p-5 border-l-4';
                card.style.borderLeftColor = cat.color;
                card.onclick = () => openModal(key, cat);
                card.innerHTML = `
                    <div class="flex justify-between items-start mb-3">
                        <h3 class="font-semibold text-gray-800 text-lg">${{cat.name}}</h3>
                        <div class="w-3 h-3 rounded-full" style="background-color:${{cat.color}}"></div>
                    </div>
                    <div class="flex items-end justify-between">
                        <div>
                            <div class="text-3xl font-bold text-gray-800">${{currentJobs}}</div>
                            <div class="text-sm text-gray-500">new this week</div>
                        </div>
                        <div class="text-right">
                            <div class="text-sm font-semibold ${{change >= 0 ? 'text-green-600' : 'text-red-600'}}">${{change >= 0 ? '↑' : '↓'}} ${{Math.abs(change)}}</div>
                            <div class="text-xs text-gray-500">${{changePercent}}%</div>
                        </div>
                    </div>
                    ${{cat.subcategories.length > 0 ? `<div class="mt-3 pt-3 border-t border-gray-100"><div class="text-xs text-gray-500">${{cat.subcategories.length}} subcategories</div></div>` : ''}}
                `;
                categoryGrid.appendChild(card);
            }});
        }}

        function updateMarketControls() {{
            const active = 'bg-indigo-600 text-white';
            const inactive = 'text-gray-700 hover:bg-indigo-50';
            document.getElementById('marketModeAll').className   = `px-3 py-1.5 text-sm font-medium ${{marketMode === 'all'   ? active : inactive}}`;
            document.getElementById('marketModeSolo').className  = `px-3 py-1.5 text-sm font-medium ${{marketMode === 'solo'  ? active : inactive}}`;
            document.getElementById('marketModeJoint').className = `px-3 py-1.5 text-sm font-medium ${{marketMode === 'joint' ? active : inactive}}`;
            document.getElementById('marketModeNote').textContent =
                marketMode === 'all'   ? 'All: every AOS tag counts (joint jobs add to multiple lines).' :
                marketMode === 'solo'  ? 'Solo: only jobs with exactly one AOS category.' :
                                         'Joint: only jobs listing multiple AOS categories; each tag still counts.';
        }}

        function setMarketMode(mode) {{
            marketMode = mode;
            renderMainChart();
            renderCategoryCards();
            updateMarketControls();
            // If the modal is open, re-render its data for the new mode
            if (currentModalKey && !document.getElementById('detailModal').classList.contains('hidden')) {{
                openModal(currentModalKey, data.categories[currentModalKey]);
            }}
        }}

        renderMainChart();
        renderCategoryCards();
        updateMarketControls();

        // ===== MODAL =====
        let detailChart = null, institutionChart = null;

        function openModal(key, category) {{
            currentModalKey = key;
            const catSeries = catDataFor(category);
            const currentJobs = catSeries[catSeries.length - 1] || 0;
            const previousJobs = catSeries[catSeries.length - 2] || 0;
            const change = currentJobs - previousJobs;
            const average = catSeries.length > 0 ? (catSeries.reduce((a, b) => a + b, 0) / catSeries.length).toFixed(1) : '0.0';
            const total = catSeries.reduce((a, b) => a + b, 0);

            document.getElementById('modalTitle').textContent = category.name + (marketMode === 'all' ? '' : ` — ${{marketMode}}`);
            document.getElementById('modalCurrentJobs').textContent = currentJobs;
            document.getElementById('modalChange').textContent = (change >= 0 ? '+' : '') + change;
            document.getElementById('modalChange').className = 'text-2xl font-bold ' + (change >= 0 ? 'text-green-600' : 'text-red-600');
            document.getElementById('modalAverage').textContent = average;
            document.getElementById('modalTotal').textContent = total;

            // Subcategories — each card includes a "Download report" button
            // that generates a multi-page PDF with the full posting for each
            // job tagged with that subcategory.
            const subcatGrid = document.getElementById('subcategoryGrid');
            document.getElementById('subcategorySection').style.display = category.subcategories.length > 0 ? 'block' : 'none';
            let subcatHtml = '';
            category.subcategories.forEach(sub => {{
                const subSeries = subDataFor(sub);
                const subTotal = subSeries.reduce((a, b) => a + b, 0);
                const subCurrent = subSeries[subSeries.length - 1] || 0;
                const soloJointData = data.detailAosByContext[sub] || {{}};
                const solo = Object.values(soloJointData.solo || {{}}).reduce((a, b) => a + b, 0);
                const joint = Object.values(soloJointData.with_others || {{}}).reduce((a, b) => a + b, 0);
                const jobIds = data.subcategoryJobIds[sub] || [];
                const jobCount = jobIds.length;
                const escapedSub = sub.replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
                const downloadBtn = jobCount > 0
                    ? `<button data-download-sub="${{escapedSub}}" class="mt-2 w-full text-xs px-2 py-1.5 bg-indigo-600 text-white rounded hover:bg-indigo-700 font-medium">📄 Download report (${{jobCount}} job${{jobCount === 1 ? '' : 's'}})</button>`
                    : `<div class="mt-2 text-xs text-gray-400 text-center">No jobs yet</div>`;
                subcatHtml += `
                    <div class="bg-gray-50 rounded-lg p-3 flex flex-col">
                        <div class="font-medium text-gray-800 text-sm mb-1">${{sub}}</div>
                        <div class="text-xs text-gray-500">${{subTotal}} total · ${{subCurrent}} this week</div>
                        ${{(solo + joint) > 0 ? `<div class="text-xs text-indigo-600 mt-1">Solo: ${{solo}} · Joint: ${{joint}}</div>` : ''}}
                        ${{downloadBtn}}
                    </div>`;
            }});
            subcatGrid.innerHTML = subcatHtml;
            subcatGrid.querySelectorAll('button[data-download-sub]').forEach(btn => {{
                btn.addEventListener('click', e => {{
                    downloadSubcategoryReport(e.currentTarget.dataset.downloadSub);
                }});
            }});

            // Trend chart
            const ctx = document.getElementById('detailChart').getContext('2d');
            if (detailChart) detailChart.destroy();
            detailChart = new Chart(ctx, {{
                type: 'line',
                data: {{
                    labels: data.dates,
                    datasets: [{{ label: category.name, data: catSeries, borderColor: category.color, backgroundColor: category.color + '30', tension: 0.4, fill: true }}]
                }},
                plugins: [seasonPlugin],
                options: {{
                    responsive: true, maintainAspectRatio: false,
                    plugins: {{ legend: {{ display: false }}, tooltip: {{ backgroundColor: 'rgba(0,0,0,0.8)' }} }},
                    scales: {{ y: {{ beginAtZero: true }}, x: {{ grid: {{ display: false }} }} }}
                }}
            }});

            // Lassiter: solo vs. joint by detail subcategory
            const lassiterDiv = document.getElementById('lassiterChart');
            const lassiterSection = document.getElementById('lassiterSection');
            if (category.subcategories.length > 0) {{
                lassiterSection.style.display = 'block';
                const rows = category.subcategories.map(sub => {{
                    const ctx2 = data.detailAosByContext[sub] || {{}};
                    const solo = Object.values(ctx2.solo || {{}}).reduce((a, b) => a + b, 0);
                    const joint = Object.values(ctx2.with_others || {{}}).reduce((a, b) => a + b, 0);
                    const total = ctx2.total || 0;
                    return {{ sub, solo, joint, total }};
                }}).filter(r => r.total > 0).sort((a, b) => b.total - a.total);
                if (rows.length > 0) {{
                    let tableHtml = '<table class="w-full border-collapse text-xs"><thead><tr><th class="text-left py-2 px-3 bg-gray-50 border border-gray-200">Subcategory</th><th class="py-2 px-2 bg-gray-50 border border-gray-200 text-center">Total</th><th class="py-2 px-2 bg-gray-50 border border-gray-200 text-center text-indigo-700">Solo</th><th class="py-2 px-2 bg-gray-50 border border-gray-200 text-center text-purple-700">Joint</th></tr></thead><tbody>';
                    rows.forEach((r, i) => {{
                        tableHtml += `<tr class="${{i % 2 === 0 ? 'bg-white' : 'bg-gray-50'}}"><td class="py-2 px-3 border border-gray-200 font-medium">${{r.sub}}</td><td class="py-2 px-2 border border-gray-200 text-center font-bold">${{r.total}}</td><td class="py-2 px-2 border border-gray-200 text-center text-indigo-700">${{r.solo}}</td><td class="py-2 px-2 border border-gray-200 text-center text-purple-700">${{r.joint}}</td></tr>`;
                    }});
                    lassiterDiv.innerHTML = tableHtml + '</tbody></table>';
                }} else {{
                    lassiterDiv.innerHTML = '<div class="text-gray-400 text-sm">No co-occurrence data yet.</div>';
                }}
            }} else {{
                lassiterSection.style.display = 'none';
            }}

            // Institution Types
            const instCtx = document.getElementById('institutionChart').getContext('2d');
            if (institutionChart) institutionChart.destroy();
            const instCurrent = ['Research University', 'Teaching College', 'Other'].map(it => {{
                const arr = data.institutionTypeData[it] || [];
                return arr[arr.length - 1] || 0;
            }});
            institutionChart = new Chart(instCtx, {{
                type: 'doughnut',
                data: {{
                    labels: ['Research University', 'Teaching College', 'Other'],
                    datasets: [{{ data: instCurrent, backgroundColor: ['#6366f1', '#10b981', '#6b7280'] }}]
                }},
                options: {{ responsive: true, plugins: {{ legend: {{ position: 'right', labels: {{ font: {{ size: 11 }}, boxWidth: 12 }} }} }} }}
            }});

            document.getElementById('detailModal').classList.remove('hidden');
        }}

        function closeModal() {{
            document.getElementById('detailModal').classList.add('hidden');
            currentModalKey = null;
            if (detailChart) {{ detailChart.destroy(); detailChart = null; }}
            if (institutionChart) {{ institutionChart.destroy(); institutionChart = null; }}
        }}
        document.getElementById('detailModal').addEventListener('click', function(e) {{
            if (e.target === this) closeModal();
        }});

        // ===== SUBCATEGORY DOWNLOAD REPORT (PDF) =====
        // Generates a multi-page PDF where each page is the full job posting
        // for a job tagged with the given subcategory. Uses jsPDF (UMD CDN).
        function downloadSubcategoryReport(subcategoryName) {{
            const jobIds = data.subcategoryJobIds[subcategoryName] || [];
            if (jobIds.length === 0) {{
                alert('No jobs available for "' + subcategoryName + '" yet.');
                return;
            }}
            if (!window.jspdf) {{
                alert('PDF library failed to load — try reloading the page.');
                return;
            }}
            const {{ jsPDF }} = window.jspdf;
            const doc = new jsPDF({{ unit: 'pt', format: 'letter' }});
            const margin = 50;
            const pageWidth = doc.internal.pageSize.getWidth();
            const pageHeight = doc.internal.pageSize.getHeight();
            const contentWidth = pageWidth - 2 * margin;
            const bottomLimit = pageHeight - margin;

            // jsPDF's default Helvetica handles Latin-1. Strip combining marks
            // for any text outside that range so it doesn't render as "?" boxes.
            const ascii = s => (s || '').toString().normalize('NFKD').replace(/[\\u0300-\\u036f]/g, '');

            jobIds.forEach((jid, idx) => {{
                const job = data.jobDetails[jid];
                if (!job) return;
                if (idx > 0) doc.addPage();
                let y = margin;

                const writeBlock = (text, fontSize, bold, color) => {{
                    if (!text) return;
                    doc.setFontSize(fontSize);
                    doc.setFont('helvetica', bold ? 'bold' : 'normal');
                    doc.setTextColor(color || 0);
                    const lines = doc.splitTextToSize(ascii(text), contentWidth);
                    lines.forEach(line => {{
                        if (y > bottomLimit) {{
                            doc.addPage();
                            y = margin;
                        }}
                        doc.text(line, margin, y);
                        y += fontSize * 1.25;
                    }});
                }};

                writeBlock(job.title || 'Untitled position', 14, true);
                writeBlock(job.institution || '', 11, false);
                y += 6;
                doc.setDrawColor(200);
                doc.line(margin, y, pageWidth - margin, y);
                y += 14;

                // Header strip — subcategory + position in batch
                writeBlock(`Subcategory: ${{subcategoryName}}  ·  Job ${{idx + 1}} of ${{jobIds.length}}`, 9, false, 120);
                y += 4;

                // Metadata
                const meta = [
                    ['Location', job.location],
                    ['Posted',   job.posted_date],
                    ['Deadline', job.deadline],
                    ['Start date', job.start_date],
                    ['Job category', job.job_category],
                    ['AOS', job.aos],
                    ['AOC', job.aoc],
                    ['Workload', job.workload],
                    ['Vacancies', job.vacancies],
                    ['Application type', job.application_type],
                    ['Application URL', job.application_url],
                    ['Contact', job.contact_email],
                    ['PhilJobs URL', job.url],
                ];
                meta.forEach(([k, v]) => {{
                    if (!v) return;
                    writeBlock(`${{k}}: ${{v}}`, 9, false);
                }});
                y += 10;

                writeBlock('Description', 11, true);
                writeBlock(job.description || 'No description recorded for this posting.', 10, false);
            }});

            const safeName = subcategoryName.replace(/[^a-z0-9]+/gi, '_').toLowerCase();
            const dateStr = new Date().toISOString().slice(0, 10);
            doc.save(`philjobs_${{safeName}}_${{dateStr}}.pdf`);
        }}

        // ===== REGIONAL CHART (with All/Solo/Joint toggle) =====
        const regionColors = {{ 'West': '#2563eb', 'Northeast': '#7c3aed', 'South': '#dc2626', 'Midwest': '#d97706' }};
        let regionMode = 'all';
        let regionalChart = null;

        function regionDataFor(region, mode) {{
            mode = mode || regionMode;
            const slot = data.regionData[region] || {{}};
            return slot[mode] || [];
        }}

        function renderRegionalChart() {{
            const ctx = document.getElementById('regionalChart').getContext('2d');
            if (regionalChart) regionalChart.destroy();
            regionalChart = new Chart(ctx, {{
                type: 'line',
                data: {{
                    labels: data.dates,
                    datasets: Object.keys(data.regionData).map(region => ({{
                        label: region,
                        data: regionDataFor(region),
                        borderColor: regionColors[region] || '#6b7280',
                        backgroundColor: (regionColors[region] || '#6b7280') + '20',
                        tension: 0.4, fill: true, borderWidth: region === 'West' ? 3 : 1.5,
                        pointRadius: 4
                    }}))
                }},
                options: {{
                    responsive: true, maintainAspectRatio: false,
                    interaction: {{ mode: 'index', intersect: false }},
                    plugins: {{ legend: {{ position: 'bottom', labels: {{ usePointStyle: true, padding: 15, font: {{ size: 12 }} }} }} }},
                    scales: {{ y: {{ beginAtZero: true }}, x: {{ grid: {{ display: false }} }} }}
                }}
            }});
        }}

        function updateRegionControls() {{
            const active = 'bg-indigo-600 text-white';
            const inactive = 'text-gray-700 hover:bg-indigo-50';
            document.getElementById('regionModeAll').className   = `px-3 py-1.5 text-sm font-medium ${{regionMode === 'all'   ? active : inactive}}`;
            document.getElementById('regionModeSolo').className  = `px-3 py-1.5 text-sm font-medium ${{regionMode === 'solo'  ? active : inactive}}`;
            document.getElementById('regionModeJoint').className = `px-3 py-1.5 text-sm font-medium ${{regionMode === 'joint' ? active : inactive}}`;
            document.getElementById('regionModeNote').textContent =
                regionMode === 'all'   ? 'All: counts every job in each region per week.' :
                regionMode === 'solo'  ? 'Solo: only jobs with exactly one AOS category.' :
                                         'Joint: only jobs listing multiple AOS categories.';
        }}

        function setRegionMode(mode) {{
            regionMode = mode;
            renderRegionalChart();
            updateRegionControls();
        }}

        renderRegionalChart();
        updateRegionControls();

        // ===== CO-OCCURRENCE MATRIX =====
        const matrixDiv = document.getElementById('coocMatrixTable');
        const matrixCats = data.mainAosCategories;
        let matrixHtml = '<table class="border-collapse text-xs"><thead><tr><th class="p-2 bg-gray-50 border border-gray-200"></th>';
        const shortNames = {{ 'Ethics': 'Ethics', 'Social & Political Philosophy': 'Soc/Pol', 'Value Theory / Aesthetics': 'Value/Aes', 'History of Philosophy': 'History', 'Non-Western & Cross-Cultural Philosophy': 'Non-West', 'Metaphysics & Epistemology': 'M&E', 'Science, Logic, & Mathematics': 'Sci/Log', 'Open': 'Open' }};
        matrixCats.forEach(c => {{ matrixHtml += `<th class="p-2 bg-gray-50 border border-gray-200 font-semibold text-gray-700" title="${{c}}">${{shortNames[c] || c}}</th>`; }});
        matrixHtml += '</tr></thead><tbody>';
        const allVals = matrixCats.flatMap(r => matrixCats.map(c => r !== c ? (data.coocMatrix[r]?.[c] || 0) : 0));
        const maxVal = Math.max(...allVals, 1);
        matrixCats.forEach((row, ri) => {{
            matrixHtml += `<tr><td class="p-2 bg-gray-50 border border-gray-200 font-semibold text-gray-700 whitespace-nowrap">${{shortNames[row] || row}}</td>`;
            matrixCats.forEach((col, ci) => {{
                if (row === col) {{
                    matrixHtml += '<td class="p-2 border border-gray-200 bg-gray-100 text-center text-gray-300">—</td>';
                }} else {{
                    const v = data.coocMatrix[row]?.[col] || 0;
                    const intensity = v > 0 ? Math.max(0.1, v / maxVal) : 0;
                    const bg = v > 0 ? `rgba(99,102,241,${{intensity.toFixed(2)}})` : '#f9fafb';
                    const color = intensity > 0.5 ? 'white' : '#374151';
                    matrixHtml += `<td class="p-2 border border-gray-200 text-center font-medium" style="background:${{bg}};color:${{color}}" title="${{row}} ↔ ${{col}}: ${{v}}">${{v > 0 ? v : ''}}</td>`;
                }}
            }});
            matrixHtml += '</tr>';
        }});
        matrixDiv.innerHTML = matrixHtml + '</tbody></table>';

        // ===== SOLO VS JOINT CHART =====
        const svjCats = Object.keys(data.soloVsJoint).filter(k => data.soloVsJoint[k].solo > 0 || data.soloVsJoint[k].joint > 0);
        new Chart(document.getElementById('soloJointChart').getContext('2d'), {{
            type: 'bar',
            data: {{
                labels: svjCats,
                datasets: [
                    {{ label: 'Solo', data: svjCats.map(k => data.soloVsJoint[k].solo || 0), backgroundColor: '#6366f1', borderRadius: 3 }},
                    {{ label: 'Joint', data: svjCats.map(k => data.soloVsJoint[k].joint || 0), backgroundColor: '#a78bfa', borderRadius: 3 }}
                ]
            }},
            options: {{
                responsive: true, maintainAspectRatio: false,
                plugins: {{ legend: {{ position: 'bottom' }} }},
                scales: {{ x: {{ stacked: false }}, y: {{ beginAtZero: true, stacked: false }} }}
            }}
        }});

        // ===== KEYWORD EXPLORER =====
        // Searches job description text only. Synonyms come from a synonym map
        // generated weekly by Claude at scrape time and embedded as data.synonymMap.
        let kwTrendChart = null;

        // Recursive morphological stemmer. Applies suffix rules until stable
        // so "feminists" → "feminist" → "femin" all collapse to one stem.
        // Mirrors the Python _keyword_stem method.
        function kwStem(word) {{
            word = word.toLowerCase().replace(/[^a-z]/g, '');
            let prev = null;
            while (prev !== word && word.length > 3) {{
                prev = word;
                if (word.endsWith('ies'))      word = word.slice(0, -3) + 'y';
                else if (word.endsWith('ism')) word = word.slice(0, -3);
                else if (word.endsWith('ist')) word = word.slice(0, -3);
                else if (word.endsWith('ing')) word = word.slice(0, -3);
                else if (word.endsWith('ed'))  word = word.slice(0, -2);
                else if (word.endsWith('es'))  word = word.slice(0, -2);
                else if (word.endsWith('s'))   word = word.slice(0, -1);
            }}
            return word;
        }}

        // Expand a query into a set of related terms via the synonym map + stemming
        function kwExpand(query) {{
            const q = query.toLowerCase().trim();
            if (!q) return new Set();
            const stem = kwStem(q);
            const terms = new Set([q, stem]);
            // Synonym map lookup (Claude-generated)
            const syns = data.synonymMap[q] || data.synonymMap[stem] || [];
            syns.forEach(s => {{
                terms.add(s.toLowerCase());
                terms.add(kwStem(s));
            }});
            return terms;
        }}

        // Test whether a job's description-term set matches any of the expanded terms.
        // Stems both sides so morphological variants ("feminist" vs "feminism") match.
        function kwJobMatches(jobStemSet, expandedTerms) {{
            for (const t of expandedTerms) {{
                if (jobStemSet.has(kwStem(t))) return true;
            }}
            return false;
        }}

        function kwSearch() {{
            const raw = document.getElementById('kwInput').value;
            const q = raw.trim();
            if (!q) {{
                document.getElementById('kwEmptyState').classList.remove('hidden');
                document.getElementById('kwResults').classList.add('hidden');
                document.getElementById('kwMatchCount').textContent = '';
                return;
            }}

            const expanded = kwExpand(q);
            const matchingJobs = [];
            data.jobsForKeyword.forEach((j) => {{
                // Build a set of stems for this job (cached per search is fine for now)
                if (!j._stemSet) {{
                    j._stemSet = new Set();
                    for (const t of j.terms) j._stemSet.add(kwStem(t));
                }}
                if (kwJobMatches(j._stemSet, expanded)) matchingJobs.push(j);
            }});

            const matchCount = matchingJobs.length;
            const expansionStr = Array.from(expanded).filter(t => t !== q.toLowerCase()).slice(0, 8).join(', ');
            document.getElementById('kwMatchCount').innerHTML =
                `<strong>${{matchCount}}</strong> job${{matchCount === 1 ? '' : 's'}} match` +
                (expansionStr ? ` &middot; <span class="text-gray-500">expanded to: ${{expansionStr}}</span>` : '');

            if (matchCount === 0) {{
                document.getElementById('kwEmptyState').classList.remove('hidden');
                document.getElementById('kwEmptyState').textContent = `No jobs found containing "${{q}}" or related terms. Try a broader term or check the bubble suggestions from another search.`;
                document.getElementById('kwResults').classList.add('hidden');
                return;
            }}

            document.getElementById('kwEmptyState').classList.add('hidden');
            document.getElementById('kwResults').classList.remove('hidden');

            // Build bubble chart from the synonym map (field-defining alternatives),
            // NOT from corpus co-occurrence. Each bubble = a synonym, sized by how
            // many jobs in the corpus contain that specific term (via stem matching).
            // This surfaces "what are the other names the field uses for this
            // concept" rather than "what words show up alongside this in postings".
            const qLower = q.toLowerCase();
            const queryStem = kwStem(qLower);
            const synonymList = data.synonymMap[qLower] || data.synonymMap[queryStem] || [];
            // Build the candidate set: query + synonyms, deduped by stem
            const stemToBubble = new Map();
            const addBubble = (rawTerm, isQuery) => {{
                const s = kwStem(rawTerm.toLowerCase());
                if (!s) return;
                if (stemToBubble.has(s)) {{
                    // Keep longest label
                    const existing = stemToBubble.get(s);
                    if (rawTerm.length > existing.label.length) existing.label = rawTerm;
                    if (isQuery) existing.isQuery = true;
                }} else {{
                    stemToBubble.set(s, {{ label: rawTerm, isQuery: !!isQuery, stem: s }});
                }}
            }};
            addBubble(qLower, true);
            synonymList.forEach(syn => addBubble(syn, false));

            // For each candidate stem, count how many jobs in the corpus contain it
            const bubbles = [];
            for (const [stem, entry] of stemToBubble) {{
                let count = 0;
                for (const j of data.jobsForKeyword) {{
                    if (j._stemSet.has(stem)) count++;
                }}
                bubbles.push({{ label: entry.label, count, isQuery: entry.isQuery }});
            }}
            // Sort: query first, then by count desc
            bubbles.sort((a, b) => {{
                if (a.isQuery && !b.isQuery) return -1;
                if (!a.isQuery && b.isQuery) return 1;
                return b.count - a.count;
            }});
            renderBubbleChart(q, bubbles, matchCount);

            // Trend chart: matching-job count per week
            const weekCounts = {{}};
            data.dates.forEach(d => {{ weekCounts[d] = 0; }});
            matchingJobs.forEach(j => {{
                if (weekCounts[j.scraped_date] !== undefined) weekCounts[j.scraped_date]++;
            }});
            renderKwTrend(data.dates.map(d => weekCounts[d]), q);
        }}

        function renderBubbleChart(query, bubbles, totalMatches) {{
            const container = document.getElementById('kwBubble');
            container.innerHTML = '';
            const width = container.clientWidth || 400;
            const height = 340;

            // If we have no synonyms AND the query has no matches, show a helpful empty state
            if (bubbles.length === 0) {{
                container.innerHTML = '<div class="text-gray-400 text-center py-12 text-sm">No field-defining synonyms found for this term in our map. The map covers the top 150 most frequent corpus terms — your term may be rare or use vocabulary the field doesn\\'t yet emphasize.</div>';
                return;
            }}

            // Convert bubble entries to D3 node format
            const nodes = bubbles.map(b => ({{
                id: b.label,
                count: b.count,
                isQuery: b.isQuery
            }}));
            const maxCount = Math.max(1, ...nodes.map(n => n.count));
            const minR = 18, maxR = 55;
            nodes.forEach(n => {{
                // Minimum size for query bubble even when 0 matches
                const safeCount = (n.isQuery && n.count === 0) ? 0.5 : n.count;
                n.r = minR + (maxR - minR) * Math.sqrt(Math.max(safeCount, 0) / maxCount);
                if (n.r < minR) n.r = minR;
            }});

            const svg = d3.select(container).append('svg')
                .attr('width', '100%').attr('height', height)
                .attr('viewBox', `0 0 ${{width}} ${{height}}`);

            const simulation = d3.forceSimulation(nodes)
                .force('charge', d3.forceManyBody().strength(5))
                .force('center', d3.forceCenter(width / 2, height / 2))
                .force('collide', d3.forceCollide(d => d.r + 2))
                .force('x', d3.forceX(width / 2).strength(0.05))
                .force('y', d3.forceY(height / 2).strength(0.05));

            const node = svg.selectAll('g').data(nodes).enter().append('g')
                .style('cursor', d => d.isQuery ? 'default' : 'pointer')
                .on('click', (event, d) => {{
                    if (d.isQuery) return;
                    document.getElementById('kwInput').value = d.id;
                    kwSearch();
                }});

            node.append('circle')
                .attr('r', d => d.r)
                .attr('fill', d => d.isQuery ? '#4f46e5' : '#a5b4fc')
                .attr('fill-opacity', d => d.isQuery ? 0.95 : 0.7)
                .attr('stroke', d => d.isQuery ? '#3730a3' : '#6366f1')
                .attr('stroke-width', 1.5);

            node.append('text')
                .text(d => d.id)
                .attr('text-anchor', 'middle')
                .attr('dominant-baseline', 'middle')
                .attr('fill', d => d.isQuery ? 'white' : '#1e1b4b')
                .attr('font-size', d => Math.max(10, Math.min(d.r * 0.45, 16)) + 'px')
                .attr('font-weight', d => d.isQuery ? '700' : '500')
                .style('pointer-events', 'none');

            node.append('title').text(d => `${{d.id}}: ${{d.count}} job${{d.count === 1 ? '' : 's'}}`);

            simulation.on('tick', () => {{
                node.attr('transform', d => `translate(${{d.x}}, ${{d.y}})`);
            }});
        }}

        function renderKwTrend(weekData, query) {{
            const ctx = document.getElementById('kwTrendChart').getContext('2d');
            if (kwTrendChart) kwTrendChart.destroy();
            kwTrendChart = new Chart(ctx, {{
                type: 'line',
                data: {{
                    labels: data.dates,
                    datasets: [{{
                        label: `Jobs matching "${{query}}"`,
                        data: weekData,
                        borderColor: '#4f46e5',
                        backgroundColor: '#a5b4fc40',
                        tension: 0.4, fill: true, borderWidth: 2, pointRadius: 4
                    }}]
                }},
                plugins: [seasonPlugin],
                options: {{
                    responsive: true, maintainAspectRatio: false,
                    plugins: {{ legend: {{ display: false }} }},
                    scales: {{
                        y: {{ beginAtZero: true, ticks: {{ precision: 0 }} }},
                        x: {{ grid: {{ display: false }}, ticks: {{ maxTicksLimit: 8 }} }}
                    }}
                }}
            }});
        }}

        document.getElementById('kwSearchBtn').addEventListener('click', kwSearch);
        document.getElementById('kwInput').addEventListener('keydown', e => {{
            if (e.key === 'Enter') kwSearch();
        }});

        // ===== POSITION TYPE CHART (with All/Solo/Joint toggle) =====
        let posTypeChart = null;
        let posTypeMode = 'all';
        const posTypeSelect = document.getElementById('posTypeAosFilter');
        data.mainAosCategories.forEach(aos => {{
            const opt = document.createElement('option');
            opt.value = aos;
            opt.textContent = aos;
            posTypeSelect.appendChild(opt);
        }});

        function ptSeriesFor(pt, aosFilter, mode) {{
            mode = mode || posTypeMode;
            if (aosFilter === '__all__') {{
                return (data.jobTypeData[pt] || {{}})[mode] || Array(data.dates.length).fill(0);
            }}
            const aosSlot = data.positionTypeByAosWeekly[aosFilter] || {{}};
            const ptSlot = aosSlot[pt] || {{}};
            return ptSlot[mode] || Array(data.dates.length).fill(0);
        }}

        function updatePositionTypeChart() {{
            const selected = posTypeSelect.value;
            const ptDatasets = data.positionTypes.map(pt => ({{
                label: pt,
                data: ptSeriesFor(pt, selected),
                borderColor: data.positionTypeColors[pt] || '#6b7280',
                backgroundColor: (data.positionTypeColors[pt] || '#6b7280') + '30',
                tension: 0.4, fill: true, borderWidth: 2, pointRadius: 3
            }}));
            if (posTypeChart) posTypeChart.destroy();
            posTypeChart = new Chart(document.getElementById('posTypeChart').getContext('2d'), {{
                type: 'line',
                data: {{ labels: data.dates, datasets: ptDatasets }},
                plugins: [seasonPlugin],
                options: {{
                    responsive: true, maintainAspectRatio: false,
                    interaction: {{ mode: 'index', intersect: false }},
                    plugins: {{ legend: {{ position: 'bottom', labels: {{ usePointStyle: true, padding: 12, font: {{ size: 11 }} }} }} }},
                    scales: {{ y: {{ beginAtZero: true }}, x: {{ grid: {{ display: false }} }} }}
                }}
            }});

            // Summary table — uses all-time pos_type_x_aos sliced by current mode
            const xAos = data.positionTypeXAos[posTypeMode] || {{}};
            const tableDiv = document.getElementById('posTypeTable');
            const aosRows = data.mainAosCategories;
            let html = '<table class="w-full border-collapse"><thead><tr>';
            html += '<th class="text-left py-2 px-3 bg-gray-50 font-semibold text-gray-700 border border-gray-200 text-sm">AOS Category</th>';
            data.positionTypes.forEach(pt => {{
                const short = pt.replace('Visiting / Adjunct / Lecturer (Fixed-Term)', 'Visiting/Adj/Lect').replace('Tenured / Continuing / Permanent', 'Tenured/Perm').replace('Postdoc / Fellowship', 'Postdoc/Fellow');
                html += `<th class="py-2 px-2 bg-gray-50 font-semibold border border-gray-200 text-center text-xs" style="color:${{data.positionTypeColors[pt] || '#6b7280'}}" title="${{pt}}">${{short}}</th>`;
            }});
            html += '<th class="py-2 px-3 bg-gray-50 font-semibold text-gray-700 border border-gray-200 text-center text-sm">Total</th></tr></thead><tbody>';
            aosRows.forEach((aos, i) => {{
                const row = xAos[aos] || {{}};
                const rowTotal = data.positionTypes.reduce((s, pt) => s + (row[pt] || 0), 0);
                if (rowTotal === 0) return;
                html += `<tr class="${{i % 2 === 0 ? 'bg-white' : 'bg-gray-50'}}">`;
                html += `<td class="py-2 px-3 font-medium text-gray-700 border border-gray-200 text-sm">${{aos}}</td>`;
                data.positionTypes.forEach(pt => {{
                    const v = row[pt] || 0;
                    const pct = rowTotal > 0 ? Math.round(v / rowTotal * 100) : 0;
                    html += `<td class="py-2 px-2 text-center border border-gray-200 text-xs ${{v > 0 ? 'font-semibold text-gray-800' : 'text-gray-300'}}">${{v > 0 ? `${{v}}<div class="text-gray-400 font-normal">${{pct}}%</div>` : '—'}}</td>`;
                }});
                html += `<td class="py-2 px-3 text-center font-bold text-indigo-600 border border-gray-200 text-sm">${{rowTotal}}</td></tr>`;
            }});
            html += '</tbody></table>';
            tableDiv.innerHTML = html;
        }}

        function updatePosTypeControls() {{
            const active = 'bg-indigo-600 text-white';
            const inactive = 'text-gray-700 hover:bg-indigo-50';
            document.getElementById('posTypeModeAll').className   = `px-3 py-1.5 text-sm font-medium ${{posTypeMode === 'all'   ? active : inactive}}`;
            document.getElementById('posTypeModeSolo').className  = `px-3 py-1.5 text-sm font-medium ${{posTypeMode === 'solo'  ? active : inactive}}`;
            document.getElementById('posTypeModeJoint').className = `px-3 py-1.5 text-sm font-medium ${{posTypeMode === 'joint' ? active : inactive}}`;
            document.getElementById('posTypeModeNote').textContent =
                posTypeMode === 'all'   ? 'All: every job counted (joint jobs add to multiple AOS rows in the table).' :
                posTypeMode === 'solo'  ? 'Solo: only jobs with exactly one AOS category.' :
                                          'Joint: only jobs listing multiple AOS categories.';
        }}

        function setPosTypeMode(mode) {{
            posTypeMode = mode;
            updatePositionTypeChart();
            updatePosTypeControls();
        }}

        updatePositionTypeChart();
        updatePosTypeControls();

        // ===== WEST COAST SPOTLIGHT — stacked horizontal bars, AOS by city/metro =====
        let wcChart = null;
        let wcViewMode = 'metro';      // 'metro' or 'city'
        let wcMode = 'all';            // 'all' | 'solo' | 'joint'
        let wcMetroFilter = null;      // when set in city view, only show cities from this metro

        function sumValues(obj) {{
            return Object.values(obj || {{}}).reduce((a, b) => a + b, 0);
        }}

        function renderWestCoastChart() {{
            const canvas = document.getElementById('westCoastChart');
            if (!canvas) return;
            const container = canvas.parentElement;
            // If we previously fell back to an empty-state message, restore the canvas
            if (!container.querySelector('canvas')) {{
                container.innerHTML = '<canvas id="westCoastChart"></canvas>';
            }}

            // Pick data source: metro vs. city × all/solo/joint
            const metroSource = data.westCoastMetroAos[wcMode] || {{}};
            const citySource = data.westCoastCityAos[wcMode] || {{}};

            let sourceData;
            if (wcViewMode === 'metro') {{
                sourceData = metroSource;
            }} else if (wcMetroFilter) {{
                const allowedCities = new Set(data.westCoastMetroCities[wcMetroFilter] || []);
                sourceData = Object.fromEntries(
                    Object.entries(citySource).filter(([c]) => allowedCities.has(c))
                );
            }} else {{
                sourceData = citySource;
            }}

            const labels = Object.keys(sourceData)
                .filter(loc => sumValues(sourceData[loc]) > 0)
                .sort((a, b) => sumValues(sourceData[b]) - sumValues(sourceData[a]));

            if (labels.length === 0) {{
                const msg = wcMode === 'solo' ? 'No solo-AOS West Coast jobs yet.'
                          : wcMode === 'joint' ? 'No multi-AOS West Coast jobs yet.'
                          : 'No West Coast data yet for this view.';
                container.innerHTML = `<div class="text-gray-400 text-center py-8 text-sm">${{msg}}</div>`;
                return;
            }}

            // Build one stacked dataset per main AOS category, in canonical order
            const datasets = data.mainAosCategories.map(cat => ({{
                label: cat,
                data: labels.map(loc => sourceData[loc]?.[cat] || 0),
                backgroundColor: data.mainAosColors[cat] || '#9ca3af',
                borderColor: '#ffffff',
                borderWidth: 1,
            }})).filter(ds => ds.data.some(v => v > 0));

            const newCanvas = document.getElementById('westCoastChart');
            if (wcChart) {{ wcChart.destroy(); }}

            wcChart = new Chart(newCanvas.getContext('2d'), {{
                type: 'bar',
                data: {{ labels, datasets }},
                options: {{
                    indexAxis: 'y',
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        legend: {{ position: 'bottom', labels: {{ usePointStyle: true, padding: 10, font: {{ size: 11 }} }} }},
                        tooltip: {{
                            callbacks: {{
                                title: (items) => {{
                                    if (!items.length) return '';
                                    const label = items[0].label;
                                    const total = items.reduce((a, b) => a + b.parsed.x, 0);
                                    const unit = wcMode === 'all' ? 'tag' : (wcMode === 'solo' ? 'job' : 'tag');
                                    return `${{label}} — ${{total}} ${{unit}}${{total === 1 ? '' : 's'}}`;
                                }},
                                label: (ctx) => {{
                                    const v = ctx.parsed.x;
                                    return v > 0 ? ` ${{ctx.dataset.label}}: ${{v}}` : null;
                                }}
                            }}
                        }}
                    }},
                    scales: {{
                        x: {{ stacked: true, beginAtZero: true, ticks: {{ precision: 0 }} }},
                        y: {{ stacked: true, grid: {{ display: false }} }}
                    }},
                    onClick: (evt, elements) => {{
                        if (wcViewMode !== 'metro' || elements.length === 0) return;
                        const idx = elements[0].index;
                        const metroClicked = labels[idx];
                        wcMetroFilter = metroClicked;
                        wcViewMode = 'city';
                        renderWestCoastChart();
                        updateWcControls();
                    }}
                }}
            }});
        }}

        function updateWcControls() {{
            const metroBtn = document.getElementById('wcViewMetro');
            const cityBtn = document.getElementById('wcViewCity');
            const allBtn = document.getElementById('wcModeAll');
            const soloBtn = document.getElementById('wcModeSolo');
            const jointBtn = document.getElementById('wcModeJoint');
            const indicator = document.getElementById('wcFilterIndicator');
            const note = document.getElementById('wcModeNote');
            const active = 'bg-blue-600 text-white';
            const inactive = 'text-gray-700 hover:bg-blue-50';

            // Metro/City toggle
            if (wcViewMode === 'metro') {{
                metroBtn.className = `px-4 py-1.5 text-sm font-medium ${{active}}`;
                cityBtn.className = `px-4 py-1.5 text-sm font-medium ${{inactive}}`;
                indicator.classList.add('hidden');
            }} else {{
                metroBtn.className = `px-4 py-1.5 text-sm font-medium ${{inactive}}`;
                cityBtn.className = `px-4 py-1.5 text-sm font-medium ${{active}}`;
                if (wcMetroFilter) {{
                    indicator.innerHTML = `Filtered to <span class="font-semibold">${{wcMetroFilter}}</span> &nbsp;<button onclick="clearWcFilter()" class="text-blue-600 hover:underline">clear</button>`;
                    indicator.classList.remove('hidden');
                }} else {{
                    indicator.classList.add('hidden');
                }}
            }}

            // All/Solo/Joint toggle
            allBtn.className = `px-3 py-1.5 text-sm font-medium ${{wcMode === 'all' ? active : inactive}}`;
            soloBtn.className = `px-3 py-1.5 text-sm font-medium ${{wcMode === 'solo' ? active : inactive}}`;
            jointBtn.className = `px-3 py-1.5 text-sm font-medium ${{wcMode === 'joint' ? active : inactive}}`;

            note.textContent = wcMode === 'all'
                ? 'All: every AOS tag counts (joint jobs add to multiple bars).'
                : wcMode === 'solo'
                ? 'Solo: only jobs with exactly one AOS category.'
                : 'Joint: only jobs listing multiple AOS categories; each tag still counts.';
        }}

        function setWcView(mode) {{
            wcViewMode = mode;
            if (mode === 'metro') wcMetroFilter = null;
            renderWestCoastChart();
            updateWcControls();
        }}

        function setWcMode(mode) {{
            wcMode = mode;
            renderWestCoastChart();
            updateWcControls();
        }}

        function clearWcFilter() {{
            wcMetroFilter = null;
            renderWestCoastChart();
            updateWcControls();
        }}

        renderWestCoastChart();
        updateWcControls();

        // ===== D3 US CHOROPLETH =====
        let currentMapMode = 'current', usAtlasData = null;
        const fipsToState = {{"01":"AL","02":"AK","04":"AZ","05":"AR","06":"CA","08":"CO","09":"CT","10":"DE","12":"FL","13":"GA","15":"HI","16":"ID","17":"IL","18":"IN","19":"IA","20":"KS","21":"KY","22":"LA","23":"ME","24":"MD","25":"MA","26":"MI","27":"MN","28":"MS","29":"MO","30":"MT","31":"NE","32":"NV","33":"NH","34":"NJ","35":"NM","36":"NY","37":"NC","38":"ND","39":"OH","40":"OK","41":"OR","42":"PA","44":"RI","45":"SC","46":"SD","47":"TN","48":"TX","49":"UT","50":"VT","51":"VA","53":"WA","54":"WV","55":"WI","56":"WY"}};

        function getStateValues(mode) {{
            if (mode === 'alltime') return data.stateAlltime;
            // Current-week reading uses the 'all' slice of the per-state series
            const r = {{}};
            Object.entries(data.stateData).forEach(([s, slot]) => {{
                const c = (slot && slot.all) ? slot.all : [];
                r[s] = c[c.length - 1] || 0;
            }});
            return r;
        }}

        function setMapMode(mode) {{
            currentMapMode = mode;
            document.getElementById('mapModeNew').className = mode === 'current' ? 'px-4 py-2 text-sm font-medium rounded-lg bg-indigo-600 text-white' : 'px-4 py-2 text-sm font-medium rounded-lg bg-gray-200 text-gray-700';
            document.getElementById('mapModeAll').className = mode === 'alltime' ? 'px-4 py-2 text-sm font-medium rounded-lg bg-indigo-600 text-white' : 'px-4 py-2 text-sm font-medium rounded-lg bg-gray-200 text-gray-700';
            if (usAtlasData) drawUSChoropleth();
        }}

        function drawUSChoropleth() {{
            const el = document.getElementById('usMapEl');
            el.innerHTML = '';
            const values = getStateValues(currentMapMode);
            const maxVal = Math.max(...Object.values(values).filter(v => v > 0), 1);
            const width = el.clientWidth || 800, height = 400;
            const features = topojson.feature(usAtlasData, usAtlasData.objects.states);
            const projection = d3.geoAlbersUsa().fitSize([width, height], features);
            const path = d3.geoPath().projection(projection);
            const svg = d3.select('#usMapEl').append('svg').attr('width', '100%').attr('height', height).attr('viewBox', `0 0 ${{width}} ${{height}}`);
            const tip = d3.select('#mapTooltip');
            svg.append('g').selectAll('path').data(features.features).join('path')
                .attr('d', path)
                .attr('fill', d => {{
                    const sc = fipsToState[String(d.id).padStart(2, '0')];
                    const v = values[sc] || 0;
                    if (v === 0) return '#e5e7eb';
                    return d3.interpolate('#d1fae5', '#065f46')(v / maxVal);
                }})
                .attr('stroke', '#9ca3af')
                .attr('stroke-width', 0.5)
                .style('cursor', 'pointer')
                .on('mouseover', function(event, d) {{
                    const sc = fipsToState[String(d.id).padStart(2, '0')] || '';
                    const v = values[sc] || 0;
                    tip.style('display', 'block').html(`<strong>${{sc}}</strong><br>${{v}} job${{v !== 1 ? 's' : ''}}`);
                    d3.select(this).attr('stroke', '#111').attr('stroke-width', 2);
                }})
                .on('mousemove', event => tip.style('left', (event.pageX + 12) + 'px').style('top', (event.pageY - 28) + 'px'))
                .on('mouseout', function(event, d) {{
                    tip.style('display', 'none');
                    d3.select(this).attr('stroke', '#9ca3af').attr('stroke-width', 0.5);
                }})
                .on('click', (event, d) => {{
                    const sc = fipsToState[String(d.id).padStart(2, '0')];
                    if (sc) showStateDetail(sc);
                }});
        }}

        async function initMaps() {{
            try {{
                usAtlasData = await d3.json('https://cdn.jsdelivr.net/npm/us-atlas@3/states-10m.json');
                drawUSChoropleth();
            }} catch(e) {{
                document.getElementById('usMapEl').innerHTML = '<div class="text-gray-400 text-center p-4 text-sm">Map unavailable — check connection</div>';
            }}
        }}
        initMaps();

        // ===== STATE DETAIL PANEL =====
        let stateTrendChart = null;
        let currentStateCode = null;
        let stateMode = 'all';
        const catColors = {json.dumps(MAIN_AOS_COLORS)};

        function renderStateDetail() {{
            if (!currentStateCode) return;
            const stateCode = currentStateCode;
            const slot = data.stateData[stateCode] || {{}};
            const weekly = slot[stateMode] || [];
            const current = weekly[weekly.length - 1] || 0;
            // All-time uses the appropriate slice
            const alltime = weekly.reduce((a, b) => a + b, 0);
            const catSlice = (data.stateCategoryData[stateMode] || {{}})[stateCode] || {{}};
            const isWC = ['CA', 'OR', 'WA'].includes(stateCode);

            document.getElementById('statePanelTitle').textContent = stateCode + (isWC ? ' 🌊' : '');
            document.getElementById('stateNewJobs').textContent = current;
            document.getElementById('stateTotalJobs').textContent = alltime;

            const ctx = document.getElementById('stateTrendChart').getContext('2d');
            if (stateTrendChart) stateTrendChart.destroy();
            stateTrendChart = new Chart(ctx, {{
                type: 'bar',
                data: {{ labels: data.dates, datasets: [{{ label: 'New Jobs', data: weekly, backgroundColor: isWC ? '#3b82f6' : '#10b981', borderRadius: 3 }}] }},
                options: {{
                    responsive: true, maintainAspectRatio: false,
                    plugins: {{ legend: {{ display: false }} }},
                    scales: {{ y: {{ beginAtZero: true, ticks: {{ precision: 0 }} }}, x: {{ ticks: {{ maxTicksLimit: 6 }} }} }}
                }}
            }});

            const breakdown = document.getElementById('stateCategoryBreakdown');
            breakdown.innerHTML = '';
            const sorted = Object.entries(catSlice).sort((a, b) => b[1] - a[1]);
            const total = sorted.reduce((s, [, v]) => s + v, 0);
            if (sorted.length === 0) {{
                breakdown.innerHTML = '<div class="text-gray-400 text-sm">No category data for this mode</div>';
            }} else {{
                sorted.forEach(([cat, count]) => {{
                    const pct = total > 0 ? Math.round(count / total * 100) : 0;
                    const color = catColors[cat] || '#6b7280';
                    breakdown.innerHTML += `
                        <div class="flex items-center gap-2 py-1">
                            <div class="w-2 h-2 rounded-full flex-shrink-0" style="background:${{color}}"></div>
                            <div class="flex-1 text-sm text-gray-700">${{cat}}</div>
                            <div class="text-sm font-bold">${{count}}</div>
                            <div class="text-xs text-gray-400">${{pct}}%</div>
                        </div>
                        <div class="h-1.5 bg-gray-100 rounded mb-1">
                            <div class="h-1.5 rounded" style="width:${{pct}}%;background:${{color}}"></div>
                        </div>`;
                }});
            }}
        }}

        function updateStateModeControls() {{
            const active = 'flex-1 px-3 py-1.5 text-sm font-medium bg-indigo-600 text-white';
            const inactive = 'flex-1 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-indigo-50';
            document.getElementById('stateModeAll').className   = stateMode === 'all'   ? active : inactive;
            document.getElementById('stateModeSolo').className  = stateMode === 'solo'  ? active : inactive;
            document.getElementById('stateModeJoint').className = stateMode === 'joint' ? active : inactive;
            document.getElementById('stateModeNote').textContent =
                stateMode === 'all'   ? 'All: every job counted regardless of AOS-listing pattern.' :
                stateMode === 'solo'  ? 'Solo: only jobs with exactly one AOS category.' :
                                        'Joint: only jobs listing multiple AOS categories.';
        }}

        function setStateMode(mode) {{
            stateMode = mode;
            updateStateModeControls();
            renderStateDetail();
        }}

        function showStateDetail(stateCode) {{
            currentStateCode = stateCode;
            updateStateModeControls();
            renderStateDetail();
            document.getElementById('stateDetailPanel').classList.remove('hidden');
        }}

        function closeStatePanel() {{
            document.getElementById('stateDetailPanel').classList.add('hidden');
            currentStateCode = null;
            if (stateTrendChart) {{ stateTrendChart.destroy(); stateTrendChart = null; }}
        }}
    </script>
</body>
</html>'''

        docs_dir = Path("docs")
        docs_dir.mkdir(exist_ok=True)
        dashboard_file = docs_dir / "index.html"
        with open(dashboard_file, 'w') as f:
            f.write(html)
        print(f"✓ US dashboard written to {dashboard_file}")


    def generate_intl_dashboard(self, historical_data):
        """Generate international HTML dashboard (docs/international.html)."""
        trends = historical_data.get('weekly_trends', [])
        if not trends:
            print("No data available for international dashboard")
            return

        all_jobs = historical_data.get('jobs', [])
        dates = [t['date'] for t in trends]

        # ── Filter to international jobs only ────────────────────────────
        intl_jobs = [j for j in all_jobs if j.get('country') and not j.get('state')]

        # Group international jobs by date key (YYYY-MM-DD)
        jobs_by_date = defaultdict(list)
        for job in intl_jobs:
            date_key = job.get('scraped_date', '')[:10]
            jobs_by_date[date_key].append(job)

        # ── Weekly series ────────────────────────────────────────────────
        series = self._compute_weekly_series(jobs_by_date, dates)
        parent_categories         = series['parent_categories']
        subcategory_data          = series['subcategory_data']
        job_type_series           = series['job_type_series']
        position_type_by_aos_weekly = series['position_type_by_aos_weekly']
        inst_type_series          = series['inst_type_series']
        total_new_jobs_weekly     = series['total_new_jobs_weekly']

        # ── International region trend lines (with solo/joint slicing) ───
        country_to_region = {c: r for r, countries in INTL_REGIONS.items() for c in countries}
        intl_region_data = {region: {'all': [0] * len(dates), 'solo': [0] * len(dates), 'joint': [0] * len(dates)}
                            for region in INTL_REGIONS}
        for i, date in enumerate(dates):
            date_key = date[:10]
            for job in jobs_by_date.get(date_key, []):
                region = country_to_region.get(job.get('country'))
                if not region:
                    continue
                cls = job.get('classification') or {}
                main_list = cls.get('main_aos', ['Open'])
                mode_key = 'solo' if len(main_list) == 1 else 'joint'
                intl_region_data[region]['all'][i] += 1
                intl_region_data[region][mode_key][i] += 1

        # ── Country-level all-time counts for world choropleth ───────────
        country_alltime = defaultdict(int)
        country_current = defaultdict(int)
        last_date_key = dates[-1][:10] if dates else ''
        for job in intl_jobs:
            c = job.get('country')
            if c:
                country_alltime[c] += 1
                if job.get('scraped_date', '')[:10] == last_date_key:
                    country_current[c] += 1

        # Build numeric → country mapping for choropleth (reverse of COUNTRY_NUMERIC)
        numeric_to_country = {v: k for k, v in COUNTRY_NUMERIC.items()
                               if k not in ('UAE',)}  # avoid dup for UAE alias

        # ── Position type × AOS all-time (with solo/joint slicing) ───────
        pos_type_x_aos_map = {m: defaultdict(lambda: defaultdict(int)) for m in ('all', 'solo', 'joint')}
        for job in intl_jobs:
            cls = job.get('classification')
            if not cls:
                continue
            raw_pt = (cls.get('position_type')
                      or JOB_TYPE_MIGRATION.get(cls.get('job_type', ''), None)
                      or job.get('job_type', 'Other'))
            pos_type = raw_pt if raw_pt in POSITION_TYPES else 'Other'
            main_list = cls.get('main_aos', [])
            mode_key = 'solo' if len(main_list) == 1 else 'joint'
            for main in main_list:
                pos_type_x_aos_map['all'][main][pos_type] += 1
                pos_type_x_aos_map[mode_key][main][pos_type] += 1
        pos_type_x_aos = {m: {k: dict(v) for k, v in pos_type_x_aos_map[m].items()} for m in ('all', 'solo', 'joint')}

        # ── Country → AOS breakdown ──────────────────────────────────────
        country_cat_map = defaultdict(lambda: defaultdict(int))
        for job in intl_jobs:
            c = job.get('country')
            if c:
                cls = job.get('classification')
                if cls:
                    for main in cls.get('main_aos', []):
                        country_cat_map[c][main] += 1
        country_category_data = {k: dict(v) for k, v in country_cat_map.items()}

        # ── Subcategory → job IDs + full job details (for PDF download) ──
        subcategory_job_ids = defaultdict(list)
        job_details_map = {}
        for job in intl_jobs:
            jid = job.get('id')
            if not jid:
                continue
            cls = job.get('classification') or {}
            for main, details in cls.get('detail_aos', {}).items():
                for detail in details:
                    if jid not in subcategory_job_ids[detail]:
                        subcategory_job_ids[detail].append(jid)
            job_details_map[jid] = {
                'id': jid,
                'url': job.get('url', ''),
                'institution': job.get('institution', ''),
                'title': job.get('title', ''),
                'job_category': job.get('job_category', ''),
                'aos': job.get('aos', ''),
                'aoc': job.get('aoc', ''),
                'location': job.get('location', ''),
                'workload': job.get('workload', ''),
                'vacancies': job.get('vacancies', ''),
                'deadline': job.get('deadline', ''),
                'start_date': job.get('start_date', ''),
                'posted_date': job.get('posted_date', ''),
                'application_type': job.get('application_type', ''),
                'application_url': job.get('application_url', ''),
                'contact_email': job.get('contact_email', ''),
                'description': job.get('description', ''),
                'job_type': job.get('job_type', ''),
            }
        subcategory_job_ids = {k: list(v) for k, v in subcategory_job_ids.items()}

        # ── Co-occurrence ─────────────────────────────────────────────────
        cooc = self._compute_cooc_from_jobs(intl_jobs)

        # ── Keyword Explorer index + synonym map (Intl) ──────────────────
        print("Building Intl keyword index + synonym map...")
        keyword_index, kw_vocab, bubble_stopwords = self.build_keyword_index(intl_jobs)
        synonym_map = self.generate_synonym_map(kw_vocab)

        # ── Summary stats ─────────────────────────────────────────────────
        last_week_jobs = jobs_by_date.get(last_date_key, [])
        current_week_new_jobs = len(last_week_jobs)
        total_unique_jobs = len(intl_jobs)
        weeks_tracked = len(dates)

        last_main = defaultdict(int)
        for job in last_week_jobs:
            cls = job.get('classification') or {}
            for main in cls.get('main_aos', ['Open']):
                last_main[main] += 1
        most_active = max(last_main, key=last_main.get) if last_main else "—"

        seasonal_markers = []
        for i, date in enumerate(dates):
            if self.is_hiring_season(date):
                seasonal_markers.append({'index': i, 'label': 'Hiring Season'})

        # ── Pre-serialise JS objects ──────────────────────────────────────
        categories_js = json.dumps({
            k: {
                'name': k,
                'dataAll': v['dataAll'], 'dataSolo': v['dataSolo'], 'dataJoint': v['dataJoint'],
                'subcategories': v['subcategories'],
                'color': v['color']
            }
            for k, v in parent_categories.items()
        })

        # ── Build HTML ────────────────────────────────────────────────────
        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>International Philosophy Job Market Analytics</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/d3@7"></script>
    <script src="https://cdn.jsdelivr.net/npm/topojson-client@3"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        body {{ font-family: 'Inter', sans-serif; }}
        .category-card:hover {{ transform: translateY(-2px); transition: all 0.3s; }}
        .stat-card {{ background: linear-gradient(135deg, #0891b2 0%, #0e7490 100%); }}
        .chart-container {{ min-height: 400px; }}
        #mapTooltip {{ display:none; position:fixed; background:rgba(0,0,0,0.8); color:white; padding:6px 10px; border-radius:6px; font-size:13px; pointer-events:none; z-index:1000; line-height:1.5; }}
    </style>
</head>
<body class="bg-gray-50">
    <!-- Tab Navigation -->
    <div class="bg-white border-b border-gray-200 sticky top-0 z-40 shadow-sm">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex gap-1 py-2">
                <a href="index.html" class="px-5 py-2 text-sm font-semibold rounded-lg text-gray-600 hover:bg-gray-100 transition-colors">🇺🇸 US Market</a>
                <a href="international.html" class="px-5 py-2 text-sm font-semibold rounded-lg bg-cyan-600 text-white">🌍 International</a>
            </div>
        </div>
    </div>
    <div class="bg-gradient-to-r from-cyan-600 to-teal-600 text-white">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
            <h1 class="text-4xl font-bold mb-2">International Philosophy Job Market</h1>
            <p class="text-cyan-100">Real-time trends from PhilJobs — non-U.S. institutions</p>
            <div class="mt-6 text-sm text-cyan-100">Last updated: {datetime.now().strftime("%B %d, %Y")}</div>
        </div>
    </div>

    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">

        <!-- Stats Cards -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-6 mb-8">
            <div class="stat-card rounded-xl shadow-lg p-6 text-white col-span-2 md:col-span-1">
                <div class="text-3xl font-bold">{current_week_new_jobs}</div>
                <div class="text-cyan-100">New Intl Jobs This Week</div>
            </div>
            <div class="bg-white rounded-xl shadow-lg p-6">
                <div class="text-3xl font-bold text-gray-800">{total_unique_jobs}</div>
                <div class="text-gray-600">Total Intl Jobs Tracked</div>
            </div>
            <div class="bg-white rounded-xl shadow-lg p-6">
                <div class="text-2xl font-bold text-gray-800 truncate">{most_active}</div>
                <div class="text-gray-600">Most Active This Week</div>
            </div>
            <div class="bg-white rounded-xl shadow-lg p-6">
                <div class="text-3xl font-bold text-gray-800">{weeks_tracked}</div>
                <div class="text-gray-600">Weeks Tracked</div>
            </div>
        </div>

        <!-- Market Overview -->
        <div class="bg-white rounded-xl shadow-lg p-6 mb-8">
            <div class="flex items-start justify-between mb-3 flex-wrap gap-3">
                <div>
                    <h2 class="text-2xl font-bold text-gray-800 mb-1">Market Overview</h2>
                    <p class="text-sm text-gray-500">New international jobs per week by main AOS category — shaded areas = hiring season (Sept–Jan). Toggle filters by solo (single-AOS) vs. joint (multi-AOS) listings.</p>
                </div>
                <div class="flex flex-col items-end gap-2">
                    <div class="inline-flex rounded-lg overflow-hidden border border-gray-300 bg-white">
                        <button id="marketModeAll" type="button" onclick="setMarketMode('all')" class="px-3 py-1.5 text-sm font-medium bg-cyan-600 text-white">All</button>
                        <button id="marketModeSolo" type="button" onclick="setMarketMode('solo')" class="px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-cyan-50">Solo</button>
                        <button id="marketModeJoint" type="button" onclick="setMarketMode('joint')" class="px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-cyan-50">Joint</button>
                    </div>
                    <div id="marketModeNote" class="text-xs text-gray-500 italic"></div>
                </div>
            </div>
            <div class="chart-container">
                <canvas id="mainChart"></canvas>
            </div>
        </div>

        <!-- International Regional Trends -->
        <div class="bg-white rounded-xl shadow-lg p-6 mb-8">
            <div class="flex items-start justify-between mb-3 flex-wrap gap-3">
                <div>
                    <h2 class="text-2xl font-bold text-gray-800 mb-1">Regional Trends</h2>
                    <p class="text-sm text-gray-500">New jobs per week by world region. Toggle filters by solo (single-AOS) vs. joint (multi-AOS) listings.</p>
                </div>
                <div class="flex flex-col items-end gap-2">
                    <div class="inline-flex rounded-lg overflow-hidden border border-gray-300 bg-white">
                        <button id="regionModeAll" type="button" onclick="setRegionMode('all')" class="px-3 py-1.5 text-sm font-medium bg-cyan-600 text-white">All</button>
                        <button id="regionModeSolo" type="button" onclick="setRegionMode('solo')" class="px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-cyan-50">Solo</button>
                        <button id="regionModeJoint" type="button" onclick="setRegionMode('joint')" class="px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-cyan-50">Joint</button>
                    </div>
                    <div id="regionModeNote" class="text-xs text-gray-500 italic"></div>
                </div>
            </div>
            <div class="chart-container">
                <canvas id="regionalChart"></canvas>
            </div>
        </div>

        <!-- Co-Occurrence Matrix -->
        <div class="bg-white rounded-xl shadow-lg p-6 mb-8">
            <h2 class="text-2xl font-bold text-gray-800 mb-1">AOS Co-Occurrence Matrix</h2>
            <p class="text-sm text-gray-500 mb-4">How often main AOS categories appear together in the same posting (all-time, international jobs). Darker = more frequent co-occurrence.</p>
            <div id="coocMatrixTable" class="overflow-x-auto text-sm"></div>
        </div>

        <!-- Solo vs. Joint -->
        <div class="bg-white rounded-xl shadow-lg p-6 mb-8">
            <h2 class="text-2xl font-bold text-gray-800 mb-1">Solo vs. Joint Hiring</h2>
            <p class="text-sm text-gray-500 mb-4">For each main AOS, jobs listing it as the <em>only</em> area (solo) versus alongside other areas (joint)</p>
            <div style="min-height:300px;">
                <canvas id="soloJointChart"></canvas>
            </div>
        </div>

        <!-- Cross-Cutting Areas -->
        <div class="bg-white rounded-xl shadow-lg p-6 mb-8">
            <div class="flex items-start justify-between mb-3 flex-wrap gap-3">
                <div>
                    <h2 class="text-2xl font-bold text-gray-800 mb-1">Cross-Cutting Areas</h2>
                    <p class="text-sm text-gray-500">Weekly trend for areas that span multiple AOS categories: Feminist Philosophy, Philosophy of Race, Philosophy of Gender, Philosophy of Law. Toggle filters by solo (single-AOS) vs. joint (multi-AOS) listings.</p>
                </div>
                <div class="flex flex-col items-end gap-2">
                    <div class="inline-flex rounded-lg overflow-hidden border border-gray-300 bg-white">
                        <button id="ccModeAll" type="button" onclick="setCcMode('all')" class="px-3 py-1.5 text-sm font-medium bg-cyan-600 text-white">All</button>
                        <button id="ccModeSolo" type="button" onclick="setCcMode('solo')" class="px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-cyan-50">Solo</button>
                        <button id="ccModeJoint" type="button" onclick="setCcMode('joint')" class="px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-cyan-50">Joint</button>
                    </div>
                    <div id="ccModeNote" class="text-xs text-gray-500 italic"></div>
                </div>
            </div>
            <div class="chart-container">
                <canvas id="crossCuttingChart"></canvas>
            </div>
        </div>

        <!-- Geographic Overview -->
        <div class="bg-white rounded-xl shadow-lg p-6 mb-8">
            <div class="flex flex-wrap justify-between items-center mb-6 gap-4">
                <div>
                    <h2 class="text-2xl font-bold text-gray-800">Geographic Overview</h2>
                    <p class="text-sm text-gray-500 mt-1">Hover over countries to see job counts</p>
                </div>
                <div class="flex gap-2">
                    <button id="mapModeNew" onclick="setMapMode('current')" class="px-4 py-2 text-sm font-medium rounded-lg bg-cyan-600 text-white">New This Week</button>
                    <button id="mapModeAll" onclick="setMapMode('alltime')" class="px-4 py-2 text-sm font-medium rounded-lg bg-gray-200 text-gray-700">All-Time</button>
                </div>
            </div>
            <div id="worldMapEl" class="bg-gray-50 rounded-lg overflow-hidden" style="height:500px;">
                <div class="flex items-center justify-center h-full text-gray-400 text-sm">Loading map...</div>
            </div>
            <!-- Top countries list -->
            <div class="mt-4 grid grid-cols-2 md:grid-cols-3 gap-3" id="topCountriesList"></div>
        </div>

        <!-- Position Type Trends -->
        <div class="bg-white rounded-xl shadow-lg p-6 mb-8">
            <div class="flex flex-wrap justify-between items-start mb-2 gap-4">
                <div>
                    <h2 class="text-2xl font-bold text-gray-800">Position Type Trends</h2>
                    <p class="text-sm text-gray-500 mt-1">New jobs per week by position type — filter by AOS to see hiring patterns within each area. Toggle filters by solo (single-AOS) vs. joint (multi-AOS) listings.</p>
                </div>
                <div class="flex flex-col items-end gap-2">
                    <div class="flex flex-wrap gap-2 justify-end">
                        <select id="posTypeAosFilter" onchange="updatePositionTypeChart()" class="text-sm border border-gray-300 rounded-lg px-3 py-2 text-gray-700 bg-white focus:outline-none focus:ring-2 focus:ring-cyan-400">
                            <option value="__all__">All AOS</option>
                        </select>
                        <div class="inline-flex rounded-lg overflow-hidden border border-gray-300 bg-white">
                            <button id="posTypeModeAll" type="button" onclick="setPosTypeMode('all')" class="px-3 py-1.5 text-sm font-medium bg-cyan-600 text-white">All</button>
                            <button id="posTypeModeSolo" type="button" onclick="setPosTypeMode('solo')" class="px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-cyan-50">Solo</button>
                            <button id="posTypeModeJoint" type="button" onclick="setPosTypeMode('joint')" class="px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-cyan-50">Joint</button>
                        </div>
                    </div>
                    <div id="posTypeModeNote" class="text-xs text-gray-500 italic"></div>
                </div>
            </div>
            <div class="chart-container mb-6">
                <canvas id="posTypeChart"></canvas>
            </div>
            <div id="posTypeTable" class="overflow-x-auto text-sm mt-4"></div>
        </div>

        <!-- Category Cards -->
        <div class="bg-white rounded-xl shadow-lg p-6 mb-8">
            <h2 class="text-2xl font-bold text-gray-800 mb-6">Browse by Category</h2>
            <div id="categoryGrid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"></div>
        </div>

        <!-- Category Detail Modal -->
        <div id="detailModal" class="hidden fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
            <div class="bg-white rounded-xl shadow-2xl max-w-6xl w-full max-h-[90vh] overflow-y-auto">
                <div class="sticky top-0 bg-white border-b px-6 py-4 flex justify-between items-center z-10">
                    <h3 id="modalTitle" class="text-2xl font-bold text-gray-800"></h3>
                    <button onclick="closeModal()" class="text-gray-400 hover:text-gray-600">
                        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                        </svg>
                    </button>
                </div>
                <div class="p-6">
                    <div id="subcategorySection" class="mb-6">
                        <h4 class="text-lg font-semibold text-gray-700 mb-4">Subcategories</h4>
                        <div id="subcategoryGrid" class="grid grid-cols-2 md:grid-cols-3 gap-3 mb-6"></div>
                    </div>
                    <div class="mb-6">
                        <h4 class="text-lg font-semibold text-gray-700 mb-4">Trend Over Time</h4>
                        <div class="chart-container"><canvas id="detailChart"></canvas></div>
                    </div>
                    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                        <div class="bg-gray-50 rounded-lg p-4">
                            <div class="text-2xl font-bold text-cyan-600" id="modalCurrentJobs">0</div>
                            <div class="text-sm text-gray-600">New Jobs This Week</div>
                        </div>
                        <div class="bg-gray-50 rounded-lg p-4">
                            <div class="text-2xl font-bold text-green-600" id="modalChange">+0</div>
                            <div class="text-sm text-gray-600">vs Last Week</div>
                        </div>
                        <div class="bg-gray-50 rounded-lg p-4">
                            <div class="text-2xl font-bold text-purple-600" id="modalAverage">0</div>
                            <div class="text-sm text-gray-600">Weekly Average</div>
                        </div>
                        <div class="bg-gray-50 rounded-lg p-4">
                            <div class="text-2xl font-bold text-blue-600" id="modalTotal">0</div>
                            <div class="text-sm text-gray-600">Total All-Time</div>
                        </div>
                    </div>
                    <div id="lassiterSection" class="mb-6">
                        <h4 class="text-lg font-semibold text-gray-700 mb-3">Solo vs. Joint by Subcategory</h4>
                        <div id="lassiterChart" class="overflow-x-auto text-sm"></div>
                    </div>
                    <div class="mb-6 max-w-md">
                        <h4 class="text-lg font-semibold text-gray-700 mb-4">Institution Types</h4>
                        <canvas id="institutionChart"></canvas>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <div id="mapTooltip"></div>

    <script>
        const data = {{
            dates: {json.dumps(dates)},
            totalNewJobsWeekly: {json.dumps(total_new_jobs_weekly)},
            categories: {categories_js},
            subcategoryData: {json.dumps(subcategory_data)},
            jobTypeData: {json.dumps(job_type_series)},
            institutionTypeData: {json.dumps(inst_type_series)},
            intlRegionData: {json.dumps(intl_region_data)},
            countryAlltime: {json.dumps(dict(country_alltime))},
            countryCurrentWeek: {json.dumps(dict(country_current))},
            countryNumeric: {json.dumps(COUNTRY_NUMERIC)},
            numericToCountry: {json.dumps(numeric_to_country)},
            countryCategoryData: {json.dumps(country_category_data)},
            seasonalMarkers: {json.dumps(seasonal_markers)},
            positionTypeByAosWeekly: {json.dumps(position_type_by_aos_weekly)},
            positionTypeXAos: {json.dumps(pos_type_x_aos)},
            positionTypes: {json.dumps(POSITION_TYPES)},
            positionTypeColors: {json.dumps(POSITION_TYPE_COLORS)},
            mainAosColors: {json.dumps(MAIN_AOS_COLORS)},
            mainAosCategories: {json.dumps(MAIN_AOS_CATEGORIES)},
            coocMatrix: {json.dumps(cooc.get('main_aos_matrix', {}))},
            soloVsJoint: {json.dumps(cooc.get('main_aos_solo_vs_joint', {}))},
            crossCutting: {json.dumps(cooc.get('cross_cutting_areas', {}))},
            detailAosByContext: {json.dumps(cooc.get('detail_aos_by_context', {}))},
            jobsForKeyword: {json.dumps(keyword_index)},
            synonymMap: {json.dumps(synonym_map)},
            bubbleStopwords: {json.dumps(bubble_stopwords)},
            subcategoryJobIds: {json.dumps(subcategory_job_ids)},
            jobDetails: {json.dumps(job_details_map)}
        }};

        // ===== SEASON PLUGIN =====
        const seasonPlugin = {{
            id: 'seasonBackground',
            beforeDraw(chart) {{
                const {{ ctx, chartArea, scales }} = chart;
                if (!chartArea || !scales.x) return;
                ctx.save();
                data.seasonalMarkers.forEach(m => {{
                    const x0 = scales.x.getPixelForValue(m.index - 0.5);
                    const x1 = scales.x.getPixelForValue(m.index + 0.5);
                    ctx.fillStyle = 'rgba(251, 191, 36, 0.15)';
                    ctx.fillRect(x0, chartArea.top, x1 - x0, chartArea.bottom - chartArea.top);
                }});
                ctx.restore();
            }}
        }};

        // ===== MARKET OVERVIEW MODE STATE (Intl) =====
        let marketMode = 'all';
        let mainChart = null;
        let currentModalKey = null;

        function catDataFor(cat, mode) {{
            mode = mode || marketMode;
            if (mode === 'solo') return cat.dataSolo;
            if (mode === 'joint') return cat.dataJoint;
            return cat.dataAll;
        }}
        function subDataFor(sub, mode) {{
            mode = mode || marketMode;
            const slot = data.subcategoryData[sub] || {{}};
            return slot[mode] || [];
        }}
        function totalDataFor(mode) {{
            mode = mode || marketMode;
            return data.totalNewJobsWeekly[mode] || [];
        }}

        function renderMainChart() {{
            const mainCtx = document.getElementById('mainChart').getContext('2d');
            if (mainChart) mainChart.destroy();
            const totalLabel = marketMode === 'all' ? 'Total (All Intl)'
                             : marketMode === 'solo' ? 'Total (Solo-AOS)'
                             : 'Total (Joint-AOS)';
            const td = {{
                label: totalLabel, data: totalDataFor(),
                borderColor: '#111827', backgroundColor: 'transparent',
                borderWidth: 2.5, borderDash: [6, 3], tension: 0.4,
                fill: false, pointRadius: 4, pointBackgroundColor: '#111827', order: 0
            }};
            const ds = [td, ...Object.entries(data.categories).map(([key, cat]) => ({{
                label: cat.name, data: catDataFor(cat), borderColor: cat.color,
                backgroundColor: cat.color + '20', tension: 0.4, fill: true, order: 1
            }}))];
            mainChart = new Chart(mainCtx, {{
                type: 'line',
                data: {{ labels: data.dates, datasets: ds }},
                plugins: [seasonPlugin],
                options: {{
                    responsive: true, maintainAspectRatio: false,
                    interaction: {{ mode: 'index', intersect: false }},
                    plugins: {{
                        legend: {{ position: 'bottom', labels: {{ usePointStyle: true, padding: 15, font: {{ size: 12 }} }} }},
                        tooltip: {{ backgroundColor: 'rgba(0,0,0,0.8)', padding: 12 }}
                    }},
                    scales: {{
                        y: {{ beginAtZero: true, ticks: {{ font: {{ size: 12 }} }}, grid: {{ color: 'rgba(0,0,0,0.05)' }} }},
                        x: {{ ticks: {{ font: {{ size: 12 }} }}, grid: {{ display: false }} }}
                    }}
                }}
            }});
        }}

        // ===== CATEGORY CARDS =====
        function renderCategoryCards() {{
            const categoryGrid = document.getElementById('categoryGrid');
            categoryGrid.innerHTML = '';
            Object.entries(data.categories).forEach(([key, cat]) => {{
                const series = catDataFor(cat);
                const currentJobs = series[series.length - 1] || 0;
                const previousJobs = series[series.length - 2] || 0;
                const change = currentJobs - previousJobs;
                const changePercent = previousJobs > 0 ? ((change / previousJobs) * 100).toFixed(1) : 0;
                const card = document.createElement('div');
                card.className = 'category-card bg-white rounded-lg shadow hover:shadow-lg cursor-pointer p-5 border-l-4';
                card.style.borderLeftColor = cat.color;
                card.onclick = () => openModal(key, cat);
                card.innerHTML = `
                    <div class="flex justify-between items-start mb-3">
                        <h3 class="font-semibold text-gray-800 text-lg">${{cat.name}}</h3>
                        <div class="w-3 h-3 rounded-full" style="background-color:${{cat.color}}"></div>
                    </div>
                    <div class="flex items-end justify-between">
                        <div>
                            <div class="text-3xl font-bold text-gray-800">${{currentJobs}}</div>
                            <div class="text-sm text-gray-500">new this week</div>
                        </div>
                        <div class="text-right">
                            <div class="text-sm font-semibold ${{change >= 0 ? 'text-green-600' : 'text-red-600'}}">${{change >= 0 ? '↑' : '↓'}} ${{Math.abs(change)}}</div>
                            <div class="text-xs text-gray-500">${{changePercent}}%</div>
                        </div>
                    </div>
                    ${{cat.subcategories.length > 0 ? `<div class="mt-3 pt-3 border-t border-gray-100"><div class="text-xs text-gray-500">${{cat.subcategories.length}} subcategories</div></div>` : ''}}
                `;
                categoryGrid.appendChild(card);
            }});
        }}

        function updateMarketControls() {{
            const active = 'bg-cyan-600 text-white';
            const inactive = 'text-gray-700 hover:bg-cyan-50';
            document.getElementById('marketModeAll').className   = `px-3 py-1.5 text-sm font-medium ${{marketMode === 'all'   ? active : inactive}}`;
            document.getElementById('marketModeSolo').className  = `px-3 py-1.5 text-sm font-medium ${{marketMode === 'solo'  ? active : inactive}}`;
            document.getElementById('marketModeJoint').className = `px-3 py-1.5 text-sm font-medium ${{marketMode === 'joint' ? active : inactive}}`;
            document.getElementById('marketModeNote').textContent =
                marketMode === 'all'   ? 'All: every AOS tag counts (joint jobs add to multiple lines).' :
                marketMode === 'solo'  ? 'Solo: only jobs with exactly one AOS category.' :
                                         'Joint: only jobs listing multiple AOS categories; each tag still counts.';
        }}

        function setMarketMode(mode) {{
            marketMode = mode;
            renderMainChart();
            renderCategoryCards();
            updateMarketControls();
            if (currentModalKey && !document.getElementById('detailModal').classList.contains('hidden')) {{
                openModal(currentModalKey, data.categories[currentModalKey]);
            }}
        }}

        renderMainChart();
        renderCategoryCards();
        updateMarketControls();

        // ===== MODAL =====
        let detailChart = null, institutionChart = null;

        function openModal(key, category) {{
            currentModalKey = key;
            const catSeries = catDataFor(category);
            const currentJobs = catSeries[catSeries.length - 1] || 0;
            const previousJobs = catSeries[catSeries.length - 2] || 0;
            const change = currentJobs - previousJobs;
            const average = catSeries.length > 0 ? (catSeries.reduce((a, b) => a + b, 0) / catSeries.length).toFixed(1) : '0.0';
            const total = catSeries.reduce((a, b) => a + b, 0);

            document.getElementById('modalTitle').textContent = category.name + (marketMode === 'all' ? '' : ` — ${{marketMode}}`);
            document.getElementById('modalCurrentJobs').textContent = currentJobs;
            document.getElementById('modalChange').textContent = (change >= 0 ? '+' : '') + change;
            document.getElementById('modalChange').className = 'text-2xl font-bold ' + (change >= 0 ? 'text-green-600' : 'text-red-600');
            document.getElementById('modalAverage').textContent = average;
            document.getElementById('modalTotal').textContent = total;

            // Subcategories — each card includes a "Download report" button
            // that generates a multi-page PDF with the full posting for each
            // job tagged with that subcategory.
            const subcatGrid = document.getElementById('subcategoryGrid');
            document.getElementById('subcategorySection').style.display = category.subcategories.length > 0 ? 'block' : 'none';
            let subcatHtml = '';
            category.subcategories.forEach(sub => {{
                const subSeries = subDataFor(sub);
                const subTotal = subSeries.reduce((a, b) => a + b, 0);
                const subCurrent = subSeries[subSeries.length - 1] || 0;
                const soloJointData = data.detailAosByContext[sub] || {{}};
                const solo = Object.values(soloJointData.solo || {{}}).reduce((a, b) => a + b, 0);
                const joint = Object.values(soloJointData.with_others || {{}}).reduce((a, b) => a + b, 0);
                const jobIds = data.subcategoryJobIds[sub] || [];
                const jobCount = jobIds.length;
                const escapedSub = sub.replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
                const downloadBtn = jobCount > 0
                    ? `<button data-download-sub="${{escapedSub}}" class="mt-2 w-full text-xs px-2 py-1.5 bg-cyan-600 text-white rounded hover:bg-cyan-700 font-medium">📄 Download report (${{jobCount}} job${{jobCount === 1 ? '' : 's'}})</button>`
                    : `<div class="mt-2 text-xs text-gray-400 text-center">No jobs yet</div>`;
                subcatHtml += `
                    <div class="bg-gray-50 rounded-lg p-3 flex flex-col">
                        <div class="font-medium text-gray-800 text-sm mb-1">${{sub}}</div>
                        <div class="text-xs text-gray-500">${{subTotal}} total · ${{subCurrent}} this week</div>
                        ${{(solo + joint) > 0 ? `<div class="text-xs text-indigo-600 mt-1">Solo: ${{solo}} · Joint: ${{joint}}</div>` : ''}}
                        ${{downloadBtn}}
                    </div>`;
            }});
            subcatGrid.innerHTML = subcatHtml;
            subcatGrid.querySelectorAll('button[data-download-sub]').forEach(btn => {{
                btn.addEventListener('click', e => {{
                    downloadSubcategoryReport(e.currentTarget.dataset.downloadSub);
                }});
            }});

            // Trend chart
            const ctx = document.getElementById('detailChart').getContext('2d');
            if (detailChart) detailChart.destroy();
            detailChart = new Chart(ctx, {{
                type: 'line',
                data: {{ labels: data.dates, datasets: [{{ label: category.name, data: catSeries, borderColor: category.color, backgroundColor: category.color + '30', tension: 0.4, fill: true }}] }},
                plugins: [seasonPlugin],
                options: {{
                    responsive: true, maintainAspectRatio: false,
                    plugins: {{ legend: {{ display: false }} }},
                    scales: {{ y: {{ beginAtZero: true }}, x: {{ grid: {{ display: false }} }} }}
                }}
            }});

            // Lassiter
            const lassiterDiv = document.getElementById('lassiterChart');
            const lassiterSection = document.getElementById('lassiterSection');
            if (category.subcategories.length > 0) {{
                lassiterSection.style.display = 'block';
                const rows = category.subcategories.map(sub => {{
                    const ctx2 = data.detailAosByContext[sub] || {{}};
                    const solo = Object.values(ctx2.solo || {{}}).reduce((a, b) => a + b, 0);
                    const joint = Object.values(ctx2.with_others || {{}}).reduce((a, b) => a + b, 0);
                    const total2 = ctx2.total || 0;
                    return {{ sub, solo, joint, total: total2 }};
                }}).filter(r => r.total > 0).sort((a, b) => b.total - a.total);
                if (rows.length > 0) {{
                    let tableHtml = '<table class="w-full border-collapse text-xs"><thead><tr><th class="text-left py-2 px-3 bg-gray-50 border border-gray-200">Subcategory</th><th class="py-2 px-2 bg-gray-50 border border-gray-200 text-center">Total</th><th class="py-2 px-2 bg-gray-50 border border-gray-200 text-center text-indigo-700">Solo</th><th class="py-2 px-2 bg-gray-50 border border-gray-200 text-center text-purple-700">Joint</th></tr></thead><tbody>';
                    rows.forEach((r, i) => {{
                        tableHtml += `<tr class="${{i % 2 === 0 ? 'bg-white' : 'bg-gray-50'}}"><td class="py-2 px-3 border border-gray-200 font-medium">${{r.sub}}</td><td class="py-2 px-2 border border-gray-200 text-center font-bold">${{r.total}}</td><td class="py-2 px-2 border border-gray-200 text-center text-indigo-700">${{r.solo}}</td><td class="py-2 px-2 border border-gray-200 text-center text-purple-700">${{r.joint}}</td></tr>`;
                    }});
                    lassiterDiv.innerHTML = tableHtml + '</tbody></table>';
                }} else {{
                    lassiterDiv.innerHTML = '<div class="text-gray-400 text-sm">No co-occurrence data yet.</div>';
                }}
            }} else {{
                lassiterSection.style.display = 'none';
            }}

            // Institution Types
            const instCtx = document.getElementById('institutionChart').getContext('2d');
            if (institutionChart) institutionChart.destroy();
            const instCurrent = ['Research University', 'Teaching College', 'Other'].map(it => {{
                const arr = data.institutionTypeData[it] || [];
                return arr[arr.length - 1] || 0;
            }});
            institutionChart = new Chart(instCtx, {{
                type: 'doughnut',
                data: {{ labels: ['Research University', 'Teaching College', 'Other'], datasets: [{{ data: instCurrent, backgroundColor: ['#6366f1', '#10b981', '#6b7280'] }}] }},
                options: {{ responsive: true, plugins: {{ legend: {{ position: 'right', labels: {{ font: {{ size: 11 }}, boxWidth: 12 }} }} }} }}
            }});

            document.getElementById('detailModal').classList.remove('hidden');
        }}

        function closeModal() {{
            document.getElementById('detailModal').classList.add('hidden');
            currentModalKey = null;
            if (detailChart) {{ detailChart.destroy(); detailChart = null; }}
            if (institutionChart) {{ institutionChart.destroy(); institutionChart = null; }}
        }}
        document.getElementById('detailModal').addEventListener('click', function(e) {{
            if (e.target === this) closeModal();
        }});

        // ===== SUBCATEGORY DOWNLOAD REPORT (PDF) =====
        // Generates a multi-page PDF where each page is the full job posting
        // for a job tagged with the given subcategory. Uses jsPDF (UMD CDN).
        function downloadSubcategoryReport(subcategoryName) {{
            const jobIds = data.subcategoryJobIds[subcategoryName] || [];
            if (jobIds.length === 0) {{
                alert('No jobs available for "' + subcategoryName + '" yet.');
                return;
            }}
            if (!window.jspdf) {{
                alert('PDF library failed to load — try reloading the page.');
                return;
            }}
            const {{ jsPDF }} = window.jspdf;
            const doc = new jsPDF({{ unit: 'pt', format: 'letter' }});
            const margin = 50;
            const pageWidth = doc.internal.pageSize.getWidth();
            const pageHeight = doc.internal.pageSize.getHeight();
            const contentWidth = pageWidth - 2 * margin;
            const bottomLimit = pageHeight - margin;

            // jsPDF's default Helvetica handles Latin-1. Strip combining marks
            // for any text outside that range so it doesn't render as "?" boxes.
            const ascii = s => (s || '').toString().normalize('NFKD').replace(/[\\u0300-\\u036f]/g, '');

            jobIds.forEach((jid, idx) => {{
                const job = data.jobDetails[jid];
                if (!job) return;
                if (idx > 0) doc.addPage();
                let y = margin;

                const writeBlock = (text, fontSize, bold, color) => {{
                    if (!text) return;
                    doc.setFontSize(fontSize);
                    doc.setFont('helvetica', bold ? 'bold' : 'normal');
                    doc.setTextColor(color || 0);
                    const lines = doc.splitTextToSize(ascii(text), contentWidth);
                    lines.forEach(line => {{
                        if (y > bottomLimit) {{
                            doc.addPage();
                            y = margin;
                        }}
                        doc.text(line, margin, y);
                        y += fontSize * 1.25;
                    }});
                }};

                writeBlock(job.title || 'Untitled position', 14, true);
                writeBlock(job.institution || '', 11, false);
                y += 6;
                doc.setDrawColor(200);
                doc.line(margin, y, pageWidth - margin, y);
                y += 14;

                // Header strip — subcategory + position in batch
                writeBlock(`Subcategory: ${{subcategoryName}}  ·  Job ${{idx + 1}} of ${{jobIds.length}}`, 9, false, 120);
                y += 4;

                // Metadata
                const meta = [
                    ['Location', job.location],
                    ['Posted',   job.posted_date],
                    ['Deadline', job.deadline],
                    ['Start date', job.start_date],
                    ['Job category', job.job_category],
                    ['AOS', job.aos],
                    ['AOC', job.aoc],
                    ['Workload', job.workload],
                    ['Vacancies', job.vacancies],
                    ['Application type', job.application_type],
                    ['Application URL', job.application_url],
                    ['Contact', job.contact_email],
                    ['PhilJobs URL', job.url],
                ];
                meta.forEach(([k, v]) => {{
                    if (!v) return;
                    writeBlock(`${{k}}: ${{v}}`, 9, false);
                }});
                y += 10;

                writeBlock('Description', 11, true);
                writeBlock(job.description || 'No description recorded for this posting.', 10, false);
            }});

            const safeName = subcategoryName.replace(/[^a-z0-9]+/gi, '_').toLowerCase();
            const dateStr = new Date().toISOString().slice(0, 10);
            doc.save(`philjobs_${{safeName}}_${{dateStr}}.pdf`);
        }}

        // ===== REGIONAL CHART =====
        const regionColors = {{
            'Europe': '#2563eb', 'Canada': '#dc2626', 'Asia-Pacific': '#16a34a',
            'Latin America': '#d97706', 'Middle East & Africa': '#9333ea'
        }};
        let regionMode = 'all';
        let regionalChart = null;

        function regionDataFor(region, mode) {{
            mode = mode || regionMode;
            const slot = data.intlRegionData[region] || {{}};
            return slot[mode] || [];
        }}

        function renderRegionalChart() {{
            const ctx = document.getElementById('regionalChart').getContext('2d');
            if (regionalChart) regionalChart.destroy();
            regionalChart = new Chart(ctx, {{
                type: 'line',
                data: {{
                    labels: data.dates,
                    datasets: Object.keys(data.intlRegionData).map(region => ({{
                        label: region,
                        data: regionDataFor(region),
                        borderColor: regionColors[region] || '#6b7280',
                        backgroundColor: (regionColors[region] || '#6b7280') + '20',
                        tension: 0.4, fill: true, borderWidth: 2, pointRadius: 4
                    }}))
                }},
                options: {{
                    responsive: true, maintainAspectRatio: false,
                    interaction: {{ mode: 'index', intersect: false }},
                    plugins: {{ legend: {{ position: 'bottom', labels: {{ usePointStyle: true, padding: 15, font: {{ size: 12 }} }} }} }},
                    scales: {{ y: {{ beginAtZero: true }}, x: {{ grid: {{ display: false }} }} }}
                }}
            }});
        }}

        function updateRegionControls() {{
            const active = 'bg-cyan-600 text-white';
            const inactive = 'text-gray-700 hover:bg-cyan-50';
            document.getElementById('regionModeAll').className   = `px-3 py-1.5 text-sm font-medium ${{regionMode === 'all'   ? active : inactive}}`;
            document.getElementById('regionModeSolo').className  = `px-3 py-1.5 text-sm font-medium ${{regionMode === 'solo'  ? active : inactive}}`;
            document.getElementById('regionModeJoint').className = `px-3 py-1.5 text-sm font-medium ${{regionMode === 'joint' ? active : inactive}}`;
            document.getElementById('regionModeNote').textContent =
                regionMode === 'all'   ? 'All: counts every job in each region per week.' :
                regionMode === 'solo'  ? 'Solo: only jobs with exactly one AOS category.' :
                                         'Joint: only jobs listing multiple AOS categories.';
        }}

        function setRegionMode(mode) {{
            regionMode = mode;
            renderRegionalChart();
            updateRegionControls();
        }}

        renderRegionalChart();
        updateRegionControls();

        // ===== CO-OCCURRENCE MATRIX =====
        const matrixDiv = document.getElementById('coocMatrixTable');
        const matrixCats = data.mainAosCategories;
        let matrixHtml = '<table class="border-collapse text-xs"><thead><tr><th class="p-2 bg-gray-50 border border-gray-200"></th>';
        const shortNames = {{ 'Ethics': 'Ethics', 'Social & Political Philosophy': 'Soc/Pol', 'Value Theory / Aesthetics': 'Value/Aes', 'History of Philosophy': 'History', 'Non-Western & Cross-Cultural Philosophy': 'Non-West', 'Metaphysics & Epistemology': 'M&E', 'Science, Logic, & Mathematics': 'Sci/Log', 'Open': 'Open' }};
        matrixCats.forEach(c => {{ matrixHtml += `<th class="p-2 bg-gray-50 border border-gray-200 font-semibold text-gray-700" title="${{c}}">${{shortNames[c] || c}}</th>`; }});
        matrixHtml += '</tr></thead><tbody>';
        const allVals = matrixCats.flatMap(r => matrixCats.map(c => r !== c ? (data.coocMatrix[r]?.[c] || 0) : 0));
        const maxCoocVal = Math.max(...allVals, 1);
        matrixCats.forEach((row, ri) => {{
            matrixHtml += `<tr><td class="p-2 bg-gray-50 border border-gray-200 font-semibold text-gray-700 whitespace-nowrap">${{shortNames[row] || row}}</td>`;
            matrixCats.forEach((col, ci) => {{
                if (row === col) {{
                    matrixHtml += '<td class="p-2 border border-gray-200 bg-gray-100 text-center text-gray-300">—</td>';
                }} else {{
                    const v = data.coocMatrix[row]?.[col] || 0;
                    const intensity = v > 0 ? Math.max(0.1, v / maxCoocVal) : 0;
                    const bg = v > 0 ? `rgba(8,145,178,${{intensity.toFixed(2)}})` : '#f9fafb';
                    const color = intensity > 0.5 ? 'white' : '#374151';
                    matrixHtml += `<td class="p-2 border border-gray-200 text-center font-medium" style="background:${{bg}};color:${{color}}" title="${{row}} ↔ ${{col}}: ${{v}}">${{v > 0 ? v : ''}}</td>`;
                }}
            }});
            matrixHtml += '</tr>';
        }});
        matrixDiv.innerHTML = matrixHtml + '</tbody></table>';

        // ===== SOLO VS JOINT CHART =====
        const svjCats = Object.keys(data.soloVsJoint).filter(k => data.soloVsJoint[k].solo > 0 || data.soloVsJoint[k].joint > 0);
        new Chart(document.getElementById('soloJointChart').getContext('2d'), {{
            type: 'bar',
            data: {{
                labels: svjCats,
                datasets: [
                    {{ label: 'Solo', data: svjCats.map(k => data.soloVsJoint[k].solo || 0), backgroundColor: '#0891b2', borderRadius: 3 }},
                    {{ label: 'Joint', data: svjCats.map(k => data.soloVsJoint[k].joint || 0), backgroundColor: '#67e8f9', borderRadius: 3 }}
                ]
            }},
            options: {{
                responsive: true, maintainAspectRatio: false,
                plugins: {{ legend: {{ position: 'bottom' }} }},
                scales: {{ x: {{ stacked: false }}, y: {{ beginAtZero: true, stacked: false }} }}
            }}
        }});

        // ===== KEYWORD EXPLORER =====
        // Searches job description text only. Synonyms come from a synonym map
        // generated weekly by Claude at scrape time and embedded as data.synonymMap.
        let kwTrendChart = null;

        // Recursive morphological stemmer. Applies suffix rules until stable
        // so "feminists" → "feminist" → "femin" all collapse to one stem.
        // Mirrors the Python _keyword_stem method.
        function kwStem(word) {{
            word = word.toLowerCase().replace(/[^a-z]/g, '');
            let prev = null;
            while (prev !== word && word.length > 3) {{
                prev = word;
                if (word.endsWith('ies'))      word = word.slice(0, -3) + 'y';
                else if (word.endsWith('ism')) word = word.slice(0, -3);
                else if (word.endsWith('ist')) word = word.slice(0, -3);
                else if (word.endsWith('ing')) word = word.slice(0, -3);
                else if (word.endsWith('ed'))  word = word.slice(0, -2);
                else if (word.endsWith('es'))  word = word.slice(0, -2);
                else if (word.endsWith('s'))   word = word.slice(0, -1);
            }}
            return word;
        }}

        // Expand a query into a set of related terms via the synonym map + stemming
        function kwExpand(query) {{
            const q = query.toLowerCase().trim();
            if (!q) return new Set();
            const stem = kwStem(q);
            const terms = new Set([q, stem]);
            // Synonym map lookup (Claude-generated)
            const syns = data.synonymMap[q] || data.synonymMap[stem] || [];
            syns.forEach(s => {{
                terms.add(s.toLowerCase());
                terms.add(kwStem(s));
            }});
            return terms;
        }}

        // Test whether a job's description-term set matches any of the expanded terms.
        // Stems both sides so morphological variants ("feminist" vs "feminism") match.
        function kwJobMatches(jobStemSet, expandedTerms) {{
            for (const t of expandedTerms) {{
                if (jobStemSet.has(kwStem(t))) return true;
            }}
            return false;
        }}

        function kwSearch() {{
            const raw = document.getElementById('kwInput').value;
            const q = raw.trim();
            if (!q) {{
                document.getElementById('kwEmptyState').classList.remove('hidden');
                document.getElementById('kwResults').classList.add('hidden');
                document.getElementById('kwMatchCount').textContent = '';
                return;
            }}

            const expanded = kwExpand(q);
            const matchingJobs = [];
            data.jobsForKeyword.forEach((j) => {{
                // Build a set of stems for this job (cached per search is fine for now)
                if (!j._stemSet) {{
                    j._stemSet = new Set();
                    for (const t of j.terms) j._stemSet.add(kwStem(t));
                }}
                if (kwJobMatches(j._stemSet, expanded)) matchingJobs.push(j);
            }});

            const matchCount = matchingJobs.length;
            const expansionStr = Array.from(expanded).filter(t => t !== q.toLowerCase()).slice(0, 8).join(', ');
            document.getElementById('kwMatchCount').innerHTML =
                `<strong>${{matchCount}}</strong> job${{matchCount === 1 ? '' : 's'}} match` +
                (expansionStr ? ` &middot; <span class="text-gray-500">expanded to: ${{expansionStr}}</span>` : '');

            if (matchCount === 0) {{
                document.getElementById('kwEmptyState').classList.remove('hidden');
                document.getElementById('kwEmptyState').textContent = `No jobs found containing "${{q}}" or related terms. Try a broader term or check the bubble suggestions from another search.`;
                document.getElementById('kwResults').classList.add('hidden');
                return;
            }}

            document.getElementById('kwEmptyState').classList.add('hidden');
            document.getElementById('kwResults').classList.remove('hidden');

            // Build bubble chart from the synonym map (field-defining alternatives),
            // NOT from corpus co-occurrence. Each bubble = a synonym, sized by how
            // many jobs in the corpus contain that specific term (via stem matching).
            // This surfaces "what are the other names the field uses for this
            // concept" rather than "what words show up alongside this in postings".
            const qLower = q.toLowerCase();
            const queryStem = kwStem(qLower);
            const synonymList = data.synonymMap[qLower] || data.synonymMap[queryStem] || [];
            // Build the candidate set: query + synonyms, deduped by stem
            const stemToBubble = new Map();
            const addBubble = (rawTerm, isQuery) => {{
                const s = kwStem(rawTerm.toLowerCase());
                if (!s) return;
                if (stemToBubble.has(s)) {{
                    // Keep longest label
                    const existing = stemToBubble.get(s);
                    if (rawTerm.length > existing.label.length) existing.label = rawTerm;
                    if (isQuery) existing.isQuery = true;
                }} else {{
                    stemToBubble.set(s, {{ label: rawTerm, isQuery: !!isQuery, stem: s }});
                }}
            }};
            addBubble(qLower, true);
            synonymList.forEach(syn => addBubble(syn, false));

            // For each candidate stem, count how many jobs in the corpus contain it
            const bubbles = [];
            for (const [stem, entry] of stemToBubble) {{
                let count = 0;
                for (const j of data.jobsForKeyword) {{
                    if (j._stemSet.has(stem)) count++;
                }}
                bubbles.push({{ label: entry.label, count, isQuery: entry.isQuery }});
            }}
            // Sort: query first, then by count desc
            bubbles.sort((a, b) => {{
                if (a.isQuery && !b.isQuery) return -1;
                if (!a.isQuery && b.isQuery) return 1;
                return b.count - a.count;
            }});
            renderBubbleChart(q, bubbles, matchCount);

            // Trend chart: matching-job count per week
            const weekCounts = {{}};
            data.dates.forEach(d => {{ weekCounts[d] = 0; }});
            matchingJobs.forEach(j => {{
                if (weekCounts[j.scraped_date] !== undefined) weekCounts[j.scraped_date]++;
            }});
            renderKwTrend(data.dates.map(d => weekCounts[d]), q);
        }}

        function renderBubbleChart(query, bubbles, totalMatches) {{
            const container = document.getElementById('kwBubble');
            container.innerHTML = '';
            const width = container.clientWidth || 400;
            const height = 340;

            // If we have no synonyms AND the query has no matches, show a helpful empty state
            if (bubbles.length === 0) {{
                container.innerHTML = '<div class="text-gray-400 text-center py-12 text-sm">No field-defining synonyms found for this term in our map. The map covers the top 150 most frequent corpus terms — your term may be rare or use vocabulary the field doesn\\'t yet emphasize.</div>';
                return;
            }}

            // Convert bubble entries to D3 node format
            const nodes = bubbles.map(b => ({{
                id: b.label,
                count: b.count,
                isQuery: b.isQuery
            }}));
            const maxCount = Math.max(1, ...nodes.map(n => n.count));
            const minR = 18, maxR = 55;
            nodes.forEach(n => {{
                // Minimum size for query bubble even when 0 matches
                const safeCount = (n.isQuery && n.count === 0) ? 0.5 : n.count;
                n.r = minR + (maxR - minR) * Math.sqrt(Math.max(safeCount, 0) / maxCount);
                if (n.r < minR) n.r = minR;
            }});

            const svg = d3.select(container).append('svg')
                .attr('width', '100%').attr('height', height)
                .attr('viewBox', `0 0 ${{width}} ${{height}}`);

            const simulation = d3.forceSimulation(nodes)
                .force('charge', d3.forceManyBody().strength(5))
                .force('center', d3.forceCenter(width / 2, height / 2))
                .force('collide', d3.forceCollide(d => d.r + 2))
                .force('x', d3.forceX(width / 2).strength(0.05))
                .force('y', d3.forceY(height / 2).strength(0.05));

            const node = svg.selectAll('g').data(nodes).enter().append('g')
                .style('cursor', d => d.isQuery ? 'default' : 'pointer')
                .on('click', (event, d) => {{
                    if (d.isQuery) return;
                    document.getElementById('kwInput').value = d.id;
                    kwSearch();
                }});

            node.append('circle')
                .attr('r', d => d.r)
                .attr('fill', d => d.isQuery ? '#4f46e5' : '#a5b4fc')
                .attr('fill-opacity', d => d.isQuery ? 0.95 : 0.7)
                .attr('stroke', d => d.isQuery ? '#3730a3' : '#6366f1')
                .attr('stroke-width', 1.5);

            node.append('text')
                .text(d => d.id)
                .attr('text-anchor', 'middle')
                .attr('dominant-baseline', 'middle')
                .attr('fill', d => d.isQuery ? 'white' : '#1e1b4b')
                .attr('font-size', d => Math.max(10, Math.min(d.r * 0.45, 16)) + 'px')
                .attr('font-weight', d => d.isQuery ? '700' : '500')
                .style('pointer-events', 'none');

            node.append('title').text(d => `${{d.id}}: ${{d.count}} job${{d.count === 1 ? '' : 's'}}`);

            simulation.on('tick', () => {{
                node.attr('transform', d => `translate(${{d.x}}, ${{d.y}})`);
            }});
        }}

        function renderKwTrend(weekData, query) {{
            const ctx = document.getElementById('kwTrendChart').getContext('2d');
            if (kwTrendChart) kwTrendChart.destroy();
            kwTrendChart = new Chart(ctx, {{
                type: 'line',
                data: {{
                    labels: data.dates,
                    datasets: [{{
                        label: `Jobs matching "${{query}}"`,
                        data: weekData,
                        borderColor: '#4f46e5',
                        backgroundColor: '#a5b4fc40',
                        tension: 0.4, fill: true, borderWidth: 2, pointRadius: 4
                    }}]
                }},
                plugins: [seasonPlugin],
                options: {{
                    responsive: true, maintainAspectRatio: false,
                    plugins: {{ legend: {{ display: false }} }},
                    scales: {{
                        y: {{ beginAtZero: true, ticks: {{ precision: 0 }} }},
                        x: {{ grid: {{ display: false }}, ticks: {{ maxTicksLimit: 8 }} }}
                    }}
                }}
            }});
        }}

        document.getElementById('kwSearchBtn').addEventListener('click', kwSearch);
        document.getElementById('kwInput').addEventListener('keydown', e => {{
            if (e.key === 'Enter') kwSearch();
        }});

        // ===== POSITION TYPE CHART (with All/Solo/Joint toggle) =====
        let posTypeChart = null;
        let posTypeMode = 'all';
        const posTypeSelect = document.getElementById('posTypeAosFilter');
        data.mainAosCategories.forEach(aos => {{
            const opt = document.createElement('option');
            opt.value = aos;
            opt.textContent = aos;
            posTypeSelect.appendChild(opt);
        }});

        function ptSeriesFor(pt, aosFilter, mode) {{
            mode = mode || posTypeMode;
            if (aosFilter === '__all__') {{
                return (data.jobTypeData[pt] || {{}})[mode] || Array(data.dates.length).fill(0);
            }}
            const aosSlot = data.positionTypeByAosWeekly[aosFilter] || {{}};
            const ptSlot = aosSlot[pt] || {{}};
            return ptSlot[mode] || Array(data.dates.length).fill(0);
        }}

        function updatePositionTypeChart() {{
            const selected = posTypeSelect.value;
            const ptDatasets = data.positionTypes.map(pt => ({{
                label: pt,
                data: ptSeriesFor(pt, selected),
                borderColor: data.positionTypeColors[pt] || '#6b7280',
                backgroundColor: (data.positionTypeColors[pt] || '#6b7280') + '30',
                tension: 0.4, fill: true, borderWidth: 2, pointRadius: 3
            }}));
            if (posTypeChart) posTypeChart.destroy();
            posTypeChart = new Chart(document.getElementById('posTypeChart').getContext('2d'), {{
                type: 'line',
                data: {{ labels: data.dates, datasets: ptDatasets }},
                plugins: [seasonPlugin],
                options: {{
                    responsive: true, maintainAspectRatio: false,
                    interaction: {{ mode: 'index', intersect: false }},
                    plugins: {{ legend: {{ position: 'bottom', labels: {{ usePointStyle: true, padding: 12, font: {{ size: 11 }} }} }} }},
                    scales: {{ y: {{ beginAtZero: true }}, x: {{ grid: {{ display: false }} }} }}
                }}
            }});

            // Summary table — uses all-time pos_type_x_aos sliced by current mode
            const xAos = data.positionTypeXAos[posTypeMode] || {{}};
            const tableDiv = document.getElementById('posTypeTable');
            const aosRows = data.mainAosCategories;
            let html = '<table class="w-full border-collapse"><thead><tr>';
            html += '<th class="text-left py-2 px-3 bg-gray-50 font-semibold text-gray-700 border border-gray-200 text-sm">AOS Category</th>';
            data.positionTypes.forEach(pt => {{
                const short = pt.replace('Visiting / Adjunct / Lecturer (Fixed-Term)', 'Visiting/Adj/Lect').replace('Tenured / Continuing / Permanent', 'Tenured/Perm').replace('Postdoc / Fellowship', 'Postdoc/Fellow');
                html += `<th class="py-2 px-2 bg-gray-50 font-semibold border border-gray-200 text-center text-xs" style="color:${{data.positionTypeColors[pt] || '#6b7280'}}" title="${{pt}}">${{short}}</th>`;
            }});
            html += '<th class="py-2 px-3 bg-gray-50 font-semibold text-gray-700 border border-gray-200 text-center text-sm">Total</th></tr></thead><tbody>';
            aosRows.forEach((aos, i) => {{
                const row = xAos[aos] || {{}};
                const rowTotal = data.positionTypes.reduce((s, pt) => s + (row[pt] || 0), 0);
                if (rowTotal === 0) return;
                html += `<tr class="${{i % 2 === 0 ? 'bg-white' : 'bg-gray-50'}}">`;
                html += `<td class="py-2 px-3 font-medium text-gray-700 border border-gray-200 text-sm">${{aos}}</td>`;
                data.positionTypes.forEach(pt => {{
                    const v = row[pt] || 0;
                    const pct = rowTotal > 0 ? Math.round(v / rowTotal * 100) : 0;
                    html += `<td class="py-2 px-2 text-center border border-gray-200 text-xs ${{v > 0 ? 'font-semibold text-gray-800' : 'text-gray-300'}}">${{v > 0 ? `${{v}}<div class="text-gray-400 font-normal">${{pct}}%</div>` : '—'}}</td>`;
                }});
                html += `<td class="py-2 px-3 text-center font-bold text-cyan-600 border border-gray-200 text-sm">${{rowTotal}}</td></tr>`;
            }});
            html += '</tbody></table>';
            tableDiv.innerHTML = html;
        }}

        function updatePosTypeControls() {{
            const active = 'bg-cyan-600 text-white';
            const inactive = 'text-gray-700 hover:bg-cyan-50';
            document.getElementById('posTypeModeAll').className   = `px-3 py-1.5 text-sm font-medium ${{posTypeMode === 'all'   ? active : inactive}}`;
            document.getElementById('posTypeModeSolo').className  = `px-3 py-1.5 text-sm font-medium ${{posTypeMode === 'solo'  ? active : inactive}}`;
            document.getElementById('posTypeModeJoint').className = `px-3 py-1.5 text-sm font-medium ${{posTypeMode === 'joint' ? active : inactive}}`;
            document.getElementById('posTypeModeNote').textContent =
                posTypeMode === 'all'   ? 'All: every job counted (joint jobs add to multiple AOS rows in the table).' :
                posTypeMode === 'solo'  ? 'Solo: only jobs with exactly one AOS category.' :
                                          'Joint: only jobs listing multiple AOS categories.';
        }}

        function setPosTypeMode(mode) {{
            posTypeMode = mode;
            updatePositionTypeChart();
            updatePosTypeControls();
        }}

        updatePositionTypeChart();
        updatePosTypeControls();

        // ===== WORLD CHOROPLETH =====
        let currentMapMode = 'current', worldAtlasData = null;

        function getCountryValues(mode) {{
            return mode === 'alltime' ? data.countryAlltime : data.countryCurrentWeek;
        }}

        function setMapMode(mode) {{
            currentMapMode = mode;
            document.getElementById('mapModeNew').className = mode === 'current' ? 'px-4 py-2 text-sm font-medium rounded-lg bg-cyan-600 text-white' : 'px-4 py-2 text-sm font-medium rounded-lg bg-gray-200 text-gray-700';
            document.getElementById('mapModeAll').className = mode === 'alltime' ? 'px-4 py-2 text-sm font-medium rounded-lg bg-cyan-600 text-white' : 'px-4 py-2 text-sm font-medium rounded-lg bg-gray-200 text-gray-700';
            if (worldAtlasData) drawWorldChoropleth();
            updateTopCountries();
        }}

        function drawWorldChoropleth() {{
            const el = document.getElementById('worldMapEl');
            el.innerHTML = '';
            const countryValues = getCountryValues(currentMapMode);
            const numericVals = {{}};
            Object.entries(data.countryNumeric).forEach(([country, code]) => {{
                numericVals[code] = Math.max(numericVals[code] || 0, countryValues[country] || 0);
            }});
            const maxVal = Math.max(...Object.values(numericVals).filter(v => v > 0), 1);
            const width = el.clientWidth || 900, height = 500;
            const features = topojson.feature(worldAtlasData, worldAtlasData.objects.countries).features;
            const projection = d3.geoNaturalEarth1().fitSize([width, height], {{type: 'FeatureCollection', features}});
            const path = d3.geoPath().projection(projection);
            const svg = d3.select('#worldMapEl').append('svg').attr('width', '100%').attr('height', height).attr('viewBox', `0 0 ${{width}} ${{height}}`);
            const tip = d3.select('#mapTooltip');
            svg.append('g').selectAll('path').data(features).join('path')
                .attr('d', path)
                .attr('fill', d => {{
                    const code = String(d.id).padStart(3, '0');
                    const v = numericVals[code] || 0;
                    if (v === 0) return '#e5e7eb';
                    return d3.interpolate('#a5f3fc', '#0e7490')(v / maxVal);
                }})
                .attr('stroke', '#9ca3af').attr('stroke-width', 0.3)
                .on('mouseover', function(event, d) {{
                    const code = String(d.id).padStart(3, '0');
                    const country = data.numericToCountry[code] || '';
                    const v = numericVals[code] || 0;
                    if (v === 0 && !country) return;
                    tip.style('display', 'block').html(`<strong>${{country || 'Unknown'}}</strong><br>${{v}} job${{v !== 1 ? 's' : ''}}`);
                    d3.select(this).attr('stroke', '#111').attr('stroke-width', 1.5);
                }})
                .on('mousemove', event => tip.style('left', (event.pageX + 12) + 'px').style('top', (event.pageY - 28) + 'px'))
                .on('mouseout', function() {{
                    tip.style('display', 'none');
                    d3.select(this).attr('stroke', '#9ca3af').attr('stroke-width', 0.3);
                }});
        }}

        function updateTopCountries() {{
            const countryValues = getCountryValues(currentMapMode);
            const sorted = Object.entries(countryValues).sort((a, b) => b[1] - a[1]).slice(0, 12);
            const listEl = document.getElementById('topCountriesList');
            if (sorted.length === 0) {{
                listEl.innerHTML = '<div class="text-gray-400 text-sm col-span-3">No international data yet</div>';
                return;
            }}
            listEl.innerHTML = sorted.map(([c, n]) => `
                <div class="bg-gray-50 rounded-lg px-3 py-2 flex justify-between items-center">
                    <span class="text-sm text-gray-700 font-medium">${{c}}</span>
                    <span class="text-sm font-bold text-cyan-700">${{n}}</span>
                </div>`).join('');
        }}

        async function initMaps() {{
            try {{
                worldAtlasData = await d3.json('https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json');
                drawWorldChoropleth();
                updateTopCountries();
            }} catch(e) {{
                document.getElementById('worldMapEl').innerHTML = '<div class="text-gray-400 text-center p-4 text-sm">Map unavailable — check connection</div>';
            }}
        }}
        initMaps();
    </script>
</body>
</html>'''

        docs_dir = Path("docs")
        docs_dir.mkdir(exist_ok=True)
        intl_file = docs_dir / "international.html"
        with open(intl_file, 'w') as f:
            f.write(html)
        print(f"✓ International dashboard written to {intl_file}")

    # ── Reports & CSV ─────────────────────────────────────────────────────

    def generate_report(self, new_jobs, snapshot, weekly_trend, historical_data):
        """Generate markdown report."""
        report = f"""# PhilJobs Weekly Report
**Date:** {snapshot['date']}

## Summary
- **New jobs this week:** {snapshot['new_jobs']}
- **Total unique jobs tracked:** {len(historical_data['jobs'])}
- **Total weekly snapshots:** {len(historical_data['weekly_snapshots'])}

## 📊 View Interactive Dashboard
[**Click here to view the comprehensive analytics dashboard**](../docs/index.html)

## Top Main AOS This Week (New Jobs)
"""
        main_aos_counts = weekly_trend.get('main_aos_counts', {})
        if main_aos_counts:
            report += "| Rank | AOS Category | New Jobs |\n"
            report += "|------|--------------|----------|\n"
            for i, (area, count) in enumerate(sorted(main_aos_counts.items(), key=lambda x: x[1], reverse=True), 1):
                report += f"| {i} | {area} | {count} |\n"

        report += f"\n## New Jobs This Week ({len(new_jobs)} total)\n"
        if new_jobs:
            for job in new_jobs[:15]:
                report += f"\n### {job.get('institution', 'Unknown')}\n"
                report += f"**Position:** {job.get('title', 'Unknown')}\n"
                if job.get('job_type'):
                    report += f"**Type:** {job['job_type']}\n"
                if job.get('aos') and job['aos'] != 'Open':
                    report += f"**AOS:** {job['aos']}\n"
                if job.get('location'):
                    report += f"**Location:** {job['location']}\n"
                if job.get('deadline'):
                    report += f"**Deadline:** {job['deadline']}\n"
                report += f"**URL:** {job['url']}\n"
            if len(new_jobs) > 15:
                report += f"\n*... and {len(new_jobs) - 15} more new jobs*\n"
        else:
            report += "\nNo new jobs this week.\n"

        report_file = self.data_dir / f"report_{snapshot['date']}.md"
        with open(report_file, 'w') as f:
            f.write(report)
        print("\n" + "=" * 70)
        print(report)
        print("=" * 70)

    def export_csv(self, historical_data):
        """Export all jobs and weekly trends to CSV."""
        jobs_fields = [
            'id', 'institution', 'title', 'job_category', 'job_type', 'institution_type',
            'aos', 'aoc', 'location', 'state', 'country', 'city',
            'workload', 'vacancies', 'deadline', 'start_date', 'posted_date',
            'status', 'url', 'scraped_date'
        ]
        jobs_file = self.data_dir / "jobs_all.csv"
        with open(jobs_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=jobs_fields, extrasaction='ignore')
            writer.writeheader()
            for job in historical_data.get('jobs', []):
                writer.writerow({k: job.get(k, '') for k in jobs_fields})

        trends = historical_data.get('weekly_trends', [])
        if trends:
            main_aos_keys = sorted({k for t in trends for k in t.get('main_aos_counts', {})})
            ptype_keys = POSITION_TYPES  # fixed ordered list
            jcat_keys = sorted({k for t in trends for k in t.get('job_category_counts', {})})
            itype_keys = sorted({k for t in trends for k in t.get('institution_type_counts', {})})
            state_keys = sorted({k for t in trends for k in t.get('state_counts', {})})

            trend_fields = (
                ['date', 'new_jobs_count']
                + [f'aos_{k}' for k in main_aos_keys]
                + [f'postype_{k.replace("/", "-").replace(" ", "_")}' for k in ptype_keys]
                + [f'jobcat_{k}' for k in jcat_keys]
                + [f'insttype_{k}' for k in itype_keys]
                + [f'state_{k}' for k in state_keys]
            )
            trends_file = self.data_dir / "trends_weekly.csv"
            with open(trends_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=trend_fields, extrasaction='ignore')
                writer.writeheader()
                for t in trends:
                    row = {'date': t['date'], 'new_jobs_count': t['new_jobs_count']}
                    for k in main_aos_keys:
                        row[f'aos_{k}'] = t.get('main_aos_counts', {}).get(k, 0)
                    for k in ptype_keys:
                        col = f'postype_{k.replace("/", "-").replace(" ", "_")}'
                        row[col] = t.get('position_type_counts', {}).get(k, 0)
                    for k in jcat_keys:
                        row[f'jobcat_{k}'] = t.get('job_category_counts', {}).get(k, 0)
                    for k in itype_keys:
                        row[f'insttype_{k}'] = t.get('institution_type_counts', {}).get(k, 0)
                    for k in state_keys:
                        row[f'state_{k}'] = t.get('state_counts', {}).get(k, 0)
                    writer.writerow(row)

        print(f"✓ CSV exports: {jobs_file}, {self.data_dir}/trends_weekly.csv")


def main():
    scraper = PhilJobsScraper()

    print("Starting PhilJobs comprehensive market analytics...")
    print("=" * 70)

    # 1. Scrape new jobs
    jobs = scraper.scrape_jobs()

    # 2. Load historical data
    print("\nLoading historical data...")
    historical_data = scraper.load_historical_data()

    # 2a. Migrate existing hashes to PhilJobs-ID-based format (one-time, safe to re-run)
    print("Checking deduplication hash format...")
    scraper.migrate_hashes_to_job_id(historical_data)

    # 2b. Detect taxonomy revisions and flag all jobs for re-classification
    print("Checking taxonomy version...")
    scraper.migrate_to_current_taxonomy(historical_data)

    # 3. Identify new jobs + save initial record
    print("Analyzing new jobs and saving...")
    new_jobs, snapshot, weekly_trend = scraper.save_data(jobs, historical_data)
    print(f"Identified {len(new_jobs)} NEW jobs this week")

    # 4. Classify new jobs with Claude API
    if new_jobs:
        print(f"\nClassifying {len(new_jobs)} new jobs with Claude API...")
        for job in new_jobs:
            if not job.get('classification'):
                classification = scraper.classify_job_with_claude(job)
                job['classification'] = classification
                job['job_type'] = classification.get('position_type', 'Other')
                job['institution_type'] = classification.get('institution_type', 'Other')
                if not job.get('state'):
                    state_us = classification.get('state_us', '')
                    if state_us and state_us != 'INTERNATIONAL':
                        job['state'] = state_us

    # 5. Migrate/reclassify any existing jobs without classification, with old labels, or that previously failed
    unclassified = [j for j in historical_data['jobs']
                    if not j.get('classification')
                    or j['classification'].get('reasoning') == 'classification_failed']
    needs_migration = [j for j in historical_data['jobs']
                       if j.get('classification') and not j['classification'].get('position_type')
                       and j['classification'].get('reasoning') != 'classification_failed']
    if unclassified or needs_migration:
        print(f"\nMigrating/reclassifying jobs (unclassified: {len(unclassified)}, needs label migration: {len(needs_migration)})...")
        scraper.reclassify_all_jobs(historical_data)
        # Rebuild weekly trends now that all jobs are classified with new labels
        print("Rebuilding weekly trends from classified data...")
        scraper.rebuild_weekly_trends(historical_data)
    else:
        # Save the newly classified jobs
        if new_jobs:
            all_data_file = scraper.data_dir / "all_jobs.json"
            with open(all_data_file, 'w') as f:
                json.dump(historical_data, f, indent=2)

    # 6. Resolve missing states via Claude
    state_resolved = scraper.resolve_missing_states(historical_data)
    if state_resolved:
        print("Rebuilding weekly trends after state resolution...")
        scraper.rebuild_weekly_trends(historical_data)

    # 8. Generate dashboards
    print("\nGenerating US dashboard...")
    scraper.generate_trend_dashboard(historical_data)
    print("Generating international dashboard...")
    scraper.generate_intl_dashboard(historical_data)

    # 8b. Write audit docs for the Keyword Explorer (synonym list + methodology)
    print("\nWriting keyword explorer audit documents...")
    scraper.write_keyword_docs(historical_data)

    # 9. Generate report + CSV
    print("\nGenerating report...")
    scraper.generate_report(new_jobs, snapshot, weekly_trend, historical_data)

    print("\nExporting CSV archives...")
    scraper.export_csv(historical_data)

    print(f"\n✓ Done! Data saved to {scraper.data_dir}/")
    print(f"  - all_jobs.json: {len(historical_data['jobs'])} unique jobs")
    print(f"  - co_occurrence.json: Co-occurrence matrix")
    print(f"  - jobs_all.csv: Full job archive (Excel-compatible)")
    print(f"  - trends_weekly.csv: Weekly trend archive")
    print(f"  - snapshot_{snapshot['date']}.json: This week's data")
    print(f"  - report_{snapshot['date']}.md: Human-readable report")
    print(f"  - docs/index.html: Interactive analytics dashboard (GitHub Pages)")


if __name__ == "__main__":
    main()

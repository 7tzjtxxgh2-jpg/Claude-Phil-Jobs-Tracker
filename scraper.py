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
        "Meta-Ethics", "Normative Ethics", "Biomedical Ethics / Bioethics",
        "Neuroethics", "AI, Technology, and Information Ethics",
        "Environmental Ethics", "Animal Ethics", "Food and Agricultural Ethics",
        "Business Ethics", "Ethics of Population, Future Generations, and Global Justice",
        "Ethics (General / Applied Ethics, Broadly Construed)",
    ],
    "Social & Political Philosophy": [
        "Social and Political Philosophy (General / Political Theory)",
        "Philosophy of Law", "Philosophy of Race", "Philosophy of Gender",
        "Feminist Philosophy", "Philosophy of Sexuality and Queer Theory",
        "PPE (Politics, Philosophy, and Economics)", "Philosophy of Education",
        "Social & Political Philosophy (General)",
    ],
    "Value Theory / Aesthetics": [
        "Aesthetics (General)", "Philosophy of Art", "Philosophy of Music",
        "Philosophy of Film and Media", "Philosophy of Literature",
        "Value Theory / Axiology", "Value Theory / Aesthetics (General)",
    ],
    "History of Philosophy": [
        "Ancient Greek and Roman Philosophy", "Medieval and Renaissance Philosophy",
        "Early Modern Philosophy (17th/18th Century)", "19th/20th Century Philosophy",
        "American Philosophy", "Continental Philosophy", "History of Philosophy (General)",
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
Ethics: Meta-Ethics, Normative Ethics, Biomedical Ethics / Bioethics, Neuroethics, AI, Technology, and Information Ethics, Environmental Ethics, Animal Ethics, Food and Agricultural Ethics, Business Ethics, Ethics of Population, Future Generations, and Global Justice, Ethics (General / Applied Ethics, Broadly Construed)
Social & Political Philosophy: Social and Political Philosophy (General / Political Theory), Philosophy of Law, Philosophy of Race, Philosophy of Gender, Feminist Philosophy, Philosophy of Sexuality and Queer Theory, PPE (Politics, Philosophy, and Economics), Philosophy of Education, Social & Political Philosophy (General)
Value Theory / Aesthetics: Aesthetics (General), Philosophy of Art, Philosophy of Music, Philosophy of Film and Media, Philosophy of Literature, Value Theory / Axiology, Value Theory / Aesthetics (General)
History of Philosophy: Ancient Greek and Roman Philosophy, Medieval and Renaissance Philosophy, Early Modern Philosophy (17th/18th Century), 19th/20th Century Philosophy, American Philosophy, Continental Philosophy, History of Philosophy (General)
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
        """Compute co-occurrence data from a filtered list of jobs (no file I/O)."""
        main_aos_matrix = defaultdict(lambda: defaultdict(int))
        main_aos_solo_vs_joint = defaultdict(lambda: {'solo': 0, 'joint': 0})
        detail_aos_by_context = defaultdict(
            lambda: {'solo': defaultdict(int), 'with_others': defaultdict(int), 'total': 0}
        )
        cc_totals = {area: 0 for area in CROSS_CUTTING_AREAS}
        cc_by_main = {area: defaultdict(int) for area in CROSS_CUTTING_AREAS}
        cc_weekly = {area: defaultdict(int) for area in CROSS_CUTTING_AREAS}

        for job in jobs:
            classification = job.get('classification')
            if not classification:
                continue
            main_list = classification.get('main_aos', [])
            detail_dict = classification.get('detail_aos', {})
            week = job.get('scraped_date', '')[:10]

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
                        cc_totals[detail] += 1
                        cc_weekly[detail][week] += 1
                        for other_main in main_list:
                            cc_by_main[detail][other_main] += 1

        all_weeks = sorted({w for area in CROSS_CUTTING_AREAS for w in cc_weekly[area]})
        cross_cutting_final = {}
        for area in CROSS_CUTTING_AREAS:
            cross_cutting_final[area] = {
                'total': cc_totals[area],
                'by_main': dict(cc_by_main[area]),
                'weekly': {w: cc_weekly[area].get(w, 0) for w in all_weeks},
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

        <!-- Cross-Cutting Areas -->
        <div class="bg-white rounded-xl shadow-lg p-6 mb-8">
            <h2 class="text-2xl font-bold text-gray-800 mb-1">Cross-Cutting Areas</h2>
            <p class="text-sm text-gray-500 mb-4">Weekly trend for areas that span multiple AOS categories: Feminist Philosophy, Philosophy of Race, Philosophy of Gender, Philosophy of Law</p>
            <div class="chart-container">
                <canvas id="crossCuttingChart"></canvas>
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
                        <select id="posTypeAosFilter" onchange="updatePositionTypeChart()" class="text-sm border border-gray-300 rounded-lg px-3 py-2 text-gray-700 bg-white focus:outline-none focus:ring-2 focus:ring-indigo-400">
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
                    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                        <div>
                            <h4 class="text-lg font-semibold text-gray-700 mb-4">Job Types</h4>
                            <canvas id="jobTypeChart"></canvas>
                        </div>
                        <div>
                            <h4 class="text-lg font-semibold text-gray-700 mb-4">Institution Types</h4>
                            <canvas id="institutionChart"></canvas>
                        </div>
                    </div>
                    <div class="mb-6">
                        <h4 class="text-lg font-semibold text-gray-700 mb-4">Geographic Distribution (US States)</h4>
                        <div class="bg-gray-50 rounded-lg p-4">
                            <div id="usStatesList" class="w-full"></div>
                        </div>
                    </div>
                    <div class="bg-blue-50 border-l-4 border-blue-500 rounded-lg p-4">
                        <h4 class="text-lg font-semibold text-blue-900 mb-2">📊 Key Insights</h4>
                        <div id="insights" class="text-sm text-blue-800"></div>
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
            detailAosByContext: {json.dumps(cooc.get('detail_aos_by_context', {}))}
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
        let detailChart = null, jobTypeChart = null, institutionChart = null;

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

            // Subcategories
            const subcatGrid = document.getElementById('subcategoryGrid');
            subcatGrid.innerHTML = '';
            document.getElementById('subcategorySection').style.display = category.subcategories.length > 0 ? 'block' : 'none';
            category.subcategories.forEach(sub => {{
                const subSeries = subDataFor(sub);
                const subTotal = subSeries.reduce((a, b) => a + b, 0);
                const subCurrent = subSeries[subSeries.length - 1] || 0;
                const soloJointData = data.detailAosByContext[sub] || {{}};
                const solo = Object.values(soloJointData.solo || {{}}).reduce((a, b) => a + b, 0);
                const joint = Object.values(soloJointData.with_others || {{}}).reduce((a, b) => a + b, 0);
                subcatGrid.innerHTML += `
                    <div class="bg-gray-50 rounded-lg p-3">
                        <div class="font-medium text-gray-800 text-sm mb-1">${{sub}}</div>
                        <div class="text-xs text-gray-500">${{subTotal}} total · ${{subCurrent}} this week</div>
                        ${{(solo + joint) > 0 ? `<div class="text-xs text-indigo-600 mt-1">Solo: ${{solo}} · Joint: ${{joint}}</div>` : ''}}
                    </div>`;
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

            // Job Types
            const jobTypeCtx = document.getElementById('jobTypeChart').getContext('2d');
            if (jobTypeChart) jobTypeChart.destroy();
            const ptByAos = data.positionTypeByAosWeekly[key] || {{}};
            const ptCurrent = data.positionTypes.map(pt => {{
                // Inherit the Market Overview mode for consistency with modal title
                const slot = ptByAos[pt] || {{}};
                const arr = slot[marketMode] || [];
                return arr[arr.length - 1] || 0;
            }});
            jobTypeChart = new Chart(jobTypeCtx, {{
                type: 'doughnut',
                data: {{
                    labels: data.positionTypes,
                    datasets: [{{ data: ptCurrent, backgroundColor: data.positionTypes.map(pt => data.positionTypeColors[pt] || '#6b7280') }}]
                }},
                options: {{ responsive: true, plugins: {{ legend: {{ position: 'right', labels: {{ font: {{ size: 11 }}, boxWidth: 12 }} }} }} }}
            }});

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

            // US States list for this category — uses the Market Overview mode
            // so the modal stays consistent with whatever filter is active.
            const statesDiv = document.getElementById('usStatesList');
            const stateCatData = {{}};
            const stateCatSlice = data.stateCategoryData[marketMode] || {{}};
            Object.entries(stateCatSlice).forEach(([state, cats]) => {{
                if (cats[key]) stateCatData[state] = cats[key];
            }});
            const sortedStates = Object.entries(stateCatData).sort((a, b) => b[1] - a[1]).slice(0, 10);
            if (sortedStates.length > 0) {{
                statesDiv.innerHTML = sortedStates.map(([s, c]) => `<div class="flex justify-between py-1 text-sm"><span class="text-gray-700">${{s}}</span><span class="font-bold">${{c}}</span></div>`).join('');
            }} else {{
                statesDiv.innerHTML = '<div class="text-gray-400 text-sm">No state data yet</div>';
            }}

            // Insights
            const insightsEl = document.getElementById('insights');
            const insights = [];
            if (total > 0) insights.push(`${{total}} total US jobs in this category since tracking began.`);
            if (change > 0) insights.push(`Up ${{change}} from last week.`);
            else if (change < 0) insights.push(`Down ${{Math.abs(change)}} from last week.`);
            insightsEl.innerHTML = insights.map(i => `<div class="mb-1">• ${{i}}</div>`).join('');

            document.getElementById('detailModal').classList.remove('hidden');
        }}

        function closeModal() {{
            document.getElementById('detailModal').classList.add('hidden');
            currentModalKey = null;
            if (detailChart) {{ detailChart.destroy(); detailChart = null; }}
            if (jobTypeChart) {{ jobTypeChart.destroy(); jobTypeChart = null; }}
            if (institutionChart) {{ institutionChart.destroy(); institutionChart = null; }}
        }}
        document.getElementById('detailModal').addEventListener('click', function(e) {{
            if (e.target === this) closeModal();
        }});

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

        // ===== CROSS-CUTTING CHART =====
        const ccColors = {{ 'Feminist Philosophy': '#ec4899', 'Philosophy of Race': '#f97316', 'Philosophy of Gender': '#8b5cf6', 'Philosophy of Law': '#0ea5e9' }};
        const ccAreas = Object.keys(data.crossCutting);
        // Align x-axis with all other charts: use data.dates, lookup counts from each area's trend list
        new Chart(document.getElementById('crossCuttingChart').getContext('2d'), {{
            type: 'line',
            data: {{
                labels: data.dates,
                datasets: ccAreas.map(area => {{
                    const trendMap = {{}};
                    (data.crossCutting[area]?.trend || []).forEach(t => {{ trendMap[t.week] = t.count; }});
                    return {{
                        label: area, data: data.dates.map(d => trendMap[d] || 0),
                        borderColor: ccColors[area] || '#6b7280', backgroundColor: (ccColors[area] || '#6b7280') + '30',
                        tension: 0.4, fill: true, borderWidth: 2, pointRadius: 4
                    }};
                }})
            }},
            options: {{
                responsive: true, maintainAspectRatio: false,
                interaction: {{ mode: 'index', intersect: false }},
                plugins: {{ legend: {{ position: 'bottom', labels: {{ usePointStyle: true, padding: 15 }} }} }},
                scales: {{ y: {{ beginAtZero: true }}, x: {{ grid: {{ display: false }} }} }}
            }}
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

        # ── Co-occurrence ─────────────────────────────────────────────────
        cooc = self._compute_cooc_from_jobs(intl_jobs)

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
            <h2 class="text-2xl font-bold text-gray-800 mb-1">Cross-Cutting Areas</h2>
            <p class="text-sm text-gray-500 mb-4">Weekly trend for areas that span multiple AOS categories: Feminist Philosophy, Philosophy of Race, Philosophy of Gender, Philosophy of Law</p>
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
                    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                        <div>
                            <h4 class="text-lg font-semibold text-gray-700 mb-4">Job Types</h4>
                            <canvas id="jobTypeChart"></canvas>
                        </div>
                        <div>
                            <h4 class="text-lg font-semibold text-gray-700 mb-4">Institution Types</h4>
                            <canvas id="institutionChart"></canvas>
                        </div>
                    </div>
                    <div class="mb-6">
                        <h4 class="text-lg font-semibold text-gray-700 mb-4">Top Countries</h4>
                        <div class="bg-gray-50 rounded-lg p-4">
                            <div id="topCountriesModal" class="w-full"></div>
                        </div>
                    </div>
                    <div class="bg-blue-50 border-l-4 border-blue-500 rounded-lg p-4">
                        <h4 class="text-lg font-semibold text-blue-900 mb-2">📊 Key Insights</h4>
                        <div id="insights" class="text-sm text-blue-800"></div>
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
            detailAosByContext: {json.dumps(cooc.get('detail_aos_by_context', {}))}
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
        let detailChart = null, jobTypeChart = null, institutionChart = null;

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

            // Subcategories
            const subcatGrid = document.getElementById('subcategoryGrid');
            subcatGrid.innerHTML = '';
            document.getElementById('subcategorySection').style.display = category.subcategories.length > 0 ? 'block' : 'none';
            category.subcategories.forEach(sub => {{
                const subSeries = subDataFor(sub);
                const subTotal = subSeries.reduce((a, b) => a + b, 0);
                const subCurrent = subSeries[subSeries.length - 1] || 0;
                const soloJointData = data.detailAosByContext[sub] || {{}};
                const solo = Object.values(soloJointData.solo || {{}}).reduce((a, b) => a + b, 0);
                const joint = Object.values(soloJointData.with_others || {{}}).reduce((a, b) => a + b, 0);
                subcatGrid.innerHTML += `
                    <div class="bg-gray-50 rounded-lg p-3">
                        <div class="font-medium text-gray-800 text-sm mb-1">${{sub}}</div>
                        <div class="text-xs text-gray-500">${{subTotal}} total · ${{subCurrent}} this week</div>
                        ${{(solo + joint) > 0 ? `<div class="text-xs text-indigo-600 mt-1">Solo: ${{solo}} · Joint: ${{joint}}</div>` : ''}}
                    </div>`;
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

            // Job Types
            const jobTypeCtx = document.getElementById('jobTypeChart').getContext('2d');
            if (jobTypeChart) jobTypeChart.destroy();
            const ptByAos = data.positionTypeByAosWeekly[key] || {{}};
            const ptCurrent = data.positionTypes.map(pt => {{
                // Inherit the Market Overview mode for consistency with modal title
                const slot = ptByAos[pt] || {{}};
                const arr = slot[marketMode] || [];
                return arr[arr.length - 1] || 0;
            }});
            jobTypeChart = new Chart(jobTypeCtx, {{
                type: 'doughnut',
                data: {{ labels: data.positionTypes, datasets: [{{ data: ptCurrent, backgroundColor: data.positionTypes.map(pt => data.positionTypeColors[pt] || '#6b7280') }}] }},
                options: {{ responsive: true, plugins: {{ legend: {{ position: 'right', labels: {{ font: {{ size: 11 }}, boxWidth: 12 }} }} }} }}
            }});

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

            // Top countries for this category
            const countryDiv = document.getElementById('topCountriesModal');
            const catCountries = {{}};
            Object.entries(data.countryCategoryData).forEach(([country, cats]) => {{
                if (cats[key]) catCountries[country] = cats[key];
            }});
            const sortedCountries = Object.entries(catCountries).sort((a, b) => b[1] - a[1]).slice(0, 10);
            if (sortedCountries.length > 0) {{
                countryDiv.innerHTML = sortedCountries.map(([c, n]) => `<div class="flex justify-between py-1 text-sm"><span class="text-gray-700">${{c}}</span><span class="font-bold">${{n}}</span></div>`).join('');
            }} else {{
                countryDiv.innerHTML = '<div class="text-gray-400 text-sm">No country data yet</div>';
            }}

            // Insights
            const insightsEl = document.getElementById('insights');
            const insights = [];
            if (total > 0) insights.push(`${{total}} total international jobs in this category since tracking began.`);
            if (change > 0) insights.push(`Up ${{change}} from last week.`);
            else if (change < 0) insights.push(`Down ${{Math.abs(change)}} from last week.`);
            insightsEl.innerHTML = insights.map(i => `<div class="mb-1">• ${{i}}</div>`).join('');

            document.getElementById('detailModal').classList.remove('hidden');
        }}

        function closeModal() {{
            document.getElementById('detailModal').classList.add('hidden');
            currentModalKey = null;
            if (detailChart) {{ detailChart.destroy(); detailChart = null; }}
            if (jobTypeChart) {{ jobTypeChart.destroy(); jobTypeChart = null; }}
            if (institutionChart) {{ institutionChart.destroy(); institutionChart = null; }}
        }}
        document.getElementById('detailModal').addEventListener('click', function(e) {{
            if (e.target === this) closeModal();
        }});

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

        // ===== CROSS-CUTTING CHART =====
        const ccColors = {{ 'Feminist Philosophy': '#ec4899', 'Philosophy of Race': '#f97316', 'Philosophy of Gender': '#8b5cf6', 'Philosophy of Law': '#0ea5e9' }};
        const ccAreas = Object.keys(data.crossCutting);
        // Align x-axis with all other charts: use data.dates, lookup counts from each area's trend list
        new Chart(document.getElementById('crossCuttingChart').getContext('2d'), {{
            type: 'line',
            data: {{
                labels: data.dates,
                datasets: ccAreas.map(area => {{
                    const trendMap = {{}};
                    (data.crossCutting[area]?.trend || []).forEach(t => {{ trendMap[t.week] = t.count; }});
                    return {{
                        label: area, data: data.dates.map(d => trendMap[d] || 0),
                        borderColor: ccColors[area] || '#6b7280', backgroundColor: (ccColors[area] || '#6b7280') + '30',
                        tension: 0.4, fill: true, borderWidth: 2, pointRadius: 4
                    }};
                }})
            }},
            options: {{
                responsive: true, maintainAspectRatio: false,
                interaction: {{ mode: 'index', intersect: false }},
                plugins: {{ legend: {{ position: 'bottom', labels: {{ usePointStyle: true, padding: 15 }} }} }},
                scales: {{ y: {{ beginAtZero: true }}, x: {{ grid: {{ display: false }} }} }}
            }}
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

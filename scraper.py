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
    'West Virginia': 'WV', 'Wisconsin': 'WI', 'Wyoming': 'WY'
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

US_REGIONS = {
    'West': ['CA', 'OR', 'WA', 'AK', 'HI', 'NV', 'ID', 'MT', 'WY', 'UT', 'CO', 'AZ', 'NM'],
    'Northeast': ['ME', 'NH', 'VT', 'MA', 'RI', 'CT', 'NY', 'NJ', 'PA'],
    'South': ['DE', 'MD', 'VA', 'WV', 'NC', 'SC', 'GA', 'FL', 'KY', 'TN', 'AL', 'MS', 'AR', 'LA', 'OK', 'TX'],
    'Midwest': ['OH', 'IN', 'IL', 'MI', 'WI', 'MN', 'IA', 'MO', 'ND', 'SD', 'NE', 'KS'],
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

        for state_name, state_code in US_STATES.items():
            if re.search(r'\b' + re.escape(state_name) + r'\b', location_string):
                city = location_string.split(',')[0].strip() if ',' in location_string else None
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

        parts = [p.strip() for p in location_string.split(',')]
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

            unique_str = f"{job.get('institution', '')}_{job.get('title', '')}"
            job['hash'] = hashlib.md5(unique_str.encode()).hexdigest()
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

        unclassified = [j for j in jobs if not j.get('classification')]
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
                if state in ['CA', 'OR', 'WA'] and city:
                    for wc_city in WEST_COAST_CITIES:
                        if wc_city.lower() in city.lower():
                            west_coast_city_counts[wc_city] += 1
                            break

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

    # ── Dashboard ─────────────────────────────────────────────────────────

    def is_hiring_season(self, date_str):
        date = datetime.strptime(date_str, "%Y-%m-%d")
        return date.month >= 9 or date.month <= 1

    def generate_trend_dashboard(self, historical_data):
        """Generate comprehensive HTML dashboard."""
        trends = historical_data.get('weekly_trends', [])
        if not trends:
            print("No data available yet for dashboard visualization")
            return

        dates = [t['date'] for t in trends]

        # ── Main AOS series (replaces old parent_categories) ────────────
        parent_categories = {}
        for cat in MAIN_AOS_CATEGORIES:
            parent_categories[cat] = {
                'data': [],
                'subcategories': DETAIL_AOS.get(cat, []),
                'color': MAIN_AOS_COLORS.get(cat, '#6b7280'),
            }
        for trend in trends:
            main_counts = trend.get('main_aos_counts', {})
            for cat in MAIN_AOS_CATEGORIES:
                parent_categories[cat]['data'].append(main_counts.get(cat, 0))

        # ── Detail AOS series (keyed by detail name) ────────────────────
        subcategory_data = {}
        for cat in MAIN_AOS_CATEGORIES:
            for detail in DETAIL_AOS.get(cat, []):
                subcategory_data[detail] = []
        for trend in trends:
            detail_counts = trend.get('detail_aos_counts', {})
            for cat in MAIN_AOS_CATEGORIES:
                for detail in DETAIL_AOS.get(cat, []):
                    key = f"{cat}::{detail}"
                    subcategory_data[detail].append(detail_counts.get(key, 0))

        # ── Position type series (all AOS combined) ──────────────────────
        job_type_series = {pt: [] for pt in POSITION_TYPES}
        for trend in trends:
            pt_counts = trend.get('position_type_counts', {})
            for pt in POSITION_TYPES:
                job_type_series[pt].append(pt_counts.get(pt, 0))

        # ── Position type broken down by AOS (for trend chart with filter) ─
        position_type_by_aos_weekly = {}
        for aos in MAIN_AOS_CATEGORIES:
            position_type_by_aos_weekly[aos] = {pt: [] for pt in POSITION_TYPES}
            for trend in trends:
                by_aos = trend.get('position_type_by_aos', {})
                aos_pt = by_aos.get(aos, {})
                for pt in POSITION_TYPES:
                    position_type_by_aos_weekly[aos][pt].append(aos_pt.get(pt, 0))

        inst_types = ['Research University', 'Teaching College', 'Other']
        inst_type_series = {it: [] for it in inst_types}
        for trend in trends:
            for it in inst_types:
                inst_type_series[it].append(trend.get('institution_type_counts', {}).get(it, 0))

        # ── Geographic data ──────────────────────────────────────────────
        state_data = {state: [] for state in US_STATES.values()}
        for trend in trends:
            sc = trend.get('state_counts', {})
            for state_code in US_STATES.values():
                state_data[state_code].append(sc.get(state_code, 0))

        west_coast_data = {}
        for trend in trends:
            for city, count in trend.get('west_coast_city_counts', {}).items():
                west_coast_data.setdefault(city, []).append(count)

        latin_america_countries = [
            'Mexico', 'Brazil', 'Argentina', 'Chile', 'Colombia', 'Peru', 'Venezuela',
            'Ecuador', 'Guatemala', 'Cuba', 'Bolivia', 'Haiti', 'Dominican Republic',
            'Honduras', 'Paraguay', 'El Salvador', 'Nicaragua', 'Costa Rica', 'Panama',
            'Puerto Rico', 'Uruguay'
        ]
        latin_data = {}
        for trend in trends:
            for country in latin_america_countries:
                latin_data.setdefault(country, []).append(trend.get('country_counts', {}).get(country, 0))

        region_data = {}
        for region, states in US_REGIONS.items():
            series = []
            for i in range(len(dates)):
                total = sum(
                    state_data.get(s, [])[i] if i < len(state_data.get(s, [])) else 0
                    for s in states
                )
                series.append(total)
            region_data[region] = series

        state_alltime = {s: sum(v) for s, v in state_data.items() if sum(v) > 0}

        # ── Job category time series ─────────────────────────────────────
        all_job_categories = sorted({
            cat for t in trends for cat in t.get('job_category_counts', {}).keys()
        })
        job_category_series = {jc: [] for jc in all_job_categories}
        for trend in trends:
            for jc in all_job_categories:
                job_category_series[jc].append(trend.get('job_category_counts', {}).get(jc, 0))

        # ── Position type × AOS all-time totals (replaces Market Matrix) ──
        pos_type_x_aos_map = defaultdict(lambda: defaultdict(int))
        for job in historical_data.get('jobs', []):
            classification = job.get('classification')
            if classification:
                raw_pt = (classification.get('position_type')
                          or JOB_TYPE_MIGRATION.get(classification.get('job_type', ''), None)
                          or job.get('job_type', 'Other'))
                pos_type = raw_pt if raw_pt in POSITION_TYPES else 'Other'
                for main in classification.get('main_aos', []):
                    pos_type_x_aos_map[main][pos_type] += 1
        pos_type_x_aos = {k: dict(v) for k, v in pos_type_x_aos_map.items()}

        # ── State → main AOS breakdown ───────────────────────────────────
        state_cat_map = defaultdict(lambda: defaultdict(int))
        for job in historical_data.get('jobs', []):
            s = job.get('state')
            if s:
                classification = job.get('classification')
                if classification:
                    for main in classification.get('main_aos', []):
                        state_cat_map[s][main] += 1
        state_category_data = {k: dict(v) for k, v in state_cat_map.items()}

        # ── Co-occurrence data ───────────────────────────────────────────
        cooc_file = self.data_dir / 'co_occurrence.json'
        if cooc_file.exists():
            with open(cooc_file) as f:
                cooc = json.load(f)
        else:
            cooc = self.compute_cooccurrence(historical_data)

        # ── Summary stats ────────────────────────────────────────────────
        current_week_new_jobs = trends[-1]['new_jobs_count']
        total_unique_jobs = len(historical_data['jobs'])
        weeks_tracked = len(trends)

        # Most active main AOS this week
        last_main = trends[-1].get('main_aos_counts', {})
        most_active = max(last_main, key=last_main.get) if last_main else "—"

        seasonal_markers = []
        for i, date in enumerate(dates):
            if self.is_hiring_season(date):
                seasonal_markers.append({'index': i, 'label': 'Hiring Season'})

        # ── Build HTML ───────────────────────────────────────────────────
        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Philosophy Job Market Analytics</title>
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
    <div class="bg-gradient-to-r from-indigo-600 to-purple-600 text-white">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
            <h1 class="text-4xl font-bold mb-2">Philosophy Job Market Analytics</h1>
            <p class="text-indigo-100">Real-time trends and insights from PhilJobs</p>
            <div class="mt-6 text-sm text-indigo-100">Last updated: {datetime.now().strftime("%B %d, %Y")}</div>
        </div>
    </div>

    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">

        <!-- Stats Cards -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-6 mb-8">
            <div class="stat-card rounded-xl shadow-lg p-6 text-white col-span-2 md:col-span-1">
                <div class="text-3xl font-bold">{current_week_new_jobs}</div>
                <div class="text-indigo-100">New Jobs This Week</div>
            </div>
            <div class="bg-white rounded-xl shadow-lg p-6">
                <div class="text-3xl font-bold text-gray-800">{total_unique_jobs}</div>
                <div class="text-gray-600">Total Unique Jobs</div>
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
            <h2 class="text-2xl font-bold text-gray-800 mb-2">Market Overview</h2>
            <p class="text-sm text-gray-500 mb-4">New jobs per week by main AOS category — shaded areas = hiring season (Sept–Jan)</p>
            <div class="chart-container">
                <canvas id="mainChart"></canvas>
            </div>
        </div>

        <!-- Regional Trends -->
        <div class="bg-white rounded-xl shadow-lg p-6 mb-8">
            <h2 class="text-2xl font-bold text-gray-800 mb-1">Regional Trends</h2>
            <p class="text-sm text-gray-500 mb-4">New jobs per week by US region — West highlighted in blue</p>
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
                    <p class="text-sm text-gray-500 mt-1">Click any state for a detailed breakdown</p>
                </div>
                <div class="flex gap-2">
                    <button id="mapModeNew" onclick="setMapMode('current')" class="px-4 py-2 text-sm font-medium rounded-lg bg-indigo-600 text-white">New This Week</button>
                    <button id="mapModeAll" onclick="setMapMode('alltime')" class="px-4 py-2 text-sm font-medium rounded-lg bg-gray-200 text-gray-700">All-Time</button>
                </div>
            </div>
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div>
                    <div class="flex items-center gap-2 mb-2">
                        <h3 class="text-lg font-semibold text-gray-700">United States</h3>
                        <span class="text-xs text-blue-600 font-medium bg-blue-50 px-2 py-0.5 rounded-full">West Coast highlighted</span>
                    </div>
                    <div id="usMapEl" class="bg-gray-50 rounded-lg overflow-hidden" style="height:300px;">
                        <div class="flex items-center justify-center h-full text-gray-400 text-sm">Loading map...</div>
                    </div>
                </div>
                <div>
                    <h3 class="text-lg font-semibold text-gray-700 mb-2">Latin America</h3>
                    <div id="latinMapEl" class="bg-gray-50 rounded-lg overflow-hidden" style="height:300px;">
                        <div class="flex items-center justify-center h-full text-gray-400 text-sm">Loading map...</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Position Type Trends -->
        <div class="bg-white rounded-xl shadow-lg p-6 mb-8">
            <div class="flex flex-wrap justify-between items-center mb-2 gap-4">
                <div>
                    <h2 class="text-2xl font-bold text-gray-800">Position Type Trends</h2>
                    <p class="text-sm text-gray-500 mt-1">New jobs per week by position type — filter by AOS to see hiring patterns within each area</p>
                </div>
                <div>
                    <select id="posTypeAosFilter" onchange="updatePositionTypeChart()" class="text-sm border border-gray-300 rounded-lg px-3 py-2 text-gray-700 bg-white focus:outline-none focus:ring-2 focus:ring-indigo-400">
                        <option value="__all__">All AOS</option>
                    </select>
                </div>
            </div>
            <div class="chart-container mb-6">
                <canvas id="posTypeChart"></canvas>
            </div>
            <div id="posTypeTable" class="overflow-x-auto text-sm mt-4"></div>
        </div>

        <!-- West Coast Spotlight -->
        <div class="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl shadow-lg p-6 mb-8 border border-blue-100">
            <h2 class="text-2xl font-bold text-gray-800 mb-1">🌊 West Coast Spotlight</h2>
            <p class="text-sm text-gray-500 mb-4">City-level weekly new-job trends — CA, OR, WA</p>
            <div class="chart-container">
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
                        <h4 class="text-lg font-semibold text-gray-700 mb-4">Geographic Distribution</h4>
                        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                            <div>
                                <h5 class="text-sm font-medium text-gray-600 mb-2">United States</h5>
                                <div id="usMapContainer" class="bg-gray-50 rounded-lg p-4 h-64 flex items-center justify-center">
                                    <div id="usStatesList" class="w-full"></div>
                                </div>
                                <div id="westCoastDetail" class="hidden mt-4 bg-blue-50 rounded-lg p-4">
                                    <h5 class="text-sm font-medium text-blue-900 mb-2">West Coast Detail</h5>
                                    <div id="westCoastCities" class="text-sm"></div>
                                </div>
                            </div>
                            <div>
                                <h5 class="text-sm font-medium text-gray-600 mb-2">Latin America</h5>
                                <div id="latinMapContainer" class="bg-gray-50 rounded-lg p-4 h-64 overflow-y-auto">
                                    <div id="latinCountriesList"></div>
                                </div>
                            </div>
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
            categories: {json.dumps({k: {{'name': k, 'data': v['data'], 'subcategories': v['subcategories'], 'color': v['color']}} for k, v in parent_categories.items()})},
            subcategoryData: {json.dumps(subcategory_data)},
            jobTypeData: {json.dumps(job_type_series)},
            institutionTypeData: {json.dumps(inst_type_series)},
            stateData: {json.dumps(state_data)},
            westCoastData: {json.dumps(west_coast_data)},
            latinData: {json.dumps(latin_data)},
            westCoastCities: {json.dumps(WEST_COAST_CITIES)},
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

        // ===== MAIN CHART =====
        const mainCtx = document.getElementById('mainChart').getContext('2d');
        const datasets = Object.entries(data.categories).map(([key, cat]) => ({{
            label: cat.name,
            data: cat.data,
            borderColor: cat.color,
            backgroundColor: cat.color + '20',
            tension: 0.4,
            fill: true
        }}));
        new Chart(mainCtx, {{
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

        // ===== CATEGORY CARDS =====
        const categoryGrid = document.getElementById('categoryGrid');
        Object.entries(data.categories).forEach(([key, cat]) => {{
            const currentJobs = cat.data[cat.data.length - 1];
            const previousJobs = cat.data[cat.data.length - 2] || 0;
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

        // ===== MODAL =====
        let detailChart = null, jobTypeChart = null, institutionChart = null;

        function openModal(key, category) {{
            const currentJobs = category.data[category.data.length - 1];
            const previousJobs = category.data[category.data.length - 2] || 0;
            const change = currentJobs - previousJobs;
            const average = (category.data.reduce((a, b) => a + b, 0) / category.data.length).toFixed(1);
            const total = category.data.reduce((a, b) => a + b, 0);

            document.getElementById('modalTitle').textContent = category.name;
            document.getElementById('modalCurrentJobs').textContent = currentJobs;
            document.getElementById('modalChange').textContent = (change >= 0 ? '+' : '') + change;
            document.getElementById('modalChange').className = 'text-2xl font-bold ' + (change >= 0 ? 'text-green-600' : 'text-red-600');
            document.getElementById('modalAverage').textContent = average;
            document.getElementById('modalTotal').textContent = total;

            // Subcategories
            const subcategoryGrid = document.getElementById('subcategoryGrid');
            subcategoryGrid.innerHTML = '';
            category.subcategories.forEach(subcat => {{
                const subcatData = data.subcategoryData[subcat] || [];
                const subcatCurrent = subcatData[subcatData.length - 1] || 0;
                const subcatPrevious = subcatData[subcatData.length - 2] || 0;
                const subcatChange = subcatCurrent - subcatPrevious;
                const el = document.createElement('div');
                el.className = 'bg-gray-50 rounded-lg p-3 hover:bg-gray-100 transition-colors';
                el.innerHTML = `
                    <div class="font-medium text-gray-700 text-sm mb-1">${{subcat}}</div>
                    <div class="flex items-center justify-between">
                        <span class="text-xl font-bold text-gray-800">${{subcatCurrent}}</span>
                        <span class="text-xs font-semibold ${{subcatChange >= 0 ? 'text-green-600' : 'text-red-600'}}">${{subcatChange >= 0 ? '↑' : '↓'}} ${{Math.abs(subcatChange)}}</span>
                    </div>
                `;
                subcategoryGrid.appendChild(el);
            }});

            // Detail chart
            const detailCtx = document.getElementById('detailChart').getContext('2d');
            if (detailChart) detailChart.destroy();
            const detailDatasets = [{{
                label: category.name + ' (Total)',
                data: category.data, borderColor: category.color, backgroundColor: category.color + '40',
                tension: 0.4, fill: true, borderWidth: 3
            }}];
            const dColors = ['#6366f1','#ec4899','#14b8a6','#f59e0b','#8b5cf6','#f97316','#06b6d4'];
            category.subcategories.forEach((subcat, idx) => {{
                detailDatasets.push({{
                    label: subcat, data: data.subcategoryData[subcat] || [],
                    borderColor: dColors[idx % dColors.length], backgroundColor: dColors[idx % dColors.length] + '20',
                    tension: 0.4, borderWidth: 2, borderDash: [5, 5]
                }});
            }});
            detailChart = new Chart(detailCtx, {{
                type: 'line',
                data: {{ labels: data.dates, datasets: detailDatasets }},
                options: {{
                    responsive: true, maintainAspectRatio: false,
                    plugins: {{ legend: {{ position: 'bottom', labels: {{ usePointStyle: true, padding: 15, font: {{ size: 11 }} }} }} }},
                    scales: {{ y: {{ beginAtZero: true }}, x: {{}} }}
                }}
            }});

            // Lassiter solo/joint by subcategory
            const lassiterDiv = document.getElementById('lassiterChart');
            lassiterDiv.innerHTML = '';
            const byCtx = data.detailAosByContext;
            if (category.subcategories.length > 0 && Object.keys(byCtx).length > 0) {{
                let html = '<table class="w-full border-collapse"><thead><tr>';
                html += '<th class="text-left py-2 px-3 bg-gray-50 border border-gray-200 text-xs font-semibold text-gray-600">Subcategory</th>';
                html += '<th class="py-2 px-3 bg-gray-50 border border-gray-200 text-xs font-semibold text-gray-600 text-center">Total</th>';
                html += '<th class="py-2 px-3 bg-gray-50 border border-gray-200 text-xs font-semibold text-indigo-600 text-center">Solo</th>';
                html += '<th class="py-2 px-3 bg-gray-50 border border-gray-200 text-xs font-semibold text-amber-600 text-center">Joint</th>';
                html += '<th class="py-2 px-3 bg-gray-50 border border-gray-200 text-xs font-semibold text-gray-600">Top Co-occurring AOS</th>';
                html += '</tr></thead><tbody>';
                category.subcategories.forEach((subcat, i) => {{
                    const ctx = byCtx[subcat] || {{}};
                    const soloCount = Object.values(ctx.solo || {{}}).reduce((a, b) => a + b, 0);
                    const total = ctx.total || 0;
                    const jointCount = total - soloCount;
                    const topCooc = Object.entries(ctx.with_others || {{}}).sort((a, b) => b[1] - a[1]).slice(0, 2).map(([k, v]) => `${{k}} (${{v}})`).join(', ');
                    html += `<tr class="${{i % 2 === 0 ? 'bg-white' : 'bg-gray-50'}}">
                        <td class="py-2 px-3 border border-gray-200 text-sm text-gray-700">${{subcat}}</td>
                        <td class="py-2 px-3 border border-gray-200 text-center font-semibold">${{total || '—'}}</td>
                        <td class="py-2 px-3 border border-gray-200 text-center text-indigo-600 font-semibold">${{soloCount || '—'}}</td>
                        <td class="py-2 px-3 border border-gray-200 text-center text-amber-600 font-semibold">${{jointCount > 0 ? jointCount : '—'}}</td>
                        <td class="py-2 px-3 border border-gray-200 text-xs text-gray-500">${{topCooc || '—'}}</td>
                    </tr>`;
                }});
                html += '</tbody></table>';
                lassiterDiv.innerHTML = html;
                document.getElementById('lassiterSection').classList.remove('hidden');
            }} else {{
                document.getElementById('lassiterSection').classList.add('hidden');
            }}

            // Position type chart (modal)
            const jobTypeCtx = document.getElementById('jobTypeChart').getContext('2d');
            if (jobTypeChart) jobTypeChart.destroy();
            jobTypeChart = new Chart(jobTypeCtx, {{
                type: 'doughnut',
                data: {{
                    labels: data.positionTypes,
                    datasets: [{{ data: data.positionTypes.map(pt => (data.jobTypeData[pt] || []).slice(-1)[0] || 0), backgroundColor: data.positionTypes.map(pt => data.positionTypeColors[pt] || '#6b7280') }}]
                }},
                options: {{ responsive: true, plugins: {{ legend: {{ position: 'bottom', labels: {{ font: {{ size: 11 }} }} }} }} }}
            }});

            // Institution type chart
            const instCtx = document.getElementById('institutionChart').getContext('2d');
            if (institutionChart) institutionChart.destroy();
            const instTypeLabels = ['Research University', 'Teaching College', 'Other'];
            institutionChart = new Chart(instCtx, {{
                type: 'doughnut',
                data: {{
                    labels: instTypeLabels,
                    datasets: [{{ data: instTypeLabels.map(t => (data.institutionTypeData[t] || []).slice(-1)[0] || 0), backgroundColor: ['#3b82f6','#10b981','#6b7280'] }}]
                }},
                options: {{ responsive: true, plugins: {{ legend: {{ position: 'bottom' }} }} }}
            }});

            // US States list
            const statesList = document.getElementById('usStatesList');
            statesList.innerHTML = '';
            const latestStateData = Object.entries(data.stateData)
                .map(([state, counts]) => [state, counts[counts.length - 1] || 0])
                .filter(([s, c]) => c > 0).sort((a, b) => b[1] - a[1]).slice(0, 10);
            if (latestStateData.length > 0) {{
                latestStateData.forEach(([state, count]) => {{
                    const isWC = ['CA', 'OR', 'WA'].includes(state);
                    statesList.innerHTML += `<div class="flex justify-between items-center py-2 px-3 ${{isWC ? 'bg-blue-100 rounded' : ''}}"><span class="font-medium ${{isWC ? 'text-blue-900' : 'text-gray-700'}}">${{state}}</span><span class="font-bold ${{isWC ? 'text-blue-900' : 'text-gray-800'}}">${{count}}</span></div>`;
                }});
                const wcData = Object.entries(data.westCoastData).map(([city, counts]) => [city, counts[counts.length - 1] || 0]).filter(([c, cnt]) => cnt > 0).sort((a, b) => b[1] - a[1]);
                if (wcData.length > 0) {{
                    document.getElementById('westCoastDetail').classList.remove('hidden');
                    document.getElementById('westCoastCities').innerHTML = wcData.map(([city, count]) => `<div class="flex justify-between py-1"><span>${{city}}</span><span class="font-bold">${{count}}</span></div>`).join('');
                }} else {{ document.getElementById('westCoastDetail').classList.add('hidden'); }}
            }} else {{ statesList.innerHTML = '<div class="text-gray-500 text-center py-8">No US jobs in this category</div>'; }}

            // Latin America list
            const latinList = document.getElementById('latinCountriesList');
            const latinCounts = Object.entries(data.latinData).map(([country, counts]) => [country, counts[counts.length - 1] || 0]).filter(([c, cnt]) => cnt > 0).sort((a, b) => b[1] - a[1]);
            if (latinCounts.length > 0) {{
                latinList.innerHTML = latinCounts.map(([country, count]) => `<div class="flex justify-between items-center py-2 px-3"><span class="font-medium text-gray-700">${{country}}</span><span class="font-bold text-gray-800">${{count}}</span></div>`).join('');
            }} else {{ latinList.innerHTML = '<div class="text-gray-500 text-center py-8">No Latin American jobs in this category</div>'; }}

            // Insights
            const insights = document.getElementById('insights');
            const trendDir = category.data[category.data.length - 1] > category.data[0] ? 'upward' : category.data[category.data.length - 1] < category.data[0] ? 'downward' : 'stable';
            let insightText = '<ul class="space-y-1">';
            if (change > 0) {{ insightText += `<li>• Growing: up ${{change}} new jobs from last week (+${{previousJobs > 0 ? ((change/previousJobs)*100).toFixed(1) : '∞'}}%)</li>`; }}
            else if (change < 0) {{ insightText += `<li>• Declining: down ${{Math.abs(change)}} new jobs from last week</li>`; }}
            else {{ insightText += `<li>• Stable: same number of new jobs as last week</li>`; }}
            insightText += `<li>• Overall trend since tracking began: ${{trendDir}}</li>`;
            insightText += `<li>• Average ${{average}} new jobs per week</li>`;
            if (category.subcategories.length > 0) {{
                let hottestSub = category.subcategories[0]; let hottestCount = 0;
                category.subcategories.forEach(sub => {{
                    const subTotal = (data.subcategoryData[sub] || []).reduce((a, b) => a + b, 0);
                    if (subTotal > hottestCount) {{ hottestCount = subTotal; hottestSub = sub; }}
                }});
                insightText += `<li>• Most active subcategory: ${{hottestSub}} (${{hottestCount}} total jobs)</li>`;
            }}
            insightText += '</ul>';
            insights.innerHTML = insightText;

            document.getElementById('detailModal').classList.remove('hidden');
        }}

        function closeModal() {{ document.getElementById('detailModal').classList.add('hidden'); }}
        document.addEventListener('keydown', (e) => {{ if (e.key === 'Escape') {{ closeModal(); closeStatePanel(); }} }});

        // ===== REGIONAL TRENDS CHART =====
        const regionColors = {{'West':'#3b82f6','Northeast':'#10b981','South':'#ef4444','Midwest':'#f59e0b'}};
        new Chart(document.getElementById('regionalChart').getContext('2d'), {{
            type: 'line',
            data: {{
                labels: data.dates,
                datasets: Object.entries(data.regionData).map(([region, values]) => ({{
                    label: region, data: values,
                    borderColor: regionColors[region] || '#6b7280',
                    backgroundColor: (regionColors[region] || '#6b7280') + '20',
                    tension: 0.4, fill: false,
                    borderWidth: region === 'West' ? 3 : 2, borderDash: region === 'West' ? [] : [5, 5]
                }}))
            }},
            options: {{
                responsive: true, maintainAspectRatio: false,
                interaction: {{ mode: 'index', intersect: false }},
                plugins: {{ legend: {{ position: 'bottom', labels: {{ usePointStyle: true, padding: 15 }} }} }},
                scales: {{ y: {{ beginAtZero: true, grid: {{ color: 'rgba(0,0,0,0.05)' }} }}, x: {{ grid: {{ display: false }} }} }}
            }}
        }});

        // ===== CO-OCCURRENCE MATRIX =====
        (function() {{
            const matrix = data.coocMatrix;
            const cats = Object.keys(data.mainAosColors).filter(c => c !== 'Open');
            const matrixDiv = document.getElementById('coocMatrixTable');
            if (!matrix || Object.keys(matrix).length === 0) {{
                matrixDiv.innerHTML = '<div class="text-gray-400 text-center py-8 text-sm">Co-occurrence data will populate after jobs are classified.</div>';
                return;
            }}
            let maxVal = 0;
            cats.forEach(r => cats.forEach(c => {{ if (r !== c) maxVal = Math.max(maxVal, (matrix[r] || {{}})[c] || 0); }}));
            let html = '<table class="w-full border-collapse text-xs"><thead><tr><th class="py-2 px-3 bg-gray-50 border border-gray-200 text-left text-gray-500">AOS</th>';
            cats.forEach(c => {{
                const short = c.replace('Non-Western & Cross-Cultural Philosophy', 'Non-Western').replace('Science, Logic, & Mathematics', 'Sci/Logic/Math').replace('Social & Political Philosophy', 'Social/Pol').replace('Value Theory / Aesthetics', 'Value/Aes').replace('Metaphysics & Epistemology', 'M&E').replace('History of Philosophy', 'History');
                html += `<th class="py-2 px-2 bg-gray-50 font-semibold text-gray-600 border border-gray-200 text-center" style="min-width:70px" title="${{c}}">${{short}}</th>`;
            }});
            html += '</tr></thead><tbody>';
            cats.forEach((row, i) => {{
                const shortRow = row.replace('Non-Western & Cross-Cultural Philosophy', 'Non-Western').replace('Science, Logic, & Mathematics', 'Sci/Logic/Math').replace('Social & Political Philosophy', 'Social/Political').replace('Value Theory / Aesthetics', 'Value/Aesthetics').replace('Metaphysics & Epistemology', 'M&E').replace('History of Philosophy', 'History');
                html += `<tr class="${{i % 2 === 0 ? 'bg-white' : 'bg-gray-50'}}"><td class="py-2 px-3 font-semibold text-gray-700 border border-gray-200 whitespace-nowrap text-xs">${{shortRow}}</td>`;
                cats.forEach(col => {{
                    if (row === col) {{
                        html += `<td class="py-2 px-2 text-center border border-gray-200 bg-gray-100 text-gray-400 text-xs">—</td>`;
                    }} else {{
                        const v = (matrix[row] || {{}})[col] || 0;
                        const intensity = maxVal > 0 ? v / maxVal : 0;
                        const alpha = Math.round(intensity * 180);
                        html += `<td class="py-2 px-2 text-center border border-gray-200 text-xs ${{v > 0 ? 'font-semibold text-gray-800' : 'text-gray-300'}}" style="background-color:rgba(99,102,241,${{alpha/255}})">${{v || '—'}}</td>`;
                    }}
                }});
                html += '</tr>';
            }});
            html += '</tbody></table>';
            matrixDiv.innerHTML = html;
        }})();

        // ===== SOLO VS. JOINT =====
        (function() {{
            const svj = data.soloVsJoint;
            const cats = Object.keys(data.mainAosColors).filter(c => c !== 'Open');
            const solos = cats.map(c => (svj[c] || {{}}).solo || 0);
            const joints = cats.map(c => (svj[c] || {{}}).joint || 0);
            if (!solos.some(v => v > 0) && !joints.some(v => v > 0)) {{
                document.getElementById('soloJointChart').parentElement.innerHTML = '<div class="text-gray-400 text-center py-8 text-sm">Solo/joint data will populate after jobs are classified.</div>';
                return;
            }}
            new Chart(document.getElementById('soloJointChart').getContext('2d'), {{
                type: 'bar',
                data: {{
                    labels: cats,
                    datasets: [
                        {{ label: 'Solo (only AOS)', data: solos, backgroundColor: '#6366f1cc', borderColor: '#6366f1', borderWidth: 1 }},
                        {{ label: 'Joint (with other AOS)', data: joints, backgroundColor: '#f59e0bcc', borderColor: '#f59e0b', borderWidth: 1 }}
                    ]
                }},
                options: {{
                    indexAxis: 'y', responsive: true, maintainAspectRatio: false,
                    interaction: {{ mode: 'index', intersect: false }},
                    plugins: {{ legend: {{ position: 'bottom', labels: {{ usePointStyle: true, padding: 15 }} }} }},
                    scales: {{
                        x: {{ stacked: true, beginAtZero: true, ticks: {{ precision: 0 }} }},
                        y: {{ stacked: true, grid: {{ display: false }} }}
                    }}
                }}
            }});
        }})();

        // ===== CROSS-CUTTING AREAS =====
        (function() {{
            const cc = data.crossCutting;
            const areas = Object.keys(cc || {{}});
            if (areas.length === 0 || !areas.some(a => (cc[a].total || 0) > 0)) {{
                document.getElementById('crossCuttingChart').parentElement.innerHTML = '<div class="text-gray-400 text-center py-8 text-sm">Cross-cutting data will populate after jobs are classified.</div>';
                return;
            }}
            const ccColors = ['#ec4899','#3b82f6','#10b981','#8b5cf6'];
            const allWeeks = data.dates;
            const ccDatasets = areas.map((area, idx) => {{
                const trendMap = {{}};
                (cc[area].trend || []).forEach(pt => {{ trendMap[pt.week] = pt.count; }});
                return {{
                    label: area, data: allWeeks.map(w => trendMap[w] || 0),
                    borderColor: ccColors[idx % ccColors.length],
                    backgroundColor: ccColors[idx % ccColors.length] + '30',
                    tension: 0.4, fill: true, borderWidth: 2
                }};
            }});
            new Chart(document.getElementById('crossCuttingChart').getContext('2d'), {{
                type: 'line',
                data: {{ labels: allWeeks, datasets: ccDatasets }},
                options: {{
                    responsive: true, maintainAspectRatio: false,
                    interaction: {{ mode: 'index', intersect: false }},
                    plugins: {{ legend: {{ position: 'bottom', labels: {{ usePointStyle: true, padding: 15 }} }} }},
                    scales: {{ y: {{ beginAtZero: true, ticks: {{ precision: 0 }} }}, x: {{ grid: {{ display: false }} }} }}
                }}
            }});
        }})();

        // ===== POSITION TYPE TRENDS =====
        (function() {{
            // Populate AOS filter dropdown
            const filterSel = document.getElementById('posTypeAosFilter');
            data.mainAosCategories.forEach(aos => {{
                const opt = document.createElement('option');
                opt.value = aos;
                opt.textContent = aos;
                filterSel.appendChild(opt);
            }});

            // Check if there's any data at all
            const hasData = data.positionTypes.some(pt =>
                (data.positionTypeByAosWeekly[data.mainAosCategories[0]] || {{}})[pt]?.some(v => v > 0)
                || (data.jobTypeData[pt] || []).some(v => v > 0)
            );
            if (!hasData) {{
                document.getElementById('posTypeChart').parentElement.innerHTML = '<div class="text-gray-400 text-center py-8 text-sm">Position type data will populate after jobs are classified.</div>';
                return;
            }}
        }})();

        let posTypeChart = null;
        function updatePositionTypeChart() {{
            const filter = document.getElementById('posTypeAosFilter').value;
            const ctx = document.getElementById('posTypeChart').getContext('2d');
            if (posTypeChart) posTypeChart.destroy();

            const datasets = data.positionTypes.map(pt => {{
                let series;
                if (filter === '__all__') {{
                    series = data.jobTypeData[pt] || data.dates.map(() => 0);
                }} else {{
                    series = ((data.positionTypeByAosWeekly[filter] || {{}})[pt]) || data.dates.map(() => 0);
                }}
                return {{
                    label: pt,
                    data: series,
                    borderColor: data.positionTypeColors[pt] || '#6b7280',
                    backgroundColor: (data.positionTypeColors[pt] || '#6b7280') + '25',
                    tension: 0.4, fill: true, borderWidth: 2, pointRadius: 3
                }};
            }});

            posTypeChart = new Chart(ctx, {{
                type: 'line',
                data: {{ labels: data.dates, datasets: datasets }},
                plugins: [seasonPlugin],
                options: {{
                    responsive: true, maintainAspectRatio: false,
                    interaction: {{ mode: 'index', intersect: false }},
                    plugins: {{
                        legend: {{ position: 'bottom', labels: {{ usePointStyle: true, padding: 15, font: {{ size: 12 }} }} }},
                        tooltip: {{ backgroundColor: 'rgba(0,0,0,0.8)', padding: 12 }}
                    }},
                    scales: {{
                        y: {{ beginAtZero: true, ticks: {{ precision: 0 }}, grid: {{ color: 'rgba(0,0,0,0.05)' }} }},
                        x: {{ grid: {{ display: false }} }}
                    }}
                }}
            }});

            // Summary table: AOS rows × position type columns
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
                const row = data.positionTypeXAos[aos] || {{}};
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
        updatePositionTypeChart();

        // ===== WEST COAST CHART =====
        const wcColors = ['#1d4ed8','#2563eb','#3b82f6','#60a5fa','#93c5fd','#1e40af','#0369a1','#0284c7','#0ea5e9','#38bdf8','#7dd3fc','#bae6fd','#047857','#065f46','#064e3b'];
        const wcDatasets = Object.entries(data.westCoastData).filter(([city, counts]) => counts.some(c => c > 0)).map(([city, counts], idx) => ({{
            label: city, data: counts, borderColor: wcColors[idx % wcColors.length], backgroundColor: wcColors[idx % wcColors.length] + '30',
            tension: 0.4, fill: false, borderWidth: 2, pointRadius: 4
        }}));
        if (wcDatasets.length > 0) {{
            new Chart(document.getElementById('westCoastChart').getContext('2d'), {{
                type: 'line', data: {{ labels: data.dates, datasets: wcDatasets }},
                options: {{
                    responsive: true, maintainAspectRatio: false,
                    interaction: {{ mode: 'index', intersect: false }},
                    plugins: {{ legend: {{ position: 'bottom', labels: {{ usePointStyle: true, padding: 10, font: {{ size: 11 }} }} }} }},
                    scales: {{ y: {{ beginAtZero: true, ticks: {{ precision: 0 }} }}, x: {{ grid: {{ display: false }} }} }}
                }}
            }});
        }} else {{
            document.getElementById('westCoastChart').parentElement.innerHTML = '<div class="text-gray-400 text-center py-8 text-sm">No West Coast city data yet.</div>';
        }}

        // ===== D3 CHOROPLETH MAPS =====
        let currentMapMode = 'current', usAtlasData = null, worldAtlasData = null;
        const fipsToState = {{"01":"AL","02":"AK","04":"AZ","05":"AR","06":"CA","08":"CO","09":"CT","10":"DE","12":"FL","13":"GA","15":"HI","16":"ID","17":"IL","18":"IN","19":"IA","20":"KS","21":"KY","22":"LA","23":"ME","24":"MD","25":"MA","26":"MI","27":"MN","28":"MS","29":"MO","30":"MT","31":"NE","32":"NV","33":"NH","34":"NJ","35":"NM","36":"NY","37":"NC","38":"ND","39":"OH","40":"OK","41":"OR","42":"PA","44":"RI","45":"SC","46":"SD","47":"TN","48":"TX","49":"UT","50":"VT","51":"VA","53":"WA","54":"WV","55":"WI","56":"WY"}};
        const latinNumeric = {{"484":"Mexico","076":"Brazil","032":"Argentina","152":"Chile","170":"Colombia","604":"Peru","862":"Venezuela","218":"Ecuador","320":"Guatemala","192":"Cuba","068":"Bolivia","332":"Haiti","214":"Dominican Republic","340":"Honduras","600":"Paraguay","222":"El Salvador","558":"Nicaragua","188":"Costa Rica","591":"Panama","858":"Uruguay"}};

        function getStateValues(mode) {{
            if (mode === 'alltime') return data.stateAlltime;
            const r = {{}};
            Object.entries(data.stateData).forEach(([s, c]) => {{ r[s] = c[c.length - 1] || 0; }});
            return r;
        }}

        function setMapMode(mode) {{
            currentMapMode = mode;
            document.getElementById('mapModeNew').className = mode === 'current' ? 'px-4 py-2 text-sm font-medium rounded-lg bg-indigo-600 text-white' : 'px-4 py-2 text-sm font-medium rounded-lg bg-gray-200 text-gray-700';
            document.getElementById('mapModeAll').className = mode === 'alltime' ? 'px-4 py-2 text-sm font-medium rounded-lg bg-indigo-600 text-white' : 'px-4 py-2 text-sm font-medium rounded-lg bg-gray-200 text-gray-700';
            if (usAtlasData) drawUSChoropleth();
            if (worldAtlasData) drawLatinChoropleth();
        }}

        function drawUSChoropleth() {{
            const el = document.getElementById('usMapEl');
            el.innerHTML = '';
            const values = getStateValues(currentMapMode);
            const maxVal = Math.max(...Object.values(values).filter(v => v > 0), 1);
            const wc = new Set(['CA', 'OR', 'WA']);
            const width = el.clientWidth || 500, height = 300;
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
                    return wc.has(sc) ? d3.interpolate('#bfdbfe', '#1d4ed8')(v / maxVal) : d3.interpolate('#d1fae5', '#065f46')(v / maxVal);
                }})
                .attr('stroke', d => wc.has(fipsToState[String(d.id).padStart(2, '0')]) ? '#1d4ed8' : '#9ca3af')
                .attr('stroke-width', d => wc.has(fipsToState[String(d.id).padStart(2, '0')]) ? 1.5 : 0.5)
                .style('cursor', 'pointer')
                .on('mouseover', function(event, d) {{
                    const sc = fipsToState[String(d.id).padStart(2, '0')] || '';
                    const v = values[sc] || 0;
                    tip.style('display', 'block').html(`<strong>${{sc}}</strong><br>${{v}} job${{v !== 1 ? 's' : ''}}`);
                    d3.select(this).attr('stroke', '#111').attr('stroke-width', 2);
                }})
                .on('mousemove', event => tip.style('left', (event.pageX + 12) + 'px').style('top', (event.pageY - 28) + 'px'))
                .on('mouseout', function(event, d) {{
                    const sc = fipsToState[String(d.id).padStart(2, '0')];
                    tip.style('display', 'none');
                    d3.select(this).attr('stroke', wc.has(sc) ? '#1d4ed8' : '#9ca3af').attr('stroke-width', wc.has(sc) ? 1.5 : 0.5);
                }})
                .on('click', (event, d) => {{
                    const sc = fipsToState[String(d.id).padStart(2, '0')];
                    if (sc) showStateDetail(sc);
                }});
        }}

        function drawLatinChoropleth() {{
            const el = document.getElementById('latinMapEl');
            el.innerHTML = '';
            const values = {{}};
            Object.entries(data.latinData).forEach(([country, counts]) => {{
                values[country] = currentMapMode === 'alltime' ? counts.reduce((a, b) => a + b, 0) : (counts[counts.length - 1] || 0);
            }});
            const maxVal = Math.max(...Object.values(values).filter(v => v > 0), 1);
            const numericVals = {{}};
            Object.entries(latinNumeric).forEach(([code, country]) => {{ numericVals[code] = values[country] || 0; }});
            const latinSet = new Set(Object.keys(latinNumeric));
            const allFeatures = topojson.feature(worldAtlasData, worldAtlasData.objects.countries).features;
            const latinFeatures = allFeatures.filter(d => latinSet.has(String(d.id).padStart(3, '0')));
            if (latinFeatures.length === 0) {{ el.innerHTML = '<div class="text-gray-400 text-center p-4 text-sm">No Latin American jobs tracked yet</div>'; return; }}
            const width = el.clientWidth || 400, height = 300;
            const projection = d3.geoMercator().fitSize([width, height], {{type: 'FeatureCollection', features: latinFeatures}});
            const path = d3.geoPath().projection(projection);
            const svg = d3.select('#latinMapEl').append('svg').attr('width', '100%').attr('height', height).attr('viewBox', `0 0 ${{width}} ${{height}}`);
            const tip = d3.select('#mapTooltip');
            svg.append('g').selectAll('path').data(latinFeatures).join('path')
                .attr('d', path)
                .attr('fill', d => {{
                    const code = String(d.id).padStart(3, '0');
                    const v = numericVals[code] || 0;
                    if (v === 0) return '#e5e7eb';
                    return d3.interpolate('#fce7f3', '#9d174d')(v / maxVal);
                }})
                .attr('stroke', '#9ca3af').attr('stroke-width', 0.5).style('cursor', 'default')
                .on('mouseover', function(event, d) {{
                    const code = String(d.id).padStart(3, '0');
                    const country = latinNumeric[code] || '';
                    const v = numericVals[code] || 0;
                    if (!country) return;
                    tip.style('display', 'block').html(`<strong>${{country}}</strong><br>${{v}} job${{v !== 1 ? 's' : ''}}`);
                    d3.select(this).attr('stroke', '#111').attr('stroke-width', 1.5);
                }})
                .on('mousemove', event => tip.style('left', (event.pageX + 12) + 'px').style('top', (event.pageY - 28) + 'px'))
                .on('mouseout', function() {{
                    tip.style('display', 'none');
                    d3.select(this).attr('stroke', '#9ca3af').attr('stroke-width', 0.5);
                }});
        }}

        async function initMaps() {{
            try {{
                [usAtlasData, worldAtlasData] = await Promise.all([
                    d3.json('https://cdn.jsdelivr.net/npm/us-atlas@3/states-10m.json'),
                    d3.json('https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json')
                ]);
                drawUSChoropleth();
                drawLatinChoropleth();
            }} catch(e) {{
                document.getElementById('usMapEl').innerHTML = '<div class="text-gray-400 text-center p-4 text-sm">Map unavailable — check connection</div>';
                document.getElementById('latinMapEl').innerHTML = '<div class="text-gray-400 text-center p-4 text-sm">Map unavailable</div>';
            }}
        }}
        initMaps();

        // ===== STATE DETAIL PANEL =====
        let stateTrendChart = null;
        const catColors = {json.dumps(MAIN_AOS_COLORS)};

        function showStateDetail(stateCode) {{
            const weekly = data.stateData[stateCode] || [];
            const current = weekly[weekly.length - 1] || 0;
            const alltime = data.stateAlltime[stateCode] || 0;
            const categories = data.stateCategoryData[stateCode] || {{}};
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
            const sorted = Object.entries(categories).sort((a, b) => b[1] - a[1]);
            const total = sorted.reduce((s, [, v]) => s + v, 0);
            if (sorted.length === 0) {{
                breakdown.innerHTML = '<div class="text-gray-400 text-sm">No category data yet</div>';
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
            document.getElementById('stateDetailPanel').classList.remove('hidden');
        }}

        function closeStatePanel() {{
            document.getElementById('stateDetailPanel').classList.add('hidden');
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
        print(f"✓ Dashboard written to {dashboard_file} (GitHub Pages)")

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

    # 5. Migrate/reclassify any existing jobs without classification or with old labels
    unclassified = [j for j in historical_data['jobs'] if not j.get('classification')]
    needs_migration = [j for j in historical_data['jobs']
                       if j.get('classification') and not j['classification'].get('position_type')]
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

    # 6. Compute co-occurrence
    print("\nComputing co-occurrence data...")
    scraper.compute_cooccurrence(historical_data)

    # 7. Generate dashboard
    print("\nGenerating comprehensive dashboard...")
    scraper.generate_trend_dashboard(historical_data)

    # 8. Generate report + CSV
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

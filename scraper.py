#!/usr/bin/env python3
"""
PhilJobs Comprehensive Market Analytics Dashboard
Tracks new job postings, job types, locations, and institution types
"""

import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
from pathlib import Path
import hashlib
import time
import re
from collections import defaultdict

# Canonical specialization categories
SPECIALIZATION_MAP = {
    # Ethics categories
    'ethics': ['ethics', 'ethical', 'meta-ethics', 'metaethics', 'normative ethics'],
    'applied ethics': ['applied ethics', 'bioethics', 'biomedical ethics', 'medical ethics',
                       'healthcare ethics', 'research ethics', 'business ethics', 'clinical ethics',
                       'public health ethics', 'disability ethics', 'reproductive ethics',
                       'neuroethics', 'data ethics'],
    'environmental ethics': ['environmental ethics', 'environmental philosophy', 'climate ethics'],
    'ai ethics': ['ai ethics', 'ethics of ai', 'ethics of artificial intelligence',
                  'artificial intelligence ethics', 'ethics & philosophy of technology'],

    # Political & Social
    'social and political philosophy': ['social and political philosophy', 'political philosophy',
                                        'social philosophy', 'political theory'],
    'philosophy of race': ['philosophy of race', 'racial justice'],
    'philosophy of gender': ['philosophy of gender', 'feminist philosophy', 'feminist epistemology'],
    'philosophy of law': ['philosophy of law', 'philosophy and law'],

    # History of Philosophy
    'ancient philosophy': ['ancient philosophy', 'ancient greek and roman philosophy'],
    'medieval philosophy': ['medieval philosophy', 'medieval and renaissance philosophy'],
    'early modern philosophy': ['early modern philosophy', 'early modern', 'modern philosophy',
                                'descartes to hegel', 'philosophy of enlightenment'],
    'continental philosophy': ['continental philosophy', '20th century european philosophy',
                               '21st century european philosophy', 'phenomenology',
                               'french phenomenology', 'francophone phenomenology'],
    'american philosophy': ['american philosophy', 'pragmatism'],
    'history of philosophy': ['history of philosophy', 'history of philosophical ethics'],

    # Non-Western Philosophy
    'asian philosophy': ['asian philosophy', 'east asian philosophy', 'chinese philosophy',
                         'indian philosophy', 'buddhist philosophy'],
    'african/africana philosophy': ['african philosophy', 'africana philosophy'],
    'latin american philosophy': ['latin american philosophy'],
    'islamic philosophy': ['islamic philosophy', 'arabic philosophy'],
    'indigenous philosophy': ['indigenous philosophy', 'native american philosophy',
                              'indigenous epistemologies'],

    # Metaphysics & Epistemology
    'metaphysics': ['metaphysics', 'metaphysics and epistemology'],
    'epistemology': ['epistemology', 'theory of knowledge', 'applied epistemology',
                     'social epistemology'],
    'philosophy of mind': ['philosophy of mind', 'philosophy of cognitive science',
                           'moral psychology', 'cognitive science'],
    'philosophy of language': ['philosophy of language'],
    'philosophy of action': ['philosophy of action'],
    'philosophy of religion': ['philosophy of religion'],

    # Science & Logic
    'philosophy of science': ['philosophy of science', 'general philosophy of science',
                              'history and philosophy of science', 'philosophy of biology',
                              'philosophy of medicine'],
    'philosophy of physics': ['philosophy of physics'],
    'logic': ['logic', 'symbolic logic', 'philosophy of logic'],
    'philosophy of mathematics': ['philosophy of mathematics'],
    'philosophy of technology': ['philosophy of technology', 'philosophy of computing',
                                 'sts', 'science and technology studies'],
    'philosophy of artificial intelligence': ['philosophy of artificial intelligence',
                                              'philosophy of ai', 'ai'],

    # Value Theory
    'aesthetics': ['aesthetics', 'philosophy of art'],
    'value theory': ['value theory', 'normativity', 'value theory and normativity'],

    # Other
    'ppe': ['ppe', 'politics philosophy and economics', 'philosophy and economics'],
    'public philosophy': ['public philosophy'],
    'critical thinking': ['critical thinking', 'informal logic'],
}

FILTER_WORDS = {
    'and', 'or', 'with', 'broadly', 'construed', 'open', 'preferred', 'including',
    'etc', 'especially', 'but', 'not', 'limited', 'to', 'the', 'in', 'of', 'a',
    'an', 'are', 'is', 'broadly construed', 'see advertisement', 'from any discipline'
}

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
    # California Bay Area
    'Berkeley': {'lat': 37.8715, 'lon': -122.2730, 'state': 'CA'},
    'Stanford': {'lat': 37.4275, 'lon': -122.1697, 'state': 'CA'},
    'San Francisco': {'lat': 37.7749, 'lon': -122.4194, 'state': 'CA'},
    'Oakland': {'lat': 37.8044, 'lon': -122.2712, 'state': 'CA'},
    'San Jose': {'lat': 37.3382, 'lon': -121.8863, 'state': 'CA'},
    'Santa Cruz': {'lat': 36.9741, 'lon': -122.0308, 'state': 'CA'},
    'Davis': {'lat': 38.5449, 'lon': -121.7405, 'state': 'CA'},
    # Southern California
    'Los Angeles': {'lat': 34.0522, 'lon': -118.2437, 'state': 'CA'},
    'San Diego': {'lat': 32.7157, 'lon': -117.1611, 'state': 'CA'},
    'Irvine': {'lat': 33.6846, 'lon': -117.8265, 'state': 'CA'},
    'Claremont': {'lat': 34.0967, 'lon': -117.7198, 'state': 'CA'},
    'Riverside': {'lat': 33.9533, 'lon': -117.3962, 'state': 'CA'},
    # Pacific Northwest
    'Seattle': {'lat': 47.6062, 'lon': -122.3321, 'state': 'WA'},
    'Portland': {'lat': 45.5152, 'lon': -122.6784, 'state': 'OR'},
    'Eugene': {'lat': 44.0521, 'lon': -123.0868, 'state': 'OR'},
    'Tacoma': {'lat': 47.2529, 'lon': -122.4443, 'state': 'WA'},
    'Olympia': {'lat': 47.0379, 'lon': -122.9007, 'state': 'WA'},
}


class PhilJobsScraper:
    def __init__(self):
        self.base_url = "https://philjobs.org"
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

    def normalize_specialization(self, raw_area):
        """Normalize a specialization to canonical form"""
        if not raw_area:
            return None

        area_lower = raw_area.lower().strip()

        if area_lower in FILTER_WORDS or len(area_lower) < 3:
            return None

        if any(area_lower.startswith(word + ' ') for word in ['or', 'and', 'with']):
            area_lower = ' '.join(area_lower.split()[1:])

        for canonical, variants in SPECIALIZATION_MAP.items():
            for variant in variants:
                if variant in area_lower:
                    return canonical

        # Drop overly long / messy fragments that aren't good categories
        if len(area_lower) > 15:
            return None

        return area_lower

    def extract_areas(self, area_string):
        """Extract and normalize areas from a string"""
        if not area_string or area_string.strip().lower() == 'open':
            return []

        raw_areas = re.split(r'[,;/]|\s+and\s+|\s+or\s+', area_string)

        normalized = []
        for raw in raw_areas:
            norm = self.normalize_specialization(raw)
            if norm and norm not in normalized:
                normalized.append(norm)

        return normalized

    def categorize_job_type(self, category_string, title_string):
        """Categorize job into tenure-track, postdoc, adjunct, tenured, or other"""
        combined = (f"{category_string} {title_string}").lower()

        if any(word in combined for word in ['tenure-track', 'tenure track', 'assistant professor']):
            return 'Tenure-track'
        elif any(word in combined for word in ['postdoc', 'post-doc', 'postdoctoral', 'fellowship']):
            return 'Postdoc'
        elif any(word in combined for word in ['adjunct', 'visiting', 'lecturer', 'instructor']):
            return 'Adjunct/Visiting'
        elif any(word in combined for word in ['tenured', 'associate professor', 'full professor', 'professor']):
            return 'Tenured'
        else:
            return 'Other'

    def categorize_institution(self, institution_name):
        """Categorize institution type based on name patterns"""
        if not institution_name:
            return "Other"
        name_lower = institution_name.lower()

        teaching_keywords = ['community college', 'junior college', 'state college', 'technical college']
        research_keywords = ['university', 'college', 'institute', 'school of', 'seminary']
        known_research = ['mit', 'caltech', 'stanford', 'harvard', 'yale', 'princeton', 'columbia',
                          'oxford', 'cambridge', 'sorbonne']

        if any(word in name_lower for word in teaching_keywords):
            return 'Teaching College'
        elif any(name_lower == r or r in name_lower for r in known_research):
            return 'Research University'
        elif any(word in name_lower for word in research_keywords):
            return 'Research University'
        else:
            return 'Other'

    def extract_location_data(self, location_string):
        """Extract state, country, and city from location string"""
        if not location_string:
            return None, None, None

        # US detection (state name or abbreviation)
        for state_name, state_code in US_STATES.items():
            if state_name in location_string or state_code in location_string:
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

        # Try to extract a country name from the last segment of the location string
        parts = [p.strip() for p in location_string.split(',')]
        country_name = parts[-1] if parts and parts[-1] else 'Other International'
        return None, country_name, None

    def get_job_ids_from_listing(self):
        """Get all job IDs from the main listing page"""
        url = f"{self.base_url}/"

        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            job_ids = []
            job_links = soup.find_all('a', href=lambda x: x and '/job/show/' in x)

            for link in job_links:
                job_id = link['href'].split('/')[-1]
                if job_id.isdigit() and job_id not in job_ids:
                    job_ids.append(job_id)

            print(f"Found {len(job_ids)} job listings")
            return job_ids

        except Exception as e:
            print(f"Error fetching job listing: {e}")
            return []

    def scrape_job_details(self, job_id):
        """Scrape detailed information from a single job posting"""
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

            table_rows = soup.find_all('tr')

            for row in table_rows:
                cells = row.find_all('td')
                if len(cells) == 2:
                    key = cells[0].get_text(strip=True)
                    value = cells[1].get_text(strip=True)

                    if key == "Job category":
                        job['job_category'] = value
                    elif key == "AOS":
                        job['aos'] = value
                        job['aos_normalized'] = self.extract_areas(value)
                    elif key == "AOC":
                        job['aoc'] = value
                        job['aoc_normalized'] = self.extract_areas(value)
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

            job['job_type'] = self.categorize_job_type(
                job.get('job_category', ''),
                job.get('title', '')
            )
            job['institution_type'] = self.categorize_institution(job.get('institution', ''))

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
        """Scrape all jobs with full details"""
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

    def load_historical_data(self):
        """Load all historical job data"""
        all_data_file = self.data_dir / "all_jobs.json"
        if all_data_file.exists():
            with open(all_data_file, 'r') as f:
                data = json.load(f)
                if 'weekly_trends' not in data:
                    data['weekly_trends'] = []
                if 'weekly_snapshots' not in data:
                    data['weekly_snapshots'] = []
                if 'jobs' not in data:
                    data['jobs'] = []
                return data
        return {'jobs': [], 'weekly_snapshots': [], 'weekly_trends': []}

    def get_category_hierarchy(self):
        """Return category to subcategory mapping"""
        hierarchy = {}
        for canonical, _variants in SPECIALIZATION_MAP.items():
            if any(x in canonical for x in ['ethics', 'bioethics', 'environmental ethics', 'ai ethics']):
                parent = 'Ethics'
            elif any(x in canonical for x in ['political', 'social', 'race', 'gender', 'law']):
                parent = 'Social & Political'
            elif any(x in canonical for x in ['ancient', 'medieval', 'modern', 'continental', 'american', 'history of']):
                parent = 'History of Philosophy'
            elif any(x in canonical for x in ['asian', 'african', 'latin american', 'islamic', 'indigenous']):
                parent = 'Non-Western Philosophy'
            elif any(x in canonical for x in ['metaphysics', 'epistemology', 'mind', 'language', 'action', 'religion']):
                parent = 'Metaphysics & Epistemology'
            elif any(x in canonical for x in ['science', 'physics', 'logic', 'mathematics', 'technology', 'artificial intelligence']):
                parent = 'Science & Logic'
            elif any(x in canonical for x in ['aesthetics', 'value theory']):
                parent = 'Value Theory/Aesthetics'
            else:
                parent = 'Other'

            hierarchy.setdefault(parent, []).append(canonical)

        return hierarchy

    def calculate_weekly_trends(self, new_jobs, timestamp):
        """Calculate trends based on NEW jobs this week only"""
        aos_counts = defaultdict(int)
        job_type_counts = defaultdict(int)
        institution_type_counts = defaultdict(int)
        state_counts = defaultdict(int)
        country_counts = defaultdict(int)
        west_coast_city_counts = defaultdict(int)

        for job in new_jobs:
            for area in job.get('aos_normalized', []):
                aos_counts[area] += 1

            job_type = job.get('job_type', 'Other')
            job_type_counts[job_type] += 1

            inst_type = job.get('institution_type', 'Other')
            institution_type_counts[inst_type] += 1

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

        weekly_trend = {
            'date': timestamp,
            'new_jobs_count': len(new_jobs),
            'aos_counts': dict(aos_counts),
            'job_type_counts': dict(job_type_counts),
            'institution_type_counts': dict(institution_type_counts),
            'state_counts': dict(state_counts),
            'country_counts': dict(country_counts),
            'west_coast_city_counts': dict(west_coast_city_counts)
        }

        return weekly_trend

    def save_data(self, jobs, historical_data):
        """Save job data and update historical records"""
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

    def get_color_for_category(self, category):
        """Assign colors to categories"""
        colors = {
            'Ethics': '#ef4444',
            'Social & Political': '#3b82f6',
            'History of Philosophy': '#8b5cf6',
            'Non-Western Philosophy': '#ec4899',
            'Metaphysics & Epistemology': '#10b981',
            'Science & Logic': '#f59e0b',
            'Value Theory/Aesthetics': '#06b6d4',
            'Other': '#6b7280'
        }
        return colors.get(category, '#6b7280')

    def is_hiring_season(self, date_str):
        """Determine if date is in hiring season (Sept-Jan)"""
        date = datetime.strptime(date_str, "%Y-%m-%d")
        month = date.month
        return month >= 9 or month <= 1

    def generate_trend_dashboard(self, historical_data):
        """Generate comprehensive dashboard with maps and breakdowns"""
        trends = historical_data.get('weekly_trends', [])

        if len(trends) < 1:
            print("No data available yet for dashboard visualization")
            return

        dates = [t['date'] for t in trends]
        hierarchy = self.get_category_hierarchy()

        # Build parent category data from NEW jobs only
        parent_categories = {}
        subcategory_data = {}

        for trend in trends:
            aos_counts = trend.get('aos_counts', {})

            for parent, subcats in hierarchy.items():
                if parent not in parent_categories:
                    parent_categories[parent] = {
                        'data': [],
                        'subcategories': subcats,
                        'color': self.get_color_for_category(parent)
                    }

                parent_total = sum(aos_counts.get(subcat, 0) for subcat in subcats)
                parent_categories[parent]['data'].append(parent_total)

                for subcat in subcats:
                    subcategory_data.setdefault(subcat, []).append(aos_counts.get(subcat, 0))

        # Prepare job type data
        job_types = ['Tenure-track', 'Postdoc', 'Adjunct/Visiting', 'Tenured', 'Other']
        job_type_series = {jt: [] for jt in job_types}
        for trend in trends:
            for jt in job_types:
                job_type_series[jt].append(trend.get('job_type_counts', {}).get(jt, 0))

        # Prepare institution type data
        inst_types = ['Research University', 'Teaching College', 'Other']
        inst_type_series = {it: [] for it in inst_types}
        for trend in trends:
            for it in inst_types:
                inst_type_series[it].append(trend.get('institution_type_counts', {}).get(it, 0))

        # Prepare location data
        state_data = {state: [] for state in US_STATES.values()}
        for trend in trends:
            state_counts = trend.get('state_counts', {})
            for state_code in US_STATES.values():
                state_data[state_code].append(state_counts.get(state_code, 0))

        # West Coast city data
        west_coast_data = {}
        for trend in trends:
            for city, count in trend.get('west_coast_city_counts', {}).items():
                west_coast_data.setdefault(city, []).append(count)

        # Latin America data
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

        # Calculate totals for current week
        current_week_new_jobs = trends[-1]['new_jobs_count']
        total_unique_jobs = len(historical_data['jobs'])
        weeks_tracked = len(trends)

        # Seasonal markers
        seasonal_markers = []
        for i, date in enumerate(dates):
            if self.is_hiring_season(date):
                seasonal_markers.append({'index': i, 'label': 'Hiring Season'})

        # Generate HTML dashboard
        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Philosophy Job Market Analytics</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        body {{ font-family: 'Inter', sans-serif; }}
        .category-card:hover {{ transform: translateY(-2px); transition: all 0.3s; }}
        .stat-card {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }}
        .chart-container {{ min-height: 400px; }}
        .season-marker {{ background: rgba(251, 191, 36, 0.1); }}
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
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div class="stat-card rounded-xl shadow-lg p-6 text-white">
                <div class="text-3xl font-bold">{current_week_new_jobs}</div>
                <div class="text-indigo-100">New Jobs This Week</div>
            </div>
            <div class="bg-white rounded-xl shadow-lg p-6">
                <div class="text-3xl font-bold text-gray-800">{weeks_tracked}</div>
                <div class="text-gray-600">Weeks Tracked</div>
            </div>
            <div class="bg-white rounded-xl shadow-lg p-6">
                <div class="text-3xl font-bold text-gray-800">{total_unique_jobs}</div>
                <div class="text-gray-600">Total Unique Jobs</div>
            </div>
        </div>

        <div class="bg-white rounded-xl shadow-lg p-6 mb-8">
            <h2 class="text-2xl font-bold text-gray-800 mb-6">Market Overview</h2>
            <div class="text-sm text-gray-600 mb-4">
                <span class="inline-flex items-center">
                    <span class="w-3 h-3 bg-yellow-100 border-2 border-yellow-400 rounded-full mr-2"></span>
                    Shaded areas indicate hiring season (Sept-Jan)
                </span>
            </div>
            <div class="chart-container">
                <canvas id="mainChart"></canvas>
            </div>
        </div>

        <div class="bg-white rounded-xl shadow-lg p-6 mb-8">
            <h2 class="text-2xl font-bold text-gray-800 mb-6">Browse by Category</h2>
            <div id="categoryGrid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            </div>
        </div>

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
                        <div id="subcategoryGrid" class="grid grid-cols-2 md:grid-cols-3 gap-3 mb-6">
                        </div>
                    </div>

                    <div class="mb-6">
                        <h4 class="text-lg font-semibold text-gray-700 mb-4">Trend Over Time</h4>
                        <div class="chart-container">
                            <canvas id="detailChart"></canvas>
                        </div>
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

    <script>
        const data = {{
            dates: {json.dumps(dates)},
            categories: {json.dumps({k: {'name': k, 'data': v['data'], 'subcategories': v['subcategories'], 'color': v['color']} for k, v in parent_categories.items()})},
            subcategoryData: {json.dumps(subcategory_data)},
            jobTypeData: {json.dumps(job_type_series)},
            institutionTypeData: {json.dumps(inst_type_series)},
            stateData: {json.dumps(state_data)},
            westCoastData: {json.dumps(west_coast_data)},
            latinData: {json.dumps(latin_data)},
            westCoastCities: {json.dumps(WEST_COAST_CITIES)},
            seasonalMarkers: {json.dumps(seasonal_markers)}
        }};

        // Plugin to shade hiring season bands on the main chart
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

        // Main chart
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
            data: {{
                labels: data.dates,
                datasets: datasets
            }},
            plugins: [seasonPlugin],
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                interaction: {{
                    mode: 'index',
                    intersect: false,
                }},
                plugins: {{
                    legend: {{
                        position: 'bottom',
                        labels: {{
                            usePointStyle: true,
                            padding: 15,
                            font: {{ size: 12 }}
                        }}
                    }},
                    tooltip: {{
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        padding: 12,
                        callbacks: {{
                            afterLabel: function(context) {{
                                const idx = context.dataIndex;
                                if (data.seasonalMarkers.some(m => m.index === idx)) {{
                                    return '🌟 Hiring Season';
                                }}
                                return '';
                            }}
                        }}
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        ticks: {{ font: {{ size: 12 }} }},
                        grid: {{ color: 'rgba(0, 0, 0, 0.05)' }}
                    }},
                    x: {{
                        ticks: {{ font: {{ size: 12 }} }},
                        grid: {{ display: false }}
                    }}
                }}
            }}
        }});

        // Generate category cards
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
                    <div class="w-3 h-3 rounded-full" style="background-color: ${{cat.color}}"></div>
                </div>
                <div class="flex items-end justify-between">
                    <div>
                        <div class="text-3xl font-bold text-gray-800">${{currentJobs}}</div>
                        <div class="text-sm text-gray-500">new this week</div>
                    </div>
                    <div class="text-right">
                        <div class="text-sm font-semibold ${{change >= 0 ? 'text-green-600' : 'text-red-600'}}">
                            ${{change >= 0 ? '↑' : '↓'}} ${{Math.abs(change)}}
                        </div>
                        <div class="text-xs text-gray-500">${{changePercent}}%</div>
                    </div>
                </div>
                ${{cat.subcategories.length > 0 ? `
                    <div class="mt-3 pt-3 border-t border-gray-100">
                        <div class="text-xs text-gray-500">${{cat.subcategories.length}} subcategories</div>
                    </div>
                ` : ''}}
            `;

            categoryGrid.appendChild(card);
        }});

        let detailChart = null;
        let jobTypeChart = null;
        let institutionChart = null;

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

                const subcatCard = document.createElement('div');
                subcatCard.className = 'bg-gray-50 rounded-lg p-3 hover:bg-gray-100 transition-colors';
                subcatCard.innerHTML = `
                    <div class="font-medium text-gray-700 text-sm mb-1 capitalize">${{subcat}}</div>
                    <div class="flex items-center justify-between">
                        <span class="text-xl font-bold text-gray-800">${{subcatCurrent}}</span>
                        <span class="text-xs font-semibold ${{subcatChange >= 0 ? 'text-green-600' : 'text-red-600'}}">
                            ${{subcatChange >= 0 ? '↑' : '↓'}} ${{Math.abs(subcatChange)}}
                        </span>
                    </div>
                `;
                subcategoryGrid.appendChild(subcatCard);
            }});

            // Detail chart
            const detailCtx = document.getElementById('detailChart').getContext('2d');
            if (detailChart) detailChart.destroy();

            const detailDatasets = [{{
                label: category.name + ' (Total)',
                data: category.data,
                borderColor: category.color,
                backgroundColor: category.color + '40',
                tension: 0.4,
                fill: true,
                borderWidth: 3
            }}];

            const colors = ['#6366f1', '#ec4899', '#14b8a6', '#f59e0b', '#8b5cf6', '#f97316', '#06b6d4'];
            category.subcategories.forEach((subcat, idx) => {{
                const subcatData = data.subcategoryData[subcat] || [];
                detailDatasets.push({{
                    label: subcat,
                    data: subcatData,
                    borderColor: colors[idx % colors.length],
                    backgroundColor: colors[idx % colors.length] + '20',
                    tension: 0.4,
                    borderWidth: 2,
                    borderDash: [5, 5]
                }});
            }});

            detailChart = new Chart(detailCtx, {{
                type: 'line',
                data: {{
                    labels: data.dates,
                    datasets: detailDatasets
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        legend: {{ position: 'bottom', labels: {{ usePointStyle: true, padding: 15, font: {{ size: 11 }} }} }}
                    }},
                    scales: {{
                        y: {{ beginAtZero: true, ticks: {{ font: {{ size: 11 }} }} }},
                        x: {{ ticks: {{ font: {{ size: 11 }} }} }}
                    }}
                }}
            }});

            // Job type chart
            const jobTypeCtx = document.getElementById('jobTypeChart').getContext('2d');
            if (jobTypeChart) jobTypeChart.destroy();

            const jobTypeLabels = ['Tenure-track', 'Postdoc', 'Adjunct/Visiting', 'Tenured', 'Other'];
            const latestJobTypes = jobTypeLabels.map(t => ((data.jobTypeData[t] || []).slice(-1)[0] || 0));
            jobTypeChart = new Chart(jobTypeCtx, {{
                type: 'doughnut',
                data: {{
                    labels: jobTypeLabels,
                    datasets: [{{ data: latestJobTypes, backgroundColor: ['#10b981', '#3b82f6', '#f59e0b', '#8b5cf6', '#6b7280'] }}]
                }},
                options: {{ responsive: true, plugins: {{ legend: {{ position: 'bottom' }} }} }}
            }});

            // Institution type chart
            const instCtx = document.getElementById('institutionChart').getContext('2d');
            if (institutionChart) institutionChart.destroy();

            const instTypeLabels = ['Research University', 'Teaching College', 'Other'];
            const latestInstTypes = instTypeLabels.map(t => ((data.institutionTypeData[t] || []).slice(-1)[0] || 0));
            institutionChart = new Chart(instCtx, {{
                type: 'doughnut',
                data: {{
                    labels: instTypeLabels,
                    datasets: [{{ data: latestInstTypes, backgroundColor: ['#3b82f6', '#10b981', '#6b7280'] }}]
                }},
                options: {{ responsive: true, plugins: {{ legend: {{ position: 'bottom' }} }} }}
            }});

            // US States list (top 10)
            const statesList = document.getElementById('usStatesList');
            statesList.innerHTML = '';
            const latestStateData = Object.entries(data.stateData)
                .map(([state, counts]) => [state, counts[counts.length - 1] || 0])
                .filter(([s, c]) => c > 0)
                .sort((a, b) => b[1] - a[1])
                .slice(0, 10);

            if (latestStateData.length > 0) {{
                latestStateData.forEach(([state, count]) => {{
                    const isWestCoast = ['CA', 'OR', 'WA'].includes(state);
                    statesList.innerHTML += `
                        <div class="flex justify-between items-center py-2 px-3 ${{isWestCoast ? 'bg-blue-100 rounded' : ''}}">
                            <span class="font-medium ${{isWestCoast ? 'text-blue-900' : 'text-gray-700'}}">${{state}}</span>
                            <span class="font-bold ${{isWestCoast ? 'text-blue-900' : 'text-gray-800'}}">${{count}}</span>
                        </div>
                    `;
                }});

                // West Coast detail
                const westCoastDetail = document.getElementById('westCoastDetail');
                const westCoastCities = document.getElementById('westCoastCities');
                const wcData = Object.entries(data.westCoastData)
                    .map(([city, counts]) => [city, counts[counts.length - 1] || 0])
                    .filter(([c, cnt]) => cnt > 0)
                    .sort((a, b) => b[1] - a[1]);

                if (wcData.length > 0) {{
                    westCoastDetail.classList.remove('hidden');
                    westCoastCities.innerHTML = wcData.map(([city, count]) =>
                        `<div class="flex justify-between py-1"><span>${{city}}</span><span class="font-bold">${{count}}</span></div>`
                    ).join('');
                }} else {{
                    westCoastDetail.classList.add('hidden');
                }}
            }} else {{
                statesList.innerHTML = '<div class="text-gray-500 text-center py-8">No US jobs in this category</div>';
            }}

            // Latin America list
            const latinList = document.getElementById('latinCountriesList');
            latinList.innerHTML = '';
            const latinCounts = Object.entries(data.latinData)
                .map(([country, counts]) => [country, counts[counts.length - 1] || 0])
                .filter(([c, cnt]) => cnt > 0)
                .sort((a, b) => b[1] - a[1]);

            if (latinCounts.length > 0) {{
                latinCounts.forEach(([country, count]) => {{
                    latinList.innerHTML += `
                        <div class="flex justify-between items-center py-2 px-3">
                            <span class="font-medium text-gray-700">${{country}}</span>
                            <span class="font-bold text-gray-800">${{count}}</span>
                        </div>
                    `;
                }});
            }} else {{
                latinList.innerHTML = '<div class="text-gray-500 text-center py-8">No Latin American jobs in this category</div>';
            }}

            // Insights
            const insights = document.getElementById('insights');
            let insightText = '<ul class="space-y-1">';

            if (change > 0) {{
                const pct = previousJobs > 0 ? ((change / previousJobs) * 100).toFixed(1) : '∞';
                insightText += `<li>• Growing field: up ${{change}} new jobs from last week (+${{pct}}%)</li>`;
            }} else if (change < 0) {{
                insightText += `<li>• Declining: down ${{Math.abs(change)}} new jobs from last week</li>`;
            }} else {{
                insightText += `<li>• Stable: same number of new jobs as last week</li>`;
            }}

            const trendDir = category.data[category.data.length - 1] > category.data[0] ? 'upward' :
                             category.data[category.data.length - 1] < category.data[0] ? 'downward' : 'stable';
            insightText += `<li>• Overall trend since tracking began: ${{trendDir}}</li>`;
            insightText += `<li>• Average ${{average}} new jobs per week</li>`;

            if (category.subcategories.length > 0) {{
                let hottestSub = category.subcategories[0];
                let hottestCount = 0;
                category.subcategories.forEach(sub => {{
                    const subData = data.subcategoryData[sub] || [];
                    const subTotal = subData.reduce((a, b) => a + b, 0);
                    if (subTotal > hottestCount) {{
                        hottestCount = subTotal;
                        hottestSub = sub;
                    }}
                }});
                insightText += `<li>• Most active subcategory: ${{hottestSub}} (${{hottestCount}} total jobs)</li>`;
            }}

            insightText += '</ul>';
            insights.innerHTML = insightText;

            document.getElementById('detailModal').classList.remove('hidden');
        }}

        function closeModal() {{
            document.getElementById('detailModal').classList.add('hidden');
        }}

        document.addEventListener('keydown', (e) => {{
            if (e.key === 'Escape') closeModal();
        }});
    </script>
</body>
</html>'''

        # Write dashboard to docs/ for GitHub Pages
        docs_dir = Path("docs")
        docs_dir.mkdir(exist_ok=True)

        dashboard_file = docs_dir / "index.html"
        with open(dashboard_file, 'w') as f:
            f.write(html)

        print(f"✓ Dashboard written to {dashboard_file} (GitHub Pages)")

    def generate_report(self, new_jobs, snapshot, weekly_trend, historical_data):
        """Generate markdown report"""
        report = f"""# PhilJobs Weekly Report
**Date:** {snapshot['date']}

## Summary
- **New jobs this week:** {snapshot['new_jobs']}
- **Total unique jobs tracked:** {len(historical_data['jobs'])}
- **Total weekly snapshots:** {len(historical_data['weekly_snapshots'])}

## 📊 View Interactive Dashboard
[**Click here to view the comprehensive analytics dashboard**](../docs/index.html)

The dashboard includes:
- Category trends with seasonal markers
- Subcategory drill-downs
- Job type and institution breakdowns
- Geographic heat maps (US and Latin America)
- West Coast city-level detail

## Top Specializations This Week (New Jobs)
"""

        aos_counts = weekly_trend.get('aos_counts', {})
        if aos_counts:
            report += "| Rank | Specialization | New Jobs |\n"
            report += "|------|----------------|----------|\n"
            for i, (area, count) in enumerate(sorted(aos_counts.items(), key=lambda x: x[1], reverse=True)[:20], 1):
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


def main():
    scraper = PhilJobsScraper()

    print("Starting PhilJobs comprehensive market analytics...")
    print("=" * 70)

    jobs = scraper.scrape_jobs()

    print("\nLoading historical data...")
    historical_data = scraper.load_historical_data()

    print("Analyzing new jobs and calculating trends...")
    new_jobs, snapshot, weekly_trend = scraper.save_data(jobs, historical_data)
    print(f"Identified {len(new_jobs)} NEW jobs this week")

    print("\nGenerating comprehensive dashboard...")
    scraper.generate_trend_dashboard(historical_data)

    print("\nGenerating report...")
    scraper.generate_report(new_jobs, snapshot, weekly_trend, historical_data)

    print(f"\n✓ Done! Data saved to {scraper.data_dir}/")
    print(f"  - all_jobs.json: {len(historical_data['jobs'])} unique jobs")
    print(f"  - snapshot_{snapshot['date']}.json: This week's data")
    print(f"  - report_{snapshot['date']}.md: Human-readable report")
    print(f"  - docs/index.html: Interactive analytics dashboard (GitHub Pages)")


if __name__ == "__main__":
    main()

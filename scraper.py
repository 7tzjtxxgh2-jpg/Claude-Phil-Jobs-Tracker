#!/usr/bin/env python3
"""
PhilJobs Weekly Scraper with Clean Categorization
Normalizes and consolidates specialization areas for better trend analysis
"""

import requests
from bs4 import BeautifulSoup
import json
import os
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

# Words to filter out
FILTER_WORDS = {
    'and', 'or', 'with', 'broadly', 'construed', 'open', 'preferred', 'including',
    'etc', 'especially', 'but', 'not', 'limited', 'to', 'the', 'in', 'of', 'a',
    'an', 'are', 'is', 'broadly construed', 'see advertisement', 'from any discipline'
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
        
        # Filter out noise words
        if area_lower in FILTER_WORDS or len(area_lower) < 3:
            return None
        
        # Check if it starts with common noise
        if any(area_lower.startswith(word + ' ') for word in ['or', 'and', 'with']):
            area_lower = ' '.join(area_lower.split()[1:])
        
        # Map to canonical category
        for canonical, variants in SPECIALIZATION_MAP.items():
            for variant in variants:
                if variant in area_lower or area_lower in variant:
                    return canonical
        
        # If no match and it's a substantial phrase, keep it as "other"
        if len(area_lower) > 15:
            return None  # Probably a full sentence, skip it
        
        return area_lower  # Keep unknown but reasonable specializations
    
    def extract_areas(self, area_string):
        """Extract and normalize areas from a string"""
        if not area_string or area_string.strip().lower() == 'open':
            return []
        
        # Split on multiple delimiters
        raw_areas = re.split(r'[,;/]|\s+and\s+|\s+or\s+', area_string)
        
        normalized = []
        for raw in raw_areas:
            norm = self.normalize_specialization(raw)
            if norm and norm not in normalized:
                normalized.append(norm)
        
        return normalized
    
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
            
            if "(EXPIRED)" in job.get('title', ''):
                job['status'] = 'expired'
                job['title'] = job['title'].replace('(EXPIRED)', '').strip()
            else:
                job['status'] = 'active'
            
            unique_str = f"{job.get('institution', '')}_{job.get('title', '')}_{job_id}"
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
                return data
        return {'jobs': [], 'weekly_snapshots': [], 'weekly_trends': []}
    
    def calculate_weekly_trends(self, jobs, historical_data, timestamp):
        """Calculate trends for this week using normalized categories"""
        aos_counts = defaultdict(int)
        aoc_counts = defaultdict(int)
        category_counts = defaultdict(int)
        location_counts = defaultdict(int)
        
        active_jobs = [j for j in jobs if j.get('status') == 'active']
        
        for job in active_jobs:
            # Count normalized AOS
            for area in job.get('aos_normalized', []):
                aos_counts[area] += 1
            
            # Count normalized AOC
            for area in job.get('aoc_normalized', []):
                aoc_counts[area] += 1
            
            category = job.get('job_category', '')
            if category:
                category_counts[category] += 1
            
            location = job.get('location', '')
            if location:
                location_counts[location] += 1
        
        weekly_trend = {
            'date': timestamp,
            'total_active_jobs': len(active_jobs),
            'aos_counts': dict(aos_counts),
            'aoc_counts': dict(aoc_counts),
            'category_counts': dict(category_counts),
            'location_counts': dict(location_counts)
        }
        
        return weekly_trend
    
    def save_data(self, jobs, historical_data):
        """Save job data and update historical records"""
        timestamp = datetime.now().strftime("%Y-%m-%d")
        
        existing_hashes = {job['hash'] for job in historical_data['jobs']}
        new_jobs = [job for job in jobs if job['hash'] not in existing_hashes]
        historical_data['jobs'].extend(new_jobs)
        
        weekly_trend = self.calculate_weekly_trends(jobs, historical_data, timestamp)
        historical_data['weekly_trends'].append(weekly_trend)
        
        snapshot = {
            'date': timestamp,
            'total_jobs': len(jobs),
            'active_jobs': len([j for j in jobs if j.get('status') == 'active']),
            'new_jobs': len(new_jobs),
            'new_job_ids': [job['id'] for job in new_jobs]
        }
        historical_data['weekly_snapshots'].append(snapshot)
        
        all_data_file = self.data_dir / "all_jobs.json"
        with open(all_data_file, 'w') as f:
            json.dump(historical_data, f, indent=2)
        
        weekly_file = self.data_dir / f"snapshot_{timestamp}.json"
        with open(weekly_file, 'w') as f:
            json.dump({
                'date': timestamp,
                'jobs': jobs,
                'new_jobs': new_jobs
            }, f, indent=2)
        
        return new_jobs, snapshot, weekly_trend
    
    def get_category_hierarchy(self):
        """Return category to subcategory mapping"""
        hierarchy = {}
        for canonical, variants in SPECIALIZATION_MAP.items():
            # Determine parent category
            parent = None
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
                parent = 'Value Theory'
            else:
                parent = 'Other'
            
            if parent not in hierarchy:
                hierarchy[parent] = []
            hierarchy[parent].append(canonical)
        
        return hierarchy
    
    def generate_trend_dashboard(self, historical_data):
        """Generate modern interactive HTML dashboard with Tailwind CSS"""
        trends = historical_data.get('weekly_trends', [])
        
        if len(trends) < 2:
            print("Need at least 2 weeks of data for trend visualization")
            return
        
        dates = [t['date'] for t in trends]
        
        # Build category hierarchy
        hierarchy = self.get_category_hierarchy()
        
        # Aggregate data by parent categories and track subcategories
        parent_categories = {}
        subcategory_data = {}
        
        for trend in trends:
            aos_counts = trend.get('aos_counts', {})
            
            for parent, subcats in hierarchy.items():
                if parent not in parent_categories:
                    parent_categories[parent] = {'data': [], 'subcategories': subcats, 'color': self.get_color_for_category(parent)}
                
                # Sum up all subcategories for this parent
                parent_total = sum(aos_counts.get(subcat, 0) for subcat in subcats)
                parent_categories[parent]['data'].append(parent_total)
                
                # Track individual subcategory data
                for subcat in subcats:
                    if subcat not in subcategory_data:
                        subcategory_data[subcat] = []
                    subcategory_data[subcat].append(aos_counts.get(subcat, 0))
        
        total_jobs_series = [t['total_active_jobs'] for t in trends]
        
        # Generate modern dashboard HTML
        html = f"""<!DOCTYPE html>
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
    </style>
</head>
<body class="bg-gray-50">
    <!-- Header -->
    <div class="bg-gradient-to-r from-indigo-600 to-purple-600 text-white">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
            <h1 class="text-4xl font-bold mb-2">Philosophy Job Market Analytics</h1>
            <p class="text-indigo-100">Real-time trends and insights from PhilJobs</p>
            <div class="mt-6 text-sm text-indigo-100">Last updated: {datetime.now().strftime("%B %d, %Y")}</div>
        </div>
    </div>

    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <!-- Stats Overview -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div class="stat-card rounded-xl shadow-lg p-6 text-white">
                <div class="text-3xl font-bold">{trends[-1]['total_active_jobs']}</div>
                <div class="text-indigo-100">Active Jobs</div>
            </div>
            <div class="bg-white rounded-xl shadow-lg p-6">
                <div class="text-3xl font-bold text-gray-800">{len(trends)}</div>
                <div class="text-gray-600">Weeks Tracked</div>
            </div>
            <div class="bg-white rounded-xl shadow-lg p-6">
                <div class="text-3xl font-bold text-gray-800">{len(historical_data['jobs'])}</div>
                <div class="text-gray-600">Total Unique Jobs</div>
            </div>
        </div>

        <!-- Main Chart -->
        <div class="bg-white rounded-xl shadow-lg p-6 mb-8">
            <h2 class="text-2xl font-bold text-gray-800 mb-6">Market Overview</h2>
            <div class="chart-container">
                <canvas id="mainChart"></canvas>
            </div>
        </div>

        <!-- Category Selection -->
        <div class="bg-white rounded-xl shadow-lg p-6 mb-8">
            <h2 class="text-2xl font-bold text-gray-800 mb-6">Browse by Category</h2>
            <div id="categoryGrid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <!-- Categories will be inserted here -->
            </div>
        </div>

        <!-- Detailed View Modal -->
        <div id="detailModal" class="hidden fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
            <div class="bg-white rounded-xl shadow-2xl max-w-6xl w-full max-h-[90vh] overflow-y-auto">
                <div class="sticky top-0 bg-white border-b px-6 py-4 flex justify-between items-center">
                    <h3 id="modalTitle" class="text-2xl font-bold text-gray-800"></h3>
                    <button onclick="closeModal()" class="text-gray-400 hover:text-gray-600">
                        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                        </svg>
                    </button>
                </div>
                <div class="p-6">
                    <!-- Subcategories -->
                    <div id="subcategorySection" class="mb-6">
                        <h4 class="text-lg font-semibold text-gray-700 mb-4">Subcategories</h4>
                        <div id="subcategoryGrid" class="grid grid-cols-2 md:grid-cols-3 gap-3 mb-6">
                            <!-- Subcategories will be inserted here -->
                        </div>
                    </div>
                    
                    <!-- Trend Chart -->
                    <div class="mb-6">
                        <h4 class="text-lg font-semibold text-gray-700 mb-4">Trend Over Time</h4>
                        <div class="chart-container">
                            <canvas id="detailChart"></canvas>
                        </div>
                    </div>

                    <!-- Stats -->
                    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                        <div class="bg-gray-50 rounded-lg p-4">
                            <div class="text-2xl font-bold text-indigo-600" id="modalCurrentJobs">0</div>
                            <div class="text-sm text-gray-600">Current Jobs</div>
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

                    <!-- Key Insights -->
                    <div id="insightsSection" class="bg-blue-50 border-l-4 border-blue-500 rounded-lg p-4">
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
            totalJobs: {json.dumps(total_jobs_series)},
            categories: {json.dumps({k: {'name': k, 'data': v['data'], 'subcategories': v['subcategories'], 'color': v['color']} for k, v in parent_categories.items()})},
            subcategoryData: {json.dumps(subcategory_data)}
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
                        titleFont: {{ size: 14, weight: 'bold' }},
                        bodyFont: {{ size: 13 }}
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
                        <div class="text-sm text-gray-500">jobs this week</div>
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
                subcatCard.className = 'bg-gray-50 rounded-lg p-3 hover:bg-gray-100 transition-colors cursor-pointer';
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
            
            // Insights
            const insights = document.getElementById('insights');
            let insightText = `<ul class="space-y-1">`;
            
            if (change > 0) {{
                insightText += `<li>• Growing field: up ${{change}} jobs from last week</li>`;
            }} else if (change < 0) {{
                insightText += `<li>• Declining: down ${{Math.abs(change)}} jobs from last week</li>`;
            }} else {{
                insightText += `<li>• Stable market with consistent demand</li>`;
            }}
            
            const trend = category.data[category.data.length - 1] > category.data[0] ? 'upward' : 
                         category.data[category.data.length - 1] < category.data[0] ? 'downward' : 'stable';
            insightText += `<li>• Overall trend: ${{trend}}</li>`;
            insightText += `<li>• Average ${{average}} jobs per week</li>`;
            
            if (category.subcategories.length > 0) {{
                // Find hottest subcategory
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
            
            insightText += `</ul>`;
            insights.innerHTML = insightText;
            
            // Detail chart
            const detailCtx = document.getElementById('detailChart').getContext('2d');
            
            if (detailChart) {{
                detailChart.destroy();
            }}
            
            const detailDatasets = [{{
                label: category.name + ' (Total)',
                data: category.data,
                borderColor: category.color,
                backgroundColor: category.color + '40',
                tension: 0.4,
                fill: true,
                borderWidth: 3
            }}];
            
            // Add subcategory lines
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
                            padding: 12
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
            
            document.getElementById('detailModal').classList.remove('hidden');
        }}

        function closeModal() {{
            document.getElementById('detailModal').classList.add('hidden');
        }}

        // Close modal on escape key
        document.addEventListener('keydown', (e) => {{
            if (e.key === 'Escape') closeModal();
        }});
    </script>
</body>
</html>"""
        
        dashboard_file = self.data_dir / "trends_dashboard.html"
        with open(dashboard_file, 'w') as f:
            f.write(html)
        
        print(f"✓ Modern trend dashboard generated: {dashboard_file}")
    
    def get_color_for_category(self, category):
        """Assign colors to categories"""
        colors = {
            'Ethics': '#ef4444',
            'Social & Political': '#3b82f6',
            'History of Philosophy': '#8b5cf6',
            'Non-Western Philosophy': '#ec4899',
            'Metaphysics & Epistemology': '#10b981',
            'Science & Logic': '#f59e0b',
            'Value Theory': '#06b6d4',
            'Other': '#6b7280'
        }
        return colors.get(category, '#6b7280')
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>PhilJobs Market Trends Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        h1 {{
            color: #333;
            text-align: center;
        }}
        .chart-container {{
            background: white;
            padding: 20px;
            margin: 20px 0;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .summary {{
            background: white;
            padding: 20px;
            margin: 20px 0;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .stat {{
            display: inline-block;
            margin: 10px 20px;
        }}
        .stat-value {{
            font-size: 32px;
            font-weight: bold;
            color: #2c5282;
        }}
        .stat-label {{
            font-size: 14px;
            color: #666;
        }}
        .insights {{
            background: #e6f7ff;
            padding: 15px;
            margin: 20px 0;
            border-radius: 8px;
            border-left: 4px solid #1890ff;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background: #f0f0f0;
            font-weight: bold;
        }}
        .trend-up {{
            color: green;
        }}
        .trend-down {{
            color: red;
        }}
    </style>
</head>
<body>
    <h1>📊 Philosophy Job Market Trends</h1>
    <p style="text-align: center; color: #666;">Last updated: {datetime.now().strftime("%B %d, %Y")}</p>
    
    <div class="summary">
        <h2>Current Market Summary</h2>
        <div class="stat">
            <div class="stat-value">{trends[-1]['total_active_jobs']}</div>
            <div class="stat-label">Active Jobs</div>
        </div>
        <div class="stat">
            <div class="stat-value">{len(trends)}</div>
            <div class="stat-label">Weeks Tracked</div>
        </div>
        <div class="stat">
            <div class="stat-value">{len(historical_data['jobs'])}</div>
            <div class="stat-label">Total Unique Jobs</div>
        </div>
    </div>
    
    <div class="chart-container">
        <h2>Total Active Jobs Over Time</h2>
        <canvas id="totalJobsChart"></canvas>
    </div>
    
    <div class="chart-container">
        <h2>Top Specializations: Week-by-Week Trends</h2>
        <canvas id="aosChart"></canvas>
    </div>
    
    <div class="insights">
        <h3>💡 Key Insights</h3>
        <div id="insights"></div>
    </div>
    
    <div class="chart-container">
        <h2>Specialization Rankings (Current Week)</h2>
        <table id="rankingTable"></table>
    </div>

    <script>
        new Chart(document.getElementById('totalJobsChart'), {{
            type: 'line',
            data: {{
                labels: {json.dumps(dates)},
                datasets: [{{
                    label: 'Total Active Jobs',
                    data: {json.dumps(total_jobs_series)},
                    borderColor: '#2c5282',
                    backgroundColor: 'rgba(44, 82, 130, 0.1)',
                    tension: 0.4,
                    fill: true
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{
                        display: true
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        title: {{
                            display: true,
                            text: 'Number of Jobs'
                        }}
                    }}
                }}
            }}
        }});

        const colors = [
            '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF',
            '#FF9F40', '#FF6384', '#C9CBCF', '#4BC0C0', '#FF6384',
            '#E7E9ED', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF'
        ];
        
        const datasets = [];
        const aosData = {json.dumps(aos_series)};
        const aosNames = {json.dumps(top_aos_names)};
        
        aosNames.forEach((name, index) => {{
            datasets.push({{
                label: name,
                data: aosData[name],
                borderColor: colors[index % colors.length],
                backgroundColor: colors[index % colors.length] + '33',
                tension: 0.4
            }});
        }});

        new Chart(document.getElementById('aosChart'), {{
            type: 'line',
            data: {{
                labels: {json.dumps(dates)},
                datasets: datasets
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{
                        display: true,
                        position: 'right'
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        title: {{
                            display: true,
                            text: 'Number of Jobs'
                        }}
                    }}
                }}
            }}
        }});

        const insightsDiv = document.getElementById('insights');
        const currentWeek = {json.dumps(trends[-1]['aos_counts'])};
        const previousWeek = {json.dumps(trends[-2]['aos_counts'] if len(trends) > 1 else {})};
        
        let insights = '<ul>';
        Object.keys(currentWeek).sort((a, b) => currentWeek[b] - currentWeek[a]).slice(0, 5).forEach(field => {{
            const current = currentWeek[field];
            const previous = previousWeek[field] || 0;
            const change = current - previous;
            const changePercent = previous > 0 ? ((change / previous) * 100).toFixed(1) : 'N/A';
            const trend = change > 0 ? '📈' : change < 0 ? '📉' : '➡️';
            const trendClass = change > 0 ? 'trend-up' : change < 0 ? 'trend-down' : '';
            
            insights += `<li><strong>${{field}}</strong>: ${{current}} jobs this week `;
            if (change !== 0) {{
                insights += `<span class="${{trendClass}}">${{trend}} ${{change > 0 ? '+' : ''}}${{change}} (${{changePercent}}%)</span>`;
            }}
            insights += '</li>';
        }});
        insights += '</ul>';
        insightsDiv.innerHTML = insights;

        const tableDiv = document.getElementById('rankingTable');
        let tableHTML = '<thead><tr><th>Rank</th><th>Specialization</th><th>Current Jobs</th><th>Change vs Last Week</th></tr></thead><tbody>';
        
        Object.entries(currentWeek).sort((a, b) => b[1] - a[1]).slice(0, 20).forEach((entry, index) => {{
            const [field, count] = entry;
            const previous = previousWeek[field] || 0;
            const change = count - previous;
            const arrow = change > 0 ? '↑' : change < 0 ? '↓' : '→';
            const trendClass = change > 0 ? 'trend-up' : change < 0 ? 'trend-down' : '';
            
            tableHTML += `<tr>
                <td>${{index + 1}}</td>
                <td><strong>${{field}}</strong></td>
                <td>${{count}}</td>
                <td class="${{trendClass}}">${{arrow}} ${{change > 0 ? '+' : ''}}${{change}}</td>
            </tr>`;
        }});
        tableHTML += '</tbody>';
        tableDiv.innerHTML = tableHTML;
    </script>
</body>
</html>"""
        
        dashboard_file = self.data_dir / "trends_dashboard.html"
        with open(dashboard_file, 'w') as f:
            f.write(html)
        
        print(f"✓ Trend dashboard generated: {dashboard_file}")
    
    def generate_report(self, new_jobs, snapshot, weekly_trend, historical_data):
        """Generate markdown report"""
        report = f"""# PhilJobs Weekly Report
**Date:** {snapshot['date']}

## Summary
- **Total jobs scraped this week:** {snapshot['total_jobs']}
- **Active jobs:** {snapshot.get('active_jobs', 'N/A')}
- **New unique jobs:** {snapshot['new_jobs']}
- **Total unique jobs tracked:** {len(historical_data['jobs'])}
- **Total weekly snapshots:** {len(historical_data['weekly_snapshots'])}

## 📊 View Interactive Trends
[**Click here to view the interactive trend dashboard**](./trends_dashboard.html)

The dashboard shows week-by-week changes in job postings by specialization with visual charts.

## Top Specializations This Week (Normalized Categories)
"""
        
        aos_counts = weekly_trend.get('aos_counts', {})
        if aos_counts:
            report += "| Rank | Specialization | Jobs This Week |\n"
            report += "|------|----------------|----------------|\n"
            for i, (area, count) in enumerate(sorted(aos_counts.items(), key=lambda x: x[1], reverse=True)[:20], 1):
                report += f"| {i} | {area} | {count} |\n"
        
        report += f"\n## New Jobs This Week ({len(new_jobs)} total)\n"
        
        if new_jobs:
            for job in new_jobs[:15]:
                report += f"\n### {job.get('institution', 'Unknown')}\n"
                report += f"**Position:** {job.get('title', 'Unknown')}\n"
                
                if job.get('job_category'):
                    report += f"**Type:** {job['job_category']}\n"
                
                if job.get('aos') and job['aos'] != 'Open':
                    report += f"**AOS:** {job['aos']}\n"
                    if job.get('aos_normalized'):
                        report += f"**AOS (normalized):** {', '.join(job['aos_normalized'])}\n"
                
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
        
        print("\n" + "="*70)
        print(report)
        print("="*70)

def main():
    scraper = PhilJobsScraper()
    
    print("Starting PhilJobs scraper with clean categorization...")
    print("="*70)
    
    jobs = scraper.scrape_jobs()
    
    print("\nLoading historical data...")
    historical_data = scraper.load_historical_data()
    
    print("Saving data and calculating trends...")
    new_jobs, snapshot, weekly_trend = scraper.save_data(jobs, historical_data)
    print(f"Identified {len(new_jobs)} new unique jobs")
    
    print("\nGenerating trend dashboard...")
    scraper.generate_trend_dashboard(historical_data)
    
    print("\nGenerating report...")
    scraper.generate_report(new_jobs, snapshot, weekly_trend, historical_data)
    
    print(f"\n✓ Done! Data saved to {scraper.data_dir}/")
    print(f"  - all_jobs.json: {len(historical_data['jobs'])} unique jobs")
    print(f"  - snapshot_{snapshot['date']}.json: This week's data")
    print(f"  - report_{snapshot['date']}.md: Human-readable report")
    print(f"  - trends_dashboard.html: Interactive trend visualization")

if __name__ == "__main__":
    main()

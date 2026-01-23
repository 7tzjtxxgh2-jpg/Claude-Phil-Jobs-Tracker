#!/usr/bin/env python3
"""
PhilJobs Weekly Scraper with Trend Dashboard
Tracks week-over-week changes and generates visual trend reports
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

class PhilJobsScraper:
    def __init__(self):
        self.base_url = "https://philjobs.org"
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
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
                    elif key == "AOC":
                        job['aoc'] = value
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
                return json.load(f)
        return {'jobs': [], 'weekly_snapshots': [], 'weekly_trends': []}
    
    def extract_areas(self, area_string):
        """Extract individual areas from comma/semicolon separated string"""
        if not area_string or area_string == 'Open':
            return []
        areas = re.split(r'[,;/]', area_string)
        return [area.strip() for area in areas if area.strip() and area.strip() != 'Open']
    
    def calculate_weekly_trends(self, jobs, historical_data, timestamp):
        """Calculate trends for this week"""
        aos_counts = defaultdict(int)
        aoc_counts = defaultdict(int)
        category_counts = defaultdict(int)
        location_counts = defaultdict(int)
        
        # Count active jobs only for current snapshot
        active_jobs = [j for j in jobs if j.get('status') == 'active']
        
        for job in active_jobs:
            # Count AOS
            for area in self.extract_areas(job.get('aos', '')):
                aos_counts[area] += 1
            
            # Count AOC
            for area in self.extract_areas(job.get('aoc', '')):
                aoc_counts[area] += 1
            
            # Count categories
            category = job.get('job_category', '')
            if category:
                category_counts[category] += 1
            
            # Count locations
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
        
        # Calculate this week's trends
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
    
    def generate_trend_dashboard(self, historical_data):
        """Generate interactive HTML dashboard with trend visualizations"""
        trends = historical_data.get('weekly_trends', [])
        
        if len(trends) < 2:
            print("Need at least 2 weeks of data for trend visualization")
            return
        
        # Prepare data for charts
        dates = [t['date'] for t in trends]
        
        # Get top 10 AOS fields across all time
        all_aos = defaultdict(int)
        for trend in trends:
            for aos, count in trend.get('aos_counts', {}).items():
                all_aos[aos] += count
        
        top_aos_fields = sorted(all_aos.items(), key=lambda x: x[1], reverse=True)[:10]
        top_aos_names = [field[0] for field in top_aos_fields]
        
        # Build time series for each top AOS
        aos_series = {}
        for aos_name in top_aos_names:
            aos_series[aos_name] = []
            for trend in trends:
                count = trend.get('aos_counts', {}).get(aos_name, 0)
                aos_series[aos_name].append(count)
        
        # Total jobs over time
        total_jobs_series = [t['total_active_jobs'] for t in trends]
        
        # Generate HTML with Chart.js
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
        // Total jobs chart
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

        // Top AOS fields chart
        const colors = [
            '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF',
            '#FF9F40', '#FF6384', '#C9CBCF', '#4BC0C0', '#FF6384'
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

        // Generate insights
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

        // Ranking table
        const tableDiv = document.getElementById('rankingTable');
        let tableHTML = '<thead><tr><th>Rank</th><th>Specialization</th><th>Current Jobs</th><th>Change vs Last Week</th></tr></thead><tbody>';
        
        Object.entries(currentWeek).sort((a, b) => b[1] - a[1]).forEach((entry, index) => {{
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

## Top Specializations This Week
"""
        
        aos_counts = weekly_trend.get('aos_counts', {})
        if aos_counts:
            report += "| Rank | Specialization | Jobs This Week |\n"
            report += "|------|----------------|----------------|\n"
            for i, (area, count) in enumerate(sorted(aos_counts.items(), key=lambda x: x[1], reverse=True)[:15], 1):
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
                
                if job.get('aoc') and job['aoc'] != 'Open':
                    report += f"**AOC:** {job['aoc']}\n"
                
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
    
    print("Starting PhilJobs scraper with trend tracking...")
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

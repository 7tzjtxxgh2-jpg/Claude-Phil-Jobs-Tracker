#!/usr/bin/env python3
"""
PhilJobs Weekly Scraper - Enhanced with Full Job Details
Automatically collects philosophy job postings and tracks unique entries
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
            # Be respectful - add a small delay
            time.sleep(0.5)
            
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract job data from the page
            job = {'id': job_id, 'url': url}
            
            # Get institution and title from h2 and h1
            h2 = soup.find('h2')
            h1 = soup.find('h1')
            job['institution'] = h2.get_text(strip=True) if h2 else "Unknown"
            job['title'] = h1.get_text(strip=True) if h1 else "Unknown"
            
            # Extract all table rows with job details
            table_rows = soup.find_all('tr')
            
            for row in table_rows:
                cells = row.find_all('td')
                if len(cells) == 2:
                    key = cells[0].get_text(strip=True)
                    value = cells[1].get_text(strip=True)
                    
                    # Map the keys to our data structure
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
                        # Get the full description text
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
            
            # Check if job is expired
            if "(EXPIRED)" in job.get('title', ''):
                job['status'] = 'expired'
                job['title'] = job['title'].replace('(EXPIRED)', '').strip()
            else:
                job['status'] = 'active'
            
            # Create unique hash for deduplication
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
        return {'jobs': [], 'weekly_snapshots': []}
    
    def save_data(self, jobs, historical_data):
        """Save job data and update historical records"""
        timestamp = datetime.now().strftime("%Y-%m-%d")
        
        # Get existing job hashes
        existing_hashes = {job['hash'] for job in historical_data['jobs']}
        
        # Identify new jobs
        new_jobs = [job for job in jobs if job['hash'] not in existing_hashes]
        
        # Add new jobs to historical data
        historical_data['jobs'].extend(new_jobs)
        
        # Create weekly snapshot
        snapshot = {
            'date': timestamp,
            'total_jobs': len(jobs),
            'active_jobs': len([j for j in jobs if j.get('status') == 'active']),
            'new_jobs': len(new_jobs),
            'new_job_ids': [job['id'] for job in new_jobs]
        }
        historical_data['weekly_snapshots'].append(snapshot)
        
        # Save all data
        all_data_file = self.data_dir / "all_jobs.json"
        with open(all_data_file, 'w') as f:
            json.dump(historical_data, f, indent=2)
        
        # Save this week's snapshot separately
        weekly_file = self.data_dir / f"snapshot_{timestamp}.json"
        with open(weekly_file, 'w') as f:
            json.dump({
                'date': timestamp,
                'jobs': jobs,
                'new_jobs': new_jobs
            }, f, indent=2)
        
        return new_jobs, snapshot
    
    def analyze_trends(self, historical_data):
        """Analyze job market trends from historical data"""
        if not historical_data['jobs']:
            return {}
        
        # Count by AOS
        aos_counts = {}
        aoc_counts = {}
        location_counts = {}
        category_counts = {}
        
        for job in historical_data['jobs']:
            # Count AOS
            aos = job.get('aos', '')
            if aos and aos != 'Open':
                # Split on common delimiters
                aos_areas = re.split(r'[,;/]', aos)
                for area in aos_areas:
                    area = area.strip()
                    if area and area != 'Open':
                        aos_counts[area] = aos_counts.get(area, 0) + 1
            
            # Count AOC
            aoc = job.get('aoc', '')
            if aoc and aoc != 'Open':
                aoc_areas = re.split(r'[,;/]', aoc)
                for area in aoc_areas:
                    area = area.strip()
                    if area and area != 'Open':
                        aoc_counts[area] = aoc_counts.get(area, 0) + 1
            
            # Count locations
            location = job.get('location', '')
            if location:
                location_counts[location] = location_counts.get(location, 0) + 1
            
            # Count job categories
            category = job.get('job_category', '')
            if category:
                category_counts[category] = category_counts.get(category, 0) + 1
        
        # Sort by popularity
        top_aos = sorted(aos_counts.items(), key=lambda x: x[1], reverse=True)[:30]
        top_aoc = sorted(aoc_counts.items(), key=lambda x: x[1], reverse=True)[:30]
        top_locations = sorted(location_counts.items(), key=lambda x: x[1], reverse=True)[:20]
        top_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
        
        return {
            'total_unique_jobs': len(historical_data['jobs']),
            'total_snapshots': len(historical_data['weekly_snapshots']),
            'top_aos': top_aos,
            'top_aoc': top_aoc,
            'top_locations': top_locations,
            'top_categories': top_categories
        }
    
    def generate_report(self, new_jobs, snapshot, trends):
        """Generate a comprehensive markdown report"""
        report = f"""# PhilJobs Weekly Report
**Date:** {snapshot['date']}

## Summary
- **Total jobs scraped this week:** {snapshot['total_jobs']}
- **Active jobs:** {snapshot.get('active_jobs', 'N/A')}
- **New unique jobs:** {snapshot['new_jobs']}
- **Total unique jobs tracked:** {trends.get('total_unique_jobs', 0)}
- **Total weekly snapshots:** {trends.get('total_snapshots', 0)}

## New Jobs This Week ({len(new_jobs)} total)
"""
        if new_jobs:
            for job in new_jobs[:15]:  # Show first 15
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
        
        # Add trends
        if trends.get('top_aos'):
            report += "\n## Top Areas of Specialization (All Time)\n"
            report += "| Rank | Area | Jobs |\n"
            report += "|------|------|------|\n"
            for i, (area, count) in enumerate(trends['top_aos'][:15], 1):
                report += f"| {i} | {area} | {count} |\n"
        
        if trends.get('top_aoc'):
            report += "\n## Top Areas of Competence (All Time)\n"
            report += "| Rank | Area | Jobs |\n"
            report += "|------|------|------|\n"
            for i, (area, count) in enumerate(trends['top_aoc'][:15], 1):
                report += f"| {i} | {area} | {count} |\n"
        
        if trends.get('top_categories'):
            report += "\n## Job Types (All Time)\n"
            for category, count in trends['top_categories']:
                report += f"- {category}: {count} jobs\n"
        
        if trends.get('top_locations'):
            report += "\n## Top Locations (All Time)\n"
            for i, (location, count) in enumerate(trends['top_locations'][:10], 1):
                report += f"{i}. {location}: {count} jobs\n"
        
        # Save report
        report_file = self.data_dir / f"report_{snapshot['date']}.md"
        with open(report_file, 'w') as f:
            f.write(report)
        
        print("\n" + "="*70)
        print(report)
        print("="*70)
        return report

def main():
    scraper = PhilJobsScraper()
    
    print("Starting PhilJobs scraper with full detail collection...")
    print("="*70)
    
    jobs = scraper.scrape_jobs()
    
    print("\nLoading historical data...")
    historical_data = scraper.load_historical_data()
    
    print("Saving data and identifying new jobs...")
    new_jobs, snapshot = scraper.save_data(jobs, historical_data)
    print(f"Identified {len(new_jobs)} new unique jobs")
    
    print("\nAnalyzing trends...")
    trends = scraper.analyze_trends(historical_data)
    
    print("\nGenerating report...")
    scraper.generate_report(new_jobs, snapshot, trends)
    
    print(f"\n✓ Done! Data saved to {scraper.data_dir}/")
    print(f"  - all_jobs.json: {len(historical_data['jobs'])} unique jobs")
    print(f"  - snapshot_{snapshot['date']}.json: This week's data")
    print(f"  - report_{snapshot['date']}.md: Human-readable report")

if __name__ == "__main__":
    main()

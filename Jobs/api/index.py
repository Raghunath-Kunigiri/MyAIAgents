import sys
import os

# Add Job_Scrapper directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
jobs_dir = os.path.dirname(current_dir)
job_scrapper_dir = os.path.join(jobs_dir, 'Job_Scrapper')
sys.path.insert(0, job_scrapper_dir)

from jobs_viewer_app import app

# Export the Flask app for Vercel
# Vercel will automatically detect this as a serverless function
handler = app


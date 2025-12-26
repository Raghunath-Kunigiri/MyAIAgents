import sys
import os

# Initialize variables for error handling
current_dir = None
jobs_dir = None
job_scrapper_dir = None

try:
    # Add Job_Scrapper directory to path for imports
    # In Vercel, the api/ directory is the function root
    current_dir = os.path.dirname(os.path.abspath(__file__))
    jobs_dir = os.path.dirname(current_dir)
    job_scrapper_dir = os.path.join(jobs_dir, 'Job_Scrapper')
    
    # Try alternative paths for different deployment scenarios
    alternative_paths = [
        job_scrapper_dir,
        os.path.join(current_dir, '..', 'Job_Scrapper'),
        os.path.join(os.getcwd(), 'Job_Scrapper'),
        os.path.join('/vercel/path0', 'Job_Scrapper'),  # Vercel build path
    ]
    
    found_path = None
    for path in alternative_paths:
        abs_path = os.path.abspath(path)
        if os.path.exists(abs_path) and os.path.exists(os.path.join(abs_path, 'jobs_viewer_app.py')):
            found_path = abs_path
            sys.path.insert(0, abs_path)
            break
    
    if not found_path:
        # Try adding the parent directory to path and import directly
        sys.path.insert(0, jobs_dir)
        sys.path.insert(0, os.path.join(jobs_dir, 'Job_Scrapper'))
        # Also try Vercel's build output path
        sys.path.insert(0, '/vercel/path0')
        sys.path.insert(0, '/vercel/path0/Job_Scrapper')
    
    from jobs_viewer_app import app
    
    # Export the Flask app for Vercel
    # Vercel will automatically detect this as a serverless function
    handler = app
    
except Exception as e:
    import traceback
    # Create a minimal Flask app to show the error
    from flask import Flask
    
    error_app = Flask(__name__)
    
    error_traceback = traceback.format_exc()
    
    @error_app.route('/', defaults={'path': ''})
    @error_app.route('/<path:path>')
    def error_handler(path):
        error_msg = f"""
        <!DOCTYPE html>
        <html>
        <head><title>Serverless Function Error</title></head>
        <body>
        <h1>Serverless Function Error</h1>
        <p><strong>Error:</strong> {str(e)}</p>
        <p><strong>Type:</strong> {type(e).__name__}</p>
        <h3>Traceback:</h3>
        <pre>{error_traceback}</pre>
        <hr>
        <h3>Debug Info:</h3>
        <ul>
            <li>Current dir: {current_dir or 'Not set'}</li>
            <li>Jobs dir: {jobs_dir or 'Not set'}</li>
            <li>Job Scrapper dir: {job_scrapper_dir or 'Not set'}</li>
            <li>Python path: {sys.path}</li>
            <li>Working directory: {os.getcwd()}</li>
        </ul>
        <p>Please check the function logs for more details.</p>
        </body>
        </html>
        """
        return error_msg, 500
    
    handler = error_app


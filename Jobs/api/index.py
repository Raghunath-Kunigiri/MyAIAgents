import sys
import os

# Initialize variables for error handling
current_dir = None
jobs_dir = None
job_scrapper_dir = None
error_details = []

def get_error_app(error, traceback_str, debug_info):
    """Create a Flask app that shows the error"""
    try:
        from flask import Flask
        error_app = Flask(__name__)
        
        @error_app.route('/', defaults={'path': ''})
        @error_app.route('/<path:path>')
        def error_handler(path):
            error_msg = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Serverless Function Error</title>
                <style>
                    body {{ font-family: Arial, sans-serif; padding: 20px; background: #f5f5f5; }}
                    .container {{ background: white; padding: 20px; border-radius: 8px; max-width: 1200px; margin: 0 auto; }}
                    pre {{ background: #f4f4f4; padding: 15px; overflow-x: auto; border-radius: 4px; }}
                    ul {{ line-height: 1.8; }}
                    h1 {{ color: #d32f2f; }}
                </style>
            </head>
            <body>
            <div class="container">
                <h1>Serverless Function Error</h1>
                <p><strong>Error:</strong> {str(error)}</p>
                <p><strong>Type:</strong> {type(error).__name__}</p>
                <h3>Traceback:</h3>
                <pre>{traceback_str}</pre>
                <hr>
                <h3>Debug Info:</h3>
                <ul>
                    {debug_info}
                </ul>
                <p>Please check the function logs in Vercel dashboard for more details.</p>
            </div>
            </body>
            </html>
            """
            return error_msg, 500
        
        return error_app
    except Exception as flask_error:
        # If Flask itself can't be imported, return a simple handler
        def simple_handler(environ, start_response):
            status = '500 Internal Server Error'
            headers = [('Content-Type', 'text/html')]
            body = f"""
            <html><body>
            <h1>Critical Error</h1>
            <p>Original error: {str(error)}</p>
            <p>Flask import error: {str(flask_error)}</p>
            <p>This means Flask is not installed or not accessible.</p>
            </body></html>
            """
            start_response(status, headers)
            return [body.encode()]
        
        return simple_handler

try:
    # Add Job_Scrapper directory to path for imports
    # In Vercel, the api/ directory is the function root
    current_dir = os.path.dirname(os.path.abspath(__file__))
    jobs_dir = os.path.dirname(current_dir)
    job_scrapper_dir = os.path.join(jobs_dir, 'Job_Scrapper')
    
    error_details.append(f"<li>Current dir: {current_dir}</li>")
    error_details.append(f"<li>Jobs dir: {jobs_dir}</li>")
    error_details.append(f"<li>Job Scrapper dir: {job_scrapper_dir}</li>")
    error_details.append(f"<li>Working directory: {os.getcwd()}</li>")
    
    # List what's in the current directory
    try:
        current_files = os.listdir(current_dir)
        error_details.append(f"<li>Files in api/: {', '.join(current_files)}</li>")
    except:
        error_details.append(f"<li>Could not list api/ directory</li>")
    
    # List what's in jobs_dir
    try:
        if os.path.exists(jobs_dir):
            jobs_files = os.listdir(jobs_dir)
            error_details.append(f"<li>Files in Jobs/: {', '.join(jobs_files)}</li>")
        else:
            error_details.append(f"<li>Jobs directory does not exist: {jobs_dir}</li>")
    except Exception as e:
        error_details.append(f"<li>Could not list Jobs/ directory: {str(e)}</li>")
    
    # Try alternative paths for different deployment scenarios
    alternative_paths = [
        job_scrapper_dir,
        os.path.join(current_dir, '..', 'Job_Scrapper'),
        os.path.join(os.getcwd(), 'Job_Scrapper'),
        os.path.join('/vercel/path0', 'Job_Scrapper'),
        os.path.join('/var/task', 'Job_Scrapper'),  # AWS Lambda style (Vercel might use similar)
    ]
    
    found_path = None
    checked_paths = []
    for path in alternative_paths:
        abs_path = os.path.abspath(path)
        checked_paths.append(abs_path)
        if os.path.exists(abs_path):
            error_details.append(f"<li>Path exists: {abs_path}</li>")
            if os.path.exists(os.path.join(abs_path, 'jobs_viewer_app.py')):
                found_path = abs_path
                sys.path.insert(0, abs_path)
                error_details.append(f"<li>✅ Found jobs_viewer_app.py at: {abs_path}</li>")
                break
            else:
                error_details.append(f"<li>Path exists but jobs_viewer_app.py not found: {abs_path}</li>")
        else:
            error_details.append(f"<li>Path does not exist: {abs_path}</li>")
    
    if not found_path:
        # Try adding the parent directory to path and import directly
        sys.path.insert(0, jobs_dir)
        sys.path.insert(0, os.path.join(jobs_dir, 'Job_Scrapper'))
        # Also try Vercel's build output path
        sys.path.insert(0, '/vercel/path0')
        sys.path.insert(0, '/vercel/path0/Job_Scrapper')
        error_details.append(f"<li>Added to sys.path: {jobs_dir}, {os.path.join(jobs_dir, 'Job_Scrapper')}</li>")
    
    error_details.append(f"<li>Python sys.path: {sys.path}</li>")
    
    from jobs_viewer_app import app
    
    # Export the Flask app for Vercel
    # Vercel will automatically detect this as a serverless function
    handler = app
    
except Exception as e:
    import traceback
    error_traceback = traceback.format_exc()
    
    error_details_html = '\n'.join(error_details) if error_details else '<li>No debug info collected</li>'
    
    handler = get_error_app(e, error_traceback, error_details_html)


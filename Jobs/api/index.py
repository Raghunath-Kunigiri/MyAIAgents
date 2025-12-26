# Ensure handler is always defined, even if imports fail
handler = None

def create_error_handler(error_msg, error_type="Unknown", traceback_str="", debug_info=""):
    """Create a WSGI-compatible error handler"""
    def wsgi_handler(environ, start_response):
        status = '500 Internal Server Error'
        headers = [('Content-Type', 'text/html; charset=utf-8')]
        
        html_body = f"""<!DOCTYPE html>
<html>
<head>
    <title>Serverless Function Error</title>
    <style>
        body {{ font-family: Arial, sans-serif; padding: 20px; background: #f5f5f5; }}
        .container {{ background: white; padding: 20px; border-radius: 8px; max-width: 1200px; margin: 0 auto; }}
        pre {{ background: #f4f4f4; padding: 15px; overflow-x: auto; border-radius: 4px; font-size: 12px; }}
        ul {{ line-height: 1.8; }}
        h1 {{ color: #d32f2f; }}
        code {{ background: #f4f4f4; padding: 2px 4px; border-radius: 2px; }}
    </style>
</head>
<body>
<div class="container">
    <h1>Serverless Function Error</h1>
    <p><strong>Error:</strong> <code>{error_msg}</code></p>
    <p><strong>Type:</strong> <code>{error_type}</code></p>
    {f'<h3>Traceback:</h3><pre>{traceback_str}</pre><hr>' if traceback_str else ''}
    {f'<h3>Debug Info:</h3><ul>{debug_info}</ul>' if debug_info else ''}
    <p><em>Please check the function logs in Vercel dashboard for more details.</em></p>
</div>
</body>
</html>"""
        
        start_response(status, headers)
        return [html_body.encode('utf-8')]
    
    return wsgi_handler

# Initialize error tracking
error_details = []
import_error = None

try:
    import sys
    import os
    import traceback
    
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
    except Exception as e:
        error_details.append(f"<li>Could not list api/ directory: {str(e)}</li>")
    
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
        os.path.join('/var/task', 'Job_Scrapper'),
    ]
    
    found_path = None
    for path in alternative_paths:
        abs_path = os.path.abspath(path)
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
        sys.path.insert(0, '/vercel/path0')
        sys.path.insert(0, '/vercel/path0/Job_Scrapper')
        error_details.append(f"<li>Added to sys.path: {jobs_dir}, {os.path.join(jobs_dir, 'Job_Scrapper')}</li>")
    
    error_details.append(f"<li>Python sys.path: {', '.join(sys.path[:10])}...</li>")
    
    # Try to import the Flask app
    from jobs_viewer_app import app
    
    # Export the Flask app for Vercel
    handler = app
    
except Exception as e:
    import_error = e
    error_traceback = traceback.format_exc() if 'traceback' in dir() else str(e)
    error_details_html = '\n'.join(error_details) if error_details else '<li>No debug info collected</li>'
    
    handler = create_error_handler(
        str(e),
        type(e).__name__,
        error_traceback,
        error_details_html
    )

# Fallback: if handler is still None, create a basic error handler
if handler is None:
    handler = create_error_handler(
        "Handler initialization failed completely",
        "UnknownError",
        "",
        "<li>Could not initialize handler. Check Vercel logs.</li>"
    )


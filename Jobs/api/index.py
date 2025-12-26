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
    
    # In Vercel, the api/ directory is the function root
    # We've copied jobs_viewer_app.py into the api/ directory for direct import
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    error_details.append(f"<li>Current dir (api/): {current_dir}</li>")
    error_details.append(f"<li>Working directory: {os.getcwd()}</li>")
    
    # List what's in the current directory
    try:
        current_files = os.listdir(current_dir)
        error_details.append(f"<li>Files in api/: {', '.join(current_files)}</li>")
        
        # Check if jobs_viewer_app.py exists in the same directory
        if 'jobs_viewer_app.py' in current_files:
            error_details.append(f"<li>✅ Found jobs_viewer_app.py in api/ directory</li>")
        else:
            error_details.append(f"<li>❌ jobs_viewer_app.py NOT found in api/ directory</li>")
    except Exception as e:
        error_details.append(f"<li>Could not list api/ directory: {str(e)}</li>")
    
    # Import the Flask app directly from the same directory
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


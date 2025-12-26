# Vercel Python Serverless Function
# Import the Flask app directly from the same directory

try:
    from jobs_viewer_app import app
    handler = app
except Exception as e:
    # Fallback error handler if import fails
    import traceback
    
    def error_handler(environ, start_response):
        status = '500 Internal Server Error'
        headers = [('Content-Type', 'text/html; charset=utf-8')]
        error_msg = f"""
        <!DOCTYPE html>
        <html>
        <head><title>Import Error</title></head>
        <body>
        <h1>Failed to import Flask app</h1>
        <p><strong>Error:</strong> {str(e)}</p>
        <p><strong>Type:</strong> {type(e).__name__}</p>
        <pre>{traceback.format_exc()}</pre>
        </body>
        </html>
        """
        start_response(status, headers)
        return [error_msg.encode('utf-8')]
    
    handler = error_handler

# Vercel Python Serverless Function
# Import Flask app and export as handler

from jobs_viewer_app import app

# Export the Flask app as the handler
# Vercel's Python runtime should recognize Flask apps as WSGI applications
handler = app

# Ensure handler is callable (WSGI requirement)
if not callable(handler):
    raise TypeError("Handler must be callable")

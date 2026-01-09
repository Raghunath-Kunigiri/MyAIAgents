import os
from flask import Flask, redirect, url_for, flash
from flask_login import LoginManager, current_user
from pymongo import MongoClient
import gridfs

# MongoDB Configuration - supports environment variables for cloud deployment
MONGODB_CONFIG = {
    "connection_string": os.environ.get(
        "MONGODB_CONNECTION_STRING",
        "mongodb+srv://kunigiriraghunath9493:Kunimongo1998@cluster0.ckryr.mongodb.net/"
    ),
    "database_name": os.environ.get("MONGODB_DATABASE_NAME", "N8N"),
    "collection_name": os.environ.get("MONGODB_COLLECTION_NAME", "Jobs_Collection")
}

login_manager = LoginManager()
login_manager.login_view = 'auth.login'

def get_db():
    """Get MongoDB database connection with error handling"""
    try:
        client = MongoClient(
            MONGODB_CONFIG["connection_string"],
            serverSelectionTimeoutMS=5000,  # 5 second timeout
            connectTimeoutMS=5000
        )
        # Test connection
        client.admin.command('ping')
        db = client[MONGODB_CONFIG["database_name"]]
        return client, db
    except Exception as e:
        import traceback
        print(f"[ERROR] MongoDB connection failed: {e}")
        if os.environ.get("FLASK_DEBUG") == "1":
            traceback.print_exc()
        raise

def create_app():
    app = Flask(__name__, template_folder='../templates')
    app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-professional")
    
    # Enable CORS for React frontend
    @app.after_request
    def after_request(response):
        from flask import request
        # Allow origin from environment variable or use request origin
        allowed_origin = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
        origin = request.headers.get('Origin')
        
        # If FRONTEND_URL is '*', allow all origins (use with caution)
        if allowed_origin == '*':
            if origin:
                response.headers.add('Access-Control-Allow-Origin', origin)
        # If specific FRONTEND_URL is set, use it
        elif allowed_origin:
            response.headers.add('Access-Control-Allow-Origin', allowed_origin)
        # Fallback to request origin for same-domain deployments
        elif origin:
            response.headers.add('Access-Control-Allow-Origin', origin)
        # Default to localhost for local development
        else:
            response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
        
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
    
    # Initialize Login Manager
    login_manager.init_app(app)
    
    # Handle unauthorized API requests with JSON response instead of redirect
    @login_manager.unauthorized_handler
    def handle_needs_login():
        from flask import request, jsonify
        # If it's an API request, return JSON error
        if request.path.startswith('/api'):
            return jsonify({
                "success": False,
                "error": "Authentication required",
                "redirect": "/login"
            }), 401
        # Otherwise, redirect to login page
        return redirect(url_for('auth.login'))
    
    from webapp.models import User
    
    @login_manager.user_loader
    def load_user(user_id):
        client, db = get_db()
        user = User.get_by_id(db, user_id)
        client.close()
        return user

    # Custom Session Protection (Single Session Enforcement)
    @app.before_request
    def check_session_token():
        if current_user.is_authenticated:
            client, db = get_db()
            user = User.get_by_id(db, current_user.id)
            client.close()
            
            # If the session token in the DB doesn't match the current user's session token
            # (which we store in the session), log them out.
            # Flask-Login stores the user object in current_user.
            # We need to store the expected token in the session during login.
            from flask import session
            if not user or user.session_token != session.get('session_token'):
                from flask_login import logout_user
                logout_user()
                flash("Your account was logged in from another location.")
                return redirect(url_for('auth.login'))

    # Register Blueprints
    from webapp.auth.routes import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    from webapp.jobs.routes import jobs as jobs_blueprint
    app.register_blueprint(jobs_blueprint)

    return app

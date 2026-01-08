import os
from flask import Flask, redirect, url_for, flash
from flask_login import LoginManager, current_user
from pymongo import MongoClient
import gridfs

# MongoDB Configuration from jobs_viewer_app.py
MONGODB_CONFIG = {
    "connection_string": "mongodb+srv://kunigiriraghunath9493:Kunimongo1998@cluster0.ckryr.mongodb.net/",
    "database_name": "N8N",
    "collection_name": "Jobs_Collection"
}

login_manager = LoginManager()
login_manager.login_view = 'auth.login'

def get_db():
    client = MongoClient(MONGODB_CONFIG["connection_string"])
    db = client[MONGODB_CONFIG["database_name"]]
    return client, db

def create_app():
    app = Flask(__name__, template_folder='../templates')
    app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-professional")
    
    # Initialize Login Manager
    login_manager.init_app(app)

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

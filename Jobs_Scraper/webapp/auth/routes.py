from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from webapp.models import User
from webapp import get_db
from email_validator import validate_email, EmailNotValidError
import os

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    # If user is authenticated, check if request is from frontend
    if current_user.is_authenticated:
        # Check if request came from frontend (via proxy)
        # When Vite proxies /login, it sets Host to localhost:5000, but we can check Referer
        referer = request.headers.get('Referer', '')
        origin = request.headers.get('Origin', '')
        host = request.headers.get('Host', '')
        x_forwarded_host = request.headers.get('X-Forwarded-Host', '')
        
        # If request is from frontend (via Vite proxy on port 3000), don't redirect
        # Instead, return a simple HTML page that redirects via JavaScript
        # This prevents the redirect loop: login -> dashboard -> frontend -> login
        # Note: When proxied, Host will be localhost:5000, but Referer/Origin will have localhost:3000
        is_frontend_request = (
            'localhost:3000' in referer or 
            origin.startswith('http://localhost:3000') or
            'localhost:3000' in x_forwarded_host or
            request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        )
        
        if is_frontend_request:
            # Frontend request - don't redirect, just return 200 OK
            # The frontend will handle staying on the dashboard
            # This prevents the redirect loop: login -> dashboard -> frontend -> login
            frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
            print(f"[LOGIN] Authenticated user from frontend (referer={referer}, origin={origin}, x-forwarded-host={x_forwarded_host}) - returning 200 OK (no redirect)")
            # Return a simple response that tells the frontend the user is authenticated
            # The frontend will handle the redirect logic
            return jsonify({
                "success": True,
                "authenticated": True,
                "redirect": frontend_url
            }), 200
        
        # For direct backend access, redirect to dashboard
        print(f"[LOGIN] Authenticated user from backend (host={host}) - redirecting to dashboard")
        return redirect(url_for('jobs.dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()  # Normalize email: trim and lowercase
        password = request.form.get('password', '')
        
        if not email or not password:
            flash("Please provide both email and password", "danger")
            return render_template('auth/login.html')
        
        client, db = get_db()
        # Try to find user with case-insensitive email
        user = User.get_by_email(db, email)
        
        # If not found with exact match, try case-insensitive search
        if not user:
            # MongoDB case-insensitive search using regex
            user_doc = db['Users'].find_one({"email": {"$regex": f"^{email}$", "$options": "i"}})
            if user_doc:
                user = User(user_doc)
        
        # Debug logging (only in debug mode to avoid security issues)
        if current_app.debug:
            print(f"[LOGIN DEBUG] Email submitted: {email}")
            print(f"[LOGIN DEBUG] User found: {user is not None}")
            if user:
                print(f"[LOGIN DEBUG] User email in DB: {user.email}")
                password_match = check_password_hash(user.password_hash, password)
                print(f"[LOGIN DEBUG] Password matches: {password_match}")
        
        if user and check_password_hash(user.password_hash, password):
            # Enforce single session: update token in DB
            new_token = user.update_session_token(db)
            # Store token in Flask session for validation in before_request
            session['session_token'] = new_token
            login_user(user)
            client.close()
            
            # Check if request is from frontend (via proxy) or direct backend access
            # If it's an AJAX request or has X-Requested-With header, return JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
                return jsonify({
                    "success": True,
                    "redirect": os.environ.get('FRONTEND_URL', 'http://localhost:3000')
                }), 200
            
            # Check if request came from frontend origin
            referer = request.headers.get('Referer', '')
            if 'localhost:3000' in referer or request.headers.get('Origin', '').startswith('http://localhost:3000'):
                # Redirect to frontend
                frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
                return redirect(frontend_url)
            
            # Default: redirect to backend dashboard (which will redirect to frontend)
            return redirect(url_for('jobs.dashboard'))
        
        client.close()
        flash("Invalid email or password. Please check your credentials and try again.", "danger")
        return render_template('auth/login.html')
        
    return render_template('auth/login.html')

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('jobs.dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()  # Normalize email: trim and lowercase
        password = request.form.get('password', '')
        name = request.form.get('name', '').strip()
        
        if not email or not password or not name:
            flash("Please fill in all fields", "danger")
            return render_template('auth/register.html')
        
        try:
            validate_email(email)
        except EmailNotValidError:
            flash("Invalid email address", "danger")
            return render_template('auth/register.html')
            
        if len(password) < 6:
            flash("Password must be at least 6 characters", "danger")
            return render_template('auth/register.html')
            
        client, db = get_db()
        if User.get_by_email(db, email):
            client.close()
            flash("Email already exists", "danger")
            return render_template('auth/register.html')
            
        password_hash = generate_password_hash(password)
        user = User.create_user(db, email, password_hash, name)
        
        # Log in the new user
        session['session_token'] = user.session_token
        login_user(user)
        client.close()
        
        flash("Account created successfully!", "success")
        return redirect(url_for('jobs.dashboard'))
        
    return render_template('auth/register.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    session.pop('session_token', None)
    return redirect(url_for('auth.login'))

@auth.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        n8n_url = request.form.get('n8n_webhook_url')
        n8n_key = request.form.get('n8n_api_key')
        
        client, db = get_db()
        current_user.update_profile(db, name, email, n8n_url, n8n_key)
        client.close()
        
        flash("Profile updated successfully!", "success")
        return redirect(url_for('auth.profile'))
        
    return render_template('auth/profile.html')

@auth.route('/reset-password', methods=['GET', 'POST'])
@login_required
def reset_password():
    if request.method == 'POST':
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')
        
        if not check_password_hash(current_user.password_hash, old_password):
            flash("Incorrect current password", "danger")
            return render_template('auth/profile.html')
            
        if len(new_password) < 6:
            flash("New password must be at least 6 characters", "danger")
            return render_template('auth/profile.html')
            
        client, db = get_db()
        new_password_hash = generate_password_hash(new_password)
        current_user.update_password(db, new_password_hash)
        client.close()
        
        flash("Password updated successfully!", "success")
        return redirect(url_for('auth.profile'))
        
    return render_template('auth/profile.html')

from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from webapp.models import User
from webapp import get_db
from email_validator import validate_email, EmailNotValidError

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('jobs.dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        client, db = get_db()
        user = User.get_by_email(db, email)
        
        if user and check_password_hash(user.password_hash, password):
            # Enforce single session: update token in DB
            new_token = user.update_session_token(db)
            # Store token in Flask session for validation in before_request
            session['session_token'] = new_token
            login_user(user)
            client.close()
            return redirect(url_for('jobs.dashboard'))
        
        client.close()
        flash("Invalid email or password", "danger")
        return render_template('auth/login.html')
        
    return render_template('auth/login.html')

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('jobs.dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        name = request.form.get('name')
        
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

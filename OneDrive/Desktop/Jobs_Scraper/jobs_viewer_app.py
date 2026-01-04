#!/usr/bin/env python3
"""
Flask Web Application to Display Job Details from MongoDB
Shows all jobs from the N8N/N8n_Jobs collection
"""

import os
import sys

# Set encoding to utf-8 to avoid UnicodeEncodeError on Windows consoles
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass
from flask import Flask, render_template_string, jsonify
from flask.json.provider import DefaultJSONProvider
from functools import wraps
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
from bson import ObjectId
import json
from datetime import datetime, timedelta
from typing import Any
import requests
import gridfs
import io
import mimetypes
from flask import send_file, request, redirect, url_for, flash, make_response
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from email_validator import validate_email, EmailNotValidError


# MongoDB Configuration
# Update these values to match your MongoDB setup
# NOTE: If connection fails, check that:
#   1. Your IP is whitelisted in MongoDB Atlas (Network Access)
#   2. The password matches your MongoDB Atlas database user password
#   3. Try running: python test_mongodb_connection.py to verify connection
MONGODB_CONFIG = {
    # IMPORTANT: Use your MongoDB Atlas connection string
    # Get it from: MongoDB Atlas → Connect → Connect your application
    "connection_string": "mongodb+srv://kunigiriraghunath9493:Kunimongo1998@cluster0.ckryr.mongodb.net/",
    # Using N8N database with Jobs_Collection collection
    "database_name": "N8N",  # N8N database
    "collection_name": "Jobs_Collection"  # Jobs_Collection collection in N8N database
}

app = Flask(__name__)

# Configure Flask to use our error handlers even in debug mode
# This ensures API endpoints always return JSON, not HTML error pages
app.config['PROPAGATE_EXCEPTIONS'] = False

# Convert MongoDB ObjectId to string for JSON serialization (Flask 2.2+ compatible)
class CustomJSONProvider(DefaultJSONProvider):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

app.json = CustomJSONProvider(app)
app.secret_key = "dev-secret-key-change-in-prod"  # Static key for stability

# Flask-Login Configuration
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User Model
class User(UserMixin):
    def __init__(self, user_doc):
        self.id = str(user_doc['_id'])
        self.email = user_doc['email']
        self.password_hash = user_doc['password_hash']
        self.name = user_doc.get('name', 'User')

@login_manager.user_loader
def load_user(user_id):
    # print(f"DEBUG: load_user called with {user_id}")
    client, db, collection, fs, error = get_db_connection()
    if not client: 
        print("DEBUG: load_user - No DB connection")
        return None
    
    try:
        users_collection = db['Users']
        user_doc = users_collection.find_one({"_id": ObjectId(user_id)})
        if user_doc:
            return User(user_doc)
        print(f"DEBUG: load_user - User {user_id} not found")
        return None
    except Exception as e:
        print(f"DEBUG: load_user exception: {e}")
        return None


# HTML Template - defined here before route handlers
HTML_TEMPLATE = r'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Job Details Viewer - N8N Jobs</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary: #2563eb;
            --primary-dark: #1d4ed8;
            --primary-light: #3b82f6;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
            --info: #06b6d4;
            --bg-primary: #f8fafc;
            --bg-secondary: #ffffff;
            --text-primary: #1e293b;
            --text-secondary: #64748b;
            --text-muted: #94a3b8;
            --border: #e2e8f0;
            --border-light: #f1f5f9;
            --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
            --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
            --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.6;
            min-height: 100vh;
            padding: 24px;
        }
        
        .container {
            max-width: 1600px;
            margin: 0 auto;
            background: var(--bg-secondary);
            border-radius: 16px;
            box-shadow: var(--shadow-xl);
            overflow: hidden;
        }
        
        header {
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            color: white;
            padding: 32px 40px;
            margin-bottom: 0;
        }
        
        h1 {
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 8px;
            letter-spacing: -0.5px;
        }
        
        .subtitle {
            color: rgba(255, 255, 255, 0.9);
            font-size: 15px;
            font-weight: 400;
        }
        
        .content-wrapper {
            padding: 32px 40px;
        }
        
        .stats-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 24px;
            margin-bottom: 32px;
        }
        
        .stat-card {
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 24px;
            transition: all 0.3s ease;
            box-shadow: var(--shadow-sm);
            position: relative;
            overflow: hidden;
        }
        
        .stat-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 4px;
            height: 100%;
            background: var(--primary);
        }
        
        .stat-card:nth-child(1)::before { background: var(--primary); }
        .stat-card:nth-child(2)::before { background: var(--success); }
        .stat-card:nth-child(3)::before { background: var(--info); }
        .stat-card:nth-child(4)::before { background: var(--warning); }
        
        .stat-card:hover {
            transform: translateY(-4px);
            box-shadow: var(--shadow-md);
            border-color: var(--primary-light);
        }
        
        .stat-card-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 16px;
        }
        
        .stat-card h3 {
            font-size: 13px;
            font-weight: 600;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .stat-card-icon {
            width: 40px;
            height: 40px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            background: var(--bg-primary);
        }
        
        .stat-card:nth-child(1) .stat-card-icon { background: rgba(37, 99, 235, 0.1); }
        .stat-card:nth-child(2) .stat-card-icon { background: rgba(16, 185, 129, 0.1); }
        .stat-card:nth-child(3) .stat-card-icon { background: rgba(6, 182, 212, 0.1); }
        .stat-card:nth-child(4) .stat-card-icon { background: rgba(245, 158, 11, 0.1); }
        
        .stat-card .number {
            font-size: 32px;
            font-weight: 700;
            color: var(--text-primary);
            line-height: 1.2;
        }
        
        .controls-section {
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 24px;
        }
        
        .controls {
            display: flex;
            gap: 16px;
            flex-wrap: wrap;
            align-items: center;
        }
        
        .search-wrapper {
            flex: 1;
            min-width: 280px;
            position: relative;
        }
        
        .search-box {
            width: 100%;
            padding: 14px 16px 14px 48px;
            border: 1.5px solid var(--border);
            border-radius: 10px;
            font-size: 14px;
            font-weight: 400;
            background: var(--bg-secondary);
            color: var(--text-primary);
            transition: all 0.2s ease;
        }
        
        .search-box::placeholder {
            color: var(--text-muted);
        }
        
        .search-box:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
        }
        
        .search-icon {
            position: absolute;
            left: 16px;
            top: 50%;
            transform: translateY(-50%);
            color: var(--text-muted);
            font-size: 18px;
        }
        
        .filter-group {
            display: flex;
            gap: 12px;
            align-items: center;
            flex-wrap: wrap;
        }
        
        select {
            padding: 14px 16px;
            border: 1.5px solid var(--border);
            border-radius: 10px;
            font-size: 14px;
            font-weight: 500;
            background: var(--bg-secondary);
            color: var(--text-primary);
            cursor: pointer;
            transition: all 0.2s ease;
            appearance: none;
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%2364748b' d='M6 9L1 4h10z'/%3E%3C/svg%3E");
            background-repeat: no-repeat;
            background-position: right 12px center;
            padding-right: 40px;
        }
        
        select:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
        }
        
        select:hover {
            border-color: var(--primary-light);
        }
        
        .date-input {
            padding: 14px 16px;
            border: 1.5px solid var(--border);
            border-radius: 10px;
            font-size: 14px;
            font-weight: 500;
            background: var(--bg-secondary);
            color: var(--text-primary);
            cursor: pointer;
            transition: all 0.2s ease;
        }
        
        .date-input:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
        }
        
        .refresh-btn {
            padding: 14px 24px;
            background: var(--primary);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .refresh-btn:hover {
            background: var(--primary-dark);
            transform: translateY(-2px);
            box-shadow: var(--shadow-md);
        }
        
        .refresh-btn:active {
            transform: translateY(0);
        }
        
        .loading {
            text-align: center;
            padding: 80px 20px;
            color: var(--text-secondary);
        }
        
        .spinner {
            border: 4px solid var(--border-light);
            border-top: 4px solid var(--primary);
            border-radius: 50%;
            width: 48px;
            height: 48px;
            animation: spin 0.8s linear infinite;
            margin: 0 auto 24px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .loading p {
            font-size: 15px;
            font-weight: 500;
            color: var(--text-secondary);
        }
        
        .error {
            background: #fef2f2;
            color: #991b1b;
            padding: 16px 20px;
            border-radius: 10px;
            border: 1px solid #fecaca;
            margin-bottom: 24px;
            font-size: 14px;
            line-height: 1.6;
        }
        
        .error strong {
            font-weight: 600;
        }
        
        .duplicate-warning {
            background: #fef3c7;
            border: 1.5px solid #f59e0b;
            border-radius: 12px;
            padding: 20px 24px;
            margin-bottom: 24px;
            box-shadow: var(--shadow-sm);
        }
        
        .duplicate-warning-content {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 24px;
            flex-wrap: wrap;
        }
        
        .duplicate-warning-content > div {
            flex: 1;
            min-width: 250px;
        }
        
        .duplicate-warning strong {
            display: block;
            font-size: 16px;
            font-weight: 600;
            color: #92400e;
            margin-bottom: 8px;
        }
        
        .duplicate-warning p {
            font-size: 14px;
            color: #78350f;
            margin: 0;
            line-height: 1.5;
        }
        
        .duplicate-warning #duplicateCount {
            font-weight: 700;
            color: #b45309;
        }
        
        .cleanup-btn {
            padding: 14px 28px;
            background: var(--warning);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            gap: 8px;
            white-space: nowrap;
        }
        
        .cleanup-btn:hover {
            background: #d97706;
            transform: translateY(-2px);
            box-shadow: var(--shadow-md);
        }
        
        .cleanup-btn:active {
            transform: translateY(0);
        }
        
        .cleanup-btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        .table-wrapper {
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 12px;
            overflow: hidden;
            box-shadow: var(--shadow-sm);
        }
        
        .table-container {
            overflow-x: auto;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            background: var(--bg-secondary);
        }
        
        thead {
            background: var(--bg-primary);
            border-bottom: 2px solid var(--border);
        }
        
        th {
            padding: 16px 20px;
            text-align: left;
            font-weight: 600;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: var(--text-secondary);
            white-space: nowrap;
        }
        
        td {
            padding: 20px;
            border-bottom: 1px solid var(--border-light);
            font-size: 14px;
            color: var(--text-primary);
            vertical-align: middle;
        }
        
        tbody tr {
            transition: all 0.2s ease;
        }
        
        tbody tr:hover {
            background: var(--bg-primary);
        }
        
        tbody tr:last-child td {
            border-bottom: none;
        }
        
        .status-badge {
            display: inline-flex;
            align-items: center;
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 600;
            text-transform: capitalize;
            white-space: nowrap;
        }
        
        .status-new {
            background: #dcfce7;
            color: #166534;
        }
        
        .status-applied {
            background: #dbeafe;
            color: #1e40af;
        }
        
        .status-interview {
            background: #fef3c7;
            color: #92400e;
        }
        
        .status-rejected {
            background: #fee2e2;
            color: #991b1b;
        }
        
        .status-yes {
            background: #d1fae5;
            color: #065f46;
        }
        
        .status-no {
            background: #fee2e2;
            color: #991b1b;
        }
        
        .job-url {
            color: var(--primary);
            text-decoration: none;
            font-weight: 500;
            display: inline-flex;
            align-items: center;
            gap: 4px;
            transition: color 0.2s ease;
        }
        
        .job-url:hover {
            color: var(--primary-dark);
            text-decoration: underline;
        }
        
        .no-data {
            text-align: center;
            padding: 80px 20px;
            color: var(--text-secondary);
        }
        
        .no-data-icon {
            font-size: 72px;
            margin-bottom: 24px;
            opacity: 0.4;
        }
        
        .no-data h2 {
            font-size: 20px;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 8px;
        }
        
        .no-data p {
            font-size: 14px;
            color: var(--text-secondary);
        }
        
        .pagination {
            display: flex;
            justify-content: center;
            gap: 12px;
            margin-top: 32px;
            align-items: center;
            flex-wrap: wrap;
        }
        
        .pagination button {
            padding: 12px 20px;
            border: 1.5px solid var(--border);
            background: var(--bg-secondary);
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            color: var(--text-primary);
            transition: all 0.2s ease;
        }
        
        .pagination button:hover:not(:disabled) {
            border-color: var(--primary);
            color: var(--primary);
            background: rgba(37, 99, 235, 0.05);
        }
        
        .pagination button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        .pagination .current-page {
            padding: 12px 24px;
            font-weight: 600;
            color: var(--text-primary);
            font-size: 14px;
        }
        
        @media (max-width: 1024px) {
            .content-wrapper {
                padding: 24px;
            }
            
            header {
                padding: 24px;
            }
        }
        
        @media (max-width: 768px) {
            body {
                padding: 12px;
            }
            
            .content-wrapper {
                padding: 20px;
            }
            
            header {
                padding: 20px;
            }
            
            h1 {
                font-size: 24px;
            }
            
            .stats-container {
                grid-template-columns: 1fr;
                gap: 16px;
            }
            
            .controls {
                flex-direction: column;
            }
            
            .search-wrapper,
            .filter-group {
                width: 100%;
            }
            
            select,
            .date-input,
            .refresh-btn {
                width: 100%;
                justify-content: center;
            }
            
            .date-input {
                margin-top: 8px;
            }
            
            th, td {
                padding: 12px;
                font-size: 13px;
            }
            
            table {
                font-size: 12px;
            }
        }
        
        /* Smooth scroll */
        html {
            scroll-behavior: smooth;
        }
        
        /* Custom scrollbar */
        .table-container::-webkit-scrollbar {
            height: 8px;
        }
        
        .table-container::-webkit-scrollbar-track {
            background: var(--bg-primary);
        }
        
        .table-container::-webkit-scrollbar-thumb {
            background: var(--border);
            border-radius: 4px;
        }
        

        .table-container::-webkit-scrollbar-thumb:hover {
            background: var(--text-muted);
        }
        
        /* Resume & Modal Styles */
        .btn-secondary { background: var(--bg-secondary); border: 1.5px solid var(--border); color: var(--text-primary); }
        .btn-secondary:hover { background: var(--border-light); }
        
        .modal-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); display: none; align-items: center; justify-content: center; z-index: 1000; }
        .modal { background: white; padding: 32px; border-radius: 16px; width: 500px; max-width: 90%; box-shadow: var(--shadow-xl); }
        .modal-header { display: flex; justify-content: space-between; margin-bottom: 24px; align-items: center; }
        .modal-title { font-size: 20px; font-weight: 700; color: var(--text-primary); }
        .close-modal { cursor: pointer; font-size: 24px; color: var(--text-muted); background: none; border: none; }
        
        .file-upload-zone { border: 2px dashed var(--border); padding: 32px; text-align: center; border-radius: 8px; margin-bottom: 20px; cursor: pointer; transition: all 0.2s; background: var(--bg-primary); }
        .file-upload-zone:hover { border-color: var(--primary); background: rgba(37,99,235,0.05); }
        
        .action-btn { padding: 6px 12px; border-radius: 6px; font-size: 12px; font-weight: 600; border: none; cursor: pointer; display: inline-flex; align-items: center; gap: 6px; transition: all 0.2s; }
        .btn-generate { background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%); color: white; }
        .btn-generate:hover { transform: translateY(-1px); box-shadow: var(--shadow-sm); }
        .btn-download { background: var(--success); color: white; }
        .btn-download:hover { transform: translateY(-1px); box-shadow: var(--shadow-sm); }
        .btn-loading { opacity: 0.7; cursor: wait; transform: none !important; }
        
        .header-controls { display: flex; gap: 12px; align-items: center; }

        /* Auth Styles */
        .auth-container {
            max-width: 400px;
            margin: 80px auto;
            padding: 32px;
            background: white;
            border-radius: 16px;
            box-shadow: var(--shadow-lg);
            text-align: center;
        }
        .auth-title { font-size: 24px; font-weight: 700; color: var(--text-primary); margin-bottom: 24px; }
        .auth-form { display: flex; flex-direction: column; gap: 16px; }
        .auth-input { padding: 12px; border: 1px solid var(--border); border-radius: 8px; font-size: 14px; width: 100%; box-sizing: border-box; }
        .auth-btn { background: var(--primary); color: white; padding: 12px; border-radius: 8px; border: none; font-weight: 600; cursor: pointer; transition: background 0.2s; }
        .auth-btn:hover { background: var(--primary-dark); }
        .auth-link { font-size: 14px; color: var(--text-secondary); margin-top: 16px; }
        .auth-link a { color: var(--primary); text-decoration: none; font-weight: 500; }
        .auth-error { background: #fee2e2; color: #b91c1c; padding: 12px; border-radius: 8px; font-size: 14px; margin-bottom: 16px; border: 1px solid #fecaca; }
    </style>
</head>
</head>
<body>
    {% if auth_mode %}
    <div class="auth-container">
        <h2 class="auth-title">
            {% if auth_mode == 'login' %}Welcome Back{% else %}Create Account{% endif %}
        </h2>
        
        {% if auth_error %}
        <div class="auth-error">{{ auth_error }}</div>
        {% endif %}
        
        {% for message in get_flashed_messages() %}
        <div class="auth-error" style="background:var(--bg-secondary); border-color:var(--border); color:var(--text-primary);">{{ message }}</div>
        {% endfor %}
        
        <form class="auth-form" method="POST">
            {% if auth_mode == 'register' %}
            <input type="text" name="name" class="auth-input" placeholder="Full Name" required>
            {% endif %}
            <input type="email" name="email" class="auth-input" placeholder="Email Address" required>
            <input type="password" name="password" class="auth-input" placeholder="Password" required>
            
            <button type="submit" class="auth-btn">
                {% if auth_mode == 'login' %}Sign In{% else %}Sign Up{% endif %}
            </button>
        </form>
        
        <div class="auth-link">
            {% if auth_mode == 'login' %}
            Don't have an account? <a href="/register">Sign up</a>
            {% else %}
            Already have an account? <a href="/login">Log in</a>
            {% endif %}
        </div>
    </div>
    {% else %}
    <div class="container">
        <header style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h1>💼 Job Details Viewer</h1>
                <p class="subtitle">All jobs from Jobs_Collection collection • Unique jobs only</p>
            </div>
            <div class="header-controls">
                <div style="font-size: 13px; color: var(--text-secondary); margin-right: 12px; text-align: right;">
                    Logged in as <strong>{{ user.name }}</strong><br>
                    <a href="/logout" style="color: var(--danger); text-decoration: none;">Logout</a>
                </div>
                <button class="refresh-btn btn-secondary" onclick="openResumeSettings()">
                    <span>📄</span>
                    <span>Resume Settings</span>
                </button>
            </div>
        </header>
        
        <div class="content-wrapper">
            <div class="stats-container" id="statsContainer">
                <div class="stat-card">
                    <div class="stat-card-header">
                        <h3>Total Jobs</h3>
                        <div class="stat-card-icon">📊</div>
                    </div>
                    <div class="number" id="statTotal">-</div>
                </div>
                <div class="stat-card">
                    <div class="stat-card-header">
                        <h3>Total Companies</h3>
                        <div class="stat-card-icon">🏢</div>
                    </div>
                    <div class="number" id="statCompanies">-</div>
                </div>
            </div>
            
            <div id="duplicateWarning" style="display: none;" class="duplicate-warning">
                <div class="duplicate-warning-content">
                    <div>
                        <strong>⚠️ Duplicate Jobs Detected</strong>
                        <p>You have <span id="duplicateCount">0</span> duplicate job(s) in your database. Click the button below to automatically remove duplicates (keeping only the most recent entry for each job_id).</p>
                    </div>
                    <button class="cleanup-btn" id="cleanupBtn" onclick="cleanupDuplicates()">
                        <span>🧹</span>
                        <span>Remove Duplicates</span>
                    </button>
                </div>
            </div>
            
            <div class="controls-section">
                <div class="controls">
                    <div class="search-wrapper">
                        <span class="search-icon">🔍</span>
                        <input type="text" 
                               class="search-box" 
                               id="searchBox" 
                               placeholder="Search by job title, company, or location...">
                    </div>
                    
                    <div class="filter-group">
                        <select id="roleFilter">
                            <option value="">All Roles</option>
                        </select>
                        
                        <select id="companyFilter">
                            <option value="">All Companies</option>
                        </select>
                        
                        <select id="dateFilter">
                            <option value="">All Dates</option>
                            <option value="today">Today</option>
                            <option value="week">This Week</option>
                            <option value="month">This Month</option>
                            <option value="custom">Custom Date</option>
                        </select>
                        
                        <input type="date" id="customDateInput" style="display: none;" class="date-input">
                        
                        <button class="refresh-btn" id="refreshBtn">
                            <span>🔄</span>
                            <span>Refresh</span>
                        </button>
                    </div>
                </div>
            </div>
            
            <div id="errorContainer"></div>
            
            <div id="loadingContainer" class="loading">
                <div class="spinner"></div>
                <p>Loading job details...</p>
            </div>
            
            <div class="table-wrapper" id="tableContainer" style="display: none;">
                <div class="table-container">
                    <table id="jobsTable">
                        <thead>
                            <tr>
                                <th>Job Title</th>
                                <th>Company</th>
                                <th>Location</th>
                                <th>Date Added</th>
                                <th>Job URL</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody id="jobsTableBody">
                        </tbody>
                    </table>
                </div>
            </div>
            
            <div id="noDataContainer" class="no-data" style="display: none;">
                <div class="no-data-icon">📭</div>
                <h2>No jobs found</h2>
                <p>Try adjusting your search filters or refresh the page.</p>
            </div>
            
            <div class="pagination" id="pagination" style="display: none;">
                <button id="prevBtn" onclick="changePage(-1)">← Previous</button>
                <span class="current-page" id="pageInfo">Page 1</span>
                <button id="nextBtn" onclick="changePage(1)">Next →</button>
            </div>
        </div>
    </div>
    
    <!-- Resume Settings Modal -->
    <div class="modal-overlay" id="resumeModal">
        <div class="modal">
            <div class="modal-header">
                <h3 class="modal-title">Resume Settings</h3>
                <button class="close-modal" onclick="closeResumeSettings()">×</button>
            </div>
            <div id="resumeModalContent">
                <div class="file-upload-zone" onclick="document.getElementById('masterResumeInput').click()">
                    <div style="font-size: 32px; margin-bottom: 12px;">📤</div>
                    <p style="font-weight: 500; margin-bottom: 4px;">Upload Master Resume</p>
                    <p style="font-size: 13px; color: var(--text-muted);">Click to select .pdf or .tex file</p>
                    <input type="file" id="masterResumeInput" accept=".pdf,.tex" style="display: none;" onchange="handleFileSelect(this)">
                </div>
                <div id="uploadStatus" style="font-size: 13px; text-align: center; min-height: 20px;"></div>
                <div style="margin-top: 24px; text-align: right;">
                    <button class="cleanup-btn" style="background: var(--primary); width: 100%; justify-content: center;" onclick="uploadMasterResume()" id="btnUploadResume" disabled>
                        Upload & Save
                    </button>
                </div>
            </div>
        </div>
    </div>
    {% endif %}
    
    <script>
        let allJobs = [];
        let filteredJobs = [];
        let currentPage = 1;
        const jobsPerPage = 50;
        
        // Load data on page load
        document.addEventListener('DOMContentLoaded', function() {
            loadStats();
            loadJobs();
            
            // Setup search and filters
            document.getElementById('searchBox').addEventListener('input', applyFilters);
            document.getElementById('roleFilter').addEventListener('change', applyFilters);
            document.getElementById('companyFilter').addEventListener('change', applyFilters);
            document.getElementById('dateFilter').addEventListener('change', function() {
                const customDateInput = document.getElementById('customDateInput');
                if (this.value === 'custom') {
                    customDateInput.style.display = 'block';
                } else {
                    customDateInput.style.display = 'none';
                    customDateInput.value = '';
                    applyFilters();
                }
            });
            document.getElementById('customDateInput').addEventListener('change', applyFilters);
            document.getElementById('refreshBtn').addEventListener('click', function() {
                loadStats();
                loadJobs();
            });
        });
        
        async function loadStats() {
            try {
                const response = await fetch('/api/stats');
                
                // Check if response is OK
                if (!response.ok) {
                    const text = await response.text();
                    console.error(`Failed to load stats: ${response.status} - ${text.substring(0, 200)}`);
                    return;
                }
                
                // Check content type
                const contentType = response.headers.get('content-type');
                if (!contentType || !contentType.includes('application/json')) {
                    const text = await response.text();
                    console.error(`Expected JSON but got ${contentType}. Response: ${text.substring(0, 200)}`);
                    return;
                }
                
                const data = await response.json();
                
                if (data.success) {
                    document.getElementById('statTotal').textContent = data.stats.total_jobs;
                    document.getElementById('statCompanies').textContent = data.stats.total_companies;
                    
                    // Show/hide duplicate warning
                    const duplicateWarning = document.getElementById('duplicateWarning');
                    const duplicateCount = data.stats.duplicate_count || 0;
                    
                    if (duplicateCount > 0) {
                        document.getElementById('duplicateCount').textContent = duplicateCount;
                        duplicateWarning.style.display = 'block';
                    } else {
                        duplicateWarning.style.display = 'none';
                    }
                } else {
                    console.error('Error loading stats:', data.error);
                }
            } catch (error) {
                console.error('Error loading stats:', error);
            }
        }
        
        async function cleanupDuplicates() {
            const cleanupBtn = document.getElementById('cleanupBtn');
            const errorContainer = document.getElementById('errorContainer');
            
            // Confirm action
            if (!confirm('Are you sure you want to remove all duplicate jobs? This will keep only the most recent entry for each job_id. This action cannot be undone.')) {
                return;
            }
            
            cleanupBtn.disabled = true;
            cleanupBtn.innerHTML = '<span>⏳</span><span>Cleaning...</span>';
            errorContainer.innerHTML = '';
            
            try {
                const response = await fetch('/api/cleanup-duplicates', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });
                
                // Check if response is OK and is JSON
                if (!response.ok) {
                    const text = await response.text();
                    throw new Error(`Server returned ${response.status}: ${text.substring(0, 200)}`);
                }
                
                // Check content type
                const contentType = response.headers.get('content-type');
                if (!contentType || !contentType.includes('application/json')) {
                    const text = await response.text();
                    throw new Error(`Expected JSON but got ${contentType}. Response: ${text.substring(0, 200)}`);
                }
                
                const data = await response.json();
                
                if (data.success) {
                    errorContainer.innerHTML = `
                        <div style="background: #d1fae5; color: #065f46; padding: 16px 20px; border-radius: 10px; border: 1px solid #86efac; margin-bottom: 24px;">
                            <strong>✅ Success!</strong> Removed ${data.deleted_count} duplicate job(s). Refreshing data...
                        </div>
                    `;
                    
                    // Refresh stats and jobs after a short delay
                    setTimeout(() => {
                        loadStats();
                        loadJobs();
                    }, 1000);
                } else {
                    errorContainer.innerHTML = `
                        <div class="error">
                            <strong>[Error] Error:</strong> ${data.error || 'Failed to remove duplicates'}
                        </div>
                    `;
                }
            } catch (error) {
                console.error('Cleanup error:', error);
                errorContainer.innerHTML = `
                    <div class="error">
                        <strong>[Error] Error:</strong> ${error.message || 'Failed to remove duplicates'}<br>
                        <small>Check the browser console for more details.</small>
                    </div>
                `;
            } finally {
                cleanupBtn.disabled = false;
                cleanupBtn.innerHTML = '<span>🧹</span><span>Remove Duplicates</span>';
            }
        }
        
        async function loadJobs() {
            const loadingContainer = document.getElementById('loadingContainer');
            const tableContainer = document.getElementById('tableContainer');
            const errorContainer = document.getElementById('errorContainer');
            const noDataContainer = document.getElementById('noDataContainer');
            
            loadingContainer.style.display = 'block';
            tableContainer.style.display = 'none';
            errorContainer.innerHTML = '';
            noDataContainer.style.display = 'none';
            
            try {
                const response = await fetch('/api/jobs');
                
                // Check if response is OK
                if (!response.ok) {
                    const text = await response.text();
                    loadingContainer.style.display = 'none';
                    errorContainer.innerHTML = `
                        <div class="error">
                            <strong>[Error] Server Error:</strong> ${response.status} ${response.statusText}<br>
                            ${text.substring(0, 500)}
                        </div>
                    `;
                    return;
                }
                
                // Check content type
                const contentType = response.headers.get('content-type');
                if (!contentType || !contentType.includes('application/json')) {
                    const text = await response.text();
                    loadingContainer.style.display = 'none';
                    errorContainer.innerHTML = `
                        <div class="error">
                            <strong>[Error] Invalid Response:</strong> Expected JSON but got ${contentType || 'unknown'}<br>
                            ${text.substring(0, 500)}
                        </div>
                    `;
                    return;
                }
                
                const data = await response.json();
                loadingContainer.style.display = 'none';
                
                if (!data.success) {
                    errorContainer.innerHTML = `
                        <div class="error">
                            <strong>[Error] Error:</strong> ${data.error || 'Failed to load jobs'}
                        </div>
                    `;
                    return;
                }
                
                allJobs = data.jobs || [];
                
                if (allJobs.length === 0) {
                    noDataContainer.style.display = 'block';
                    return;
                }
                
                // Sort all jobs by date/time (newest first) when initially loaded
                allJobs = sortJobsByDate(allJobs);
                
                // Populate filter dropdowns
                populateFilters();
                
                applyFilters();
                
            } catch (error) {
                loadingContainer.style.display = 'none';
                errorContainer.innerHTML = `
                    <div class="error">
                        <strong>[Error] Connection Error:</strong> ${error.message}<br>
                        Make sure the Flask server is running on port 5000 and responding with JSON.
                    </div>
                `;
                console.error('Error loading jobs:', error);
            }
        }
        
        // Helper function to parse date string and return timestamp for sorting
        function parseDateForSorting(dateStr) {
            if (!dateStr || dateStr === '-') return 0;
            
            try {
                // Handle YYYY-MM-DD format (e.g., "2025-12-05")
                if (/^\d{4}-\d{2}-\d{2}$/.test(dateStr)) {
                    const date = new Date(dateStr + 'T00:00:00');
                    if (!isNaN(date.getTime())) {
                        return date.getTime();
                    }
                }
                
                // Try to parse other formats like "November 27, 2025 5:19 PM (CST)"
                // Remove timezone info for parsing
                let cleanDate = dateStr.replace(/\s*\([^)]*\)\s*$/, ''); // Remove (CST) etc
                
                // Parse the date string
                const date = new Date(cleanDate);
                
                // If parsing failed, return 0 (will appear at end)
                if (isNaN(date.getTime())) return 0;
                
                return date.getTime();
            } catch (e) {
                return 0;
            }
        }
        
        // Sort jobs by date/time (newest first)
        function sortJobsByDate(jobs) {
            return jobs.sort((a, b) => {
                const dateA = parseDateForSorting(a.timestamp_added);
                const dateB = parseDateForSorting(b.timestamp_added);
                
                // If dates are equal, use _id as fallback (MongoDB ObjectId contains timestamp)
                if (dateA === dateB) {
                    // Compare _id strings (newer ObjectIds are greater)
                    return (b._id || '').localeCompare(a._id || '');
                }
                
                // Sort by date (newest first)
                return dateB - dateA;
            });
        }
        

        // --- Resume Functions ---

        function openResumeSettings() {
            document.getElementById('resumeModal').style.display = 'flex';
            checkMasterResumeStatus();
        }
        
        function closeResumeSettings() {
            document.getElementById('resumeModal').style.display = 'none';
        }
        
        function handleFileSelect(input) {
            const statusDiv = document.getElementById('uploadStatus');
            const btn = document.getElementById('btnUploadResume');
            if (input.files && input.files[0]) {
                const file = input.files[0];
                statusDiv.innerHTML = `Selected: <strong>${file.name}</strong> (${(file.size/1024).toFixed(1)} KB)`;
                statusDiv.style.color = 'var(--text-primary)';
                btn.disabled = false;
            } else {
                statusDiv.textContent = '';
                btn.disabled = true;
            }
        }
        
        async function checkMasterResumeStatus() {
            try {
                const response = await fetch('/api/check_master_resume');
                const data = await response.json();
                const statusDiv = document.getElementById('uploadStatus');
                if (data.exists) {
                    statusDiv.innerHTML = `✅ Master Resume Found: <strong>${data.filename}</strong><br><span style="color:var(--text-muted)">Upload new file to replace.</span>`;
                } else {
                    statusDiv.innerHTML = `<span style="color:var(--warning)">⚠️ No Master Resume found. Please upload one.</span>`;
                }
            } catch (e) { console.error(e); }
        }
        
        async function uploadMasterResume() {
            const input = document.getElementById('masterResumeInput');
            const btn = document.getElementById('btnUploadResume');
            const statusDiv = document.getElementById('uploadStatus');
            
            if (!input.files[0]) return;
            
            const formData = new FormData();
            formData.append('resume', input.files[0]);
            
            btn.disabled = true;
            btn.innerHTML = 'Uploading...';
            
            try {
                const response = await fetch('/api/upload_master_resume', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                if (data.success) {
                    statusDiv.innerHTML = `✅ ${data.message}`;
                    statusDiv.style.color = 'var(--success)';
                    setTimeout(closeResumeSettings, 1500);
                } else {
                    statusDiv.textContent = 'Error: ' + data.error;
                    statusDiv.style.color = 'var(--danger)';
                }
            } catch (e) {
                statusDiv.textContent = 'Upload failed: ' + e.message;
                statusDiv.style.color = 'var(--danger)';
            } finally {
                btn.disabled = false;
                btn.innerHTML = 'Upload & Save';
            }
        }
        
        async function generateResume(jobId, btn) {
            const originalText = btn.innerHTML;
            btn.innerHTML = '⚙️ ...';
            btn.classList.add('btn-loading');
            btn.disabled = true;
            
            try {
                const response = await fetch(`/api/generate_resume/${jobId}`, {
                    method: 'POST'
                });
                const data = await response.json();
                
                if (data.success) {
                    // Update button content to Download
                    btn.classList.remove('btn-loading', 'btn-generate');
                    btn.classList.add('btn-download');
                    btn.innerHTML = '⬇️ Download';
                    btn.onclick = () => downloadResume(data.resume_id);
                    btn.disabled = false;
                    alert('✅ Resume generated successfully!');
                } else {
                    alert('❌ Error: ' + data.error);
                    btn.innerHTML = originalText;
                    btn.classList.remove('btn-loading');
                    btn.disabled = false;
                }
            } catch (e) {
                alert('❌ Connection failed: ' + e.message);
                btn.innerHTML = originalText;
                btn.classList.remove('btn-loading');
                btn.disabled = false;
            }
        }
        
        function downloadResume(fileId) {
            window.open(`/api/download_resume/${fileId}`, '_blank');
        }

        function populateFilters() {
            // Get unique roles and companies
            const uniqueRoles = new Set();
            const uniqueCompanies = new Set();
            
            allJobs.forEach(job => {
                if (job.job_title) uniqueRoles.add(job.job_title);
                if (job.company_name) uniqueCompanies.add(job.company_name);
            });
            
            // Populate role filter
            const roleFilter = document.getElementById('roleFilter');
            const currentRoleValue = roleFilter.value;
            roleFilter.innerHTML = '<option value="">All Roles</option>';
            Array.from(uniqueRoles).sort().forEach(role => {
                const option = document.createElement('option');
                option.value = role;
                option.textContent = role;
                roleFilter.appendChild(option);
            });
            if (currentRoleValue) roleFilter.value = currentRoleValue;
            
            // Populate company filter
            const companyFilter = document.getElementById('companyFilter');
            const currentCompanyValue = companyFilter.value;
            companyFilter.innerHTML = '<option value="">All Companies</option>';
            Array.from(uniqueCompanies).sort().forEach(company => {
                const option = document.createElement('option');
                option.value = company;
                option.textContent = company;
                companyFilter.appendChild(option);
            });
            if (currentCompanyValue) companyFilter.value = currentCompanyValue;
        }
        
        function applyFilters() {
            const searchTerm = document.getElementById('searchBox').value.toLowerCase();
            const roleFilter = document.getElementById('roleFilter').value;
            const companyFilter = document.getElementById('companyFilter').value;
            const dateFilter = document.getElementById('dateFilter').value;
            const customDate = document.getElementById('customDateInput').value;
            
            filteredJobs = allJobs.filter(job => {
                // Search filter
                const matchesSearch = !searchTerm || 
                    (job.job_title && job.job_title.toLowerCase().includes(searchTerm)) ||
                    (job.company_name && job.company_name.toLowerCase().includes(searchTerm)) ||
                    (job.location_full && job.location_full.toLowerCase().includes(searchTerm));
                
                // Role filter
                const matchesRole = !roleFilter || (job.job_title === roleFilter);
                
                // Company filter
                const matchesCompany = !companyFilter || (job.company_name === companyFilter);
                
                // Date filter
                let matchesDate = true;
                if (dateFilter && job.timestamp_added) {
                    const jobDate = parseDateForSorting(job.timestamp_added);
                    if (jobDate > 0) {
                        const today = new Date();
                        today.setHours(0, 0, 0, 0);
                        const todayTime = today.getTime();
                        
                        if (dateFilter === 'custom' && customDate) {
                            const selectedDate = new Date(customDate);
                            selectedDate.setHours(0, 0, 0, 0);
                            const selectedDateStr = selectedDate.toISOString().split('T')[0];
                            const jobDateStr = new Date(jobDate).toISOString().split('T')[0];
                            matchesDate = jobDateStr === selectedDateStr;
                        } else if (dateFilter === 'today') {
                            const jobDateOnly = new Date(jobDate);
                            jobDateOnly.setHours(0, 0, 0, 0);
                            matchesDate = jobDateOnly.getTime() === todayTime;
                        } else if (dateFilter === 'week') {
                            const weekAgo = todayTime - (7 * 24 * 60 * 60 * 1000);
                            matchesDate = jobDate >= weekAgo;
                        } else if (dateFilter === 'month') {
                            const monthAgo = todayTime - (30 * 24 * 60 * 60 * 1000);
                            matchesDate = jobDate >= monthAgo;
                        }
                    } else {
                        matchesDate = false;
                    }
                }
                
                return matchesSearch && matchesRole && matchesCompany && matchesDate;
            });
            
            // Sort filtered jobs by date/time (newest first)
            filteredJobs = sortJobsByDate(filteredJobs);
            
            currentPage = 1;
            renderJobs();
        }
        
        function renderJobs() {
            const tbody = document.getElementById('jobsTableBody');
            const tableContainer = document.getElementById('tableContainer');
            const noDataContainer = document.getElementById('noDataContainer');
            const pagination = document.getElementById('pagination');
            
            if (filteredJobs.length === 0) {
                tableContainer.style.display = 'none';
                noDataContainer.style.display = 'block';
                pagination.style.display = 'none';
                return;
            }
            
            tableContainer.style.display = 'block';
            noDataContainer.style.display = 'none';
            
            // Calculate pagination
            const totalPages = Math.ceil(filteredJobs.length / jobsPerPage);
            const startIndex = (currentPage - 1) * jobsPerPage;
            const endIndex = startIndex + jobsPerPage;
            const pageJobs = filteredJobs.slice(startIndex, endIndex);
            
            // Render jobs
            tbody.innerHTML = pageJobs.map(job => {
                return `
                <tr>
                    <td><strong>${job.job_title || '-'}</strong></td>
                    <td>${job.company_name || '-'}</td>
                    <td>${job.location_full || '-'}</td>
                    <td>${job.timestamp_added || '-'}</td>
                    <td>
                        ${job.job_url ? `<a href="${job.job_url}" target="_blank" class="job-url">View ↗</a>` : '-'}
                    </td>
                    <td>
                        ${job.resume_id ? 
                            `<button class="action-btn btn-download" onclick="downloadResume('${job.resume_id}')">⬇️ Download</button>` : 
                            `<button class="action-btn btn-generate" onclick="generateResume('${job._id}', this)">✨ Generate</button>`
                        }
                    </td>
                </tr>
                `;
            }).join('');
            
            // Update pagination
            if (totalPages > 1) {
                pagination.style.display = 'flex';
                document.getElementById('pageInfo').textContent = `Page ${currentPage} of ${totalPages} (${filteredJobs.length} jobs)`;
                document.getElementById('prevBtn').disabled = currentPage === 1;
                document.getElementById('nextBtn').disabled = currentPage === totalPages;
            } else {
                pagination.style.display = 'none';
            }
        }
        
        function changePage(direction) {
            const totalPages = Math.ceil(filteredJobs.length / jobsPerPage);
            const newPage = currentPage + direction;
            
            if (newPage >= 1 && newPage <= totalPages) {
                currentPage = newPage;
                renderJobs();
                window.scrollTo({ top: 0, behavior: 'smooth' });
            }
        }
    </script>
</body>
</html>
'''

def get_mongodb_client():
    """Get MongoDB client connection"""
    connection_string = MONGODB_CONFIG["connection_string"]
    
    # Mask password in error messages for security
    masked_connection = connection_string.split('@')[0].split(':')[0] + ':***@' + '@'.join(connection_string.split('@')[1:])
    
    try:
        print(f"🔌 Attempting to connect to MongoDB...")
        client = MongoClient(
            connection_string,
            serverSelectionTimeoutMS=10000  # Increased timeout to 10 seconds
        )
        # Test connection
        print(f"   Testing connection with ping...")
        client.admin.command('ping')
        print(f"    Connection successful!")
        return client
    except ConnectionFailure as e:
        error_msg = (
            f" Connection Failure: Unable to reach MongoDB server.\n"
            f"   Connection string: {masked_connection}\n"
            f"   Error: {str(e)}\n\n"
            f" Troubleshooting steps:\n"
            f"   1. Check your internet connection\n"
            f"   2. Verify MongoDB Atlas cluster is running (check Atlas dashboard)\n"
            f"   3. Verify your IP address is whitelisted in MongoDB Atlas:\n"
            f"      - Go to MongoDB Atlas → Network Access\n"
            f"      - Add your current IP address (or use 0.0.0.0/0 for testing)\n"
            f"   4. Try running: python test_mongodb_connection.py"
        )
        print(error_msg)
        return None
    except OperationFailure as e:
        error_msg = (
            f"[Error] Authentication Failed: Invalid credentials.\n"
            f"   Connection string: {masked_connection}\n"
            f"   Error: {str(e)}\n\n"
            f"💡 Troubleshooting steps:\n"
            f"   1. Verify username and password in connection string\n"
            f"   2. Check if password has special characters (may need URL encoding)\n"
            f"   3. Verify database user has proper permissions in MongoDB Atlas\n"
            f"   4. Get fresh connection string from MongoDB Atlas Dashboard\n"
            f"   5. Try running: python test_mongodb_connection.py"
        )
        print(error_msg)
        return None
    except Exception as e:
        error_msg = (
            f"[Error] Unexpected error connecting to MongoDB.\n"
            f"   Connection string: {masked_connection}\n"
            f"   Error: {str(e)}"
        )
        print(error_msg)
        import traceback
        print("\n📋 Full error traceback:")
        traceback.print_exc()
        return None


# Helper to get Database and GridFS connection
def get_db_connection():
    client = get_mongodb_client()
    if not client:
        return None, None, None, None, "Failed to connect to MongoDB"
    
    try:
        # DB Selection Logic (same as get_all_jobs)
        possible_databases = ["N8N", MONGODB_CONFIG["database_name"], "ACN", "n8n_jobs_db"]
        possible_collection_names = ["Jobs_Collection", MONGODB_CONFIG["collection_name"], "N8n_Jobs", "N8N Jobs", "jobs"]
        
        actual_db = None
        actual_coll_name = None
        
        for db_name in possible_databases:
            try:
                db_list = client.list_database_names()
                if db_name in db_list:
                    db = client[db_name]
                    colls = db.list_collection_names()
                    for coll in possible_collection_names:
                        if coll in colls:
                            actual_db = db
                            actual_coll_name = coll
                            break
                if actual_db is not None: break
            except: continue
            
        if actual_db is None:
             # Fallback to config defaults even if they don't exist (mongo will create on write)
            actual_db = client[MONGODB_CONFIG["database_name"]]
            actual_coll_name = MONGODB_CONFIG["collection_name"]

        collection = actual_db[actual_coll_name]
        fs = gridfs.GridFS(actual_db)
        
        return client, actual_db, collection, fs, None
        
    except Exception as e:
        return None, None, None, None, str(e)

def get_all_jobs():
    """Fetch all jobs from MongoDB collection"""
    client = get_mongodb_client()
    if not client:
        error_details = (
            "Failed to connect to MongoDB.\n\n"
            "Possible causes:\n"
            "• IP address not whitelisted in MongoDB Atlas\n"
            "• Incorrect password in connection string\n"
            "• Network connectivity issues\n"
            "• MongoDB Atlas cluster is down\n\n"
            "Troubleshooting:\n"
            "1. Run: python test_mongodb_connection.py\n"
            "2. Check MongoDB Atlas → Network Access → Add your IP\n"
            "3. Verify connection string password matches Atlas password\n"
            "4. Check error messages above for more details"
        )
        return None, error_details
    
    try:
        # Use N8N database with Jobs_Collection collection (prioritize exact match)
        possible_databases = [
            "N8N",  # N8N database first (as specified by user)
            MONGODB_CONFIG["database_name"],
            "ACN",  # Fallback
            "n8n_jobs_db"
        ]
        
        # Prioritize Jobs_Collection collection
        possible_collection_names = [
            "Jobs_Collection",  # Exact collection name in N8N database
            MONGODB_CONFIG["collection_name"],
            "N8n_Jobs",
            "N8N Jobs",
            "N8n Jobs",
            "jobs"
        ]
        
        actual_db = None
        actual_collection_name = None
        
        # Try N8N database first, then others
        for db_name in possible_databases:
            try:
                db = client[db_name]
                collections = db.list_collection_names()
                
                # Try to find the collection in this database
                for coll_name in possible_collection_names:
                    if coll_name in collections:
                        actual_db = db
                        actual_collection_name = coll_name
                        print(f"✅ Found collection '{coll_name}' in database '{db_name}'")
                        break
                
                if actual_db is not None and actual_collection_name:
                    break
            except Exception as e:
                print(f"⚠️  Warning: Could not access database '{db_name}': {e}")
                continue
        
        if actual_db is None or actual_collection_name is None:
            # List all available databases and collections for debugging
            db_list = client.list_database_names()
            all_collections = {}
            for db_name in [d for d in db_list if d not in ['admin', 'config', 'local']]:
                try:
                    db = client[db_name]
                    all_collections[db_name] = db.list_collection_names()
                except:
                    pass
            
            error_msg = f"Collection not found. Tried databases: {', '.join(possible_databases)}. "
            error_msg += f"Available databases: {', '.join(all_collections.keys()) if all_collections else 'none'}"
            if all_collections:
                error_msg += "\nCollections found:"
                for db_name, colls in all_collections.items():
                    if colls:
                        error_msg += f"\n  • {db_name}: {', '.join(colls)}"
            client.close()
            return None, error_msg
        
        collection = actual_db[actual_collection_name]
        
        # Log which database and collection we're using
        db_name_used = actual_db.name
        print(f"📊 Using database: '{db_name_used}', collection: '{actual_collection_name}'")
        
        # Get total document count from MongoDB
        total_doc_count = collection.count_documents({})
        print(f"📈 Total documents in collection: {total_doc_count}")
        
        # Fetch all jobs, sorted by _id (newest first) - _id is timestamp-based and more reliable than string timestamp
        # This ensures if there are duplicates, we process the most recent first
        all_jobs = list(collection.find({}).sort("_id", -1))
        
        # Verify we got all documents
        if len(all_jobs) != total_doc_count:
            print(f"⚠️  Warning: Fetched {len(all_jobs)} documents but count_documents() returned {total_doc_count}")
        
        # Filter to get unique jobs by job_id (keep the first one encountered, which is most recent due to sort)
        # Jobs without job_id are always included (they can't be duplicates)
        seen_job_ids = set()
        unique_jobs = []
        jobs_without_id = 0
        
        for job in all_jobs:
            job_id = job.get('job_id')
            # Handle both numeric and string job_ids
            if job_id is not None:
                # Convert to string for consistent comparison
                job_id_str = str(job_id)
                if job_id_str not in seen_job_ids:
                    seen_job_ids.add(job_id_str)
                    unique_jobs.append(job)
            else:
                # Jobs without job_id are always included (they can't be duplicates)
                unique_jobs.append(job)
                jobs_without_id += 1
        
        # Convert ObjectId to string for JSON serialization
        for job in unique_jobs:
            if '_id' in job:
                job['_id'] = str(job['_id'])
        
        duplicates_removed = len(all_jobs) - len(unique_jobs)
        print(f"✅ Loaded {len(unique_jobs)} unique jobs from {len(all_jobs)} total documents")
        print(f"   - {len(seen_job_ids)} unique jobs with job_id")
        print(f"   - {jobs_without_id} jobs without job_id (all included)")
        if duplicates_removed > 0:
            print(f"   - {duplicates_removed} duplicate job_ids removed")
        
        client.close()
        return unique_jobs, None
    
    except Exception as e:
        if client:
            client.close()
        return None, str(e)

def get_collection():
    """Helper function to get MongoDB collection"""
    client = get_mongodb_client()
    if not client:
        print("[Error] get_collection: Failed to get MongoDB client")
        return None, None, None
    
    try:
        # Use N8N database with Jobs_Collection collection (prioritize exact match)
        possible_databases = [
            "N8N",  # N8N database first (as specified by user)
            MONGODB_CONFIG["database_name"],
            "ACN",  # Fallback
            "n8n_jobs_db"
        ]
        
        # Prioritize Jobs_Collection collection
        possible_collection_names = [
            "Jobs_Collection",  # Exact collection name in N8N database
            MONGODB_CONFIG["collection_name"],
            "N8n_Jobs",
            "N8N Jobs",
            "N8n Jobs",
            "jobs"
        ]
        
        actual_db = None
        actual_collection_name = None
        
        # Try N8N database first, then others
        for db_name in possible_databases:
            try:
                db = client[db_name]
                collections = db.list_collection_names()
                
                for coll_name in possible_collection_names:
                    if coll_name in collections:
                        actual_db = db
                        actual_collection_name = coll_name
                        print(f"✅ get_collection: Found '{coll_name}' in database '{db_name}'")
                        break
                
                if actual_db is not None and actual_collection_name:
                    break
            except Exception as e:
                print(f"⚠️  get_collection: Could not access database '{db_name}': {e}")
                continue
        
        if actual_db is None or actual_collection_name is None:
            print("[Error] get_collection: Collection not found in any database")
            # List available databases and collections for debugging
            try:
                db_list = client.list_database_names()
                all_collections = {}
                for db_name in [d for d in db_list if d not in ['admin', 'config', 'local']]:
                    try:
                        db = client[db_name]
                        all_collections[db_name] = db.list_collection_names()
                    except:
                        pass
                print(f"📋 Available databases and collections: {all_collections}")
            except:
                pass
            client.close()
            return None, None, None
        
        collection = actual_db[actual_collection_name]
        return client, collection, actual_collection_name
    except Exception as e:
        print(f"[Error] get_collection: Exception occurred: {e}")
        import traceback
        traceback.print_exc()
        if client:
            client.close()
        return None, None, None

# Global error handler to ensure all errors return JSON
@app.errorhandler(404)
def not_found(error):
    return jsonify({"success": False, "error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    import traceback
    error_msg = "Internal server error. Check console for details."
    if hasattr(error, 'original_exception') and error.original_exception:
        error_msg = f"Internal server error: {str(error.original_exception)}"
    traceback.print_exc()
    return jsonify({"success": False, "error": error_msg}), 500

@app.errorhandler(Exception)
def handle_exception(e):
    """Handle all unhandled exceptions and return JSON"""
    import traceback
    traceback.print_exc()
    return jsonify({"success": False, "error": f"Internal server error: {str(e)}"}), 500


# --- Auth Routes ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        client, db, collection, fs, error = get_db_connection()
        if not client:
             flash("Database connection error")
             return render_template_string(HTML_TEMPLATE, auth_error="Database connection error")
        
        users_collection = db['Users']
        user_doc = users_collection.find_one({"email": email})
        
        if user_doc and check_password_hash(user_doc['password_hash'], password):
            user = User(user_doc)
            login_user(user)
            return redirect(url_for('index'))
        
        flash("Invalid email or password")
        return render_template_string(HTML_TEMPLATE, auth_mode="login", auth_error="Invalid email or password")
        
    return render_template_string(HTML_TEMPLATE, auth_mode="login")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        name = request.form.get('name')
        
        try:
            validate_email(email)
        except EmailNotValidError:
            flash("Invalid email address")
            return render_template_string(HTML_TEMPLATE, auth_mode="register", auth_error="Invalid email address")
            
        if len(password) < 6:
            flash("Password must be at least 6 characters")
            return render_template_string(HTML_TEMPLATE, auth_mode="register", auth_error="Password too short")
            
        client, db, collection, fs, error = get_db_connection()
        if not client:
             flash("Database connection error")
             return render_template_string(HTML_TEMPLATE, auth_mode="register", auth_error="Database error")
        
        users_collection = db['Users']
        
        if users_collection.find_one({"email": email}):
            flash("Email already exists")
            return render_template_string(HTML_TEMPLATE, auth_mode="register", auth_error="Email already exists")
            
        # Create User
        new_user = {
            "email": email,
            "password_hash": generate_password_hash(password),
            "name": name,
            "created_at": datetime.now()
        }
        users_collection.insert_one(new_user)
        
        # Login
        user_doc = users_collection.find_one({"email": email})
        user = User(user_doc)
        login_user(user)
        
        return redirect(url_for('index'))
        
    return render_template_string(HTML_TEMPLATE, auth_mode="register")

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
def index():
    """Serve the main HTML page"""
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    return render_template_string(HTML_TEMPLATE, user=current_user)


@app.route('/api/jobs')
@login_required
def api_jobs():
    """API endpoint to get all jobs with user-specific application data"""
    try:
        client, db, collection, fs, error = get_db_connection()
        if not client: return jsonify({"success": False, "error": "DB Error"}), 500
        
        # 1. Fetch ALL Jobs (Shared)
        jobs = list(collection.find({}).sort("_id", -1))
        
        # 2. Fetch User's Applications
        applications_collection = db['Applications']
        user_apps = list(applications_collection.find({"user_id": current_user.id}))
        
        # Map job_id -> application data
        apps_map = {app['job_id']: app for app in user_apps}
        
        # 3. Merge Data
        serialized_jobs = []
        unique_job_ids = set()
        
        for job in jobs:
            # Skip duplicates in list if needed (though backend cleanup handles DB)
            job_id_str = str(job.get('job_id'))
            if job_id_str in unique_job_ids: continue
            if job.get('job_id'): unique_job_ids.add(job_id_str)
            
            job_oid = str(job['_id'])
            serialized_job = {}
            
            # Serialize basic fields
            for key, value in job.items():
                if isinstance(value, ObjectId):
                    serialized_job[key] = str(value)
                elif isinstance(value, datetime):
                    serialized_job[key] = value.isoformat()
                else:
                    serialized_job[key] = value
            
            # ATTACH USER DATA
            if job_oid in apps_map:
                app_data = apps_map[job_oid]
                serialized_job['resume_id'] = app_data.get('resume_id')
                serialized_job['resume_filename'] = app_data.get('resume_filename')
                serialized_job['application_status'] = app_data.get('status')
            
            serialized_jobs.append(serialized_job)
        
        return jsonify({
            "success": True,
            "count": len(serialized_jobs),
            "jobs": serialized_jobs
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": f"Internal server error: {str(e)}",
            "jobs": []
        }), 500
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": f"Internal server error: {str(e)}",
            "jobs": []
        }), 500

@app.route('/api/stats')
@login_required
def api_stats():
    """API endpoint to get job statistics"""
    client = None
    try:
        client = get_mongodb_client()
        if not client:
            return jsonify({"success": False, "error": "Failed to connect to MongoDB"}), 500
        # Use N8N database with Jobs_Collection collection (prioritize exact match)
        possible_databases = [
            "N8N",  # N8N database first (as specified by user)
            MONGODB_CONFIG["database_name"],
            "ACN",  # Fallback
            "n8n_jobs_db"
        ]
        
        # Prioritize Jobs_Collection collection
        possible_collection_names = [
            "Jobs_Collection",  # Exact collection name in N8N database
            MONGODB_CONFIG["collection_name"],
            "N8n_Jobs",
            "N8N Jobs",
            "N8n Jobs",
            "jobs"
        ]
        
        actual_db = None
        actual_collection_name = None
        
        # Try N8N database first, then others
        for db_name in possible_databases:
            try:
                db = client[db_name]
                collections = db.list_collection_names()
                
                # Try to find the collection in this database
                for coll_name in possible_collection_names:
                    if coll_name in collections:
                        actual_db = db
                        actual_collection_name = coll_name
                        print(f"✅ Using collection '{coll_name}' in database '{db_name}'")
                        break
                
                if actual_db is not None and actual_collection_name:
                    break
            except Exception as e:
                print(f"Warning: Could not access database '{db_name}': {e}")
                continue
        
        if actual_db is None or actual_collection_name is None:
            # List all available databases and collections for debugging
            db_list = client.list_database_names()
            all_collections = {}
            for db_name in [d for d in db_list if d not in ['admin', 'config', 'local']]:
                try:
                    db = client[db_name]
                    all_collections[db_name] = db.list_collection_names()
                except:
                    pass
            
            error_details = f"Available databases: {', '.join(all_collections.keys())}"
            for db_name, colls in all_collections.items():
                if colls:
                    error_details += f"\n  {db_name}: {', '.join(colls)}"
            
            client.close()
            return jsonify({
                "success": False, 
                "error": f"Collection not found. Tried: {', '.join(possible_databases)} databases, {', '.join(possible_collection_names)} collections.\n{error_details}"
            }), 404
        
        collection = actual_db[actual_collection_name]
        
        # Log which database and collection we're using
        db_name_used = actual_db.name
        print(f"📊 Using database: '{db_name_used}', collection: '{actual_collection_name}'")
        
        # Get total document count from MongoDB
        total_doc_count = collection.count_documents({})
        print(f"📈 Total documents in collection: {total_doc_count}")
        
        # Get all jobs sorted by _id (newest first) - _id is timestamp-based and more reliable than string timestamp
        all_jobs = list(collection.find({}).sort("_id", -1))
        total_documents = len(all_jobs)
        
        # Verify we got all documents
        if len(all_jobs) != total_doc_count:
            print(f"⚠️  Warning: Fetched {len(all_jobs)} documents but count_documents() returned {total_doc_count}")
        
        # Filter to unique jobs by job_id (keep the first/most recent one encountered)
        # Jobs without job_id are always included (they can't be duplicates)
        seen_job_ids = set()
        unique_jobs = []
        job_id_counts = {}  # Track how many times each job_id appears
        
        for job in all_jobs:
            job_id = job.get('job_id')
            if job_id is not None:
                # Convert to string for consistent comparison
                job_id_str = str(job_id)
                job_id_counts[job_id_str] = job_id_counts.get(job_id_str, 0) + 1
                
                if job_id_str not in seen_job_ids:
                    seen_job_ids.add(job_id_str)
                    unique_jobs.append(job)
            else:
                # Jobs without job_id are always included (they can't be duplicates)
                unique_jobs.append(job)
        
        # Count duplicates (jobs with same job_id that appear more than once)
        duplicate_count = sum(count - 1 for count in job_id_counts.values() if count > 1)
        
        # Calculate statistics based on unique jobs
        total_jobs = len(unique_jobs)
        
        # Count unique companies from unique jobs
        unique_companies = set()
        for job in unique_jobs:
            company = job.get('company_name')
            if company:
                unique_companies.add(company)
        
        client.close()
        client = None
        
        return jsonify({
            "success": True,
            "stats": {
                "total_jobs": total_jobs,
                "total_documents": total_documents,
                "duplicate_count": duplicate_count,
                "total_companies": len(unique_companies)
            }
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        if client:
            try:
                client.close()
            except:
                pass
        return jsonify({"success": False, "error": f"Internal server error: {str(e)}"}), 500

@app.route('/api/cleanup-duplicates', methods=['POST'])
@login_required
def cleanup_duplicates():
    """API endpoint to delete duplicate jobs, keeping only the most recent one for each job_id"""
    print("🧹 Cleanup duplicates endpoint called")
    
    try:
        client, collection, collection_name = get_collection()
        
        if not client:
            print("[Error] Failed to get MongoDB client")
            return jsonify({
                "success": False,
                "error": "Failed to connect to MongoDB"
            }), 500
        
        if not collection:
            print("[Error] Failed to get collection")
            if client:
                client.close()
            return jsonify({
                "success": False,
                "error": f"Collection not found. Please check database '{MONGODB_CONFIG['database_name']}' and collection '{MONGODB_CONFIG['collection_name']}'"
            }), 404
        
        print(f"✅ Connected to collection '{collection_name}'")
        
        # Get all jobs sorted by _id (newest first)
        print("📥 Fetching all jobs from collection...")
        all_jobs = list(collection.find({}).sort("_id", -1))
        print(f"📊 Found {len(all_jobs)} total documents")
        
        # Group jobs by job_id
        jobs_by_id = {}
        jobs_without_id = []
        
        for job in all_jobs:
            job_id = job.get('job_id')
            if job_id is not None:
                job_id_str = str(job_id)
                if job_id_str not in jobs_by_id:
                    jobs_by_id[job_id_str] = []
                jobs_by_id[job_id_str].append(job)
            else:
                # Jobs without job_id are kept (they can't be duplicates)
                jobs_without_id.append(job)
        
        # Identify duplicates (job_ids with more than one entry)
        duplicates_to_delete = []
        kept_jobs = len(jobs_without_id)  # All jobs without ID are kept
        
        print(f"🔍 Analyzing {len(jobs_by_id)} unique job_ids for duplicates...")
        
        for job_id_str, job_list in jobs_by_id.items():
            if len(job_list) > 1:
                # Keep the first one (most recent), delete the rest
                kept_job = job_list[0]
                kept_jobs += 1
                
                # Add all duplicates to delete list
                for duplicate_job in job_list[1:]:
                    duplicates_to_delete.append(duplicate_job['_id'])
            else:
                # Only one job with this ID, keep it
                kept_jobs += 1
        
        print(f"📋 Found {len(duplicates_to_delete)} duplicate jobs to delete")
        
        # Delete duplicate jobs
        deleted_count = 0
        if duplicates_to_delete:
            from bson import ObjectId
            
            # Convert IDs to ObjectId format (handle both ObjectId and string)
            object_ids_to_delete = []
            for oid in duplicates_to_delete:
                try:
                    if isinstance(oid, ObjectId):
                        object_ids_to_delete.append(oid)
                    else:
                        object_ids_to_delete.append(ObjectId(str(oid)))
                except Exception as e:
                    print(f"⚠️  Warning: Could not convert ID {oid} to ObjectId: {e}")
                    continue
            
            if object_ids_to_delete:
                print(f"🗑️  Deleting {len(object_ids_to_delete)} duplicate documents...")
                result = collection.delete_many({"_id": {"$in": object_ids_to_delete}})
                deleted_count = result.deleted_count
                print(f"✅ Successfully deleted {deleted_count} duplicate documents from MongoDB")
        else:
            print("ℹ️  No duplicates found to delete")
        
        client.close()
        
        print(f"🧹 Cleanup completed: Deleted {deleted_count} duplicate jobs, kept {kept_jobs} unique jobs")
        
        return jsonify({
            "success": True,
            "message": f"Successfully deleted {deleted_count} duplicate jobs",
            "deleted_count": deleted_count,
            "kept_count": kept_jobs
        })
    
    except Exception as e:
        import traceback
        error_msg = str(e)
        print(f"[Error] Error during cleanup: {error_msg}")
        print("📋 Full traceback:")
        traceback.print_exc()
        
        # Ensure client is closed on error
        try:
            if 'client' in locals() and client:
                client.close()
        except:
            pass
        
        return jsonify({
            "success": False,
            "error": f"Error during cleanup: {error_msg}"
        }), 500


# --- Resume Routes ---

@app.route('/api/check_master_resume', methods=['GET'])
@login_required
def check_master_resume():
    """Check if a master resume exists for current user"""
    try:
        client, db, collection, fs, error = get_db_connection()
        if error: return jsonify({"exists": False, "error": error}), 500
        
        # Check for user's master resume
        master_resume = fs.find_one({
            "metadata.type": "master_resume",
            "metadata.user_id": current_user.id
        })
        
        if master_resume:
            return jsonify({
                "exists": True, 
                "filename": master_resume.filename,
                "uploadDate": master_resume.upload_date
            })
        return jsonify({"exists": False})
    except Exception as e:
        return jsonify({"exists": False, "error": str(e)}), 500

@app.route('/api/upload_master_resume', methods=['POST'])
@login_required
def upload_master_resume():
    """Upload Master Resume to GridFS for current user"""
    if 'resume' not in request.files:
        return jsonify({"success": False, "error": "No file part"}), 400
        
    file = request.files['resume']
    if file.filename == '':
        return jsonify({"success": False, "error": "No selected file"}), 400
        
    if file and (file.filename.endswith('.pdf') or file.filename.endswith('.tex')):
        try:
            client, db, collection, fs, error = get_db_connection()
            if error: return jsonify({"success": False, "error": error}), 500
            
            # Delete existing master resume(s) for this user
            existing = fs.find({
                "metadata.type": "master_resume",
                "metadata.user_id": current_user.id
            })
            for f in existing:
                fs.delete(f._id)
            
            # Save new one
            file_id = fs.put(
                file, 
                filename=file.filename, 
                metadata={
                    "type": "master_resume",
                    "user_id": current_user.id
                }
            )
            
            return jsonify({
                "success": True, 
                "message": "Master resume uploaded successfully",
                "file_id": str(file_id)
            })
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500
            
    return jsonify({"success": False, "error": "Invalid file type. Only PDF or TEX allowed."}), 400

@app.route('/api/generate_resume/<job_id>', methods=['POST'])
@login_required
def generate_resume(job_id):
    """Trigger n8n webhook to generate resume for current user"""
    try:
        client, db, collection, fs, error = get_db_connection()
        if error: return jsonify({"success": False, "error": error}), 500
        
        # 1. Get Job Details
        job = collection.find_one({"_id": ObjectId(job_id)})
        if not job:
            return jsonify({"success": False, "error": "Job not found"}), 404
            
        # 2. Get User's Master Resume
        master_resume = fs.find_one({
            "metadata.type": "master_resume",
            "metadata.user_id": current_user.id
        })
        if not master_resume:
            return jsonify({"success": False, "error": "Master resume not uploaded. Please upload one first."}), 400
            
        resume_content = master_resume.read().decode('utf-8', errors='ignore')
        
        # 3. Prepare Payload (Same as before)
        city = ""
        state = ""
        if job.get('location_full') and ',' in job['location_full']:
            parts = job['location_full'].split(',')
            if len(parts) >= 2:
                city = parts[0].strip()
                state = parts[1].strip()

        payload = {
            "job_url": job.get('job_url', ''),
            "job_description": job.get('job_description', '') or f"Job Title: {job.get('job_title')}\nCompany: {job.get('company_name')}",
            "company_name": job.get('company_name', ''),
            "job_title": job.get('job_title', ''),
            "location": job.get('location_full', ''),
            "location_city": city,
            "location_state": state,
            "employment_type": job.get('employment_type', 'Full-time'),
            "remote_option": "on-site", 
            "resume_content": resume_content,
            "resume_filename": master_resume.filename,
            "user_id": current_user.id # Pass user ID if n8n needs it (optional)
        }
        
        # 4. Call n8n Webhook
        webhook_url = "http://localhost:5678/webhook/resume-tailor"  # Production webhook
        # webhook_url = "http://localhost:5678/webhook-test/resume-tailor" # Testing
        
        print(f"🚀 Triggering n8n webhook: {webhook_url}")
        
        response = requests.post(webhook_url, json=payload, stream=True)
        
        if response.status_code != 200:
            return jsonify({"success": False, "error": f"n8n Webhook failed: {response.text}"}), 502
            
        # 5. Save generated PDF to GridFS (User Specific)
        filename = f"Resume_{job.get('company_name')}_{job.get('job_title')}.pdf".replace(' ', '_').replace('/', '-')
        
        if 'Content-Disposition' in response.headers:
            import re
            fname = re.findall('filename="?([^"]+)"?', response.headers['Content-Disposition'])
            if fname: filename = fname[0]

        generated_file_id = fs.put(
            response.content,
            filename=filename,
            content_type='application/pdf',
            metadata={
                "type": "generated_resume", 
                "job_id": job_id,
                "company": job.get('company_name'),
                "user_id": current_user.id 
            }
        )
        
        # 6. Update Applications Collection (Instead of Jobs Collection)
        applications_collection = db['Applications']
        applications_collection.update_one(
            {"user_id": current_user.id, "job_id": job_id},
            {"$set": {
                "resume_id": str(generated_file_id),
                "resume_filename": filename,
                "generated_at": datetime.now(),
                "status": "Resume Generated"
            }},
            upsert=True
        )
        
        return jsonify({
            "success": True, 
            "message": "Resume generated successfully",
            "resume_id": str(generated_file_id)
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/download_resume/<file_id>', methods=['GET'])
@login_required
def download_resume(file_id):
    """Download a file from GridFS"""
    try:
        client, db, collection, fs, error = get_db_connection()
        if error: return f"Error: {error}", 500
        
        grid_out = fs.get(ObjectId(file_id))
        
        return send_file(
            io.BytesIO(grid_out.read()),
            mimetype=grid_out.content_type or 'application/pdf',
            as_attachment=True,
            download_name=grid_out.filename
        )
    except Exception as e:
        return f"Error downloading content: {str(e)}", 404

if __name__ == '__main__':
    print("=" * 70)
    print("Starting Job Viewer Application")
    print("=" * 70)
    print(f"Database: {MONGODB_CONFIG['database_name']}")
    print(f"Collection: {MONGODB_CONFIG['collection_name']}")
    print(f"Server will run on: http://localhost:5001")
    print("=" * 70)
    print()
    
    app.run(debug=True, host='0.0.0.0', port=5001)

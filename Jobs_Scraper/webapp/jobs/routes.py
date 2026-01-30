from flask import Blueprint, jsonify, request, send_file, redirect, current_app, render_template, send_from_directory
# Authentication removed - login_required and current_user no longer needed
from webapp import get_db, MONGODB_CONFIG
from bson import ObjectId
from datetime import datetime
import gridfs
import io
import os
import requests

jobs = Blueprint('jobs', __name__)


def _get_public_jobs_list():
    """Fetch jobs for the public page (title, company, url, location only). Returns (jobs, error)."""
    client = None
    try:
        client, db = get_db()
        collection = db[MONGODB_CONFIG["collection_name"]]
        all_jobs_raw = list(collection.find({}).sort("_id", -1).limit(1000))
        seen = set()
        out = []
        for job in all_jobs_raw:
            jid = job.get('job_id')
            if jid is not None:
                key = str(jid)
                if key in seen:
                    continue
                seen.add(key)
            out.append({
                "job_title": job.get("job_title") or "Job",
                "company_name": job.get("company_name") or "—",
                "job_url": job.get("job_url"),
                "location_full": job.get("location_full") or "",
            })
        return out, None
    except Exception as e:
        msg = str(e)
        if "MongoDB" in msg or "connection" in msg.lower():
            msg = "Database connection error. Please try again later."
        return [], msg
    finally:
        if client:
            client.close()


@jobs.route('/')
def dashboard():
    # On Vercel (or when frontend/dist exists): serve the built React app
    react_dist = current_app.config.get('REACT_DIST')
    if react_dist and os.path.isfile(os.path.join(react_dist, 'index.html')):
        from flask import send_from_directory
        return send_from_directory(react_dist, 'index.html')
    # Local dev: redirect to frontend if reachable
    frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
    try:
        response = requests.get(frontend_url, timeout=2)
        if response.status_code == 200:
            return redirect(frontend_url)
    except (requests.exceptions.RequestException, requests.exceptions.Timeout):
        pass
    # Frontend not running: show instructions
    from flask import render_template_string
    return render_template_string("""
    <!DOCTYPE html>
    <html><head><meta charset="UTF-8"><title>Run the app</title>
    <style>
      body { font-family: system-ui; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; background: #f1f5f9; }
      .box { background: white; padding: 2rem; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); max-width: 420px; }
      h1 { margin: 0 0 1rem; color: #334155; font-size: 1.25rem; }
      p { color: #64748b; margin: 0 0 1rem; font-size: 0.95rem; }
      code { background: #f1f5f9; padding: 0.2em 0.4em; border-radius: 4px; font-size: 0.9em; }
      .url { margin-top: 1rem; }
      a { color: #6366f1; }
    </style></head>
    <body>
      <div class="box">
        <h1>Open the frontend app</h1>
        <p>This is the API server. Use the <strong>frontend</strong> to view the dashboard.</p>
        <p>In a terminal run:</p>
        <p><code>cd frontend</code><br><code>npm run dev</code></p>
        <p class="url">Then open: <a href="{{ url }}">{{ url }}</a></p>
      </div>
    </body></html>
    """, url=frontend_url), 200


@jobs.route('/api/stats')
def api_stats():
    client = None
    try:
        print(f"[API] /api/stats called - connecting to MongoDB...")
        try:
            client, db = get_db()
            print(f"[API] MongoDB connection successful")
        except Exception as db_error:
            import traceback
            error_trace = traceback.format_exc()
            print(f"[API] MongoDB connection failed: {db_error}")
            print(error_trace)
            return jsonify({
                "success": False,
                "error": f"MongoDB connection failed: {str(db_error)}"
            }), 500
        
        collection = db[MONGODB_CONFIG["collection_name"]]
        apps_collection = db['Applications']
        print(f"[API] Using collection: {MONGODB_CONFIG['collection_name']}")
        
        total_jobs = collection.count_documents({})
        unique_companies = len(collection.distinct("company_name"))
        
        # Status stats - get all applications (no user filtering)
        user_id = None
        
        pipeline = [
            {"$group": {"_id": "$status", "count": {"$sum": 1}}}
        ]
        status_counts = {item['_id']: item['count'] for item in apps_collection.aggregate(pipeline) if item['_id'] is not None}
        
        # Calculate jobs without status (not in Applications collection)
        # Total jobs minus jobs this user has already applied to = jobs with "Not Set" status
        applied_total = sum(status_counts.values())
        not_set_count = max(0, total_jobs - applied_total)
        if not_set_count > 0:
            status_counts['Not Set'] = not_set_count

        # Check for duplicates (optimized with limit)
        pipeline = [
            {"$group": {"_id": "$job_id", "count": {"$sum": 1}}},
            {"$match": {"count": {"$gt": 1}}}
        ]
        duplicates = list(collection.aggregate(pipeline))
        duplicate_count = sum(d['count'] - 1 for d in duplicates if d['_id'] is not None)

        return jsonify({
            "success": True,
            "stats": {
                "total_jobs": total_jobs,
                "total_companies": unique_companies,
                "duplicate_count": duplicate_count,
                "status_counts": status_counts
            }
        })
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print("ERROR in api_stats:")
        print(error_trace)
        # Return error message that's safe to show to frontend
        error_msg = str(e)
        if "MongoDB" in error_msg or "connection" in error_msg.lower():
            error_msg = "Database connection error. Please check if MongoDB is accessible."
        return jsonify({
            "success": False,
            "error": error_msg,
            "traceback": error_trace if current_app.debug else None
        }), 500
    finally:
        if client:
            client.close()

@jobs.route('/api/jobs')
def api_jobs():
    client = None
    try:
        print(f"[API] /api/jobs called - connecting to MongoDB...")
        client, db = get_db()
        collection = db[MONGODB_CONFIG["collection_name"]]
        print(f"[API] Using collection: {MONGODB_CONFIG['collection_name']}")
        
        # Get all jobs, with deduplication by job_id
        # Strategy: Get all jobs first, then deduplicate in Python for better error handling
        try:
            # Get all jobs sorted by newest first
            print(f"[API] Fetching jobs from collection...")
            all_jobs_raw = list(collection.find({}).sort("_id", -1).limit(1000))
            print(f"[API] Found {len(all_jobs_raw)} raw jobs in database")
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"[API] Error fetching jobs: {e}")
            return jsonify({
                "success": False,
                "error": f"Error fetching jobs: {str(e)}"
            }), 500
        
        # Deduplicate by job_id (if it exists)
        all_jobs = []
        seen_job_ids = set()
        
        for job in all_jobs_raw:
            job_id = job.get('job_id')
            if job_id is not None:
                job_id_str = str(job_id)
                if job_id_str not in seen_job_ids:
                    seen_job_ids.add(job_id_str)
                    all_jobs.append(job)
            else:
                # Jobs without job_id - include them all (use _id as unique identifier)
                all_jobs.append(job)
        
        # Fetch all applications (no user filtering)
        apps_collection = db['Applications']
        try:
            user_apps_list = list(apps_collection.find({}))
            # Create lookup dict using job_id (which should be the ObjectId of the job)
            user_apps = {}
            for app in user_apps_list:
                job_id = app.get('job_id')
                if job_id:
                    # Store with both ObjectId string and regular string for lookup flexibility
                    user_apps[str(job_id)] = app
        except Exception as e:
            print(f"Error fetching applications: {e}")
            user_apps = {}
        
        serialized_jobs = []
        
        print(f"[API] Processing {len(all_jobs)} jobs after deduplication...")
        for job in all_jobs:
            job_oid = str(job['_id'])
            serialized_job = {
                "_id": job_oid,
                "job_title": job.get('job_title', 'N/A'),
                "company_name": job.get('company_name', 'N/A'),
                "location_full": job.get('location_full', 'N/A'),
                "timestamp_added": job.get('timestamp_added', 'N/A'),
                "job_url": job.get('job_url'),
                "job_description": job.get('job_description', 'No description available.'),
                "notes": ""
            }
            
            # Look up user application data - try both job_oid and job_id
            app_data = None
            if job_oid in user_apps:
                app_data = user_apps[job_oid]
            else:
                job_id = job.get('job_id')
                if job_id and str(job_id) in user_apps:
                    app_data = user_apps[str(job_id)]
            
            if app_data:
                serialized_job['resume_id'] = app_data.get('resume_id')
                serialized_job['app_status'] = app_data.get('status', None)
                serialized_job['notes'] = app_data.get('notes', '')
            else:
                serialized_job['app_status'] = None
                
            serialized_jobs.append(serialized_job)
        
        print(f"[API] Returning {len(serialized_jobs)} serialized jobs")
        return jsonify({
            "success": True, 
            "jobs": serialized_jobs,
            "count": len(serialized_jobs)
        })
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print("ERROR in api_jobs:")
        print(error_trace)
        # Return error message that's safe to show to frontend
        error_msg = str(e)
        if "MongoDB" in error_msg or "connection" in error_msg.lower():
            error_msg = "Database connection error. Please check if MongoDB is accessible."
        return jsonify({
            "success": False,
            "error": error_msg,
            "traceback": error_trace if current_app.debug else None
        }), 500
    finally:
        if client:
            client.close()

# Simplified other routes logic...
@jobs.route('/api/check_master_resume')
def check_master_resume():
    client = None
    try:
        client, db = get_db()
        fs = gridfs.GridFS(db)
        # Get any master resume (no user filtering)
        master = fs.find_one({"metadata.type": "master_resume"})
        exists = master is not None
        filename = master.filename if exists else None
        return jsonify({"exists": exists, "filename": filename})
    except Exception as e:
        return jsonify({"exists": False, "error": str(e)}), 500
    finally:
        if client:
            client.close()

@jobs.route('/api/upload_master_resume', methods=['POST'])
def upload_master_resume():
    client = None
    try:
        if 'resume' not in request.files:
            return jsonify({"success": False, "error": "No file"}), 400
        file = request.files['resume']
        client, db = get_db()
        fs = gridfs.GridFS(db)
        # Cleanup old (no user filtering)
        for f in fs.find({"metadata.type": "master_resume"}):
            fs.delete(f._id)
        # Save new (no user_id in metadata)
        fs.put(file, filename=file.filename, metadata={"type": "master_resume"})
        return jsonify({"success": True, "message": "Uploaded successfully"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        if client:
            client.close()

@jobs.route('/api/generate_resume/<job_id>', methods=['POST'])
def generate_resume(job_id):
    """Trigger n8n webhook to generate resume for current user"""
    client = None
    try:
        # Authentication removed - proceed without user check
        
        client, db = get_db()
        collection = db[MONGODB_CONFIG["collection_name"]]
        fs = gridfs.GridFS(db)
        
        # 1. Get Job Details - Handle invalid ObjectId
        try:
            job_oid = ObjectId(job_id) if job_id else None
        except Exception:
            if client:
                client.close()
            return jsonify({"success": False, "error": f"Invalid job ID format: {job_id}"}), 400
        
        job = collection.find_one({"_id": job_oid})
        if not job:
            if client:
                client.close()
            return jsonify({"success": False, "error": "Job not found"}), 404
            
        # 2. Get Master Resume (no user filtering)
        master_resume = fs.find_one({
            "metadata.type": "master_resume"
        })
        
        if not master_resume:
            if client:
                client.close()
            return jsonify({"success": False, "error": "Master resume not uploaded. Please upload one first."}), 400
            
        resume_content = master_resume.read().decode('utf-8', errors='ignore')
        
        # 3. Prepare Payload
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
            "user_id": None
        }
        
        # 4. Call n8n Webhooks (both production and local)
        # Define webhook URLs - user's configured URL + additional test webhooks
        webhook_urls = []
        
        # Webhook URLs - check environment variable or use default
        n8n_webhook_url = os.environ.get('N8N_WEBHOOK_URL')
        if n8n_webhook_url:
            webhook_urls.append(n8n_webhook_url)
        
        # Add additional webhook URLs for testing
        additional_webhooks = [
            "http://54.90.110.145:5678/webhook-test/resume-tailor",  # Cloud Test
            "http://192.168.1.199:5678/webhook/resume-tailor"   # Local/Network
        ]
        
        # Add additional webhooks (avoid duplicates)
        for webhook in additional_webhooks:
            if webhook not in webhook_urls:
                webhook_urls.append(webhook)
        
        if not webhook_urls:
            if client:
                client.close()
            return jsonify({"success": False, "error": "N8N Webhook URL not configured. Please go to your profile and set it up."}), 400
            
        headers = {}
        n8n_api_key = os.environ.get('N8N_API_KEY')
        if n8n_api_key:
            headers['X-N8N-API-KEY'] = n8n_api_key
            # Alternative: headers['Authorization'] = f"Bearer {n8n_api_key}"
        
        # Try calling all webhooks, use first successful response
        # But we'll try ALL webhooks to trigger them all, then use the first successful one
        response = None
        last_error = None
        successful_webhook = None
        errors = []
        webhook_responses = []  # Store all responses
        
        for webhook_url in webhook_urls:
            try:
                # Log which webhook we're trying
                print(f"[DEBUG] Attempting webhook: {webhook_url}")
                # Try POST first (standard for webhooks with data)
                webhook_response = requests.post(webhook_url, json=payload, headers=headers, stream=True, timeout=60)
                print(f"[DEBUG] Webhook {webhook_url} responded with status: {webhook_response.status_code}")
                
                # Check if response is successful
                if webhook_response.status_code == 200:
                    # Success! Store this response
                    if not response:  # Use first successful response
                        response = webhook_response
                        successful_webhook = webhook_url
                    print(f"[DEBUG] Webhook {webhook_url} succeeded!")
                    # Continue to trigger other webhooks too, but don't break
                    continue
                
                # If webhook is configured for GET, try GET with query parameters
                elif webhook_response.status_code == 404 and "GET request" in webhook_response.text:
                    # For GET requests, we need to send data as query parameters
                    # Note: This won't work well for large resume content, but we'll try
                    import urllib.parse
                    query_params = {
                        'job_url': payload.get('job_url', ''),
                        'company_name': payload.get('company_name', ''),
                        'job_title': payload.get('job_title', ''),
                        'location': payload.get('location', ''),
                        'location_city': payload.get('location_city', ''),
                        'location_state': payload.get('location_state', ''),
                        'employment_type': payload.get('employment_type', ''),
                        'user_id': str(payload.get('user_id', '')),
                    }
                    query_string = urllib.parse.urlencode(query_params)
                    get_url = f"{webhook_url}?{query_string}"
                    webhook_response = requests.get(get_url, headers=headers, stream=True, timeout=60)
                    
                    if webhook_response.status_code == 200:
                        if not response:  # Use first successful response for PDF generation
                            response = webhook_response
                            successful_webhook = webhook_url
                        print(f"[DEBUG] Webhook {webhook_url} succeeded via GET! (continuing to trigger other webhooks)")
                        # Continue to trigger other webhooks too, don't break
                        continue
                    else:
                        # Try to parse n8n error response
                        try:
                            error_data = webhook_response.json()
                            error_msg = error_data.get('message', webhook_response.text)
                            hint = error_data.get('hint', '')
                            if hint:
                                error_msg += f"\n\n{hint}"
                        except:
                            error_msg = webhook_response.text
                        errors.append(f"{webhook_url}: {error_msg}")
                
                # Non-200 status code
                else:
                    # Try to parse n8n error response for better error messages
                    try:
                        error_data = webhook_response.json()
                        error_msg = error_data.get('message', webhook_response.text)
                        hint = error_data.get('hint', '')
                        if hint:
                            error_msg += f"\n\n{hint}"
                        full_error = f"Status {webhook_response.status_code}: {error_msg}"
                    except:
                        full_error = f"Status {webhook_response.status_code}: {webhook_response.text[:200]}"
                    errors.append(f"{webhook_url}: {full_error}")
                    print(f"[DEBUG] Webhook {webhook_url} failed: {full_error}")
                    
            except requests.exceptions.RequestException as e:
                # Connection error for this webhook, try next one
                error_msg = f"Connection failed - {str(e)}"
                print(f"[DEBUG] Webhook {webhook_url} connection error: {error_msg}")
                errors.append(f"{webhook_url}: {error_msg}")
                continue
        
        # Check if we got a successful response from any webhook
        if not response or not successful_webhook:
            if client:
                client.close()
            error_summary = "\n".join([f"  - {err}" for err in errors])
            return jsonify({
                "success": False, 
                "error": f"All webhooks failed:\n{error_summary}\n\nPlease check:\n1. Your webhook URLs are correct\n2. Your n8n webhooks are configured to accept POST requests\n3. Your network connection is working\n4. Your n8n workflows are active"
            }), 502
            
        # 5. Save generated PDF to GridFS
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
                "user_id": None
            }
        )
        
        # 6. Update Applications Collection
        applications_collection = db['Applications']
        applications_collection.update_one(
            {"job_id": job_id},
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
            "message": f"Resume generated successfully (via {successful_webhook})",
            "resume_id": str(generated_file_id),
            "webhook_used": successful_webhook
        })

    except Exception as e:
        import traceback
        error_msg = str(e)
        if current_app.debug:
            traceback.print_exc()
        if client:
            try:
                client.close()
            except:
                pass
        return jsonify({
            "success": False, 
            "error": f"An error occurred while generating the resume: {error_msg}\n\nPlease check:\n1. Your n8n webhook is properly configured\n2. Your master resume is uploaded\n3. Your job details are complete"
        }), 500

@jobs.route('/api/download_resume/<file_id>', methods=['GET'])
def download_resume(file_id):
    """Download a file from GridFS"""
    client = None
    try:
        client, db = get_db()
        fs = gridfs.GridFS(db)
        
        grid_out = fs.get(ObjectId(file_id))
        
        # Read file content BEFORE closing the client
        file_content = grid_out.read()
        filename = grid_out.filename
        content_type = grid_out.content_type or 'application/pdf'
        
        # Now we can safely close the client since we have the file content in memory
        client.close()
        client = None
        
        return send_file(
            io.BytesIO(file_content),
            mimetype=content_type,
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        if client:
            try:
                client.close()
            except:
                pass
        return f"Error downloading content: {str(e)}", 404

@jobs.route('/api/update_app_status/<job_oid>', methods=['POST'])
def update_app_status(job_oid):
    client = None
    try:
        # Authentication removed - no user filtering
        status = request.json.get('status')
        if not status:
            return jsonify({"success": False, "error": "Status required"}), 400
            
        client, db = get_db()
        apps_collection = db['Applications']
        
        # Update or create application record (no user filtering)
        apps_collection.update_one(
            {"job_id": job_oid},
            {"$set": {
                "status": status, 
                "updated_at": datetime.now(),
                "job_id": job_oid   # Ensure job_id is set on upsert
            }},
            upsert=True
        )
        return jsonify({"success": True})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        if client:
            client.close()

@jobs.route('/api/update_app_notes/<job_oid>', methods=['POST'])
def update_app_notes(job_oid):
    client = None
    try:
        # Authentication removed - no user filtering
        notes = request.json.get('notes', '')
        client, db = get_db()
        apps_collection = db['Applications']
        apps_collection.update_one(
            {"job_id": job_oid},
            {"$set": {
                "notes": notes, 
                "updated_at": datetime.now(),
                "job_id": job_oid   # Ensure job_id is set on upsert
            }},
            upsert=True
        )
        return jsonify({"success": True})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        if client:
            client.close()

@jobs.route('/api/export_jobs')
def export_jobs():
    import csv
    from io import StringIO
    from flask import make_response

    client = None
    try:
        client, db = get_db()
        collection = db[MONGODB_CONFIG["collection_name"]]
        all_jobs = list(collection.find({}).sort("_id", -1).limit(1000))
        
        apps_collection = db['Applications']
        user_apps = {str(app['job_id']): app for app in apps_collection.find({})}
        
        si = StringIO()
        cw = csv.writer(si)
        cw.writerow(['Job Title', 'Company', 'Location', 'Status', 'Date Added', 'Notes', 'Job URL'])
        
        seen_ids = set()
        for job in all_jobs:
            job_id = job.get('job_id')
            if job_id is not None:
                job_id_str = str(job_id)
                if job_id_str in seen_ids:
                    continue
                seen_ids.add(job_id_str)
            
            job_oid = str(job['_id'])
            app = user_apps.get(job_oid, {})
            cw.writerow([
                job.get('job_title', 'N/A'),
                job.get('company_name', 'N/A'),
                job.get('location_full', 'N/A'),
                app.get('status', 'Interested'),
                job.get('timestamp_added', 'N/A'),
                app.get('notes', ''),
                job.get('job_url', '')
            ])
        
        output = make_response(si.getvalue())
        output.headers["Content-Disposition"] = "attachment; filename=jobs_export.csv"
        output.headers["Content-type"] = "text/csv"
        return output
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        if client:
            client.close()

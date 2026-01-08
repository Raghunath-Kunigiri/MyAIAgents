from flask import Blueprint, render_template, jsonify, request, send_file
from flask_login import login_required, current_user
from webapp import get_db, MONGODB_CONFIG
from bson import ObjectId
from datetime import datetime
import gridfs
import io
import requests

jobs = Blueprint('jobs', __name__)

@jobs.route('/')
@login_required
def dashboard():
    return render_template('jobs/index.html', user=current_user)

@jobs.route('/api/stats')
@login_required
def api_stats():
    client = None
    try:
        client, db = get_db()
        collection = db[MONGODB_CONFIG["collection_name"]]
        apps_collection = db['Applications']
        
        total_jobs = collection.count_documents({})
        unique_companies = len(collection.distinct("company_name"))
        
        # Status stats
        pipeline = [
            {"$match": {"user_id": current_user.id}},
            {"$group": {"_id": "$status", "count": {"$sum": 1}}}
        ]
        status_counts = {item['_id']: item['count'] for item in apps_collection.aggregate(pipeline) if item['_id'] is not None}
        
        # Calculate jobs without status (not in Applications collection)
        applied_total = sum(status_counts.values())
        not_set_count = total_jobs - applied_total
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
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
    finally:
        if client:
            client.close()

@jobs.route('/api/jobs')
@login_required
def api_jobs():
    client = None
    try:
        client, db = get_db()
        collection = db[MONGODB_CONFIG["collection_name"]]
        
        # Optimize: Use aggregation to deduplicate at database level and limit fields
        # First, get distinct job_ids to filter duplicates
        pipeline = [
            {"$sort": {"_id": -1}},  # Sort by newest first
            {"$group": {
                "_id": "$job_id",
                "doc": {"$first": "$$ROOT"}  # Keep first (newest) document for each job_id
            }},
            {"$replaceRoot": {"newRoot": "$doc"}},
            {"$limit": 1000}  # Limit to prevent excessive data transfer
        ]
        
        # For jobs without job_id, we need to handle them separately
        jobs_with_id = list(collection.aggregate(pipeline))
        jobs_without_id = list(collection.find({"job_id": None}).sort("_id", -1).limit(100))
        
        all_jobs = jobs_with_id + jobs_without_id
        all_jobs.sort(key=lambda x: x.get('_id'), reverse=True)  # Sort by _id descending
        
        # Fetch user applications in one query
        apps_collection = db['Applications']
        user_apps = {str(app['job_id']): app for app in apps_collection.find({"user_id": current_user.id})}
        
        serialized_jobs = []
        seen_ids = set()
        
        for job in all_jobs:
            job_id = job.get('job_id')
            if job_id is not None:
                job_id_str = str(job_id)
                if job_id_str in seen_ids:
                    continue
                seen_ids.add(job_id_str)
            
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
            
            if job_oid in user_apps:
                app = user_apps[job_oid]
                serialized_job['resume_id'] = app.get('resume_id')
                serialized_job['app_status'] = app.get('status', None)
                serialized_job['notes'] = app.get('notes', '')
            else:
                serialized_job['app_status'] = None
                
            serialized_jobs.append(serialized_job)
        
        return jsonify({"success": True, "jobs": serialized_jobs})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
    finally:
        if client:
            client.close()

# Simplified other routes logic...
@jobs.route('/api/check_master_resume')
@login_required
def check_master_resume():
    client = None
    try:
        client, db = get_db()
        fs = gridfs.GridFS(db)
        master = fs.find_one({"metadata.type": "master_resume", "metadata.user_id": current_user.id})
        exists = master is not None
        filename = master.filename if exists else None
        return jsonify({"exists": exists, "filename": filename})
    except Exception as e:
        return jsonify({"exists": False, "error": str(e)}), 500
    finally:
        if client:
            client.close()

@jobs.route('/api/upload_master_resume', methods=['POST'])
@login_required
def upload_master_resume():
    client = None
    try:
        if 'resume' not in request.files:
            return jsonify({"success": False, "error": "No file"}), 400
        file = request.files['resume']
        client, db = get_db()
        fs = gridfs.GridFS(db)
        # Cleanup old
        for f in fs.find({"metadata.type": "master_resume", "metadata.user_id": current_user.id}):
            fs.delete(f._id)
        # Save new
        fs.put(file, filename=file.filename, metadata={"type": "master_resume", "user_id": current_user.id})
        return jsonify({"success": True, "message": "Uploaded successfully"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        if client:
            client.close()

@jobs.route('/api/generate_resume/<job_id>', methods=['POST'])
@login_required
def generate_resume(job_id):
    """Trigger n8n webhook to generate resume for current user"""
    client = None
    try:
        client, db = get_db()
        collection = db[MONGODB_CONFIG["collection_name"]]
        fs = gridfs.GridFS(db)
        
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
            "user_id": current_user.id
        }
        
        # 4. Call n8n Webhook
        webhook_url = current_user.n8n_webhook_url
        if not webhook_url:
            if client:
                client.close()
            return jsonify({"success": False, "error": "N8N Webhook URL not configured. Please go to your profile and set it up."}), 400
            
        headers = {}
        if current_user.n8n_api_key:
            headers['X-N8N-API-KEY'] = current_user.n8n_api_key
            # Alternative: headers['Authorization'] = f"Bearer {current_user.n8n_api_key}"
        
        # Try POST first (standard for webhooks with data)
        try:
            response = requests.post(webhook_url, json=payload, headers=headers, stream=True, timeout=60)
            
            # If webhook is configured for GET, try GET with query parameters
            if response.status_code == 404 and "GET request" in response.text:
                # For GET requests, we need to send data as query parameters
                # Note: This won't work well for large resume content, but we'll try
                import urllib.parse
                # Convert payload to query string (only for smaller fields)
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
                # For resume content, we'll need to send it separately or the webhook needs to be POST
                # Build URL with query params
                query_string = urllib.parse.urlencode(query_params)
                get_url = f"{webhook_url}?{query_string}"
                response = requests.get(get_url, headers=headers, stream=True, timeout=60)
                
                if response.status_code != 200:
                    if client:
                        client.close()
                    return jsonify({
                        "success": False, 
                        "error": f"n8n Webhook failed: {response.text}\n\nNote: Your webhook is configured for GET requests, but resume content requires POST. Please configure your n8n webhook to accept POST requests in the webhook node settings."
                    }), 502
            elif response.status_code != 200:
                if client:
                    client.close()
                return jsonify({
                    "success": False, 
                    "error": f"n8n Webhook failed (Status {response.status_code}): {response.text}"
                }), 502
        except requests.exceptions.RequestException as e:
            if client:
                client.close()
            return jsonify({
                "success": False, 
                "error": f"Failed to connect to n8n webhook: {str(e)}\n\nPlease check:\n1. Your webhook URL is correct\n2. Your n8n webhook is configured to accept POST requests\n3. Your network connection is working"
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
                "user_id": current_user.id 
            }
        )
        
        # 6. Update Applications Collection
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
    finally:
        if client:
            try:
                client.close()
            except:
                pass

@jobs.route('/api/download_resume/<file_id>', methods=['GET'])
@login_required
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
@login_required
def update_app_status(job_oid):
    client = None
    try:
        status = request.json.get('status')
        if not status:
            return jsonify({"success": False, "error": "Status required"}), 400
            
        client, db = get_db()
        apps_collection = db['Applications']
        apps_collection.update_one(
            {"user_id": current_user.id, "job_id": job_oid},
            {"$set": {"status": status, "updated_at": datetime.now()}},
            upsert=True
        )
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        if client:
            client.close()

@jobs.route('/api/update_app_notes/<job_oid>', methods=['POST'])
@login_required
def update_app_notes(job_oid):
    client = None
    try:
        notes = request.json.get('notes', '')
        client, db = get_db()
        apps_collection = db['Applications']
        apps_collection.update_one(
            {"user_id": current_user.id, "job_id": job_oid},
            {"$set": {"notes": notes, "updated_at": datetime.now()}},
            upsert=True
        )
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        if client:
            client.close()

@jobs.route('/api/export_jobs')
@login_required
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
        user_apps = {str(app['job_id']): app for app in apps_collection.find({"user_id": current_user.id})}
        
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

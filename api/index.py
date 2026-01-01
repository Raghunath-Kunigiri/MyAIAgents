# Vercel Python Serverless Function using FastAPI
# FastAPI works better with Vercel than Flask

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import sys

# Import the MongoDB functions from the Flask app
# We'll keep the business logic but use FastAPI for routing
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from jobs_viewer_app import (
        get_all_jobs,
        get_mongodb_client,
        MONGODB_CONFIG,
        HTML_TEMPLATE,
        get_collection
    )
except ImportError as e:
    # If import fails, create a minimal app
    def get_all_jobs():
        return None, "Failed to import jobs functions"
    HTML_TEMPLATE = "<html><body><h1>Import Error</h1></body></html>"

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler to ensure all errors return JSON
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions and return JSON"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "error": str(exc.detail)}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    """Handle validation errors and return JSON"""
    return JSONResponse(
        status_code=422,
        content={"success": False, "error": str(exc)}
    )

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Ensure all exceptions return JSON responses"""
    import traceback
    error_details = str(exc)
    # Only include traceback in non-production for security
    if os.environ.get("VERCEL_ENV") != "production":
        error_details += f"\n{traceback.format_exc()}"
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": error_details}
    )

@app.get("/", response_class=HTMLResponse)
async def index():
    """Serve the main HTML page"""
    return HTMLResponse(content=HTML_TEMPLATE)

@app.get("/resume", response_class=HTMLResponse)
@app.get("/job_input_form.html", response_class=HTMLResponse)
@app.get("/Resume_Generator/job_input_form.html", response_class=HTMLResponse)
async def resume_generator():
    """Serve the resume generator HTML form"""
    # Try multiple path resolutions
    possible_paths = [
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'Resume_Generator', 'job_input_form.html'),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Resume_Generator', 'job_input_form.html'),
        os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Resume_Generator', 'job_input_form.html')),
    ]
    
    html_content = None
    for html_path in possible_paths:
        try:
            if os.path.exists(html_path):
                with open(html_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                break
        except Exception:
            continue
    
    if html_content:
        return HTMLResponse(content=html_content)
    else:
        raise HTTPException(status_code=404, detail=f"Resume generator file not found. Tried: {possible_paths}")

@app.get("/api/jobs")
async def api_jobs():
    """API endpoint to get all jobs"""
    try:
        # Safely call get_all_jobs with error handling
        try:
            jobs, error = get_all_jobs()
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"success": False, "error": f"Error calling get_all_jobs: {str(e)}"}
            )
        
        if error:
            return JSONResponse(
                status_code=500,
                content={"success": False, "error": error}
            )
        
        return JSONResponse(content={
            "success": True,
            "count": len(jobs) if jobs else 0,
            "jobs": jobs or []
        })
    except Exception as e:
        import traceback
        error_msg = str(e)
        if os.environ.get("VERCEL_ENV") != "production":
            error_msg += f"\n{traceback.format_exc()}"
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": error_msg}
        )

@app.get("/api/stats")
async def api_stats():
    """API endpoint to get job statistics"""
    from jobs_viewer_app import MONGODB_CONFIG
    
    client = get_mongodb_client()
    if not client:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": "Failed to connect to MongoDB"}
        )
    
    try:
        possible_databases = ["N8N", MONGODB_CONFIG["database_name"], "ACN", "n8n_jobs_db"]
        possible_collection_names = ["Jobs_Collection", MONGODB_CONFIG["collection_name"], "N8n_Jobs", "N8N Jobs", "N8n Jobs", "jobs"]
        
        actual_db = None
        actual_collection_name = None
        
        for db_name in possible_databases:
            try:
                db = client[db_name]
                collections = db.list_collection_names()
                for coll_name in possible_collection_names:
                    if coll_name in collections:
                        actual_db = db
                        actual_collection_name = coll_name
                        break
                if actual_db is not None:
                    break
            except Exception:
                continue
        
        if actual_db is None:
            client.close()
            return JSONResponse(
                status_code=404,
                content={"success": False, "error": "Collection not found"}
            )
        
        collection = actual_db[actual_collection_name]
        total_doc_count = collection.count_documents({})
        all_jobs = list(collection.find({}).sort("_id", -1))
        
        seen_job_ids = set()
        unique_jobs = []
        job_id_counts = {}
        
        for job in all_jobs:
            job_id = job.get('job_id')
            if job_id is not None:
                job_id_str = str(job_id)
                job_id_counts[job_id_str] = job_id_counts.get(job_id_str, 0) + 1
                if job_id_str not in seen_job_ids:
                    seen_job_ids.add(job_id_str)
                    unique_jobs.append(job)
            else:
                unique_jobs.append(job)
        
        duplicate_count = sum(count - 1 for count in job_id_counts.values() if count > 1)
        unique_companies = set()
        for job in unique_jobs:
            company = job.get('company_name')
            if company:
                unique_companies.add(company)
        
        client.close()
        
        return JSONResponse(content={
            "success": True,
            "stats": {
                "total_jobs": len(unique_jobs),
                "total_documents": len(all_jobs),
                "duplicate_count": duplicate_count,
                "total_companies": len(unique_companies)
            }
        })
    except Exception as e:
        if client:
            client.close()
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.post("/api/cleanup-duplicates")
async def cleanup_duplicates():
    """API endpoint to delete duplicate jobs"""
    client, collection, collection_name = get_collection()
    
    if not client or not collection:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": "Failed to connect to MongoDB or collection not found"}
        )
    
    try:
        all_jobs = list(collection.find({}).sort("_id", -1))
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
                jobs_without_id.append(job)
        
        duplicates_to_delete = []
        for job_id_str, job_list in jobs_by_id.items():
            if len(job_list) > 1:
                for duplicate_job in job_list[1:]:
                    duplicates_to_delete.append(duplicate_job['_id'])
        
        deleted_count = 0
        if duplicates_to_delete:
            from bson import ObjectId
            object_ids_to_delete = [ObjectId(str(oid)) if not isinstance(oid, ObjectId) else oid for oid in duplicates_to_delete]
            result = collection.delete_many({"_id": {"$in": object_ids_to_delete}})
            deleted_count = result.deleted_count
        
        client.close()
        
        return JSONResponse(content={
            "success": True,
            "message": f"Successfully deleted {deleted_count} duplicate jobs",
            "deleted_count": deleted_count,
            "kept_count": len(jobs_without_id) + len(jobs_by_id)
        })
    except Exception as e:
        if client:
            client.close()
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

# Export handler for Vercel using Mangum
# FastAPI is ASGI, but Vercel needs a Lambda-compatible handler
try:
    from mangum import Mangum
    handler = Mangum(app)
except ImportError:
    # Fallback if mangum is not available
    handler = app

# Resume Generator & Jobs Display Application

This repository contains:
1. **Resume Generator** (`job_input_form.html`) - HTML form for uploading and tailoring resumes
2. **Jobs Display Application** (`jobs_viewer_app.py`) - Flask app to display jobs from MongoDB

## Vercel Deployment

### Prerequisites
- Vercel account
- MongoDB Atlas connection string

### Deployment Steps

1. **Install Vercel CLI** (if not already installed):
   ```bash
   npm i -g vercel
   ```

2. **Login to Vercel**:
   ```bash
   vercel login
   ```

3. **Deploy**:
   ```bash
   vercel
   ```

4. **Set Environment Variables** in Vercel Dashboard:
   - Go to your project settings → Environment Variables
   - Add your MongoDB connection string if needed (or keep it in the code)

### Project Structure

```
.
├── api/
│   └── index.py          # Vercel serverless function entry point
├── job_input_form.html   # Resume generator HTML form
├── jobs_viewer_app.py   # Flask application
├── requirements.txt      # Python dependencies
├── vercel.json          # Vercel configuration
└── README.md            # This file
```

### Routes

- `/` - Jobs display application (Flask app)
- `/api/jobs` - API endpoint for jobs data
- `/api/stats` - API endpoint for statistics
- `/job_input_form.html` - Resume generator form

### Local Development

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run Flask app**:
   ```bash
   python jobs_viewer_app.py
   ```

3. **Access**:
   - Jobs Display: http://localhost:5000
   - Resume Generator: http://localhost:5000/job_input_form.html

### Notes

- The Flask app connects to MongoDB Atlas
- Make sure your MongoDB connection string is configured in `jobs_viewer_app.py`
- The resume generator form makes API calls to your N8N webhooks (configure URLs in the HTML file)


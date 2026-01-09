# JobTracker Pro - Modern Job Application Dashboard

A full-stack job application management system with a modern React frontend and Flask backend, connected to MongoDB for persistent storage.

## 🚀 Features

### Frontend (React + TypeScript + Tailwind CSS)
- 🎨 **Modern Dashboard**: Clean, enterprise-grade UI inspired by Linear and Stripe
- ⚡ **Fast Performance**: Built with Vite for lightning-fast development
- 🎭 **Smooth Animations**: Framer Motion for delightful user interactions
- 🔍 **Advanced Filtering**: Search and filter jobs by status, title, company, or location
- 📊 **Real-time Stats**: Live statistics dashboard with beautiful cards
- 🎯 **Status Management**: Custom dropdown for managing application statuses
- 📄 **Slide-over Details**: Modern slide-over panel for job details
- 💼 **Resume Management**: Upload and generate tailored resumes
- 📱 **Responsive**: Fully responsive design that works on all devices

### Backend (Flask + MongoDB)
- 🔐 **Authentication**: User login and session management
- 📈 **API Endpoints**: RESTful API for jobs, stats, and resume management
- 💾 **MongoDB Integration**: Persistent storage for jobs and user data
- 🔒 **Secure**: Session-based authentication with Flask-Login
- 🔗 **n8n Integration**: Multiple webhook support for resume generation

## 📋 Prerequisites

- **Python 3.8+**
- **Node.js 18+** and npm/yarn/pnpm
- **MongoDB** (MongoDB Atlas or local instance)
- **Virtual Environment** (recommended)

## 🛠️ Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Jobs_Scraper
```

### 2. Backend Setup

```bash
# Create and activate virtual environment
python -m venv venv

# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Create a test user (optional)
python create_test_user.py
```

### 3. Frontend Setup

```bash
cd frontend
npm install
```

## 🚀 Running the Application

### Start Backend (Terminal 1)

**Windows:**
```bash
# Option 1: Use the script
.\start_backend.bat

# Option 2: Manual start
python index.py
```

**Linux/Mac:**
```bash
source venv/bin/activate
python index.py
```

Backend will run on: `http://localhost:5000`

### Start Frontend (Terminal 2)

```bash
cd frontend
npm run dev
```

Frontend will run on: `http://localhost:3000` (or next available port)

## 🔐 Authentication

1. **Login Page**: Go to `http://localhost:5000/login`
2. **Test Credentials** (if created with `create_test_user.py`):
   - Email: `test@example.com`
   - Password: `test123`
3. **After Login**: You'll be redirected to `http://localhost:3000` (React dashboard)

### Create a Test User

```bash
python create_test_user.py
```

This will create a user with:
- Email: `test@example.com`
- Password: `test123`

## 📁 Project Structure

```
Jobs_Scraper/
├── frontend/                 # React frontend
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── hooks/           # Custom React hooks
│   │   ├── services/        # API services
│   │   └── types/           # TypeScript types
│   ├── package.json
│   └── vite.config.ts       # Vite configuration
├── webapp/                   # Flask backend
│   ├── __init__.py          # Flask app factory
│   ├── auth/                # Authentication routes
│   ├── jobs/                # Job management routes
│   └── models.py            # Database models
├── templates/                # Jinja2 templates (for auth pages)
│   └── auth/
│       ├── login.html
│       ├── register.html
│       └── profile.html
├── index.py                  # Flask application entry point
├── requirements.txt          # Python dependencies
├── start_backend.bat         # Windows start script
├── start_backend.ps1         # PowerShell start script
├── create_test_user.py       # Utility to create test user
├── update_webhook_url.py     # Utility to update webhook URL
├── switch_webhook.py         # Utility to switch between test/prod webhooks
└── README.md                 # This file
```

## 🔌 API Endpoints

All API endpoints require authentication (login first):

- `GET /api/stats` - Get dashboard statistics
- `GET /api/jobs` - Get all jobs
- `POST /api/update_app_status/<job_id>` - Update job status
- `POST /api/update_app_notes/<job_id>` - Update job notes
- `POST /api/generate_resume/<job_id>` - Generate resume (triggers multiple webhooks)
- `GET /api/download_resume/<file_id>` - Download resume
- `POST /api/upload_master_resume` - Upload master resume
- `GET /api/export_jobs` - Export jobs to CSV

## 🎨 Tech Stack

### Frontend
- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Utility-first CSS framework
- **Framer Motion** - Animation library
- **Lucide React** - Icon library

### Backend
- **Flask** - Python web framework
- **Flask-Login** - Session management
- **MongoDB** - Database (via PyMongo)
- **GridFS** - File storage for resumes

## 🐛 Troubleshooting

### Backend Issues

**Port 5000 already in use:**
```bash
# Change port in index.py
app.run(host='0.0.0.0', port=5000, debug=True)
```

**MongoDB connection error:**
- Check your MongoDB connection string in `webapp/__init__.py`
- Verify MongoDB Atlas whitelist includes your IP
- For cloud deployment, set `MONGODB_CONNECTION_STRING` environment variable
- Go to MongoDB Atlas → Network Access → Add IP Address (`0.0.0.0/0` for cloud)

**Authentication errors:**
- Make sure you're logged in at `http://localhost:5000/login`
- Check browser cookies are enabled
- Clear cookies and try logging in again

**500 Internal Server Error:**
- Usually means you're not logged in
- Log in at `http://localhost:5000/login` first
- Check Flask backend is running on port 5000

### Frontend Issues

**Port 3000 already in use:**
- Vite will automatically use the next available port (3001, 3002, etc.)
- Update the redirect in `webapp/jobs/routes.py` if using a different port

**API errors (500, 401, CORS):**
- Make sure Flask backend is running on port 5000
- Check browser console for specific error messages
- Verify you're logged in at `http://localhost:5000/login` first
- Ensure both servers are running simultaneously

**Node modules issues:**
- Delete `node_modules` and `package-lock.json`
- Run `npm install` again
- If using OneDrive, ensure `node_modules` is excluded (`.onedriveignore` file included)

### Database Issues

**"Database is not connected" error:**
1. Test connection: `python check_db_status.py`
2. Verify MongoDB Atlas Network Access includes your IP
3. For cloud: Add `0.0.0.0/0` to allow all IPs (or specific cloud IPs)
4. Check connection string in `webapp/__init__.py` or environment variable

**Connection timeout:**
- Check internet connection
- Verify firewall isn't blocking MongoDB (port 27017)
- For MongoDB Atlas, no firewall changes needed

## 📦 Building for Production

### Frontend

```bash
cd frontend
npm run build
```

The built files will be in `frontend/dist/`

### Backend

For production deployment, set environment variables:
- `SECRET_KEY` - Flask secret key for sessions
- `FRONTEND_URL` - URL where React frontend is hosted
- `MONGODB_CONNECTION_STRING` - MongoDB connection string (optional, defaults to hardcoded)
- `MONGODB_DATABASE_NAME` - Database name (default: "N8N")
- `MONGODB_COLLECTION_NAME` - Collection name (default: "Jobs_Collection")

## 🚀 Cloud Deployment

### Environment Variables

#### Backend:
- `SECRET_KEY` - Flask secret key (required)
- `FRONTEND_URL` - Frontend URL for CORS (e.g., `https://your-frontend.vercel.app`)
- `MONGODB_CONNECTION_STRING` - MongoDB connection string (optional)
- `MONGODB_DATABASE_NAME` - Database name (default: "N8N")
- `MONGODB_COLLECTION_NAME` - Collection name (default: "Jobs_Collection")

#### Frontend:
- `VITE_API_BASE_URL` - Backend API URL (if deployed separately)
- `VITE_BACKEND_URL` - Backend URL for login redirects
- `VITE_LOGIN_URL` - Login URL (defaults to BACKEND_URL/login)

### Deployment Platforms

**Vercel:**
- Backend: Use `vercel.json` (already configured)
- Frontend: Build command: `cd frontend && npm run build`, Output: `frontend/dist`
- Set environment variables in Project Settings

**Railway/Render:**
- Backend: Set as Web Service, configure environment variables
- Frontend: Set as Static Site, build command: `cd frontend && npm run build`

### MongoDB Atlas for Cloud

1. Go to MongoDB Atlas → **Network Access**
2. Add IP Address: `0.0.0.0/0` (allows all IPs - for testing)
3. Or add specific cloud platform IP ranges
4. Set `MONGODB_CONNECTION_STRING` environment variable in your cloud platform

### CORS Configuration

Backend automatically handles CORS based on `FRONTEND_URL`:
- Local: `FRONTEND_URL=http://localhost:3000`
- Production: `FRONTEND_URL=https://your-frontend.vercel.app`
- Allow All: `FRONTEND_URL=*` (not recommended)

## 🔗 n8n Webhook Configuration

The system supports multiple webhooks for resume generation. Configure webhook URLs in your profile:

1. Go to: `http://localhost:5000/profile`
2. Set **Webhook URL** field
3. Set **API Key** (optional) if your n8n webhook requires authentication

**Default webhooks** (configured in code):
- Production: `http://54.90.110.145:5678/webhook/resume-tailor`
- Local/Network: `http://192.168.1.199:5678/webhook/resume-tailor`

**Note:** Both webhooks are triggered when generating a resume. The first successful response is used.

**Utilities:**
- `python update_webhook_url.py <email> <webhook_url>` - Update webhook URL
- `python switch_webhook.py <email> <test|prod>` - Switch between test/production webhooks

## 📄 License

MIT

## 👥 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

**Note**: Make sure both the Flask backend (port 5000) and React frontend (port 3000) are running simultaneously for the application to work properly. Always log in at `http://localhost:5000/login` before accessing the React dashboard.

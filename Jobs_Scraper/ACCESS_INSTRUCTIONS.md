# How to Access the Application

**Open the frontend directly.** The backend (index.py) only provides the API; you use the app by running the frontend and opening it in the browser.

---

## Run locally

### 1. Terminal 1 – Backend (API)

From the project folder:

```powershell
cd "C:\Users\kunig\OneDrive\Documentos\N8N\MyAIAgents\Jobs_Scraper"

# Optional: use a virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Start the API server
python index.py
```

Leave this running. The API will be at http://localhost:5000.

### 2. Terminal 2 – Frontend (the app you open)

Open a **second** terminal:

```powershell
cd "C:\Users\kunig\OneDrive\Documentos\N8N\MyAIAgents\Jobs_Scraper\frontend"

npm install
npm run dev
```

### 3. Open the app in your browser

Open **http://localhost:3000** (the frontend). You’ll see the full dashboard (filters, stats, job table, Resume Settings, export, etc.).

Do **not** use http://localhost:5000 to use the app; that’s only the API. If you open 5000, you’ll get a message to run the frontend and open 3000.

---

## MongoDB

The app needs MongoDB for jobs. Set these if you use your own database:

- `MONGODB_CONNECTION_STRING`
- `MONGODB_DATABASE_NAME` (e.g. `N8N`)
- `MONGODB_COLLECTION_NAME` (e.g. `Jobs_Collection`)

---

## Quick reference

| What              | URL / Command                          |
|-------------------|----------------------------------------|
| **Open the app**  | **http://localhost:3000** (frontend)   |
| API (backend)     | http://localhost:5000 (for the frontend only) |
| Start frontend    | `cd frontend` then `npm run dev`       |
| Start backend     | `python index.py`                      |

The app is the frontend. Run it and open **http://localhost:3000**.

---

## Running on Vercel (one URL for app + API)

The project is set up so **one Vercel deployment** serves both the React app and the Python API.

1. **Connect the repo** to Vercel (e.g. from [vercel.com](https://vercel.com) → New Project → Import your Git repo).

2. **Root directory:** If the repo is **MyAIAgents** and the app lives in **Jobs_Scraper**, set **Root Directory** in Vercel to `Jobs_Scraper`. If the repo is just Jobs_Scraper, leave root as `.`

3. **Environment variables** (Vercel → Project → Settings → Environment Variables):
   - `MONGODB_CONNECTION_STRING` – your MongoDB Atlas (or other) connection string  
   - `MONGODB_DATABASE_NAME` (optional, default `N8N`)  
   - `MONGODB_COLLECTION_NAME` (optional, default `Jobs_Collection`)

4. **Deploy.** Vercel will:
   - Build the frontend (`frontend/` → `frontend/dist`)
   - Build the Python app (`index.py`)
   - Serve everything from one URL: the app at `/` and the API at `/api/*`

5. **Open the deployment URL** (e.g. `https://your-project.vercel.app`). You get the full dashboard; no need to run two processes. The frontend calls `/api/jobs` and `/api/stats` on the same host.

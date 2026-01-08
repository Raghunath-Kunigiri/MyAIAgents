# Vercel Deployment Guide

## Prerequisites

1. **Vercel Account**: Sign up at [vercel.com](https://vercel.com)
2. **Vercel CLI** (optional but recommended): `npm i -g vercel`
3. **GitHub/GitLab/Bitbucket Account** (for automatic deployments)

## Step 1: Prepare Your Code

Ensure your `index.py` file is set up correctly:

```python
from webapp import create_app

app = create_app()
```

The `vercel.json` file is already configured.

## Step 2: Environment Variables

You need to set these environment variables in Vercel:

### Required Variables:
- `SECRET_KEY`: A secret key for Flask sessions (generate a random string)
  - Example: `python -c "import secrets; print(secrets.token_hex(32))"`

### Optional Variables (if you want to change from hardcoded values):
- `MONGODB_CONNECTION_STRING`: Your MongoDB connection string
- `MONGODB_DATABASE_NAME`: Database name (default: "N8N")
- `MONGODB_COLLECTION_NAME`: Collection name (default: "Jobs_Collection")

## Step 3: Deploy via Vercel Dashboard

### Method 1: GitHub Integration (Recommended)

1. **Push your code to GitHub**:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin <your-github-repo-url>
   git push -u origin main
   ```

2. **Connect to Vercel**:
   - Go to [vercel.com/new](https://vercel.com/new)
   - Import your GitHub repository
   - Vercel will auto-detect it's a Python project

3. **Configure Settings**:
   - **Framework Preset**: Other
   - **Root Directory**: `./` (default)
   - **Build Command**: Leave empty (Vercel handles Python)
   - **Output Directory**: Leave empty
   - **Install Command**: Leave empty

4. **Add Environment Variables**:
   - Go to Project Settings → Environment Variables
   - Add `SECRET_KEY` with a secure random value
   - Add any other environment variables you need

5. **Deploy**:
   - Click "Deploy"
   - Wait for deployment to complete

### Method 2: Vercel CLI

1. **Install Vercel CLI**:
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

4. **Follow the prompts**:
   - Link to existing project or create new
   - Confirm settings

5. **Set Environment Variables**:
   ```bash
   vercel env add SECRET_KEY
   # Enter your secret key value
   ```

6. **Deploy to Production**:
   ```bash
   vercel --prod
   ```

## Step 4: Post-Deployment

1. **Verify Deployment**:
   - Visit your Vercel URL (e.g., `https://your-app.vercel.app`)
   - Test login/registration
   - Test job dashboard

2. **Configure Custom Domain** (Optional):
   - Go to Project Settings → Domains
   - Add your custom domain
   - Follow DNS configuration instructions

## Important Notes

### MongoDB Connection
- Your MongoDB Atlas cluster must allow connections from Vercel's IP addresses
- Go to MongoDB Atlas → Network Access → Add IP Address
- Add `0.0.0.0/0` (allow all IPs) for testing, or use Vercel's IP ranges for production

### Session Storage
- Vercel serverless functions use in-memory sessions by default
- For production, consider using:
  - MongoDB sessions (store session data in MongoDB)
  - Redis sessions
  - Cookie-based sessions with secure cookies

### File Upload Limits
- Vercel has a 4.5MB limit for serverless functions
- Large resume files might hit this limit
- Consider using external storage (S3, Cloudinary) for file uploads

### Cold Starts
- First request after inactivity may be slower (cold start)
- Vercel Pro plan reduces cold starts

## Troubleshooting

### Build Errors
- Check that all dependencies are in `requirements.txt`
- Ensure Python version is compatible (Vercel uses Python 3.9 by default)
- Check build logs in Vercel dashboard

### Runtime Errors
- Check function logs in Vercel dashboard
- Verify environment variables are set correctly
- Ensure MongoDB connection string is correct

### Session Issues
- Verify `SECRET_KEY` is set
- Check that cookies are enabled in browser
- For HTTPS-only sessions, ensure your app uses HTTPS

## Updating Your Deployment

### Automatic (GitHub Integration)
- Push to your main branch
- Vercel automatically redeploys

### Manual (CLI)
```bash
vercel --prod
```

## Need Help?

- [Vercel Documentation](https://vercel.com/docs)
- [Vercel Python Runtime](https://vercel.com/docs/concepts/functions/serverless-functions/runtimes/python)
- [Flask on Vercel](https://vercel.com/guides/deploying-flask-with-vercel)

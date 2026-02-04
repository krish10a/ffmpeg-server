# How to Deploy Fastest

I have prepared the code for 1-click deployment on **Render.com** (easiest free tier) or **Railway.app** (fastest/most reliable).

## Step 1: Upload code to GitHub
You need to put the `ffmpeg_server` folder into a GitHub repository.

1.  Create a new repository on GitHub (e.g., `ffmpeg-api`).
2.  Open your terminal in `c:\Users\ASUS\Desktop\shorts_final\ffmpeg_server`.
3.  Run these commands:
    ```powershell
    git init
    git add .
    git commit -m "Initial commit"
    git branch -M main
    git remote add origin https://github.com/<YOUR_USERNAME>/ffmpeg-api.git
    git push -u origin main
    ```

## Step 2: Deploy

### Option A: Render (Free Tier Available)
1.  Go to [dashboard.render.com](https://dashboard.render.com).
2.  Click **New +** -> **Web Service**.
3.  Select "Build and deploy from a Git repository".
4.  Connect your `ffmpeg-api` repo.
5.  Render will auto-detect the `Dockerfile` or `render.yaml`.
6.  Click **Create Web Service**.
    *   *Note: Free tier spins down after inactivity (slow first request).*

### Option B: Railway (Fastest)
1.  Go to [railway.app](https://railway.app).
2.  Click **New Project** -> **Deploy from GitHub repo**.
3.  Select your `ffmpeg-api` repo.
4.  Railway will detect the `railway.json` and `Dockerfile`.
5.  Click **Deploy Now**.
    *   *Note: Very fast, usually ready in < 2 minutes.*

## Step 3: Update n8n
Once deployed, copy your new URL (e.g., `https://ffmpeg-api.onrender.com`) and update `antig.json` nodes:
*   Merge Node: `YOUR_URL/v1/run-ffmpeg`
*   Poll Node: `YOUR_URL/v1/jobs/{{id}}`
*   Delete Node: `YOUR_URL/v1/commands/{{id}}/files`

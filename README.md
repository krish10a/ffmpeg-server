# Self-Hosted FFmpeg API Server

A lightweight, self-hosted replacement for the Rendi API. Accepts FFmpeg commands via HTTP, processes them locally, and serves the results.

## Features
- **Drop-in Compatible**: API structure mimics Rendi's `run-ffmpeg-command` for easy migration.
- **Async Processing**: Jobs are run in the background; status can be polled.
- **Dockerized**: Easy to deploy on Render, Railway, or any VPS.

## API Endpoints

### 1. Run Command
`POST /v1/run-ffmpeg`

**Body:**
```json
{
  "ffmpeg_command": "-i {{in_1}} -filter_complex ... {{out_1}}",
  "input_files": {
    "in_1": "https://example.com/video.mp4"
  },
  "output_files": {
    "out_1": "output.mp4"
  }
}
```

**Response:**
```json
{
  "command_id": "uuid-string"
}
```

### 2. Poll Status
`GET /v1/jobs/{command_id}`

**Response:**
```json
{
  "command_id": "...",
  "status": "completed",
  "output_files": {
     "out_1": "https://your-domain.com/v1/downloads/{command_id}/output.mp4"
  }
}
```

### 3. Download File
`GET /v1/downloads/{command_id}/{filename}`

## Local Development
1. Install FFmpeg.
2. `pip install -r requirements.txt`
3. `uvicorn app.main:app --reload`

## Deployment (Docker)
1. Build: `docker build -t ffmpeg-server .`
2. Run: `docker run -p 8000:8000 ffmpeg-server`

### Free/Cheap Hosting Options
1. **Render.com**: Connect repo, deploy as "Web Service", choose "Docker".
2. **Railway.app**: Connect repo, it detects Dockerfile automatically.

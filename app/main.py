from fastapi import FastAPI, BackgroundTasks, HTTPException, Request
from fastapi.responses import FileResponse
import os
import uuid
import logging
from contextlib import asynccontextmanager

from .models import FFmpegRequest, JobResponse, JobStatus
from .tasks import process_ffmpeg_job
from .utils import TEMP_OUTPUTS_DIR
from . import db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    db.init_db()
    yield

app = FastAPI(title="Self-Hosted FFmpeg API", lifespan=lifespan)

@app.get("/")
def read_root():
    return {"message": "FFmpeg API Server is running (SQLite Persistence)."}

@app.post("/v1/run-ffmpeg", response_model=JobResponse)
async def run_ffmpeg(request: FFmpegRequest, background_tasks: BackgroundTasks, req: Request):
    job_id = str(uuid.uuid4())
    base_url = str(req.base_url).rstrip("/")
    
    # 1. Persist 'pending' status immediately
    db.create_job(job_id)
    
    # 2. Add background task
    background_tasks.add_task(process_ffmpeg_job, job_id, request, base_url)
    
    return JobResponse(command_id=job_id)

@app.post("/v1/commands", response_model=JobResponse)
async def run_ffmpeg_legacy(request: FFmpegRequest, background_tasks: BackgroundTasks, req: Request):
    return await run_ffmpeg(request, background_tasks, req)

@app.get("/v1/jobs/{job_id}", response_model=JobStatus)
def get_job_status(job_id: str):
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return JobStatus(**job)

@app.get("/v1/commands/{job_id}", response_model=JobStatus)
def get_job_status_legacy(job_id: str):
    return get_job_status(job_id)

@app.get("/v1/downloads/{job_id}/{filename}")
def download_file(job_id: str, filename: str):
    file_path = os.path.join(TEMP_OUTPUTS_DIR, job_id, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)

@app.delete("/v1/commands/{job_id}/files")
def delete_job_files(job_id: str):
    # Optional: cleanup can be implemented here
    # For now, we rely on checking job existence or just returning success
    # Removing from DB not strictly required for this logic, but good practice
    return {"status": "deleted"}

from fastapi import FastAPI, BackgroundTasks, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import os
import uuid
import logging
from .models import FFmpegRequest, JobResponse, JobStatus
from .tasks import process_ffmpeg_job, JOB_STORE
from .utils import TEMP_OUTPUTS_DIR

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Self-Hosted FFmpeg API")

@app.get("/")
def read_root():
    return {"message": "FFmpeg API Server is running. Use POST /v1/run-ffmpeg to start a job."}

@app.post("/v1/run-ffmpeg", response_model=JobResponse)
async def run_ffmpeg(request: FFmpegRequest, background_tasks: BackgroundTasks, req: Request):
    job_id = str(uuid.uuid4())
    
    # Construct base URL for download links
    base_url = str(req.base_url).rstrip("/")
    
    # Start background task
    background_tasks.add_task(process_ffmpeg_job, job_id, request, base_url)
    
    return JobResponse(command_id=job_id)

@app.post("/v1/commands", response_model=JobResponse)
async def run_ffmpeg_legacy(request: FFmpegRequest, background_tasks: BackgroundTasks, req: Request):
    """Alias for /v1/run-ffmpeg to match some Rendi patterns if needed"""
    return await run_ffmpeg(request, background_tasks, req)

@app.get("/v1/jobs/{job_id}", response_model=JobStatus)
def get_job_status(job_id: str):
    if job_id not in JOB_STORE:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job_data = JOB_STORE[job_id]
    return JobStatus(
        command_id=job_id,
        status=job_data["status"],
        output_files=job_data.get("output_files"),
        error=job_data.get("error")
    )

@app.get("/v1/commands/{job_id}", response_model=JobStatus)
def get_job_status_legacy(job_id: str):
    """Alias for /v1/jobs/{job_id}"""
    return get_job_status(job_id)

@app.get("/v1/downloads/{job_id}/{filename}")
def download_file(job_id: str, filename: str):
    file_path = os.path.join(TEMP_OUTPUTS_DIR, job_id, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)

# Cleanup endpoint (Optional, manual trigger)
@app.delete("/v1/commands/{job_id}/files")
def delete_job_files(job_id: str):
    if job_id not in JOB_STORE:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Just a stub for now to match Rendi API signature
    # In a real implementation this would rm -rf the dirs
    return {"status": "deleted"}

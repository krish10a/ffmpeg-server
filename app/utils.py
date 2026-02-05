import os
import aiofiles
import httpx
import uuid
import logging

logger = logging.getLogger(__name__)

TEMP_DOWNLOADS_DIR = os.path.abspath("temp_downloads")
TEMP_OUTPUTS_DIR = os.path.abspath("temp_outputs")

# Ensure dirs exist (also handled in Dockerfile, but good for local dev)
os.makedirs(TEMP_DOWNLOADS_DIR, exist_ok=True)
os.makedirs(TEMP_OUTPUTS_DIR, exist_ok=True)

async def download_file(url: str, dest_path: str):
    logger.info(f"Downloading {url} to {dest_path}")
    async with httpx.AsyncClient() as client:
        async with client.stream('GET', url, follow_redirects=True) as response:
            if response.status_code != 200:
                raise Exception(f"Failed to download {url}: Status {response.status_code}")
            async with aiofiles.open(dest_path, 'wb') as f:
                async for chunk in response.aiter_bytes():
                    await f.write(chunk)

def get_job_dirs(job_id: str):
    """Returns (download_dir, output_dir) unique for this job"""
    d_dir = os.path.join(TEMP_DOWNLOADS_DIR, job_id)
    o_dir = os.path.join(TEMP_OUTPUTS_DIR, job_id)
    return d_dir, o_dir

def setup_job_dirs(job_id: str):
    d_dir, o_dir = get_job_dirs(job_id)
    os.makedirs(d_dir, exist_ok=True)
    os.makedirs(o_dir, exist_ok=True)
    return d_dir, o_dir

def cleanup_job_files(job_id: str):
    # Optional: cleanup logic to be called after some time or on execution end
    pass

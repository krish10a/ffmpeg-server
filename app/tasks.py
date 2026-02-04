import asyncio
import subprocess
import os
import logging
from typing import Dict
from .models import FFmpegRequest
from .utils import setup_job_dirs, download_file, get_job_dirs

logger = logging.getLogger(__name__)

# Simple in-memory job store
# job_id -> { "status": str, "error": str, "output_files": dict }
JOB_STORE = {}

async def process_ffmpeg_job(job_id: str, request: FFmpegRequest, base_url: str):
    logger.info(f"Starting job {job_id}")
    JOB_STORE[job_id] = {"status": "processing"}
    
    download_dir, output_dir = setup_job_dirs(job_id)
    
    try:
        # 1. Download input files
        input_paths = {}
        download_tasks = []
        for alias, url in request.input_files.items():
            # Basic sanitization for filename
            filename = f"{alias}_{os.path.basename(url.split('?')[0])}"
            if not filename.endswith(('.mp4', '.mov', '.avi', '.mp3', '.mkv')):
                 filename += ".mp4" # Default extension if missing
            
            file_path = os.path.join(download_dir, filename)
            input_paths[alias] = file_path
            download_tasks.append(download_file(url, file_path))
        
        await asyncio.gather(*download_tasks)
        logger.info(f"Job {job_id}: Inputs downloaded")

        # 2. Build FFmpeg command
        # Replace {{alias}} or {{ alias }} with local paths
        # Also need to replace {{alias}} or {{ alias }} for outputs with output paths
        cmd = request.ffmpeg_command
        
        # Replace inputs
        for alias, path in input_paths.items():
            # Rendi uses {{alias}}
            cmd = cmd.replace(f"{{{{{alias}}}}}", path)
            cmd = cmd.replace(f"{{{{ {alias} }}}}", path)
        
        # Replace outputs
        final_output_map = {} # alias -> server_url
        for alias, filename in request.output_files.items():
            out_path = os.path.join(output_dir, filename)
            cmd = cmd.replace(f"{{{{{alias}}}}}", out_path)
            cmd = cmd.replace(f"{{{{ {alias} }}}}", out_path)
            # Store relative path/filename to construct URL later
            final_output_map[alias] = filename

        # 3. Execute FFmpeg
        # command string to list
        import shlex
        args = shlex.split(cmd)
        
        logger.info(f"Job {job_id}: Running command: {cmd}")
        
        process = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            error_msg = stderr.decode()
            logger.error(f"Job {job_id} failed: {error_msg}")
            JOB_STORE[job_id] = {"status": "failed", "error": error_msg}
            return

        logger.info(f"Job {job_id}: Success")
        
        # 4. Construct Output URLs
        # Format: base_url/v1/downloads/{job_id}/{filename}
        output_urls = {}
        for alias, filename in final_output_map.items():
            output_urls[alias] = f"{base_url}/v1/downloads/{job_id}/{filename}"
            
        JOB_STORE[job_id] = {
            "status": "completed",
            "output_files": output_urls
        }

    except Exception as e:
        logger.exception(f"Job {job_id} crashed")
        JOB_STORE[job_id] = {"status": "failed", "error": str(e)}

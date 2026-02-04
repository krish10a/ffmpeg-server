import asyncio
import os
import logging
import shlex
from .models import FFmpegRequest
from .utils import setup_job_dirs, download_file
from . import db

logger = logging.getLogger(__name__)

async def process_ffmpeg_job(job_id: str, request: FFmpegRequest, base_url: str):
    logger.info(f"Starting job {job_id}")
    
    # Update status to processing
    db.update_job(job_id, "processing")
    
    download_dir, output_dir = setup_job_dirs(job_id)
    
    try:
        # 1. Download input files
        input_paths = {}
        download_tasks = []
        for alias, url in request.input_files.items():
            filename = f"{alias}_{os.path.basename(url.split('?')[0])}"
            if not filename.endswith(('.mp4', '.mov', '.avi', '.mp3', '.mkv')):
                 filename += ".mp4"
            
            file_path = os.path.join(download_dir, filename)
            input_paths[alias] = file_path
            download_tasks.append(download_file(url, file_path))
        
        await asyncio.gather(*download_tasks)
        logger.info(f"Job {job_id}: Inputs downloaded")

        # 2. Build FFmpeg command
        cmd = request.ffmpeg_command
        
        # Replace inputs
        for alias, path in input_paths.items():
            cmd = cmd.replace(f"{{{{{alias}}}}}", path)
            cmd = cmd.replace(f"{{{{ {alias} }}}}", path)
        
        # Replace outputs
        final_output_map = {} 
        for alias, filename in request.output_files.items():
            out_path = os.path.join(output_dir, filename)
            cmd = cmd.replace(f"{{{{{alias}}}}}", out_path)
            cmd = cmd.replace(f"{{{{ {alias} }}}}", out_path)
            final_output_map[alias] = filename

        # 3. Execute FFmpeg
        # Optimized for stability (low RAM/CPU) to prevent Server OOM crashes
        # Added: -preset ultrafast -threads 2
        cmd = cmd.replace("-c:v libx264", "-c:v libx264 -preset ultrafast -threads 2")
        
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
            db.update_job(job_id, "failed", error=error_msg)
            return

        logger.info(f"Job {job_id}: Success")
        
        # 4. Construct Output URLs
        output_urls = {}
        for alias, filename in final_output_map.items():
            output_urls[alias] = f"{base_url}/v1/downloads/{job_id}/{filename}"
            
        db.update_job(job_id, "completed", output_files=output_urls)

    except Exception as e:
        logger.exception(f"Job {job_id} crashed")
        db.update_job(job_id, "failed", error=str(e))

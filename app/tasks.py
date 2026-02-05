import asyncio
import os
import logging
import shlex
import aiofiles
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

        # 2. Build Concat List (Concat Demuxer - Low RAM)
        # Create a text file listing all inputs for sequential processing
        list_path = os.path.join(download_dir, "inputs.txt")
        sorted_inputs = sorted(input_paths.items()) # Ensure 0,1,2,3 order if keys are input_0 etc.
        
        async with aiofiles.open(list_path, 'w') as f:
            for alias, path in sorted_inputs:
                # Escape single quotes for ffmpeg concat file
                safe_path = path.replace("'", "'\\''")
                await f.write(f"file '{safe_path}'\n")
        
        # 3. Execute FFmpeg (Concat Mode)
        # Using -f concat is much lighter on RAM than complex filters
        # -safe 0: Allow absolute paths
        # -c:v libx264 -preset ultrafast: Re-encode quickly to ensure uniform output
        output_filename = request.output_files.get("output_0", "merged.mp4")
        output_path = os.path.join(output_dir, output_filename)
        
        cmd = (
            f"ffmpeg -fflags +genpts -f concat -safe 0 -i \"{list_path}\" "
            f"-c:v libx264 -preset veryfast -crf 28 -r 30 -threads 2 "
            f"-pix_fmt yuv420p -a:c aac -movflags +faststart -max_interleave_delta 0 -y \"{output_path}\""
        )
        
        # Helper: Map the output alias to the filename we just used
        final_output_map = {"output_0": output_filename}
        
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

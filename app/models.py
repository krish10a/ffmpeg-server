from pydantic import BaseModel
from typing import Dict, Optional

class FFmpegRequest(BaseModel):
    ffmpeg_command: str
    input_files: Dict[str, str]  # alias -> url
    output_files: Dict[str, str] # alias -> filename e.g. "out_1": "output.mp4"
    webhook_url: Optional[str] = None

class JobResponse(BaseModel):
    command_id: str

class JobStatus(BaseModel):
    command_id: str
    status: str  # pending, processing, completed, failed
    output_files: Optional[Dict[str, str]] = None # alias -> download_url
    error: Optional[str] = None

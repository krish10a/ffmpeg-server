import sqlite3
import json
import os
from typing import Optional, Dict

DB_PATH = "/code/jobs.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            job_id TEXT PRIMARY KEY,
            status TEXT NOT NULL,
            output_files TEXT,
            error TEXT
        )
    ''')
    conn.commit()
    conn.close()

def create_job(job_id: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO jobs (job_id, status) VALUES (?, ?)', (job_id, "pending"))
    conn.commit()
    conn.close()

def update_job(job_id: str, status: str, output_files: Optional[Dict[str, str]] = None, error: Optional[str] = None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    outputs_json = json.dumps(output_files) if output_files else None
    
    c.execute('''
        UPDATE jobs 
        SET status = ?, output_files = ?, error = ?
        WHERE job_id = ?
    ''', (status, outputs_json, error, job_id))
    conn.commit()
    conn.close()

def get_job(job_id: str) -> Optional[Dict]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM jobs WHERE job_id = ?', (job_id,))
    row = c.fetchone()
    conn.close()
    
    if row:
        return {
            "command_id": row["job_id"],
            "status": row["status"],
            "output_files": json.loads(row["output_files"]) if row["output_files"] else None,
            "error": row["error"]
        }
    return None

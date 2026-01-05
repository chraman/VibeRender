"""
Utility script to reset failed jobs back to pending status.
Use this if you want to retry jobs that failed due to API limits.

Usage:
    python reset_failed_jobs.py [job_id]
    
    If job_id is provided, only that job will be reset.
    If no job_id is provided, all failed jobs will be reset.
"""

import sys
import psycopg2
from config import Config

DB_CONFIG = {
    'host': Config.DB_HOST,
    'port': Config.DB_PORT,
    'database': Config.DB_NAME,
    'user': Config.DB_USER,
    'password': Config.DB_PASSWORD,
}

def reset_failed_jobs(job_id=None):
    """Reset failed jobs back to pending status."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        if job_id:
            # Reset specific job
            cursor.execute(
                "UPDATE jobs SET status = 'pending', updated_at = NOW() WHERE id = %s AND status = 'failed",
                (job_id,)
            )
            if cursor.rowcount > 0:
                print(f'✅ Reset job {job_id} from failed to pending')
            else:
                print(f'⚠️  Job {job_id} not found or not in failed status')
        else:
            # Reset all failed jobs
            cursor.execute(
                "UPDATE jobs SET status = 'pending', updated_at = NOW() WHERE status = 'failed'"
            )
            count = cursor.rowcount
            if count > 0:
                print(f'✅ Reset {count} failed job(s) back to pending')
            else:
                print('ℹ️  No failed jobs to reset')
        
        conn.commit()
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f'❌ Error: {e}')
        sys.exit(1)

if __name__ == '__main__':
    job_id = int(sys.argv[1]) if len(sys.argv) > 1 else None
    reset_failed_jobs(job_id)


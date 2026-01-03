"""
VibeRender Video Worker
Polls the PostgreSQL database for new video generation jobs and processes them.
"""

import time
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, Any
from config import Config
from asset_generator import generate_assets

# Database connection configuration from Config
DB_CONFIG = {
    'host': Config.DB_HOST,
    'port': Config.DB_PORT,
    'database': Config.DB_NAME,
    'user': Config.DB_USER,
    'password': Config.DB_PASSWORD,
}

# Polling interval in seconds
POLL_INTERVAL = Config.POLL_INTERVAL

# Track the last processed job ID to avoid reprocessing
last_processed_id = 0


def get_db_connection():
    """
    Create and return a database connection.
    Uses context manager pattern to ensure proper cleanup.
    """
    return psycopg2.connect(**DB_CONFIG)


def get_pending_jobs(cursor: RealDictCursor, last_id: int) -> list[Dict[str, Any]]:
    """
    Fetch new pending jobs from the database that haven't been processed yet.
    
    Args:
        cursor: Database cursor with RealDictCursor for dict-like results
        last_id: The last processed job ID to avoid reprocessing
        
    Returns:
        List of job dictionaries
    """
    query = """
        SELECT id, topic, status, created_at
        FROM jobs
        WHERE id > %s AND status = 'pending'
        ORDER BY id ASC
        LIMIT 10
    """
    cursor.execute(query, (last_id,))
    return cursor.fetchall()


def update_job_status(cursor: RealDictCursor, job_id: int, status: str):
    """
    Update the status of a job in the database.
    
    Args:
        cursor: Database cursor
        job_id: The ID of the job to update
        status: New status ('processing', 'completed', 'failed')
    """
    query = """
        UPDATE jobs
        SET status = %s, updated_at = NOW()
        WHERE id = %s
    """
    cursor.execute(query, (status, job_id))


def process_job(job: Dict[str, Any], cursor: RealDictCursor):
    """
    Process a single video generation job.
    Generates script and audio assets using OpenAI and ElevenLabs.
    
    Args:
        job: Job dictionary with id, topic, status, created_at
        cursor: Database cursor for updating job status
        
    Raises:
        Exception: If asset generation fails
    """
    job_id = job['id']
    topic = job['topic']
    
    print(f'\n🎬 Processing video for: {topic} (Job ID: {job_id})')
    
    # Update job status to 'processing'
    update_job_status(cursor, job_id, 'processing')
    
    try:
        # Generate assets (script and audio)
        assets = generate_assets(job_id, topic)
        
        print(f'  📦 Assets generated:')
        print(f'     Script: {assets["script_path"]}')
        print(f'     Audio: {assets["audio_path"]}')
        
        # TODO: Add video rendering logic here using the generated assets
        # For now, we mark the job as completed after assets are generated
        
        # Update job status to 'completed'
        update_job_status(cursor, job_id, 'completed')
        print(f'  ✅ Completed processing job {job_id} for topic: {topic}')
        
    except Exception as e:
        print(f'  ❌ Error generating assets for job {job_id}: {e}')
        # Update job status to 'failed'
        update_job_status(cursor, job_id, 'failed')
        raise


def main():
    """
    Main polling loop that continuously checks for new jobs.
    """
    global last_processed_id
    
    # Validate configuration before starting
    if not Config.validate():
        print('\n❌ Configuration validation failed. Please set required API keys.')
        print('   Set OPENAI_API_KEY and ELEVENLABS_API_KEY as environment variables.')
        return
    
    print('=' * 60)
    print('VibeRender Video Worker started')
    print('=' * 60)
    print(f'Polling database every {POLL_INTERVAL} seconds...')
    print(f'Database: {DB_CONFIG["database"]}@{DB_CONFIG["host"]}:{DB_CONFIG["port"]}')
    print(f'Assets directory: {Config.TEMP_ASSETS_DIR}')
    print(f'Last processed job ID: {last_processed_id}')
    print('Press Ctrl+C to stop\n')
    
    poll_count = 0
    
    try:
        while True:
            poll_count += 1
            current_time = time.strftime('%Y-%m-%d %H:%M:%S')
            
            # Use context manager to ensure connection is properly closed
            with get_db_connection() as conn:
                # Use RealDictCursor to get results as dictionaries
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    # Fetch pending jobs
                    jobs = get_pending_jobs(cursor, last_processed_id)
                    
                    if jobs:
                        print(f'\n[{current_time}] Poll #{poll_count}: Found {len(jobs)} new job(s)')
                        
                        # Process each job
                        for job in jobs:
                            try:
                                process_job(job, cursor)
                                # Update last processed ID
                                last_processed_id = max(last_processed_id, job['id'])
                            except Exception as e:
                                print(f'❌ Error processing job {job["id"]}: {e}')
                                # Mark job as failed
                                try:
                                    update_job_status(cursor, job['id'], 'failed')
                                except:
                                    pass
                        
                        # Commit all changes
                        conn.commit()
                    else:
                        # Show polling activity every 10 polls to indicate it's working
                        if poll_count % 10 == 0:
                            print(f'[{current_time}] Poll #{poll_count}: No new jobs (last processed: {last_processed_id})')
                        
                        # No new jobs, just wait
                        time.sleep(POLL_INTERVAL)
                        continue
                        
            # Small delay before next poll
            time.sleep(POLL_INTERVAL)
            
    except KeyboardInterrupt:
        print('\n\nShutting down worker...')
    except Exception as e:
        print(f'\n\nFatal error: {e}')
        raise


if __name__ == '__main__':
    main()


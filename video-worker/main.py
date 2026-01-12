"""
VibeRender Video Worker
Polls the PostgreSQL database for new video generation jobs and processes them.
"""

import time
import logging
import sys
import os
import pathlib
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, Any
from config import Config
from asset_generator import generate_assets
from video_renderer import render_video
from utils import mask_api_key

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

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

# Test mode flag - when True, uses test assets instead of generating new ones
TEST_MODE = False


def get_db_connection():
    """
    Create and return a database connection.
    Uses context manager pattern to ensure proper cleanup.
    """
    return psycopg2.connect(**DB_CONFIG)


def get_all_jobs_summary(cursor: RealDictCursor) -> Dict[str, Any]:
    """
    Get aggregated job counts by status (debugging/monitoring only).
    """
    query = """
        SELECT
            status,
            COUNT(*) AS job_count
        FROM jobs
        GROUP BY status
    """
    cursor.execute(query)
    rows = cursor.fetchall()

    summary = {}
    for row in rows:
        summary[row["status"]] = {
            "count": row["job_count"]
        }

    return summary


def get_pending_jobs(cursor: RealDictCursor) -> list[Dict[str, Any]]:
    """
    Fetch pending jobs with channel context.
    Uses row-level locking to avoid double processing.
    """
    query = """
        SELECT
            j.id,
            j.topic,
            j.video_theme,
            j.emotional_goal,
            j.pacing,
            j.status,
            j.created_at,
            j.channel_id,
            c.name AS channel_name,
            c.category,
            c.sub_niche
        FROM jobs j
        JOIN channels c ON c.id = j.channel_id
        WHERE j.status = 'pending'
        ORDER BY j.created_at ASC
        LIMIT 5
        FOR UPDATE SKIP LOCKED
    """
    cursor.execute(query)
    return cursor.fetchall()


def update_job_status(cursor: RealDictCursor, job_id: str, status: str):
    """
    Update job status safely.
    """
    cursor.execute(
        """
        UPDATE jobs
        SET status = %s,
            updated_at = NOW()
        WHERE id = %s
        """,
        (status, job_id)
    )


def process_job(job: Dict[str, Any], cursor: RealDictCursor):
    """
    Process a single video generation job.
    Generates script and audio assets using Google Gemini and ElevenLabs.
    
    Args:
        job: Job dictionary with id, topic, status, created_at
        cursor: Database cursor for updating job status
        
    Raises:
        Exception: If asset generation fails
    """
    job_id = job['id']
    topic = job['topic']
    created_at = job.get('created_at', 'unknown')
    
    logger.info("=" * 60)
    logger.info("🎬 STARTING JOB PROCESSING")
    logger.info(f"   Job ID: {job_id}")
    logger.info(f"   Topic: {job['topic']}")
    logger.info(f"   Channel: {job['channel_name']} ({job['category']} / {job['sub_niche']})")
    logger.info(f"   Created: {job.get('created_at')}")
    logger.info("=" * 60)
    
    # Update job status to 'processing'
    update_job_status(cursor, job_id, 'processing')
    cursor.connection.commit()
    logger.info(f'✅ Job {job_id} status updated to: processing')
    
    try:
        start_time = time.time()
        
        # Check if we're in test mode
        if TEST_MODE:
            logger.info('🧪 TEST_MODE enabled - using test assets')
            
            # Test assets directory
            test_dir = pathlib.Path('temp_assets') / 'test'
            test_dir.mkdir(parents=True, exist_ok=True)
            
            # Read script from file
            script_path = test_dir / 'narrator_only.txt'
            if not script_path.exists():
                raise FileNotFoundError(f'Test script not found: {script_path}')
            
            with open(script_path, 'r', encoding='utf-8') as f:
                script_text = f.read().strip()
            
            # Get audio file
            audio_path = test_dir / 'audio.mp3'
            if not audio_path.exists():
                raise FileNotFoundError(f'Test audio not found: {audio_path}')
            audio_path = str(audio_path)
            
            # Find all image and video files in test directory
            # Supported image formats
            image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
            # Supported video formats
            video_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.webm']
            
            media_paths = []
            for file_path in test_dir.iterdir():
                if file_path.is_file():
                    ext = file_path.suffix.lower()
                    if ext in image_extensions or ext in video_extensions:
                        # Skip the audio file if it has a video extension
                        if file_path.name != 'audio.mp3':
                            media_paths.append(str(file_path))
            
            # Sort media paths for consistent ordering
            media_paths.sort()
            
            if not media_paths:
                raise FileNotFoundError(f'No image or video files found in {test_dir}')
            
            logger.info(f'   Using test script: {script_path} ({len(script_text)} chars)')
            logger.info(f'   Using test audio: {audio_path}')
            logger.info(f'   Using test media: {len(media_paths)} file(s)')
            for i, media_path in enumerate(media_paths, 1):
                logger.info(f'      {i}. {os.path.basename(media_path)}')
        else:
            # Generate assets (script, audio, and images)
            logger.info(f'📦 Starting asset generation for job {job_id}...')
            
            assets = generate_assets(job_id, job)
            
            elapsed_time = time.time() - start_time
            logger.info(f'✅ Asset generation completed in {elapsed_time:.2f} seconds')
            logger.info(f'   Script JSON: {assets["script_path"]}')
            logger.info(f'   Narration: {assets["narration_path"]}')
            logger.info(f'   Audio: {assets["audio_path"]}')
            logger.info(f'   Images: {len(assets.get("image_paths", []))} image(s)')
            
            # Read narration text from narrator_only.txt (for video rendering)
            with open(assets['narration_path'], 'r', encoding='utf-8') as f:
                script_text = f.read()
            
            audio_path = assets['audio_path']
            image_paths = assets.get('image_paths', [])
        
        # Render video from assets
        logger.info(f'🎬 Rendering video from assets...')
        video_start_time = time.time()
        
        # Create output video path
        job_dir = pathlib.Path(Config.TEMP_ASSETS_DIR) / str(job_id)
        job_dir.mkdir(exist_ok=True)
        video_output_path = str(job_dir / 'video.mp4')
        
        # Render the video
        # Use media_paths in test mode, image_paths in normal mode
        render_media_paths = media_paths if TEST_MODE else image_paths
        render_video(script_text, audio_path, render_media_paths, video_output_path)
        
        video_elapsed = time.time() - video_start_time
        logger.info(f'✅ Video rendering completed in {video_elapsed:.2f} seconds')
        logger.info(f'   Video output: {video_output_path}')
        
        total_time = time.time() - start_time
        
        # Update job status to 'completed'
        update_job_status(cursor, job_id, 'completed')
        logger.info('=' * 60)
        logger.info(f'✅ JOB {job_id} COMPLETED SUCCESSFULLY')
        logger.info(f'   Topic: {topic}')
        logger.info(f'   Total time: {total_time:.2f} seconds')
        logger.info(f'   Video: {video_output_path}')
        logger.info('=' * 60)
        
    except Exception as e:
        logger.error('=' * 60)
        logger.error(f'❌ JOB {job_id} FAILED')
        logger.error(f'   Topic: {topic}')
        logger.error(f'   Error: {str(e)}')
        logger.error(f'   Error type: {type(e).__name__}')
        logger.error('=' * 60)
        # Update job status to 'failed'
        update_job_status(cursor, job_id, 'failed')
        raise


def main():
    """
    Main polling loop that continuously checks for new jobs.
    """
    
    # Validate configuration before starting
    logger.info('🔍 Validating configuration...')
    
    # Log API keys (masked for security)
    logger.info('🔑 API Keys Status:')
    if Config.GEMINI_API_KEY:
        logger.info(f'   GEMINI_API_KEY: {mask_api_key(Config.GEMINI_API_KEY)} (length: {len(Config.GEMINI_API_KEY)})')
    else:
        logger.warning('   GEMINI_API_KEY: ❌ NOT SET')
    
    if Config.ELEVENLABS_API_KEY:
        logger.info(f'   ELEVENLABS_API_KEY: {mask_api_key(Config.ELEVENLABS_API_KEY)} (length: {len(Config.ELEVENLABS_API_KEY)})')
    else:
        logger.warning('   ELEVENLABS_API_KEY: ❌ NOT SET')
    
    if not Config.validate():
        logger.error('❌ Configuration validation failed. Please set required API keys.')
        logger.error('   Set GEMINI_API_KEY and ELEVENLABS_API_KEY as environment variables.')
        return
    
    logger.info('✅ Configuration validated successfully')
    
    # Check database connection and get initial job summary
    try:
        logger.info('🔍 Checking database connection and job status...')
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                summary = get_all_jobs_summary(cursor)
                if summary:
                    logger.info('📊 Current database job status:')
                    for status, info in summary.items():
                        logger.info(f'   {status}: {info["count"]} job(s) (IDs: {info["min_id"]}-{info["max_id"]})')
                else:
                    logger.info('📊 No jobs found in database')
    except Exception as e:
        logger.warning(f'⚠️  Could not check database status: {e}')
    
    logger.info('=' * 60)
    logger.info('🚀 VibeRender Video Worker STARTED')
    logger.info('=' * 60)
    logger.info(f'📊 Configuration:')
    logger.info(f'   Polling interval: {POLL_INTERVAL} seconds')
    logger.info(f'   Database: {DB_CONFIG["database"]}@{DB_CONFIG["host"]}:{DB_CONFIG["port"]}')
    logger.info(f'   Assets directory: {Config.TEMP_ASSETS_DIR}')
    logger.info('=' * 60)
    logger.info('⏳ Starting polling loop...')
    logger.info('   Press Ctrl+C to stop\n')
    
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
                    jobs = get_pending_jobs(cursor)
                    
                    if jobs:
                        logger.info(f'\n🔔 Poll #{poll_count} [{current_time}]: Found {len(jobs)} new job(s)')
                        
                        # Process each job
                        for job in jobs:
                            try:
                                process_job(job, cursor)
                            except Exception as e:
                                logger.error(f'❌ Error processing job {job["id"]}: {e}', exc_info=True)
                                # Mark job as failed
                                try:
                                    update_job_status(cursor, job['id'], 'failed')
                                except Exception as update_error:
                                    logger.error(f'❌ Failed to update job {job["id"]} status: {update_error}')
                        
                        # Commit all changes
                        conn.commit()
                        logger.debug('✅ Database transaction committed')
                    else:
                        # Show polling activity every 10 polls to indicate it's working
                        if poll_count % 10 == 0:
                            # Every 10 polls, show database summary for debugging
                            try:
                                summary = get_all_jobs_summary(cursor)
                                if summary:
                                    pending = summary.get('pending', {})
                                    if pending.get('count', 0) > 0:
                                        logger.warning(f'   ⚠️  Note: {pending["count"]} pending job(s) exist but are not being processed')
                            except:
                                pass
                        else:
                            logger.debug(f'Poll #{poll_count}: No new jobs')
                        
                        # No new jobs, just wait
                        time.sleep(POLL_INTERVAL)
                        continue
                        
            # Small delay before next poll
            time.sleep(POLL_INTERVAL)
            
    except KeyboardInterrupt:
        logger.info('\n\n🛑 Shutdown signal received...')
        logger.info('👋 Worker shutting down gracefully')
    except Exception as e:
        logger.critical(f'\n\n💥 FATAL ERROR: {e}', exc_info=True)
        raise


if __name__ == '__main__':
    main()


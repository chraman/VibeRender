"""
Utility script to check job status in the database.
Helps debug why jobs might not be getting processed.

Usage:
    python check_jobs.py
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from config import Config

DB_CONFIG = {
    'host': Config.DB_HOST,
    'port': Config.DB_PORT,
    'database': Config.DB_NAME,
    'user': Config.DB_USER,
    'password': Config.DB_PASSWORD,
}

def check_jobs():
    """Check all jobs in the database."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get all jobs
        cursor.execute("""
            SELECT id, topic, status, created_at, updated_at
            FROM jobs
            ORDER BY id DESC
            LIMIT 20
        """)
        all_jobs = cursor.fetchall()
        
        # Get summary
        cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM jobs
            GROUP BY status
        """)
        summary = cursor.fetchall()
        
        print('=' * 60)
        print('📊 JOB STATUS SUMMARY')
        print('=' * 60)
        print('\nStatus Breakdown:')
        for row in summary:
            print(f'  {row["status"]}: {row["count"]} job(s)')
        
        print(f'\n📋 Recent Jobs (last 20):')
        print('-' * 60)
        for job in all_jobs:
            print(f'  ID: {job["id"]:3d} | Status: {job["status"]:10s} | Topic: {job["topic"][:40]}')
            print(f'        Created: {job["created_at"]} | Updated: {job["updated_at"]}')
        
        # Check for pending jobs
        cursor.execute("SELECT COUNT(*) as count FROM jobs WHERE status = 'pending'")
        pending_count = cursor.fetchone()['count']
        
        print('\n' + '=' * 60)
        if pending_count > 0:
            print(f'⚠️  WARNING: {pending_count} job(s) are pending and should be processed by the worker')
            cursor.execute("SELECT id, topic, created_at FROM jobs WHERE status = 'pending' ORDER BY id")
            pending_jobs = cursor.fetchall()
            print('\nPending Jobs:')
            for job in pending_jobs:
                print(f'  - Job {job["id"]}: "{job["topic"]}" (created: {job["created_at"]})')
        else:
            print('✅ No pending jobs')
        
        print('=' * 60)
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    check_jobs()


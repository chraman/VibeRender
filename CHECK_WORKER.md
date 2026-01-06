# How to Verify Worker is Processing Jobs

## Quick Verification Steps

### 1. Check if Worker is Running

Look at the worker console. You should see:
```
============================================================
VibeRender Video Worker started
============================================================
Polling database every 5 seconds...
Database: viberender_new@localhost:5432
Last processed job ID: 0
Press Ctrl+C to stop
```

### 2. Create a Job in the UI

1. Go to http://localhost:3000
2. Enter a topic (e.g., "How to make pizza")
3. Click "Generate Video"
4. You should see a success message and the job appear in the "Job Status" section

### 3. Watch the Worker Console

Within 5 seconds, you should see in the worker console:
```
[2024-01-03 12:00:00] Poll #1: Found 1 new job(s)
Processing video for: How to make pizza (Job ID: 1)
Completed processing job 1 for topic: How to make pizza
```

### 4. Check Job Status in UI

The UI automatically refreshes every 3 seconds. You should see:
- Status change from `pending` → `processing` → `completed`
- The status badge color will change accordingly

## Manual Database Check

If you want to check the database directly:

```bash
docker exec -it viberender-new-postgres psql -U postgres -d viberender_new
```

Then run:
```sql
SELECT id, topic, status, created_at, updated_at 
FROM jobs 
ORDER BY id DESC 
LIMIT 10;
```

You should see your jobs with their current status.

## Troubleshooting

### Worker Not Seeing Jobs

1. **Check Database Connection:**
   - Verify Docker containers are running: `docker ps`
   - Check if worker can connect (look for connection errors in console)

2. **Check Job Status:**
   - Jobs should have `status = 'pending'` to be picked up
   - Worker only processes jobs with `id > last_processed_id`

3. **Check Worker Logs:**
   - Worker shows polling activity every 10 polls
   - If you see "No new jobs", the worker is running but waiting

### Jobs Stuck in "pending"

1. **Worker Not Running:**
   - Make sure `python main.py` is running in the video-worker directory

2. **Database Connection Issue:**
   - Check worker console for connection errors
   - Verify DATABASE_URL or DB_* environment variables

3. **Worker Already Processed:**
   - Check `last_processed_id` in worker console
   - If job ID is less than last processed, it won't be picked up

### Status Not Updating in UI

1. **Auto-refresh:**
   - UI refreshes every 3 seconds automatically
   - Check browser console for errors

2. **Manual Refresh:**
   - Refresh the page to see latest status

## Expected Flow

1. ✅ User creates job → Status: `pending`
2. ✅ Worker picks up job → Status: `processing`
3. ✅ Worker completes → Status: `completed`
4. ✅ UI shows updated status (auto-refreshes)

## Status Colors

- 🟡 **Pending** - Job created, waiting for worker
- 🔵 **Processing** - Worker is currently processing
- 🟢 **Completed** - Job finished successfully
- 🔴 **Failed** - Job encountered an error


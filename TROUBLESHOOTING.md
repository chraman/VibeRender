# Troubleshooting Guide

## Issue: Job shows "Completed" in UI but worker shows no activity

### Symptoms
- UI shows job status as "completed"
- Worker console shows no processing activity
- No assets generated in `temp_assets/` folder

### Possible Causes

1. **Worker is not running**
   - Check if the worker process is actually running
   - Look for the startup message: `🚀 VibeRender Video Worker STARTED`

2. **Job was already processed before**
   - The job might have been completed in a previous run
   - Check the job's `updated_at` timestamp

3. **Job status is incorrect in database**
   - Job might be marked as "completed" without actually processing
   - This can happen if the worker crashed mid-processing

### Diagnostic Steps

#### Step 1: Check if Worker is Running
```bash
cd video-worker
python main.py
```

You should see:
```
🚀 VibeRender Video Worker STARTED
⏳ Starting polling loop...
```

If you don't see this, the worker isn't running.

#### Step 2: Check Job Status in Database
```bash
cd video-worker
python check_jobs.py
```

This will show:
- All jobs and their statuses
- Which jobs are pending
- When jobs were created/updated

#### Step 3: Check Worker Logs
Look for these messages in the worker console:
- `🔔 Poll #X: Found N new job(s)` - Worker found jobs
- `🎬 STARTING JOB PROCESSING` - Worker started processing
- `✅ JOB X COMPLETED SUCCESSFULLY` - Job finished

If you see polling messages but no job processing, check:
- Is `last_processed_id` higher than your job ID?
- Are jobs actually in "pending" status?

#### Step 4: Verify Job Status
Check the database directly:
```bash
docker exec -it viberender-postgres psql -U postgres -d viberender -c "SELECT id, topic, status, created_at, updated_at FROM jobs ORDER BY id DESC LIMIT 5;"
```

### Solutions

#### Solution 1: Reset Failed Jobs
If a job failed and you want to retry it:
```bash
cd video-worker
# Reset all failed jobs
python reset_failed_jobs.py

# Or reset a specific job
python reset_failed_jobs.py 1
```

#### Solution 2: Check Worker is Processing
The worker now shows detailed logging:
- Every poll is logged
- Database summary is shown on startup
- Pending jobs are listed when found

Look for these log messages:
```
📊 Current database job status:
   pending: 1 job(s) (IDs: 5-5)
   completed: 3 job(s) (IDs: 1-4)
```

#### Solution 3: Verify New Jobs are Created
When you create a job in the UI, check:
1. **Browser Console** - Should show:
   ```
   [FRONTEND] ✅ Job created successfully
     Job ID: 5
   ```

2. **Next.js Server Console** - Should show:
   ```
   [SERVER ACTION] ✅ Job created successfully
     Job ID: 5
     Status: pending
   ```

3. **Worker Console** - Within 5 seconds, should show:
   ```
   🔔 Poll #X: Found 1 new job(s)
   🎬 STARTING JOB PROCESSING
   ```

### Common Issues

#### Issue: Worker shows "No new jobs" but UI shows pending jobs

**Cause**: `last_processed_id` is higher than the pending job ID

**Solution**: The worker will now warn you:
```
⚠️  There are 1 pending job(s) in database, but none match id > X
   Pending jobs being skipped: [{'id': 5, 'topic': '...'}]
```

If this happens, the pending job has an ID lower than `last_processed_id`. This shouldn't happen with auto-increment, but if it does, you can:
1. Check the job ID in the database
2. Manually update `last_processed_id` (not recommended)
3. Or reset the failed job and let it process

#### Issue: Job shows "completed" but no assets

**Cause**: Job was marked complete without generating assets

**Solution**:
1. Check if assets exist: `ls temp_assets/{job_id}/`
2. Check worker logs for errors
3. Reset the job and try again: `python reset_failed_jobs.py {job_id}`

#### Issue: Worker not picking up new jobs

**Checklist**:
- [ ] Worker is running (`python main.py`)
- [ ] Database connection is working (check startup logs)
- [ ] Job is in "pending" status (use `check_jobs.py`)
- [ ] Job ID is higher than `last_processed_id` (shown in worker logs)
- [ ] No errors in worker console

### Enhanced Logging

The worker now provides:
- **Startup summary**: Shows all job statuses in database
- **Polling details**: Shows what jobs are found (or why none are found)
- **Warning messages**: Alerts when pending jobs exist but aren't being processed
- **Database summaries**: Every 10 polls, shows job status breakdown

### Quick Diagnostic Commands

```bash
# Check all jobs
cd video-worker
python check_jobs.py

# Reset failed jobs
python reset_failed_jobs.py

# Check database directly
docker exec -it viberender-postgres psql -U postgres -d viberender -c "SELECT * FROM jobs ORDER BY id DESC;"

# Check if worker is processing
# Look for these in worker console:
# - Poll messages every 5 seconds
# - Job processing messages when jobs are found
```


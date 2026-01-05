# Logging Guide

This project has comprehensive logging throughout the entire flow to help you track jobs from creation to completion.

## Logging Levels

### Python Worker (video-worker/)
- **INFO**: Important events (job processing, status updates, completions)
- **DEBUG**: Detailed information (database queries, API calls, file operations)
- **WARNING**: Rate limits, retries
- **ERROR**: Failures, exceptions
- **CRITICAL**: Fatal errors that stop the worker

### Next.js Frontend/Backend (web-app/)
- **Console logs**: All user actions, API calls, and state changes
- **Server Actions**: Detailed logging with timestamps and performance metrics

## Where to See Logs

### 1. Python Worker Console
Run the worker and watch the console:
```bash
cd video-worker
python main.py
```

You'll see:
- Worker startup and configuration
- Polling activity
- Job processing details
- API calls (Gemini, ElevenLabs)
- File operations
- Errors and retries

### 2. Next.js Server Console
When running `npm run dev`, check the terminal where Next.js is running:
- Server Action calls
- Database operations
- Job creation/fetching
- Performance metrics

### 3. Browser Console
Open browser DevTools (F12) → Console tab:
- Frontend form submissions
- Job loading
- Status updates
- API responses

## Log Flow Example

### 1. User Creates Job (Frontend)
```
[FRONTEND] Form submitted
  Topic: "How to make pizza"
  Timestamp: 2024-01-03T12:00:00.000Z
[FRONTEND] Calling createJob server action...
```

### 2. Server Action (Backend)
```
[SERVER ACTION] createJob called
  Topic: "How to make pizza"
  Timestamp: 2024-01-03T12:00:00.000Z
[SERVER ACTION] Inserting job into database...
[SERVER ACTION] ✅ Job created successfully
  Job ID: 1
  Status: pending
  Time taken: 45ms
```

### 3. Worker Picks Up Job
```
2024-01-03 12:00:05 [INFO] 🔔 Poll #1 [2024-01-03 12:00:05]: Found 1 new job(s)
2024-01-03 12:00:05 [INFO] Found 1 pending job(s): [1]
2024-01-03 12:00:05 [INFO] ============================================================
2024-01-03 12:00:05 [INFO] 🎬 STARTING JOB PROCESSING
2024-01-03 12:00:05 [INFO]    Job ID: 1
2024-01-03 12:00:05 [INFO]    Topic: How to make pizza
2024-01-03 12:00:05 [INFO]    Created: 2024-01-03 12:00:00
2024-01-03 12:00:05 [INFO] ============================================================
```

### 4. Asset Generation
```
2024-01-03 12:00:05 [INFO] ✅ Job 1 status updated to: processing
2024-01-03 12:00:05 [INFO] 📦 Starting asset generation for job 1...
2024-01-03 12:00:05 [INFO] 📝 Step 1/2: Generating script for topic: "How to make pizza"
2024-01-03 12:00:05 [INFO] 🤖 Calling Gemini API (attempt 1/2)...
2024-01-03 12:00:07 [INFO] ✅ Gemini API response received in 2.15 seconds
2024-01-03 12:00:07 [INFO] ✅ Script generated and saved: temp_assets/1/script.txt (234 bytes)
2024-01-03 12:00:07 [INFO] 🎤 Step 2/2: Generating audio from script...
2024-01-03 12:00:07 [INFO] 🎤 Getting available voices from ElevenLabs...
2024-01-03 12:00:07 [INFO] 🎙️  Using voice: Rachel (ID: 21m00Tcm4TlvDq8ikWAM)
2024-01-03 12:00:07 [INFO] 📝 Converting script to audio (length: 234 characters)...
2024-01-03 12:00:10 [INFO] ✅ Audio generation completed in 3.42 seconds
2024-01-03 12:00:10 [INFO] 💾 Audio file saved: temp_assets/1/audio.mp3 (45678 bytes)
2024-01-03 12:00:10 [INFO] ✅ All assets generated successfully for job 1
```

### 5. Job Completion
```
2024-01-03 12:00:10 [INFO] ✅ Asset generation completed in 5.57 seconds
2024-01-03 12:00:10 [INFO]    Script: temp_assets/1/script.txt
2024-01-03 12:00:10 [INFO]    Audio: temp_assets/1/audio.mp3
2024-01-03 12:00:10 [INFO] Updating job 1 status to: completed
2024-01-03 12:00:10 [INFO] ============================================================
2024-01-03 12:00:10 [INFO] ✅ JOB 1 COMPLETED SUCCESSFULLY
2024-01-03 12:00:10 [INFO]    Topic: How to make pizza
2024-01-03 12:00:10 [INFO]    Total time: 5.57 seconds
2024-01-03 12:00:10 [INFO] ============================================================
```

## Troubleshooting with Logs

### Job Stuck in "Pending"
1. Check worker console - is it running?
2. Look for polling messages: `Poll #X: No new jobs`
3. Verify `last_processed_id` matches your job ID

### Job Shows "Completed" but No Assets
1. Check worker logs for asset generation
2. Look for file paths in logs
3. Verify `temp_assets/` directory exists
4. Check for permission errors

### Rate Limit Errors
```
⚠️  Rate limit hit. Waiting 10 seconds before retry 1/1...
```
- Worker will automatically retry once
- Check API quota/limits

### Database Connection Issues
```
❌ Error: connection refused
```
- Verify Docker containers are running
- Check database credentials in logs

## Log Format

### Python Worker
```
YYYY-MM-DD HH:MM:SS [LEVEL] Message
```

### Next.js
```
[COMPONENT] Message
  Details...
```

## Performance Tracking

All logs include timing information:
- Server Actions: `Time taken: 45ms`
- API Calls: `completed in 2.15 seconds`
- Total Job Time: `Total time: 5.57 seconds`

Use these to identify bottlenecks and optimize performance.


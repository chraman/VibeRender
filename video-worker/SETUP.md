# Video Worker Setup Guide

## Quick Start

### 1. Install Dependencies

```bash
cd video-worker
python -m pip install -r requirements.txt
```

Or using `uv` (recommended):
```bash
uv pip install -r requirements.txt
```

### 2. Set Up API Keys

**Option A: Environment Variables (Recommended)**

Set these in your shell or system environment:
```bash
export GEMINI_API_KEY="your_gemini_key_here"
export ELEVENLABS_API_KEY="your_elevenlabs_key_here"
```

**Option B: .env File**

Create a `.env` file in the `video-worker/` directory:
```env
GEMINI_API_KEY=your_gemini_key_here
ELEVENLABS_API_KEY=your_elevenlabs_key_here
```

Then load it before running:
```bash
# On Windows (PowerShell)
$env:GEMINI_API_KEY="your_key"
$env:ELEVENLABS_API_KEY="your_key"

# On Mac/Linux
export GEMINI_API_KEY="your_key"
export ELEVENLABS_API_KEY="your_key"
```

### 3. Get API Keys

**Google Gemini API Key:**
1. Go to https://aistudio.google.com/app/apikey
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key (you won't see it again!)

**ElevenLabs API Key:**
1. Go to https://elevenlabs.io/app/settings/api-keys
2. Sign in or create an account
3. Click "Create" to generate a new API key
4. Copy the key

### 4. Run the Worker

```bash
python main.py
```

The worker will:
- Validate that API keys are set
- Start polling the database
- Generate scripts and audio when jobs are found
- Store assets in `temp_assets/{job_id}/`

## Verification

When you start the worker, you should see:
```
============================================================
VibeRender Video Worker started
============================================================
Polling database every 5 seconds...
Database: viberender@localhost:5432
Assets directory: temp_assets
Last processed job ID: 0
Press Ctrl+C to stop
```

If you see warnings about missing API keys, make sure they're set correctly.

## Generated Assets

After processing a job, check the `temp_assets/` directory:
```
temp_assets/
  └── 1/
      ├── script.txt    # Generated 30-second script
      └── audio.mp3     # Generated audio file
```

## Troubleshooting

### "GEMINI_API_KEY is not set"
- Make sure the environment variable is set
- Check that you're using the correct variable name
- Restart your terminal/IDE after setting variables

### "ELEVENLABS_API_KEY is not set"
- Same as above - verify the variable is set correctly

### "Failed to generate script with Gemini"
- Check your Google Gemini API key is valid
- Verify you have quota available in your Google AI Studio account
- Check your internet connection

### "Failed to generate audio with ElevenLabs"
- Check your ElevenLabs API key is valid
- Verify you have credits in your ElevenLabs account
- Check your internet connection

### Assets not being created
- Check that the `temp_assets/` directory is writable
- Look for error messages in the worker console
- Verify the job status in the database


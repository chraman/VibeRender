# VibeRender Video Worker

Python worker that polls the PostgreSQL database for new video generation jobs and generates video assets (scripts and audio).

## Setup

1. Install dependencies:
```bash
uv pip install -r requirements.txt
```

Or using pip:
```bash
pip install -r requirements.txt
```

2. Set up API keys:

Create a `.env` file in the `video-worker/` directory (or set environment variables):

```bash
# Required API Keys
OPENAI_API_KEY=your_openai_api_key_here
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here

# Optional: Database and worker settings
DB_HOST=localhost
DB_PORT=5432
DB_NAME=viberender
DB_USER=postgres
DB_PASSWORD=postgres
POLL_INTERVAL=5
TEMP_ASSETS_DIR=temp_assets
```

**Get API Keys:**
- OpenAI: https://platform.openai.com/api-keys
- ElevenLabs: https://elevenlabs.io/app/settings/api-keys

## Configuration

### Required Environment Variables
- `OPENAI_API_KEY` - OpenAI API key for script generation
- `ELEVENLABS_API_KEY` - ElevenLabs API key for text-to-speech

### Optional Environment Variables
- `DB_HOST` - Database host (default: localhost)
- `DB_PORT` - Database port (default: 5432)
- `DB_NAME` - Database name (default: viberender)
- `DB_USER` - Database user (default: postgres)
- `DB_PASSWORD` - Database password (default: postgres)
- `POLL_INTERVAL` - Polling interval in seconds (default: 5)
- `TEMP_ASSETS_DIR` - Directory for storing generated assets (default: temp_assets)

## Running

```bash
python main.py
```

The worker will:
1. Poll the database for new jobs with status 'pending'
2. Generate a 30-second video script using OpenAI
3. Convert the script to MP3 audio using ElevenLabs
4. Store assets in `temp_assets/{job_id}/` directory
5. Update job status to 'completed' or 'failed'

## Generated Assets

Assets are stored in the `temp_assets/` directory, organized by job ID:
```
temp_assets/
  ├── 1/
  │   ├── script.txt
  │   └── audio.mp3
  ├── 2/
  │   ├── script.txt
  │   └── audio.mp3
  └── ...
```

## Architecture

- `main.py` - Main worker loop and job processing
- `config.py` - Configuration management and environment variable loading
- `asset_generator.py` - OpenAI script generation and ElevenLabs audio conversion


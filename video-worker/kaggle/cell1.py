# 1. Install system dependencies for audio
!apt-get install -y espeak-ng libsndfile1

# 2. Install the Python 3.12 compatible versions
!pip install --no-cache-dir -U pyngrok coqui-tts diffusers transformers accelerate pydub nest_asyncio fastapi uvicorn
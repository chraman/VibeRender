import os
import io
import torch
import asyncio
import nest_asyncio
import uvicorn
import logging
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pyngrok import ngrok
from diffusers import AutoPipelineForText2Image
from TTS.api import TTS
from pydub import AudioSegment
from urllib.parse import unquote

# --- PRE-FLIGHT CONFIG ---
# 1. Automatically accept Coqui TOS for headless environment
os.environ["COQUI_TOS_AGREED"] = "1"

# 2. Patch the event loop for Jupyter/Kaggle
nest_asyncio.apply()

# 3. Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("KaggleServer")

# --- MODEL HOLDER & LIFESPAN ---
models = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles startup and shutdown of heavy ML models."""
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"⏳ Loading Models on {device}...")
    
    try:
        # Load Image Model
        models["pipe"] = AutoPipelineForText2Image.from_pretrained(
            "Lykon/dreamshaper-xl-v2-turbo", 
            torch_dtype=torch.float16, 
            variant="fp16"
        ).to(device)
        
        # Load Voice Model
        models["tts"] = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
        
        logger.info("✅ Models Loaded Successfully!")
    except Exception as e:
        logger.error(f"❌ Model Loading Failed: {e}")
        
    yield
    # Cleanup on shutdown
    models.clear()

# --- APP INITIALIZATION ---
app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- ENDPOINTS ---

@app.get("/generate-image")
async def generate_image(prompt: str, seed: int = 42):
    """Generates an image from a prompt."""
    prompt = unquote(prompt)
    image = models["pipe"](
        prompt=prompt,
        width=512, height=896,
        num_inference_steps=6,
        guidance_scale=2.0,
        generator=torch.Generator("cuda").manual_seed(seed)
    ).images[0]
    
    buf = io.BytesIO()
    image.save(buf, format="JPEG")
    return Response(content=buf.getvalue(), media_type="image/jpeg")

@app.get("/generate-audio")
async def generate_audio(text: str, lang: str = "en", speaker_wav: str = "/kaggle/working/sample.wav"):
    """Generates audio with hallucination fixes and automatic silence/noise trimming."""
    text = unquote(text).strip()
    
    # Safety punctuation
    if not text.endswith(('.', '!', '?', '_')):
        text += "_"

    if not os.path.exists(speaker_wav):
        return Response(content=f"Error: {speaker_wav} not found.", status_code=404)

    # 1. Generate the raw audio
    wav = models["tts"].tts(
        text=text, 
        speaker_wav=speaker_wav, 
        language=lang,
        temperature=0.6,           
        repetition_penalty=2.0
    )
    
    # 2. Convert to Pydub AudioSegment
    import numpy as np
    wav_norm = np.array(wav) * (32767 / max(0.01, np.max(np.abs(wav))))
    audio = AudioSegment(
        data=wav_norm.astype(np.int16).tobytes(), 
        sample_width=2, 
        frame_rate=24000, 
        channels=1
    )
    
    # 3. THE FIX: Detect and Trim Trailing Silence/Gibberish
    # This looks for anything quieter than -40dBFS and cuts it from the end
    from pydub.effects import strip_silence
    
    # We apply it specifically to the end to avoid cutting natural pauses in speech
    # padding=100 keeps 100ms of natural "air" at the end so it doesn't sound clipped
    audio = strip_silence(
        audio, 
        silence_thresh=-40, 
        chunk_size=10, 
        padding=100
    )

    # 4. Export to MP3
    buf = io.BytesIO()
    audio.export(buf, format="mp3", bitrate="192k")
    
    logger.info(f"✅ Audio processed and trimmed for text: {text[:30]}...")
    return Response(content=buf.getvalue(), media_type="audio/mpeg")

# --- SERVER START ---

if __name__ == "__main__":
    # 1. CLEANUP: Kill old tunnels and ports
    !fuser -k 8000/tcp
    ngrok.kill()
    
    # 2. START NGROK
    NGROK_TOKEN = "37vraVxV1TunmyLhSBA7H7ryytC_2U3FfH5E2t4oyrijUUCwX"
    ngrok.set_auth_token(NGROK_TOKEN)
    public_url = ngrok.connect(8000).public_url
    print(f"\n🚀 SERVER IS LIVE AT: {public_url}\n")

    # 3. START UVICORN (The Python 3.12 manual way)
    config = uvicorn.Config(
        app, 
        host="127.0.0.1", # Matches Ngrok's default private leg
        port=8000, 
        loop="asyncio",
        timeout_keep_alive=60
    )
    server = uvicorn.Server(config)
    
    # Run the server manually inside the notebook's event loop
    loop = asyncio.get_event_loop()
    loop.create_task(server.serve())
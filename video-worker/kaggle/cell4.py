import os
import io
import re
import logging
import asyncio
import torch
import numpy as np
import nest_asyncio
import uvicorn
import noisereduce as nr
from urllib.parse import unquote
from contextlib import asynccontextmanager

# FastAPI & Network
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from pyngrok import ngrok

# ML & Audio Processing
from diffusers import AutoPipelineForText2Image
from TTS.api import TTS
from pydub import AudioSegment
from pydub.effects import normalize, compress_dynamic_range, strip_silence

# --- CONFIGURATION & CONSTANTS ---

# Environment Setup
os.environ["COQUI_TOS_AGREED"] = "1"  # Automatically accept Coqui TOS
nest_asyncio.apply()  # Patch event loop for Jupyter/Kaggle

# Logging Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("KaggleServer")

# Constants
NGROK_TOKEN = "37vraVxV1TunmyLhSBA7H7ryytC_2U3FfH5E2t4oyrijUUCwX"
SILENCE_GAP = AudioSegment.silent(duration=300)  # Slightly longer for natural breath
MAX_CHARS = 200  # XTTS stability threshold
SPEAKER_WAV_DEFAULT = "/kaggle/working/sample_cleaned.wav"
SFX_DIR = "/kaggle/working"

# Global Model Holder
models = {}

# --- HELPER FUNCTIONS ---

def clean_text(text: str) -> str:
    """Sanitizes text for TTS stability."""
    text = unquote(text).strip()
    # Replace symbols that confuse XTTS
    text = text.replace("&", " and ").replace("%", " percent ")
    text = re.sub(r'\s+', ' ', text)
    return text

def smart_split(text: str) -> list[str]:
    """Splits text by punctuation AND length to prevent model instability."""
    # Split by . ! ? or , (commas help keep chunks manageable)
    tokens = re.split(r'(?<=[.!?]) +|(?<=,) +', text)
    final_sentences = []
    
    for t in tokens:
        if len(t) > MAX_CHARS:
            # Further split long run-on sentences by space
            sub_parts = [t[i:i+MAX_CHARS] for i in range(0, len(t), MAX_CHARS)]
            final_sentences.extend(sub_parts)
        else:
            final_sentences.append(t)
    return final_sentences

# --- LIFESPAN MANAGER ---

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
async def generate_audio(text: str, effect: str = "ambient", lang: str = "en", speaker_wav: str = SPEAKER_WAV_DEFAULT):
    decoded_text = clean_text(text)
    sentences = smart_split(decoded_text)
    
    audio_chunks = []
    
    with torch.inference_mode():
        for sentence in sentences:
            if len(sentence.strip()) < 2: continue

            # PRO FIX 1: The "Ending Underscore" / Period Appending
            input_text = sentence.strip() + " ."

            wav = models["tts"].tts(
                text=input_text, 
                speaker_wav=speaker_wav, 
                language=lang, 
                temperature=0.6,          # Lower temp = more stability
                repetition_penalty=1.8,   # 1.8 is safer than 2.0
                length_penalty=1.0
            )
            
            # Convert to numpy
            wav_array = np.array(wav)
            
            # PRO FIX 2: Spectral Noise Reduction
            wav_array = nr.reduce_noise(y=wav_array, sr=24000, prop_decrease=0.8)
            
            audio_data = (wav_array * 32767).astype(np.int16)
            chunk = AudioSegment(data=audio_data.tobytes(), sample_width=2, frame_rate=24000, channels=1)

            # PRO FIX 3: Dynamic Compression
            chunk = compress_dynamic_range(chunk, threshold=-20.0, ratio=3.0)

            # Tight surgical trim
            chunk = strip_silence(chunk, silence_thresh=-42, padding=20)
            chunk = chunk.fade_in(20).fade_out(20)
            audio_chunks.append(chunk)

    if not audio_chunks:
        return Response(status_code=400, content="Failed to generate audio")

    # Efficient Concat
    combined_voice = audio_chunks[0]
    for next_chunk in audio_chunks[1:]:
        combined_voice = combined_voice + SILENCE_GAP + next_chunk

    # Final Leveling
    combined_voice = normalize(combined_voice)

    # PRO FIX 4: Background Ducking
    sfx_path = f"{SFX_DIR}/{effect}.mp3"
    if os.path.exists(sfx_path):
        bg = AudioSegment.from_file(sfx_path) - 25 
        if len(bg) < len(combined_voice):
            bg = bg * ((len(combined_voice) // len(bg)) + 1)
        
        # Fade out the background music slightly after the voice ends
        bg = bg[:len(combined_voice) + 500].fade_out(1500)
        final_audio = bg.overlay(combined_voice)
    else:
        final_audio = combined_voice

    buf = io.BytesIO()
    final_audio.export(buf, format="mp3", bitrate="192k")
    return Response(content=buf.getvalue(), media_type="audio/mpeg")

# --- SERVER START ---

if __name__ == "__main__":
    # 1. CLEANUP: Kill old tunnels and ports
    # Note: Using os.system instead of ! magic command for valid Python syntax
    os.system("fuser -k 8000/tcp")
    ngrok.kill()
    
    # 2. START NGROK
    ngrok.set_auth_token(NGROK_TOKEN)
    public_url = ngrok.connect(8000).public_url
    print(f"\n🚀 SERVER IS LIVE AT: {public_url}\n")

    # 3. START UVICORN (The Python 3.12 manual way)
    config = uvicorn.Config(
        app, 
        host="127.0.0.1", 
        port=8000, 
        loop="asyncio",
        timeout_keep_alive=60
    )
    server = uvicorn.Server(config)
    
    # Run the server manually inside the notebook's event loop
    loop = asyncio.get_event_loop()
    loop.create_task(server.serve())
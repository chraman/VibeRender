import os
import io
import re
import torch
import asyncio
import logging
import numpy as np
import nest_asyncio
import uvicorn
import gc
from urllib.parse import unquote
from contextlib import asynccontextmanager

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from pyngrok import ngrok
from pydub import AudioSegment
from diffusers import AutoPipelineForText2Image
from f5_tts.api import F5TTS

# --- CONFIGURATION ---
nest_asyncio.apply()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("KaggleServer")

NGROK_TOKEN = "37vraVxV1TunmyLhSBA7H7ryytC_2U3FfH5E2t4oyrijUUCwX"
SPEAKER_WAV_DEFAULT = "/kaggle/working/sample_cleaned.wav" 
models = {}

# --- LIFESPAN MANAGER ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Loads heavy models on startup and clears them on shutdown."""
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"⏳ Loading Models on {device}...")
    try:
        # Image Model (Dreamshaper XL)
        models["pipe"] = AutoPipelineForText2Image.from_pretrained(
            "Lykon/dreamshaper-xl-v2-turbo", 
            torch_dtype=torch.float16, variant="fp16"
        ).to(device)
        
        # Voice Model (F5-TTS)
        models["tts"] = F5TTS()
        
        logger.info("✅ Models Loaded Successfully!")
    except Exception as e:
        logger.error(f"❌ Model Loading Failed: {e}")
    yield
    models.clear()

app = FastAPI(lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# --- ENDPOINTS ---

@app.get("/generate-image")
async def generate_image(prompt: str, seed: int = 42):
    # Ensure Image model is on GPU
    models["pipe"].to("cuda")
    torch.cuda.empty_cache()
    gc.collect()
    
    try:
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
    except Exception as e:
        logger.error(f"Image Error: {e}")
        return Response(status_code=500, content=str(e))

@app.get("/generate-audio")
async def generate_audio(text: str, effect: str = "ambient", speaker_wav: str = SPEAKER_WAV_DEFAULT):
    # 1. Force Image model to CPU to make room
    models["pipe"].to("cpu")
    torch.cuda.empty_cache()
    gc.collect()

    # 2. Hardcoded reference text from your sample
    # This prevents the Whisper model from loading!
    SAMPLE_REF_TEXT = "Printing, in the only sense with which we are at present concerned, differs from most if not from all the arts and crafts represented in the exhibition."

    try:
        decoded_text = unquote(text).strip()
        sentences = [s.strip() for s in re.split(r'(?<=[.!?]) +', decoded_text) if s.strip()]
        
        combined_voice = AudioSegment.empty()
        
        for sentence in sentences:
            # 3. Use inference_mode for maximum VRAM efficiency
            with torch.inference_mode():
                wav, sr, _ = models["tts"].infer(
                    ref_file=speaker_wav,
                    ref_text=SAMPLE_REF_TEXT,  # <--- CRITICAL FIX
                    gen_text=sentence,
                    remove_silence=True
                )

            wav_norm = np.array(wav) * 32767
            chunk = AudioSegment(
                data=wav_norm.astype(np.int16).tobytes(), 
                sample_width=2, frame_rate=sr, channels=1
            )
            combined_voice += chunk + AudioSegment.silent(duration=400)
            
            # Clear cache between sentences
            torch.cuda.empty_cache()

        # 4. Mix Background (SFX)
        sfx_path = f"/kaggle/working/{effect}.mp3"
        if os.path.exists(sfx_path):
            bg = AudioSegment.from_file(sfx_path) - 22
            if len(bg) < len(combined_voice):
                bg = bg * ((len(combined_voice) // len(bg)) + 1)
            final_audio = bg[:len(combined_voice) + 500].fade_out(1000).overlay(combined_voice)
        else:
            final_audio = combined_voice

        buf = io.BytesIO()
        final_audio.export(buf, format="mp3", bitrate="192k")
        
        # 5. Bring Image model back to GPU
        models["pipe"].to("cuda")
        
        return Response(content=buf.getvalue(), media_type="audio/mpeg")

    except Exception as e:
        models["pipe"].to("cuda")
        logger.error(f"Audio Error: {e}")
        return Response(status_code=500, content=f"Model Error: {str(e)}")

# --- SERVER START ---

if __name__ == "__main__":
    # Cleanup old processes
    os.system("fuser -k 8000/tcp")
    ngrok.kill()
    
    # Setup Ngrok
    ngrok.set_auth_token(NGROK_TOKEN)
    public_url = ngrok.connect(8000).public_url
    print(f"\n🚀 SERVER LIVE: {public_url}\n")

    # Run Uvicorn
    config = uvicorn.Config(
        app, host="0.0.0.0", port=8000, 
        loop="asyncio", timeout_keep_alive=150
    )
    server = uvicorn.Server(config)
    
    loop = asyncio.get_event_loop()
    loop.run_until_complete(server.serve())
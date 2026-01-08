import numpy as np
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
import re
from pydub import AudioSegment
from pydub.effects import strip_silence
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
async def generate_audio(text: str, effect: str = "ambient", lang: str = "en", speaker_wav: str = "/kaggle/working/sample.wav"):
    decoded_text = unquote(text).strip()
    
    # 1. DYNAMIC SENTENCE SPLITTING
    # This splits by . ! or ? while keeping the punctuation
    sentences = re.split(r'(?<=[.!?]) +', decoded_text)

    combined_voice = AudioSegment.empty()
    
    for sentence in sentences:
        if not sentence.strip(): continue

        import torch
        import gc
        
        # Inside the loop:
        torch.cuda.empty_cache()
        gc.collect()
        
        # 1. Generate the sentence
        wav = models["tts"].tts(text=sentence, speaker_wav=speaker_wav, language=lang, temperature=0.4)
        
        # 2. Convert to Pydub
        wav_norm = np.array(wav) * (32767 / max(0.01, np.max(np.abs(wav))))
        clip = AudioSegment(data=wav_norm.astype(np.int16).tobytes(), sample_width=2, frame_rate=24000, channels=1)
        
        # 3. DOUBLE-ENDED TRIMMING (Crucial Fix)
        # We trim silence from the START and the END of the clip to remove the 3-4s gibberish
        # We use a more aggressive -50dB threshold
        from pydub.effects import strip_silence

        # Increase threshold to -55 (very sensitive)
        # 'seek_step=1' makes the search more precise
        clip = strip_silence(clip, silence_thresh=-55, padding=50)
        
        # FORCE trim the first 20ms of every clip 
        # This physically deletes the "eh" or "click" sound XTTS often starts with
        if len(clip) > 100:
            clip = clip[20:]
        
        # 4. MICRO FADES
        # Fade in/out by 50ms to kill any sudden digital pops or clicks
        clip = clip.fade_in(50).fade_out(50)
        
        # 5. Build the track with a fixed pause
        # Instead of: combined_voice += clip + AudioSegment.silent(duration=400)
        # Use this:
        if len(combined_voice) == 0:
            combined_voice = clip
        else:
            # This overlaps the new sentence by 100ms with the previous one
            # effectively "shaving off" the dead air
            combined_voice = combined_voice.append(clip, crossfade=100)


    # 4. MIX WITH DYNAMIC BACKGROUND
    sfx_path = f"/kaggle/working/{effect}.mp3"
    if os.path.exists(sfx_path):
        bg = AudioSegment.from_file(sfx_path) - 25 # Music is much quieter
        
        # Loop music to fit total voice length
        if len(bg) < len(combined_voice):
            bg = bg * (int(len(combined_voice) / len(bg)) + 1)
        
        bg = bg[:len(combined_voice)].fade_out(1500)
        final_audio = bg.overlay(combined_voice)
    else:
        final_audio = combined_voice

    # 5. EXPORT
    buf = io.BytesIO()
    final_audio.export(buf, format="mp3", bitrate="192k")
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
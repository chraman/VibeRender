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
# from f5_tts.api import F5TTS


from diffusers import FluxPipeline

from kaggle_secrets import UserSecretsClient
import os

from diffusers import FluxPipeline, FluxTransformer2DModel
from transformers import T5EncoderModel, BitsAndBytesConfig
import torch

# Fetch the secret and set it as an environment variable
user_secrets = UserSecretsClient()
hf_token = user_secrets.get_secret("HF_TOKEN")
os.environ["HF_TOKEN"] = hf_token

# --- CONFIGURATION ---
nest_asyncio.apply()

# Standard Console Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("KaggleServer")

NGROK_TOKEN = "37vraVxV1TunmyLhSBA7H7ryytC_2U3FfH5E2t4oyrijUUCwX"
SPEAKER_WAV_DEFAULT = "/kaggle/working/sample_cleaned.wav" 

# WHISPER-BYPASS FIX: Hardcoded text from your sample_cleaned.wav 
# Prevents the model from loading Whisper (Saves 2GB VRAM)
SAMPLE_REF_TEXT = "Printing, in the only sense with which we are at present concerned, differs from most if not from all the arts and crafts represented in the exhibition."

models = {}

def clear_vram():
    """Aggressively clears GPU memory to prevent Kernel Death"""
    gc.collect()
    torch.cuda.empty_cache()
    torch.cuda.ipc_collect() # Clears inter-process memory
    with torch.cuda.device("cuda"):
        torch.cuda.empty_cache()

# --- LIFESPAN MANAGER ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Loads heavy models on startup and clears them on shutdown."""
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"⏳ Loading Models on {device}...")
    try:
        # Load FLUX in 4-bit (NF4)
                # 1. Configure the 8-bit Quantization
        quantization_config = BitsAndBytesConfig(load_in_8bit=True)
        
        # 2. Load the Transformer (the heavy part) in 8-bit
        transformer = FluxTransformer2DModel.from_pretrained(
            "black-forest-labs/FLUX.1-schnell",
            subfolder="transformer",
            quantization_config=quantization_config,
            torch_dtype=torch.bfloat16
        )
        
        # 3. Load the rest of the pipeline
        models["pipe"] = FluxPipeline.from_pretrained(
            "black-forest-labs/FLUX.1-schnell",
            transformer=transformer,
            torch_dtype=torch.bfloat16
        )
        
        # 4. Critical for Kaggle T4 (especially if running F5-TTS simultaneously)
        models["pipe"].enable_sequential_cpu_offload()

        # model_id = "sayakpaul/flux.1-schnell-fp8"
        # models["pipe"] = FluxPipeline.from_pretrained(
        #     model_id, 
        #     torch_dtype=torch.bfloat16 # The weights are 4-bit, but compute is bf16
        # )
        # Use sequential offload for maximum VRAM savings
        # models["pipe"].enable_sequential_cpu_offload()
        
        # Voice Model (F5-TTS)
        # models["tts"] = F5TTS()
        
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
    # models["pipe"].to("cuda")
    clear_vram()
    
    try:
        prompt = unquote(prompt)
        logger.info(f"🎨 Generating Image: {prompt[:50]}...")
        
        with torch.inference_mode():
            image = models["pipe"](
                prompt=prompt,
                width=512, 
                height=512,
                num_inference_steps=4, # Dev needs ~20 steps (Schnell needs 4)
                guidance_scale=0.0,     # Typical for Flux-Dev
                max_sequence_length=256,# Crucial for Flux text understanding
                generator=torch.Generator("cpu").manual_seed(seed)
            ).images[0]
        
        buf = io.BytesIO()
        image.save(buf, format="JPEG")
        return Response(content=buf.getvalue(), media_type="image/jpeg")
    except Exception as e:
        logger.error(f"❌ Image Error: {e}")
        return Response(status_code=500, content=str(e))

# @app.get("/generate-audio")
# async def generate_audio(text: str, effect: str = "ambient", speaker_wav: str = SPEAKER_WAV_DEFAULT):
#     # 1. Move Image model to CPU to make room for TTS (Crucial for 16GB GPUs)
#     # models["pipe"].to("cpu")
#     clear_vram()

#     try:
#         decoded_text = unquote(text).strip()
#         logger.info(f"🎙️ Generating Audio: {decoded_text[:50]}...")
        
#         # PRECISION NARRATOR FIX: Split by punctuation to ensure short words aren't skipped
#         raw_sentences = re.split(r'(?<=[.!?]) +', decoded_text)
#         sentences = [s.strip() for s in raw_sentences if s.strip()]
        
#         combined_voice = AudioSegment.empty()
        
#         for sentence in sentences:
#             logger.info(f"Processing segment: {sentence}")
#             with torch.inference_mode():
#                 wav, sr, _ = models["tts"].infer(
#                     ref_file=speaker_wav,
#                     ref_text=SAMPLE_REF_TEXT, # Whisper bypass
#                     gen_text=sentence,
#                     remove_silence=False      # Keeps natural word-ending breath
#                 )

#             wav_norm = np.array(wav) * 32767
#             chunk = AudioSegment(
#                 data=wav_norm.astype(np.int16).tobytes(), 
#                 sample_width=2, frame_rate=sr, channels=1
#             )
            
#             # HORROR PACING: Longer pauses after short, punchy sentences (like "Unblinking.")
#             # 
#             pause_duration = 800 if len(sentence.split()) < 3 else 450
#             combined_voice += chunk + AudioSegment.silent(duration=pause_duration)
            
#             clear_vram()

#         # 3. Mix Background (SFX)
#         sfx_path = f"/kaggle/working/{effect}.mp3"
#         if os.path.exists(sfx_path):
#             bg = AudioSegment.from_file(sfx_path) - 22
#             if len(bg) < len(combined_voice):
#                 bg = bg * ((len(combined_voice) // len(bg)) + 1)
#             final_audio = bg[:len(combined_voice) + 500].fade_out(1000).overlay(combined_voice)
#         else:
#             final_audio = combined_voice

#         buf = io.BytesIO()
#         final_audio.export(buf, format="mp3", bitrate="192k")
        
#         # 4. Bring Image model back to GPU
#         models["pipe"].to("cuda")
        
#         return Response(content=buf.getvalue(), media_type="audio/mpeg")

#     except Exception as e:
#         models["pipe"].to("cuda")
#         logger.error(f"❌ Audio Error: {e}")
#         return Response(status_code=500, content=f"Model Error: {str(e)}")

# --- SERVER START ---

if __name__ == "__main__":
    os.system("fuser -k 8000/tcp")
    ngrok.kill()
    
    ngrok.set_auth_token(NGROK_TOKEN)
    public_url = ngrok.connect(8000).public_url
    print(f"\n🚀 SERVER LIVE: {public_url}\n")

    config = uvicorn.Config(
        app, host="0.0.0.0", port=8000, 
        loop="asyncio", timeout_keep_alive=150
    )
    server = uvicorn.Server(config)
    
    loop = asyncio.get_event_loop()
    loop.run_until_complete(server.serve())
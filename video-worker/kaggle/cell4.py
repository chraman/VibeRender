import os, io, gc, torch, asyncio, logging, nest_asyncio, uvicorn
from urllib.parse import unquote
from contextlib import asynccontextmanager
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from pyngrok import ngrok
from diffusers import FluxPipeline, FluxTransformer2DModel
from transformers import BitsAndBytesConfig
from kaggle_secrets import UserSecretsClient

# Fetch the secret and set it as an environment variable
user_secrets = UserSecretsClient()
hf_token = user_secrets.get_secret("HF_TOKEN")
os.environ["HF_TOKEN"] = hf_token

# --- CONFIGURATION ---
nest_asyncio.apply()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("KaggleServer")
NGROK_TOKEN = "37vraVxV1TunmyLhSBA7H7ryytC_2U3FfH5E2t4oyrijUUCwX"

models = {}

def clear_vram():
    """Aggressively clears GPU memory to prevent Kernel Death"""
    gc.collect()
    torch.cuda.empty_cache()
    torch.cuda.ipc_collect() # Clears inter-process memory
    with torch.cuda.device("cuda"):
        torch.cuda.empty_cache()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("⏳ Loading FLUX (8-Bit High Fidelity Mode)...")
    try:
        # 1. 8-Bit Config
        quant_config = BitsAndBytesConfig(
            load_in_8bit=True,
        )
        
        # 2. Load Transformer in 8-bit
        transformer = FluxTransformer2DModel.from_pretrained(
            "black-forest-labs/FLUX.1-schnell",
            subfolder="transformer",
            quantization_config=quant_config,
            torch_dtype=torch.float16 # Use float16 for 8-bit compatibility
        )

        # 3. Load Pipeline
        models["pipe"] = FluxPipeline.from_pretrained(
            "black-forest-labs/FLUX.1-schnell",
            transformer=transformer,
            torch_dtype=torch.float16
        )

        # 4. THE CRITICAL 8-BIT OPTIMIZATION
        # This is the only way 8-bit fits on a T4. It offloads every layer 
        # to the CPU after it finishes its piece of the math.
        models["pipe"].enable_sequential_cpu_offload()
        models["pipe"].vae.enable_tiling()
        
        logger.info("✅ 8-Bit FLUX Loaded. Ready for high-quality generation!")
        clear_vram()
    except Exception as e:
        logger.error(f"❌ Initialization Failed: {e}")
    yield
    models.clear()
    clear_vram()

app = FastAPI(lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/generate-image")
async def generate_image(prompt: str, seed: int = 42):
    clear_vram()
    try:
        prompt = unquote(prompt)
        # For Schnell, use exactly 4 steps and 0.0 guidance
        generator = torch.Generator(device="cpu").manual_seed(seed)
        
        with torch.inference_mode():
            output = models["pipe"](
                prompt=prompt,
                width=512, 
                height=896,
                num_inference_steps=4,
                guidance_scale=0.0,
                max_sequence_length=256,
                generator=generator
            ).images[0]
        
        buf = io.BytesIO()
        output.save(buf, format="JPEG", quality=90)
        return Response(content=buf.getvalue(), media_type="image/jpeg")
    except Exception as e:
        logger.error(f"❌ Generation Error: {e}")
        return Response(status_code=500, content=str(e))

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
"""
Image generation logic for VibeRender Video Worker.
"""

import os
import time
import logging
import pathlib
import random
import requests
from urllib.parse import quote
from typing import List
from api_clients import GeminiClient

logger = logging.getLogger(__name__)


class ImageGenerator:
    """Handles image prompt generation and downloading."""
    
    def __init__(self, gemini_client: GeminiClient, temp_assets_dir: pathlib.Path):
        """
        Initialize image generator.
        
        Args:
            gemini_client: Configured GeminiClient instance
            temp_assets_dir: Path to temporary assets directory
        """
        self.gemini_model = gemini_client.get_model()
        self.temp_assets_dir = pathlib.Path(temp_assets_dir)
        self.kaggle_url = "https://branchless-corazon-uncoifed.ngrok-free.dev"
        logger.debug('🖼️  ImageGenerator initialized')
    
    def normalize_image_prompt(self, prompt: str) -> str:
        # Adding negative-style prompts directly into the positive prompt
        # helps keep the 'Vibe' consistent across scenes.
        style_boosters = (
            "centered, vertical composition, 9:16 ratio"
        )
        return f"{prompt}, {style_boosters}"

    def download_image(self, prompt: str, job_id: int, scene_index: int) -> str:
        """
        Download an image from the custom Kaggle SDXL Turbo server.
        """
        try:
            random_seed = random.randint(1, 1000000)
            
            # Use the URL from self

            prompt = self.normalize_image_prompt(prompt)
            encoded_prompt = quote(prompt)
            image_url = f"{self.kaggle_url}/generate?prompt={encoded_prompt}&seed={random_seed}"
            
            headers = {
                "ngrok-skip-browser-warning": "true",
                "User-Agent": "VibeRenderWorker/1.0"
            }
            
            job_dir = self.temp_assets_dir / str(job_id)
            job_dir.mkdir(exist_ok=True)
            
            image_filename = f'scene_{job_id}_{scene_index}.jpg'
            image_path = job_dir / image_filename
            
            response = requests.get(
                image_url, 
                headers=headers,
                stream=True, 
                timeout=(15, 60)
            )
            
            if response.status_code != 200:
                raise Exception(f'Kaggle Server returned {response.status_code}')
            
            with open(image_path, 'wb') as image_file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        image_file.write(chunk)
            
            return str(image_path)
            
        except Exception as e:
            logger.error(f'❌ Failed: {str(e)}')
            raise e
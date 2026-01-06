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
        logger.debug('🖼️  ImageGenerator initialized')
    
    def normalize_image_prompt(self, prompt: str) -> str:
        return (
            f"{prompt}, vertical 9:16, portrait orientation, "
            f"cinematic framing, subject centered, safe margins, "
            f"no borders, no distortion, sharp focus, high detail"
        )

    def download_image(self, prompt: str, job_id: int, scene_index: int) -> str:
        """
        Download an image from Pollinations.ai based on a prompt.
        
        Args:
            prompt: The image generation prompt/description
            job_id: The job ID for organizing files
            scene_index: The scene index (0, 1, 2, etc.)
            
        Returns:
            Path to the downloaded image file
            
        Raises:
            Exception: If image download fails
        """
        try:
            # Generate random seed for image variation
            random_seed = random.randint(1, 1000000)
            
            # Encode the prompt for URL
            final_prompt = self.normalize_image_prompt(prompt)
            encoded_prompt = quote(prompt)
            
            # Construct the Pollinations.ai URL
            image_url = (
                f'https://image.pollinations.ai/prompt/{encoded_prompt}'
                f'?width=1080&height=1920&nologo=true&seed={random_seed}'
            )
            
            logger.debug(f'   Downloading image from: {image_url[:80]}...')
            
            # Create job-specific directory if it doesn't exist
            job_dir = self.temp_assets_dir / str(job_id)
            job_dir.mkdir(exist_ok=True)
            
            # Construct output file path
            image_filename = f'scene_{job_id}_{scene_index}.jpg'
            image_path = job_dir / image_filename
            
            # Download the image with retry logic for timeouts
            max_retries = 2
            retry_count = 0
            start_time = time.time()
            
            while retry_count <= max_retries:
                try:
                    # Use longer timeout for image generation (120 seconds)
                    # Pollinations.ai can take time to generate images
                    response = requests.get(
                        image_url, 
                        stream=True, 
                        timeout=(30, 120)  # (connect timeout, read timeout)
                    )
                    
                    # Check for HTTP errors
                    if response.status_code != 200:
                        raise Exception(
                            f'Pollinations.ai returned status {response.status_code}: {response.text[:200]}'
                        )
                    
                    # Save image to file using context manager
                    with open(image_path, 'wb') as image_file:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                image_file.write(chunk)
                    
                    elapsed_time = time.time() - start_time
                    file_size = os.path.getsize(image_path)
                    
                    if file_size == 0:
                        raise ValueError(f'Image file was created but is empty at {image_path}')
                    
                    logger.info(f'   ✅ Image {scene_index + 1} downloaded: {image_path} ({file_size} bytes, {elapsed_time:.2f}s)')
                    
                    return str(image_path)
                    
                except (requests.exceptions.Timeout, requests.exceptions.ReadTimeout) as e:
                    retry_count += 1
                    if retry_count <= max_retries:
                        wait_time = 5 * retry_count  # Exponential backoff: 5s, 10s
                        logger.warning(
                            f'   ⚠️  Timeout downloading image {scene_index + 1} '
                            f'(attempt {retry_count}/{max_retries + 1}). '
                            f'Retrying in {wait_time} seconds...'
                        )
                        time.sleep(wait_time)
                        continue
                    else:
                        raise Exception(
                            f'Timeout after {max_retries + 1} attempts. '
                            f'Pollinations.ai may be slow or unavailable.'
                        )
                except Exception as e:
                    # For non-timeout errors, don't retry
                    raise
            
        except Exception as e:
            logger.error(f'   ❌ Failed to download image {scene_index + 1}: {str(e)}')
            raise Exception(f'Failed to download image from Pollinations.ai: {str(e)}')


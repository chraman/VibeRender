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
    
    def generate_image_prompts(self, script: str) -> List[str]:
        """
        Generate 3 specific image prompts for scenes using Google Gemini.
        
        Args:
            script: The video script to generate image prompts for
            
        Returns:
            List of 3 image prompt strings
            
        Raises:
            Exception: If image prompt generation fails
        """
        max_retries = 1
        retry_count = 0
        
        # Construct the prompt to generate image descriptions
        prompt = (
            'You are a visual content creator. Based on the following video script, '
            'create exactly 3 specific, detailed image prompts for key scenes. '
            'Each prompt should be a single line describing a visual scene that would work '
            'for a short-form video. Make them vivid, specific, and suitable for AI image generation.\n\n'
            f'Video Script:\n{script}\n\n'
            'Provide exactly 3 image prompts, one per line. Each prompt should be a complete '
            'visual description without numbering or labels.'
        )
        
        while retry_count <= max_retries:
            try:
                logger.info(f'🖼️  Generating image prompts with Gemini (attempt {retry_count + 1}/{max_retries + 1})...')
                
                generation_config = {
                    'temperature': 0.7,
                    'max_output_tokens': 300
                }
                start_time = time.time()
                
                response = self.gemini_model.generate_content(
                    prompt,
                    generation_config=generation_config
                )
                
                elapsed_time = time.time() - start_time
                result_text = response.text.strip()
                
                logger.info(f'✅ Image prompts generated in {elapsed_time:.2f} seconds')
                
                # Parse the response to extract individual prompts
                # Split by newlines and filter out empty lines
                prompts = [line.strip() for line in result_text.split('\n') if line.strip()]
                
                # Remove any numbering or bullet points
                prompts = [p.lstrip('0123456789.-) ').strip() for p in prompts]
                
                # Take first 3 prompts
                prompts = prompts[:3]
                
                if len(prompts) < 3:
                    logger.warning(f'⚠️  Only got {len(prompts)} prompts, expected 3')
                    # If we got fewer than 3, pad with generic prompts
                    while len(prompts) < 3:
                        prompts.append(f'Scene from video about the topic')
                
                logger.debug(f'   Generated {len(prompts)} image prompts')
                for i, prompt_text in enumerate(prompts, 1):
                    logger.debug(f'   Prompt {i}: {prompt_text[:60]}...')
                
                return prompts
                
            except Exception as e:
                error_str = str(e).lower()
                is_rate_limit = (
                    '429' in error_str or 
                    'rate limit' in error_str or 
                    'quota' in error_str or
                    'resource exhausted' in error_str
                )
                
                if is_rate_limit and retry_count < max_retries:
                    retry_count += 1
                    logger.warning(f'⚠️  Rate limit hit. Waiting 10 seconds before retry {retry_count}/{max_retries}...')
                    time.sleep(10)
                    continue
                else:
                    if is_rate_limit:
                        logger.error(f'❌ Rate limit exceeded after {max_retries} retry(ies)')
                        raise Exception(f'Failed to generate image prompts: Rate limit exceeded after {max_retries} retry(ies)')
                    else:
                        logger.error(f'❌ Gemini API error: {str(e)}')
                        raise Exception(f'Failed to generate image prompts with Gemini: {str(e)}')
    
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
            encoded_prompt = quote(prompt)
            
            # Construct the Pollinations.ai URL
            image_url = (
                f'https://image.pollinations.ai/prompt/{encoded_prompt}'
                f'?width=1024&height=1024&nologo=true&seed={random_seed}'
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


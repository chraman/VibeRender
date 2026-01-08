"""
Audio generation logic for VibeRender Video Worker using custom Kaggle XTTSv2 server.
"""

import os
import time
import logging
import requests
from urllib.parse import quote
from config import Config

logger = logging.getLogger(__name__)

class AudioGenerator:
    """Handles audio generation using custom Kaggle XTTSv2 server."""
    
    def __init__(self, *args, **kwargs):
        """
        Initialize audio generator. 
        Note: We no longer need the elevenlabs_client, but keep *args 
        to avoid breaking the main.py initialization logic.
        """
        # Replace with your current Ngrok URL from Kaggle
        self.base_url = "https://branchless-corazon-uncoifed.ngrok-free.dev"
        logger.info(f'🎤 AudioGenerator initialized (Kaggle Server: {self.base_url})')
    
    def generate_audio(self, script: str, output_path: str, language: str = "en") -> None:
        """
        Generate MP3 audio from script using custom XTTSv2 server.
        
        Args:
            script: The script text to convert to audio
            output_path: Path where the MP3 file should be saved
            language: Language code (default 'en')
        """
        try:
            start_time = time.time()
            
            # 1. Prepare Request
            # Note: 'effect' can be 'cosmic', 'dramatic', or 'none'
            encoded_text = quote(script)
            api_url = f'{self.base_url}/generate-audio?text={encoded_text}&lang={language}&effect=cosmic'
            
            headers = {
                "ngrok-skip-browser-warning": "true",
                "User-Agent": "VibeRenderWorker/1.0"
            }
            
            logger.info(f'📝 Converting script to audio via Kaggle (len: {len(script)} chars)...')
            
            # 2. Make the request to your Kaggle Server
            response = requests.get(api_url, headers=headers, stream=True, timeout=120)
            
            if response.status_code != 200:
                error_content = response.text[:200]
                raise Exception(f'Kaggle Server returned {response.status_code}: {error_content}')
            
            # 3. Save audio to file
            total_bytes = 0
            with open(output_path, 'wb') as audio_file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        audio_file.write(chunk)
                        total_bytes += len(chunk)
            
            # 4. Final Validation
            elapsed_time = time.time() - start_time
            if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
                raise ValueError(f'Audio file creation failed at {output_path}')
            
            logger.info(f'✅ Audio generated: {elapsed_time:.2f}s | {total_bytes} bytes')
            
        except Exception as e:
            logger.error(f'❌ Kaggle Audio Error: {str(e)}')
            raise Exception(f'Failed to generate audio: {str(e)}')
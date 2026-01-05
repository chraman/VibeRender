"""
Audio generation logic for VibeRender Video Worker.
"""

import os
import time
import logging
import requests
from api_clients import ElevenLabsClient
from config import Config

logger = logging.getLogger(__name__)


class AudioGenerator:
    """Handles audio generation using ElevenLabs."""
    
    def __init__(self, elevenlabs_client: ElevenLabsClient):
        """
        Initialize audio generator.
        
        Args:
            elevenlabs_client: Configured ElevenLabsClient instance
        """
        self.elevenlabs_client = elevenlabs_client.get_client()
        logger.debug('🎤 AudioGenerator initialized')
    
    def generate_audio(self, script: str, output_path: str) -> None:
        """
        Generate MP3 audio from script using ElevenLabs.
        
        Args:
            script: The script text to convert to audio
            output_path: Path where the MP3 file should be saved
            
        Raises:
            Exception: If audio generation fails
        """
        try:
            logger.info('🎤 Getting available voices from ElevenLabs...')
            # Get available voices to find a default voice ID
            # Using the first available voice as default (usually includes Rachel)
            voices = self.elevenlabs_client.voices.get_all()
            logger.debug(f'   Found {len(voices.voices)} available voices')
            
            # Try to find Rachel voice, otherwise use the first available voice
            voice_id = None
            voice_name = None
            for voice in voices.voices:
                if voice.name.lower() == 'rachel':
                    voice_id = voice.voice_id
                    voice_name = voice.name
                    break
            
            # If Rachel not found, use the first available voice
            if not voice_id and voices.voices:
                voice_id = voices.voices[0].voice_id
                voice_name = voices.voices[0].name
            
            if not voice_id:
                raise ValueError('No voices available in ElevenLabs account')
            
            logger.info(f'🎙️  Using voice: {voice_name} (ID: {voice_id})')
            logger.info(f'📝 Converting script to audio (length: {len(script)} characters)...')
            logger.debug(f'   Model: eleven_multilingual_v2')
            logger.debug(f'   Voice settings: stability=0.5, similarity_boost=0.7')
            
            start_time = time.time()
            
            # Call ElevenLabs REST API directly to ensure model_id is explicitly set
            api_url = f'https://api.elevenlabs.io/v1/text-to-speech/{voice_id}'
            headers = {
                'Accept': 'audio/mpeg',
                'Content-Type': 'application/json',
                'xi-api-key': Config.ELEVENLABS_API_KEY
            }
            
            payload = {
                'text': script,
                'model_id': 'eleven_multilingual_v2',
                'voice_settings': {
                    'stability': 0.5,
                    'similarity_boost': 0.7
                }
            }
            
            logger.debug(f'   API URL: {api_url}')
            logger.debug(f'   Request payload: {{"text": "...", "model_id": "eleven_multilingual_v2", "voice_settings": {{"stability": 0.5, "similarity_boost": 0.7}}}}')
            
            # Make the API request
            response = requests.post(api_url, json=payload, headers=headers, stream=True)
            
            # Check for HTTP errors
            if response.status_code != 200:
                error_body = response.text
                try:
                    error_json = response.json()
                    error_message = error_json.get('detail', {}).get('message', error_body)
                except:
                    error_message = error_body
                
                raise Exception(
                    f'ElevenLabs API returned status {response.status_code}: {error_message}'
                )
            
            # Save audio to file using context manager for proper file handling
            total_bytes = 0
            with open(output_path, 'wb') as audio_file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        audio_file.write(chunk)
                        total_bytes += len(chunk)
            
            elapsed_time = time.time() - start_time
            logger.info(f'✅ Audio generation completed in {elapsed_time:.2f} seconds')
            logger.debug(f'   Total bytes received: {total_bytes}')
            
            if not os.path.exists(output_path):
                raise ValueError(f'Audio file was not created at {output_path}')
            
            # Verify file was written and has content
            file_size = os.path.getsize(output_path)
            if file_size == 0:
                raise ValueError(f'Audio file is empty at {output_path}')
            
            logger.info(f'💾 Audio file saved: {output_path} ({file_size} bytes)')
            
        except Exception as e:
            logger.error(f'❌ ElevenLabs API error: {str(e)}')
            raise Exception(f'Failed to generate audio with ElevenLabs: {str(e)}')


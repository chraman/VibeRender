"""
Asset generation module for VibeRender Video Worker.
Handles script generation with Google Gemini and audio conversion with ElevenLabs.
"""

import os
import time
import logging
import pathlib
import requests
from typing import Dict
import google.generativeai as genai
from elevenlabs import ElevenLabs
from config import Config

logger = logging.getLogger(__name__)


def mask_api_key(key: str, show_chars: int = 4) -> str:
    """
    Mask an API key for safe logging.
    Shows first and last N characters with asterisks in between.
    
    Args:
        key: The API key to mask
        show_chars: Number of characters to show at start and end
        
    Returns:
        Masked API key string
    """
    if not key or len(key) <= show_chars * 2:
        return '*' * len(key) if key else 'None'
    
    return f'{key[:show_chars]}...{key[-show_chars:]}'


class AssetGenerator:
    """Handles generation of video assets (script and audio)."""
    
    def __init__(self):
        """Initialize the asset generator with API clients."""
        logger.info('🔧 Initializing AssetGenerator...')
        
        if not Config.GEMINI_API_KEY:
            raise ValueError('GEMINI_API_KEY is not set in environment variables')
        if not Config.ELEVENLABS_API_KEY:
            raise ValueError('ELEVENLABS_API_KEY is not set in environment variables')
        
        # Log API keys (masked for security)
        logger.info('🔑 API Keys Configuration:')
        logger.info(f'   GEMINI_API_KEY: {mask_api_key(Config.GEMINI_API_KEY)} (length: {len(Config.GEMINI_API_KEY)})')
        logger.info(f'   ELEVENLABS_API_KEY: {mask_api_key(Config.ELEVENLABS_API_KEY)} (length: {len(Config.ELEVENLABS_API_KEY)})')
        
        # Configure Google Gemini API
        logger.debug('🔑 Configuring Google Gemini API...')
        genai.configure(api_key=Config.GEMINI_API_KEY)
        self.gemini_model = genai.GenerativeModel('gemini-2.0-flash')
        logger.info('✅ Google Gemini API configured (model: gemini-2.0-flash)')
        
        logger.debug('🔑 Configuring ElevenLabs API...')
        self.elevenlabs_client = ElevenLabs(api_key=Config.ELEVENLABS_API_KEY)
        logger.info('✅ ElevenLabs API configured')
        
        # Ensure temp_assets directory exists
        self.temp_assets_dir = pathlib.Path(Config.TEMP_ASSETS_DIR)
        self.temp_assets_dir.mkdir(exist_ok=True)
        logger.info(f'📁 Assets directory: {self.temp_assets_dir}')
    
    def generate_script(self, topic: str) -> str:
        """
        Generate a 30-second video script using Google Gemini.
        Includes retry logic for rate limit errors.
        
        Args:
            topic: The topic for the video
            
        Returns:
            The generated script text
            
        Raises:
            Exception: If script generation fails after retries
        """
        max_retries = 1
        retry_count = 0
        
        # Construct the prompt with system instructions
        prompt = (
            'You are a professional video script writer. '
            'Create engaging, concise scripts for short-form video content. '
            'Scripts should be exactly 30 seconds when read at a normal pace '
            '(approximately 75-90 words). Make them informative, engaging, and '
            'suitable for YouTube Shorts or TikTok-style content.\n\n'
            f'Write a 30-second video script about: {topic}'
        )
        
        while retry_count <= max_retries:
            try:
                logger.info(f'🤖 Calling Gemini API (attempt {retry_count + 1}/{max_retries + 1})...')
                logger.debug(f'   Prompt length: {len(prompt)} characters')
                
                # Generate content using Gemini
                generation_config = {
                    'temperature': 0.7,
                    'max_output_tokens': 200
                }
                start_time = time.time()
                
                response = self.gemini_model.generate_content(
                    prompt,
                    generation_config=generation_config
                )
                
                elapsed_time = time.time() - start_time
                script = response.text.strip()
                
                logger.info(f'✅ Gemini API response received in {elapsed_time:.2f} seconds')
                logger.debug(f'   Script length: {len(script)} characters')
                
                if not script:
                    raise ValueError('Gemini returned an empty script')
                
                return script
                
            except Exception as e:
                # Check if it's a rate limit error (429 status code or similar)
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
                        raise Exception(f'Failed to generate script: Rate limit exceeded after {max_retries} retry(ies)')
                    else:
                        logger.error(f'❌ Gemini API error: {str(e)}')
                        raise Exception(f'Failed to generate script with Gemini: {str(e)}')
    
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
    
    def generate_assets(self, job_id: int, topic: str) -> Dict[str, str]:
        """
        Generate all assets for a video job (script and audio).
        
        Args:
            job_id: The job ID to use for organizing assets
            topic: The topic for the video
            
        Returns:
            Dictionary with paths to generated assets:
            {
                'script_path': path to script text file,
                'audio_path': path to MP3 audio file
            }
            
        Raises:
            Exception: If asset generation fails
        """
        # Create job-specific directory
        job_dir = self.temp_assets_dir / str(job_id)
        job_dir.mkdir(exist_ok=True)
        
        script_path = job_dir / 'script.txt'
        audio_path = job_dir / 'audio.mp3'
        
        logger.info(f'📝 Step 1/2: Generating script for topic: "{topic}"')
        
        # Generate script
        script = self.generate_script(topic)
        # script = "Visual: Close up on two cats, one wearing a tiny tie, the other looking grumpy. A human hand holds out two small stacks of treats."
        # Save script to file using context manager
        logger.debug(f'💾 Saving script to: {script_path}')
        with open(script_path, 'w', encoding='utf-8') as script_file:
            script_file.write(script)
        
        script_size = os.path.getsize(script_path)
        logger.info(f'✅ Script generated and saved: {script_path} ({script_size} bytes)')
        logger.debug(f'   Script preview: {script[:100]}...')
        
        logger.info(f'🎤 Step 2/2: Generating audio from script...')
        
        # Generate audio
        self.generate_audio(script, str(audio_path))
        
        logger.info(f'✅ All assets generated successfully for job {job_id}')
        
        return {
            'script_path': str(script_path),
            'audio_path': str(audio_path)
        }


def generate_assets(job_id: int, topic: str) -> Dict[str, str]:
    """
    Convenience function to generate assets for a job.
    
    Args:
        job_id: The job ID
        topic: The topic for the video
        
    Returns:
        Dictionary with paths to generated assets
    """
    generator = AssetGenerator()
    return generator.generate_assets(job_id, topic)


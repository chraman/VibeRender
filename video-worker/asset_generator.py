"""
Asset generation module for VibeRender Video Worker.
Handles script generation with Google Gemini and audio conversion with ElevenLabs.
"""

import os
import time
import logging
import pathlib
import random
import requests
from urllib.parse import quote
from typing import Dict, List
from moviepy import AudioFileClip, ImageClip, VideoFileClip, CompositeVideoClip, TextClip, ColorClip
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
                'audio_path': path to MP3 audio file,
                'image_paths': list of paths to generated image files
            }
            
        Raises:
            Exception: If asset generation fails
        """
        # Create job-specific directory
        job_dir = self.temp_assets_dir / str(job_id)
        job_dir.mkdir(exist_ok=True)
        
        script_path = job_dir / 'script.txt'
        audio_path = job_dir / 'audio.mp3'
        
        logger.info(f'📝 Step 1/4: Generating script for topic: "{topic}"')
        
        # Generate script
        script = self.generate_script(topic)
        # script = "Okay, here are a few options for a 30-second video script about petting two puppies, geared for a kids' audience and suitable for short-form video:\n\n**Option 1: Focus on the Cuteness**\n\n**(Visual: Opens with two adorable puppies snuggled together)**\n\n**(Sound: Upbeat, playful music starts immediately)**\n\n**Narrator:** Aww, look at these fluffy friends! (Pause, point at one puppy) Soft fur! (Point at the other) Wiggly tails!\n\n**(Visual: You gently pet both puppies)**\n\n**Narrator:**  The BEST feeling is giving puppy cuddles! (Puppies yawn or look sleepy) Oh, sleepyheads!  They love getting petted.\n\n**(Visual: Close-up on a puppy's face, then back to both puppies)**\n\n**Narrator:**  Who wants to give these cuties a hug?  So sweet! (Music fades out)"
        # Save script to file using context manager
        logger.debug(f'💾 Saving script to: {script_path}')
        with open(script_path, 'w', encoding='utf-8') as script_file:
            script_file.write(script)
        
        script_size = os.path.getsize(script_path)
        logger.info(f'✅ Script generated and saved: {script_path} ({script_size} bytes)')
        logger.debug(f'   Script preview: {script[:100]}...')
        
        # Generate image prompts from the script
        logger.info(f'🖼️  Step 2/4: Generating image prompts from script...')
        image_prompts = self.generate_image_prompts(script)
        logger.info(f'✅ Generated {len(image_prompts)} image prompts')
        
        # Download images for each prompt
        logger.info(f'📥 Step 3/4: Downloading images from Pollinations.ai...')
        image_paths = []
        for index, prompt in enumerate(image_prompts):
            logger.info(f'   Downloading image {index + 1}/{len(image_prompts)}: {prompt[:60]}...')
            image_path = self.download_image(prompt, job_id, index)
            image_paths.append(image_path)
        
        logger.info(f'✅ Downloaded {len(image_paths)} images')
        
        logger.info(f'🎤 Step 4/4: Generating audio from script...')
        
        # Generate audio
        self.generate_audio(script, str(audio_path))
        
        logger.info(f'✅ All assets generated successfully for job {job_id}')
        
        return {
            'script_path': str(script_path),
            'audio_path': str(audio_path),
            'image_paths': image_paths
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


def render_video(script_text: str, audio_path: str, media_paths: List[str], output_path: str) -> None:
    """
    Render a video from existing assets using MoviePy.
    
    Creates a vertical video (1080x1920) with:
    - Images/videos displayed sequentially for equal durations
    - Script text overlaid in center with semi-transparent background
    - Audio synchronized with the video
    
    Args:
        script_text: The script text to display as overlay
        audio_path: Path to the audio file
        media_paths: List of paths to image or video files (supports .jpg, .png, .mp4, etc.)
        output_path: Path where the final video should be saved
        
    Raises:
        Exception: If video rendering fails
    """
    audio_clip = None
    media_clips = []
    text_clip = None
    bg_clip = None
    final_clip = None
    video_clip = None
    
    try:
        logger.info('🎬 Starting video rendering...')
        logger.info(f'   Audio: {audio_path}')
        logger.info(f'   Media files: {len(media_paths)} file(s)')
        logger.info(f'   Output: {output_path}')
        
        # Load audio to get duration
        logger.debug('   Loading audio file...')
        audio_clip = AudioFileClip(audio_path)
        audio_duration = audio_clip.duration
        logger.info(f'   Audio duration: {audio_duration:.2f} seconds')
        
        if not media_paths:
            raise ValueError('No media paths provided for video rendering')
        
        # Calculate duration per media item (equal distribution)
        duration_per_media = audio_duration / len(media_paths)
        logger.debug(f'   Duration per media: {duration_per_media:.2f} seconds')
        
        # Create media clips (images or videos)
        logger.debug('   Creating media clips...')
        for i, media_path in enumerate(media_paths):
            if not os.path.exists(media_path):
                raise FileNotFoundError(f'Media file not found: {media_path}')
            
            # Determine if it's an image or video based on extension
            media_ext = os.path.splitext(media_path)[1].lower()
            is_video = media_ext in ['.mp4', '.mov', '.avi', '.mkv', '.webm']
            is_image = media_ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
            
            if not (is_image or is_video):
                logger.warning(f'   Unknown media type for {media_path}, treating as image')
                is_image = True
            
            logger.debug(f'   Loading {i + 1}/{len(media_paths)}: {media_path} ({media_ext})')
            
            if is_video:
                # Load video clip
                media_clip = VideoFileClip(media_path)
                # If video is longer than allocated duration, trim it
                if media_clip.duration > duration_per_media:
                    media_clip = media_clip.subclipped(0, duration_per_media)
                # If video is shorter, loop it or extend with last frame
                elif media_clip.duration < duration_per_media:
                    # Extend by looping the video
                    loops_needed = int(duration_per_media / media_clip.duration) + 1
                    media_clip = CompositeVideoClip([media_clip] * loops_needed).subclipped(0, duration_per_media)
            else:
                # Create image clip with specified duration
                media_clip = ImageClip(media_path, duration=duration_per_media)
            
            # Resize to 1080x1920 (vertical format) while maintaining aspect ratio
            # Resize to fit height first, then crop/center width
            # MoviePy 2.x uses resized() instead of resize()
            media_clip = media_clip.resized(height=1920)
            
            # If width is less than 1080, we'll center it; if more, crop to center
            if media_clip.w < 1080:
                # Center horizontally by resizing to 1080 and centering
                media_clip = media_clip.resized(width=1080)
            else:
                # Crop to center 1080 pixels
                media_clip = media_clip.cropped(x_center=media_clip.w / 2, width=1080)
            
            # Ensure final size is exactly 1080x1920
            media_clip = media_clip.resized(new_size=(1080, 1920))
            media_clip = media_clip.with_position('center')
            
            # Set start time for this media
            media_clip = media_clip.with_start(i * duration_per_media)
            
            media_clips.append(media_clip)
        
        logger.debug('   Creating composite video from media clips...')
        # Create composite video from all media clips
        video_clip = CompositeVideoClip(media_clips, size=(1080, 1920))
        video_clip = video_clip.with_duration(audio_duration)
        
        # Create text overlay with semi-transparent background
        logger.debug('   Creating text overlay...')
        # Split script into lines for better readability (max ~50 chars per line)
        words = script_text.split()
        lines = []
        current_line = ''
        
        for word in words:
            if len(current_line + ' ' + word) <= 50:
                current_line = current_line + ' ' + word if current_line else word
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        # Join lines with newline
        text_content = '\n'.join(lines)
        
        # Create text clip
        # MoviePy 2.x: Use font_size, text_align, and full font path
        # Try Arial Bold first, fallback to regular Arial, then default
        font_paths = [
            'C:/Windows/Fonts/arialbd.ttf',  # Arial Bold
            'C:/Windows/Fonts/arial.ttf',    # Arial Regular
            None  # Default font
        ]
        
        text_clip = None
        for font_path in font_paths:
            try:
                if font_path:
                    text_clip = TextClip(
                        text=text_content,
                        font=font_path,
                        font_size=40,
                        color='white',
                        method='caption',
                        size=(900, None),  # Width constraint, auto height
                        text_align='center'
                    )
                else:
                    # Fallback: try without explicit font (uses default)
                    text_clip = TextClip(
                        text=text_content,
                        font_size=40,
                        color='white',
                        method='caption',
                        size=(900, None),
                        text_align='center'
                    )
                break
            except Exception as e:
                if font_path is None:  # Last attempt failed
                    logger.error(f'   TextClip creation failed: {e}')
                    raise
                logger.debug(f'   Font {font_path} failed, trying next: {e}')
                continue
        
        # Set text duration to match video (MoviePy 2.0: returns new clip)
        text_clip = text_clip.with_duration(audio_duration)
        
        # Position text in center (MoviePy 2.0: returns new clip)
        text_clip = text_clip.with_position('center')
        
        # Create semi-transparent background for text
        # Make background slightly larger than text
        # MoviePy 2.x: Use font_size and full font path
        bg_font_paths = [
            'C:/Windows/Fonts/arial.ttf',  # Arial Regular
            None  # Default font
        ]
        
        bg_clip = None
        for font_path in bg_font_paths:
            try:
                if font_path:
                    bg_clip = TextClip(
                        text=' ' * 60,  # Wide space for background
                        font=font_path,
                        font_size=1,
                        color='black',
                        bg_color='black',
                        size=(1000, text_clip.h + 40),
                        method='caption'
                    )
                else:
                    # Fallback without explicit font
                    bg_clip = TextClip(
                        text=' ' * 60,
                        font_size=1,
                        color='black',
                        bg_color='black',
                        size=(1000, text_clip.h + 40),
                        method='caption'
                    )
                break
            except Exception as e:
                if font_path is None:  # Last attempt failed
                    logger.warning(f'   Background TextClip creation failed: {e}, continuing without background')
                    # Create a simple colored clip as fallback
                    bg_clip = ColorClip(size=(1000, text_clip.h + 40), color=(0, 0, 0))
                    bg_clip = bg_clip.with_opacity(0.6)
                    break
                logger.debug(f'   Background font {font_path} failed, trying next: {e}')
                continue
        bg_clip = bg_clip.with_duration(audio_duration)
        bg_clip = bg_clip.with_opacity(0.6)  # Semi-transparent (MoviePy 2.0: with_opacity)
        bg_clip = bg_clip.with_position('center')
        
        # Composite everything together
        logger.debug('   Compositing final video...')
        final_clip = CompositeVideoClip([
            video_clip,
            bg_clip,
            text_clip
        ], size=(1080, 1920))
        
        # Add audio (MoviePy 2.0: returns new clip)
        final_clip = final_clip.with_audio(audio_clip)
        final_clip = final_clip.with_duration(audio_duration)
        
        # Export video
        logger.info('   Exporting video (this may take a while)...')
        start_time = time.time()
        final_clip.write_videofile(
            output_path,
            fps=24,
            codec='libx264',
            audio_codec='aac',
            preset='medium',
            logger=None  # Suppress MoviePy's verbose logging
        )
        
        elapsed_time = time.time() - start_time
        file_size = os.path.getsize(output_path)
        
        logger.info(f'✅ Video rendered successfully in {elapsed_time:.2f} seconds')
        logger.info(f'   Output: {output_path} ({file_size} bytes)')
        
    except Exception as e:
        logger.error(f'❌ Video rendering error: {str(e)}')
        raise Exception(f'Failed to render video: {str(e)}')
    
    finally:
        # Clean up MoviePy objects to save RAM
        logger.debug('   Cleaning up MoviePy objects...')
        if audio_clip:
            try:
                audio_clip.close()
            except:
                pass
        
        for clip in media_clips:
            try:
                clip.close()
            except:
                pass
        
        if text_clip:
            try:
                text_clip.close()
            except:
                pass
        
        if bg_clip:
            try:
                bg_clip.close()
            except:
                pass
        
        if video_clip:
            try:
                video_clip.close()
            except:
                pass
        
        if final_clip:
            try:
                final_clip.close()
            except:
                pass
        
        logger.debug('   Cleanup complete')


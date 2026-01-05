"""
Asset generation module for VibeRender Video Worker.
Main coordinator for generating video assets (script, audio, images).
"""

import os
import logging
import pathlib
from typing import Dict
from config import Config
from api_clients import GeminiClient, ElevenLabsClient
from script_generator import ScriptGenerator
from audio_generator import AudioGenerator
from image_generator import ImageGenerator
from video_renderer import render_video

logger = logging.getLogger(__name__)


class AssetGenerator:
    """Handles generation of video assets (script, audio, images)."""
    
    def __init__(self):
        """Initialize the asset generator with API clients and specialized generators."""
        logger.info('🔧 Initializing AssetGenerator...')
        
        # Initialize API clients
        self.gemini_client = GeminiClient(Config.GEMINI_API_KEY)
        self.elevenlabs_client = ElevenLabsClient(Config.ELEVENLABS_API_KEY)
        
        # Initialize specialized generators
        self.script_generator = ScriptGenerator(self.gemini_client)
        self.audio_generator = AudioGenerator(self.elevenlabs_client)
        
        # Ensure temp_assets directory exists
        self.temp_assets_dir = pathlib.Path(Config.TEMP_ASSETS_DIR)
        self.temp_assets_dir.mkdir(exist_ok=True)
        logger.info(f'📁 Assets directory: {self.temp_assets_dir}')
        
        # Initialize image generator (needs temp_assets_dir)
        self.image_generator = ImageGenerator(self.gemini_client, self.temp_assets_dir)
        
        logger.info('✅ AssetGenerator initialized')
    
    def generate_assets(self, job_id: int, topic: str) -> Dict[str, str]:
        """
        Generate all assets for a video job (script, audio, and images).
        
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
        script = self.script_generator.generate_script(topic)
        # Save script to file using context manager
        logger.debug(f'💾 Saving script to: {script_path}')
        with open(script_path, 'w', encoding='utf-8') as script_file:
            script_file.write(script)
        
        script_size = os.path.getsize(script_path)
        logger.info(f'✅ Script generated and saved: {script_path} ({script_size} bytes)')
        logger.debug(f'   Script preview: {script[:100]}...')
        
        # Generate image prompts from the script
        logger.info(f'🖼️  Step 2/4: Generating image prompts from script...')
        image_prompts = self.image_generator.generate_image_prompts(script)
        logger.info(f'✅ Generated {len(image_prompts)} image prompts')
        
        # Download images for each prompt
        logger.info(f'📥 Step 3/4: Downloading images from Pollinations.ai...')
        image_paths = []
        for index, prompt in enumerate(image_prompts):
            logger.info(f'   Downloading image {index + 1}/{len(image_prompts)}: {prompt[:60]}...')
            image_path = self.image_generator.download_image(prompt, job_id, index)
            image_paths.append(image_path)
        
        logger.info(f'✅ Downloaded {len(image_paths)} images')
        
        logger.info(f'🎤 Step 4/4: Generating audio from script...')
        
        # Generate audio
        self.audio_generator.generate_audio(script, str(audio_path))
        
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

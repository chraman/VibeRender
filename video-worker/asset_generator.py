"""
Asset generation module for VibeRender Video Worker.
Main coordinator for generating video assets (script, audio, images).
Updated for Gemini 2.0 (google-genai) and F5-TTS optimization.
"""

import os
import json
import logging
import pathlib
from typing import Dict, Any
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
        """Initialize with updated API clients and specialized generators."""
        logger.info('🔧 Initializing AssetGenerator...')
        
        # Initialize API clients
        # GeminiClient now expects the new google-genai SDK Client architecture
        self.gemini_client = GeminiClient(Config.GEMINI_API_KEY)
        self.elevenlabs_client = ElevenLabsClient(Config.ELEVENLABS_API_KEY)
        
        # Initialize specialized generators
        # We pass the gemini_client which now holds the genai.Client()
        self.script_generator = ScriptGenerator(self.gemini_client)
        self.audio_generator = AudioGenerator(self.elevenlabs_client)
        
        # Ensure temp_assets directory exists
        self.temp_assets_dir = pathlib.Path(Config.TEMP_ASSETS_DIR)
        self.temp_assets_dir.mkdir(exist_ok=True)
        logger.info(f'📁 Assets directory: {self.temp_assets_dir}')
        
        # Initialize image generator (needs temp_assets_dir)
        self.image_generator = ImageGenerator(self.gemini_client, self.temp_assets_dir)
        
        logger.info('✅ AssetGenerator initialized')

    def normalize_narration(self, text: str) -> str:
        """
        Aggressive normalization for F5-TTS pacing.
        Replaces pause-inducing punctuation with spaces to ensure 
        a rapid-fire, high-energy narration delivery.
        """
        # Remove characters that trigger long pauses in TTS engines
        for char in [",", "...", "—", "-", ":", ";"]:
            text = text.replace(char, " ")
        
        # Normalize whitespace
        text = " ".join(text.split())
        return text.strip()

    def generate_assets(self, job_id: int, job: Dict[str, Any]) -> Dict[str, str]:
        """
        Generate all assets for a video job (script, audio, and images).
        
        Args:
            job_id: The job ID to use for organizing assets
            topic: The job for the video
            
        Returns:
            Dictionary with paths to generated assets:
            {
                'script_path': path to script JSON file,
                'narration_path': path to narrator_only.txt file,
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
        narration_path = job_dir / 'narrator_only.txt'
        audio_path = job_dir / 'audio.mp3'
        
        logger.info(f'📝 Step 1/3: Generating script (includes narration and visual prompts) for topic: "{job['topic']}"')
        
        # Generate script (now returns JSON structure)
        script_data = self.script_generator.generate_script(job)
        
        # Extract components from JSON response
        narration = self.normalize_narration(script_data['narration'])
        visual_prompts = script_data['visual_prompts']
        audio_vibe = script_data.get('audio_vibe', '')
        language_code = script_data.get('language_code', '')
        
        logger.debug(f'   Narration length: {len(narration)} characters')
        logger.debug(f'   Visual prompts: {len(visual_prompts)} items')
        logger.debug(f'   Audio vibe: {audio_vibe}')
        logger.debug(f'   Audio vibe: {language_code}')
        
        # Save full JSON structure to script.txt (for debugging)
        logger.debug(f'💾 Saving full JSON to: {script_path}')
        with open(script_path, 'w', encoding='utf-8') as script_file:
            json.dump(script_data, script_file, indent=2, ensure_ascii=False)
        
        script_size = os.path.getsize(script_path)
        logger.info(f'✅ Script JSON saved: {script_path} ({script_size} bytes)')
        
        # Save narration only to narrator_only.txt
        logger.debug(f'💾 Saving narration to: {narration_path}')
        with open(narration_path, 'w', encoding='utf-8') as narration_file:
            narration_file.write(narration)
        
        narration_size = os.path.getsize(narration_path)
        logger.info(f'✅ Narration saved: {narration_path} ({narration_size} bytes)')
        logger.debug(f'   Narration preview: {narration[:100]}...')
        
        # Download images using visual_prompts from script generation (no separate API call needed)
        logger.info(f'📥 Step 2/3: Downloading images from Pollinations.ai using visual prompts from script...')
        image_paths = []
        for index, prompt in enumerate(visual_prompts):
            logger.info(f'   Downloading image {index + 1}/{len(visual_prompts)}: {prompt[:60]}...')
            image_path = self.image_generator.download_image(prompt, job_id, index)
            image_paths.append(image_path)
        
        logger.info(f'✅ Downloaded {len(image_paths)} images')
        
        logger.info(f'🎤 Step 3/3: Generating audio from narration...')
        
        # Generate audio using clean narration text (no labels, no parentheses)
        self.audio_generator.generate_audio(narration, str(audio_path), "Aoede", audio_vibe, language_code)
        
        logger.info(f'✅ All assets generated successfully for job {job_id}')
        
        return {
            'script_path': str(script_path),
            'narration_path': str(narration_path),
            'audio_path': str(audio_path),
            'image_paths': image_paths
        }


def generate_assets(job_id: int, job: Dict[str, Any]) -> Dict[str, str]:
    """
    Convenience function to generate assets for a job.
    
    Args:
        job_id: The job ID
        job: The job for the video
        
    Returns:
        Dictionary with paths to generated assets
    """
    generator = AssetGenerator()
    return generator.generate_assets(job_id, job)

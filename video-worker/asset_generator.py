"""
Asset generation module for VibeRender Video Worker.
Handles script generation with OpenAI and audio conversion with ElevenLabs.
"""

import os
import pathlib
from typing import Dict
from openai import OpenAI
from elevenlabs import generate, set_api_key
from config import Config


class AssetGenerator:
    """Handles generation of video assets (script and audio)."""
    
    def __init__(self):
        """Initialize the asset generator with API clients."""
        if not Config.OPENAI_API_KEY:
            raise ValueError('OPENAI_API_KEY is not set in environment variables')
        if not Config.ELEVENLABS_API_KEY:
            raise ValueError('ELEVENLABS_API_KEY is not set in environment variables')
        
        self.openai_client = OpenAI(api_key=Config.OPENAI_API_KEY)
        set_api_key(Config.ELEVENLABS_API_KEY)
        
        # Ensure temp_assets directory exists
        self.temp_assets_dir = pathlib.Path(Config.TEMP_ASSETS_DIR)
        self.temp_assets_dir.mkdir(exist_ok=True)
    
    def generate_script(self, topic: str) -> str:
        """
        Generate a 30-second video script using OpenAI.
        
        Args:
            topic: The topic for the video
            
        Returns:
            The generated script text
            
        Raises:
            Exception: If script generation fails
        """
        try:
            response = self.openai_client.chat.completions.create(
                model='gpt-4o-mini',
                messages=[
                    {
                        'role': 'system',
                        'content': (
                            'You are a professional video script writer. '
                            'Create engaging, concise scripts for short-form video content. '
                            'Scripts should be exactly 30 seconds when read at a normal pace '
                            '(approximately 75-90 words). Make them informative, engaging, and '
                            'suitable for YouTube Shorts or TikTok-style content.'
                        )
                    },
                    {
                        'role': 'user',
                        'content': f'Write a 30-second video script about: {topic}'
                    }
                ],
                temperature=0.7,
                max_tokens=200
            )
            
            script = response.choices[0].message.content.strip()
            
            if not script:
                raise ValueError('OpenAI returned an empty script')
            
            return script
            
        except Exception as e:
            raise Exception(f'Failed to generate script with OpenAI: {str(e)}')
    
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
            # Generate audio using ElevenLabs
            # Using default voice (Rachel) - can be customized later
            audio = generate(
                text=script,
                voice='Rachel',  # Default voice, can be made configurable
                model='eleven_monolingual_v1'
            )
            
            # Save audio to file using context manager for proper file handling
            # The generate function returns bytes, so we write them directly
            with open(output_path, 'wb') as audio_file:
                audio_file.write(audio)
            
            if not os.path.exists(output_path):
                raise ValueError(f'Audio file was not created at {output_path}')
            
            # Verify file was written and has content
            file_size = os.path.getsize(output_path)
            if file_size == 0:
                raise ValueError(f'Audio file is empty at {output_path}')
            
        except Exception as e:
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
        
        print(f'  📝 Generating script for topic: {topic}')
        
        # Generate script
        script = self.generate_script(topic)
        
        # Save script to file using context manager
        with open(script_path, 'w', encoding='utf-8') as script_file:
            script_file.write(script)
        
        print(f'  ✅ Script generated: {script_path}')
        print(f'  🎤 Generating audio from script...')
        
        # Generate audio
        self.generate_audio(script, str(audio_path))
        
        print(f'  ✅ Audio generated: {audio_path}')
        
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


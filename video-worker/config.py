"""
Configuration module for VibeRender Video Worker.
Loads environment variables for API keys and settings.
"""

import os
from typing import Optional


class Config:
    """Application configuration loaded from environment variables."""
    
    # Google Gemini API Configuration
    GEMINI_API_KEY: Optional[str] = os.getenv('GEMINI_API_KEY')
    
    # ElevenLabs API Configuration
    ELEVENLABS_API_KEY: Optional[str] = os.getenv('ELEVENLABS_API_KEY')
    
    # Database Configuration
    DB_HOST: str = os.getenv('DB_HOST', 'localhost')
    DB_PORT: str = os.getenv('DB_PORT', '5432')
    DB_NAME: str = os.getenv('DB_NAME', 'viberender')
    DB_USER: str = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD: str = os.getenv('DB_PASSWORD', 'postgres')
    
    # Worker Configuration
    POLL_INTERVAL: int = int(os.getenv('POLL_INTERVAL', '5'))
    
    # Asset Storage Configuration
    TEMP_ASSETS_DIR: str = os.getenv('TEMP_ASSETS_DIR', 'temp_assets')
    
    @classmethod
    def validate(cls) -> bool:
        """
        Validate that required API keys are present.
        
        Returns:
            True if all required keys are present, False otherwise
        """
        missing_keys = []
        
        if not cls.GEMINI_API_KEY:
            missing_keys.append('GEMINI_API_KEY')
        
        if not cls.ELEVENLABS_API_KEY:
            missing_keys.append('ELEVENLABS_API_KEY')
        
        if missing_keys:
            print(f'⚠️  Warning: Missing API keys: {", ".join(missing_keys)}')
            print('   Set these as environment variables before running the worker.')
            return False
        
        return True


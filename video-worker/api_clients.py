"""
API client initialization and configuration for VibeRender Video Worker.
"""

import logging
import google.generativeai as genai
from elevenlabs import ElevenLabs
from utils import mask_api_key

logger = logging.getLogger(__name__)


class GeminiClient:
    """Handles Google Gemini API configuration and initialization."""
    
    def __init__(self, api_key: str, model_name: str = 'gemini-2.0-flash'):
        """
        Initialize Gemini API client.
        
        Args:
            api_key: Google Gemini API key
            model_name: Model name to use (default: 'gemini-2.0-flash')
            
        Raises:
            ValueError: If API key is not provided
        """
        if not api_key:
            raise ValueError('GEMINI_API_KEY is not set in environment variables')
        
        logger.info('🔑 API Keys Configuration:')
        logger.info(f'   GEMINI_API_KEY: {mask_api_key(api_key)} (length: {len(api_key)})')
        
        # Configure Google Gemini API
        logger.debug('🔑 Configuring Google Gemini API...')
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        logger.info(f'✅ Google Gemini API configured (model: {model_name})')
    
    def get_model(self):
        """Get the configured Gemini model."""
        return self.model


class ElevenLabsClient:
    """Handles ElevenLabs API configuration and initialization."""
    
    def __init__(self, api_key: str):
        """
        Initialize ElevenLabs API client.
        
        Args:
            api_key: ElevenLabs API key
            
        Raises:
            ValueError: If API key is not provided
        """
        if not api_key:
            raise ValueError('ELEVENLABS_API_KEY is not set in environment variables')
        
        logger.info(f'   ELEVENLABS_API_KEY: {mask_api_key(api_key)} (length: {len(api_key)})')
        
        logger.debug('🔑 Configuring ElevenLabs API...')
        self.client = ElevenLabs(api_key=api_key)
        logger.info('✅ ElevenLabs API configured')
    
    def get_client(self):
        """Get the ElevenLabs client."""
        return self.client


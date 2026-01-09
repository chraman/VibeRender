"""
API client initialization and configuration for VibeRender Video Worker.
"""

import logging
from google import genai
from google.genai import types
from elevenlabs import ElevenLabs
from utils import mask_api_key

logger = logging.getLogger(__name__)


class GeminiClient:
    """Updated for the new google-genai SDK architecture."""
    
    def __init__(self, api_key: str):
        # NEW: The Client is the main entry point, no more 'genai.configure'
        self.client = genai.Client(api_key=api_key)
        logger.info("✅ Gemini 2.0 Client (new SDK) initialized")

    def get_model(self):
        """
        Returns the client. In the new SDK, calls look like:
        client.models.generate_content(model='model-id', ...)
        """
        return self.client

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


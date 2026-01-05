"""
Script generation logic for VibeRender Video Worker.
"""

import time
import logging
from api_clients import GeminiClient

logger = logging.getLogger(__name__)


class ScriptGenerator:
    """Handles script generation using Google Gemini."""
    
    def __init__(self, gemini_client: GeminiClient):
        """
        Initialize script generator.
        
        Args:
            gemini_client: Configured GeminiClient instance
        """
        self.gemini_model = gemini_client.get_model()
        logger.debug('📝 ScriptGenerator initialized')
    
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


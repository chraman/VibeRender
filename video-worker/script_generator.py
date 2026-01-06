"""
Script generation logic for VibeRender Video Worker.
"""

import json
import time
import logging
from typing import Dict, Any
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
    
    def _parse_script_json(self, json_str: str) -> Dict[str, Any]:
        """
        Parse and validate the JSON response from Gemini.
        
        Args:
            json_str: The JSON string to parse
            
        Returns:
            Dictionary with keys: 'narration', 'visual_prompts', 'audio_vibe'
            
        Raises:
            ValueError: If JSON is invalid or missing required fields
        """
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f'Invalid JSON response from Gemini: {str(e)}')
        
        # Validate required keys exist
        required_keys = ['narration', 'visual_prompts', 'audio_vibe']
        missing_keys = [key for key in required_keys if key not in data]
        if missing_keys:
            raise ValueError(f'Missing required keys in JSON response: {missing_keys}')
        
        # Validate visual_prompts is a list with exactly 3 items
        if not isinstance(data['visual_prompts'], list):
            raise ValueError(f'visual_prompts must be a list, got {type(data["visual_prompts"])}')
        
        if len(data['visual_prompts']) != 3:
            raise ValueError(f'visual_prompts must contain exactly 3 items, got {len(data["visual_prompts"])}')
        
        # Validate narration is a string
        if not isinstance(data['narration'], str):
            raise ValueError(f'narration must be a string, got {type(data["narration"])}')
        
        # Validate audio_vibe is a string
        if not isinstance(data['audio_vibe'], str):
            raise ValueError(f'audio_vibe must be a string, got {type(data["audio_vibe"])}')
        
        return data
    
    def generate_script(self, topic: str) -> Dict[str, Any]:
        """
        Generate a 30-second video script using Google Gemini.
        Returns structured JSON with narration, visual prompts, and audio vibe.
        Includes retry logic for rate limit errors.
        
        Args:
            topic: The topic for the video
            
        Returns:
            Dictionary with keys:
                - 'narration': The exact words to be spoken by the AI voice
                - 'visual_prompts': List of 3 image prompts for scenes
                - 'audio_vibe': Description of the tone (e.g., whispering, deep suspenseful bass)
            
        Raises:
            Exception: If script generation fails after retries
            ValueError: If JSON parsing or validation fails
        """
        max_retries = 1
        retry_count = 0
        
        # Construct the prompt with system instructions requesting JSON
        prompt = (
            'You are a professional video script writer. '
            'Create engaging, concise scripts for short-form video content. '
            'Scripts should be exactly 30 seconds when read at a normal pace '
            '(approximately 75-90 words). Make them informative, engaging, and '
            'suitable for YouTube Shorts or TikTok-style content.\n\n'
            f'Write a 30-second video script about: {topic}\n\n'
            'Return your response as a JSON object with the following structure:\n'
            '{\n'
            '  "narration": "The exact words to be spoken by the AI voice. No labels, no parentheses, no stage directions.",\n'
            '  "visual_prompts": [\n'
            '    "Prompt for scene 1 (9:16 aspect ratio, cinematic horror)",\n'
            '    "Prompt for scene 2 (9:16 aspect ratio, cinematic horror)",\n'
            '    "Prompt for scene 3 (9:16 aspect ratio, cinematic horror)"\n'
            '  ],\n'
            '  "audio_vibe": "Description of the tone (e.g., whispering, deep suspenseful bass)"\n'
            '}'
        )
        
        while retry_count <= max_retries:
            try:
                logger.info(f'🤖 Calling Gemini API (attempt {retry_count + 1}/{max_retries + 1})...')
                logger.debug(f'   Prompt length: {len(prompt)} characters')
                
                # Generate content using Gemini with JSON response type
                generation_config = {
                    'temperature': 0.7,
                    'max_output_tokens': 500,
                    'response_mime_type': 'application/json'
                }
                start_time = time.time()
                
                response = self.gemini_model.generate_content(
                    prompt,
                    generation_config=generation_config
                )
                
                elapsed_time = time.time() - start_time
                json_str = response.text.strip()
                
                logger.info(f'✅ Gemini API response received in {elapsed_time:.2f} seconds')
                logger.debug(f'   JSON response length: {len(json_str)} characters')
                
                if not json_str:
                    raise ValueError('Gemini returned an empty response')
                
                # Parse and validate the JSON
                script_data = self._parse_script_json(json_str)
                
                logger.debug(f'   Parsed narration length: {len(script_data["narration"])} characters')
                logger.debug(f'   Visual prompts: {len(script_data["visual_prompts"])} items')
                logger.debug(f'   Audio vibe: {script_data["audio_vibe"]}')
                
                return script_data
                
            except (ValueError, json.JSONDecodeError) as e:
                # JSON parsing/validation errors - don't retry, fail immediately
                logger.error(f'❌ JSON parsing error: {str(e)}')
                raise Exception(f'Failed to parse script JSON: {str(e)}')
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


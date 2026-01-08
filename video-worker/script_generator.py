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
    
    def _extract_json(self, text: str) -> str:
        """
        Extract JSON object from LLM response text.
        """
        start = text.find("{")
        end = text.rfind("}")

        if start == -1 or end == -1 or end <= start:
            raise ValueError("No JSON object found in response")

        return text[start:end + 1]
        
    def _parse_script_json(self, json_str: str) -> Dict[str, Any]:
        try:
            try:
                data = json.loads(json_str)
            except json.JSONDecodeError:
                # Fallback: extract JSON from text
                extracted = self._extract_json(json_str)
                data = json.loads(extracted)

            required_keys = ["narration", "visual_prompts", "audio_vibe"]
            missing = [k for k in required_keys if k not in data]
            if missing:
                raise ValueError(f"Missing required keys in JSON response: {missing}")

            # --- VISUAL PROMPTS VALIDATION ---
            if not isinstance(data["visual_prompts"], list):
                raise ValueError("visual_prompts must be a list")

            visual_count = len(data["visual_prompts"])
            if visual_count < 6 or visual_count > 8:
                raise ValueError(
                    f"visual_prompts must contain between 6 and 8 items, got {visual_count}"
                )

            # --- NARRATION VALIDATION ---
            if not isinstance(data["narration"], str) or not data["narration"].strip():
                raise ValueError("narration must be a non-empty string")

            # --- AUDIO VIBE VALIDATION ---
            if not isinstance(data["audio_vibe"], str) or not data["audio_vibe"].strip():
                raise ValueError("audio_vibe must be a non-empty string")

            return data

        except Exception as e:
            logger.error("❌ Failed to parse Gemini script JSON")
            logger.error(f"Raw Gemini response:\n{json_str}")
            raise

    def generate_script(self, context: Dict[str, Any]) -> Dict[str, Any]:
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
        topic = context["topic"]
        video_theme = context["video_theme"]
        emotional_goal = context["emotional_goal"]
        pacing = context.get("pacing") or "natural"
        category = context.get("category")
        sub_niche = context.get("sub_niche")
        # Construct the prompt with system instructions requesting JSON
        # prompt = (
        #     'You are a professional video script writer. '
        #     'Create engaging, concise scripts for short-form video content. '
        #     'Scripts should be exactly 30 seconds when read at a normal pace '
        #     '(approximately 75-90 words). Make them informative, engaging, and '
        #     'suitable for YouTube Shorts or TikTok-style content.\n\n'
        #     f'CHANNEL CONTEXT:- Category: {category} Sub-niche: {sub_niche}\n'
        #     f'VIDEO INTENT: - Topic: {topic} \n- Theme / Visual Style: {video_theme}\n - Emotional Goal: {emotional_goal}\n - Pacing: {pacing}\n\n'
        #     'IMPORTANT OUTPUT RULES:\n'
        #     '- Respond with ONLY valid JSON\n'
        #     '- Do NOT include markdown\n'
        #     '- Do NOT include explanations\n'
        #     '- Do NOT wrap in ```json\n'
        #     '- Do NOT include any text before or after JSON\n'
        #     '- The response MUST be parseable by json.loads()\n'
        #     '-AUDIO DELIVERY RULES:\n'
        #     '- Speak slightly faster than normal narration\n'
        #     '- Minimal pauses\n'
        #     '- Avoid long dramatic silences\n'
        #     '- Sound engaging and energetic, not slow or cinematic\n'
        #     'REQUIRED JSON SCHEMA (keys must match exactly):\n'
        #     '{\n'
        #     '  "narration": "The exact words to be spoken by the AI voice. No labels, no parentheses, no stage directions.",\n'
        #     '  "visual_prompts": [\n'
        #     '    "Prompt for scene 1 (cinematic, 9:16, aligned with theme)",\n'
        #     '    "Prompt for scene 2 (cinematic, 9:16, escalating tension)",\n'
        #     '    "Prompt for scene 3 (cinematic, 9:16, climax or reveal)"\n'
        #     '  ],\n'
        #     '  "audio_vibe": "Description of the tone (e.g., whispering, deep suspenseful bass)"\n'
        #     '}'
        # )
        
        prompt = f"""
            You are a world-class professional video script writer and visual director 
            Create engaging, concise scripts for short-form video content.

            ASSUME:
            - The viewer has zero patience
            - They can swipe away at any moment
            - The goal is retention, replays, and shares

            VIDEO CONTEXT:
            - Topic: {topic}
            - Channel Category: {category}
            - Sub-niche: {sub_niche}
            - Video Theme / Style: {video_theme}
            - Emotional Goal: {emotional_goal}
            - Pacing: Fast, engaging, no dead air

            OBJECTIVE:
            Create a highly viral 20–30 second YouTube Short.

            CRITICAL STRUCTURE (MANDATORY):
            Divide the script into EXACTLY 3 narrative parts:

            PART 1 — HOOK (0–2 seconds):
            - Start with a bold, counter-intuitive, or curiosity-inducing statement
            - No introductions, no context, no definitions
            - Must immediately stop scrolling

            PART 2 — TENSION BUILD (next 10–15 seconds):
            - Gradually explain the idea WITHOUT fully resolving it
            - Introduce at least one surprising or non-obvious insight
            - Use short, punchy sentences
            - Avoid educational or tutorial tone

            PART 3 — PAYOFF + LOOP (final 3–5 seconds):
            - Deliver a sharp insight or mental model
            - Do NOT fully close the loop
            - End with a thought that encourages rewatching

            SCRIPT RULES:
            - 75–90 words total
            - Conversational, confident, slightly fast-paced
            - No emojis
            - No hashtags
            - No calls to action
            - No summaries or conclusions
            - Do NOT use phrases like "in this video" or "let me explain"

            VISUAL DIRECTION (VERY IMPORTANT):
            - Create 6–8 visuals total
            - Visuals must change every 2–3 seconds
            - Maintain strong visual consistency across scenes

            VISUAL PROMPT RULES:
            - Scene 1–2 correspond to PART 1 (hook visuals)
            - Scene 3–5 correspond to PART 2 (tension visuals)
            - Scene 6–8 correspond to PART 3 (payoff visuals)

            VISUAL PROMPT RULES (FOR DREAMSHAPER XL TURBO):
            Each visual prompt must follow this technical structure:
            1. CORE SUBJECT: Define a consistent character/object description to use in ALL scenes (e.g., "The same monk with a silver beard").
            2. ENVIRONMENT & LIGHTING: Specify "Cinematic lighting," "God rays," or "Neon cyberpunk glow."
            3. CAMERA: Specify "Low angle," "Close-up portrait," or "Wide panoramic."
            4. STYLE WRAPPERS: Always include: "masterpiece, 8k, highly detailed, sharp focus, anatomically correct."
            5. NO DISTORTION: Explicitly avoid mentioning "text," "signatures," or "extra limbs."

            AUDIO DELIVERY:
            - Slightly faster than normal narration
            - Minimal pauses
            - Confident and engaging
            - Not slow, not overly dramatic
            
            AUDIO VIBE CATEGORIES:
            - You MUST choose EXACTLY one of these vibes for the "audio_vibe" field: 
              [cosmic, epic, horror]
            - Choose the vibe that best matches the script's emotional goal.

            OUTPUT FORMAT (STRICT):
            - Return ONLY valid JSON
            - Do NOT include markdown
            - Do NOT include explanations
            - Do NOT include text before or after JSON
            - Response must be directly parseable by json.loads()

            REQUIRED JSON SCHEMA:
            {{
            "narration": "Full narration text only",
            "visual_prompts": [
                "Scene 1: Hook Subject, close-up, [Style Wrappers]",
                "Scene 2: Hook Subject, different angle, [Style Wrappers]",
                "Scene 3: Tension Subject, environment shift, [Style Wrappers]",
                "Scene 4: Tension Subject, action shot, [Style Wrappers]",
                "Scene 5: Tension Subject, macro detail, [Style Wrappers]",
                "Scene 6: Payoff Subject, epic wide shot, [Style Wrappers]",
                "Scene 7: Payoff Subject, final mysterious look, [Style Wrappers]"
            ],
            "audio_vibe": "horror"
            }}
            """.strip()

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


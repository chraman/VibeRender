import json
import re
import logging
from typing import Dict, Any
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

class ScriptGenerator:
    """Handles script generation using Gemini 2.0 Thinking for optimized TTS pacing."""
    
    def __init__(self, gemini_client: Any):
        # Initializing with the new GenAI Client
        self.client = gemini_client.get_model()
        # Using the specific Thinking Experimental model
        self.model_id = "gemini-3-flash-preview"
        logger.info(f'📝 ScriptGenerator initialized with {self.model_id}')

    def _clean_json_string(self, text: str) -> str:
        """Helper to remove common LLM JSON artifacts like trailing commas."""
        # Remove trailing commas before a closing brace or bracket
        text = re.sub(r',\s*([\]}])', r'\1', text)
        # Remove any leading/trailing non-JSON characters (like markdown backticks)
        json_match = re.search(r"\{.*\}", text, re.DOTALL)
        return json_match.group() if json_match else text
    
    def _get_narration(self, context: Dict[str, Any]) -> str:
        """Step 1: Generate script with 'Thinking' enabled to plan pacing and duration."""

        # Define genre-specific "vibe" instructions to inject into the prompt
        genre_profiles = {
            "horror stories": "Guttural, staccato sentences, heavy on atmosphere and sudden shocks.",
            "sci-fi stories": "Cold, clinical, high-tech terminology, pulsating rhythm.",
            "action": "Verbal explosions, punchy verbs, zero fluff, high kinetic energy.",
            "noir": "Rhythmic, cynical, slow-burn tension that snaps at the end."
        }
        
        selected_vibe = genre_profiles.get(context['sub_niche'].lower(), "Dynamic and cinematic.")
        # We calculate a word budget: 45 seconds - pauses = ~90 words max.
        prompt = f"""
           Act as a Director and Lead Editor for a 45-second cinematic short.
        
            GENRE: {context['sub_niche']}
            TOPIC: {context['topic']}
            EMOTION: {context['emotional_goal']}
            Language Code: Choose exactly one from [en-US, hi-IN].

            TASK:
            Create a 45-second story blueprint. 
            Focus on deep descriptive detail that captures the 'mood' and 'action' of each scene.

            CONSTRAINTS:
            1. CHARACTER DNA: Define a consistent physical anchor (clothing, features, age).
            2. NARRATION: Fast-paced third-person script (Max 80 words). Use [fast] and [PAUSE=0.5s].
            3. SCENE DETAILS: Describe the setting, the action, and the lighting for 3 scenes. No technical prompts—just vivid descriptions.

            TTS TAGS: Use [fast], [slow], [intense], and [PAUSE=0.5s].
            Output only valid JSON. Do not include trailing commas after the last item in a list or object. Ensure the output is strictly parseable by the Python json.loads() library.
            JSON OUTPUT:
            {{
                "narration": "The full script for TTS....",
                "character_dna": "Detailed physical description of the protagonist."
                "language_code": "Language Code",
                "storyboard": [
                    {{
                    "sequence": "Hook",
                    "timing": "0-7s",
                    "scene_description": "A vivid description of the environment and the character's initial action.",
                    "emotional_beat": "The specific feeling this scene should evoke."
                    }},
                    {{
                    "sequence": "Twist",
                    "timing": "7-30s",
                    "scene_description": "How the environment or character changes. Detail the subtle 'wrong' element.",
                    "emotional_beat": "The shift in mood."
                    }},
                    {{
                    "sequence": "Payoff",
                    "timing": "30-45s",
                    "scene_description": "The final climactic imagery and the character's end state.",
                    "emotional_beat": "The lingering impact."
                    }}
                ]
            }}
        """.strip()

        response = self.client.models.generate_content(
            model=self.model_id,
            contents=prompt,
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(include_thoughts=True),
                temperature=0.9, # Slightly lower for better constraint following
                response_mime_type="application/json"
            )
        )

        # Extracting text while skipping 'thought' parts
        actual_text = "".join(
            [part.text for part in response.candidates[0].content.parts if not hasattr(part, 'thought') or not part.thought]
        )

        actual_text = "".join(
            [part.text for part in response.candidates[0].content.parts if not hasattr(part, 'thought') or not part.thought]
        )

        try:
            cleaned_json = self._clean_json_string(actual_text)
            data = json.loads(cleaned_json)
            return data
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Step 1 Parsing failed. Raw Text: {actual_text[:200]}...")
            raise
    
    def generate_script(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Orchestrates the 2-step generation with thinking-enabled visuals."""
        
        # STEP 1: Narration
        logger.info("🤖 Step 1: Thinking about Narration & Pacing...")
        narration = self._get_narration(context)
        
        # STEP 2: Visuals & Vibe (Requesting Structured JSON)
        logger.info("🤖 Step 2: Planning Visual Director logic...")
        visual_prompt = f"""
            Act as a professional Cinematographer and FLUX.1-schnell Visual Architect.
    
            TASK: 
            Convert the following 3-act storyboard into 5 descriptive, natural-language image prompts optimized for FLUX.1-schnell.
            
            INPUT DATA:
            - CHARACTER ANCHOR: {narration['character_dna']}
            - THEME/STYLE: {context['video_theme']}
            - STORY DETAILS: {narration['storyboard']}
            - Audio Vibe: Choose exactly one from [cosmic, epic, horror].
            - Language Code: {narration['language_code']}

            CRITICAL INSTRUCTIONS:
            1. COMPOSITION OVER CHARACTER: Do not start every prompt with the Character DNA. Start with the "Scene Setup" or "Camera Angle" to ensure the story world is rendered.
            2. THE INTERACTION: Ensure the character is INTERACTING with objects or the environment mentioned in the storyboard.
            3. FLUX NATURAL LANGUAGE: Describe the scene in 2-3 descriptive sentences. Avoid keyword "tag" clouds.
            4. CONSISTENCY: Use the Character DNA as a recurring descriptive anchor, but integrate it naturally.
            5. STYLE: Apply the '{context['video_theme']}' art style consistently.

            Output only valid JSON. Do not include trailing commas after the last item in a list or object. Ensure the output is strictly parseable by the Python json.loads() library.
            OUTPUT JSON STRUCTURE:
            {{
                "narration": "{narration['narration']}",
                "character_dna": "{narration['character_dna']}",
                "visual_prompts": [
                    "Shot 1 (The Hook): [Style] style. [Wide/Establishing shot]. Describe the environment first, then place [Character DNA] within it, establishing the routine.",
                    "Shot 2 (Development): [Style] style. [Medium shot]. Focus on the character's interaction with a specific object or setting detail from the storyboard.",
                    "Shot 3 (The Twist): [Style] style. [Dutch angle or Close-up]. Highlight the 'wrong' or 'subtle' detail. The character's [Key DNA details] should be secondary to the haunting element.",
                    "Shot 4 (Reaction): [Style] style. [Extreme Close-up]. Focus on the character's facial expression and the shift in lighting/atmosphere.",
                    "Shot 5 (The Payoff): [Style] style. [Climactic composition]. The visual realization of the payoff. Focus on the transformation or high-stakes reveal mentioned in the storyboard."
                ],
                "audio_vibe": "Audio Vibe",
                "language_code": "Language Code",
                "storyboard_reference": {narration['storyboard']}
            }}
        """.strip()

        # Step 2 uses standard JSON response type
        response = self.client.models.generate_content(
            model=self.model_id,
            contents=visual_prompt,
            config=types.GenerateContentConfig(
                response_mime_type='application/json',
                temperature=0.4
            )
        )
# FIX 1: Fixed the logging crash by using a format string
        logger.debug("Step 2 Raw Response: %s", response.text)

        actual_text = "".join(
            [part.text for part in response.candidates[0].content.parts if not hasattr(part, 'thought') or not part.thought]
        )

        try:
            # FIX 2: Applied cleaning logic to Step 2 as well
            cleaned_json = self._clean_json_string(actual_text)
            data = json.loads(cleaned_json)
            
            # Injecting storyboard back if missing (safety)
            if 'storyboard_reference' not in data:
                data['storyboard_reference'] = narration.get('storyboard')
                
            return data
        except (json.JSONDecodeError, ValueError) as e:
            # FIX 3: Detailed error logging to see what specifically broke
            logger.error("Step 2 JSON Parsing failed: %s", e)
            logger.error("Problematic Text: %s", actual_text)
            raise
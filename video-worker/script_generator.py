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
            2. SYNCHRONIZED NARRATION: The narration must act as a 'play-by-play' of the visual action. If the scene description says the character is running, the narration must reflect that immediate tension. Use [fast], [slow], [intense], and [PAUSE=0.5s].
            3. SCENE DETAILS: Describe the setting, the action, and the lighting for 5 scenes. No technical prompts—just vivid descriptions.
            4. 5-ACT STRUCTURE: You must provide exactly 5 storyboard items to ensure a smooth visual flow (Inciting Incident, Rising Action, The Twist, The Reaction, The Payoff).


            TTS TAGS: Use [fast], [slow], [intense], and [PAUSE=0.5s].
            Output only valid JSON. Do not include trailing commas after the last item in a list or object. Ensure the output is strictly parseable by the Python json.loads() library.
            JSON OUTPUT:
            {{
                "narration_full": "The full script for TTS....",
                "character_dna": "Detailed physical description of the protagonist."
                "language_code": "Language Code",
                "storyboard": [
                    {{
                    "sequence": "Hook",
                    "timing": "0-5s",
                    "scene_description": "A vivid description of the environment and the character's initial action.",
                    "scene_narration": "Narration specifically for these 0-5s seconds",
                    "emotional_beat": "The specific feeling this scene should evoke."
                    }},
                    {{
                    "sequence": "The Build (5-12s)",
                    "timing": "5-12s",
                    "scene_description": "A secondary action that develops the story. Focus on a specific object or interaction.",
                    "scene_narration": "Narration specifically for these 5-12s seconds",
                    "emotional_beat": "Rising tension."
                    }},
                    {{
                    "sequence": "The Shift (12-18s)",
                    "timing": "12-18s",
                    "scene_description": "The moment something changes. Detail the 'wrong' or 'unusual' element visually.",
                    "scene_narration": "Narration specifically for these 12-18s seconds",
                    "emotional_beat": "The Twist."
                    }},
                    {{
                    "sequence": "The Reaction (18-24s)",
                    "timing": "18-24s",
                    "scene_description": "A close-up shot of the character's emotional or physical response to the shift.",
                    "scene_narration": "Narration specifically for these 18-24s seconds",
                    "emotional_beat": "High stakes."
                    }},
                    {{
                    "sequence": "The Payoff (24-28s)",
                    "timing": "24-28s",
                    "scene_description": "The final climactic imagery and the character's end state.",
                    "scene_narration": "Narration specifically for these 24-28s seconds",
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
        # visual_prompt = f"""
        #     Act as a professional Cinematographer and FLUX.1-schnell Visual Architect.
    
        #     TASK: 
        #     Convert the following 3-act storyboard into 5 descriptive, natural-language image prompts optimized for FLUX.1-schnell.
            
        #     INPUT DATA:
        #     - CHARACTER ANCHOR: {narration['character_dna']}
        #     - THEME/STYLE: {context['video_theme']}
        #     - STORYBOARD BEATS: {narration['storyboard']}
        #     - Audio Vibe: Choose exactly one from [cosmic, epic, horror].
        #     - Language Code: {narration['language_code']}
            
        #     CRITICAL INSTRUCTIONS FOR PROMPT ARCHITECTURE RULES FOR FLUX:
        #     1. START WITH THE FRAME: Always begin with the lens, lighting, or camera perspective (e.g., "A low-angle wide shot," "Candid 35mm film photography," "Soft morning light hits...").
        #     2. SEAMLESS DNA: Integrate the {narration['character_dna']} naturally. Do not just list traits; describe the character doing the action (e.g., "The silver-haired man in the tattered trench coat reaches for...").
        #     3. NO PLACEHOLDERS: Do not use brackets like [Style] or [Shot 1]. Write in full, flowing sentences.
        #     4. SENSORY DETAIL: Describe textures, weather, and specific lighting (e.g., "neon reflections on wet pavement," "dust motes dancing in a sunbeam").
        #     5. STYLE CONSISTENCY: Every prompt must embody the '{context['video_theme']}' aesthetic without explicitly saying "in the style of." Describe the visual elements that make up that style.


        #     Output only valid JSON. Do not include trailing commas after the last item in a list or object. Ensure the output is strictly parseable by the Python json.loads() library.
        #     OUTPUT JSON STRUCTURE:
        #     {{
        #         "narration": "{narration['narration_full']}",
        #         "character_dna": "{narration['character_dna']}",
        #         "visual_prompts": [
        #             "Shot 1 (The Hook) description",
        #             "Shot 2 (Development) description",
        #             "Shot 3 (The Twist) description",
        #             "Shot 4 (Reaction) description",
        #             "Shot 5 (The Payoff) description."
        #         ],
        #         "audio_vibe": "Audio Vibe",
        #         "language_code": "Language Code",
        #         "storyboard_reference": {narration['storyboard']}
        #     }}
        # """.strip()

        visual_prompt = f"""
            Act as a professional Cinematographer and FLUX.1-schnell Visual Architect.

            TASK: 
            Convert the following 5-beat storyboard into 5 descriptive, natural-language image prompts. 
            Each prompt must be a standalone cinematic masterpiece that ensures visual continuity.

            INPUT DATA:
            - CHARACTER DNA: {narration['character_dna']}
            - VISUAL THEME: {context['video_theme']}
            - STORYBOARD BEATS: {narration['storyboard']}
            - Audio Vibe: Choose exactly one from [cosmic, epic, horror].
            - Language Code: {narration['language_code']}

            CRITICAL CONTINUITY LOGIC:
            1. REACTION SHOTS: If a storyboard beat mentions 'Reaction' or 'Awe', do NOT use a POV shot. Use an 'Over-the-shoulder' or 'Medium Close-up' so the character's facial expression and DNA are visible.
            2. THE RED THREAD: The red Kalava thread mentioned in the DNA must be a visual anchor in every shot where hands are visible.
            3. TRANSITIONS: Ensure Shot 4 visually explains the transition from the 'Shadow' in Shot 3 to the 'Physical Hand' in Shot 4.
            4. WEIGHT & SCALE: Explicitly describe the scale difference between the small boy and the colossal deity to emphasize the 'Epic' vibe.

            FLUX PROMPT ARCHITECTURE:
            1. START WITH THE FRAME: Begin with lens/lighting (e.g., "A wide-angle 2D game art style shot bathed in cinematic morning gold...").
            2. SEAMLESS DNA: Do not list traits. Describe the character performing the action (e.g., "Aryan, with his messy curly hair and faded blue uniform, grips his heavy bag...").
            3. NO PLACEHOLDERS: Write in flowing, natural prose. No brackets.
            4. STYLE: Apply the '{context['video_theme']}' aesthetic through descriptive textures (e.g., cel-shading, parallax layers, hand-painted gradients).

            Output only valid JSON. Ensure it is strictly parseable by python json.loads().
            OUTPUT JSON STRUCTURE:
            {{
                "narration": "{narration['narration_full']}",
                "character_dna": "{narration['character_dna']}",
                "visual_prompts": [
                    "Shot 1: The Hook. Environment-first, establishing the sprint and the departing bus.",
                    "Shot 2: The Build. Focus on physical struggle, exhaustion, and the weight of the bag.",
                    "Shot 3: The Shift. Introduce the colossal shadow and the Gada. Maintain the side-profile scale.",
                    "Shot 4: The Reaction. Over-the-shoulder shot showing Aryan’s face as the divine hand descends.",
                    "Shot 5: The Payoff. High-speed action shot with golden energy trails and the deity in the clouds."
                ],
                "audio_vibe": "Audio Vibe",
                "language_code": "Language Code",
        #       "storyboard_reference": {narration['storyboard']}
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
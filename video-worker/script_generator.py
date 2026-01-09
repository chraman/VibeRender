import json
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

    def _get_narration(self, context: Dict[str, Any]) -> str:
        """Step 1: Generate script with 'Thinking' enabled to plan pacing."""
        prompt = f"""
            Act as a world-class short-form copywriter.
            Topic: {context['topic']}
            Category: {context['category']}
            Goal: {context['emotional_goal']}
            
            F5-TTS OPTIMIZATION REQUIREMENTS:
            1. SPEED: The audio must be fast and high-energy.
            2. NO PAUSES: Do not use commas, ellipses, or dashes. 
            3. WORD COUNT: Exactly 80-85 words for a 25-second duration.
            
            THINKING PROCESS:
            Before writing the script, analyze how to achieve a 'rapid-fire' pace 
            without using punctuation that triggers TTS pauses.
            
            RETURN ONLY THE FINAL SCRIPT TEXT.
        """.strip()

        # Call with Thinking Config
        response = self.client.models.generate_content(
            model=self.model_id,
            contents=prompt,
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(include_thoughts=True),
                temperature=0.7
            )
        )
        return response.text.strip()

    def generate_script(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Orchestrates the 2-step generation with thinking-enabled visuals."""
        
        # STEP 1: Narration
        logger.info("🤖 Step 1: Thinking about Narration & Pacing...")
        narration = self._get_narration(context)
        
        # STEP 2: Visuals & Vibe (Requesting Structured JSON)
        logger.info("🤖 Step 2: Planning Visual Director logic...")
        visual_prompt = f"""
            Based on this script: "{narration}"
            Generate 7 cinematic visual prompts in {context['video_theme']} style.
            
            - Theme: {context['video_theme']}
            - Topic: {context['topic']}
            - Style: Real-world, high-stakes cinematography.
            - Audio Vibe: Choose exactly one from [cosmic, epic, horror].

            OUTPUT MUST BE VALID JSON:
            {{
                "narration": "{narration}",
                "visual_prompts": ["Scene 1...", "Scene 2...", "..."],
                "audio_vibe": "vibe"
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
        
        return json.loads(response.text)
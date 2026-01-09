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
            Act as a world-class Story Architect.
            Topic: {context['topic']}
            Goal: {context['emotional_goal']} (Make it deeply relatable and haunting)

            TASK:
            Create a complete narrative blueprint for a 25-30 second cinematic short.

            NARRATIVE ARCHITECTURE:
            1. HOOK: A common, relatable routine or memory (e.g., bedtime, a drawing, a toy).
            2. TWIST: A subtle, "wrong" detail that twists that routine.
            3. PAYOFF: A high-stakes payoff that leaves the viewer breathless.

            TTS PERFORMANCE GUIDELINES:
            - Use expressive tags in square brackets like [whispering], [sighing], [laughing], or [shouting] to direct the voice.
            - Use [PAUSE=1s] for dramatic silences.
            - Use natural punctuation (..., !, ?) to guide the model's native prosody.

            REQUIRED OUTPUT STRUCTURE (JSON ONLY):
            {{
                "character_dna": "Define a consistent physical anchor for the main character (e.g., 'A 5-year-old girl named Lily, raven-black bob hair, pale skin, wearing a tattered teal silk nightgown').",
                "narration": "Write the full story script. Use natural punctuation (commas, ellipses) for cinematic pacing since TTS speed restrictions are removed.",
                "storyboard": [
                    {{
                        "sequence": "Hook",
                        "description": "Describe the relatable safe start. Focus on the mood and the character's initial state."
                    }},
                    {{
                        "sequence": "Twist",
                        "description": "Describe the moment reality shifts. Focus on the subtle 'wrong' detail."
                    }},
                    {{
                        "sequence": "Payoff",
                        "description": "Describe the climactic final visual. Focus on high-impact horror/drama."
                    }}
                ]
            }}
        """.strip()

        # Call with Thinking Config
        response = self.client.models.generate_content(
            model=self.model_id,
            contents=prompt,
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(include_thoughts=True),
                temperature=1.0
            )
        )
        raw_text = response.text
        # FIX: Extract text by filtering out "thinking" parts
        actual_text = ""
        if response.candidates and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                # If the part has a 'thought' attribute and it's True, skip it
                if hasattr(part, 'thought') and part.thought:
                    continue
                if part.text:
                    actual_text += part.text

        if not actual_text:
            logger.error("❌ Gemini returned an empty response. Check safety filters.")
            raise ValueError("Empty response from AI")

        # Clean and parse JSON
        try:
            clean_json = actual_text.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_json)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON. Raw text: {actual_text[:100]}...")
            raise

    def generate_script(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Orchestrates the 2-step generation with thinking-enabled visuals."""
        
        # STEP 1: Narration
        logger.info("🤖 Step 1: Thinking about Narration & Pacing...")
        narration = self._get_narration(context)
        
        # STEP 2: Visuals & Vibe (Requesting Structured JSON)
        logger.info("🤖 Step 2: Planning Visual Director logic...")
        visual_prompt = f"""
            Act as a professional Cinematographer and SDXL Prompt Engineer. 
            TASK: Convert the 3-act storyboard into 5 distinct, highly-detailed technical image prompts.

            INPUT DATA:
            - Character DNA: {narration['character_dna']}
            - Storyboard: {narration['storyboard']}
            - Art Style: {context['video_theme']}.

          
            OUTPUT MUST BE VALID JSON:
            {{
                "narration": "{narration['narration']}",
                "visual_prompts": [
                    "Shot 1 (Establishing): [Character DNA] + [Environment details]",
                    "Shot 2 (Routine): [Character DNA] + [Specific action] ",
                    "Shot 3 (The Wrong Detail): [Character DNA] + [Macro focus on object] + [Deep ink shadows]",
                    "Shot 4 (Reaction): [Character DNA] + [Expression details]",
                    "Shot 5 (The Payoff): [Character DNA] + [Climax action] + [Splash page climax]"
                ],
                "audio_vibe": "horror"
                "character_dna": "{narration['character_dna']}"
                "storyboard": {narration['storyboard']}
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
        logger.info("🤖 Step 2: Planning Visual Director logic...",response.text )
        return json.loads(response.text)
import os
import io
import logging
from pydub import AudioSegment
from google import genai
from google.genai import types

# Define the absolute path to your ffmpeg bin folder
FFMPEG_PATH = r"C:\Projects\ffmpeg-2026-01-07-git-af6a1dd0b2-essentials_build\bin"

# 1. Update the System Path for the current Python session
os.environ["PATH"] += os.pathsep + FFMPEG_PATH

# 2. Tell Pydub exactly where the binaries are
AudioSegment.converter = os.path.join(FFMPEG_PATH, "ffmpeg.exe")
AudioSegment.ffprobe = os.path.join(FFMPEG_PATH, "ffprobe.exe")

logger = logging.getLogger(__name__)

class AudioGenerator:
    """Handles audio generation using Gemini 2.5 TTS and mixes with background atmosphere."""
    
    def __init__(self, *args, **kwargs):
        self.client = genai.Client()
        self.model_id = "gemini-2.5-flash-preview-tts"
        self.atmosphere_dir = "media"  # Folder where your bg music lives
        logger.info(f'🎤 AudioGenerator initialized (Model: {self.model_id})')
    
    def _mix_atmosphere(self, voice_segment, vibe):
        """Internal helper to overlay background music."""
        bg_path = os.path.join(self.atmosphere_dir, f"{vibe.lower()}.mp3")
        
        if not os.path.exists(bg_path):
            logger.warning(f"⚠️ Atmosphere file {bg_path} not found. Returning raw voice.")
            return voice_segment

        try:
            logger.info(f"⚠️ Atmosphere file {bg_path} found. Returning raw voice.")
            background = AudioSegment.from_file(bg_path)
            # Reduce background volume (ducking) so voice is clear
            background = background - 22 
            
            # Overlay music on voice, looping the music if the voice is longer
            combined = voice_segment.overlay(background, loop=True)
            # Add a cinematic fade out
            return combined.fade_out(2000)
        except Exception as e:
            logger.error(f"Failed to mix atmosphere: {e}")
            return voice_segment

    def generate_audio(self, script: str, output_path: str, voice_name: str = "Aoede", vibe: str = None) -> None:
        """Generates MP3 audio and optionally mixes it with a background vibe."""
        try:
            clean_script = script.strip()
            # 1. Formatting the prompt to ensure tags are followed
            # We tell Gemini explicitly to follow the [PAUSE] and [vocal] tags.
            full_prompt = (
                "Perform this script as a voice actor. Follow all instructions in brackets like [PAUSE=1s] "
                "or [whispering] by actually performing them. Do not speak the brackets aloud. "
                f"Script: {clean_script}"
            )

            config = types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=voice_name
                        )
                    )
                )
            )

            logger.info(f'📝 Sending to Gemini: "{clean_script[:50]}..."')
            
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=full_prompt,
                config=config
            )

            # 1. Load raw PCM from Gemini into Pydub
            audio_bytes = response.candidates[0].content.parts[0].inline_data.data
            voice_segment = AudioSegment.from_raw(
                io.BytesIO(audio_bytes),
                sample_width=2,
                frame_rate=24000,
                channels=1
            )

            # 2. Apply Atmosphere if a vibe is provided
            if vibe:
                logger.info(f"🎵 Mixing with atmosphere: {vibe}")
                final_audio = self._mix_atmosphere(voice_segment, vibe)
            else:
                final_audio = voice_segment

            # 3. Export to MP3
            final_audio.export(output_path, format="mp3", bitrate="192k")
            logger.info(f'✅ Audio generated successfully: {output_path}')

        except Exception as e:
            logger.error(f'❌ Gemini TTS Error: {str(e)}')
            raise Exception(f'Failed to generate audio: {str(e)}')

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    gen = AudioGenerator()
    
    # Ensure this folder exists for the test to work!
    if not os.path.exists("Atmosphere"):
        os.makedirs("Atmosphere")
        print("Created Atmosphere folder. Please add a 'horror.mp3' for testing.")

    test_script = "The routine was always the same. I'd tuck her in, kiss her forehead, and check under the bed. But tonight, she wasn't looking at me. She was looking behind me."
    test_output = "cinematic_test.mp3"
    
    print(f"\n--- Starting Cinematic Test ---")
    try:
        # Pass the 'vibe' here (matching a filename in your Atmosphere folder)
        gen.generate_audio(test_script, test_output, voice_name="Aoede", vibe="horror")
        
        if os.path.exists(test_output):
            print(f"✅ Success! Check {test_output}")
            
    except Exception as e:
        print(f"❌ Test Failed: {e}")
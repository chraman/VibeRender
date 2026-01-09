import os
import io
import logging
from pydub import AudioSegment
from google import genai
from google.genai import types
from pydub import AudioSegment

# Replace this with the actual path to where you extracted ffmpeg.exe
AudioSegment.converter = r"C:\Projects\ffmpeg-2026-01-07-git-af6a1dd0b2-essentials_build\bin\ffmpeg.exe"
logger = logging.getLogger(__name__)

class AudioGenerator:
    """Handles audio generation using Gemini 2.5 TTS and exports to MP3."""
    
    def __init__(self, *args, **kwargs):
        # Initialize the client (ensure GOOGLE_API_KEY is in your environment)
        self.client = genai.Client()
        # The -preview suffix is required for the current TTS model
        self.model_id = "gemini-2.5-flash-preview-tts"
        logger.info(f'🎤 AudioGenerator initialized (Model: {self.model_id})')
    
    def _export_to_mp3(self, pcm_data, output_path):
        """Converts raw 24kHz PCM data from Gemini to MP3 format."""
        try:
            # Gemini's native output is raw PCM: 24000Hz, 16-bit, Mono
            audio = AudioSegment.from_raw(
                io.BytesIO(pcm_data),
                sample_width=2,    # 16-bit
                frame_rate=24000,  # 24kHz
                channels=1         # Mono
            )
            # Export to MP3
            audio.export(output_path, format="mp3", bitrate="192k")
        except Exception as e:
            logger.error(f"Failed to convert PCM to MP3: {e}")
            raise

    def generate_audio(self, script: str, output_path: str, voice_name: str = "Aoede") -> None:
        """Generates MP3 audio from text using Gemini TTS."""
        try:
            clean_script = script.strip()
            
            # Request configuration for native audio generation
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
            
            # Using generate_content for TTS
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=f"Read this naturally and clearly: {clean_script}",
                config=config
            )

            # Extract the raw PCM bytes
            # Part 0 contains the inline_data which is the audio stream
            audio_bytes = response.candidates[0].content.parts[0].inline_data.data
            
            # Convert and Save as MP3
            self._export_to_mp3(audio_bytes, output_path)
            
            logger.info(f'✅ Audio generated successfully: {output_path}')

        except Exception as e:
            logger.error(f'❌ Gemini TTS Error: {str(e)}')
            # Re-raise to let the main worker handle the failure
            raise Exception(f'Failed to generate MP3: {str(e)}')

if __name__ == "__main__":
    # Configure basic logging to see the output in your terminal
    logging.basicConfig(level=logging.INFO)
    
    # 1. Initialize the generator
    # Make sure your GOOGLE_API_KEY is set in your environment variables
    gen = AudioGenerator()
    
    # 2. Define a test script and output path
    test_script = "Hello! This is a test of the Gemini text to speech engine. Everything seems to be working perfectly."
    test_output = "test_gemini_audio.mp3"
    
    print(f"\n--- Starting Standalone Test ---")
    try:
        # 3. Run the generation
        # You can try different voices here: "Aoede", "Kore", "Charon", "Fenrir"
        gen.generate_audio(test_script, test_output, voice_name="Aoede")
        
        # 4. Final check
        if os.path.exists(test_output):
            size = os.path.getsize(test_output)
            print(f"✅ Success! Generated: {test_output} ({size} bytes)")
        else:
            print(f"❌ Failed: File was not created.")
            
    except Exception as e:
        print(f"❌ Test Failed with error: {e}")
    print(f"--- Test Finished ---\n")
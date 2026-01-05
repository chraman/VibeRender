"""
Standalone script to test ElevenLabs API with a default script.
Can be called from the Next.js UI to test audio generation without Gemini.
"""

import sys
import os
import pathlib
from elevenlabs import ElevenLabs
from config import Config

# Default test script (30-second video script)
DEFAULT_SCRIPT = """Welcome to this quick guide! Today we're exploring something exciting. 
In just 30 seconds, you'll learn something new and useful. 
Let's dive right in and discover what makes this topic special. 
Remember, the best way to learn is by doing. 
So let's get started on this journey together!"""


def test_elevenlabs_audio(script: str = None, output_path: str = None):
    """
    Test ElevenLabs audio generation with a default or provided script.
    
    Args:
        script: Script text to convert (uses default if not provided)
        output_path: Path to save audio file (uses default if not provided)
        
    Returns:
        Dictionary with success status and file path
    """
    try:
        if not Config.ELEVENLABS_API_KEY:
            return {
                'success': False,
                'error': 'ELEVENLABS_API_KEY is not set in environment variables'
            }
        
        # Use default script if not provided
        test_script = script or DEFAULT_SCRIPT
        
        # Use default output path if not provided
        if not output_path:
            temp_dir = pathlib.Path(Config.TEMP_ASSETS_DIR) / 'test'
            temp_dir.mkdir(parents=True, exist_ok=True)
            output_path = str(temp_dir / 'test_audio.mp3')
        
        print(f'[TEST] Testing ElevenLabs API...')
        print(f'[TEST] Script length: {len(test_script)} characters')
        print(f'[TEST] Output path: {output_path}')
        
        # Initialize ElevenLabs client
        client = ElevenLabs(api_key=Config.ELEVENLABS_API_KEY)
        
        # Get available voices
        print(f'[TEST] Fetching available voices...')
        voices = client.voices.get_all()
        
        # Try to find Rachel voice, otherwise use the first available voice
        voice_id = None
        voice_name = None
        for voice in voices.voices:
            if voice.name.lower() == 'rachel':
                voice_id = voice.voice_id
                voice_name = voice.name
                break
        
        # If Rachel not found, use the first available voice
        if not voice_id and voices.voices:
            voice_id = voices.voices[0].voice_id
            voice_name = voices.voices[0].name
        
        if not voice_id:
            return {
                'success': False,
                'error': 'No voices available in ElevenLabs account'
            }
        
        print(f'[TEST] Using voice: {voice_name} (ID: {voice_id})')
        print(f'[TEST] Generating audio...')
        
        # Generate audio
        audio_generator = client.text_to_speech.convert(
            voice_id=voice_id,
            text=test_script,
            model_id='eleven_monolingual_v1',
            output_format='mp3_44100_128'
        )
        
        # Save audio to file
        chunk_count = 0
        total_bytes = 0
        with open(output_path, 'wb') as audio_file:
            for chunk in audio_generator:
                if chunk:
                    audio_file.write(chunk)
                    chunk_count += 1
                    total_bytes += len(chunk)
        
        file_size = os.path.getsize(output_path)
        
        if file_size == 0:
            return {
                'success': False,
                'error': 'Audio file was created but is empty'
            }
        
        print(f'[TEST] ✅ Audio generated successfully!')
        print(f'[TEST] File size: {file_size} bytes')
        print(f'[TEST] Chunks received: {chunk_count}')
        
        return {
            'success': True,
            'audio_path': output_path,
            'file_size': file_size,
            'voice_used': voice_name,
            'script_length': len(test_script)
        }
        
    except Exception as e:
        error_msg = str(e)
        print(f'[TEST] ❌ Error: {error_msg}')
        return {
            'success': False,
            'error': error_msg
        }


if __name__ == '__main__':
    # Allow script to be called with optional script text
    # If script is provided, use it; otherwise use default
    script = None
    if len(sys.argv) > 1:
        # Join all arguments in case script contains spaces
        script = ' '.join(sys.argv[1:])
        # Unescape newlines if they were escaped
        script = script.replace('\\n', '\n')
    
    result = test_elevenlabs_audio(script)
    
    # Print result as JSON for easy parsing
    import json
    print('\n[RESULT]', json.dumps(result))


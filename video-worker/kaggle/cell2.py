import requests
import os
import io
import numpy as np
import noisereduce as nr
import librosa
import soundfile as sf
from pydub import AudioSegment
from pydub.effects import compress_dynamic_range, normalize

def clean_reference_audio(input_path, output_path):
    """
    CLEANING THE SOURCE:
    Removes the background hiss from 'sample (1).wav' so the AI doesn't clone it.
    """
    # Load audio (XTTS prefers 24kHz)
    y, sr = librosa.load(input_path, sr=24000)
    
    # Perform non-stationary noise reduction
    # prop_decrease=0.90 ensures we don't make the voice sound 'robotic' or 'hollow'
    reduced_noise = nr.reduce_noise(y=y, sr=sr, prop_decrease=0.90, stationary=False)
    
    # Save the cleaned reference
    sf.write(output_path, reduced_noise, sr)
    print(f"Cleaned reference saved to: {output_path}")

def master_vocal_chain(segment: AudioSegment):
    """
    THE 'THICK' NARRATOR CHAIN:
    Applies professional mastering to the generated AI voice.
    """
    # 1. High-Pass Filter: Removes low-end 'mud' (rumble below 80Hz)
    mastered = segment.high_pass_filter(80)
    
    # 2. Dynamic Compression: The 'Secret Sauce'
    # This squeezes the audio so the quiet parts and loud parts are closer together,
    # making the voice sound thick, authoritative, and 'forward' in the mix.
    # threshold: where it starts working | ratio: how much it squeezes
    mastered = compress_dynamic_range(
        mastered, 
        threshold=-18.0, 
        ratio=4.0, 
        attack=5.0, 
        release=50.0
    )
    
    # 3. Frequency Boost (Subtle EQ): 
    # Boost lower-mids for warmth and highs for clarity
    mastered = mastered.low_shelf_filter(300, gain=2) # Warmth
    
    # 4. Final Normalization
    # Ensures the peak is at -1.0 dB (industry standard)
    return normalize(mastered, headroom=1.0)

# --- EXECUTION EXAMPLE ---
# 1. Clean your sample file once before starting the server
# Download a professional narrator sample
url = "https://github.com/coqui-ai/TTS/raw/main/tests/data/ljspeech/wavs/LJ001-0001.wav"
r = requests.get(url)
with open("/kaggle/working/sample.wav", "wb") as f:
    f.write(r.content)
print("✅ Voice sample 'sample.wav' ready at /kaggle/working/")
clean_reference_audio("sample.wav", "sample_cleaned.wav")
# Define your library
library = {
    "cosmic": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3", # Replace with real SFX links
    "epic": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3",
    "horror": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.mp3"
}

# Download them to the working directory
for name, url in library.items():
    path = f"/kaggle/working/{name}.mp3"
    if not os.path.exists(path):
        print(f"Downloading {name}...")
        r = requests.get(url)
        with open(path, "wb") as f:
            f.write(r.content)
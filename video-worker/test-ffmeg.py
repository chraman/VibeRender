import os
import shutil
from pydub import AudioSegment

# 1. SET THE PATH (Use the exact path to your bin folder)
ffmpeg_bin = r"C:\Projects\ffmpeg-2026-01-07-git-af6a1dd0b2-essentials_build\bin"

# 2. FORCE THE ENVIRONMENT (Crucial for VS Code)
os.environ["PATH"] += os.pathsep + ffmpeg_bin

# 3. DIRECT ASSIGNMENT TO PYDUB
AudioSegment.converter = os.path.join(ffmpeg_bin, "ffmpeg.exe")
AudioSegment.ffprobe = os.path.join(ffmpeg_bin, "ffprobe.exe")

print("--- Diagnostics ---")
print(f"Checking ffmpeg.exe: {'✅ Found' if os.path.exists(AudioSegment.converter) else '❌ MISSING'}")
print(f"Checking ffprobe.exe: {'✅ Found' if os.path.exists(AudioSegment.ffprobe) else '❌ MISSING'}")

# 4. VERIFY SYSTEM ACCESS
ffmpeg_actual_path = shutil.which("ffmpeg")
print(f"System sees ffmpeg at: {ffmpeg_actual_path}")

try:
    # Try a simple pydub operation that requires ffprobe
    test_audio = AudioSegment.silent(duration=100)
    print("✅ Pydub can now process audio!")
except Exception as e:
    print(f"❌ Pydub test failed: {e}")
import requests
# Download a professional narrator sample
url = "https://github.com/coqui-ai/TTS/raw/main/tests/data/ljspeech/wavs/LJ001-0001.wav"
r = requests.get(url)
with open("/kaggle/working/sample.wav", "wb") as f:
    f.write(r.content)
print("✅ Voice sample 'sample.wav' ready at /kaggle/working/")
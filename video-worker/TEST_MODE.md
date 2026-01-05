# Test Mode Guide

## How to Enable Test Mode

Test mode allows you to test video rendering without making API calls to Gemini or ElevenLabs.

### Step 1: Enable TEST_MODE

Open `video-worker/main.py` and change line 44:

```python
# Change this:
TEST_MODE = False

# To this:
TEST_MODE = True
```

### Step 2: Place Test Assets

Create the following test assets in the `video-worker/temp_assets/test/` directory:

**Required files:**
- `temp_assets/test/script.txt` - A text file containing the script to display on the video
- `temp_assets/test/test_audio.mp3` - An MP3 audio file (any duration)
- `temp_assets/test/*.jpg` or `temp_assets/test/*.mp4` - One or more image or video files

**Supported formats:**
- **Images:** `.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`
- **Videos:** `.mp4`, `.mov`, `.avi`, `.mkv`, `.webm`

### Step 3: Create Test Assets Directory

If the directory doesn't exist, create it:

```bash
cd video-worker
mkdir -p temp_assets/test
```

### Step 4: Add Your Test Files

Place your test files in `video-worker/temp_assets/test/`:
- `script.txt` - Your script text (will be overlaid on the video)
- `test_audio.mp3` - Your test audio file
- `image1.jpg`, `image2.jpg`, etc. - Your test image files (or video files like `video1.mp4`)

### Step 5: Run the Worker

Start the worker as normal:

```bash
cd video-worker
python main.py
```

When a job is processed, it will:
- ✅ Skip asset generation (no API calls)
- ✅ Use your test assets
- ✅ Render the video using the test assets
- ✅ Save output to `temp_assets/{job_id}/video.mp4`

## Test Assets Requirements

### Script File (`script.txt`)
- **Format:** Plain text file
- **Location:** `video-worker/temp_assets/test/script.txt`
- **Content:** The script text that will be overlaid on the video
- **Example:** 
  ```
  This is a test script for VibeRender.
  It can be multiple lines.
  The text will be word-wrapped and displayed with a semi-transparent background.
  ```

### Audio File (`test_audio.mp3`)
- **Format:** MP3
- **Location:** `video-worker/temp_assets/test/test_audio.mp3`
- **Duration:** Any duration (will determine video length)
- **Example:** You can use any MP3 file, or generate one using ElevenLabs manually

### Media Files (Images or Videos)
- **Formats:** 
  - Images: `.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`
  - Videos: `.mp4`, `.mov`, `.avi`, `.mkv`, `.webm`
- **Location:** `video-worker/temp_assets/test/` (any filename)
- **Quantity:** One or more files (all will be used in sequence)
- **Size:** Any size (will be automatically resized/cropped to 1080x1920)
- **Example:** 
  - `image1.jpg`, `image2.jpg`, `image3.jpg`
  - `video1.mp4`, `video2.mp4`
  - Mix of images and videos: `image1.jpg`, `video1.mp4`, `image2.jpg`

## Disabling Test Mode

To return to normal operation, change `TEST_MODE` back to `False` in `main.py`:

```python
TEST_MODE = False
```

## Example: Creating Test Assets

### Option 1: Use Existing Assets
If you have existing assets from a previous job, you can copy them:

```bash
# Create test directory
mkdir -p temp_assets/test

# Copy script from a previous job
cp temp_assets/21/script.txt temp_assets/test/script.txt

# Copy audio from a previous job
cp temp_assets/21/audio.mp3 temp_assets/test/test_audio.mp3

# Copy images from a previous job
cp temp_assets/21/scene_21_0.jpg temp_assets/test/image1.jpg
cp temp_assets/21/scene_21_1.jpg temp_assets/test/image2.jpg
cp temp_assets/21/scene_21_2.jpg temp_assets/test/image3.jpg
```

### Option 2: Download Sample Assets
You can download sample assets from the internet or create them manually.

### Option 3: Generate Test Audio
You can use ElevenLabs API directly or any TTS service to generate `test_audio.mp3`.

## Troubleshooting

**Error: "Test script not found"**
- Make sure `temp_assets/test/script.txt` exists
- Check the file path is correct (relative to `video-worker/` directory)

**Error: "Test audio not found"**
- Make sure `temp_assets/test/test_audio.mp3` exists
- Check the file path is correct (relative to `video-worker/` directory)

**Error: "No image or video files found"**
- Make sure you have at least one image or video file in `temp_assets/test/`
- Supported formats: `.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.mp4`, `.mov`, `.avi`, `.mkv`, `.webm`
- Files are automatically discovered - just place them in the test directory

**Video not rendering:**
- Check that both test files exist and are valid
- Ensure MoviePy is installed: `pip install moviepy`
- Check the logs for specific error messages


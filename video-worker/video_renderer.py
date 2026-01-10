import os
import logging
import random
import numpy as np
from PIL import Image
from typing import List

try:
    from moviepy import AudioFileClip, VideoClip, VideoFileClip, CompositeVideoClip, TextClip
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO)
except ImportError:
    raise ImportError("Please install moviepy: pip install moviepy")

# ---------------------------------------------------------
# DYNAMIC MOTION ENGINE (Zoom + Random Shift)
# ---------------------------------------------------------
def create_animated_image_clip(image_path, duration, target_size=(1080, 1920)):
    # 1. Load and initial "Fill" to target size
    pil_img = Image.open(image_path).convert("RGB")
    orig_w, orig_h = pil_img.size
    target_w, target_h = target_size

    # 2. ASPECT RATIO COVER (The "Fill" logic)
    # Determine the minimum scale needed to cover the screen
    scale_to_cover = max(target_w / orig_w, target_h / orig_h)
    
    # 3. QUALITY CHECK
    # If the image is already smaller than the screen, we limit the zoom
    # If the image is huge (4K), we can zoom more safely.
    if orig_w < target_w or orig_h < target_h:
        # Image is low-res, use a very tiny motion to prevent blur
        zoom_intensity = 1.05 
        buffer_factor = 1.05
    else:
        # Image is high-res, we can afford a bit more motion
        zoom_intensity = 1.12 
        buffer_factor = 1.10

    # 4. PRE-RESIZE (Prepare the base canvas)
    # We scale it just enough to cover + buffer, no more.
    base_w = int(orig_w * scale_to_cover * buffer_factor)
    base_h = int(orig_h * scale_to_cover * buffer_factor)
    pil_img = pil_img.resize((base_w, base_h), Image.Resampling.LANCZOS)

    # 5. RANDOM DRIFT RANGE
    # Drift is limited to the 'buffer' area only
    max_dx = (base_w - target_w) // 2
    max_dy = (base_h - target_h) // 2
    
    dx_start, dx_end = random.randint(-max_dx, max_dx), random.randint(-max_dx, max_dx)
    dy_start, dy_end = random.randint(-max_dy, max_dy), random.randint(-max_dy, max_dy)

    def make_frame(t):
        progress = t / duration
        
        # Linear Zoom & Drift
        curr_zoom = 1.0 + (zoom_intensity - 1.0) * progress
        curr_dx = dx_start + (dx_end - dx_start) * progress
        curr_dy = dy_start + (dy_end - dy_start) * progress
        
        # Calculate zoomed dimensions
        z_w, z_h = int(base_w * curr_zoom), int(base_h * curr_zoom)
        img_zoomed = pil_img.resize((z_w, z_h), Image.Resampling.LANCZOS)
        
        # Center-based crop coordinates
        center_x, center_y = img_zoomed.width // 2, img_zoomed.height // 2
        
        # Final Crop Coordinates
        left = (center_x - target_w // 2) + curr_dx
        top = (center_y - target_h // 2) + curr_dy
        
        # Final safety clamp to prevent black edges
        left = max(0, min(left, img_zoomed.width - target_w))
        top = max(0, min(top, img_zoomed.height - target_h))
        
        img_final = img_zoomed.crop((left, top, left + target_w, top + target_h))
        
        frame = np.array(img_final)
        
        # Smooth Fade-In
        if t < 0.4:
            frame = (frame * (t / 0.4)).astype(np.uint8)
            
        return frame

    from moviepy import VideoClip
    return VideoClip(make_frame, duration=duration)
# ---------------------------------------------------------
# SUBTITLE ENGINE
# ---------------------------------------------------------
def build_subtitles(script_text, audio_duration):
    logger.info("...Generating Subtitles")
    font_path = "C:/Windows/Fonts/arialbd.ttf"
    if not os.path.exists(font_path): font_path = "Arial"

    words = script_text.split()
    phrases = [" ".join(words[i:i+3]) for i in range(0, len(words), 3)]
    dur_per_phrase = audio_duration / max(len(phrases), 1)
    
    clips = []
    for i, phrase in enumerate(phrases):
        txt = (TextClip(
            text=phrase.upper(),
            font=font_path,
            font_size=80,
            color="white",
            stroke_color="black",
            stroke_width=2,
            method="caption",
            size=(900, 400)
        ).with_start(i * dur_per_phrase)
         .with_duration(dur_per_phrase)
         .with_position(("center", 1300)))
        
        # Text clips in v2 usually work better with static opacity
        # If you need them to fade, use the same np.array logic as above
        clips.append(txt)
    return clips

# ---------------------------------------------------------
# MAIN RENDERER
# ---------------------------------------------------------
def render_video(script_text: str, audio_path: str, media_paths: List[str], output_path: str):
    logger.info("🎬 Starting Render Process")
    
    try:
        from moviepy import AudioFileClip, CompositeVideoClip
        audio_clip = AudioFileClip(audio_path)
        audio_dur = audio_clip.duration
        slot_dur = audio_dur / len(media_paths)
        
        final_clips = []
        for i, path in enumerate(media_paths):
            # Create the dynamic clip
            # Every time this runs, it picks new random drift/zoom values
            clip = create_animated_image_clip(path, slot_dur)
            clip = clip.with_start(i * slot_dur)
            final_clips.append(clip)
            
        # ... (Include subtitle building code from previous step) ...
        sub_clips = build_subtitles(script_text, audio_dur)

        final_video = CompositeVideoClip(
            final_clips + sub_clips, 
            size=(1080, 1920)
        ).with_audio(audio_clip).with_duration(audio_dur)

        final_video.write_videofile(
            output_path,
            fps=30,
            codec="libx264",
            audio_codec="aac",
            threads=4,
            preset="ultrafast"
        )
        logger.info(f"✅ Video saved to: {output_path}")

    except Exception as e:
        logger.error(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'audio_clip' in locals(): audio_clip.close()
        if 'final_video' in locals(): final_video.close()
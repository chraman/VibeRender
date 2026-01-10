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
    
    # Calculate scale to fill the 1080x1920 area completely (Aspect Ratio Cover)
    target_w, target_h = target_size
    img_w, img_h = pil_img.size
    scale_f = max(target_w / img_w, target_h / img_h)
    
    # Base size is now slightly larger than target to allow for motion buffer
    # We add 20% extra padding (1.2x) so we never see black edges while drifting
    buffer_factor = 1.2 
    fill_w = int(img_w * scale_f * buffer_factor)
    fill_h = int(img_h * scale_f * buffer_factor)
    
    pil_img = pil_img.resize((fill_w, fill_h), Image.Resampling.LANCZOS)
    
    # --- RANDOMIZE MOTION ---
    zoom_start = 1.0
    zoom_end = random.uniform(1.1, 1.2) # Zooming in further
    
    # Random drift range (now safe because we have the 20% buffer)
    max_dx = (fill_w - target_w) // 2
    max_dy = (fill_h - target_h) // 2
    
    dx_start, dx_end = random.randint(-max_dx, max_dx), random.randint(-max_dx, max_dx)
    dy_start, dy_end = random.randint(-max_dy, max_dy), random.randint(-max_dy, max_dy)

    def make_frame(t):
        progress = t / duration
        
        # Calculate current zoom and drift
        curr_zoom = zoom_start + (zoom_end - zoom_start) * progress
        curr_dx = dx_start + (dx_end - dx_start) * progress
        curr_dy = dy_start + (dy_end - dy_start) * progress
        
        # Resize for zoom
        z_w, z_h = int(fill_w * curr_zoom), int(fill_h * curr_zoom)
        # Optimization: Only resize if zoom is significantly different
        img_zoomed = pil_img.resize((z_w, z_h), Image.Resampling.LANCZOS)
        
        # Calculate center-based crop
        center_x, center_y = img_zoomed.width // 2, img_zoomed.height // 2
        
        # Final Crop Coordinates
        left = (center_x - target_w // 2) + curr_dx
        top = (center_y - target_h // 2) + curr_dy
        
        # Final safety clamp to prevent black edges
        left = max(0, min(left, img_zoomed.width - target_w))
        top = max(0, min(top, img_zoomed.height - target_h))
        
        img_final = img_zoomed.crop((left, top, left + target_w, top + target_h))
        
        frame = np.array(img_final)
        
        # Fade-in effect logic
        if t < 0.5:
            alpha = t / 0.5
            frame = (frame * alpha).astype(np.uint8)
            
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
import os
import logging
import random
import numpy as np
from PIL import Image
from typing import List
import re
import whisper

try:
    from moviepy import AudioFileClip, VideoClip, VideoFileClip, CompositeVideoClip, TextClip
    logger = logging.getLogger(__name__)
except ImportError:
    raise ImportError("Please install moviepy: pip install moviepy")

# ---------------------------------------------------------
# DYNAMIC MOTION ENGINE (Zoom + Random Shift)
# ---------------------------------------------------------
def create_animated_image_clip(image_path, duration, target_size=(1080, 1920)):
    # 1. Load and prepare high-res base
    pil_img = Image.open(image_path).convert("RGB")
    tw, th = target_size
    
    # Scale to cover target + 20% extra "playing field" for the camera to move
    # This is crucial: if you don't have extra image, you can't have motion!
    scale_f = max(tw / pil_img.width, th / pil_img.height) * 1.20 
    base_w, base_h = int(pil_img.width * scale_f), int(pil_img.height * scale_f)
    pil_img = pil_img.resize((base_w, base_h), Image.Resampling.LANCZOS)

    # 2. DEFINE A RANDOM FLIGHT PATH
    # We pick a starting corner and an ending corner
    # This ensures vertical, horizontal, and diagonal movement
    move_types = ['zoom_in', 'zoom_out', 'pan_up', 'pan_down', 'pan_left', 'pan_right']
    mode = random.choice(move_types)
    
    # Calculate how much "extra" image we have to move within
    limit_x = base_w - tw
    limit_y = base_h - th

    # Start and End coordinates (X, Y)
    if mode == 'pan_up':
        start_x, start_y = limit_x // 2, limit_y
        end_x, end_y = limit_x // 2, 0
    elif mode == 'pan_down':
        start_x, start_y = limit_x // 2, 0
        end_x, end_y = limit_x // 2, limit_y
    elif mode == 'pan_right':
        start_x, start_y = 0, limit_y // 2
        end_x, end_y = limit_x, limit_y // 2
    else: # Default/Zoom modes
        start_x, start_y = random.randint(0, limit_x), random.randint(0, limit_y)
        end_x, end_y = random.randint(0, limit_x), random.randint(0, limit_y)

    def make_frame(t):
        # Progress from 0.0 to 1.0
        p = t / duration
        
        # Calculate current position using linear interpolation (Lerp)
        curr_x = int(start_x + (end_x - start_x) * p)
        curr_y = int(start_y + (end_y - start_y) * p)
        
        # Subtle dynamic zoom (independent of panning)
        # Even while panning, we zoom in an extra 5%
        zoom_p = 1.0 + (0.07 * p) 
        
        # Crop the window
        img_frame = pil_img.crop((curr_x, curr_y, curr_x + tw, curr_y + th))
        
        # Apply the final micro-zoom
        if zoom_p > 1.0:
            zw, zh = int(tw * zoom_p), int(th * zoom_p)
            img_frame = img_frame.resize((zw, zh), Image.Resampling.BILINEAR)
            # Crop back to center
            left = (zw - tw) // 2
            top = (zh - th) // 2
            img_frame = img_frame.crop((left, top, left + tw, top + th))

        # Convert to numpy for MoviePy
        frame = np.array(img_frame)

        # 3. Add a dynamic "Flash" or "Fade" at the start
        if t < 0.3:
            # Quick brightness ramp-up (Flash effect)
            factor = t / 0.3
            frame = (frame * factor).astype(np.uint8)
            
        return frame

    from moviepy import VideoClip
    return VideoClip(make_frame, duration=duration)
# ---------------------------------------------------------
# SUBTITLE ENGINE
# ---------------------------------------------------------
def build_subtitles(script_text, audio_path):
    # 1. Load Whisper (CPU optimized for your 16GB RAM)
    model = whisper.load_model("base", device="cpu")
    
    # Force language and disable translation
    # word_timestamps=True is the key for "one-by-one" appearance
    result = model.transcribe(
        audio_path,
        word_timestamps=True, 
        language="en", 
        task="transcribe",
        max_initial_timestamp=None,
        no_speech_threshold=0.6,
        condition_on_previous_text=False)
    
    # 2. Clean your original script (Ensures NO translation is used)
    clean_text = re.sub(r'\[.*?\]', '', script_text)
    original_words = clean_text.split()
    
    clips = []
        # 3. Extract EVERY word timestamp from Whisper
    all_word_timestamps = []
    for segment in result['segments']:
        for word_data in segment['words']:
            all_word_timestamps.append({
                'start': word_data['start'],
                'end': word_data['end']
            })

    # --- POP ANIMATION FUNCTION ---
    def pop_effect(get_frame, t):
        frame = get_frame(t)
        if t < 0.1:
            zoom = 1.2 - (0.2 * (t / 0.1))
            img = Image.fromarray(frame)
            w, h = img.size
            img = img.resize((int(w*zoom), int(h*zoom)), Image.Resampling.LANCZOS)
            left = (img.size[0] - w) / 2
            top = (img.size[1] - h) / 2
            return np.array(img.crop((left, top, left + w, top + h)))
        return frame

    # --- UPDATED SYNC LOOP ---
    last_end_time = 0
    for i in range(len(original_words)):
        # If Whisper missed words at the end, use the last known timing
        if i < len(all_word_timestamps):
            word_info = all_word_timestamps[i]
            start_t = word_info['start']
            end_t = word_info['end']
            last_end_time = end_t
        else:
            # SAFETY: If script is longer than Whisper's detection, 
            # show remaining words briefly at the very end
            start_t = last_end_time
            end_t = last_end_time + 0.3 
            last_end_time = end_t

        color = "white" if i % 2 == 0 else "yellow"
        
        txt = (TextClip(
            text=original_words[i].upper(),
            font="C:/Windows/Fonts/arialbd.ttf",
            font_size=130, 
            color=color,
            stroke_color="black",
            stroke_width=6,
            method="label",
            transparent=True,
             # Label is better for single words
            margin=(20, 40)
        ).with_start(start_t)
         .with_duration(max(0.1, end_t - start_t)) # Ensure duration is never 0
         .with_position(("center", 0.7), relative=True))

        txt = txt.transform(pop_effect)
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
        # sub_clips = build_subtitles(script_text, audio_dur)
        sub_clips = build_subtitles(script_text, audio_path)

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
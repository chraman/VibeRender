import os
import logging
import random
import numpy as np
from typing import List
from moviepy import (
    AudioFileClip,
    ImageClip,
    VideoFileClip,
    CompositeVideoClip,
    TextClip
)
from moviepy.video.VideoClip import VideoClip
logger = logging.getLogger(__name__)


# ---------------------------------------------------------
# RANDOM KEN-BURNS STYLE ZOOM + DRIFT (MoviePy 2.1.2 SAFE)
# ---------------------------------------------------------
def apply_random_motion(clip, duration):
    import random
    import math

    zoom_in = random.choice([True, False])
    zoom_amount = random.uniform(1.02, 1.08)

    start_zoom = 1.0
    end_zoom = zoom_amount if zoom_in else (1.0 / zoom_amount)

    # Pan drift (smooth)
    drift_x = random.randint(-120, 120)
    drift_y = random.randint(-150, 150)

    # --- Smoothed zoom animation ---
    def size_func(t):
        p = max(0, min(1, t / duration))
        ease = 3 * p**2 - 2 * p**3
        zoom = start_zoom + (end_zoom - start_zoom) * ease
        return (int(clip.w * zoom), int(clip.h * zoom))

    # --- Smoothed position drift ---
    def pos_func(t):
        p = max(0, min(1, t / duration))
        ease = 3 * p**2 - 2 * p**3

        offset_x = int(drift_x * ease)
        offset_y = int(drift_y * ease)

        # VALID MoviePy format:  (x, y)
        return ("center", offset_y)

    clip = clip.resized(size_func)
    clip = clip.with_position(pos_func)

    return clip

def get_font_path():
    """
    Returns a valid font path for MoviePy on Windows.
    Fallback order:
    1. Arial Bold
    2. Arial Regular
    3. No font (TextClip will use default)
    """
    arial_bold = "C:/Windows/Fonts/arialbd.ttf"
    arial_regular = "C:/Windows/Fonts/arial.ttf"

    if os.path.exists(arial_bold):
        return arial_bold
    if os.path.exists(arial_regular):
        return arial_regular

    return None  # MoviePy will fallback (not recommended)


# ---------------------------------------------------------
# SUBTITLES (Stable for MoviePy 2.1.2)
# ---------------------------------------------------------
def build_subtitles(script_text: str, audio_duration: float, font_path: str):
    words = script_text.split()
    phrase_groups = []

    i = 0
    while i < len(words):
        n = random.randint(5, 8)
        phrase_groups.append(" ".join(words[i:i + n]))
        i += n

    num_phrases = len(phrase_groups)
    dur = audio_duration / num_phrases

    clips = []

    for idx, phrase in enumerate(phrase_groups):

        clip = TextClip(
            text=phrase,
            font=font_path,
            color="white",
            stroke_color="black",
            stroke_width=3,
            method="caption",
            size=(900, 400),
            text_align="center",
            vertical_align="center"
        )

        clip = (
            clip.with_start(idx * dur)
                .with_duration(dur)
                .with_position(("center", 1350))
                .with_fps(24)
        )

        clips.append(clip)

    return clips

def build_subtitles_s2(script_text: str, audio_duration: float):
    """
    S2-PRO SUBTITLE ENGINE
    - Groups text into 5–8 word segments
    - Fixed block height (prevents jitter)
    - Crisp readable font
    - Very fast rendering
    """
    
    words = script_text.strip().split()
    total_words = len(words)

    # Best for Shorts retention
    MIN_W, MAX_W = 5, 8

    segments = []
    i = 0
    while i < total_words:
        seg_len = random.randint(MIN_W, MAX_W)
        segment = " ".join(words[i:i + seg_len])
        if segment:
            segments.append(segment)
        i += seg_len

    num_segments = len(segments)
    dur_per_segment = audio_duration / max(num_segments, 1)

    # Font paths
    FONT_BOLD = "C:/Windows/Fonts/arialbd.ttf"
    FONT_REG  = "C:/Windows/Fonts/arial.ttf"

    font_path = FONT_BOLD if os.path.exists(FONT_BOLD) else FONT_REG

    clips = []
    for idx, seg in enumerate(segments):
        try:
            txt = seg.strip()
            txt_clip = TextClip(
                text=txt,
                color="white",
                stroke_color="black",
                stroke_width=2,
                method="caption",
                size=(900, 320),      # Fixed line-block prevents jitter
                text_align="center",
                vertical_align="center",
                font=font_path
            )

            txt_clip = (
                txt_clip
                .with_duration(dur_per_segment)
                .with_start(idx * dur_per_segment)
                .with_position(("center", 1380))  # near bottom, safe zone
                .with_fps(24)
            )

            clips.append(txt_clip)

        except Exception as e:
            print(f"[WARN] Subtitle segment failed: {seg[:25]}... / {e}")
            continue

    return clips

def ease_out_cubic(t):
    t = max(0, min(1, t))
    return 1 - (1 - t) ** 3

def build_subtitles_s3(script_text, audio_duration):
    # Clean text: remove parentheses
    words = script_text.replace("(", "").replace(")", "").split()
    if not words:
        return []

    # Subtitle grouping: 3 words per phrase (fits the 2-4 rule)
    phrases = []
    for i in range(0, len(words), 3):
        phrase = " ".join(words[i:i+3])
        if phrase:
            phrases.append(phrase)
            
    phrase_count = len(phrases)
    phrase_duration = audio_duration / phrase_count
    subtitle_clips = []
    
    for i, phrase in enumerate(phrases):
        start_time = i * phrase_duration
        
        # Base TextClip
        text_clip = TextClip(
            text=phrase,
            font="C:/Windows/Fonts/arialbd.ttf",
            font_size=70,
            color="white",
            stroke_color="black",
            stroke_width=3,
            method="caption",
            size=(900, 400)
        ).with_duration(phrase_duration).with_start(start_time).with_position(("center", 1350))

        # 1️⃣ Fade in logic: 0 -> 1 over 0.25s
        # 2️⃣ Scale pop-in logic: 0.90 -> 1.05
        def s3_animator(get_frame, t):
            # Get the original frame at time t
            frame = get_frame(t)
            
            # Calculate opacity (0.0 to 1.0)
            opacity = min(1.0, t / 0.25)
            
            # Apply opacity to the frame pixels (uint8)
            # We multiply by opacity and ensure it remains uint8
            return (frame * opacity).astype("uint8")

        def scale_func(t):
            return 0.90 + (0.15 * (t / phrase_duration))

        # Apply scale first using built-in resized (which handles functions well)
        # Then apply the custom transformation for opacity
        animated_clip = (text_clip
                         .resized(scale_func)
                         .transform(s3_animator))
        
        subtitle_clips.append(animated_clip)
        
    return subtitle_clips
# ---------------------------------------------------------
# MAIN RENDER FUNCTION
# ---------------------------------------------------------
def render_video(script_text: str, audio_path: str, media_paths: List[str], output_path: str):
    audio_clip = None
    final_clip = None
    media_clips = []
    subtitle_clips = []

    try:
        logger.info("🎬 Rendering video...")

        # LOAD AUDIO
        audio_clip = AudioFileClip(audio_path)
        audio_duration = audio_clip.duration

        # PICK BACKGROUND IMAGE
        bg_path = next(
            (p for p in media_paths if p.lower().endswith((".jpg", ".jpeg", ".png"))),
            media_paths[0]
        )

        # FOREGROUND MEDIA
        slot_duration = audio_duration / len(media_paths)

        for i, path in enumerate(media_paths):

            ext = path.lower().split(".")[-1]

            if ext in ["mp4", "mov", "webm", "mkv"]:
                clip = VideoFileClip(path)
                clip = clip.subclipped(0, min(slot_duration, clip.duration))
            else:
                clip = ImageClip(path, duration=slot_duration)

            clip = clip.resized(new_size=(1080, 1920))
            clip = clip.with_start(i * slot_duration)

            # ADD RANDOM MOTION
            clip = apply_random_motion(clip, slot_duration)

            media_clips.append(clip)

        # SUBTITLES
        font_path = get_font_path()
        subtitle_clips = build_subtitles_s3(script_text, audio_duration)

        # COMPOSITE
        final_clip = CompositeVideoClip(
            media_clips + subtitle_clips,
            size=(1080, 1920)
        ).with_audio(audio_clip)

        # EXPORT
        final_clip.write_videofile(
            output_path,
            fps=24,
            codec="libx264",
            audio_codec="aac",
            preset="veryfast",
            threads=8,
            bitrate="2500k"
        )

        logger.info("✅ Render complete")

    except Exception as e:
        logger.error(f"❌ Rendering failed: {e}")
        raise

    finally:
        # CLEANUP
        try:
            if audio_clip: audio_clip.close()
            for c in media_clips: c.close()
            for t in subtitle_clips: t.close()
            if final_clip: final_clip.close()
        except:
            pass

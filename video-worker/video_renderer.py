import os
import logging
import random
from typing import List
from moviepy import (
    AudioFileClip,
    ImageClip,
    VideoFileClip,
    CompositeVideoClip,
    TextClip
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------
# RANDOM KEN-BURNS STYLE ZOOM + DRIFT (MoviePy 2.1.2 SAFE)
# ---------------------------------------------------------
def apply_random_motion(clip, duration):

    zoom_amount = random.uniform(1.02, 1.06)
    zoom_in = random.choice([True, False])

    start_w, start_h = clip.size

    if zoom_in:
        end_w = int(start_w * zoom_amount)
        end_h = int(start_h * zoom_amount)
    else:
        end_w = int(start_w / zoom_amount)
        end_h = int(start_h / zoom_amount)

    # Animate size through time
    def size_func(t):
        progress = min(max(t / duration, 0), 1)
        w = int(start_w + (end_w - start_w) * progress)
        h = int(start_h + (end_h - start_h) * progress)
        return (w, h)

    # Animated position drift
    drift_x = random.randint(-30, 30)
    drift_y = random.randint(-30, 30)

    def pos_func(t):
        progress = min(max(t / duration, 0), 1)
        x = int(drift_x * progress)
        y = int(drift_y * progress)
        return (x, y)

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
        n = random.randint(3, 5)
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
        )

        clips.append(clip)

    return clips


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
        subtitle_clips = build_subtitles(script_text, audio_duration, font_path)

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

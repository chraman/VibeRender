"""
Video rendering logic for VibeRender Video Worker.
"""

import os
import logging
import random
from typing import List
from moviepy import AudioFileClip, ImageClip, VideoFileClip, CompositeVideoClip, TextClip

logger = logging.getLogger(__name__)


def render_video(script_text: str, audio_path: str, media_paths: List[str], output_path: str) -> None:
    """
    Render a video from existing assets using MoviePy.
    
    Creates a vertical video (1080x1920) with:
    - Images/videos displayed sequentially for equal durations
    - Script text overlaid in center with semi-transparent background
    - Audio synchronized with the video
    
    Args:
        script_text: The script text to display as overlay
        audio_path: Path to the audio file
        media_paths: List of paths to image or video files (supports .jpg, .png, .mp4, etc.)
        output_path: Path where the final video should be saved
        
    Raises:
        Exception: If video rendering fails
    """
    audio_clip = None
    media_clips = []
    text_clips = []
    final_clip = None
    video_clip = None
    
    try:
        logger.info('🎬 Starting video rendering...')
        logger.info(f'   Audio: {audio_path}')
        logger.info(f'   Media files: {len(media_paths)} file(s)')
        logger.info(f'   Output: {output_path}')
        
        # Load audio to get duration
        logger.debug('   Loading audio file...')
        audio_clip = AudioFileClip(audio_path)
        audio_duration = audio_clip.duration
        logger.info(f'   Audio duration: {audio_duration:.2f} seconds')
        
        if not media_paths:
            raise ValueError('No media paths provided for video rendering')
        
        # Optimize: Use single ImageClip as background for entire duration
        # Use the first image as background (most efficient)
        background_image_path = None
        for media_path in media_paths:
            media_ext = os.path.splitext(media_path)[1].lower()
            if media_ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                background_image_path = media_path
                break
        
        if not background_image_path:
            # If no image found, use first media file
            background_image_path = media_paths[0]
        
        if not os.path.exists(background_image_path):
            raise FileNotFoundError(f'Background media file not found: {background_image_path}')
        
        logger.debug(f'   Using single background image: {background_image_path}')
        # Create single image clip for full duration (optimized)
        # Use memoize=True parameter in ImageClip constructor for faster loading
        video_clip = ImageClip(background_image_path, duration=audio_duration)
        # Resize to 1080x1920 - do all resizing in one step
        video_clip = video_clip.resized(new_size=(1080, 1920))
        video_clip = video_clip.with_position('center')
        video_clip = video_clip.with_duration(audio_duration)
        # Set FPS explicitly to prevent frame timing issues (fixes subtitle lag)
        video_clip = video_clip.with_fps(24)
        # Memoize the background to cache it in RAM (prevents re-reading from disk)
        # MoviePy 2.x: use keyword argument memoize=True
        try:
            video_clip = video_clip.with_memoize(memoize=True)
            logger.debug('   Background image memoized for faster rendering')
        except Exception as e:
            # If memoize fails, continue without it (non-critical optimization)
            logger.debug(f'   Memoization not available: {e}, continuing without memoization')
        
        # Only process multiple media if we have videos or need sequencing
        if len(media_paths) > 1:
            # Multiple media files: create sequence (only if needed)
            duration_per_media = audio_duration / len(media_paths)
            logger.debug(f'   Duration per media: {duration_per_media:.2f} seconds')
            
            # Create media clips (images or videos) - overlay on background
            logger.debug('   Creating overlay media clips...')
            for i, media_path in enumerate(media_paths):
                if media_path == background_image_path:
                    continue  # Skip background image
                
                if not os.path.exists(media_path):
                    raise FileNotFoundError(f'Media file not found: {media_path}')
                
                # Determine if it's an image or video based on extension
                media_ext = os.path.splitext(media_path)[1].lower()
                is_video = media_ext in ['.mp4', '.mov', '.avi', '.mkv', '.webm']
                is_image = media_ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
                
                if not (is_image or is_video):
                    logger.warning(f'   Unknown media type for {media_path}, treating as image')
                    is_image = True
                
                logger.debug(f'   Loading overlay {i + 1}/{len(media_paths)}: {media_path} ({media_ext})')
                
                if is_video:
                    # Load video clip
                    media_clip = VideoFileClip(media_path)
                    # If video is longer than allocated duration, trim it
                    if media_clip.duration > duration_per_media:
                        media_clip = media_clip.subclipped(0, duration_per_media)
                    # If video is shorter, loop it or extend with last frame
                    elif media_clip.duration < duration_per_media:
                        # Extend by looping the video
                        loops_needed = int(duration_per_media / media_clip.duration) + 1
                        media_clip = CompositeVideoClip([media_clip] * loops_needed).subclipped(0, duration_per_media)
                else:
                    # Create image clip with specified duration
                    media_clip = ImageClip(media_path, duration=duration_per_media)
                
                # Resize to 1080x1920 - do all resizing in one step (avoid redundant resizing)
                media_clip = media_clip.resized(new_size=(1080, 1920))
                # Set position and start time after resizing (only once)
                media_clip = media_clip.with_position('center')
                media_clip = media_clip.with_start(i * duration_per_media)
                # Set FPS explicitly to prevent frame timing issues (fixes subtitle lag)
                media_clip = media_clip.with_fps(24)
                
                media_clips.append(media_clip)
        
        # Optimize: Check font existence once at the top (remove slow fallback loop)
        font_path = None
        arial_bold_path = 'C:/Windows/Fonts/arialbd.ttf'
        arial_regular_path = 'C:/Windows/Fonts/arial.ttf'
        
        if os.path.exists(arial_bold_path):
            font_path = arial_bold_path
            logger.debug('   Using Arial Bold font')
        elif os.path.exists(arial_regular_path):
            font_path = arial_regular_path
            logger.debug('   Using Arial Regular font')
        else:
            logger.debug('   Using default font (system fonts not found)')
        
        # Create phrase-by-phrase subtitles (group words into phrases of 3-5 words)
        logger.debug('   Creating phrase-by-phrase subtitles (grouped for performance)...')
        # Split script into words
        words = script_text.split()
        num_words = len(words)
        
        # Group words into phrases of 3-5 words (reduces clip count by 75%)
        phrase_groups = []
        i = 0
        while i < num_words:
            # Random phrase length between 3-5 words for natural feel
            phrase_length = random.randint(3, 5)
            phrase = ' '.join(words[i:i + phrase_length])
            if phrase:  # Only add non-empty phrases
                phrase_groups.append(phrase)
            i += phrase_length
        
        num_phrases = len(phrase_groups)
        phrase_duration = audio_duration / num_phrases if num_phrases > 0 else audio_duration
        
        logger.debug(f'   Total words: {num_words}, Grouped into {num_phrases} phrases, Duration per phrase: {phrase_duration:.3f} seconds')
        
        # Create TextClip for each phrase (much fewer clips = faster rendering)
        text_clips = []
        for index, phrase in enumerate(phrase_groups):
            try:
                # Clean up phrase: remove leading/trailing spaces to prevent alignment jitters
                # Add vertical padding to prevent stroke clipping at edges
                phrase = f'\n{phrase.strip()}\n'
                if not phrase.strip():  # Skip empty phrases
                    continue
                
                if font_path:
                    phrase_clip = TextClip(
                        text=phrase,
                        font=font_path,
                        font_size=70,
                        color='yellow',
                        method='caption',  # Caption method with size for proper wrapping
                        size=(900, 400),  # Fixed width and height container (prevents cropping)
                        text_align='center',  # Center alignment
                        vertical_align='center',  # Vertical center alignment (prevents text drifting)
                        stroke_color='black',
                        stroke_width=2
                    )
                else:
                    # Fallback without explicit font
                    phrase_clip = TextClip(
                        text=phrase,
                        font_size=70,
                        color='yellow',
                        method='caption',  # Caption method with size for proper wrapping
                        size=(900, 400),  # Fixed width and height container (prevents cropping)
                        text_align='center',  # Center alignment
                        vertical_align='center',  # Vertical center alignment (prevents text drifting)
                        stroke_color='black',
                        stroke_width=2
                    )
                
                # Set duration and start time for this phrase (no memoize to avoid frame-sync issues)
                phrase_clip = phrase_clip.with_duration(phrase_duration)
                phrase_clip = phrase_clip.with_start(index * phrase_duration)
                # Set FPS explicitly to prevent frame timing issues (fixes subtitle lag)
                phrase_clip = phrase_clip.with_fps(24)
                # Position at bottom-center (y=1300 from top - more breathing room from bottom)
                phrase_clip = phrase_clip.with_position(('center', 1300))
                text_clips.append(phrase_clip)
            except Exception as e:
                logger.warning(f'   TextClip creation failed for phrase "{phrase[:30]}...": {e}')
                # Skip this phrase if we can't create the clip
                continue
        
        logger.debug(f'   Created {len(text_clips)} phrase subtitle clips (reduced from {num_words} words)')
        
        # Composite everything together efficiently
        logger.debug('   Compositing final video...')
        # Group all clips: background video + overlay media + all text clips
        all_clips = [video_clip] + media_clips + text_clips
        logger.debug(f'   Compositing {len(all_clips)} clips (1 background + {len(media_clips)} media + {len(text_clips)} text)')
        # use_bgclip=True tells MoviePy the first clip is a full-screen background, skipping transparency checks
        final_clip = CompositeVideoClip(all_clips, size=(1080, 1920), use_bgclip=True)
        
        # Add audio (MoviePy 2.0: returns new clip)
        final_clip = final_clip.with_audio(audio_clip)
        final_clip = final_clip.with_duration(audio_duration)
        
        # Export video with optimized settings for speed
        logger.info('   Exporting video (this may take a while)...')
        import time
        start_time = time.time()
        
        # Use ultrafast preset and 8 threads for maximum speed
        num_threads = 8
        logger.debug(f'   Using {num_threads} threads for encoding')
        
        final_clip.write_videofile(
            output_path,
            fps=24,
            codec='libx264',
            audio_codec='aac',
            preset='ultrafast',  # Fastest encoding preset
            threads=num_threads,  # Use 8 threads for maximum speed
            bitrate='2000k',  # Lower bitrate speeds up encoding without quality loss for social media
            pixel_format='yuv420p',  # Standard web format, much faster to encode than high-bit-depth
            ffmpeg_params=['-tune', 'zerolatency', '-crf', '28'],  # Start streaming immediately, no buffer delays
            logger=None  # Disable progress calculation (saves CPU cycles)
        )
        
        elapsed_time = time.time() - start_time
        file_size = os.path.getsize(output_path)
        
        logger.info(f'✅ Video rendered successfully in {elapsed_time:.2f} seconds')
        logger.info(f'   Output: {output_path} ({file_size} bytes)')
        
    except Exception as e:
        logger.error(f'❌ Video rendering error: {str(e)}')
        raise Exception(f'Failed to render video: {str(e)}')
    
    finally:
        # Clean up MoviePy objects to save RAM (critical for memory management)
        logger.debug('   Cleaning up MoviePy objects...')
        
        # Close audio first (important for memory)
        if audio_clip:
            try:
                audio_clip.close()
                logger.debug('   Audio clip closed')
            except Exception as e:
                logger.debug(f'   Error closing audio clip: {e}')
        
        # Close all media clips
        for clip in media_clips:
            try:
                clip.close()
            except Exception as e:
                logger.debug(f'   Error closing media clip: {e}')
        
        # Close all text clips
        for clip in text_clips:
            try:
                clip.close()
            except Exception as e:
                logger.debug(f'   Error closing text clip: {e}')
        
        # Close video clip
        if video_clip:
            try:
                video_clip.close()
                logger.debug('   Video clip closed')
            except Exception as e:
                logger.debug(f'   Error closing video clip: {e}')
        
        # Close final clip last (critical for memory)
        if final_clip:
            try:
                final_clip.close()
                logger.debug('   Final clip closed')
            except Exception as e:
                logger.debug(f'   Error closing final clip: {e}')
        
        logger.debug('   Cleanup complete')


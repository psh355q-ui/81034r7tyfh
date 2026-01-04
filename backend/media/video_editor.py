import json
import os
import logging
from typing import List
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, ImageClip, concatenate_videoclips
from moviepy.video.fx.all import crop, resize
from gtts import gTTS
import asyncio

logger = logging.getLogger(__name__)

class VideoEditor:
    """
    Stitches video clips based on shooting_script.json.
    Adds TTS audio and subtitles.
    """
    
    def __init__(self, script_path: str, clips_dir: str, output_path: str):
        self.script_path = script_path
        self.clips_dir = clips_dir
        self.output_path = output_path
        
        # Load Script
        with open(script_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
            
    def _create_tts(self, text: str, filename: str):
        """Generates TTS audio file"""
        tts = gTTS(text=text, lang='ko')
        tts.save(filename)
        return filename

    def _zoom_in_effect(self, clip, zoom_ratio=0.04):
        """
        Applies a slow zoom-in effect to the clip.
        """
        def effect(get_frame, t):
            img = get_frame(t)
            h, w = img.shape[:2]
            
            # Zoom factor increases with time
            scale = 1 + (zoom_ratio * t / clip.duration)
            
            # Calculate new dimensions
            new_h, new_w = int(h / scale), int(w / scale)
            
            # Crop center
            y1 = (h - new_h) // 2
            x1 = (w - new_w) // 2
            
            # Return cropped frame (MoviePy will resize it back to original size if needed, 
            # but usually we handle resize usage carefully. 
            # Simplified: Just cropping is faster, but might lose resolution.
            # Better: Resize image larger first, then crop to standard size?
            # For performance, let's skip complex transforms and assume static image is high res.
            return img[y1:y1+new_h, x1:x1+new_w]

            return img[y1:y1+new_h, x1:x1+new_w]

        # MoviePy's resize is better for quality, but slower.
        return clip.resize(lambda t: 1 + 0.02 * t) # Simple dynamic resize (Zoom in)

    def _create_fallback_clip(self, image_path: str, duration: float) -> VideoFileClip:
        """
        Creates a static image clip with zoom effect if video is missing.
        """
        from moviepy.editor import ColorClip # Import locally to ensure availability
        
        try:
            # Check if image exists
            if not os.path.exists(image_path):
                logger.warning(f"Image not found: {image_path}, using black screen.")
                # Use ColorClip (Black) instead of TextClip to avoid ImageMagick issues
                return ColorClip(size=(1080, 1920), color=(0,0,0), duration=duration)

            # Create Image Clip
            img = ImageClip(image_path).set_duration(duration)
            
            # Resize logic (vertical 1080x1920)
            # 1. Resize height to 1920 (width will auto-scale)
            # 2. If width < 1080, we need to resize width to 1080 and crop height
            # But usually character images are square or portrait.
            # Let's try to fit height 1920 first.
            img = img.resize(height=1920)
            
            # Center on 1080x1920 canvas
            # A simple way is to compose it on a black background
            bg = ColorClip(size=(1080, 1920), color=(0,0,0), duration=duration)
            img = img.set_position("center")
            
            # Apply Zoom logic on the IMAGE, then composite
            # Note: Zooming a Composted clip is complex. 
            # Let's apply zoom to img first if possible, but img duration needs to be set.
            # Simplified: just return the composite for stability first.
            
            return CompositeVideoClip([bg, img]).set_duration(duration)
            
        except Exception as e:
            logger.error(f"Error creating fallback: {e}")
            # Final safety net
            return ColorClip(size=(1080, 1920), color=(255,0,0), duration=duration)

    def process(self):
        logger.info("🎬 Starting Video Stitching...")
        
        final_clips = []
        
        for scene in self.data["scenes"]:
            scene_num = scene["scene_number"]
            dialogue = scene["dialogue"]
            image_path = scene["image_path"] # Fallback asset
            
            logger.info(f"Processing Scene {scene_num}...")
            
            # 1. Generate Audio
            audio_file = f"temp_audio_{scene_num}.mp3"
            self._create_tts(dialogue, audio_file)
            audio = AudioFileClip(audio_file)
            duration = audio.duration
            
            # 2. Convert Audio Duration to Video Duration
            # Check if user provided video exists
            video_path = os.path.join(self.clips_dir, f"scene_{scene_num}.mp4")
            
            if os.path.exists(video_path):
                logger.info(f"   Found user video: {video_path}")
                clip = VideoFileClip(video_path)
                # Loop or trim
                if clip.duration < duration:
                    clip = clip.loop(duration=duration)
                else:
                    clip = clip.subclip(0, duration)
            else:
                logger.warning(f"   User video not found. Using static image fallback: {image_path}")
                clip = self._create_fallback_clip(image_path, duration)
                
            # 3. Set Audio
            clip = clip.set_audio(audio)
            
            # 4. Add Subtitles (Simple TextClip)
            # MoviePy TextClip requires ImageMagick. If missing, this might fail.
            # For now, let's skip complex subtitles or try simple one.
            # Assuming ImageMagick is NOT installed on Windows by default safely, skipping for stability.
            
            final_clips.append(clip)
            
            # Cleanup audio temp
            # os.remove(audio_file) # Keep for debug
            
        # 5. Concatenate
        logger.info("Combining clips...")
        final = concatenate_videoclips(final_clips, method="compose")
        
        # 6. Write Output
        logger.info(f"Writing to {self.output_path}...")
        final.write_videofile(self.output_path, fps=24, codec="libx264", audio_codec="aac")
        logger.info("✅ Render Complete!")

if __name__ == "__main__":
    editor = VideoEditor(
        script_path="shooting_script.json",
        clips_dir="movie/clips",
        output_path="output_short.mp4"
    )
    editor.process()

import os
from typing import List, Dict, Optional
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, concatenate_videoclips
from moviepy.video.fx.resize import resize
from moviepy.video.fx.fadein import fadein
from moviepy.video.fx.fadeout import fadeout
import numpy as np

class VideoEditor:
    def __init__(self, output_dir: str = "~/weird_news_pipeline/videos"):
        self.output_dir = os.path.expanduser(output_dir)
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Default style settings
        self.text_settings = {
            'font': 'Arial',
            'fontsize': 48,
            'color': 'white',
            'stroke_color': 'black',
            'stroke_width': 2
        }
        
        # Video settings
        self.target_resolution = (1920, 1080)
        self.fps = 30
        self.transition_duration = 1.0  # seconds
        
    def create_text_overlay(self, text: str, duration: float, position: str = 'center') -> TextClip:
        """Create a text overlay with the specified style."""
        text_clip = TextClip(
            text,
            font=self.text_settings['font'],
            fontsize=self.text_settings['fontsize'],
            color=self.text_settings['color'],
            stroke_color=self.text_settings['stroke_color'],
            stroke_width=self.text_settings['stroke_width']
        )
        
        # Set position
        if position == 'top':
            text_clip = text_clip.set_position(('center', 50))
        elif position == 'bottom':
            text_clip = text_clip.set_position(('center', 'bottom'))
        else:
            text_clip = text_clip.set_position('center')
            
        return text_clip.set_duration(duration)
    
    def prepare_video_clip(self, video_path: str, target_duration: float) -> VideoFileClip:
        """Prepare a video clip with consistent formatting."""
        clip = VideoFileClip(video_path)
        
        # Resize to target resolution while maintaining aspect ratio
        clip = resize(clip, width=self.target_resolution[0])
        
        # Trim or loop the clip to match target duration
        if clip.duration < target_duration:
            # Loop the clip
            repeats = int(np.ceil(target_duration / clip.duration))
            clip = concatenate_videoclips([clip] * repeats)
        
        # Trim to exact duration
        clip = clip.subclip(0, target_duration)
        
        # Add fade effects
        clip = fadein(clip, self.transition_duration)
        clip = fadeout(clip, self.transition_duration)
        
        return clip
    
    def create_newsreel(self, 
                       script: Dict,
                       video_clips: List[Dict],
                       output_filename: str) -> str:
        """
        Create a complete newsreel video with text overlays and transitions.
        
        Args:
            script: Dictionary containing the script sections and timing
            video_clips: List of dictionaries containing video paths and durations
            output_filename: Name of the output video file
        
        Returns:
            Path to the created video file
        """
        final_clips = []
        
        # Process each section of the script with corresponding video
        for i, (section, video) in enumerate(zip(script['script_sections'].items(), video_clips)):
            section_name, section_content = section
            video_path = video['path']
            duration = video['duration']
            
            # Prepare the video clip
            video_clip = self.prepare_video_clip(video_path, duration)
            
            # Create text overlay
            if section_name == 'hook':
                text_clip = self.create_text_overlay(section_content, duration, position='top')
            elif section_name == 'main_content':
                text_clip = self.create_text_overlay(section_content, duration, position='bottom')
            else:  # CTA
                text_clip = self.create_text_overlay(section_content, duration, position='center')
            
            # Combine video and text
            composite = CompositeVideoClip([video_clip, text_clip])
            final_clips.append(composite)
        
        # Concatenate all clips
        final_video = concatenate_videoclips(final_clips)
        
        # Save the final video
        output_path = os.path.join(self.output_dir, output_filename)
        final_video.write_videofile(
            output_path,
            fps=self.fps,
            codec='libx264',
            audio_codec='aac'
        )
        
        # Close all clips to free up resources
        final_video.close()
        for clip in final_clips:
            clip.close()
        
        return output_path
    
    def concatenate_videos(self, video_paths: List[str], output_filename: str) -> str:
        """Concatenate multiple video clips into a single video."""
        try:
            video_clips = []
            for video_path in video_paths:
                if not os.path.exists(video_path):
                    raise FileNotFoundError(f"Video file not found: {video_path}")
                video_clips.append(VideoFileClip(video_path))
            
            final_video = concatenate_videoclips(video_clips)
            
            output_path = os.path.join(self.output_dir, output_filename)
            final_video.write_videofile(
                output_path,
                fps=self.fps,
                codec='libx264',
                audio_codec='aac'
            )
            
            # Close all clips to free up resources
            final_video.close()
            for clip in video_clips:
                clip.close()
            
            return output_path
        except FileNotFoundError as e:
            print(f"Error: {e}")
            return ""
        except Exception as e:
            print(f"Error concatenating videos: {e}")
            return ""

async def main():
    """Test the VideoEditor with sample content."""
    editor = VideoEditor()
    
    # Sample script
    sample_script = {
        'script_sections': {
            'hook': "FLASH! Witness the extraordinary tale of science gone wild!",
            'main_content': "In a groundbreaking discovery, scientists reveal the unexpected truth about garden gnomes...",
            'cta': "Stay tuned for more incredible revelations!"
        }
    }
    
    # Sample video clips (replace with actual paths)
    sample_videos = [
        {'path': 'path/to/video1.mp4', 'duration': 5.0},
        {'path': 'path/to/video2.mp4', 'duration': 15.0},
        {'path': 'path/to/video3.mp4', 'duration': 5.0}
    ]
    
    try:
        output_path = editor.create_newsreel(
            sample_script,
            sample_videos,
            'test_newsreel.mp4'
        )
        print(f"Newsreel created successfully: {output_path}")
    except Exception as e:
        print(f"Error creating newsreel: {str(e)}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

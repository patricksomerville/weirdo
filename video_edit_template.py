import os
from typing import List, Dict, Optional
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, concatenate_videoclips
from moviepy.video.fx.resize import resize
from moviepy.video.fx.fadein import fadein
from moviepy.video.fx.fadeout import fadeout
import numpy as np
import json

class VideoEditorTemplate:
    def __init__(self, output_dir: str = ".", music: str = "music1.mp3", style: str = "default", tone: str = "neutral"):
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
        
        # Music, style, and tone settings
        self.music = music
        self.style = style
        self.tone = tone
        
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
    
    def apply_style(self, clip: VideoFileClip) -> VideoFileClip:
        """Apply style and tone adjustments to the video clip."""
        if self.style == "vibrant":
            clip = clip.fx(lambda clip: clip.colorx(1.2))  # Increase color intensity
        elif self.style == "dark":
            clip = clip.fx(lambda clip: clip.colorx(0.8))  # Decrease color intensity
        
        # Add more style options here
        
        return clip
    
    def create_newsreel(self, 
                       script: Dict,
                       video_clips: List[Dict],
                       output_filename: str,
                       music: Optional[str] = None) -> str:
        """
        Create a complete newsreel video with text overlays and transitions.
        
        Args:
            script: Dictionary containing the script sections and timing
            video_clips: List of dictionaries containing video paths and durations
            output_filename: Name of the output video file
            music: Optional path to background music
        
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
            
            # Apply style
            video_clip = self.apply_style(video_clip)
            
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
        
        # Add background music
        if music:
            from moviepy.editor import AudioFileClip, CompositeAudioClip
            audio_clip = AudioFileClip(music)
            final_audio = CompositeAudioClip([audio_clip.audio_loop(duration=final_video.duration)])
            final_video = final_video.set_audio(final_audio)
        
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

async def main():
    """Test the VideoEditorTemplate with sample content."""
    print("Starting main function")  # Add debug print
    # Sample video clips (replace with actual paths and durations)
    sample_videos = [
        {'path': 'video1.mp4', 'duration': 5.0},
        {'path': 'video1.mp4', 'duration': 15.0},
        {'path': 'video1.mp4', 'duration': 5.0}
    ]
    
    # Load the 1940s script
    script_path_1940s = "/Users/patricksomerville/weird_news_pipeline/scripts/crab_divorce_script_1940s.json"
    print(f"Loading script from: {script_path_1940s}")  # Add debug print
    with open(script_path_1940s, 'r') as f:
        script_1940s = json.load(f)
    
    # Create 1940s newsreel video
    editor1 = VideoEditorTemplate(output_dir=".")
    try:
        output_path_1940s = editor1.create_newsreel(
            script_1940s,
            sample_videos,
            'crab_divorce_newsreel_1940s.mp4'
        )
        print(f"Newsreel created successfully: {output_path_1940s}")  # Add debug print
    except Exception as e:
        print(f"Error creating newsreel: {str(e)}")
    
    # Load the comedic script
    script_path_comedic = "/Users/patricksomerville/weird_news_pipeline/scripts/crab_divorce_script_comedic.json"
    print(f"Loading script from: {script_path_comedic}")  # Add debug print
    with open(script_path_comedic, 'r') as f:
        script_comedic = json.load(f)
    
    # Create comedic video
    editor2 = VideoEditorTemplate(style="vibrant", output_dir=".")
    try:
        output_path_comedic = editor2.create_newsreel(
            script_comedic,
            sample_videos,
            'crab_divorce_newsreel_comedic.mp4'
        )
        print(f"Newsreel created successfully: {output_path_comedic}")  # Add debug print
    except Exception as e:
        print(f"Error creating newsreel: {str(e)}")
    
    # Concatenate the videos
    if output_path_1940s and output_path_comedic:
        from video_editor import VideoEditor
        editor = VideoEditor()
        video_paths = [output_path_1940s, output_path_comedic]
        print(f"Concatenating videos: {video_paths}")  # Add debug print
        output_path_combined = editor.concatenate_videos(video_paths, 'crab_divorce_combined.mp4')
        print(f"Combined video created successfully: {output_path_combined}")  # Add debug print
    else:
        print("Error: One or both video paths are missing.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
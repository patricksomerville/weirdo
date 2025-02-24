import os
import asyncio
import time
from typing import Dict, List
from script_generator import ScriptGenerator
from media_manager import MediaManager
from voice_manager import VoiceManager
from video_editor import VideoEditor
from news_scraper import NewsScraper
from stock_footage_manager import StockFootageManager

class VideoPipeline:
    def __init__(self):
        self.script_generator = ScriptGenerator()
        self.stock_footage = StockFootageManager()
        self.video_editor = VideoEditor()
        self.news_scraper = NewsScraper()
        
        # Create necessary directories
        self.base_dir = os.path.expanduser("~/weird_news_pipeline")
        self.footage_dir = os.path.join(self.base_dir, "stock_footage")
        self.output_dir = os.path.join(self.base_dir, "videos")
        
        for directory in [self.base_dir, self.footage_dir, self.output_dir]:
            os.makedirs(directory, exist_ok=True)

    async def fetch_todays_story(self) -> Dict:
        """Fetch today's weirdest news story."""
        print("Fetching today's weird news stories...")
        await self.news_scraper.fetch_all_articles()
        return self.news_scraper.get_weirdest_article()

    async def generate_daily_video(self) -> str:
        """Generate a video for today's weirdest story."""
        try:
            # Get today's weirdest story
            article = await self.fetch_todays_story()
            print(f"\nToday's weirdest story:")
            print(f"Title: {article['title']}")
            print(f"Source: {article['source']}")
            print(f"Weirdness Score: {article['weirdness_score']:.2f}")
            
            # Create the video
            output_path = await self.create_video(article)
            print(f"\nVideo created successfully: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"Error generating daily video: {str(e)}")
            raise

    async def find_relevant_footage(self, script: Dict) -> List[Dict]:
        """Find relevant stock footage based on script content."""
        video_clips = []
        
        # Search for footage for each script section
        for section_name, content in script['script_sections'].items():
            # Extract keywords from the content
            keywords = self._extract_keywords(content)
            
            # Search for videos using the keywords
            result = await self.stock_footage.search_videos(" ".join(keywords))
            
            if result['videos']:
                video = result['videos'][0]  # Get the first matching video
                
                # Download the video
                filename = f"{section_name}_{video['id']}.mp4"
                filepath = os.path.join(self.footage_dir, filename)
                
                if video['download_url']:
                    await self.stock_footage.download_video(video['download_url'], filepath)
                    
                    # Add to our clips list with duration
                    video_clips.append({
                        'path': filepath,
                        'duration': video['duration']
                    })
        
        return video_clips

    def _extract_keywords(self, content: str) -> List[str]:
        """Extract relevant keywords from script content."""
        # Remove common words and punctuation
        common_words = {'and', 'the', 'in', 'on', 'at', 'to', 'for', 'of', 'with'}
        words = content.lower().replace('!', '').replace('.', '').replace(',', '').split()
        keywords = [word for word in words if word not in common_words]
        
        # Add specific keywords based on content type
        if 'FLASH!' in content or 'BREAKING' in content:
            keywords.extend(['newsreel', 'vintage', 'news'])
        
        return keywords[:5]  # Limit to top 5 keywords

    async def create_video(self, article: Dict) -> str:
        """Create a complete video from an article."""
        try:
            # Generate script
            script = await self.script_generator.generate_script(article)
            
            # Find and download relevant footage
            video_clips = await self.find_relevant_footage(script)
            
            if not video_clips:
                raise Exception("No suitable video clips found")
            
            # Generate unique filename based on article
            filename = f"newsreel_{article.get('id', 'unknown')}_{int(asyncio.get_event_loop().time())}.mp4"
            
            # Create the final video
            output_path = self.video_editor.create_newsreel(
                script,
                video_clips,
                filename
            )
            
            return output_path
            
        except Exception as e:
            print(f"Error creating video: {str(e)}")
            raise

async def main():
    """Test the video pipeline with today's weirdest story."""
    pipeline = VideoPipeline()
    await pipeline.generate_daily_video()

if __name__ == "__main__":
    asyncio.run(main())

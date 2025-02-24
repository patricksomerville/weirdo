import os
import asyncio
import aiohttp
from typing import Dict, List, Optional
from image_manager import ImageManager
from stock_footage_manager import StockFootageManager

class MediaManager:
    def __init__(self):
        self.image_manager = ImageManager()  # For Stability AI image generation
        self.stock_manager = StockFootageManager()  # For Pexels stock footage
        
        # Base directories
        self.base_dir = os.path.expanduser("~/weird_news_pipeline/media")
        self.generated_dir = os.path.join(self.base_dir, "generated")
        self.stock_dir = os.path.join(self.base_dir, "stock")
        
        # Create directories
        for directory in [self.base_dir, self.generated_dir, self.stock_dir]:
            os.makedirs(directory, exist_ok=True)

        # Pexels API for stock photos
        self.pexels_headers = {
            "Authorization": os.getenv("PEXELS_API_KEY")
        }

    async def generate_video_content(self, prompt: str, duration: float) -> Dict:
        """Generate video content using Runway ML."""
        try:
            # Configure Runway for video generation
            runway_config = {
                "prompt": f"vintage newsreel style: {prompt}",
                "negative_prompt": "modern, digital, low quality",
                "duration": duration,
                "num_frames": int(duration * 24)  # 24 fps
            }
            
            # Generate video using Runway
            video_data = await self._generate_runway_video(runway_config)
            
            # Save the generated video
            filename = f"generated_{int(asyncio.get_event_loop().time())}.mp4"
            filepath = os.path.join(self.generated_dir, filename)
            
            with open(filepath, "wb") as f:
                f.write(video_data)
            
            return {
                "type": "generated_video",
                "path": filepath,
                "duration": duration,
                "metadata": {
                    "source": "runway",
                    "prompt": runway_config["prompt"]
                }
            }
        except Exception as e:
            print(f"Error generating video: {str(e)}")
            return None

    async def get_stock_photo(self, query: str) -> Optional[Dict]:
        """Fetch relevant stock photo from Pexels."""
        try:
            async with aiohttp.ClientSession() as session:
                url = "https://api.pexels.com/v1/search"
                params = {
                    "query": f"vintage {query}",
                    "per_page": 1,
                    "size": "large"
                }
                
                async with session.get(url, headers=self.pexels_headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data["photos"]:
                            photo = data["photos"][0]
                            
                            # Download the photo
                            filename = f"stock_{int(asyncio.get_event_loop().time())}.jpg"
                            filepath = os.path.join(self.stock_dir, filename)
                            
                            async with session.get(photo["src"]["original"]) as img_response:
                                if img_response.status == 200:
                                    with open(filepath, "wb") as f:
                                        f.write(await img_response.read())
                                    
                                    return {
                                        "type": "stock_photo",
                                        "path": filepath,
                                        "metadata": {
                                            "source": "pexels",
                                            "id": photo["id"],
                                            "photographer": photo["photographer"]
                                        }
                                    }
            return None
        except Exception as e:
            print(f"Error fetching stock photo: {str(e)}")
            return None

    async def get_media_for_section(self, section: str, prompt: str, duration: float) -> List[Dict]:
        """Get a mix of media content for a section."""
        media = []
        
        # Try to get AI-generated video first
        generated_video = await self.generate_video_content(prompt, duration)
        if generated_video:
            media.append(generated_video)
        
        # Get stock footage
        stock_result = await self.stock_manager.search_videos(prompt)
        if stock_result["videos"]:
            video = stock_result["videos"][0]
            if video["download_url"]:
                filename = f"stock_{int(asyncio.get_event_loop().time())}.mp4"
                filepath = os.path.join(self.stock_dir, filename)
                
                await self.stock_manager.download_video(video["download_url"], filepath)
                
                media.append({
                    "type": "stock_video",
                    "path": filepath,
                    "duration": video["duration"],
                    "metadata": {
                        "source": "pexels",
                        "id": video["id"]
                    }
                })
        
        # Get stock photo as backup/additional content
        stock_photo = await self.get_stock_photo(prompt)
        if stock_photo:
            media.append(stock_photo)
        
        # Generate AI image as backup if we don't have enough content
        if len(media) < 2:
            try:
                result = await self.image_manager.generate_image(
                    prompt=f"1940s newsreel style, black and white: {prompt}",
                    negative_prompt="modern, digital, low quality, color"
                )
                
                if result["images"]:
                    filename = f"generated_{int(asyncio.get_event_loop().time())}.png"
                    filepath = os.path.join(self.generated_dir, filename)
                    
                    await self.image_manager.save_image(result["images"][0], filepath)
                    
                    media.append({
                        "type": "generated_image",
                        "path": filepath,
                        "metadata": {
                            "source": "stability",
                            **result["metadata"]
                        }
                    })
            except Exception as e:
                print(f"Error generating image: {str(e)}")
        
        return media

async def main():
    """Test the MediaManager."""
    manager = MediaManager()
    
    test_sections = [
        ("hook", "Breaking news: Scientists discover talking plants", 5.0),
        ("main_content", "Laboratory experiments reveal plants communicating", 15.0),
        ("cta", "Stay tuned for more incredible scientific discoveries", 5.0)
    ]
    
    for section, prompt, duration in test_sections:
        print(f"\nGetting media for section: {section}")
        media = await manager.get_media_for_section(section, prompt, duration)
        print(f"Found {len(media)} media items:")
        for item in media:
            print(f"- Type: {item['type']}")
            print(f"  Path: {item['path']}")
            print(f"  Metadata: {item['metadata']}")

if __name__ == "__main__":
    asyncio.run(main())

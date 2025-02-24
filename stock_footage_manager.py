import os
import aiohttp
import asyncio
from typing import Dict
from config import STOCK_FOOTAGE_CONFIGS

class StockFootageManager:
    def __init__(self):
        """Initialize Pexels stock footage manager"""
        self.config = STOCK_FOOTAGE_CONFIGS['pexels']
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": self.config['api_key']
        }

    async def search_videos(self, query: str) -> Dict:
        """Search videos using Pexels API."""
        url = f"{self.config['api_host']}/search"
        params = {
            "query": query,
            "per_page": self.config['per_page'],
            "min_width": self.config['min_width'],
            "min_duration": self.config['min_duration'],
            "max_duration": self.config['max_duration']
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers, params=params) as response:
                if response.status != 200:
                    raise Exception(f"Non-200 response: {await response.text()}")
                
                data = await response.json()
                return {
                    "videos": [{
                        "id": video["id"],
                        "url": video["url"],
                        "download_url": video.get("video_files", [{}])[0].get("link", ""),
                        "duration": video.get("duration", 0),
                        "width": video.get("width", 0),
                        "height": video.get("height", 0),
                        "preview": video.get("image", "")
                    } for video in data.get("videos", [])]
                }

    async def download_video(self, url: str, filepath: str) -> str:
        """Download a video file from the given URL."""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    raise Exception(f"Failed to download video: {response.status}")
                
                with open(filepath, 'wb') as f:
                    while True:
                        chunk = await response.content.read(8192)
                        if not chunk:
                            break
                        f.write(chunk)
        
        return filepath

async def main():
    """Test the StockFootageManager with a sample search."""
    test_query = "vintage newsreel footage"
    
    manager = StockFootageManager()
    try:
        result = await manager.search_videos(test_query)
        
        print(f"Found {len(result['videos'])} videos")
        if result['videos']:
            # Download the first video as a test
            video = result['videos'][0]
            if video['download_url']:
                filepath = os.path.expanduser("~/weird_news_pipeline/stock_footage/test_video.mp4")
                await manager.download_video(video['download_url'], filepath)
                print(f"Video downloaded to: {filepath}")
            print("First video metadata:", video)
    except Exception as e:
        print(f"Error searching videos: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())

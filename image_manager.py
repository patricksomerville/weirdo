import os
import aiohttp
import base64
from typing import Dict, List, Optional
from config import IMAGE_CONFIGS

class ImageManager:
    def __init__(self, provider='stability'):
        """Initialize with either 'stability' or 'runway' as provider"""
        if provider not in IMAGE_CONFIGS:
            raise ValueError(f"Unsupported provider: {provider}")
        
        self.provider = provider
        self.config = IMAGE_CONFIGS[provider]
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config['api_key']}"
        }

    async def generate_image(self, prompt: str, negative_prompt: str = "") -> Dict:
        """Generate an image using the configured provider."""
        if self.provider == 'stability':
            return await self._generate_stability_image(prompt, negative_prompt)
        else:
            return await self._generate_runway_image(prompt, negative_prompt)

    async def _generate_stability_image(self, prompt: str, negative_prompt: str = "") -> Dict:
        """Generate an image using Stability AI."""
        url = f"{self.config['api_host']}/v1/generation/{self.config['engine_id']}/text-to-image"
        
        payload = {
            "text_prompts": [
                {
                    "text": prompt,
                    "weight": 1
                }
            ],
            "cfg_scale": self.config['cfg_scale'],
            "height": self.config['height'],
            "width": self.config['width'],
            "steps": self.config['steps'],
            "samples": self.config['samples']
        }

        if negative_prompt:
            payload["text_prompts"].append({
                "text": negative_prompt,
                "weight": -1
            })

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=self.headers, json=payload) as response:
                if response.status != 200:
                    raise Exception(f"Non-200 response: {await response.text()}")
                
                data = await response.json()
                return {
                    "images": [base64.b64decode(image["base64"]) for image in data["artifacts"]],
                    "metadata": {
                        "provider": "stability",
                        "prompt": prompt,
                        "negative_prompt": negative_prompt,
                        "engine": self.config['engine_id'],
                        "cfg_scale": self.config['cfg_scale'],
                        "steps": self.config['steps']
                    }
                }

    async def _generate_runway_image(self, prompt: str, negative_prompt: str = "") -> Dict:
        """Generate an image using Runway ML."""
        url = f"{self.config['api_host']}/inference"
        
        payload = {
            "prompt": prompt,
            "negative_prompt": negative_prompt if negative_prompt else None,
            "model": self.config['model'],
            "height": self.config['height'],
            "width": self.config['width'],
            "num_outputs": self.config['num_outputs'],
            "steps": self.config['steps']
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=self.headers, json=payload) as response:
                if response.status != 200:
                    raise Exception(f"Non-200 response: {await response.text()}")
                
                data = await response.json()
                # Runway returns images in a different format, adjust accordingly
                images = [base64.b64decode(img) for img in data.get('images', [])]
                return {
                    "images": images,
                    "metadata": {
                        "provider": "runway",
                        "prompt": prompt,
                        "negative_prompt": negative_prompt,
                        "model": self.config['model'],
                        "steps": self.config['steps']
                    }
                }

    async def save_image(self, image_data: bytes, filepath: str) -> str:
        """Save a generated image to disk."""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "wb") as f:
            f.write(image_data)
        return filepath

async def main():
    """Test the ImageManager with both providers."""
    test_prompt = "A vintage 1940s newsreel scene showing a bizarre UFO sighting"
    test_negative = "modern, digital, low quality"
    
    for provider in ['stability', 'runway']:
        print(f"\nTesting {provider.title()} provider:")
        manager = ImageManager(provider=provider)
        try:
            result = await manager.generate_image(
                prompt=test_prompt,
                negative_prompt=test_negative
            )
            
            # Save the first generated image
            if result["images"]:
                filepath = os.path.expanduser(f"~/weird_news_pipeline/images/test_image_{provider}.png")
                await manager.save_image(result["images"][0], filepath)
                print(f"Image saved to: {filepath}")
                print("Metadata:", result["metadata"])
        except Exception as e:
            print(f"Error generating image with {provider}: {str(e)}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

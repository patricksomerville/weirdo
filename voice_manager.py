import os
import asyncio
from typing import Dict, Optional
from use_mcp_tool import use_mcp_tool

class VoiceManager:
    def __init__(self):
        # Create output directory for audio files
        self.output_dir = os.path.expanduser("~/weird_news_pipeline/audio")
        os.makedirs(self.output_dir, exist_ok=True)

    async def generate_narration(self, text: str, style: str = "newsreel_announcer") -> Optional[str]:
        """Generate narration using Make.com's vintage audio generation."""
        try:
            # Call Make.com scenario through MCP
            result = await use_mcp_tool(
                server_name="make",
                tool_name="generate_vintage_audio",
                arguments={
                    "text": text,
                    "style": style,
                    "effects": ["vinyl_crackle", "tube_amp"]
                }
            )

            if result and not result.get("isError"):
                # Parse the response
                response_data = json.loads(result["content"][0]["text"])
                audio_url = response_data["audio_url"]

                # Download the audio file
                async with aiohttp.ClientSession() as session:
                    async with session.get(audio_url) as response:
                        if response.status == 200:
                            # Generate unique filename
                            filename = f"narration_{int(asyncio.get_event_loop().time())}.mp3"
                            filepath = os.path.join(self.output_dir, filename)
                            
                            # Save the audio file
                            with open(filepath, "wb") as f:
                                f.write(await response.read())
                            
                            return filepath

            print(f"Error generating narration: {result.get('content', [{'text': 'Unknown error'}])[0]['text']}")
            return None

        except Exception as e:
            print(f"Error in generate_narration: {str(e)}")
            return None

    async def add_background_music(self, audio_path: str, style: str = "1940s_news") -> Optional[str]:
        """Add vintage background music to narration."""
        try:
            # Upload the audio file to a temporary URL
            # (In a real implementation, you'd use a proper file hosting service)
            audio_url = f"file://{audio_path}"

            # Call Make.com scenario through MCP
            result = await use_mcp_tool(
                server_name="make",
                tool_name="add_background_music",
                arguments={
                    "audio_url": audio_url,
                    "music_style": style,
                    "volume": 0.3
                }
            )

            if result and not result.get("isError"):
                # Parse the response
                response_data = json.loads(result["content"][0]["text"])
                mixed_audio_url = response_data["mixed_audio_url"]

                # Download the mixed audio file
                async with aiohttp.ClientSession() as session:
                    async with session.get(mixed_audio_url) as response:
                        if response.status == 200:
                            # Generate unique filename
                            filename = f"mixed_{int(asyncio.get_event_loop().time())}.mp3"
                            filepath = os.path.join(self.output_dir, filename)
                            
                            # Save the audio file
                            with open(filepath, "wb") as f:
                                f.write(await response.read())
                            
                            return filepath

            print(f"Error adding background music: {result.get('content', [{'text': 'Unknown error'}])[0]['text']}")
            return None

        except Exception as e:
            print(f"Error in add_background_music: {str(e)}")
            return None

    async def add_sound_effects(self, audio_path: str, effects: List[Dict]) -> Optional[str]:
        """Add vintage sound effects to audio."""
        try:
            # Upload the audio file to a temporary URL
            audio_url = f"file://{audio_path}"

            # Call Make.com scenario through MCP
            result = await use_mcp_tool(
                server_name="make",
                tool_name="add_sound_effects",
                arguments={
                    "audio_url": audio_url,
                    "effects": effects
                }
            )

            if result and not result.get("isError"):
                # Parse the response
                response_data = json.loads(result["content"][0]["text"])
                mixed_audio_url = response_data["mixed_audio_url"]

                # Download the mixed audio file
                async with aiohttp.ClientSession() as session:
                    async with session.get(mixed_audio_url) as response:
                        if response.status == 200:
                            # Generate unique filename
                            filename = f"effects_{int(asyncio.get_event_loop().time())}.mp3"
                            filepath = os.path.join(self.output_dir, filename)
                            
                            # Save the audio file
                            with open(filepath, "wb") as f:
                                f.write(await response.read())
                            
                            return filepath

            print(f"Error adding sound effects: {result.get('content', [{'text': 'Unknown error'}])[0]['text']}")
            return None

        except Exception as e:
            print(f"Error in add_sound_effects: {str(e)}")
            return None

async def main():
    """Test the VoiceManager."""
    manager = VoiceManager()
    
    # Test narration generation
    test_text = "FLASH! In an extraordinary turn of events, scientists have made a breakthrough discovery!"
    narration_path = await manager.generate_narration(test_text)
    
    if narration_path:
        print(f"Narration generated: {narration_path}")
        
        # Test adding background music
        with_music = await manager.add_background_music(narration_path)
        if with_music:
            print(f"Added background music: {with_music}")
            
            # Test adding sound effects
            effects = [
                {"type": "teletype", "timestamp": 0.5},
                {"type": "flash_bulb", "timestamp": 2.0}
            ]
            final_audio = await manager.add_sound_effects(with_music, effects)
            if final_audio:
                print(f"Added sound effects: {final_audio}")

if __name__ == "__main__":
    asyncio.run(main())

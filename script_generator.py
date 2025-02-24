import os
import json
import asyncio
from llm_manager import LLMManager
from config import LLM_CONFIGS

class ScriptGenerator:
    def __init__(self):
        self.llm_manager = LLMManager()
        self.system_prompt = """You are a vintage newsreel announcer from the 1940s, writing scripts for weird news stories.
Your style should capture the dramatic, theatrical tone of classic movie newsreels:
1. Use authoritative, bombastic language
2. Speak in present tense for immediacy
3. Include classic newsreel transitions like "And now!" and "In other news!"
4. Add dramatic pauses and emphasis
5. Keep the tone sensational and theatrical
6. Use period-appropriate expressions and vocabulary"""

    async def generate_hook(self, article, style="1940s newsreel"):
        """Generate an attention-grabbing newsreel-style hook."""
        if style == "1940s newsreel":
            hook_prompt = f"""Create a dramatic, 1940s newsreel-style opening for this weird news story:
Title: {article['title']}

Examples:
"FLASH! From the far corners of [Location] comes a tale that defies belief!"
"ATTENTION CITIZENS! Prepare yourselves for a story that will astound and amaze!"
"BREAKING NEWS from the world of the bizarre and extraordinary!"

Make it dramatic and attention-grabbing in the style of old movie newsreels."""
        elif style == "comedic":
            hook_prompt = f"""Create a funny, comedic opening for this weird news story:
Title: {article['title']}

Examples:
"Hold on to your hats, folks, because this one's a doozy!"
"You won't believe what happened next! (Spoiler: it's ridiculous)"
"Is this real life? Or is it just fantasy? (Probably the latter)"

Make it lighthearted and humorous."""
        else:  # Default to 1940s newsreel
            hook_prompt = f"""Create a dramatic, 1940s newsreel-style opening for this weird news story:
Title: {article['title']}

Examples:
"FLASH! From the far corners of [Location] comes a tale that defies belief!"
"ATTENTION CITIZENS! Prepare yourselves for a story that will astound and amaze!"
"BREAKING NEWS from the world of the bizarre and extraordinary!"

Make it dramatic and attention-grabbing in the style of old movie newsreels."""

        try:
            hook = await self.llm_manager.generate_response(hook_prompt, 'gpt4')
        except Exception:
            hook = await self.llm_manager.generate_response(hook_prompt, 'claude')
        return hook.strip()

    async def generate_cta(self, style="1940s newsreel"):
        """Generate a vintage-style call-to-action."""
        if style == "1940s newsreel":
            cta_prompt = """Generate a call-to-action that maintains the 1940s newsreel style while incorporating modern social media elements.

Examples:
"And now, dear viewers, share your thoughts in the comments below! What strange tales have YOU witnessed?"
"Stay tuned for more extraordinary reports from around the globe! Don't forget to subscribe!"
"This has been your Weird News Newsreel! Like and follow for more astounding stories!"

Make it sound like a classic newsreel sign-off while encouraging modern engagement."""
        elif style == "comedic":
            cta_prompt = """Generate a funny, comedic call-to-action that incorporates modern social media elements.

Examples:
"Don't forget to like and subscribe, or else... (ominous music)"
"Share this with your friends and spread the weirdness!"
"What's the weirdest thing YOU'VE ever seen? Tell us in the comments!"

Make it lighthearted and humorous."""
        else:  # Default to 1940s newsreel
            cta_prompt = """Generate a call-to-action that maintains the 1940s newsreel style while incorporating modern social media elements.

Examples:
"And now, dear viewers, share your thoughts in the comments below! What strange tales have YOU witnessed?"
"Stay tuned for more extraordinary reports from around the globe! Don't forget to subscribe!"
"This has been your Weird News Newsreel! Like and follow for more astounding stories!"

Make it sound like a classic newsreel sign-off while encouraging modern engagement."""
        
        try:
            cta = await self.llm_manager.generate_response(cta_prompt, 'gpt4')
        except Exception:
            cta = await self.llm_manager.generate_response(cta_prompt, 'claude')
        return cta.strip()

    async def generate_script(self, article, style="1940s newsreel"):
        """Generate a complete newsreel-style script."""
        # Generate hook first
        hook = await self.generate_hook(article, style)
        
        if style == "1940s newsreel":
            script_prompt = f"""Transform this weird news story into a 1940s-style newsreel script:

ARTICLE:
{article['title']}
{article.get('description', '')}
{article.get('url', '')}

REQUIREMENTS:
1. Start with this hook: {hook}
2. Write in the style of vintage movie newsreels
3. Use dramatic, authoritative language
4. Include classic newsreel transitions
5. Add [DRAMATIC PAUSE] and [EMPHASIS] markers
6. Suggest period-appropriate [MUSIC: triumphant brass]
7. Include [VISUAL: black and white footage] suggestions
8. Keep length to 30-60 seconds when read aloud

Format the script with:
- HOOK
- STORY (with dramatic pauses and emphasis)
- MUSIC AND VISUAL CUES
- SIGN-OFF

Example style:
"FLASH! In an astounding turn of events... [DRAMATIC PAUSE] 
Citizens of Milwaukee witness what can only be described as... [EMPHASIS] the most peculiar parade in history! 
[MUSIC: dramatic orchestral swell]
[VISUAL: panning shot of confused onlookers]"
"""
        elif style == "comedic":
            script_prompt = f"""Transform this weird news story into a comedic script:

ARTICLE:
{article['title']}
{article.get('description', '')}
{article.get('url', '')}

REQUIREMENTS:
1. Start with this hook: {hook}
2. Write in a funny, lighthearted style
3. Use jokes, puns, and witty observations
4. Add [COMEDIC PAUSE] and [EXAGGERATED REACTION] markers
5. Suggest silly [MUSIC: kazoo solo]
6. Include [VISUAL: cartoonish animation] suggestions
7. Keep length to 30-60 seconds when read aloud

Format the script with:
- HOOK
- STORY (with comedic pauses and exaggerated reactions)
- MUSIC AND VISUAL CUES
- SIGN-OFF

Example style:
"Well, folks, you won't believe this one... [COMEDIC PAUSE]
A squirrel in Central Park has been hoarding acorns... [EXAGGERATED REACTION] like it's the end of the world!
[MUSIC: kazoo solo]
[VISUAL: cartoonish animation of a squirrel stuffing acorns into its cheeks]"
"""
        else:  # Default to 1940s newsreel
            script_prompt = f"""Transform this weird news story into a 1940s-style newsreel script:

ARTICLE:
{article['title']}
{article.get('description', '')}
{article.get('url', '')}

REQUIREMENTS:
1. Start with this hook: {hook}
2. Write in the style of vintage movie newsreels
3. Use dramatic, authoritative language
4. Include classic newsreel transitions
5. Add [DRAMATIC PAUSE] and [EMPHASIS] markers
6. Suggest period-appropriate [MUSIC: triumphant brass]
7. Include [VISUAL: black and white footage] suggestions
8. Keep length to 30-60 seconds when read aloud

Format the script with:
- HOOK
- STORY (with dramatic pauses and emphasis)
- MUSIC AND VISUAL CUES
- SIGN-OFF

Example style:
"FLASH! In an astounding turn of events... [DRAMATIC PAUSE] 
Citizens of Milwaukee witness what can only be described as... [EMPHASIS] the most peculiar parade in history! 
[MUSIC: dramatic orchestral swell]
[VISUAL: panning shot of confused onlookers]"
"""

        # Generate main script with fallback options
        try:
            main_script = await self.llm_manager.generate_response(script_prompt, 'gpt4')
        except Exception:
            try:
                main_script = await self.llm_manager.generate_response(script_prompt, 'claude')
            except Exception:
                main_script = await self.llm_manager.generate_response(script_prompt, 'gemini')
        
        # Generate CTA
        cta = await self.generate_cta(style)
        
        # Combine all parts and format
        full_script = {
            "metadata": {
                "source_article": article['url'],
                "weirdness_score": article.get('weirdness_score', 0),
                "timestamp": article.get('created_at', ''),
                "style": style,
                "models_used": {
                    "primary": "gpt4",
                    "fallback": ["claude", "gemini"]
                }
            },
            "script_sections": {
                "hook": hook,
                "main_content": main_script,
                "cta": cta
            },
            "audio_notes": {
                "voice_style": "Authoritative, theatrical newsreel announcer",
                "pacing": "Quick and punchy with dramatic pauses",
                "music": "Period-appropriate orchestral and brass"
            },
            "visual_notes": {
                "style": "Black and white, vintage newsreel footage",
                "transitions": "Classic film reel transitions",
                "effects": "Grain overlay, slight flicker effect"
            },
            "estimated_duration": "30-60 seconds"
        }
        
        return full_script

    def save_script(self, script, filename):
        """Save the generated script to a JSON file."""
        filepath = os.path.join(os.path.expanduser("~/weird_news_pipeline/scripts"), filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(script, f, indent=4)
        
        return filepath

async def main():
    """Test the script generator with a sample article."""
    sample_article = {
        "title": "Florida Man Arrested for Attempting to 'Time Travel' by Driving Car into Building",
        "description": "A Florida man claimed he was trying to time travel when he drove his car through a building, causing thousands in damage.",
        "url": "https://example.com/weird-news",
        "weirdness_score": 9.5,
        "created_at": "2024-01-20T12:00:00Z"
    }
    
    generator = ScriptGenerator()
    
    # Generate 1940s newsreel script
    script1 = await generator.generate_script(sample_article, style="1940s newsreel")
    filepath1 = generator.save_script(script1, "test_script_1940s.json")
    print(f"Script generated and saved to: {filepath1}")
    print("\nGenerated Script:")
    print(json.dumps(script1, indent=2))
    
    # Generate comedic script
    script2 = await generator.generate_script(sample_article, style="comedic")
    filepath2 = generator.save_script(script2, "test_script_comedic.json")
    print(f"Script generated and saved to: {filepath2}")
    print("\nGenerated Script:")
    print(json.dumps(script2, indent=2))

if __name__ == "__main__":
    asyncio.run(main())

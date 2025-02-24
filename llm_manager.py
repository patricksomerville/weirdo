import time
import random
import asyncio
import aiohttp
from typing import Dict, List, Optional
import openai
from anthropic import Anthropic
import google.generativeai as genai
from config import LLM_CONFIGS, RATE_LIMIT_REQUESTS, RATE_LIMIT_PERIOD

class LLMManager:
    def __init__(self):
        self.llm_configs = LLM_CONFIGS
        self.rate_limit = RATE_LIMIT_REQUESTS
        self.rate_period = RATE_LIMIT_PERIOD
        self.request_times = []

    async def call_openai(self, prompt: str) -> str:
        """Call OpenAI's GPT-4 API."""
        response = await openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=self.llm_configs['gpt4']['max_tokens'],
            temperature=self.llm_configs['gpt4']['temperature']
        )
        return response.choices[0].message.content.strip()

    async def call_anthropic(self, prompt: str) -> str:
        """Call Anthropic's Claude API."""
        client = Anthropic(api_key=self.llm_configs['claude']['api_key'])
        response = await client.completions.create(
            prompt=prompt,
            max_tokens=self.llm_configs['claude']['max_tokens'],
            temperature=self.llm_configs['claude']['temperature']
        )
        return response['completion']

    async def call_google(self, prompt: str) -> str:
        """Call Google's Gemini API."""
        response = await genai.ChatCompletion.create(
            model="gemini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=self.llm_configs['gemini']['max_tokens'],
            temperature=self.llm_configs['gemini']['temperature']
        )
        return response.choices[0].message.content.strip()

    async def manage_requests(self, func, *args, **kwargs):
        """Manage rate limiting for API requests."""
        while True:
            current_time = time.time()
            self.request_times = [t for t in self.request_times if t > current_time - self.rate_period]
            if len(self.request_times) < self.rate_limit:
                self.request_times.append(current_time)
                return await func(*args, **kwargs)
            await asyncio.sleep(1)

    async def generate_response(self, prompt: str, model: str) -> str:
        """Generate a response using the specified model."""
        if model == 'gpt4':
            return await self.manage_requests(self.call_openai, prompt)
        elif model == 'claude':
            return await self.manage_requests(self.call_anthropic, prompt)
        elif model == 'gemini':
            return await self.manage_requests(self.call_google, prompt)
        else:
            raise ValueError("Unsupported model specified.")

def main():
    """Test the LLMManager with a sample prompt."""
    manager = LLMManager()
    prompt = "What is the weirdest news story you can think of?"
    
    loop = asyncio.get_event_loop()
    response = loop.run_until_complete(manager.generate_response(prompt, 'gpt4'))
    print("Response from GPT-4:", response)

if __name__ == "__main__":
    main()

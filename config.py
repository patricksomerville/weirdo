import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# System Configuration
RATE_LIMIT_REQUESTS = int(os.getenv('RATE_LIMIT_REQUESTS', 50))
RATE_LIMIT_PERIOD = int(os.getenv('RATE_LIMIT_PERIOD', 60))
MAX_PARALLEL_REQUESTS = int(os.getenv('MAX_PARALLEL_REQUESTS', 10))
REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', 30))

# LLM Configuration
LLM_CONFIGS = {
    'gpt4': {
        'api_key': os.getenv('OPENAI_API_KEY'),
        'org_id': os.getenv('OPENAI_ORG_ID'),
        'max_tokens': int(os.getenv('OPENAI_MAX_TOKENS', 4096)),
        'temperature': float(os.getenv('OPENAI_TEMPERATURE', 0.7)),
        'weight': float(os.getenv('MODEL_WEIGHTS_GPT4', 1.0))
    },
    'claude': {
        'api_key': os.getenv('ANTHROPIC_API_KEY'),
        'max_tokens': int(os.getenv('ANTHROPIC_MAX_TOKENS', 4096)),
        'temperature': float(os.getenv('ANTHROPIC_TEMPERATURE', 0.7)),
        'weight': float(os.getenv('MODEL_WEIGHTS_CLAUDE', 0.9))
    },
    'mistral': {
        'api_key': os.getenv('MISTRAL_API_KEY'),
        'max_tokens': int(os.getenv('MISTRAL_MAX_TOKENS', 4096)),
        'temperature': float(os.getenv('MISTRAL_TEMPERATURE', 0.7)),
        'weight': float(os.getenv('MODEL_WEIGHTS_MISTRAL', 0.8))
    },
    'deepseek': {
        'api_key': os.getenv('DEEPSEEK_API_KEY'),
        'max_tokens': int(os.getenv('DEEPSEEK_MAX_TOKENS', 4096)),
        'temperature': float(os.getenv('DEEPSEEK_TEMPERATURE', 0.7)),
        'weight': float(os.getenv('MODEL_WEIGHTS_DEEPSEEK', 0.8))
    },
    'gemini': {
        'api_key': os.getenv('GOOGLE_API_KEY'),
        'max_tokens': int(os.getenv('GEMINI_MAX_TOKENS', 100000)),
        'temperature': float(os.getenv('GEMINI_TEMPERATURE', 0.7)),
        'weight': float(os.getenv('MODEL_WEIGHTS_GEMINI', 0.9))
    },
    'perplexity': {
        'api_key': os.getenv('PERPLEXITY_API_KEY'),
        'max_tokens': int(os.getenv('PERPLEXITY_MAX_TOKENS', 4096)),
        'temperature': float(os.getenv('PERPLEXITY_TEMPERATURE', 0.7)),
        'weight': float(os.getenv('MODEL_WEIGHTS_PERPLEXITY', 0.7))
    }
}

# Voice Generation Configuration
VOICE_CONFIGS = {
    'elevenlabs': {
        'api_key': os.getenv('ELEVENLABS_API_KEY'),
        'model': os.getenv('ELEVENLABS_MODEL', 'eleven_multilingual_v2'),
        'voice_id': os.getenv('ELEVENLABS_VOICE_ID'),
        'stability': float(os.getenv('ELEVENLABS_STABILITY', 0.75)),
        'similarity_boost': float(os.getenv('ELEVENLABS_SIMILARITY_BOOST', 0.75)),
        'weight': float(os.getenv('MODEL_WEIGHTS_ELEVENLABS', 0.8))
    },
    'uberduck': {
        'api_key': os.getenv('UBERDUCK_API_KEY'),
        'api_secret': os.getenv('UBERDUCK_API_SECRET'),
        'model': os.getenv('UBERDUCK_MODEL', 'uberduck-ml-v3'),
        'voice_id': os.getenv('UBERDUCK_VOICE_ID'),
        'pace': float(os.getenv('UBERDUCK_PACE', 1.0)),
        'emotion_weight': float(os.getenv('UBERDUCK_EMOTION_WEIGHT', 0.7)),
        'weight': float(os.getenv('MODEL_WEIGHTS_UBERDUCK', 0.8))
    }
}

# Stock Footage Configuration
STOCK_FOOTAGE_CONFIGS = {
    'pexels': {
        'api_key': os.getenv('PEXELS_API_KEY'),
        'api_host': 'https://api.pexels.com/videos',
        'per_page': 15,
        'min_width': 1920,
        'min_duration': 3,
        'max_duration': 30
    }
}

# Image Generation Configuration
IMAGE_CONFIGS = {
    'stability': {
        'api_key': os.getenv('STABILITY_API_KEY'),
        'api_host': "https://api.stability.ai",
        'engine_id': "stable-diffusion-xl-1024-v1-0",
        'height': 1024,
        'width': 1024,
        'cfg_scale': 7,
        'steps': 30,
        'samples': 1
    },
    'runway': {
        'api_key': os.getenv('RUNWAY_KEY', 'key_d6492b0692f4079fd08832ee3c3df17ac68845811f1fc4d3e54108a9ae920822c56b19e8ab16252c1cf82eb3ad492f4c602d8a5a9096d23f2a750015b1eef44f'),
        'api_host': "https://api.runwayml.com/v1",
        'model': "stable-diffusion-v1",
        'height': 1024,
        'width': 1024,
        'num_outputs': 1,
        'steps': 30
    }
}

def validate_config():
    """Validates that all required environment variables are set."""
    required_vars = [
        'OPENAI_API_KEY',
        'NEWS_API_KEY',
        'SUPABASE_URL',
        'SUPABASE_KEY',
        'REDDIT_CLIENT_ID',
        'REDDIT_CLIENT_SECRET',
        'TWITTER_BEARER_TOKEN',
        'ELEVENLABS_API_KEY',
        'PEXELS_API_KEY',
        'STABILITY_API_KEY'
    ]
    
    for var in required_vars:
        if not os.getenv(var):
            logging.error(f"Required environment variable {var} is not set.")
            raise ValueError(f"Missing required environment variable: {var}")
    logging.info("All required environment variables are set.")

# Validate configuration on startup
validate_config()

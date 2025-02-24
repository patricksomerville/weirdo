from quart import Quart, request, jsonify
import os
import time
import threading
import json
import subprocess
import tempfile
import asyncio
import aiohttp
from dotenv import load_dotenv
import openai
from google.cloud import language_v1
from supabase import create_client, Client
import praw
import tweepy
from datetime import datetime
from script_generator import ScriptGenerator
from video_pipeline import VideoPipeline

# Load environment variables
load_dotenv()

# Initialize APIs
openai.api_key = os.getenv("OPENAI_API_KEY")
newsapi_key = os.getenv("NEWS_API_KEY")
supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

# Reddit initialization
reddit_client_id=os.getenv("REDDIT_CLIENT_ID")
reddit_client_secret=os.getenv("REDDIT_CLIENT_SECRET")
user_agent="WeirdNewsScraper/1.0"

# Twitter/X initialization
twitter_client = tweepy.Client(
    bearer_token=os.getenv("TWITTER_BEARER_TOKEN")
)

# Configure Quart app for async support
app = Quart(__name__)

# Root directory for the pipeline
BASE_DIR = os.path.expanduser("~/weird_news_pipeline")
LOG_FILE = os.path.join(BASE_DIR, "pipeline_log.json")
SCRIPTS_DIR = os.path.join(BASE_DIR, "scripts")
VIDEOS_DIR = os.path.join(BASE_DIR, "videos")

# Ensure directories exist
for directory in [BASE_DIR, SCRIPTS_DIR, VIDEOS_DIR]:
    os.makedirs(directory, exist_ok=True)

def log_event(event):
    """Logs events to a JSON file for system tracking."""
    logs = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            logs = json.load(f)
    logs.append({"timestamp": time.time(), "event": event})
    with open(LOG_FILE, "w") as f:
        json.dump(logs, f, indent=4)
    print(f"[LOG]: {event}")

class NewsSource:
    """Base class for news sources"""
    async def fetch_articles(self):
        raise NotImplementedError

class NewsAPIScraper(NewsSource):
    async def fetch_articles(self):
        """Fetch articles from NewsAPI asynchronously"""
        async with aiohttp.ClientSession() as session:
            url = f"https://newsapi.org/v2/everything?q=weird OR strange OR unusual&apiKey={newsapi_key}"
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('articles', [])
                return []

class RedditScraper(NewsSource):
    reddit = None
    async def fetch_articles(self):
        """Fetch articles from Reddit weird news subreddits"""
        if not RedditScraper.reddit:
            RedditScraper.reddit = praw.Reddit(
                client_id=reddit_client_id,
                client_secret=reddit_client_secret,
                user_agent=user_agent
            )
        subreddits = ['WeirdNews', 'nottheonion', 'offbeat']
        articles = []
        for subreddit_name in subreddits:
            try:
                subreddit = RedditScraper.reddit.subreddit(subreddit_name)
                posts = subreddit.hot(limit=25)
                async for post in posts:
                    try:
                        articles.append({
                            'title': post.title,
                            'url': post.url,
                            'score': post.score,
                            'source': f'reddit/{subreddit_name}'
                        })
                    except Exception as e:
                        print(f"Error processing Reddit post: {str(e)}")
                        continue
            except Exception as e:
                print(f"Error processing subreddit {subreddit_name}: {str(e)}")
                continue
        return articles

class TwitterScraper(NewsSource):
    async def fetch_articles(self):
        """Fetch trending weird news from Twitter/X"""
        query = "weird news OR strange news OR unusual news"
        tweets = await twitter_client.search_recent_tweets(
            query=query,
            max_results=100
        )
        return [{
            'title': tweet.text,
            'url': f"https://twitter.com/x/status/{tweet.id}",
            'source': 'twitter'
        } for tweet in tweets.data] if tweets.data else []

class WeirdnessScorer:
    def __init__(self):
        self.language_client = language_v1.LanguageServiceClient()

    async def analyze_entities(self, text):
        """Analyze entities in text using Google Cloud NLP"""
        document = language_v1.Document(
            content=text,
            type_=language_v1.Document.Type.PLAIN_TEXT
        )
        return self.language_client.analyze_entities(document=document)

    async def get_gpt_weirdness_score(self, text):
        """Use GPT to determine weirdness score"""
        response = await openai.ChatCompletion.acreate(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Rate the weirdness of this news story on a scale of 1-10, where 10 is the weirdest. Respond with just the number."},
                {"role": "user", "content": text}
            ]
        )
        try:
            return float(response.choices[0].message.content.strip())
        except ValueError:
            return 5.0

    async def calculate_weirdness_score(self, article):
        """Calculate overall weirdness score"""
        # Combine title and description for analysis
        text = f"{article.get('title', '')} {article.get('description', '')}"
        
        # Get GPT weirdness score
        gpt_score = await self.get_gpt_weirdness_score(text)
        
        # Analyze entities
        entity_analysis = await self.analyze_entities(text)
        unusual_entities = len([entity for entity in entity_analysis.entities
                              if entity.salience > 0.3])
        
        # Calculate engagement score
        engagement_score = min(article.get('score', 0) / 1000, 10)
        
        # Combine scores (weighted average)
        final_score = (
            gpt_score * 0.5 +           # GPT score (50% weight)
            unusual_entities * 0.3 +     # Unusual entities (30% weight)
            engagement_score * 0.2       # Engagement (20% weight)
        )
        
        return min(final_score, 10)  # Cap at 10

class NewsPipeline:
    def __init__(self):
        self.sources = [
            NewsAPIScraper(),
            RedditScraper(),
            TwitterScraper()
        ]
        self.scorer = WeirdnessScorer()

    async def run(self):
        """Run the full pipeline"""
        # 1. Collect articles from all sources
        all_articles = []
        for source in self.sources:
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    articles = await source.fetch_articles()
                    all_articles.extend(articles)
                    log_event(f"Fetched {len(articles)} articles from {source.__class__.__name__}")
                    break  # Break the retry loop if successful
                except Exception as e:
                    log_event(f"Error fetching from {source.__class__.__name__} (Attempt {attempt + 1}/{max_retries}): {str(e)}")
                    if attempt == max_retries - 1:
                        log_event(f"Failed to fetch from {source.__class__.__name__} after multiple retries.")
                    await asyncio.sleep(5)  # Wait before retrying

        # 2. Score and rank articles
        scored_articles = []
        for article in all_articles:
            try:
                score = await self.scorer.calculate_weirdness_score(article)
                article['weirdness_score'] = score
                scored_articles.append(article)
                log_event(f"Scored article: {article['title']} - Score: {score}")
            except Exception as e:
                log_event(f"Error scoring article: {str(e)}")

        # 3. Sort by weirdness score
        ranked_articles = sorted(
            scored_articles,
            key=lambda x: x.get('weirdness_score', 0),
            reverse=True
        )

        # 4. Store top articles in Supabase
        if ranked_articles:
            top_article = ranked_articles[0]
            try:
                supabase.table('weird_news').insert({
                    'title': top_article['title'],
                    'url': top_article['url'],
                    'source': top_article['source'],
                    'weirdness_score': top_article['weirdness_score'],
                    'created_at': datetime.now().isoformat()
                }).execute()
                log_event(f"Stored top article: {top_article['title']}")
            except Exception as e:
                log_event(f"Error storing article: {str(e)}")

        # Generate newsreel script for top article
        if ranked_articles:
            generator = ScriptGenerator()
            script = await generator.generate_script(ranked_articles[0])
            timestamp = int(time.time())
            script_path = os.path.join(SCRIPTS_DIR, f"newsreel_script_{timestamp}.json")
            generator.save_script(script, script_path)
            log_event(f"Generated newsreel script for top article: {ranked_articles[0]['title']}")
            
            result = {
                "status": "success",
                "articles": ranked_articles[:10],
                "script": {
                    "path": script_path,
                    "content": script,
                    "style": "1940s newsreel"
                }
            }
        else:
            result = {
                "status": "success",
                "articles": []
            }
        return result

@app.route('/run', methods=['POST'])
async def run_pipeline():
    """Endpoint to trigger pipeline execution"""
    try:
        pipeline = NewsPipeline()
        result = await pipeline.run()
        return jsonify({
            "status": "success",
            **result
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/top', methods=['GET'])
async def get_top_articles():
    """Get today's top weird news articles"""
    try:
        response = supabase.table('weird_news') \
            .select('*') \
            .order('created_at', desc=True) \
            .limit(10) \
            .execute()
        return jsonify({
            "status": "success",
            "articles": response.data
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/generate-video', methods=['POST'])
async def generate_video():
    """Endpoint for Make.com to trigger video generation"""
    try:
        # Get webhook URL for notifications if provided
        webhook_url = request.json.get('webhook_url') if request.is_json else None
        
        # Initialize video pipeline
        pipeline = VideoPipeline()
        
        # Start video generation
        try:
            output_path = await pipeline.generate_daily_video()
            
            # Store video info in Supabase
            video_info = {
                'path': output_path,
                'status': 'completed',
                'created_at': datetime.now().isoformat()
            }
            
            supabase.table('videos').insert(video_info).execute()
            
            # Send success webhook if URL provided
            if webhook_url:
                async with aiohttp.ClientSession() as session:
                    await session.post(webhook_url, json={
                        'status': 'success',
                        'video': video_info
                    })
            
            return jsonify({
                'status': 'success',
                'video': video_info
            })
            
        except Exception as e:
            error_info = {
                'error': str(e),
                'status': 'failed',
                'timestamp': datetime.now().isoformat()
            }
            
            # Store error in Supabase
            supabase.table('pipeline_errors').insert(error_info).execute()
            
            # Send error webhook if URL provided
            if webhook_url:
                async with aiohttp.ClientSession() as session:
                    await session.post(webhook_url, json={
                        'status': 'error',
                        'error': error_info
                    })
            
            return jsonify(error_info), 500
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/video-status/<video_id>', methods=['GET'])
async def get_video_status(video_id):
    """Get status of a video generation job"""
    try:
        response = supabase.table('videos') \
            .select('*') \
            .eq('id', video_id) \
            .execute()
            
        if response.data:
            return jsonify({
                'status': 'success',
                'video': response.data[0]
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Video not found'
            }), 404
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

async def auto_run():
    """Automatically run the pipeline periodically"""
    while True:
        try:
            pipeline = NewsPipeline()
            await pipeline.run()
            log_event("Auto-run completed successfully")
        except Exception as e:
            log_event(f"Auto-run failed: {str(e)}")
        await asyncio.sleep(3600)  # Run every hour

# Start the auto-run thread
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
auto_thread = threading.Thread(target=lambda: loop.run_forever(), daemon=True)
auto_thread.start()
loop.create_task(auto_run())

if __name__ == '__main__':
    log_event("Weird news pipeline service started")
    app.run(debug=True, port=5000)

import os
import asyncio
import aiohttp
import json
import schedule
import time
from datetime import datetime
from bs4 import BeautifulSoup
from typing import List, Dict
from config import STOCK_FOOTAGE_CONFIGS

class NewsScraper:
    def __init__(self):
        self.base_dir = os.path.expanduser("~/weird_news_pipeline")
        self.cache_dir = os.path.join(self.base_dir, "cache")
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Sources configuration
        self.sources = {
            'reddit': {
                'subreddits': ['WeirdNews', 'nottheonion', 'offbeat'],
                'url': 'https://www.reddit.com/r/{}/new.json',
                'headers': {'User-Agent': 'WeirdNewsScraper/1.0'}
            },
            'newsapi': {
                'url': 'https://newsapi.org/v2/everything',
                'api_key': os.getenv('NEWS_API_KEY'),
                'keywords': ['weird', 'strange', 'unusual', 'bizarre', 'odd']
            }
        }

    async def fetch_reddit_articles(self) -> List[Dict]:
        """Fetch articles from specified subreddits."""
        articles = []
        
        async with aiohttp.ClientSession() as session:
            for subreddit in self.sources['reddit']['subreddits']:
                url = self.sources['reddit']['url'].format(subreddit)
                headers = self.sources['reddit']['headers']
                
                try:
                    async with session.get(url, headers=headers) as response:
                        if response.status == 200:
                            data = await response.json()
                            for post in data['data']['children']:
                                post_data = post['data']
                                articles.append({
                                    'id': post_data['id'],
                                    'title': post_data['title'],
                                    'url': post_data['url'],
                                    'source': f'reddit/{subreddit}',
                                    'created_at': datetime.fromtimestamp(post_data['created_utc']).isoformat(),
                                    'score': post_data['score']
                                })
                except Exception as e:
                    print(f"Error fetching from r/{subreddit}: {str(e)}")
                
                # Respect rate limits
                await asyncio.sleep(2)
        
        return articles

    async def fetch_newsapi_articles(self) -> List[Dict]:
        """Fetch articles from NewsAPI."""
        articles = []
        
        if not self.sources['newsapi']['api_key']:
            print("NewsAPI key not configured")
            return articles
        
        async with aiohttp.ClientSession() as session:
            for keyword in self.sources['newsapi']['keywords']:
                params = {
                    'q': keyword,
                    'apiKey': self.sources['newsapi']['api_key'],
                    'language': 'en',
                    'sortBy': 'publishedAt'
                }
                
                try:
                    async with session.get(self.sources['newsapi']['url'], params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            for article in data.get('articles', []):
                                articles.append({
                                    'id': hash(article['url']),  # Create unique ID from URL
                                    'title': article['title'],
                                    'description': article.get('description', ''),
                                    'url': article['url'],
                                    'source': f"newsapi/{article['source']['name']}",
                                    'created_at': article['publishedAt']
                                })
                except Exception as e:
                    print(f"Error fetching from NewsAPI with keyword '{keyword}': {str(e)}")
                
                # Respect rate limits
                await asyncio.sleep(1)
        
        return articles

    def calculate_weirdness_score(self, article: Dict) -> float:
        """Calculate a weirdness score for an article based on various factors."""
        score = 0.0
        
        # Check title for weird keywords
        weird_keywords = ['bizarre', 'strange', 'unusual', 'mysterious', 'unexpected', 
                         'surprising', 'odd', 'weird', 'incredible', 'unbelievable']
        title_lower = article['title'].lower()
        
        # Add points for each weird keyword
        score += sum(2.0 for keyword in weird_keywords if keyword in title_lower)
        
        # Add points for engagement (if available)
        if 'score' in article:
            score += min(article['score'] / 1000, 3.0)  # Cap at 3 points
        
        # Add points for recency
        try:
            created_at = datetime.fromisoformat(article['created_at'].replace('Z', '+00:00'))
            hours_old = (datetime.now() - created_at).total_seconds() / 3600
            if hours_old < 24:
                score += 2.0
            elif hours_old < 48:
                score += 1.0
        except Exception:
            pass
        
        # Normalize score to 0-10 range
        return min(max(score, 0.0), 10.0)

    async def fetch_all_articles(self) -> List[Dict]:
        """Fetch articles from all sources and calculate weirdness scores."""
        # Fetch from all sources concurrently
        reddit_articles = await self.fetch_reddit_articles()
        newsapi_articles = await self.fetch_newsapi_articles()
        
        # Combine articles and calculate scores
        all_articles = reddit_articles + newsapi_articles
        for article in all_articles:
            article['weirdness_score'] = self.calculate_weirdness_score(article)
        
        # Sort by weirdness score
        all_articles.sort(key=lambda x: x['weirdness_score'], reverse=True)
        
        # Cache the results
        cache_path = os.path.join(self.cache_dir, f"articles_{int(time.time())}.json")
        with open(cache_path, 'w') as f:
            json.dump(all_articles, f, indent=2)
        
        return all_articles

    def get_weirdest_article(self) -> Dict:
        """Get the weirdest article from the most recent cache."""
        # Find the most recent cache file
        cache_files = [f for f in os.listdir(self.cache_dir) if f.startswith('articles_')]
        if not cache_files:
            raise Exception("No cached articles found")
        
        latest_cache = max(cache_files)
        cache_path = os.path.join(self.cache_dir, latest_cache)
        
        with open(cache_path, 'r') as f:
            articles = json.load(f)
        
        if not articles:
            raise Exception("No articles found in cache")
        
        return articles[0]  # Return the article with highest weirdness score

async def main():
    """Test the NewsScraper functionality."""
    scraper = NewsScraper()
    
    print("Fetching articles...")
    articles = await scraper.fetch_all_articles()
    
    print(f"\nFound {len(articles)} articles")
    print("\nTop 5 weirdest articles:")
    for article in articles[:5]:
        print(f"\nTitle: {article['title']}")
        print(f"Source: {article['source']}")
        print(f"Weirdness Score: {article['weirdness_score']:.2f}")
        print(f"URL: {article['url']}")

if __name__ == "__main__":
    asyncio.run(main())

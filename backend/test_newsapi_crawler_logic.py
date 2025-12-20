import os
import sys
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
from newsapi import NewsApiClient

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Replicate EnhancedNewsCrawler env loading
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
print(f"Loading .env from: {env_path}")
load_dotenv(dotenv_path=env_path)

api_key = os.getenv('NEWS_API_KEY')
print(f"API Key: {api_key[:4]}..." if api_key else "API Key: None")

def test_crawler_logic():
    if not api_key:
        print("No API Key")
        return

    client = NewsApiClient(api_key=api_key)
    
    # Replicate Crawler Logic
    hours = 24
    max_articles = 50
    
    # Keywords
    TICKER_KEYWORDS = {
        'NVDA': ['NVIDIA', 'Nvidia', 'nvda', 'H100', 'H200', 'Blackwell', 'B200', 'Grace Hopper'],
        'GOOGL': ['Google', 'Alphabet', 'TPU', 'TPU v5', 'TPU v6', 'Cloud TPU'],
    }
    GENERAL_KEYWORDS = [
        'semiconductor', 'AI chip', 'GPU', 'accelerator', 'processor'
    ]
    
    all_keywords = []
    for keywords in TICKER_KEYWORDS.values():
        all_keywords.extend(keywords)
    all_keywords.extend(GENERAL_KEYWORDS)
    
    unique_keywords = list(set(all_keywords))[:30]
    query = ' OR '.join(f'"{kw}"' for kw in unique_keywords[:20])
    
    # UTC Time
    from_date = datetime.utcnow() - timedelta(hours=hours)
    from_str = from_date.strftime('%Y-%m-%dT%H:%M:%S')
    
    print(f"\n--- 1. Initial Query ---")
    print(f"Query: {query}")
    print(f"From: {from_str}")
    
    try:
        response = client.get_everything(
            q=query,
            language='en',
            from_param=from_str,
            sort_by='publishedAt',
            page_size=max_articles
        )
        print(f"Status: {response.get('status')}")
        print(f"Total Results: {response.get('totalResults')}")
        
        if response['status'] == 'ok' and response['totalResults'] == 0:
            print("\n--- 2. Fallback Query ---")
            fallback_query = 'technology OR AI OR "stock market" OR semiconductor'
            print(f"Fallback Query: {fallback_query}")
            
            response = client.get_everything(
                q=fallback_query,
                language='en',
                from_param=from_str,
                sort_by='publishedAt',
                page_size=max_articles
            )
            print(f"Status: {response.get('status')}")
            print(f"Total Results: {response.get('totalResults')}")
            
            if response['totalResults'] == 0:
                print("\n--- 3. Fallback WITHOUT Date ---")
                response = client.get_everything(
                    q=fallback_query,
                    language='en',
                    sort_by='publishedAt',
                    page_size=max_articles
                )
                print(f"Status: {response.get('status')}")
                print(f"Total Results: {response.get('totalResults')}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_crawler_logic()

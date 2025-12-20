import os
from dotenv import load_dotenv
from newsapi import NewsApiClient
import json
from datetime import datetime, timedelta

# Load environment variables
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
print(f"Loading .env from: {env_path}")
load_dotenv(dotenv_path=env_path)

api_key = os.getenv('NEWS_API_KEY')
print(f"API Key loaded: {'Yes' if api_key else 'No'}")
if api_key:
    print(f"API Key (first 4 chars): {api_key[:4]}...")

try:
    # Initialize client
    newsapi = NewsApiClient(api_key=api_key)

    # 1. Simple test with broad query
    print("\n--- Test 1: Broad Query ('AI') ---")
    top_headlines = newsapi.get_top_headlines(q='AI', language='en')
    print(f"Top Headlines status: {top_headlines.get('status')}")
    print(f"Total Results: {top_headlines.get('totalResults')}")
    
    if top_headlines.get('articles'):
        print(f"First article: {top_headlines['articles'][0]['title']}")

    # 2. Test with Everything endpoint (simulating crawler)
    print("\n--- Test 2: Everything Endpoint (Simple) ---")
    # Try without date first
    all_articles = newsapi.get_everything(
        q='technology',
        language='en',
        sort_by='publishedAt',
        page_size=5
    )
    print(f"Simple Everything status: {all_articles.get('status')}")
    print(f"Total Results: {all_articles.get('totalResults')}")
    
    # 3. Test with Date (UTC)
    print("\n--- Test 3: Everything Endpoint (With Date UTC) ---")
    # Use UTC time!
    from_date = (datetime.utcnow() - timedelta(hours=24)).strftime('%Y-%m-%dT%H:%M:%S')
    print(f"From date (UTC): {from_date}")
    
    all_articles_date = newsapi.get_everything(
        q='technology',
        from_param=from_date,
        language='en',
        sort_by='publishedAt',
        page_size=5
    )
    print(f"Date Everything status: {all_articles_date.get('status')}")
    print(f"Total Results: {all_articles_date.get('totalResults')}")

    # 4. Test with Complex Query (Simulating Crawler)
    print("\n--- Test 4: Complex Query (UTC) ---")
    keywords = ["NVIDIA", "AI", "GPU", "Blackwell"]
    query = ' OR '.join(f'"{kw}"' for kw in keywords)
    print(f"Query: {query}")
    
    complex_articles = newsapi.get_everything(
        q=query,
        from_param=from_date,
        language='en',
        sort_by='publishedAt',
        page_size=5
    )
    print(f"Complex status: {complex_articles.get('status')}")
    print(f"Total Results: {complex_articles.get('totalResults')}")

except Exception as e:
    print(f"\n❌ Error: {str(e)}")

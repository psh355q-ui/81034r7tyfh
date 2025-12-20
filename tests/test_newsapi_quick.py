"""Quick test to verify NewsAPI connection"""
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv('NEWS_API_KEY')
print(f"API Key loaded: {'Yes' if api_key else 'No'}")
if api_key:
    print(f"API Key (masked): {api_key[:8]}...")
    
    try:
        from newsapi import NewsApiClient
        client = NewsApiClient(api_key=api_key)
        
        # Simple test query
        response = client.get_top_headlines(
            q='NVIDIA',
            language='en',
            page_size=5
        )
        
        if response['status'] == 'ok':
            articles = response.get('articles', [])
            print(f"\n✅ NewsAPI Connected! Found {len(articles)} articles")
            
            for i, article in enumerate(articles[:3], 1):
                print(f"\n{i}. {article['title']}")
                print(f"   Source: {article['source']['name']}")
                print(f"   URL: {article['url'][:60]}...")
        else:
            print(f"\n❌ NewsAPI Error: {response}")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
else:
    print("\n❌ No API key found")

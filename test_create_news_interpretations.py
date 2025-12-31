#!/usr/bin/env python
"""
Create News Interpretations for Accountability Phase
Reads news from SQLite and creates interpretations in PostgreSQL
"""
import sys
import os
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv(project_root / '.env', override=True)

print("="*80)
print(f"Create News Interpretations - {datetime.now().strftime('%H:%M:%S')}")
print("="*80)
print()

# Step 1: Read news from SQLite
print("[1/4] Reading Recent News from SQLite...")
print("-"*80)

# SQLite DB: /tmp/news.db (뉴스 수집 데이터)
# - news_articles (1,097건)
# - news_analysis (348건)
from backend.data.news_models import SessionLocal as NewsSession, NewsArticle, NewsAnalysis

news_db = NewsSession()

# Get recent analyzed news (last 7 days)
# Eagerly load ticker_relevances to avoid lazy loading after session close
from sqlalchemy.orm import joinedload

cutoff_date = datetime.now() - timedelta(days=7)
recent_news = news_db.query(NewsArticle).options(
    joinedload(NewsArticle.ticker_relevances)
).join(NewsAnalysis).filter(
    NewsArticle.published_at >= cutoff_date
).order_by(NewsArticle.published_at.desc()).limit(10).all()

print(f"✅ Found {len(recent_news)} recent analyzed news articles")
for i, article in enumerate(recent_news, 1):
    print(f"{i}. {article.title[:70]}...")
    print(f"   Source: {article.source}, Published: {article.published_at}")
    if article.analysis:
        print(f"   Sentiment: {article.analysis.sentiment_overall}, Actionable: {article.analysis.trading_actionable}")
print()

news_db.close()

# Step 2: Get Macro Context
print("[2/4] Loading Current Macro Context...")
print("-"*80)

# PostgreSQL DB: localhost:5433/ai_trading (Accountability 데이터)
# - macro_context_snapshots (1건)
# - news_interpretations (0건 → 여기에 저장할 예정)
from backend.database.repository import MacroContextRepository, get_sync_session
from datetime import date

pg_session = get_sync_session()
macro_repo = MacroContextRepository(pg_session)

# Try to get today's or yesterday's macro context
macro_context = macro_repo.get_by_date(date.today())
if not macro_context:
    yesterday = date.today() - timedelta(days=1)
    macro_context = macro_repo.get_by_date(yesterday)

if macro_context:
    print(f"✅ Macro Context loaded ({macro_context.snapshot_date}):")
    print(f"   Regime: {macro_context.regime}")
    print(f"   Fed Stance: {macro_context.fed_stance}")
    print(f"   Market Sentiment: {macro_context.market_sentiment}")
    print(f"   VIX: {macro_context.vix_level} ({macro_context.vix_category})")
else:
    print("⚠️ No macro context found, using default context")
print()

# Step 3: Create News Interpretations with Claude
print("[3/4] Creating News Interpretations with Claude...")
print("-"*80)

from anthropic import Anthropic
from backend.database.models import NewsInterpretation

client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

created_count = 0

for article in recent_news[:5]:  # Limit to 5 for testing
    try:
        # Skip if no ticker relevance
        if not article.ticker_relevances:
            print(f"⏭️  Skipping '{article.title[:50]}...' (no ticker relevance)")
            continue

        ticker = article.ticker_relevances[0].ticker

        # Create interpretation prompt
        prompt = f"""Analyze this news headline for trading impact.

News: {article.title}
Ticker: {ticker}
Source: {article.source}
Published: {article.published_at}

Market Context:
- Regime: {macro_context.regime if macro_context else 'UNKNOWN'}
- Fed Stance: {macro_context.fed_stance if macro_context else 'UNKNOWN'}
- Market Sentiment: {macro_context.market_sentiment if macro_context else 'UNKNOWN'}

Provide analysis in this JSON format:
{{
    "direction": "BULLISH" | "BEARISH" | "NEUTRAL",
    "confidence": 0.0-1.0,
    "expected_magnitude": "HIGH" | "MEDIUM" | "LOW",
    "time_horizon": "IMMEDIATE" | "INTRADAY" | "MULTI_DAY",
    "reasoning": "Brief explanation (max 200 chars)"
}}

Return ONLY valid JSON."""

        response = client.messages.create(
            model='claude-3-5-haiku-20241022',
            max_tokens=500,
            messages=[{'role': 'user', 'content': prompt}]
        )

        # Parse response
        import json
        import re
        response_text = response.content[0].text.strip()
        json_match = re.search(r'\{[^}]+\}', response_text, re.DOTALL)

        if json_match:
            interpretation = json.loads(json_match.group())

            # Create NewsInterpretation record
            # Map to actual database columns
            news_interp = NewsInterpretation(
                ticker=ticker,
                headline_bias=interpretation['direction'],  # BULLISH/BEARISH/NEUTRAL
                expected_impact=interpretation['expected_magnitude'],  # HIGH/MEDIUM/LOW
                time_horizon=interpretation['time_horizon'],  # IMMEDIATE/INTRADAY/MULTI_DAY
                confidence=int(interpretation['confidence'] * 100),  # 0-100
                reasoning=interpretation['reasoning'],
                macro_context_id=macro_context.id if macro_context else None
            )

            pg_session.add(news_interp)
            pg_session.flush()

            created_count += 1
            print(f"✅ {ticker}: {interpretation['direction']} ({interpretation['confidence']:.0%} confidence)")
            print(f"   {interpretation['reasoning'][:80]}...")
        else:
            print(f"❌ Failed to parse response for {article.title[:50]}...")

    except Exception as e:
        print(f"❌ Error processing article: {e}")
        import traceback
        traceback.print_exc()

pg_session.commit()
print()
print(f"✅ Created {created_count} news interpretations")
print()

# Step 4: Verify
print("[4/4] Verifying Results...")
print("-"*80)

from backend.database.models import NewsInterpretation
interp_count = pg_session.query(NewsInterpretation).count()
print(f"Total news_interpretations: {interp_count}")

# Show recent
recent_interps = pg_session.query(NewsInterpretation).order_by(
    NewsInterpretation.created_at.desc()
).limit(5).all()

for interp in recent_interps:
    print(f"  - {interp.ticker}: {interp.headline_bias} ({interp.confidence}% confidence)")
    print(f"    Impact: {interp.expected_impact}, Horizon: {interp.time_horizon}")

pg_session.close()

print()
print("="*80)
print("News Interpretation Creation Complete")
print("="*80)
print()
print("Next Steps:")
print("1. Wait 1h/1d/3d to track actual price movements")
print("2. Calculate NIA (News Interpretation Accuracy)")
print("3. Update Accountability Dashboard")
print("="*80)

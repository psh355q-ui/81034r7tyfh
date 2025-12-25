"""
Dividend Data Collector - 배당 데이터 수집기

Phase 21: Dividend Intelligence Module - Step 1.2
Date: 2025-12-25

Features:
- TTM (Trailing Twelve Months) Yield 직접 계산 (yfinance info 의존 금지)
- Redis 캐싱 (TTL 24시간)
- 배당 주기 자동 감지 (월/분기/연)
- 배당락일 T-3 알림
"""

import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import redis
import json
import logging
import os
import asyncpg
from decimal import Decimal

logger = logging.getLogger(__name__)


class DividendCollector:
    """배당 데이터 수집 (Redis 캐싱)"""
    
    def __init__(self):
        # Redis 연결
        redis_host = os.getenv('REDIS_HOST', 'localhost')
        redis_port = int(os.getenv('REDIS_PORT', 6379))
        
        try:
            self.redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=0,
                decode_responses=True
            )
            # 연결 테스트
            self.redis_client.ping()
            logger.info(f"✅ Redis connected: {redis_host}:{redis_port}")
        except Exception as e:
            logger.warning(f"⚠️ Redis connection failed: {e}. Caching disabled.")
            self.redis_client = None
        
        # 캐시 TTL (24시간)
        self.CACHE_TTL = 86400
        
        # DB 설정
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 5432)),
            'database': os.getenv('DB_NAME', 'trading_db'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', '')
        }
    
    async def calculate_ttm_yield(self, ticker: str) -> Dict:
        """
        TTM (Trailing Twelve Months) Yield 직접 계산
        
        yfinance info['dividendYield'] 사용 금지!
        실제 배당금 데이터로부터 직접 계산
        
        Args:
            ticker: 종목 코드 (예: "JNJ", "SCHD")
        
        Returns:
            {
                "ticker": "JNJ",
                "ttm_dividends": 4.52,      # 최근 12개월 배당금 합계 (USD)
                "current_price": 158.32,     # 현재 주가 (USD)
                "ttm_yield": 2.85,           # TTM 배당률 (%)
                "payment_count": 4,          # 배당 횟수
                "calculated_at": "2025-12-25T11:15:00"
            }
        """
        
        # 1. Redis 캐시 확인
        cache_key = f"ttm_yield:{ticker}"
        if self.redis_client:
            cached = self.redis_client.get(cache_key)
            if cached:
                logger.info(f"📦 Cache hit: {ticker}")
                return json.loads(cached)
        
        try:
            logger.info(f"🔍 Fetching dividend data: {ticker}")
            stock = yf.Ticker(ticker)
            
            # 2. 최근 12개월 배당금 직접 합산
            dividends = stock.dividends
            
            if dividends.empty:
                logger.warning(f"⚠️ No dividend data for {ticker}")
                return {
                    "ticker": ticker,
                    "ttm_dividends": 0.0,
                    "current_price": 0.0,
                    "ttm_yield": 0.0,
                    "payment_count": 0,
                    "calculated_at": datetime.now().isoformat(),
                    "error": "No dividend history"
                }
            
            # 최근 12개월 데이터
            one_year_ago = datetime.now() - timedelta(days=365)
            recent_dividends = dividends[dividends.index >= one_year_ago]
            
            ttm_dividends = float(recent_dividends.sum())
            payment_count = len(recent_dividends)
            
            # 3. 현재 주가 조회
            try:
                current_price = float(stock.info.get('currentPrice', 0))
                if current_price == 0:
                    # currentPrice가 없으면 history에서 가져오기
                    hist = stock.history(period='1d')
                    if not hist.empty:
                        current_price = float(hist['Close'].iloc[-1])
            except Exception as e:
                logger.error(f"Failed to get price for {ticker}: {e}")
                current_price = 0
            
            # 4. TTM Yield 계산
            ttm_yield = 0.0
            if current_price > 0 and ttm_dividends > 0:
                ttm_yield = (ttm_dividends / current_price) * 100
            
            result = {
                "ticker": ticker,
                "ttm_dividends": round(ttm_dividends, 4),
                "current_price": round(current_price, 2),
                "ttm_yield": round(ttm_yield, 2),
                "payment_count": payment_count,
                "calculated_at": datetime.now().isoformat()
            }
            
            # 5. Redis 캐시 저장
            if self.redis_client:
                self.redis_client.setex(
                    cache_key,
                    self.CACHE_TTL,
                    json.dumps(result)
                )
                logger.info(f"💾 Cached: {ticker} (TTL: {self.CACHE_TTL}s)")
            
            logger.info(f"✅ {ticker}: ${ttm_dividends:.2f} / ${current_price:.2f} = {ttm_yield:.2f}%")
            return result
        
        except Exception as e:
            logger.error(f"❌ Error calculating TTM yield for {ticker}: {e}")
            return {
                "ticker": ticker,
                "ttm_dividends": 0.0,
                "current_price": 0.0,
                "ttm_yield": 0.0,
                "payment_count": 0,
                "calculated_at": datetime.now().isoformat(),
                "error": str(e)
            }
    
    async def detect_payment_frequency(self, ticker: str) -> str:
        """
        배당 주기 자동 감지 (월/분기/연)
        
        Args:
            ticker: 종목 코드
        
        Returns:
            "Monthly" | "Quarterly" | "Annual" | "None"
        """
        
        try:
            stock = yf.Ticker(ticker)
            dividends = stock.dividends
            
            if dividends.empty:
                return "None"
            
            # 최근 12개월 배당 횟수
            one_year_ago = datetime.now() - timedelta(days=365)
            recent = dividends[dividends.index >= one_year_ago]
            payment_count = len(recent)
            
            # 주기 판단
            if payment_count >= 12:
                return "Monthly"
            elif payment_count >= 4:
                return "Quarterly"
            elif payment_count >= 1:
                return "Annual"
            else:
                return "None"
        
        except Exception as e:
            logger.error(f"Failed to detect frequency for {ticker}: {e}")
            return "Unknown"
    
    async def get_upcoming_ex_dates(self, days: int = 3) -> List[Dict]:
        """
        배당락일 T-3 알림 데이터
        
        DB에서 ex_dividend_date가 today + days 이내인 종목 조회
        
        Args:
            days: 며칠 앞까지 조회할지 (기본 3일)
        
        Returns:
            [
                {
                    "ticker": "JNJ",
                    "ex_dividend_date": "2025-12-28",
                    "payment_date": "2026-01-15",
                    "amount": 1.19,
                    "days_until": 3
                },
                ...
            ]
        """
        
        try:
            conn = await asyncpg.connect(**self.db_config)
            
            today = datetime.now().date()
            target_date = today + timedelta(days=days)
            
            query = """
                SELECT 
                    ticker,
                    ex_dividend_date,
                    payment_date,
                    amount,
                    ex_dividend_date - CURRENT_DATE as days_until
                FROM dividend_history
                WHERE ex_dividend_date BETWEEN CURRENT_DATE AND $1
                ORDER BY ex_dividend_date, ticker
            """
            
            rows = await conn.fetch(query, target_date)
            
            upcoming = []
            for row in rows:
                upcoming.append({
                    "ticker": row['ticker'],
                    "ex_dividend_date": row['ex_dividend_date'].isoformat(),
                    "payment_date": row['payment_date'].isoformat() if row['payment_date'] else None,
                    "amount": float(row['amount']),
                    "days_until": row['days_until']
                })
            
            await conn.close()
            
            logger.info(f"📅 Found {len(upcoming)} upcoming ex-dividend dates")
            return upcoming
        
        except Exception as e:
            logger.error(f"Failed to get upcoming ex-dates: {e}")
            return []
    
    async def save_dividend_history(self, ticker: str) -> int:
        """
        yfinance에서 배당 이력을 가져와서 DB에 저장
        
        Args:
            ticker: 종목 코드
        
        Returns:
            저장된 레코드 수
        """
        
        try:
            stock = yf.Ticker(ticker)
            dividends = stock.dividends
            
            if dividends.empty:
                logger.warning(f"No dividend data for {ticker}")
                return 0
            
            # 배당 주기 자동 감지
            frequency = await self.detect_payment_frequency(ticker)
            
            conn = await asyncpg.connect(**self.db_config)
            
            saved_count = 0
            for date, amount in dividends.items():
                # 중복 체크 & INSERT
                insert_query = """
                    INSERT INTO dividend_history 
                        (ticker, ex_dividend_date, amount, frequency)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (ticker, ex_dividend_date) 
                    DO UPDATE SET 
                        amount = $3,
                        frequency = $4,
                        updated_at = CURRENT_TIMESTAMP
                """
                
                await conn.execute(
                    insert_query,
                    ticker,
                    date.date(),
                    Decimal(str(amount)),
                    frequency
                )
                saved_count += 1
            
            await conn.close()
            
            logger.info(f"✅ Saved {saved_count} dividend records for {ticker}")
            return saved_count
        
        except Exception as e:
            logger.error(f"Failed to save dividend history for {ticker}: {e}")
            return 0
    
    async def bulk_collect(self, tickers: List[str]) -> Dict:
        """
        여러 종목의 배당 데이터 일괄 수집
        
        Args:
            tickers: 종목 코드 리스트
        
        Returns:
            {
                "total": 10,
                "success": 8,
                "failed": 2,
                "results": [...]
            }
        """
        
        results = []
        success_count = 0
        
        for ticker in tickers:
            try:
                # TTM Yield 계산
                ttm_data = await self.calculate_ttm_yield(ticker)
                
                # DB 저장
                saved = await self.save_dividend_history(ticker)
                
                results.append({
                    "ticker": ticker,
                    "status": "success",
                    "ttm_yield": ttm_data.get('ttm_yield', 0),
                    "records_saved": saved
                })
                
                success_count += 1
                
            except Exception as e:
                logger.error(f"Failed to collect {ticker}: {e}")
                results.append({
                    "ticker": ticker,
                    "status": "failed",
                    "error": str(e)
                })
        
        return {
            "total": len(tickers),
            "success": success_count,
            "failed": len(tickers) - success_count,
            "results": results
        }


# CLI 실행
async def main():
    """테스트 실행"""
    
    collector = DividendCollector()
    
    print("=" * 60)
    print("Dividend Collector Test")
    print("=" * 60)
    print()
    
    # 테스트 종목
    test_tickers = ["JNJ", "PG", "KO", "SCHD"]
    
    for ticker in test_tickers:
        print(f"\n📊 Testing: {ticker}")
        print("-" * 60)
        
        # TTM Yield 계산
        ttm = await collector.calculate_ttm_yield(ticker)
        print(f"TTM Dividends: ${ttm['ttm_dividends']}")
        print(f"Current Price: ${ttm['current_price']}")
        print(f"TTM Yield: {ttm['ttm_yield']}%")
        print(f"Payment Count: {ttm['payment_count']}")
        
        # 배당 주기
        frequency = await collector.detect_payment_frequency(ticker)
        print(f"Frequency: {frequency}")
        
        # DB 저장
        saved = await collector.save_dividend_history(ticker)
        print(f"Saved Records: {saved}")
    
    print("\n" + "=" * 60)
    print("✅ Test completed")
    print("=" * 60)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

"""
AI Trading System Metrics Collector

Phase 14-16 메트릭 수집 및 Prometheus 통합

Metrics:
- ai_trading_news_articles_crawled_total
- ai_trading_signals_generated_total
- ai_trading_signals_by_type{type="PRIMARY|HIDDEN|LOSER"}
- ai_trading_signals_by_ticker{ticker="NVDA|AMD|..."}
- ai_trading_gemini_api_calls_total
- ai_trading_api_cost_usd_total
- ai_trading_hidden_beneficiary_hit_rate
- ai_trading_analysis_duration_seconds
"""

from prometheus_client import Counter, Gauge, Histogram, Info
from typing import Dict, Optional
from datetime import datetime
import asyncio


# ============================================
# Prometheus Metrics Definitions
# ============================================

# News Crawling Metrics
news_articles_crawled = Counter(
    'ai_trading_news_articles_crawled_total',
    'Total number of news articles crawled',
    ['source']  # TechCrunch, Reuters, etc.
)

news_articles_relevant = Counter(
    'ai_trading_news_articles_relevant_total',
    'Number of relevant articles (passed keyword filter)'
)

# Signal Generation Metrics
signals_generated = Counter(
    'ai_trading_signals_generated_total',
    'Total trading signals generated'
)

signals_by_type = Counter(
    'ai_trading_signals_by_type',
    'Signals broken down by type',
    ['type']  # PRIMARY, HIDDEN, LOSER
)

signals_by_ticker = Counter(
    'ai_trading_signals_by_ticker',
    'Signals broken down by ticker',
    ['ticker', 'action']  # ticker=NVDA, action=BUY
)

signals_high_confidence = Counter(
    'ai_trading_signals_high_confidence_total',
    'Signals with >85% confidence'
)

# Hidden Beneficiary Metrics
hidden_beneficiaries_found = Counter(
    'ai_trading_hidden_beneficiaries_found_total',
    'Total hidden beneficiaries discovered'
)

hidden_beneficiary_hit_rate = Gauge(
    'ai_trading_hidden_beneficiary_hit_rate',
    'Percentage of analyses that found hidden beneficiaries'
)

# API Call Metrics
gemini_api_calls = Counter(
    'ai_trading_gemini_api_calls_total',
    'Total Gemini API calls',
    ['model']  # gemini-2.5-pro, gemini-2.5-flash
)

api_cost_usd = Gauge(
    'ai_trading_api_cost_usd_total',
    'Total API cost in USD'
)

daily_api_cost = Gauge(
    'ai_trading_api_cost_daily_usd',
    'Daily API cost in USD'
)

# Performance Metrics
analysis_duration = Histogram(
    'ai_trading_analysis_duration_seconds',
    'Time taken for Deep Reasoning analysis',
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
)

crawl_cycle_duration = Histogram(
    'ai_trading_crawl_cycle_duration_seconds',
    'Time taken for full crawl cycle',
    buckets=[5.0, 10.0, 20.0, 30.0, 60.0, 120.0]
)

# System Info
system_info = Info(
    'ai_trading_system_info',
    'AI Trading System information'
)


# ============================================
# Metrics Tracker Class
# ============================================

class AITradingMetrics:
    """
    AI Trading 시스템 메트릭 추적 및 수집

    Usage:
        metrics = AITradingMetrics()
        metrics.record_article_crawled("TechCrunch")
        metrics.record_signal("NVDA", "BUY", "HIDDEN", 0.90)
        metrics.record_api_call("gemini-2.5-pro", cost_usd=0.007)
    """

    def __init__(self):
        self.total_analyses = 0
        self.hidden_found_count = 0
        self.cumulative_cost = 0.0
        self.daily_cost = 0.0
        self.last_reset_date = datetime.now().date()

        # Initialize system info
        system_info.info({
            'version': '1.1.0',
            'phase': 'Phase 14-16',
            'features': 'Deep Reasoning, RAG, RSS Crawling'
        })

    def record_article_crawled(self, source: str):
        """뉴스 기사 크롤링 기록"""
        news_articles_crawled.labels(source=source).inc()

    def record_article_relevant(self):
        """관련 기사 필터링 통과"""
        news_articles_relevant.inc()

    def record_signal(
        self,
        ticker: str,
        action: str,
        signal_type: str,
        confidence: float
    ):
        """
        Trading signal 기록

        Args:
            ticker: 종목 코드 (NVDA, AMD, etc.)
            action: BUY, SELL, TRIM, HOLD
            signal_type: PRIMARY, HIDDEN, LOSER
            confidence: 신뢰도 (0.0-1.0)
        """
        # 총 시그널
        signals_generated.inc()

        # 타입별
        signals_by_type.labels(type=signal_type).inc()

        # 티커별
        signals_by_ticker.labels(ticker=ticker, action=action).inc()

        # High confidence
        if confidence > 0.85:
            signals_high_confidence.inc()

        # Hidden beneficiary tracking
        if signal_type == "HIDDEN":
            hidden_beneficiaries_found.inc()
            self.hidden_found_count += 1

    def record_analysis_complete(self, duration_seconds: float, found_hidden: bool):
        """
        분석 완료 기록

        Args:
            duration_seconds: 분석 소요 시간
            found_hidden: Hidden beneficiary 발견 여부
        """
        self.total_analyses += 1

        # Duration histogram
        analysis_duration.observe(duration_seconds)

        # Hit rate 계산
        if self.total_analyses > 0:
            hit_rate = (self.hidden_found_count / self.total_analyses) * 100
            hidden_beneficiary_hit_rate.set(hit_rate)

    def record_api_call(self, model: str, cost_usd: float):
        """
        API 호출 기록

        Args:
            model: gemini-2.5-pro, gemini-2.5-flash, etc.
            cost_usd: 호출 비용 (USD)
        """
        gemini_api_calls.labels(model=model).inc()

        # Cost tracking
        self.cumulative_cost += cost_usd
        api_cost_usd.set(self.cumulative_cost)

        # Daily cost (자정에 리셋)
        today = datetime.now().date()
        if today != self.last_reset_date:
            self.daily_cost = 0.0
            self.last_reset_date = today

        self.daily_cost += cost_usd
        daily_api_cost.set(self.daily_cost)

    def record_crawl_cycle(self, duration_seconds: float, articles_found: int):
        """
        크롤링 사이클 기록

        Args:
            duration_seconds: 사이클 소요 시간
            articles_found: 발견한 기사 수
        """
        crawl_cycle_duration.observe(duration_seconds)

    def get_stats(self) -> Dict:
        """현재 통계 반환"""
        return {
            'total_analyses': self.total_analyses,
            'hidden_found': self.hidden_found_count,
            'hidden_hit_rate': (
                (self.hidden_found_count / self.total_analyses * 100)
                if self.total_analyses > 0
                else 0.0
            ),
            'cumulative_cost_usd': self.cumulative_cost,
            'daily_cost_usd': self.daily_cost,
        }


# ============================================
# Global Metrics Instance
# ============================================

# 싱글톤 인스턴스
_metrics_instance: Optional[AITradingMetrics] = None


def get_metrics() -> AITradingMetrics:
    """Global metrics instance 가져오기"""
    global _metrics_instance
    if _metrics_instance is None:
        _metrics_instance = AITradingMetrics()
    return _metrics_instance


# ============================================
# Context Managers for Timing
# ============================================

class AnalysisTimer:
    """Deep Reasoning 분석 시간 측정 컨텍스트 매니저"""

    def __init__(self, metrics: AITradingMetrics):
        self.metrics = metrics
        self.start_time = None
        self.found_hidden = False

    def __enter__(self):
        self.start_time = asyncio.get_event_loop().time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = asyncio.get_event_loop().time() - self.start_time
        self.metrics.record_analysis_complete(duration, self.found_hidden)

    def set_found_hidden(self, found: bool):
        """Hidden beneficiary 발견 여부 설정"""
        self.found_hidden = found


class CrawlCycleTimer:
    """RSS 크롤링 사이클 시간 측정 컨텍스트 매니저"""

    def __init__(self, metrics: AITradingMetrics):
        self.metrics = metrics
        self.start_time = None
        self.articles_found = 0

    def __enter__(self):
        self.start_time = asyncio.get_event_loop().time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = asyncio.get_event_loop().time() - self.start_time
        self.metrics.record_crawl_cycle(duration, self.articles_found)

    def set_articles_found(self, count: int):
        """발견한 기사 수 설정"""
        self.articles_found = count


# ============================================
# Demo & Testing
# ============================================

def demo():
    """메트릭 수집 데모"""
    print("=" * 80)
    print("AI Trading Metrics Demo")
    print("=" * 80)

    metrics = get_metrics()

    # 뉴스 크롤링 시뮬레이션
    print("\n[1] Simulating news crawling...")
    metrics.record_article_crawled("TechCrunch")
    metrics.record_article_crawled("Reuters")
    metrics.record_article_crawled("Bloomberg")
    metrics.record_article_relevant()
    metrics.record_article_relevant()

    # 시그널 생성 시뮬레이션
    print("\n[2] Simulating signal generation...")
    metrics.record_signal("NVDA", "BUY", "PRIMARY", 0.95)
    metrics.record_signal("SMCI", "BUY", "HIDDEN", 0.85)
    metrics.record_signal("AMD", "TRIM", "LOSER", 0.70)

    # 분석 완료 시뮬레이션
    print("\n[3] Simulating analysis completion...")
    metrics.record_analysis_complete(2.5, found_hidden=True)
    metrics.record_analysis_complete(3.1, found_hidden=False)
    metrics.record_analysis_complete(2.8, found_hidden=True)

    # API 호출 시뮬레이션
    print("\n[4] Simulating API calls...")
    metrics.record_api_call("gemini-2.5-pro", 0.007)
    metrics.record_api_call("gemini-2.5-pro", 0.007)
    metrics.record_api_call("gemini-2.5-flash", 0.0003)

    # 크롤링 사이클 시뮬레이션
    print("\n[5] Simulating crawl cycle...")
    metrics.record_crawl_cycle(18.5, 3)

    # 통계 출력
    print("\n" + "=" * 80)
    print("METRICS STATS")
    print("=" * 80)
    stats = metrics.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    print("\n" + "=" * 80)
    print("Metrics are now available at /metrics endpoint")
    print("=" * 80)


if __name__ == "__main__":
    demo()

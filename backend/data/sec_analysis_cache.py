"""
SEC 분석 결과 캐싱

분석 비용 절감을 위한 캐싱 시스템

Author: AI Trading System
Date: 2025-11-22
"""

import json
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging

from backend.core.models.sec_analysis_models import (
    SECAnalysisResult,
    SECAnalysisCache,
    RiskFactor,
    RedFlag,
    FinancialTrend,
    ManagementTone,
    RiskLevel,
    SentimentTone,
    RedFlagType
)

logger = logging.getLogger(__name__)


class SECAnalysisCache:
    """
    SEC 분석 결과 캐시 관리
    
    Features:
    - 파일 기반 캐시 (JSON)
    - 90일 TTL (10-K/10-Q는 분기마다만 업데이트)
    - 캐시 키: ticker + filing_type + fiscal_period
    """
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Args:
            cache_dir: 캐시 디렉토리 (기본: data/sec_analysis_cache)
        """
        self.cache_dir = cache_dir or Path("data/sec_analysis_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"SEC Analysis Cache initialized: {self.cache_dir}")
    
    def _get_cache_key(
        self,
        ticker: str,
        filing_type: str,
        fiscal_period: str
    ) -> str:
        """
        캐시 키 생성
        
        Args:
            ticker: 주식 티커
            filing_type: 공시 유형 (10-K, 10-Q)
            fiscal_period: 회계 기간 (FY2024, Q3 2024 등)
            
        Returns:
            캐시 키 (MD5 해시)
        """
        key_str = f"{ticker}_{filing_type}_{fiscal_period}".upper()
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _get_cache_file(self, cache_key: str) -> Path:
        """캐시 파일 경로"""
        return self.cache_dir / f"{cache_key}.json"
    
    def get(
        self,
        ticker: str,
        filing_type: str,
        fiscal_period: str
    ) -> Optional[SECAnalysisResult]:
        """
        캐시에서 분석 결과 조회
        
        Args:
            ticker: 주식 티커
            filing_type: 공시 유형
            fiscal_period: 회계 기간
            
        Returns:
            SECAnalysisResult 또는 None (캐시 없음/만료)
        """
        cache_key = self._get_cache_key(ticker, filing_type, fiscal_period)
        cache_file = self._get_cache_file(cache_key)
        
        if not cache_file.exists():
            logger.debug(f"Cache miss: {ticker} {filing_type} {fiscal_period}")
            return None
        
        try:
            # 캐시 파일 읽기
            with open(cache_file, 'r') as f:
                data = json.load(f)
            
            # 만료 확인
            cached_at = datetime.fromisoformat(data["cached_at"])
            ttl_days = data.get("ttl_days", 90)
            
            if datetime.now() > cached_at + timedelta(days=ttl_days):
                logger.debug(f"Cache expired: {ticker} {filing_type} {fiscal_period}")
                cache_file.unlink()  # 삭제
                return None
            
            # 분석 결과 복원
            result = self._deserialize_result(data["analysis"])
            
            logger.info(
                f"Cache hit: {ticker} {filing_type} {fiscal_period} "
                f"(cached {(datetime.now() - cached_at).days} days ago)"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to load cache: {e}")
            return None
    
    def set(
        self,
        result: SECAnalysisResult,
        ttl_days: int = 90
    ):
        """
        분석 결과 캐시 저장
        
        Args:
            result: 분석 결과
            ttl_days: 캐시 유효 기간 (기본 90일)
        """
        cache_key = self._get_cache_key(
            result.ticker,
            result.filing_type,
            result.fiscal_period
        )
        cache_file = self._get_cache_file(cache_key)
        
        try:
            # 캐시 데이터 생성
            cache_data = {
                "cache_key": cache_key,
                "ticker": result.ticker,
                "filing_type": result.filing_type,
                "fiscal_period": result.fiscal_period,
                "cached_at": datetime.now().isoformat(),
                "ttl_days": ttl_days,
                "analysis": self._serialize_result(result)
            }
            
            # 파일 저장
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
            
            logger.info(f"Cached: {result.ticker} {result.filing_type} {result.fiscal_period}")
            
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")
    
    def invalidate(
        self,
        ticker: str,
        filing_type: str,
        fiscal_period: str
    ):
        """
        캐시 무효화 (삭제)
        
        Args:
            ticker: 주식 티커
            filing_type: 공시 유형
            fiscal_period: 회계 기간
        """
        cache_key = self._get_cache_key(ticker, filing_type, fiscal_period)
        cache_file = self._get_cache_file(cache_key)
        
        if cache_file.exists():
            cache_file.unlink()
            logger.info(f"Cache invalidated: {ticker} {filing_type} {fiscal_period}")
    
    def clear_all(self):
        """모든 캐시 삭제"""
        count = 0
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()
            count += 1
        
        logger.info(f"Cleared {count} cache files")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """캐시 통계"""
        cache_files = list(self.cache_dir.glob("*.json"))
        
        total_size = sum(f.stat().st_size for f in cache_files)
        
        return {
            "total_files": len(cache_files),
            "total_size_mb": total_size / (1024 * 1024),
            "cache_dir": str(self.cache_dir)
        }
    
    def _serialize_result(self, result: SECAnalysisResult) -> Dict[str, Any]:
        """SECAnalysisResult → JSON 딕셔너리"""
        return {
            "ticker": result.ticker,
            "filing_type": result.filing_type,
            "fiscal_period": result.fiscal_period,
            "analysis_date": result.analysis_date.isoformat(),
            "overall_risk_level": result.overall_risk_level.value,
            "overall_risk_score": result.overall_risk_score,
            "investment_signal": result.investment_signal,
            "risk_factors": [
                {
                    "category": rf.category,
                    "title": rf.title,
                    "description": rf.description,
                    "severity": rf.severity.value,
                    "impact_score": rf.impact_score,
                    "likelihood_score": rf.likelihood_score,
                    "is_new": rf.is_new
                }
                for rf in result.risk_factors
            ],
            "red_flags": [
                {
                    "flag_type": rf.flag_type.value,
                    "severity": rf.severity.value,
                    "description": rf.description,
                    "detected_in_section": rf.detected_in_section,
                    "quotes": rf.quotes,
                    "action_required": rf.action_required
                }
                for rf in result.red_flags
            ],
            "financial_trends": [
                {
                    "metric": ft.metric,
                    "current_value": ft.current_value,
                    "prior_value": ft.prior_value,
                    "change_percent": ft.change_percent,
                    "trend": ft.trend,
                    "interpretation": ft.interpretation
                }
                for ft in result.financial_trends
            ],
            "management_tone": {
                "overall_sentiment": result.management_tone.overall_sentiment.value,
                "sentiment_score": result.management_tone.sentiment_score,
                "confidence_level": result.management_tone.confidence_level,
                "key_phrases": result.management_tone.key_phrases,
                "tone_change_vs_prior": result.management_tone.tone_change_vs_prior,
                "concerns_mentioned": result.management_tone.concerns_mentioned,
                "opportunities_mentioned": result.management_tone.opportunities_mentioned
            } if result.management_tone else None,
            "executive_summary": result.executive_summary,
            "key_takeaways": result.key_takeaways,
            "model_used": result.model_used,
            "tokens_used": result.tokens_used,
            "analysis_cost": result.analysis_cost,
            "confidence_score": result.confidence_score
        }
    
    def _deserialize_result(self, data: Dict[str, Any]) -> SECAnalysisResult:
        """JSON 딕셔너리 → SECAnalysisResult"""
        # Risk Factors
        risk_factors = [
            RiskFactor(
                category=rf["category"],
                title=rf["title"],
                description=rf["description"],
                severity=RiskLevel(rf["severity"]),
                impact_score=rf["impact_score"],
                likelihood_score=rf["likelihood_score"],
                is_new=rf.get("is_new", False)
            )
            for rf in data.get("risk_factors", [])
        ]
        
        # Red Flags
        red_flags = [
            RedFlag(
                flag_type=RedFlagType(rf["flag_type"]),
                severity=RiskLevel(rf["severity"]),
                description=rf["description"],
                detected_in_section=rf["detected_in_section"],
                quotes=rf.get("quotes", []),
                action_required=rf.get("action_required", False)
            )
            for rf in data.get("red_flags", [])
        ]
        
        # Financial Trends
        financial_trends = [
            FinancialTrend(
                metric=ft["metric"],
                current_value=ft.get("current_value"),
                prior_value=ft.get("prior_value"),
                change_percent=ft.get("change_percent"),
                trend=ft["trend"],
                interpretation=ft["interpretation"]
            )
            for ft in data.get("financial_trends", [])
        ]
        
        # Management Tone
        management_tone = None
        if data.get("management_tone"):
            mt = data["management_tone"]
            management_tone = ManagementTone(
                overall_sentiment=SentimentTone(mt["overall_sentiment"]),
                sentiment_score=mt["sentiment_score"],
                confidence_level=mt["confidence_level"],
                key_phrases=mt.get("key_phrases", []),
                tone_change_vs_prior=mt.get("tone_change_vs_prior"),
                concerns_mentioned=mt.get("concerns_mentioned", []),
                opportunities_mentioned=mt.get("opportunities_mentioned", [])
            )
        
        # 결과 생성
        return SECAnalysisResult(
            ticker=data["ticker"],
            filing_type=data["filing_type"],
            fiscal_period=data["fiscal_period"],
            analysis_date=datetime.fromisoformat(data["analysis_date"]),
            overall_risk_level=RiskLevel(data["overall_risk_level"]),
            overall_risk_score=data["overall_risk_score"],
            investment_signal=data["investment_signal"],
            risk_factors=risk_factors,
            red_flags=red_flags,
            financial_trends=financial_trends,
            management_tone=management_tone,
            executive_summary=data["executive_summary"],
            key_takeaways=data["key_takeaways"],
            model_used=data["model_used"],
            tokens_used=data["tokens_used"],
            analysis_cost=data["analysis_cost"],
            confidence_score=data["confidence_score"]
        )


# ============================================
# 캐싱 래퍼 (Analyzer 통합용)
# ============================================

class CachedSECAnalyzer:
    """
    캐싱 기능이 통합된 SEC Analyzer
    
    자동으로 캐시를 확인하고, 없으면 분석 후 캐시 저장
    """
    
    def __init__(
        self,
        analyzer,  # SECAnalyzer 인스턴스
        cache: Optional[SECAnalysisCache] = None
    ):
        """
        Args:
            analyzer: SECAnalyzer 인스턴스
            cache: SECAnalysisCache 인스턴스 (선택)
        """
        self.analyzer = analyzer
        self.cache = cache or SECAnalysisCache()
    
    async def analyze_ticker(
        self,
        request  # SECAnalysisRequest
    ) -> SECAnalysisResult:
        """
        캐싱 기능이 통합된 분석
        
        1. 캐시 확인
        2. 있으면 반환
        3. 없으면 분석 후 캐시 저장
        """
        # force_refresh면 캐시 무시
        if not request.force_refresh:
            # 캐시 확인 (fiscal_period는 아직 모름)
            # 일단 최신 공시 조회 필요
            pass
        
        # 분석 실행
        result = await self.analyzer.analyze_ticker(request)
        
        # 캐시 저장
        self.cache.set(result)
        
        return result


# ============================================
# 테스트
# ============================================

if __name__ == "__main__":
    from backend.core.models.sec_analysis_models import SECAnalysisResult
    
    # 샘플 결과 생성
    sample_result = SECAnalysisResult(
        ticker="AAPL",
        filing_type="10-K",
        fiscal_period="FY2024",
        overall_risk_level=RiskLevel.MEDIUM,
        overall_risk_score=0.5,
        investment_signal="HOLD",
        executive_summary="Sample summary",
        key_takeaways=["Takeaway 1", "Takeaway 2"],
        model_used="claude-sonnet-4.5",
        tokens_used=10000,
        analysis_cost=0.05,
        confidence_score=0.85
    )
    
    # 캐시 테스트
    cache = SECAnalysisCache()
    
    print("=== Cache Test ===\n")
    
    # 저장
    cache.set(sample_result)
    print(f"✅ Saved to cache")
    
    # 조회
    cached = cache.get("AAPL", "10-K", "FY2024")
    if cached:
        print(f"✅ Retrieved from cache")
        print(f"   Risk: {cached.overall_risk_level.value}")
        print(f"   Signal: {cached.investment_signal}")
    
    # 통계
    stats = cache.get_cache_stats()
    print(f"\n📊 Cache Stats:")
    print(f"   Files: {stats['total_files']}")
    print(f"   Size: {stats['total_size_mb']:.2f} MB")

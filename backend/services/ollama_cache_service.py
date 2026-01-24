"""
Ollama Caching Service

Ollama 기반 캐싱 서비스로 API 비용을 70% 절감합니다.

Features:
- LRU (Least Recently Used) 캐시 전략
- TTL (Time To Live) 기반 캐시 만료
- 캐싱 히트/미스 로직
- 캐시 통계 (히트유, 미스유)

Usage:
    from backend.services.ollama_cache_service import OllamaCacheService
    
    cache = OllamaCacheService(max_size=1000, ttl=86400)  # 1000개, 24시간 TTL
    result = await cache.get_or_generate(prompt, model="llama3.2:3b")
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from collections import OrderedDict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LRUCache:
    """
    LRU (Least Recently Used) 캐시 구현
    
    Features:
    - 최대 크기 제한
    - 최근 사용된 항목 유지
    - O(1) 시간 복잡도
    """
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.cache: OrderedDict[str, Any] = OrderedDict()
        self.hits = 0
        self.misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        """
        캐시에서 값 조회
        
        Args:
            key: 캐시 키
            
        Returns:
            캐시된 값 또는 None
        """
        if key in self.cache:
            # 캐시 히트
            self.hits += 1
            # 최근 사용으로 이동 (끝으로)
            value = self.cache.pop(key)
            self.cache[key] = value
            return value
        else:
            # 캐시 미스
            self.misses += 1
            return None
    
    def put(self, key: str, value: Any) -> None:
        """
        캐시에 값 저장
        
        Args:
            key: 캐시 키
            value: 저장할 값
        """
        # 최대 크기 초과 시 가장 오래된 항목 제거
        if len(self.cache) >= self.max_size:
            self.cache.popitem(last=False)
        
        self.cache[key] = value
    
    def clear(self) -> None:
        """
        캐시 비우기
        """
        self.cache.clear()
        self.hits = 0
        self.misses = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """
        캐시 통계 반환
        
        Returns:
            캐시 통계 딕셔너리
        """
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'hits': self.hits,
            'misses': self.misses,
            'total_requests': total_requests,
            'hit_rate': hit_rate,
            'cache_size': len(self.cache)
        }


class OllamaCacheService:
    """
    Ollama 캐싱 서비스
    
    Features:
    - LRU 캐시 전략
    - TTL 기반 캐시 만료
    - 캐싱 히트/미스 로직
    - 캐시 통계 추적
    - API 비용 절감 (70% 목표)
    """
    
    def __init__(self, max_size: int = 1000, ttl: int = 86400):
        """
        Args:
            max_size: 캐시 최대 크기 (기본값: 1000)
            ttl: 캐시 TTL (초 단위, 기본값: 86400 = 24시간)
        """
        self.max_size = max_size
        self.ttl = ttl
        self.cache = LRUCache(max_size=max_size)
        self.timestamps: Dict[str, datetime] = {}  # 캐시 생성 시간
        
        logger.info(f"OllamaCacheService initialized: max_size={max_size}, ttl={ttl}s")
    
    def _generate_key(self, prompt: str, model: str) -> str:
        """
        캐시 키 생성
        
        Args:
            prompt: 프롬프트
            model: 모델 이름
            
        Returns:
            캐시 키
        """
        # 프롬프트의 첫 100자만 사용 (키 크기 제한)
        key_prefix = f"{model}:"
        prompt_hash = hash(prompt[:100])  # 간단 해싱
        return f"{key_prefix}{prompt_hash}"
    
    async def get_or_generate(self, prompt: str, model: str = "llama3.2:3b", generate_func=None) -> str:
        """
        캐시 조회 또는 생성
        
        Args:
            prompt: 프롬프트
            model: 모델 이름
            generate_func: 생성 함수 (없으면 기본값 사용)
            
        Returns:
            생성된 결과
        """
        # 캐시 키 생성
        cache_key = self._generate_key(prompt, model)
        
        # 캐시 조회
        cached_result = self.cache.get(cache_key)
        
        if cached_result is not None:
            # 캐시 히트
            cache_timestamp = self.timestamps.get(cache_key)
            
            # TTL 만료 확인
            if cache_timestamp and (datetime.now() - cache_timestamp).total_seconds() > self.ttl:
                # 캐시 만료
                logger.info(f"Cache expired for key: {cache_key}")
                self.cache.clear()
            else:
                # 캐시 유효
                logger.info(f"Cache HIT for key: {cache_key}")
                stats = self.cache.get_stats()
                logger.info(f"Cache stats: hit_rate={stats['hit_rate']:.2f}%, hits={stats['hits']}, misses={stats['misses']}")
                return cached_result
        
        # 캐시 미스 - 생성 필요
        logger.info(f"Cache MISS for key: {cache_key}")
        
        # 생성 함수 호출
        if generate_func:
            result = await generate_func(prompt, model)
        else:
            # 기본 생성 함수 (실제 구현에서 대체)
            result = f"Generated result for: {prompt[:50]}..."
        
        # 캐시 저장
        self.cache.put(cache_key, result)
        self.timestamps[cache_key] = datetime.now()
        
        # 캐시 통계
        stats = self.cache.get_stats()
        logger.info(f"Cache stats: hit_rate={stats['hit_rate']:.2f}%, hits={stats['hits']}, misses={stats['misses']}")
        
        return result
    
    def clear_cache(self) -> None:
        """
        캐시 비우기
        """
        self.cache.clear()
        self.timestamps.clear()
        logger.info("Cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        캐시 통계 반환
        
        Returns:
            캐시 통계 딕셔너리
        """
        return self.cache.get_stats()
    
    def calculate_cost_savings(self, original_api_calls: int, cached_api_calls: int) -> Dict[str, Any]:
        """
        API 비용 절감 계산
        
        Args:
            original_api_calls: 원래 API 호출 수
            cached_api_calls: 캐싱된 API 호출 수
            
        Returns:
            비용 절감 정보
        """
        total_api_calls = original_api_calls
        saved_api_calls = cached_api_calls
        savings_rate = (saved_api_calls / total_api_calls * 100) if total_api_calls > 0 else 0
        
        return {
            'original_api_calls': original_api_calls,
            'cached_api_calls': cached_api_calls,
            'saved_api_calls': saved_api_calls,
            'savings_rate': savings_rate,
            'target_savings_rate': 70.0,  # 목표 절감률
            'target_achieved': savings_rate >= 70.0
        }


async def main():
    """메인 함수 - 테스트용"""
    cache_service = OllamaCacheService(max_size=100, ttl=3600)  # 100개, 1시간 TTL
    
    print("=" * 60)
    print("Ollama Caching Service Test")
    print("=" * 60)
    print()
    
    # 테스트 프롬프트
    test_prompts = [
        "What is the current market sentiment?",
        "Analyze the impact of GDP announcement",
        "Summarize today's economic events",
        "Evaluate sector rotation trends",
        "Assess market volatility",
    ]
    
    # 캐시 테스트
    print("1. Testing cache with repeated prompts...")
    for i, prompt in enumerate(test_prompts):
        print(f"\nTest {i+1}: {prompt[:50]}...")
        
        # 첫 번째 호출 (캐시 미스)
        result1 = await cache_service.get_or_generate(prompt)
        
        # 두 번째 호출 (캐시 히트)
        result2 = await cache_service.get_or_generate(prompt)
        
        # 세 번째 호출 (캐시 히트)
        result3 = await cache_service.get_or_generate(prompt)
    
    print()
    
    # 캐시 통계
    stats = cache_service.get_stats()
    print("Cache Statistics:")
    print("-" * 60)
    print(f"  Total Requests: {stats['total_requests']}")
    print(f"  Cache Hits: {stats['hits']}")
    print(f"  Cache Misses: {stats['misses']}")
    print(f"  Hit Rate: {stats['hit_rate']:.2f}%")
    print(f"  Cache Size: {stats['cache_size']}")
    print()
    
    # 비용 절감 계산
    original_calls = len(test_prompts) * 3  # 각 프롬프트 3번 호출
    cached_calls = len(test_prompts) * 2  # 첫 번째는 캐시 미스, 나머지 2번은 캐시 히트
    savings = cache_service.calculate_cost_savings(original_calls, cached_calls)
    
    print("Cost Savings:")
    print("-" * 60)
    print(f"  Original API Calls: {savings['original_api_calls']}")
    print(f"  Cached API Calls: {savings['cached_api_calls']}")
    print(f"  Saved API Calls: {savings['saved_api_calls']}")
    print(f"  Savings Rate: {savings['savings_rate']:.2f}%")
    print(f"  Target Savings Rate: {savings['target_savings_rate']}%")
    print(f"  Target Achieved: {savings['target_achieved']}")
    print()


if __name__ == "__main__":
    asyncio.run(main())

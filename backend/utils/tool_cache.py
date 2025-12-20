"""
Tool Definition Caching System

토큰 비용 절감을 위한 도구 정의 캐싱 시스템

Features:
- 도구 정의 해시 기반 캐싱
- TTL 기반 자동 만료
- 캐시 히트/미스 통계
- OpenAI Prompt Caching 지원

Author: AI Trading System
Date: 2025-12-04
"""

import hashlib
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """캐시 항목"""
    cache_key: str
    tools: List[Dict[str, Any]]
    cached_at: datetime
    expires_at: datetime
    hit_count: int = 0
    last_accessed: Optional[datetime] = None


class ToolDefinitionCache:
    """
    도구 정의 캐싱 시스템

    매 API 요청마다 전송되는 도구 정의를 캐싱하여 토큰 절감

    Usage:
        cache = ToolDefinitionCache()
        cache_key = cache.cache_tools(tools)

        # 이후 요청
        cached_tools = cache.get_cached_tools(cache_key)
    """

    def __init__(self, ttl_hours: int = 24, max_cache_size: int = 100):
        """
        Args:
            ttl_hours: 캐시 유효 시간 (시간)
            max_cache_size: 최대 캐시 항목 수
        """
        self.ttl = timedelta(hours=ttl_hours)
        self.max_cache_size = max_cache_size
        self.cache: Dict[str, CacheEntry] = {}

        # 통계
        self.stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "total_cached": 0,
            "total_evicted": 0,
        }

        logger.info(f"ToolDefinitionCache initialized (ttl={ttl_hours}h, max_size={max_cache_size})")

    def get_or_create_cache_key(self, tools: List[Dict]) -> str:
        """
        도구 목록의 해시 생성

        Args:
            tools: 도구 정의 목록

        Returns:
            16자리 해시 문자열
        """
        # 도구를 정렬하여 순서에 무관하게 동일한 해시 생성
        tools_json = json.dumps(tools, sort_keys=True, ensure_ascii=False)
        hash_object = hashlib.sha256(tools_json.encode('utf-8'))
        cache_key = hash_object.hexdigest()[:16]

        return cache_key

    def cache_tools(self, tools: List[Dict]) -> str:
        """
        도구 정의 캐싱 및 캐시 키 반환

        Args:
            tools: 도구 정의 목록

        Returns:
            cache_key: 캐시 키 (16자리 해시)
        """
        if not tools:
            return ""

        cache_key = self.get_or_create_cache_key(tools)

        # 이미 캐시되어 있으면 반환
        if cache_key in self.cache:
            logger.debug(f"Tools already cached: {cache_key}")
            return cache_key

        # 캐시 크기 제한 확인
        if len(self.cache) >= self.max_cache_size:
            self._evict_oldest()

        # 캐싱
        now = datetime.now()
        entry = CacheEntry(
            cache_key=cache_key,
            tools=tools,
            cached_at=now,
            expires_at=now + self.ttl,
        )

        self.cache[cache_key] = entry
        self.stats["total_cached"] += 1

        logger.info(
            f"Tools cached: {cache_key} ({len(tools)} tools, "
            f"expires: {entry.expires_at.strftime('%Y-%m-%d %H:%M')})"
        )

        return cache_key

    def get_cached_tools(self, cache_key: str) -> Optional[List[Dict]]:
        """
        캐시된 도구 정의 조회

        Args:
            cache_key: 캐시 키

        Returns:
            도구 목록 (만료되었거나 없으면 None)
        """
        self.stats["total_requests"] += 1

        if not cache_key:
            self.stats["cache_misses"] += 1
            return None

        entry = self.cache.get(cache_key)

        if not entry:
            self.stats["cache_misses"] += 1
            logger.debug(f"Cache miss: {cache_key}")
            return None

        # 만료 체크
        if datetime.now() > entry.expires_at:
            del self.cache[cache_key]
            self.stats["cache_misses"] += 1
            logger.debug(f"Cache expired: {cache_key}")
            return None

        # 캐시 히트
        entry.hit_count += 1
        entry.last_accessed = datetime.now()
        self.stats["cache_hits"] += 1

        logger.debug(
            f"Cache hit: {cache_key} (hit_count={entry.hit_count}, "
            f"age={int((datetime.now() - entry.cached_at).total_seconds() / 60)}min)"
        )

        return entry.tools

    def is_cached(self, cache_key: str) -> bool:
        """캐시 존재 여부 확인 (만료 체크 포함)"""
        if not cache_key or cache_key not in self.cache:
            return False

        entry = self.cache[cache_key]
        return datetime.now() <= entry.expires_at

    def invalidate(self, cache_key: str) -> bool:
        """특정 캐시 무효화"""
        if cache_key in self.cache:
            del self.cache[cache_key]
            logger.info(f"Cache invalidated: {cache_key}")
            return True
        return False

    def clear_all(self):
        """모든 캐시 제거"""
        count = len(self.cache)
        self.cache.clear()
        logger.info(f"All caches cleared ({count} entries)")

    def cleanup_expired(self) -> int:
        """만료된 캐시 제거"""
        now = datetime.now()
        expired_keys = [
            key for key, entry in self.cache.items()
            if now > entry.expires_at
        ]

        for key in expired_keys:
            del self.cache[key]

        if expired_keys:
            logger.info(f"Expired caches removed: {len(expired_keys)}")

        return len(expired_keys)

    def _evict_oldest(self):
        """가장 오래된 캐시 항목 제거 (LRU)"""
        if not self.cache:
            return

        # last_accessed 기준으로 정렬 (없으면 cached_at 사용)
        oldest_key = min(
            self.cache.keys(),
            key=lambda k: self.cache[k].last_accessed or self.cache[k].cached_at
        )

        del self.cache[oldest_key]
        self.stats["total_evicted"] += 1
        logger.debug(f"Evicted oldest cache: {oldest_key}")

    def get_statistics(self) -> Dict[str, Any]:
        """캐시 통계 조회"""
        hit_rate = (
            self.stats["cache_hits"] / self.stats["total_requests"]
            if self.stats["total_requests"] > 0 else 0
        )

        return {
            **self.stats,
            "current_cache_size": len(self.cache),
            "hit_rate": hit_rate,
            "estimated_token_savings": self._estimate_token_savings(),
        }

    def _estimate_token_savings(self) -> int:
        """예상 토큰 절감량 계산"""
        # 가정: 도구 정의 평균 100토큰, 캐시 히트 시 90% 절감
        avg_tokens_per_tool = 100
        cache_reduction = 0.9

        total_tools = sum(len(entry.tools) for entry in self.cache.values())
        avg_tools = total_tools / len(self.cache) if self.cache else 0

        tokens_saved = int(
            self.stats["cache_hits"] * avg_tools * avg_tokens_per_tool * cache_reduction
        )

        return tokens_saved

    def get_cache_info(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """특정 캐시 정보 조회"""
        entry = self.cache.get(cache_key)
        if not entry:
            return None

        return {
            "cache_key": entry.cache_key,
            "tool_count": len(entry.tools),
            "cached_at": entry.cached_at.isoformat(),
            "expires_at": entry.expires_at.isoformat(),
            "hit_count": entry.hit_count,
            "last_accessed": entry.last_accessed.isoformat() if entry.last_accessed else None,
            "age_minutes": int((datetime.now() - entry.cached_at).total_seconds() / 60),
        }


# ============================================================================
# Global Cache Instance
# ============================================================================

_global_cache: Optional[ToolDefinitionCache] = None


def get_tool_cache() -> ToolDefinitionCache:
    """전역 캐시 인스턴스 가져오기"""
    global _global_cache

    if _global_cache is None:
        _global_cache = ToolDefinitionCache(ttl_hours=24, max_cache_size=100)
        logger.info("Global ToolDefinitionCache created")

    return _global_cache


def reset_tool_cache():
    """전역 캐시 리셋 (테스트용)"""
    global _global_cache
    _global_cache = None


# ============================================================================
# OpenAI Prompt Caching Support
# ============================================================================

class OpenAIPromptCacheHelper:
    """
    OpenAI Prompt Caching API 지원

    OpenAI는 시스템 메시지와 도구 정의를 자동으로 캐싱합니다.
    (2024년 10월 출시)
    """

    @staticmethod
    def prepare_messages_with_caching(
        system_message: str,
        user_messages: List[Dict],
        tools: List[Dict]
    ) -> tuple[List[Dict], List[Dict]]:
        """
        캐싱을 위한 메시지 구조화

        Args:
            system_message: 시스템 메시지
            user_messages: 사용자 메시지 목록
            tools: 도구 정의

        Returns:
            (messages, tools): 캐싱 최적화된 메시지와 도구
        """
        # 시스템 메시지를 첫 번째로 배치 (캐싱 대상)
        messages = [
            {
                "role": "system",
                "content": system_message,
            }
        ]

        # 사용자 메시지 추가
        messages.extend(user_messages)

        # 도구 정의는 그대로 반환 (OpenAI가 자동 캐싱)
        return messages, tools

    @staticmethod
    def estimate_cache_savings(
        total_tokens: int,
        is_cache_hit: bool = False
    ) -> Dict[str, Any]:
        """
        OpenAI 프롬프트 캐싱 절감액 추정

        Args:
            total_tokens: 전체 토큰 수
            is_cache_hit: 캐시 히트 여부

        Returns:
            절감 정보
        """
        # OpenAI Prompt Caching: 캐시 히트 시 50% 할인
        if is_cache_hit:
            original_cost = total_tokens
            cached_cost = total_tokens * 0.5
            savings = original_cost - cached_cost

            return {
                "original_tokens": original_cost,
                "cached_tokens": cached_cost,
                "tokens_saved": savings,
                "savings_rate": 0.5,
            }
        else:
            return {
                "original_tokens": total_tokens,
                "cached_tokens": total_tokens,
                "tokens_saved": 0,
                "savings_rate": 0.0,
            }

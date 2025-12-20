"""
Four Signal Calculator
뉴스 클러스터 신뢰도를 4가지 신호로 평가
"""
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import statistics
import logging

from .text_similarity import average_similarity

logger = logging.getLogger(__name__)


@dataclass
class FourSignals:
    """4개 신호 결과"""
    DI: float  # Diversity Integrity (0.0 ~ 1.0)
    TN: float  # Temporal Naturalness (0.0 ~ 1.0)
    NI: float  # Narrative Independence (0.0 ~ 1.0)
    EL: float  # Event Legitimacy (0.0 ~ 1.0)
    
    @property
    def overall_score(self) -> float:
        """전체 점수 (평균)"""
        return (self.DI + self.TN + self.NI + self.EL) / 4.0
    
    def to_dict(self) -> Dict[str, float]:
        """딕셔너리 변환"""
        return {
            'DI': self.DI,
            'TN': self.TN,
            'NI': self.NI,
            'EL': self.EL,
            'overall_score': self.overall_score
        }


class FourSignalCalculator:
    """
    Four Signal Calculator
    
    뉴스 클러스터의 신뢰도를 4가지 관점에서 평가:
    1. DI (Diversity Integrity): 출처 다양성
    2. TN (Temporal Naturalness): 시간적 자연스러움
    3. NI (Narrative Independence): 내러티브 독립성
    4. EL (Event Legitimacy): 이벤트 정당성
    """
    
    # 출처 신뢰도 가중치 (source_credibility 테이블과 동일)
    SOURCE_WEIGHTS = {
        # Tier 1
        'Bloomberg': 2.0,
        'Reuters': 2.0,
        'WSJ': 2.0,
        'Wall Street Journal': 2.0,
        'Financial Times': 2.0,
        'SEC Filing': 2.5,
        
        # Tier 2
        'CNBC': 1.5,
        'Yahoo Finance': 1.3,
        'MarketWatch': 1.4,
        '연합뉴스': 1.3,
        'Yonhap': 1.3,
    }
    
    def __init__(self, source_credibility_map: Optional[Dict[str, float]] = None):
        """
        Args:
            source_credibility_map: 출처별 신뢰도 가중치 (옵션)
        """
        if source_credibility_map:
            self.source_weights = source_credibility_map
        else:
            self.source_weights = self.SOURCE_WEIGHTS
    
    def calculate(
        self,
        articles: List[Dict[str, Any]],
        calendar_event: Optional[Dict[str, Any]] = None
    ) -> FourSignals:
        """
        4개 신호 계산
        
        Args:
            articles: 뉴스 기사 리스트
                [
                    {
                        'title': str,
                        'content': str,
                        'source': str,
                        'published_at': datetime,
                        'url': str
                    }
                ]
            calendar_event: 경제 캘린더 이벤트 (옵션)
                {
                    'event_name': str,
                    'scheduled_at': datetime,
                    'event_type': str
                }
        
        Returns:
            FourSignals
        """
        if not articles:
            return FourSignals(DI=0.0, TN=0.0, NI=0.0, EL=0.0)
        
        # 1. DI - 출처 다양성
        DI = self._calc_diversity_integrity(articles)
        
        # 2. TN - 시간적 자연스러움  
        TN = self._calc_temporal_naturalness(articles, calendar_event)
        
        # 3. NI - 내러티브 독립성
        NI = self._calc_narrative_independence(articles)
        
        # 4. EL - 이벤트 정당성
        EL = self._calc_event_legitimacy(articles, calendar_event)
        
        return FourSignals(DI=DI, TN=TN, NI=NI, EL=EL)
    
    def _calc_diversity_integrity(self, articles: List[Dict[str, Any]]) -> float:
        """
        DI (Diversity Integrity) - 출처 다양성
        
        논리:
        - 단일 출처: 0.0 (불신)
        - 2-3개 출처: 0.5
        - 4+ 출처 (다양한 Tier): 1.0
        - 가중치 합산
        """
        if not articles:
            return 0.0
        
        # 출처별 개수
        source_counts = {}
        weighted_sum = 0.0
        
        for article in articles:
            source = article.get('source', 'Unknown')
            source_counts[source] = source_counts.get(source, 0) + 1
            
            # 가중치
            weight = self.source_weights.get(source, 1.0)
            weighted_sum += weight
        
        unique_sources = len(source_counts)
        
        # 단일 출처
        if unique_sources == 1:
            return 0.0
        
        # 2-3개 출처
        elif unique_sources <= 3:
            # 가중치 합산이 높으면 점수 상승
            score = min(0.8, weighted_sum / 6.0)
            return score
        
        # 4+ 출처
        else:
            # 가중치 합산이 높으면 만점
            score = min(1.0, weighted_sum / 8.0)
            return score
    
    def _calc_temporal_naturalness(
        self,
        articles: List[Dict[str, Any]],
        calendar_event: Optional[Dict[str, Any]] = None
    ) -> float:
        """
        TN (Temporal Naturalness) - 시간적 자연스러움
        
        논리:
        - 엠바고 해제 (경제 지표, 실적): 1.0 (자연스러움)
        - 1분 내 30개 기사: 0.3 (의심)
        - 시간 분산도가 높을수록: 1.0
        """
        if not articles:
            return 0.0
        
        # 엠바고 이벤트 체크 (경제 캘린더 매칭)
        if calendar_event:
            event_type = calendar_event.get('event_type', '')
            if event_type in ['CPI', 'GDP', 'NFP', 'EARNINGS', 'FOMC']:
                # 엠바고 해제는 자연스러움
                return 1.0
        
        # 발행 시간 추출
        timestamps = []
        for article in articles:
            pub_time = article.get('published_at')
            if pub_time:
                timestamps.append(pub_time)
        
        if len(timestamps) < 2:
            return 0.5  # 판단 불가
        
        # 시간 범위 계산
        earliest = min(timestamps)
        latest = max(timestamps)
        time_span = (latest - earliest).total_seconds()
        
        # 1분 내 집중도 체크
        if time_span < 60:
            # velocity 계산
            velocity = len(articles) / max(time_span, 1)  # 기사/초
            
            if velocity > 0.5:  # 초당 0.5개 이상 (1분에 30개)
                return 0.3  # 비정상적 속도
        
        # 시간 분산도 계산
        try:
            # 타임스탬프를 초로 변환
            time_seconds = [(t - earliest).total_seconds() for t in timestamps]
            
            if len(time_seconds) > 1:
                time_variance = statistics.stdev(time_seconds)
                
                # 5분 분산을 기준으로 점수화
                # 분산이 클수록 자연스러움
                score = min(1.0, time_variance / 300)  # 300초 = 5분
                return max(0.3, score)  # 최소 0.3
        except:
            pass
        
        return 0.5  # 기본값
    
    def _calc_narrative_independence(self, articles: List[Dict[str, Any]]) -> float:
        """
        NI (Narrative Independence) - 내러티브 독립성
        
        논리:
        - 복붙 (유사도 > 0.9): 0.2
        - 독립적 취재 (유사도 < 0.5): 1.0
        - 중간: 선형 스케일
        """
        if not articles or len(articles) < 2:
            return 0.5  # 판단 불가
        
        # 기사 본문 추출
        texts = []
        for article in articles:
            # 제목 + 본문 (본문 우선)
            content = article.get('content') or article.get('title', '')
            if content:
                texts.append(content)
        
        if len(texts) < 2:
            return 0.5
        
        # 평균 유사도 계산
        try:
            avg_sim = average_similarity(texts, method='cosine')
        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            return 0.5
        
        # 유사도 기반 점수
        if avg_sim > 0.9:
            # 복붙 의심
            return 0.2
        elif avg_sim < 0.5:
            # 독립적 취재
            return 1.0
        else:
            # 중간: 선형 스케일
            # avg_sim이 0.5 -> 1.0, 0.9 -> 0.2
            score = 1.0 - ((avg_sim - 0.5) / 0.4) * 0.8
            return max(0.2, min(1.0, score))
    
    def _calc_event_legitimacy(
        self,
        articles: List[Dict[str, Any]],
        calendar_event: Optional[Dict[str, Any]] = None
    ) -> float:
        """
        EL (Event Legitimacy) - 이벤트 정당성
        
        논리:
        - 경제 캘린더 매칭 (±30분): 1.0
        - 매칭 없음: 0.5 (일반 뉴스)
        """
        if not calendar_event:
            # 경제 캘린더 이벤트 없음
            return 0.5  # 일반 뉴스
        
        # 이벤트 시간
        event_time = calendar_event.get('scheduled_at')
        if not event_time:
            return 0.5
        
        # 기사 발행 시간
        article_times = [
            a.get('published_at') for a in articles 
            if a.get('published_at')
        ]
        
        if not article_times:
            return 0.5
        
        earliest_article = min(article_times)
        
        # ±30분 매칭 확인
        time_diff = abs((earliest_article - event_time).total_seconds())
        
        if time_diff < 1800:  # 30분 = 1800초
            return 1.0  # 경제 캘린더 이벤트 매칭
        else:
            return 0.5  # 일반 뉴스

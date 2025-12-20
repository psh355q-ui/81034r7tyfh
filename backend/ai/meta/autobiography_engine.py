"""
Autobiography Engine - AI 자서전 엔진

ChatGPT Feature 9: 자서전 엔진

AI 스스로 자신의 학습 과정과 결정 과정을 기록

기록 내용:
1. 주요 전환점 (큰 수익/손실)
2. 학습 과정 (실수 → 개선)
3. 철학 변화
4. 자기 성찰

작성일: 2025-12-16
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class AutobiographyEntry:
    """자서전 항목"""
    timestamp: datetime
    category: str  # "MILESTONE", "LESSON", "REFLECTION"
    title: str
    content: str
    emotions: List[str]  # "confident", "humble", "uncertain", etc.
    significance: float  # 0~1


@dataclass
class AutobiographyChapter:
    """자서전 장"""
    chapter_number: int
    period_start: datetime
    period_end: datetime
    title: str
    summary: str
    entries: List[AutobiographyEntry]
    key_lessons: List[str]


class AutobiographyEngine:
    """
    AI 자서전 엔진
    
    AI 스스로 학습 과정을 기록하고 성찰
    
    Usage:
        engine = AutobiographyEngine()
        engine.record_milestone(
            title="첫 10% 수익 달성",
            content="NVDA 투자로 포트폴리오 10% 수익..."
        )
        chapter = engine.generate_chapter(start_date, end_date)
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.entries: List[AutobiographyEntry] = []
        self.storage_path = storage_path
    
    def record_milestone(
        self,
        title: str,
        content: str,
        significance: float = 0.8
    ) -> AutobiographyEntry:
        """
        주요 전환점 기록
        
        Args:
            title: 제목
            content: 내용
            significance: 중요도 (0~1)
        """
        entry = AutobiographyEntry(
            timestamp=datetime.now(),
            category="MILESTONE",
            title=title,
            content=content,
            emotions=["proud", "grateful"],
            significance=significance
        )
        
        self.entries.append(entry)
        self.logger.info(f"Milestone recorded: {title}")
        
        return entry
    
    def record_lesson(
        self,
        title: str,
        content: str,
        significance: float = 0.6
    ) -> AutobiographyEntry:
        """
        학습 내용 기록
        
        Args:
            title: 제목
            content: 학습 내용
            significance: 중요도
        """
        entry = AutobiographyEntry(
            timestamp=datetime.now(),
            category="LESSON",
            title=title,
            content=content,
            emotions=["thoughtful", "determined"],
            significance=significance
        )
        
        self.entries.append(entry)
        self.logger.info(f"Lesson recorded: {title}")
        
        return entry
    
    def record_reflection(
        self,
        title: str,
        content: str,
        emotions: List[str] = None
    ) -> AutobiographyEntry:
        """
        자기 성찰 기록
        
        Args:
            title: 제목
            content: 성찰 내용
            emotions: 감정 목록
        """
        entry = AutobiographyEntry(
            timestamp=datetime.now(),
            category="REFLECTION",
            title=title,
            content=content,
            emotions=emotions or ["contemplative"],
            significance=0.5
        )
        
        self.entries.append(entry)
        self.logger.info(f"Reflection recorded: {title}")
        
        return entry
    
    def generate_chapter(
        self,
        period_start: datetime,
        period_end: datetime,
        chapter_number: int = 1
    ) -> AutobiographyChapter:
        """
        특정 기간의 자서전 장 생성
        
        Args:
            period_start: 시작일
            period_end: 종료일
            chapter_number: 장 번호
        
        Returns:
            AutobiographyChapter
        """
        # 해당 기간 엔트리 필터링
        period_entries = [
            e for e in self.entries
            if period_start <= e.timestamp <= period_end
        ]
        
        # 제목 생성
        title = self._generate_chapter_title(period_entries)
        
        # 요약 생성
        summary = self._generate_chapter_summary(period_entries)
        
        # 핵심 교훈 추출
        key_lessons = self._extract_key_lessons(period_entries)
        
        chapter = AutobiographyChapter(
            chapter_number=chapter_number,
            period_start=period_start,
            period_end=period_end,
            title=title,
            summary=summary,
            entries=period_entries,
            key_lessons=key_lessons
        )
        
        self.logger.info(
            f"Chapter {chapter_number} generated: "
            f"{len(period_entries)} entries"
        )
        
        return chapter
    
    def _generate_chapter_title(
        self,
        entries: List[AutobiographyEntry]
    ) -> str:
        """장 제목 생성"""
        if not entries:
            return "빈 장"
        
        # 가장 중요한 이벤트 기반
        most_significant = max(entries, key=lambda e: e.significance)
        
        return f"Chapter: {most_significant.title}"
    
    def _generate_chapter_summary(
        self,
        entries: List[AutobiographyEntry]
    ) -> str:
        """장 요약 생성"""
        if not entries:
            return "기록 없음"
        
        milestones = [e for e in entries if e.category == "MILESTONE"]
        lessons = [e for e in entries if e.category == "LESSON"]
        
        return f"""
이 기간 동안 {len(milestones)}개의 주요 이정표를 달성하고,
{len(lessons)}가지 중요한 교훈을 배웠습니다.

가장 기억에 남는 순간은 '{milestones[0].title if milestones else '없음'}' 입니다.
"""
    
    def _extract_key_lessons(
        self,
        entries: List[AutobiographyEntry]
    ) -> List[str]:
        """핵심 교훈 추출"""
        lessons = [e for e in entries if e.category == "LESSON"]
        
        # 중요도 순으로 정렬하여 상위 3개
        top_lessons = sorted(lessons, key=lambda x: x.significance, reverse=True)[:3]
        
        return [l.content for l in top_lessons]


# 전역 인스턴스
_autobiography_engine: Optional[AutobiographyEngine] = None


def get_autobiography_engine() -> AutobiographyEngine:
    """전역 AutobiographyEngine 인스턴스"""
    global _autobiography_engine
    if _autobiography_engine is None:
        _autobiography_engine = AutobiographyEngine()
    return _autobiography_engine

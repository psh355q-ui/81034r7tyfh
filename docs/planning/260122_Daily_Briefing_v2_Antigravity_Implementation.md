# Daily Briefing System v2.0 - Antigravity 구현 계획서

**작성일**: 2026-01-22
**대상**: Antigravity Agent 자동 실행
**목적**: 캐싱 전략, RSS 전처리 통합, 국내 주식 브리핑 시스템 구현

---

## 📋 목차

1. [시스템 개요](#시스템-개요)
2. [핵심 아키텍처](#핵심-아키텍처)
3. [구현 Phase 순서](#구현-phase-순서)
4. [Phase별 상세 작업](#phase별-상세-작업)
5. [검증 체크리스트](#검증-체크리스트)
6. [완료 기준](#완료-기준)

---

## 시스템 개요

### 목표
1. **캐싱 전략**으로 불필요한 LLM API 호출 절감 (비용 70% 절감 목표)
2. **RSS 크롤링 결과**를 Ollama로 전처리하여 Gemini/Claude가 읽기 쉽게 DB 저장
3. **오전 8시 국내 주식 맞춤 브리핑** 추가 (미국 장 → 한국 장 연계)

### 핵심 변경사항

**❌ 잘못된 이해 (수정 전)**:
- Ollama가 국내 브리핑 품질 검토 (0-100점 평가)
- Ollama가 브리핑 개선 제안 생성

**✅ 올바른 이해 (수정 후)**:
- Ollama는 **RSS 데이터 전처리만** 담당
- 카테고리 분류, 핵심 요약, 키포인트 추출, 시장 영향도 평가
- **브리핑 생성/검토는 Gemini/Claude만 사용**

---

## 핵심 아키텍처

### 시스템 흐름

```
┌─────────────────────────────────────────────────────────────────┐
│  STEP 1: RSS 크롤링 (독립 실행, 백그라운드)                        │
│  - Reuters, AP, White House, CNBC, Bloomberg                    │
│  - 원본 DB 저장 (enhanced_by_ollama = False)                    │
└─────────────────────────────────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 2: Ollama RSS 전처리 (5분 간격)                            │
│  - 카테고리 분류 (AI & Tech, Semiconductors, Energy, etc.)       │
│  - 핵심 내용 요약 (2-3문장)                                       │
│  - 키포인트 추출 (평균 3개)                                       │
│  - 시장 영향도 평가 (HIGH/MEDIUM/LOW)                            │
│  - Enhanced DB 저장 (enhanced_by_ollama = True)                 │
└─────────────────────────────────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 3: 07:10 미국 브리핑 (Gemini/Claude API)                    │
│  - Ollama 전처리된 RSS 데이터 읽기                                │
│  - API 이용하여 시장 이슈 검색 및 추론 진행                         │
│  - 캐싱 전략 (변경 감지 → 중요도 평가 → 조건부 업데이트)            │
│  - 브리핑 생성 (Gemini/Claude)                                   │
└─────────────────────────────────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 4: 08:00 국내 브리핑 (Gemini/Claude API)                    │
│  - 미국 브리핑 읽기                                               │
│  - API 이용하여 시장 이슈 및 추론 진행                             │
│  - US → Korea 종목 매핑 (NVDA → 삼성전자/SK하이닉스)              │
│  - 한국 브리핑 생성 (Ollama 사용 안 함 ✅)                        │
└─────────────────────────────────────────────────────────────────┘
```

### 캐싱 전략

**중요도 점수 계산 (0-100점)**:
- 시장 갭 (Market Gaps): 30점
- 섹터 로테이션 (Sector Changes): 30점
- 경제 이벤트 (Economic Events): 25점
- AI 추천주 (AI Picks): 15점

**업데이트 기준**:
- **< 15점**: 캐시 사용 (변경 없음)
- **15-40점**: 메트릭만 업데이트
- **> 40점**: 전체 재생성

---

## 구현 Phase 순서

**반드시 순서대로 진행:**

```
Phase 1: DB 마이그레이션 (선행 필수)
  └─> models.py 수정 → 마이그레이션 파일 생성 → DB 적용

Phase 2: Ollama 전처리 시스템
  └─> ollama_rss_preprocessor.py 생성 → 테스트

Phase 3: 캐싱 시스템
  └─> daily_briefing_cache_manager.py 생성
  └─> daily_briefing_service.py 수정

Phase 4: 브리핑 통합
  └─> enhanced_daily_reporter.py 수정 (Ollama 전처리 데이터 읽기)
  └─> ollama_client.py 수정 (브리핑 검토 기능 제거)

Phase 5: 국내 브리핑
  └─> korean_market_briefing_reporter.py 생성

Phase 6: API & 스케줄러
  └─> reports_router.py 수정 (market 파라미터 추가)
  └─> scheduler.py 수정 (Ollama 전처리 스케줄 추가)

Phase 7: 환경 설정 & 배치 파일
  └─> .env.example 업데이트
  └─> 7_Ollama_전처리_시작.bat 생성
```

---

## Phase별 상세 작업

### Phase 1: DB 마이그레이션 (선행 필수)

#### Task 1.1: models.py 수정

**파일**: `backend/database/models.py`
**수정 위치**: NewsArticle 클래스 내부 (line 107 이후)

**추가할 컬럼** (line 107 `glm_analysis = Column(JSONB, nullable=True)` 바로 다음):

```python
    # Ollama RSS Preprocessing Fields (Added in Daily Briefing System v2.0 - 2026-01-22)
    enhanced_by_ollama = Column(Boolean, default=False, nullable=False, index=True, comment='Ollama 전처리 완료 여부')
    category = Column(String(50), nullable=True, comment='뉴스 카테고리 (AI & Tech, Semiconductors, Energy, Financials, Healthcare, Geopolitics, Other)')
    enhanced_summary = Column(Text, nullable=True, comment='Ollama 생성 핵심 요약 (2-3문장)')
    key_points = Column(JSONB, nullable=True, comment='핵심 포인트 리스트 ["포인트1", "포인트2", "포인트3"]')
    market_relevance = Column(String(20), nullable=True, comment='시장 영향도 (HIGH/MEDIUM/LOW)')
    sectors_affected = Column(JSONB, nullable=True, comment='영향받는 섹터 ["Technology", "Energy", "Financials"]')
```

**추가할 인덱스** (__table_args__ 섹션 내부, 기존 Index 리스트 마지막에):

```python
        # Ollama Preprocessing Indexes (Daily Briefing System v2.0 - 2026-01-22)
        Index('idx_news_enhanced_by_ollama', 'enhanced_by_ollama'),
        Index('idx_news_category', 'category', postgresql_where=text('category IS NOT NULL')),
        Index('idx_news_market_relevance', 'market_relevance', postgresql_where=text('market_relevance IS NOT NULL')),
```

**주의사항**:
- `text()` import 확인: `from sqlalchemy import ..., text`
- 쉼표(,) 빠뜨리지 않기
- 들여쓰기 정확히 (8 spaces)

#### Task 1.2: 마이그레이션 파일 생성

**파일**: `backend/database/migrations/add_ollama_enhancement_columns.py` (신규)

```python
"""
Add Ollama RSS enhancement columns to news_articles

Migration for Daily Briefing System v2.0
Created: 2026-01-22
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


def upgrade():
    """Add Ollama preprocessing columns to news_articles"""
    print("🔄 Adding Ollama enhancement columns...")

    # Add columns
    op.add_column('news_articles', sa.Column(
        'enhanced_by_ollama',
        sa.Boolean(),
        nullable=False,
        server_default='false',
        comment='Ollama 전처리 완료 여부'
    ))

    op.add_column('news_articles', sa.Column(
        'category',
        sa.String(50),
        nullable=True,
        comment='뉴스 카테고리'
    ))

    op.add_column('news_articles', sa.Column(
        'enhanced_summary',
        sa.Text(),
        nullable=True,
        comment='Ollama 생성 요약'
    ))

    op.add_column('news_articles', sa.Column(
        'key_points',
        JSONB,
        nullable=True,
        comment='핵심 포인트'
    ))

    op.add_column('news_articles', sa.Column(
        'market_relevance',
        sa.String(20),
        nullable=True,
        comment='시장 영향도'
    ))

    op.add_column('news_articles', sa.Column(
        'sectors_affected',
        JSONB,
        nullable=True,
        comment='영향 섹터'
    ))

    # Add indexes
    op.create_index(
        'idx_news_enhanced_by_ollama',
        'news_articles',
        ['enhanced_by_ollama']
    )

    op.create_index(
        'idx_news_category',
        'news_articles',
        ['category'],
        postgresql_where=sa.text('category IS NOT NULL')
    )

    op.create_index(
        'idx_news_market_relevance',
        'news_articles',
        ['market_relevance'],
        postgresql_where=sa.text('market_relevance IS NOT NULL')
    )

    print("✅ Ollama enhancement columns added successfully")


def downgrade():
    """Remove Ollama preprocessing columns"""
    print("🔄 Removing Ollama enhancement columns...")

    # Drop indexes first
    op.drop_index('idx_news_market_relevance', 'news_articles')
    op.drop_index('idx_news_category', 'news_articles')
    op.drop_index('idx_news_enhanced_by_ollama', 'news_articles')

    # Drop columns
    op.drop_column('news_articles', 'sectors_affected')
    op.drop_column('news_articles', 'market_relevance')
    op.drop_column('news_articles', 'key_points')
    op.drop_column('news_articles', 'enhanced_summary')
    op.drop_column('news_articles', 'category')
    op.drop_column('news_articles', 'enhanced_by_ollama')

    print("✅ Ollama enhancement columns removed")
```

**실행 방법**:
```bash
python backend/database/migrations/add_ollama_enhancement_columns.py
# 또는
1_DB_마이그레이션.bat
```

**검증 방법**:
```sql
-- PostgreSQL에서 확인
\d news_articles

-- 컬럼 확인
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'news_articles'
AND column_name IN ('enhanced_by_ollama', 'category', 'enhanced_summary', 'key_points', 'market_relevance', 'sectors_affected');

-- 인덱스 확인
SELECT indexname FROM pg_indexes WHERE tablename = 'news_articles' AND indexname LIKE '%ollama%';
```

---

### Phase 2: Ollama RSS 전처리 시스템 (핵심)

#### Task 2.1: ollama_rss_preprocessor.py 신규 생성

**파일**: `backend/ai/llm/ollama_rss_preprocessor.py` (신규)

**목적**: RSS 원본 데이터를 Gemini/Claude가 읽기 쉽게 전처리

**전체 코드** (500+ lines):

```python
"""
Ollama RSS Preprocessor

역할: RSS 원본 데이터를 Gemini/Claude가 읽기 쉽게 전처리
- 카테고리 분류 (AI & Tech, Semiconductors, Energy, etc.)
- 핵심 내용 요약 (2-3문장)
- 키포인트 추출 (평균 3개)
- 시장 영향도 평가 (HIGH/MEDIUM/LOW)
- 영향 섹터 식별

실행: 독립 프로세스 (백그라운드), 5분 간격
"""

import asyncio
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

import httpx
from sqlalchemy import select, update, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

# 상대 import 사용
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from backend.database.models import NewsArticle
from backend.database.connection import DatabaseSession
from backend.ai.llm.ollama_client import get_ollama_client

logger = logging.getLogger(__name__)


class OllamaRSSPreprocessor:
    """
    Ollama 기반 RSS 데이터 전처리기

    특징:
    - 5분 간격으로 미전처리 뉴스 체크
    - 배치 처리 (100개씩)
    - Ollama 실패 시 폴백 (규칙 기반)
    """

    # RSS 뉴스 카테고리 (테마별 키워드)
    CATEGORY_THEMES = {
        'AI & Tech': [
            'artificial intelligence', 'ai', 'machine learning', 'openai',
            'google', 'microsoft', 'nvidia', 'chatgpt', 'deepmind', 'llm'
        ],
        'Semiconductors': [
            'chip', 'semiconductor', 'tsmc', 'intel', 'amd', 'nvidia',
            'fabrication', 'wafer', 'chipmaker', 'asml'
        ],
        'Energy': [
            'oil', 'energy', 'crude', 'opec', 'exxon', 'chevron',
            'renewable', 'solar', 'wind', 'lng', 'gas'
        ],
        'Financials': [
            'bank', 'fed', 'interest rate', 'jpmorgan', 'goldman sachs',
            'credit', 'loan', 'mortgage', 'treasury', 'inflation'
        ],
        'Healthcare': [
            'pharma', 'drug', 'vaccine', 'pfizer', 'moderna',
            'clinical trial', 'fda', 'biotech', 'health'
        ],
        'Geopolitics': [
            'trump', 'biden', 'white house', 'congress', 'china',
            'russia', 'ukraine', 'tariff', 'trade war', 'election'
        ]
    }

    def __init__(self):
        """초기화"""
        self.ollama = get_ollama_client()
        self.use_ollama = self.ollama.check_health()

        if not self.use_ollama:
            logger.error("❌ Ollama not available! Preprocessor will use fallback mode.")
        else:
            logger.info("✅ Ollama client initialized successfully")

    async def run_preprocessing_loop(self, interval_minutes: float = 5.0):
        """
        전처리 루프 (백그라운드 실행)

        Args:
            interval_minutes: 체크 간격 (분, 기본 5분)
        """
        logger.info(f"🚀 Starting Ollama RSS preprocessing loop (every {interval_minutes} min)...")

        while True:
            try:
                async with DatabaseSession() as session:
                    # 1. 미전처리 뉴스 조회
                    unprocessed_news = await self._get_unprocessed_rss_news(session)

                    if unprocessed_news:
                        logger.info(f"📰 Found {len(unprocessed_news)} unprocessed RSS articles")

                        # 2. 배치 전처리
                        success_count = 0
                        fail_count = 0

                        for article in unprocessed_news:
                            try:
                                # Ollama로 전처리
                                enhanced_data = await self._enhance_article_with_ollama(article)

                                # DB 업데이트
                                await self._save_enhanced_data(session, article.id, enhanced_data)

                                success_count += 1
                                logger.info(f"✅ Enhanced [{success_count}/{len(unprocessed_news)}]: {article.title[:50]}...")

                            except Exception as e:
                                fail_count += 1
                                logger.error(f"❌ Failed to enhance article {article.id}: {e}")
                                continue

                        await session.commit()
                        logger.info(f"🎉 Batch complete: {success_count} success, {fail_count} failed")
                    else:
                        logger.debug("✨ No unprocessed RSS articles found")

                # 다음 체크까지 대기
                await asyncio.sleep(interval_minutes * 60)

            except asyncio.CancelledError:
                logger.info("🛑 Preprocessing loop cancelled")
                break
            except Exception as e:
                logger.error(f"❌ Preprocessing loop error: {e}")
                await asyncio.sleep(60)  # 에러 발생 시 1분 대기

    async def _get_unprocessed_rss_news(self, session: AsyncSession) -> List[NewsArticle]:
        """미전처리 RSS 뉴스 조회"""
        stmt = (
            select(NewsArticle)
            .where(
                and_(
                    NewsArticle.enhanced_by_ollama == False,
                    NewsArticle.source.in_([
                        'Reuters', 'AP News', 'White House',
                        'CNBC', 'Bloomberg', 'C-SPAN'
                    ])
                )
            )
            .order_by(desc(NewsArticle.published_date))
            .limit(100)  # 배치 크기
        )
        result = await session.execute(stmt)
        return result.scalars().all()

    async def _enhance_article_with_ollama(self, article: NewsArticle) -> Dict[str, Any]:
        """
        Ollama로 RSS 기사 전처리

        Returns:
            {
                'category': 'AI & Tech',
                'enhanced_summary': '핵심 요약 2-3문장',
                'key_points': ['포인트1', '포인트2', '포인트3'],
                'market_relevance': 'HIGH',
                'sectors_affected': ['Technology', 'Semiconductors']
            }
        """
        prompt = f"""당신은 금융 뉴스 분석 전문가입니다. 다음 RSS 뉴스를 전처리하세요:

**제목**: {article.title}
**내용**: {article.summary or article.content[:1000]}
**출처**: {article.source}

다음 JSON 형식으로 전처리 결과를 제공하세요:

{{
    "category": "AI & Tech",
    "enhanced_summary": "이 뉴스의 핵심 내용을 2-3문장으로 요약",
    "key_points": ["핵심 포인트 1", "핵심 포인트 2", "핵심 포인트 3"],
    "market_relevance": "HIGH",
    "sectors_affected": ["Technology", "Semiconductors"]
}}

**카테고리 선택지**:
- AI & Tech (인공지능, 빅테크)
- Semiconductors (반도체)
- Energy (에너지, 원유)
- Financials (금융, 은행, 금리)
- Healthcare (제약, 바이오)
- Geopolitics (정치, 무역전쟁)
- Other (기타)

**시장 영향도 (market_relevance)**:
- HIGH: 주가에 즉각적 영향 (실적, M&A, 규제, 정책 변화)
- MEDIUM: 중기적 영향 (산업 동향, 기술 발표)
- LOW: 참고용 (일반 뉴스, 비금융 이슈)

**섹터 (sectors_affected)**:
- 영향받을 것으로 예상되는 산업 섹터 리스트
- 예: ["Technology", "Semiconductors"], ["Energy", "Financials"]

유효한 JSON만 응답하세요. 다른 텍스트 포함 금지."""

        try:
            response = httpx.post(
                f"{self.ollama.base_url}/api/generate",
                json={
                    "model": self.ollama.model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                    "options": {
                        "temperature": 0.3,
                        "num_predict": 500
                    }
                },
                timeout=60.0
            )

            if response.status_code == 200:
                result = response.json()
                enhanced_data = json.loads(result["response"])

                # 필수 키 검증
                required_keys = ['category', 'enhanced_summary', 'key_points', 'market_relevance']
                if all(k in enhanced_data for k in required_keys):
                    return enhanced_data
                else:
                    logger.warning(f"⚠️ Missing keys in Ollama response: {enhanced_data}")
                    return self._fallback_enhancement(article)
            else:
                logger.error(f"❌ Ollama API error: {response.status_code}")
                return self._fallback_enhancement(article)

        except Exception as e:
            logger.error(f"❌ Ollama enhancement failed: {e}")
            return self._fallback_enhancement(article)

    def _fallback_enhancement(self, article: NewsArticle) -> Dict[str, Any]:
        """Ollama 실패 시 폴백 전처리 (규칙 기반 키워드 매칭)"""
        content_lower = f"{article.title} {article.summary or ''}".lower()

        # 키워드 매칭으로 카테고리 추정
        category = 'Other'
        for cat, keywords in self.CATEGORY_THEMES.items():
            if any(kw in content_lower for kw in keywords):
                category = cat
                break

        return {
            'category': category,
            'enhanced_summary': article.summary or article.title,
            'key_points': [article.title],
            'market_relevance': 'MEDIUM',
            'sectors_affected': []
        }

    async def _save_enhanced_data(
        self,
        session: AsyncSession,
        article_id: int,
        enhanced_data: Dict[str, Any]
    ):
        """전처리 결과를 DB에 저장"""
        stmt = (
            update(NewsArticle)
            .where(NewsArticle.id == article_id)
            .values(
                enhanced_by_ollama=True,
                category=enhanced_data['category'],
                enhanced_summary=enhanced_data['enhanced_summary'],
                key_points=json.dumps(enhanced_data['key_points']),
                market_relevance=enhanced_data['market_relevance'],
                sectors_affected=json.dumps(enhanced_data.get('sectors_affected', []))
            )
        )
        await session.execute(stmt)


# 직접 실행 시
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    async def main():
        preprocessor = OllamaRSSPreprocessor()
        await preprocessor.run_preprocessing_loop(interval_minutes=5.0)

    asyncio.run(main())
```

**실행 방법**:
```bash
# 백그라운드 실행
python backend/ai/llm/ollama_rss_preprocessor.py &

# 또는 배치 파일
7_Ollama_전처리_시작.bat
```

**테스트 방법**:
```bash
# 1. Ollama 서버 확인
curl http://localhost:11434/api/tags

# 2. DB에 미전처리 뉴스 확인
psql -d trading_db -c "SELECT COUNT(*) FROM news_articles WHERE enhanced_by_ollama = false AND source IN ('Reuters', 'AP News');"

# 3. 전처리 실행 (포그라운드, 1회만)
python backend/ai/llm/ollama_rss_preprocessor.py

# 4. 전처리 결과 확인 (30초 후)
psql -d trading_db -c "SELECT id, title, category, market_relevance, enhanced_summary FROM news_articles WHERE enhanced_by_ollama = true LIMIT 5;"
```

---

### Phase 3-7: 나머지 Phase

나머지 Phase (캐싱 시스템, 브리핑 통합, 국내 브리핑, API & 스케줄러)는 Plan 파일 `C:\Users\a\.claude\plans\dapper-cuddling-bear.md`의 **ANTIGRAVITY 구현 가이드** 섹션 (line 1400~2900)에 상세히 기술되어 있습니다.

**핵심 파일 목록**:

- **Phase 3**:
  - `backend/services/daily_briefing_cache_manager.py` (신규)
  - `backend/services/daily_briefing_service.py` (수정)

- **Phase 4**:
  - `backend/ai/reporters/enhanced_daily_reporter.py` (수정)
  - `backend/ai/llm/ollama_client.py` (수정)

- **Phase 5**:
  - `backend/ai/reporters/korean_market_briefing_reporter.py` (신규)

- **Phase 6**:
  - `backend/api/reports_router.py` (수정)
  - `backend/automation/scheduler.py` (수정)

- **Phase 7**:
  - `.env.example` (수정)
  - `7_Ollama_전처리_시작.bat` (신규)

**각 Phase의 상세 코드, 수정 위치, 테스트 방법은 원본 Plan 파일을 참조하세요.**

---

## 검증 체크리스트

### Phase 1 검증: DB 마이그레이션
- [ ] `news_articles` 테이블에 6개 컬럼 추가 확인
- [ ] 3개 인덱스 생성 확인
- [ ] 기본값 `enhanced_by_ollama = false` 확인

### Phase 2 검증: Ollama 전처리
- [ ] Ollama 서버 정상 (localhost:11434)
- [ ] 전처리 루프 5분 간격 실행 확인
- [ ] 카테고리 분류 정확도 > 80%
- [ ] enhanced_summary 생성 확인
- [ ] key_points 추출 확인
- [ ] market_relevance 평가 (HIGH/MEDIUM/LOW)
- [ ] Ollama 실패 시 폴백 동작 (규칙 기반)

### Phase 3-4 검증: 브리핑 시스템
- [ ] 미국 브리핑 Ollama 전처리 데이터 사용 확인
- [ ] Gemini/Claude API가 시장 이슈 검색 및 추론 수행 확인
- [ ] 캐싱 전략 정상 동작 (hit rate > 60%)
- [ ] 중요도 점수 계산 정확

### Phase 5 검증: 국내 브리핑
- [ ] 08:00 자동 생성
- [ ] US → Korea 매핑 정확 (NVDA → 삼성전자)
- [ ] Ollama 검토 기능 없음 확인 (Gemini/Claude만 사용)
- [ ] 구체적 목표가 제시

### Phase 6-7 검증: 스케줄러 & 설정
- [ ] `/daily?market=us` 엔드포인트 동작
- [ ] `/daily?market=korea` 엔드포인트 동작
- [ ] 07:10, 08:00 스케줄 확인
- [ ] .env 설정 적용

---

## 완료 기준

모든 Phase가 완료되면 다음 상태가 되어야 합니다:

1. ✅ **DB**: news_articles 테이블에 6개 컬럼 + 3개 인덱스 추가
2. ✅ **Ollama 전처리**: 백그라운드 실행 중, 5분마다 미전처리 뉴스 처리
3. ✅ **미국 브리핑**: Ollama 전처리 RSS 데이터 읽어서 생성, Gemini/Claude API가 시장 이슈 검색 및 추론
4. ✅ **국내 브리핑**: 미국 브리핑 기반으로 생성, Gemini/Claude API가 추론 (Ollama 사용 안 함)
5. ✅ **API**: `/daily?market=us|korea` 엔드포인트 동작
6. ✅ **스케줄러**: 07:10 미국, 08:00 국내 자동 생성

---

## 참고 문서

- **상세 구현 가이드**: `C:\Users\a\.claude\plans\dapper-cuddling-bear.md` (line 1400~2900)
- **구조 맵**: `docs/architecture/structure-map.md`
- **빠른 시작 가이드**: `docs/guides/QUICK_START.md`

---

**End of Implementation Plan**

https://youtu.be/Xxnb_oFqdlE?si=YORPNIWR_24A5M5W

이 영상을 확인하고 이러한 방식으로 일일 브리핑을 남기게 하려고 아래와 같이 개발 계획을 작성하였어

영상처럼 분석 할 수 있게 추가 할 내용과, 보완할 내용 검토해줘



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




---



## Phase별 상세 작업



### Phase 1: DB 마이그레이션 (선행 필수)



#### Task 1.1: models.py 수정



**파일**: backend/database/models.py

**수정 위치**: NewsArticle 클래스 내부 (line 107 이후)



**추가할 컬럼** (line 107 glm_analysis = Column(JSONB, nullable=True) 바로 다음):




python

    # Ollama RSS Preprocessing Fields (Added in Daily Briefing System v2.0 - 2026-01-22)

    enhanced_by_ollama = Column(Boolean, default=False, nullable=False, index=True, comment='Ollama 전처리 완료 여부')

    category = Column(String(50), nullable=True, comment='뉴스 카테고리 (AI & Tech, Semiconductors, Energy, Financials, Healthcare, Geopolitics, Other)')

    enhanced_summary = Column(Text, nullable=True, comment='Ollama 생성 핵심 요약 (2-3문장)')

    key_points = Column(JSONB, nullable=True, comment='핵심 포인트 리스트 ["포인트1", "포인트2", "포인트3"]')

    market_relevance = Column(String(20), nullable=True, comment='시장 영향도 (HIGH/MEDIUM/LOW)')

    sectors_affected = Column(JSONB, nullable=True, comment='영향받는 섹터 ["Technology", "Energy", "Financials"]')




**추가할 인덱스** (__table_args__ 섹션 내부, 기존 Index 리스트 마지막에):




python

        # Ollama Preprocessing Indexes (Daily Briefing System v2.0 - 2026-01-22)

        Index('idx_news_enhanced_by_ollama', 'enhanced_by_ollama'),

        Index('idx_news_category', 'category', postgresql_where=text('category IS NOT NULL')),

        Index('idx_news_market_relevance', 'market_relevance', postgresql_where=text('market_relevance IS NOT NULL')),




**주의사항**:

- text() import 확인: from sqlalchemy import ..., text

- 쉼표(,) 빠뜨리지 않기

- 들여쓰기 정확히 (8 spaces)



#### Task 1.2: 마이그레이션 파일 생성



**파일**: backend/database/migrations/add_ollama_enhancement_columns.py (신규)




python

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




**실행 방법**:


bash

python backend/database/migrations/add_ollama_enhancement_columns.py

# 또는

1_DB_마이그레이션.bat




**검증 방법**:


sql

-- PostgreSQL에서 확인

\d news_articles



-- 컬럼 확인

SELECT column_name, data_type, is_nullable

FROM information_schema.columns

WHERE table_name = 'news_articles'

AND column_name IN ('enhanced_by_ollama', 'category', 'enhanced_summary', 'key_points', 'market_relevance', 'sectors_affected');



-- 인덱스 확인

SELECT indexname FROM pg_indexes WHERE tablename = 'news_articles' AND indexname LIKE '%ollama%';




---



### Phase 2: Ollama RSS 전처리 시스템 (핵심)



#### Task 2.1: ollama_rss_preprocessor.py 신규 생성



**파일**: backend/ai/llm/ollama_rss_preprocessor.py (신규)



**목적**: RSS 원본 데이터를 Gemini/Claude가 읽기 쉽게 전처리



**전체 코드** (500+ lines):




python

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




**실행 방법**:


bash

# 백그라운드 실행

python backend/ai/llm/ollama_rss_preprocessor.py &



# 또는 배치 파일

7_Ollama_전처리_시작.bat




**테스트 방법**:


bash

# 1. Ollama 서버 확인

curl http://localhost:11434/api/tags



# 2. DB에 미전처리 뉴스 확인

psql -d trading_db -c "SELECT COUNT(*) FROM news_articles WHERE enhanced_by_ollama = false AND source IN ('Reuters', 'AP News');"



# 3. 전처리 실행 (포그라운드, 1회만)

python backend/ai/llm/ollama_rss_preprocessor.py



# 4. 전처리 결과 확인 (30초 후)

psql -d trading_db -c "SELECT id, title, category, market_relevance, enhanced_summary FROM news_articles WHERE enhanced_by_ollama = true LIMIT 5;"




---



### Phase 3-7: 나머지 Phase



나머지 Phase (캐싱 시스템, 브리핑 통합, 국내 브리핑, API & 스케줄러)는 Plan 파일 C:\Users\a\.claude\plans\dapper-cuddling-bear.md의 **ANTIGRAVITY 구현 가이드** 섹션 (line 1400~2900)에 상세히 기술되어 있습니다.



**핵심 파일 목록**:



- **Phase 3**:

  - backend/services/daily_briefing_cache_manager.py (신규)

  - backend/services/daily_briefing_service.py (수정)



- **Phase 4**:

  - backend/ai/reporters/enhanced_daily_reporter.py (수정)

  - backend/ai/llm/ollama_client.py (수정)



- **Phase 5**:

  - backend/ai/reporters/korean_market_briefing_reporter.py (신규)



- **Phase 6**:

  - backend/api/reports_router.py (수정)

  - backend/automation/scheduler.py (수정)



- **Phase 7**:

  - .env.example (수정)

  - 7_Ollama_전처리_시작.bat (신규)



**각 Phase의 상세 코드, 수정 위치, 테스트 방법은 원본 Plan 파일을 참조하세요.**



---



## 검증 체크리스트



### Phase 1 검증: DB 마이그레이션

- [ ] news_articles 테이블에 6개 컬럼 추가 확인

- [ ] 3개 인덱스 생성 확인

- [ ] 기본값 enhanced_by_ollama = false 확인



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

- [ ] /daily?market=us 엔드포인트 동작

- [ ] /daily?market=korea 엔드포인트 동작

- [ ] 07:10, 08:00 스케줄 확인

- [ ] .env 설정 적용



---



## 완료 기준



모든 Phase가 완료되면 다음 상태가 되어야 합니다:



1. ✅ **DB**: news_articles 테이블에 6개 컬럼 + 3개 인덱스 추가

2. ✅ **Ollama 전처리**: 백그라운드 실행 중, 5분마다 미전처리 뉴스 처리

3. ✅ **미국 브리핑**: Ollama 전처리 RSS 데이터 읽어서 생성, Gemini/Claude API가 시장 이슈 검색 및 추론

4. ✅ **국내 브리핑**: 미국 브리핑 기반으로 생성, Gemini/Claude API가 추론 (Ollama 사용 안 함)

5. ✅ **API**: /daily?market=us|korea 엔드포인트 동작

6. ✅ **스케줄러**: 07:10 미국, 08:00 국내 자동 생성



---



## 참고 문서



- **상세 구현 가이드**: C:\Users\a\.claude\plans\dapper-cuddling-bear.md (line 1400~2900)

- **구조 맵**: docs/architecture/structure-map.md

- **빠른 시작 가이드**: docs/guides/QUICK_START.md



---



**End of Implementation Plan**


좋은 방향으로 이미 구조를 잘 잡아두셨고, 자동 브리핑 시스템 구현을 위한 계획서 초안도 상세합니다. 메시지에 포함하신 YouTube 영상의 정체는 아래와 같습니다:

👉 미국 증시 오늘의 요약 영상 (Xxnb_oFqdlE)
 — 제목처럼 “미국 증시 오늘의 요약” 브리핑 영상입니다. 주로 시황 / 주요 이슈 / 핵심 포인트 요약을 보여주는 포맷입니다 (미국 증시, 뉴스, 비트코인 등 핵심 시장 변수 정리).

🔎 영상처럼 분석·브리핑을 만들기 위한 추가·보완 포인트

아래는 현재 계획서 기반으로 영상 스타일/퀄리티를 갖춘 Daily Briefing으로 발전시키기 위한 구체적인 내용입니다.

✅ 1) 포맷 정의: 핵심 구성 요소

현재 시스템은 기술적으로는 훌륭하지만, 영상처럼 사람이 이해하기 쉬운 레포트/브리핑으로 만들려면 아래 정형 포맷을 명시해야 합니다.

📌 권장 브리핑 구성 (매일 고정 템플릿):

오늘 요약 헤드라인 (Headline)

예: “트럼프 관세 철회 → TACO 장세 재부상”

핵심 시장 지표 요약

미국 주요 지수 (S&P500, NASDAQ, Dow)

변동성, 옵션 흐름

Top 3 핵심 뉴스 & 요약

뉴스 제목 + 2–3문장 요약 + 영향도
→ (이건 Ollama 전처리 결과로 자동 채울 수 있음)

시장 스냅샷 (숫자 포인트)

지수 상승/하락 폭

섹터별 특징

주요 코멘트 / 인사이트

단순 요약이 아닌 맥락/추세/퀀텀 인사이트

전일 이벤트 → 국내 장 연결

미국 ↔ 한국 장 사이 영향 매핑

👉 영상처럼 진행 흐름을 미리 정하고, 모델 역할/입력 템플릿을 통일하면 퀄리티를 한층 끌어올릴 수 있습니다.

✅ 2) LLM 템플릿 개선 — 기사 + 인사이트 통합

현재 브리핑 생성 단계에서 “시장 이슈 검색 및 추론”으로 되어 있는데,

✔ 기사 요약 + 인사이트 레이어
✔ 시장 영향도 설명
✔ 관련 핵심 시그널 정리

이 3가지 층을 명확히 나눠주세요.

📌 예: Gemini 프롬프트 템플릿 구조

1) 제목 + 요약
2) 해당 뉴스의 시장 의미 (정량/정성)
3) 주요 가격·섹터 영향
4) 연관 종목/지수 제시 (예: NVDA → 삼성HYNIX)


이렇게 4단계 레이어로 나누면 영상처럼 구조화된 아웃풋이 더 일관되게 됩니다.

✅ 3) 캐싱 전략 → 중요도 스코어링 세분화

현재는 중요도 0–100점을 4그룹으로 나눠서 캐싱 조건을 적용 중입니다.

📌 추천 확장:

점수 범위	행동
0–10	캐시 유지
10–25	메트릭 업데이트
25–60	일부 재생성
60+	전체 재생성 + 서머리 재작성

👉 이렇게 그레이드 구간을 늘리면 중요도에 따라 내용을 유지/갱신하는 전략을 더 정교하게 설계할 수 있습니다.

✅ 4) 데이터 연계 지표

영상 브리핑은 종종 “핵심 숫자 + 뉴스”가 결합되어 있습니다. 현재는 뉴스 위주인데,

📊 여기에 실시간 지수/거래량/변동성/코인 지수 데이터를 자동 연동하세요.

예:

S&P 500 → 하루 변동폭

Bitcoin 24h % 변동

금리·환율

이런 “숫자 + 텍스트” 결합 포인트는 영상 브리핑 퀄리티를 끌어올립니다.

✅ 5) 테스트 케이스 & 벤치마크

영상처럼 정렬된 브리핑을 만들려면 벤치마크 사례가 필요합니다.

✔ (예) 다우존스 리서치 데일리 브리핑
✔ (예) CNBC 시장 리캡

실제 예제를 모아 LLM 출력 스타일/문장 길이/포맷을 비교해 보세요.

🛠 정리: 보완/추가 요약
항목	필요성	추가/보완
브리핑 템플릿	매우 높음	고정 헤드라인, 섹션 정의, 숫자/텍스트 결합
LLM 프롬프트	중요	인사이트 레이어 강화
캐시 전략	중간	점수 범위 세분화
실시간 데이터	높음	지수/거래량/가격 지표 추가
벤치마크	보완	상용 브리핑 사례 수집
📣 다음 단계 제안

영상 스타일 브리핑 템플릿 정의 문서화

섹션별 필드 + 출력 예시

LLM Prompt 정규화 표준 만들기

US / KR 브리핑 모두 일관된 구조

실시간 숫자 데이터 파이프라인 구축

Q1

영상처럼 더 정교한 시장 브리핑을 만들 때 어떤 ‘정량 지표’를 어떤 방식으로 Daily Report에 포함시키는 것이 가장 효과적일까요?

Q2

Ollama 전처리에서 추출한 핵심 포인트를 Gemini/Claude 브리핑에 가장 자연스럽게 녹여낼 수 있는 구조화 포맷은 어떤 모습일까요?

Q3

미국 시장 이슈를 국내 종목 브리핑으로 연결할 때 구체적으로 어떤 매핑 로직이나 룰셋을 정의하는 게 좋을까요?

이런 경제캘린더 주요 일정에 대해서 검토하는 내용을 추가해야해

주요 지표가 악화될경우 시장 상황이 갑자기 안좋아질수있어

지정된 시간 후 10초~30초내 업데이트 하도록해야해,

시장분석에 참고할 수 있도록 추가 구현해줘

좋은 포인트야 — 경제 캘린더 주요 일정 데이터를 Daily Briefing에 실시간으로 반영하면 급격한 시장 변동 리스크를 포착할 수 있어. 요청 기준인 지정 시간 이후 10~30초 내 업데이트 반영 및 시장 영향도 분석 기능까지 설계 방향과 코드/구조 예시를 아래에 정리했어.

🧠 구현 목표 요약

추가해야 할 기능

경제 캘린더 파싱 모듈

주요 경제 지표: GDP, PCE, 실업자수, EIA 재고 등

예상치 대비 실제치 비교

이벤트 트리거 & 리스너

발표 직후 10–30초 내 알림/업데이트

시장 영향 점수화

실제치가 예상과 얼마나 차이 나는지에 따라 영향도 점수 부여

브리핑 통합 레이어

뉴스/지표/지수 변동까지 한 번에 요약

LLM 입출력 템플릿 강화

경제 지표 결과를 자연스럽게 시장 해석 포함

🛠 시스템 설계 & 대략 코드 구조
✅ 1) 경제 캘린더 데이터 소스

RSS/크롤러/Scheduler 로 가져올 수 있는 주요 API 후보:

- Investing.com/ForexFactory 경제캘린더
- FRED/EIA/BEA/US BLS 공식 발표
- Alpha Vantage / EconAPI


※ 자동화를 위해 정규화된 JSON 포맷으로 저장할 예정

✅ 2) 경제 이벤트 모델 (DB)
# backend/database/models.py

class EconEvent(Base):
    __tablename__ = "economic_events"

    id = Column(Integer, primary_key=True)
    event_name = Column(String(200), nullable=False)
    market = Column(String(50), nullable=False)  # US / KR / Global
    schedule_time = Column(DateTime, nullable=False)
    actual_value = Column(Float, nullable=True)
    forecast_value = Column(Float, nullable=True)
    prior_value = Column(Float, nullable=True)
    impact_score = Column(Integer, nullable=True)  # 계산된 영향도 점수
    is_processed = Column(Boolean, default=False)

✅ 3) Scheduler + Real Time Listener
# backend/automation/econ_calendar_listener.py

import asyncio
from datetime import datetime, timedelta
from backend.database.connection import DatabaseSession
from backend.database.models import EconEvent

class EconCalendarListener:

    async def loop(self):
        while True:
            async with DatabaseSession() as session:
                now = datetime.utcnow()
                
                # 10초 ~ 30초 범위의 이벤트 조회
                upcoming = await session.execute(
                    select(EconEvent).where(
                        and_(
                            EconEvent.schedule_time <= now,
                            EconEvent.is_processed == False
                        )
                    )
                )
                for event in upcoming.scalars().all():
                    # 즉시 처리
                    await self.process_event(session, event)

                await session.commit()

            await asyncio.sleep(5)  # 5초 단위 체크

    async def process_event(self, session, event: EconEvent):
        # 1) 발표 Actual 값 API로 fetch
        actual = await self.fetch_actual(event)
        event.actual_value = actual

        # 2) 영향도 계산
        event.impact_score = self.compute_impact_score(
            event.forecast_value, actual
        )

        # 3) 마크 처리
        event.is_processed = True

        # 4) 즉시 브리핑 전송/업데이트
        await self.trigger_briefing_update(event)

    async def fetch_actual(self, event):
        # API call to source
        return await fetch_api_actual(event.id)

    def compute_impact_score(self, forecast, actual):
        diff = abs(actual - forecast)
        relative_diff = diff / (forecast if forecast else 1)

        # HIGH / MEDIUM / LOW 점수화
        if relative_diff > 0.1:
            return 90
        elif relative_diff > 0.05:
            return 60
        return 20

    async def trigger_briefing_update(self, event):
        # 브리핑 리포터에 이벤트 포함하도록 queue/flag 세팅
        await event_broker.enqueue(event)


✅ 4) 브리핑 생성 단계에서 반영

LLM 프롬프트 예시:

## 오늘 발표된 주요 경제 지표

1) {event_name}
   - 예상: {forecast_value}
   - 실제: {actual_value}
   - 차이: {delta} ({%diff})
   - 영향도: {impact_label}

이 지표는 다음과 같은 시장 반응을 유발했습니다:


템플릿은 아래처럼 인수로 제공될 수 있어:

economic_section = generate_econ_section(events_list)

✅ 5) 영향도 점수 연동

종합 Daily Briefing 점수화 로직 예시

소스	가중치
뉴스 영향도 합	40%
경제 지표 영향도	40%
기술/섹터 시그널	20%
total_score = news_score*0.4 + econ_score*0.4 + tech_score*0.2

🚀 실시간 반영 전략 (10~30초)
Checkpoint Loop

스케줄러는 UTC 기준 ± 15초 범위 체크

이벤트 있는 시각 근처 ± 15초 이내 우선 처리

발표 직후 10~30초 안에 알림/브리핑 반영

이전 구조와 같이 scheduler.py 에 이벤트 리스너만 추가:

scheduler.add_task(EconCalendarListener().loop)

🧩 시장 영향도 분류 예시

세 가지 레벨로 자동 분류:

영향 레벨	조건
HIGH	실질값이 예측치 대비 +10% 이상 차이
MEDIUM	실질값이 ±5%~10% 차이
LOW	실질값 ±5% 이내
🛠 출력 예시 (Daily Briefing)
📊 Economic Calendar Update

1) 미국 – 3Q GDP 발표
   - 예상 4.3% → 실제 2.7%
   - 영향: 📉 HIGH
   - 코멘트: GDP 둔화로 증시 변동 가능성이 커졌습니다.

2) 미국 – 실업수당 청구 건수
   - 예상 209K → 실제 198K
   - 영향: 📈 MEDIUM
   - 코멘트: 노동시장 개선 신호가 포착됨.

=> 종합 관점: GDP 악화 리스크가 오늘 증시 방향성에 가장 큰 영향.


Q1

경제 지표 데이터 중에서 시장 영향도가 높다고 판단할 수 있는 대표 지표와 그 이유는 무엇인가요?

Q2

브리핑에서 경제 캘린더 이벤트를 시각화(예: 테이블, 그래프) 방식으로 표현하려면 어떻게 설계하면 좋을까요?

Q3

경제 이벤트 기반으로 자동 트레이딩/시그널 알림까지 확장시키려면 어떤 구조/로직이 필요할까요?
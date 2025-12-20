# 🤖 AI Trading System - 프로젝트 지침서

**버전**: 1.0.0
**최종 업데이트**: 2025-11-12
**프로젝트 상태**: Phase 4 완료 (57% 진행)

---

## 📋 목차

1. [프로젝트 소개](#1-프로젝트-소개)
2. [빠른 시작](#2-빠른-시작)
3. [시스템 아키텍처](#3-시스템-아키텍처)
4. [개발 가이드](#4-개발-가이드)
5. [테스트 가이드](#5-테스트-가이드)
6. [배포 가이드](#6-배포-가이드)
7. [운영 가이드](#7-운영-가이드)
8. [트러블슈팅](#8-트러블슈팅)
9. [기여 가이드](#9-기여-가이드)
10. [FAQ](#10-faq)

---

## 1. 프로젝트 소개

### 1.1 개요

AI Trading System은 Claude API를 활용한 지능형 주식 자동매매 시스템입니다. Constitution Rules 기반의 엄격한 리스크 관리와 3개의 AI Factors를 통해 안정적이고 효율적인 거래를 실현합니다.

### 1.2 핵심 특징

- **AI 기반 의사결정**: Claude 3.5 Haiku 모델 사용
- **2-Layer Feature Store**: Redis (L1) + TimescaleDB (L2)
- **Constitution Rules**: Pre/Post-Check 기반 리스크 관리
- **3개 AI Factors**: 비정형 위험, 경영진 신뢰도, 공급망 리스크
- **Event-Driven Backtest**: 슬리피지 + 수수료 모델링
- **초저비용 운영**: 월 $0.043 (100종목 기준)

### 1.3 프로젝트 현황

```
✅ Phase 1: Feature Store              - 100% 완료
✅ Phase 2: Data Integration           - 100% 완료
✅ Phase 3: AI Trading Agent           - 100% 완료
✅ Phase 4: AI Factors & Backtest      - 100% 완료
⏳ Phase 5: Strategy Ensemble          - 대기 중
⏳ Phase 6: Smart Execution            - 대기 중
⏳ Phase 7: Production Ready           - 대기 중

전체 진행률: 4/7 Phases = 57%
```

---

## 2. 빠른 시작

### 2.1 필수 요구사항

**시스템 요구사항**:
- Python 3.11+
- Git
- Docker & Docker Compose (선택사항)
- 8GB+ RAM
- 10GB+ 디스크 공간

**API 키**:
- Anthropic Claude API Key (필수)
- NewsAPI.org API Key (선택사항)

### 2.2 설치

#### Step 1: 저장소 클론

```bash
git clone https://github.com/psh355q-ui/ai-trading-system.git
cd ai-trading-system
```

#### Step 2: 환경 변수 설정

```bash
# .env 파일 생성
cp .env.example .env

# .env 파일 편집
nano .env
```

**.env 예시**:
```bash
# Claude API
CLAUDE_API_KEY=sk-ant-api03-your-key-here
CLAUDE_MODEL=claude-3-5-haiku-20241022
CLAUDE_TEMPERATURE=0.3

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_TTL_SECONDS=300

# TimescaleDB
TIMESCALE_HOST=localhost
TIMESCALE_PORT=5432
TIMESCALE_USER=postgres
TIMESCALE_PASSWORD=your_password
TIMESCALE_DATABASE=ai_trading

# Constitution Rules
MAX_VOLATILITY_PCT=50.0
MIN_MOMENTUM_PCT=-30.0
CONVICTION_THRESHOLD_BUY=0.7
CONVICTION_THRESHOLD_SELL=0.6

# Risk Thresholds
MAX_NON_STANDARD_RISK_CRITICAL=0.6
MAX_NON_STANDARD_RISK_HIGH=0.3
HIGH_RISK_POSITION_REDUCTION_PCT=50.0

# News API (Optional)
NEWSAPI_KEY=your_newsapi_key_here
```

#### Step 3: Python 환경 설정

```bash
# 가상환경 생성
python -m venv venv

# 가상환경 활성화 (Windows)
venv\Scripts\activate

# 가상환경 활성화 (Linux/Mac)
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt
```

#### Step 4: 데이터베이스 설정

**Docker 사용 (권장)**:
```bash
docker-compose up -d redis timescaledb
```

**수동 설치**:
```bash
# Redis 설치 및 실행
# TimescaleDB 설치 및 실행
# 자세한 내용은 공식 문서 참조
```

### 2.3 첫 실행

#### 기본 테스트

```bash
cd backend

# Feature Store 테스트
python -m pytest tests/test_feature_store.py -v

# Trading Agent 테스트
python -m pytest tests/test_trading_agent.py -v

# Cache Warmer 테스트
python tests/test_cache_warmer.py
```

#### 단일 종목 분석

```python
import asyncio
from ai.trading_agent import TradingAgent

async def analyze_stock():
    agent = TradingAgent()
    decision = await agent.analyze('AAPL')

    print(f"Action: {decision.action}")
    print(f"Conviction: {decision.conviction:.2f}")
    print(f"Reasoning: {decision.reasoning}")
    print(f"Position Size: {decision.position_size}%")

asyncio.run(analyze_stock())
```

---

## 3. 시스템 아키텍처

### 3.1 전체 구조

```
┌─────────────────────────────────────────────────────────┐
│                   Data Sources                           │
│   Yahoo Finance, NewsAPI, SEC, Alternative Data          │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│              Feature Store (2-Layer)                     │
│   L1: Redis (< 5ms) | L2: TimescaleDB (< 100ms)        │
│   - Standard Features (ret, vol, mom)                    │
│   - AI Factors (risk, credibility, supply chain)         │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│               AI Trading Agent                           │
│   Pre-Check → Claude AI → Post-Check                     │
│   Constitution Rules + Risk Management                   │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│              Decision Execution                          │
│   Portfolio Manager → Order Management → Execution       │
└─────────────────────────────────────────────────────────┘
```

### 3.2 핵심 컴포넌트

#### Feature Store

**파일**: `backend/data/feature_store/store.py`

**기능**:
- 2-Layer 캐싱 (Redis L1 + TimescaleDB L2)
- 표준 Feature 계산 (ret_5d, ret_20d, vol_20d, mom_20d)
- AI Factor 통합 (risk, credibility, supply_chain)

**성능**:
- Cache Hit: < 5ms (Redis)
- Cache Miss: < 100ms (TimescaleDB)
- Hit Rate: 95%+ (Cache Warming 후)

#### Trading Agent

**파일**: `backend/ai/trading_agent.py`

**의사결정 흐름**:
1. **Feature 조회**: Feature Store에서 데이터 가져오기
2. **Pre-Check**: Constitution Rules 적용
   - 변동성 > 50% → HOLD
   - 모멘텀 < -30% → HOLD
   - CRITICAL 리스크 ≥ 0.6 → HOLD
3. **AI 분석**: Claude API 호출
4. **Post-Check**: 결과 검증 및 조정
   - Conviction < 70% (BUY) → HOLD
   - Conviction < 60% (SELL) → HOLD
   - HIGH 리스크 0.3~0.6 → 포지션 50% 축소

#### AI Factors

**1. 비정형 위험 팩터** (`backend/data/features/non_standard_risk.py`)
- 6개 카테고리: LEGAL, REGULATORY, OPERATIONAL, LABOR, GOVERNANCE, REPUTATION
- 뉴스 기반 리스크 평가
- 비용: $0/월

**2. 경영진 신뢰도** (`backend/data/features/management_credibility.py`)
- 5개 구성 요소: CEO 재임, 센티먼트, 보상, 내부자거래, 이사회
- Claude API 센티먼트 분석
- 비용: $0.043/월

**3. 공급망 리스크** (`backend/data/features/supply_chain_risk.py`)
- 재귀 분석 (max depth 3)
- 4개 요소: Direct, Supplier, Customer, Geographic
- 30일 캐싱
- 비용: $0/월

---

## 4. 개발 가이드

### 4.1 프로젝트 구조

```
ai-trading-system/
├── backend/
│   ├── ai/                          # AI 모듈
│   │   ├── claude_client.py         # Claude API 클라이언트
│   │   ├── trading_agent.py         # Trading Agent 핵심
│   │   └── model_comparison.py      # A/B 테스트
│   │
│   ├── data/                        # 데이터 레이어
│   │   ├── feature_store/           # Feature Store
│   │   │   ├── store.py             # 메인 스토어
│   │   │   ├── cache_layer.py       # 캐시 레이어
│   │   │   └── cache_warmer.py      # Cache Warming
│   │   │
│   │   └── features/                # Feature 계산
│   │       ├── non_standard_risk.py # 비정형 위험
│   │       ├── management_credibility.py
│   │       ├── supply_chain_risk.py
│   │       └── news_collector.py    # 뉴스 수집
│   │
│   ├── backtesting/                 # 백테스트
│   │   ├── backtest_engine.py       # Event-driven 엔진
│   │   └── engine.py                # 레거시
│   │
│   ├── tests/                       # 테스트
│   │   ├── test_trading_agent.py
│   │   ├── test_feature_store.py
│   │   ├── test_cache_warmer.py
│   │   └── test_risk_integration.py
│   │
│   ├── config.py                    # 설정
│   └── main.py                      # 메인 엔트리포인트
│
├── scripts/                         # 유틸리티 스크립트
│   ├── warm_cache.py                # Cache warming
│   └── run_backtest.py              # 백테스트 실행
│
├── docs/                            # 문서
├── .env.example                     # 환경변수 예시
├── requirements.txt                 # Python 의존성
├── docker-compose.yml               # Docker 설정
├── README.md                        # 프로젝트 소개
├── MASTER_GUIDE.md                  # 기술 가이드
└── PROJECT_GUIDE.md                 # 이 문서
```

### 4.2 코딩 컨벤션

#### Python 스타일

**PEP 8 준수**:
```python
# Good
def calculate_sharpe_ratio(returns: List[float], risk_free_rate: float = 0.0) -> float:
    """
    Calculate Sharpe Ratio.

    Args:
        returns: List of period returns
        risk_free_rate: Risk-free rate (default: 0.0)

    Returns:
        Sharpe Ratio (annualized)
    """
    excess_returns = [r - risk_free_rate for r in returns]
    return (np.mean(excess_returns) / np.std(excess_returns)) * np.sqrt(252)

# Bad
def CalcSharpe(ret,rf=0):
    er=ret-rf
    return np.mean(er)/np.std(er)*np.sqrt(252)
```

#### Type Hints 사용

```python
from typing import Dict, List, Optional
from datetime import datetime

async def get_features(
    ticker: str,
    as_of_date: datetime,
    feature_names: Optional[List[str]] = None
) -> Dict[str, float]:
    """Get features for a ticker."""
    pass
```

#### Docstring 형식

```python
def analyze_stock(ticker: str) -> TradingDecision:
    """
    Analyze a stock and make trading decision.

    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL')

    Returns:
        TradingDecision with action, conviction, reasoning

    Raises:
        ValueError: If ticker is invalid
        APIError: If Claude API fails

    Example:
        >>> decision = await analyze_stock('AAPL')
        >>> print(decision.action)
        'BUY'
    """
    pass
```

### 4.3 새로운 Feature 추가

#### Step 1: Feature 클래스 작성

```python
# backend/data/features/my_feature.py

import logging
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class MyFeatureCalculator:
    """My custom feature calculator."""

    def __init__(self):
        """Initialize calculator."""
        self.cache = {}
        logger.info("MyFeatureCalculator initialized")

    async def calculate(
        self,
        ticker: str,
        as_of_date: datetime
    ) -> Dict[str, float]:
        """
        Calculate custom feature.

        Args:
            ticker: Stock ticker
            as_of_date: Calculation date

        Returns:
            Dict with feature values
        """
        try:
            # Your calculation logic here
            result = {
                "my_feature_score": 0.5,
                "my_feature_level": "MODERATE",
            }

            logger.info(f"Calculated my_feature for {ticker}: {result}")
            return result

        except Exception as e:
            logger.error(f"Error calculating my_feature for {ticker}: {e}")
            return {}
```

#### Step 2: Feature Store 통합

```python
# backend/data/features/my_feature_integration.py

from data.feature_store.store import FeatureStore
from data.features.my_feature import MyFeatureCalculator

# Feature Store의 get_features 메서드에 추가
# 또는 별도 메서드로 구현
```

#### Step 3: 테스트 작성

```python
# backend/tests/test_my_feature.py

import pytest
from datetime import datetime
from data.features.my_feature import MyFeatureCalculator


@pytest.mark.asyncio
async def test_my_feature_calculation():
    """Test my feature calculation."""
    calculator = MyFeatureCalculator()

    result = await calculator.calculate(
        ticker="AAPL",
        as_of_date=datetime.now()
    )

    assert "my_feature_score" in result
    assert 0.0 <= result["my_feature_score"] <= 1.0


@pytest.mark.asyncio
async def test_my_feature_error_handling():
    """Test error handling."""
    calculator = MyFeatureCalculator()

    # Test with invalid ticker
    result = await calculator.calculate(
        ticker="INVALID",
        as_of_date=datetime.now()
    )

    assert result == {}
```

### 4.4 Git 워크플로우

#### 브랜치 전략

```
main (master)           # 프로덕션 브랜치
  ├── develop           # 개발 브랜치
  │   ├── feature/*     # 새 기능
  │   ├── bugfix/*      # 버그 수정
  │   └── hotfix/*      # 긴급 수정
  └── release/*         # 릴리스 준비
```

#### 커밋 메시지 형식

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Type**:
- `feat`: 새 기능
- `fix`: 버그 수정
- `docs`: 문서 변경
- `style`: 코드 포맷팅
- `refactor`: 리팩토링
- `test`: 테스트 추가/수정
- `chore`: 빌드/설정 변경

**예시**:
```
feat(trading-agent): Add pre-check for CRITICAL risk

Implement automatic filtering for stocks with non-standard
risk >= 0.6 to save AI API costs.

- Add max_non_standard_risk_critical config (default: 0.6)
- Update pre-check logic in analyze() method
- Add test cases for risk filtering

Closes #42
```

---

## 5. 테스트 가이드

### 5.1 테스트 실행

#### 전체 테스트

```bash
# 모든 테스트 실행
pytest

# 상세 출력
pytest -v

# 특정 파일만
pytest tests/test_trading_agent.py

# 특정 테스트만
pytest tests/test_trading_agent.py::test_pre_check_volatility

# Coverage 리포트
pytest --cov=backend --cov-report=html
```

#### 개별 컴포넌트 테스트

```bash
# Feature Store
python tests/test_feature_store.py

# Trading Agent
python tests/test_trading_agent.py

# Cache Warmer
python tests/test_cache_warmer.py

# Risk Integration
python tests/test_risk_integration.py

# Backtest Engine
python tests/test_backtest_simple.py
```

### 5.2 Mock 데이터 사용

대부분의 테스트는 실제 API 호출 없이 Mock 데이터를 사용합니다:

```python
class MockFeatureStore:
    """Mock Feature Store for testing."""

    async def get_features(self, ticker, as_of_date):
        return {
            "ret_5d": 0.02,
            "ret_20d": 0.05,
            "vol_20d": 0.15,
            "mom_20d": 0.05,
            "non_standard_risk_score": 0.05,
            "management_credibility": 0.7,
            "supply_chain_risk": 0.2,
        }
```

### 5.3 통합 테스트

실제 API를 사용한 통합 테스트:

```bash
# 환경변수 설정 필요
export CLAUDE_API_KEY=your_key_here
export REDIS_URL=redis://localhost:6379/0

# 통합 테스트 실행
pytest tests/integration/ -v
```

---

## 6. 배포 가이드

### 6.1 Docker 배포

#### docker-compose.yml

```yaml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  timescaledb:
    image: timescale/timescaledb:latest-pg15
    environment:
      POSTGRES_PASSWORD: ${TIMESCALE_PASSWORD}
      POSTGRES_DB: ai_trading
    ports:
      - "5432:5432"
    volumes:
      - timescale_data:/var/lib/postgresql/data

  backend:
    build: .
    depends_on:
      - redis
      - timescaledb
    environment:
      CLAUDE_API_KEY: ${CLAUDE_API_KEY}
      REDIS_URL: redis://redis:6379/0
      TIMESCALE_HOST: timescaledb
    volumes:
      - ./backend:/app/backend
    command: python backend/main.py

volumes:
  redis_data:
  timescale_data:
```

#### 배포 명령어

```bash
# 빌드 및 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f backend

# 중지
docker-compose down

# 완전 제거 (볼륨 포함)
docker-compose down -v
```

### 6.2 NAS 배포 (Synology)

#### 파일 전송

```bash
# rsync 사용
rsync -avz --exclude 'venv' --exclude '__pycache__' \
  backend/ admin@192.168.50.148:/volume1/docker/ai-trading-system/backend/

# scp 사용
scp -r backend admin@192.168.50.148:/volume1/docker/ai-trading-system/
```

#### Cron 작업 설정

```bash
# Cache warming (매일 9:00 AM)
0 9 * * 1-5 cd /volume1/docker/ai-trading-system && docker-compose exec -T backend python scripts/warm_cache.py

# Daily backtest (매일 6:00 PM)
0 18 * * 1-5 cd /volume1/docker/ai-trading-system && docker-compose exec -T backend python scripts/run_backtest.py
```

---

## 7. 운영 가이드

### 7.1 일일 체크리스트

**오전 (9:00 AM)**:
- [ ] Cache Warming 실행 확인
- [ ] Redis/TimescaleDB 상태 확인
- [ ] 전일 거래 로그 검토

**오후 (3:00 PM - 장 마감 후)**:
- [ ] Trading 결과 검토
- [ ] 포트폴리오 성과 분석
- [ ] 에러 로그 확인

**저녁 (6:00 PM)**:
- [ ] 일일 백테스트 실행
- [ ] 메트릭 리뷰
- [ ] 다음날 Watchlist 업데이트

### 7.2 모니터링

#### 주요 메트릭

**시스템 메트릭**:
- Redis 메모리 사용률
- TimescaleDB 디스크 사용률
- API 호출 횟수 및 비용
- Cache Hit Rate

**트레이딩 메트릭**:
- 일일 수익률
- Sharpe Ratio
- Max Drawdown
- Win Rate

#### 로그 확인

```bash
# Backend 로그
tail -f logs/backend.log

# Trading 로그
tail -f logs/trading.log

# Error 로그만
grep ERROR logs/backend.log

# 특정 ticker 로그
grep "AAPL" logs/trading.log
```

### 7.3 백업

#### 데이터베이스 백업

```bash
# TimescaleDB 백업
docker-compose exec timescaledb pg_dump -U postgres ai_trading > backup_$(date +%Y%m%d).sql

# 복원
docker-compose exec -T timescaledb psql -U postgres ai_trading < backup_20251112.sql
```

#### 설정 파일 백업

```bash
# .env 파일 (주의: 민감 정보 포함)
cp .env .env.backup.$(date +%Y%m%d)

# 전체 프로젝트 백업 (rsync)
rsync -avz ai-trading-system/ /backup/ai-trading-system-$(date +%Y%m%d)/
```

---

## 8. 트러블슈팅

### 8.1 일반적인 문제

#### Redis 연결 실패

**증상**:
```
redis.exceptions.ConnectionError: Error connecting to Redis
```

**해결**:
```bash
# Redis 상태 확인
docker-compose ps redis

# Redis 재시작
docker-compose restart redis

# 연결 테스트
redis-cli ping
# 응답: PONG
```

#### Claude API 오류

**증상**:
```
anthropic.APIError: rate_limit_error
```

**해결**:
1. API 키 확인: `.env` 파일의 `CLAUDE_API_KEY` 검증
2. Rate Limit 확인: Anthropic Console에서 사용량 확인
3. 재시도 로직 확인: `claude_client.py`의 `max_retries` 설정

#### Feature Store 캐시 미스

**증상**:
- 느린 응답 시간
- Cache Hit Rate < 80%

**해결**:
```bash
# Cache Warming 실행
python scripts/warm_cache.py

# Redis 캐시 확인
redis-cli
> KEYS feature:*
> GET feature:AAPL:20251112
```

### 8.2 성능 문제

#### 느린 Trading Agent

**원인**:
1. Feature Store 캐시 미스
2. Claude API 응답 지연
3. 네트워크 지연

**해결**:
1. Cache Warming 스케줄 확인
2. `CLAUDE_TEMPERATURE` 낮추기 (0.3 → 0.1)
3. Timeout 설정 조정

#### 높은 메모리 사용

**원인**:
- Redis 메모리 부족
- Feature Store 메모리 누수

**해결**:
```bash
# Redis 메모리 확인
redis-cli INFO memory

# Redis 메모리 정리 (주의!)
redis-cli FLUSHDB

# Python 메모리 프로파일링
python -m memory_profiler backend/main.py
```

---

## 9. 기여 가이드

### 9.1 기여 방법

1. **Fork** 저장소
2. **Feature 브랜치** 생성 (`git checkout -b feature/amazing-feature`)
3. **변경사항 커밋** (`git commit -m 'Add amazing feature'`)
4. **브랜치에 Push** (`git push origin feature/amazing-feature`)
5. **Pull Request** 생성

### 9.2 Pull Request 가이드

#### PR 제목

```
[Type] Brief description

예시:
[Feature] Add dynamic position sizing based on volatility
[Fix] Correct Sharpe Ratio calculation in backtest engine
[Docs] Update README with Phase 5 information
```

#### PR 설명 템플릿

```markdown
## 변경 사항 요약
<!-- 무엇을 변경했는지 간략히 설명 -->

## 변경 이유
<!-- 왜 이 변경이 필요한지 설명 -->

## 테스트
<!-- 어떻게 테스트했는지 설명 -->
- [ ] 단위 테스트 추가
- [ ] 통합 테스트 통과
- [ ] 수동 테스트 완료

## 체크리스트
- [ ] 코드가 PEP 8 스타일 가이드를 따름
- [ ] Docstring 추가됨
- [ ] 테스트 추가됨
- [ ] 문서 업데이트됨 (필요시)

## 관련 이슈
Closes #123
```

### 9.3 코드 리뷰 기준

**필수 확인사항**:
- [ ] 기능이 의도대로 작동하는가?
- [ ] 테스트가 충분한가?
- [ ] 코드가 읽기 쉬운가?
- [ ] 문서화가 되어있는가?
- [ ] 기존 기능을 깨뜨리지 않는가?

**선택 확인사항**:
- [ ] 성능이 개선되었는가?
- [ ] 보안 이슈가 없는가?
- [ ] 에러 처리가 적절한가?

---

## 10. FAQ

### Q1: Phase 5는 언제 시작하나요?

A: Phase 4가 완료되어 Phase 5 (Strategy Ensemble) 진행 준비가 되었습니다. 구체적인 일정은 프로젝트 로드맵을 참고하세요.

### Q2: 실제 거래에 바로 사용할 수 있나요?

A: 아니요. 현재는 백테스트와 시뮬레이션 단계입니다. 실제 거래는 Phase 7 (Production Ready) 완료 후 충분한 검증을 거쳐야 합니다.

### Q3: 운영 비용이 정말 월 $0.043인가요?

A: 100종목, 일 1회 분석 기준입니다. 실제 비용은 다음에 따라 달라집니다:
- 분석 빈도
- 종목 수
- AI Factor 사용 여부
- Cache Hit Rate

### Q4: Haiku vs Sonnet, 정말 Haiku가 나은가요?

A: Cost-Adjusted Sharpe 기준으로 Haiku가 3.4배 더 효율적입니다. 하지만:
- Sonnet이 절대 성능은 약간 우수 (Sharpe +13.8%)
- 거래 빈도가 낮다면 Sonnet도 고려 가능
- A/B 테스트로 실전 검증 권장

### Q5: NAS 없이 로컬에서만 실행 가능한가요?

A: 예. Redis와 TimescaleDB를 로컬에 설치하면 됩니다:
```bash
# Docker로 간단히 실행
docker-compose up -d redis timescaledb
```

### Q6: 한국 주식도 지원하나요?

A: 현재는 미국 주식만 지원합니다. 한국 주식 지원은:
- Yahoo Finance API 확인 필요
- DART API 통합 필요
- Feature 계산 로직 조정 필요

### Q7: 백테스트 결과를 신뢰할 수 있나요?

A: 백테스트는 다음을 포함합니다:
- 슬리피지 (1 bps)
- 수수료 (0.015%)
- Look-ahead Bias 방지
- Event-driven 시뮬레이션

하지만 과거 성과가 미래를 보장하지 않습니다.

### Q8: Constitution Rules를 수정하려면?

A: `backend/config.py` 또는 `.env` 파일 수정:
```bash
# .env
MAX_VOLATILITY_PCT=60.0  # 기본값: 50.0
CONVICTION_THRESHOLD_BUY=0.75  # 기본값: 0.7
```

### Q9: 새로운 AI Factor를 추가하려면?

A: [4.3 새로운 Feature 추가](#43-새로운-feature-추가) 섹션 참고

### Q10: 문제가 해결되지 않으면?

A: 다음 순서로 시도하세요:
1. [트러블슈팅](#8-트러블슈팅) 섹션 확인
2. GitHub Issues 검색
3. 새 Issue 생성 (재현 방법 포함)
4. Discord/Slack 커뮤니티 질문

---

## 📞 지원 및 연락

- **GitHub**: [https://github.com/psh355q-ui/ai-trading-system](https://github.com/psh355q-ui/ai-trading-system)
- **Issues**: [GitHub Issues](https://github.com/psh355q-ui/ai-trading-system/issues)
- **Documentation**: [MASTER_GUIDE.md](MASTER_GUIDE.md)

---

## 📜 라이선스

MIT License - 자세한 내용은 [LICENSE](LICENSE) 파일 참고

---

## ⚠️ 면책 조항

> **경고**: 이 시스템은 투자 자문이 아닙니다.
>
> - AI는 틀릴 수 있습니다
> - 모든 투자 결정의 책임은 사용자에게 있습니다
> - 투자 손실에 대해 개발자는 책임지지 않습니다
> - 반드시 시뮬레이션 모드로 충분히 테스트한 후 사용하세요

---

**프로젝트 지침서 v1.0.0**
**최종 업데이트**: 2025-11-12

*"In investing, what is comfortable is rarely profitable."*
*- Robert Arnott*

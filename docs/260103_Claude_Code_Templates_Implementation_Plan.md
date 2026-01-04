# Claude Code Templates 통합 구현 계획

**작성일**: 2026-01-03
**기준일**: 2026-01-02 작업 완료 후
**우선순위**: P1 (High - Development Efficiency)
**상태**: 📋 Ready for Implementation

---

## Executive Summary

Claude Code Templates에서 선정한 3가지 컴포넌트를 AI Trading System에 통합하여 개발 효율성, 코드 품질, 성능을 개선합니다.

**선정된 컴포넌트:**
1. `/generate-tests` Command - 테스트 자동화 (우선순위 1)
2. React Performance Optimizer Agent - 프론트엔드 최적화 (우선순위 2)
3. Auto Git Hooks - 문서화 자동화 (우선순위 3)

**참고**:
- Database Architect Agent 계획은 별도 문서: [260102_Database_Optimization_Plan.md](260102_Database_Optimization_Plan.md)
- **Database Optimization Phase 1 완료** (2026-01-02): [Work_Log_20260102.md](Work_Log_20260102.md)
  - 복합 인덱스 5개 추가 ✅
  - N+1 쿼리 패턴 제거 ✅
  - TTL 캐싱 구현 ✅
  - War Room MVP: 12.76초 (목표 15초 이내 달성) ✅

---

## 현재 상태 분석 (2026-01-03 기준)

### 1. 테스트 인프라 현황

**기존 테스트:**
- 총 57개 테스트 파일 (9,132 줄)
- 195개 테스트 함수
- 프레임워크: pytest 7.4.0+ (asyncio, coverage, benchmark 지원)
- 커버리지 요구사항: 80% 이상

**테스트 커버리지 갭:**
- **Routers**: 53개 중 7개만 테스트 (13% 커버리지) ❌
  - `data_backfill_router.py` (675줄) - 테스트 없음
  - `kill_switch_router.py` (신규, 2026-01-02) - 테스트 필요
  - 46개 라우터 테스트 누락
- **Repository**: 1,512줄 - 테스트 전무 ❌
- **War Room MVP**: 부분적 커버리지 (3/5 agent 테스트)
- **Kill Switch**: 기본 테스트만 존재 (통합 테스트 필요)

**테스트 패턴:**
- Integration-heavy (느린 테스트)
- Unit 테스트 부족 (빠른 격리 테스트)
- Fixture 공유 제한적 (conftest.py에 3개만)

---

### 2. 프론트엔드 성능 현황

**대형 컴포넌트 (> 300줄):**
- `DataBackfill.tsx`: 917줄 (5개 섹션 통합) ❌
- `BacktestDashboard.tsx`: 896줄 (복잡한 차트 렌더링) ❌
- `RssFeedManagement.tsx`: 847줄 (다중 폼) ❌
- 총 10개 컴포넌트가 300줄 이상

**번들 이슈:**
- `antd`: 2,500KB (트리 쉐이킹 없음)
- `recharts`: 1,300KB (102개 차트 인스턴스)
- `date-fns` + `dayjs` 중복 (40KB vs 15KB)
- 코드 스플리팅 미구성
- Lazy loading 없음

**React 최적화 부재:**
- `useMemo/useCallback` 사용: 2개 파일만 ✅
- `React.memo` 미사용: 대부분 컴포넌트 ❌
- Key binding: 일부 index 사용 (잘못된 패턴) ❌

**API 폴링 과다:**
- 5초 간격: 5개 쿼리 (720 calls/hour per query) ❌
- 10초 간격: 6개 쿼리 (360 calls/hour)
- WebSocket 미사용

---

### 3. Git 워크플로우 현황

**Hooks 상태:**
- `.git/hooks/`: 샘플만 존재, 활성 hooks 없음 ❌
- `.husky/`: 미구성 ❌
- `commitlint`: 미구성 ❌
- Pre-commit 검증 없음 ❌

**문서화 패턴:**
- 총 380+ .md 파일 (docs/)
- 네이밍 불일치: `YYYYMMDD_*.md` vs 설명형
- 중복 문서: 같은 날짜에 3-4개 요약 파일
- **최근 추가**: Work_Log_20260102.md, Shadow_Trading_Week1_Report.md

**커밋 메시지:**
- Conventional commits: 35% 준수 (docs:, feat:, fix:)
- 65%는 prefix 없음 ❌
- 단일 작성자 (psh355q-ui)
- 총 138+ 커밋

**자동화 현황:**
- GitHub Actions: 기본 CI만 (테스트 실행 안 함) ❌
- 자동 커밋 없음
- 문서 정리 자동화 없음

---

## Component 1: `/generate-tests` Command (테스트 자동화)

### 목표
- 테스트 커버리지 60% → 90% 향상
- 46개 미테스트 라우터에 대한 테스트 자동 생성
- Repository 패턴 단위 테스트 추가
- War Room MVP agent 테스트 완성
- **Kill Switch 통합 테스트 추가** (2026-01-02 신규)

### 설치 방법
```bash
npx claude-code-templates@latest --command generate-tests --yes
```

### 적용 전략

#### Phase 1A: High Priority - Data Backfill Router 테스트 생성

**대상 파일**: `backend/api/data_backfill_router.py` (675줄)

**생성할 테스트**: `backend/tests/test_data_backfill_router.py`

**테스트 범위:**
1. **POST /prices** 엔드포인트
   - 정상 요청 (200 OK)
   - Yahoo Finance 제한 검증 (1m: 7일, 1h: 730일) - **2026-01-02 추가 기능**
   - 잘못된 간격 (400 Bad Request)
   - 잘못된 티커 (400 Bad Request)

2. **POST /news** 엔드포인트
   - 정상 요청
   - RSS 소스 검증
   - 날짜 범위 검증

3. **GET /jobs/{job_id}** 엔드포인트
   - 존재하는 작업 조회
   - 존재하지 않는 작업 (404)
   - 작업 상태 전환 검증

**예상 코드:**
```python
# backend/tests/test_data_backfill_router.py
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

class TestPriceBackfill:
    """주가 백필 API 테스트"""

    def test_price_backfill_success(self):
        """정상 주가 백필 요청"""
        response = client.post("/api/backfill/prices", json={
            "tickers": ["AAPL", "MSFT"],
            "start_date": "2025-12-01",
            "end_date": "2026-01-01",
            "interval": "1d"
        })
        assert response.status_code == 200
        assert "job_id" in response.json()

    def test_price_backfill_1h_limit_exceeded(self):
        """1시간 봉 730일 제한 검증 (2026-01-02 추가 기능)"""
        response = client.post("/api/backfill/prices", json={
            "tickers": ["AAPL"],
            "start_date": "2024-01-01",
            "end_date": "2026-01-02",
            "interval": "1h"
        })
        assert response.status_code == 400
        assert "730 days" in response.json()["detail"]

    def test_price_backfill_1m_limit_exceeded(self):
        """1분 봉 7일 제한 검증"""
        response = client.post("/api/backfill/prices", json={
            "tickers": ["AAPL"],
            "start_date": "2026-01-01",
            "end_date": "2026-01-10",
            "interval": "1m"
        })
        assert response.status_code == 400
        assert "7 days" in response.json()["detail"]
```

**예상 소요**: 2시간
**예상 효과**: 커버리지 +5%, 백필 기능 안정성 확보

---

#### Phase 1B: High Priority - Kill Switch 통합 테스트 (신규)

**대상 파일**: `backend/execution/kill_switch.py` (319줄), `backend/routers/kill_switch_router.py`

**생성할 테스트**: `backend/tests/test_kill_switch_integration.py`

**테스트 범위:**
1. **7가지 트리거 조건 검증**
   - Daily Loss (5% 손실)
   - Max Drawdown (10% 손실)
   - API Error (3회 연속)
   - Position Concentration (단일 종목 30%)
   - Stale Data (가격 5분 지연)
   - Manual Trigger
   - Daily Trade Limit (20회 초과)

2. **War Room MVP 통합 테스트**
   - Kill Switch 활성화 시 거래 차단 검증
   - Shadow Trading 통합 검증
   - Telegram 알림 전송 검증

3. **Reset 로직 테스트**
   - 수동 Override 코드 검증
   - Reset 후 정상 거래 재개 검증

**예상 코드:**
```python
# backend/tests/test_kill_switch_integration.py
import pytest
from backend.execution.kill_switch import KillSwitch, TriggerType
from backend.execution.shadow_trading import ShadowTradingEngine

class TestKillSwitchIntegration:
    """Kill Switch 통합 테스트"""

    @pytest.fixture
    def kill_switch(self):
        """Kill Switch 인스턴스"""
        return KillSwitch()

    @pytest.fixture
    def shadow_trading(self, kill_switch):
        """Shadow Trading Engine with Kill Switch"""
        engine = ShadowTradingEngine()
        engine.kill_switch = kill_switch
        return engine

    def test_daily_loss_trigger(self, kill_switch):
        """일일 5% 손실 시 Kill Switch 발동"""
        trading_state = {
            'daily_pnl': -5000,  # -5%
            'total_capital': 100000
        }

        result = kill_switch.check_triggers(trading_state)

        assert result['triggered'] == True
        assert result['reason'] == TriggerType.DAILY_LOSS.value
        assert kill_switch.is_active == True

    def test_shadow_trading_blocked_when_active(self, shadow_trading, kill_switch):
        """Kill Switch 활성화 시 거래 차단"""
        kill_switch.trigger(TriggerType.MANUAL, {})

        with pytest.raises(Exception) as exc_info:
            shadow_trading.execute_trade('AAPL', 'BUY', 100, 150.0)

        assert "Trading Halted" in str(exc_info.value)

    def test_reset_with_override_code(self, kill_switch):
        """Override 코드로 정상 해제"""
        kill_switch.trigger(TriggerType.MANUAL, {})

        result = kill_switch.reset(override_code='OVERRIDE_2026')

        assert result == True
        assert kill_switch.is_active == False
        assert kill_switch.can_trade() == True
```

**예상 소요**: 3시간
**예상 효과**: Kill Switch 안정성 보장, Shadow Trading 통합 검증

---

#### Phase 1C: Medium Priority - Repository 단위 테스트

**대상 파일**: `backend/database/repository.py` (1,512줄)

**생성할 테스트**: `backend/tests/test_repository.py`

**테스트 전략:**
- Mock database session 사용
- SQLAlchemy ORM 동작 검증
- N+1 쿼리 방지 검증
- **ON CONFLICT 로직 검증** (2026-01-02 추가 기능)
- **TTL 캐싱 검증** (2026-01-02 추가 기능)

**테스트 범위:**
1. **NewsRepository**
   - `add_article()` - 중복 체크 동작 (ON CONFLICT)
   - `get_recent_articles()` - 날짜 범위 쿼리 + 캐싱
   - `get_article_by_id()` - 단일 조회

2. **SignalRepository**
   - `create_signal()` - 신호 생성
   - `get_signals_by_ticker()` - 티커별 조회
   - `update_signal_performance()` - 성과 업데이트

3. **StockRepository**
   - `add_price_data()` - 가격 데이터 추가
   - `get_latest_price()` - 최신 가격 조회

**Mock 패턴:**
```python
# backend/tests/test_repository.py
import pytest
from unittest.mock import MagicMock, patch
from backend.database.repository import NewsRepository
from backend.database.models import NewsArticle

class TestNewsRepository:
    """NewsRepository 단위 테스트"""

    @pytest.fixture
    def mock_session(self):
        """Mock SQLAlchemy session"""
        session = MagicMock()
        return session

    @pytest.fixture
    def news_repo(self, mock_session):
        """NewsRepository 인스턴스"""
        return NewsRepository(mock_session)

    def test_add_article_on_conflict(self, news_repo, mock_session):
        """ON CONFLICT DO NOTHING 동작 검증 (2026-01-02 추가)"""
        article = NewsArticle(
            title="Test",
            url="http://test.com",
            content_hash="hash123"
        )

        # ON CONFLICT 사용 시 execute 호출 검증
        news_repo.add_article(article)

        # execute가 INSERT ... ON CONFLICT를 실행했는지 확인
        mock_session.execute.assert_called_once()

    @patch('backend.database.repository._query_cache', {})
    def test_get_recent_articles_caching(self, news_repo, mock_session):
        """TTL 캐싱 동작 검증 (2026-01-02 추가)"""
        # First call - DB query
        articles1 = news_repo.get_recent_articles(hours=24)
        query_count_1 = mock_session.query.call_count

        # Second call within TTL - cached
        articles2 = news_repo.get_recent_articles(hours=24)
        query_count_2 = mock_session.query.call_count

        # 캐시 히트 시 쿼리 호출 없음
        assert query_count_2 == query_count_1
```

**예상 소요**: 4시간
**예상 효과**: 커버리지 +10%, Repository 안정성 확보, 최적화 검증

---

#### Phase 1D: Low Priority - War Room MVP Agent 테스트 완성

**대상 파일:**
- `backend/ai/mvp/pm_agent_mvp.py`
- `backend/ai/mvp/analyst_agent_mvp.py`
- `backend/ai/mvp/risk_agent_mvp.py`

**생성할 테스트:**
- `backend/tests/test_pm_agent_mvp.py`
- `backend/tests/test_analyst_agent_mvp.py`
- `backend/tests/test_risk_agent_mvp.py`

**테스트 범위:**
- Agent 초기화
- analyze() 메서드 동작
- 출력 JSON 스키마 검증
- Hard rules 검증 (PM Agent)

**예상 소요**: 3시간
**예상 효과**: 커버리지 +5%, War Room MVP 안정성

---

### 구현 로드맵 (테스트 자동화)

**Week 1: 핵심 테스트 생성**
- [ ] `/generate-tests` 설치 및 구성
- [ ] Data Backfill Router 테스트 생성 (Yahoo Finance 제한 포함)
- [ ] Kill Switch 통합 테스트 생성
- [ ] 테스트 실행 및 검증
- [ ] CI에 테스트 추가

**Week 2: Repository 테스트**
- [ ] Mock session 설정
- [ ] NewsRepository 테스트 (ON CONFLICT, 캐싱 검증)
- [ ] SignalRepository 테스트
- [ ] 커버리지 측정

**Week 3: Agent 테스트 완성**
- [ ] PM Agent 테스트
- [ ] Analyst Agent 테스트
- [ ] Risk Agent 테스트
- [ ] 전체 커버리지 검증

**예상 효과:**
- 테스트 커버리지: 60% → 90%
- 버그 발견 시간: 1일 → 1시간
- 리그레션 방지 100%
- Kill Switch 안정성 보장

---

## Component 2: React Performance Optimizer (프론트엔드 최적화)

### 목표
- 프론트엔드 로딩 시간 30% 감소
- 번들 크기 20% 감소
- War Room/News 페이지 렌더링 성능 개선
- API 폴링 최적화 (720 calls/hour → 120 calls/hour)

### 설치 방법
```bash
npx claude-code-templates@latest --agent react-performance-optimizer --yes
```

### 적용 전략

#### Phase 2A: Critical - 번들 크기 최적화

**1. 중복 라이브러리 제거**

**파일**: `frontend/package.json`

**변경:**
```diff
- "date-fns": "^2.30.0",      # 40KB gzipped
+ "dayjs": "^1.11.19",         # 15KB gzipped (유지)
```

**작업:**
1. `date-fns` import 찾기 (Grep)
2. `dayjs`로 변경
3. package.json에서 `date-fns` 제거
4. `npm install` 재실행

**예상 효과**: -25KB gzipped

---

**2. Ant Design 트리 쉐이킹**

**파일**: `frontend/vite.config.ts`

**추가:**
```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor-antd': ['antd'],
          'vendor-charts': ['recharts'],
          'vendor-utils': ['dayjs', 'lodash-es']
        }
      }
    }
  },
  optimizeDeps: {
    include: ['antd', 'recharts', 'dayjs']
  },
  server: {
    port: 3002,
    proxy: {
      '/api': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
    },
  },
})
```

**예상 효과**: -50KB gzipped (미사용 컴포넌트 제거)

---

#### Phase 2B: High Priority - 컴포넌트 최적화

**1. NewsAggregation.tsx 최적화**

**파일**: `frontend/src/pages/NewsAggregation.tsx` (421줄)

**변경 사항:**

```typescript
// Line 235-236: ArticleItem을 React.memo로 래핑
const ArticleItem = React.memo(({ article, onClick }: ArticleItemProps) => {
  return (
    <div onClick={() => onClick(article.id)}>
      {/* 기존 코드 */}
    </div>
  );
}, (prevProps, nextProps) => {
  // article.id가 같으면 리렌더링 스킵
  return prevProps.article.id === nextProps.article.id;
});

// Line 387: Keywords key 개선
article.tickers.map((ticker, i) => (
  <span key={`${ticker}-${i}`} className="...">  // index 대신 복합 키
    {ticker}
  </span>
))

// Line 257-319: Modal을 별도 컴포넌트로 분리
const ArticleDetailModal = React.lazy(() => import('./ArticleDetailModal'));

// Line 368-411: ArticleItem 사용 시
<ArticleItem
  key={article.id}  // 안전한 키
  article={article}
  onClick={handleArticleClick}
/>
```

**예상 소요**: 2시간
**예상 효과**: 뉴스 페이지 렌더링 50% 개선

---

**2. WarRoomCard.tsx 최적화**

**파일**: `frontend/src/components/war-room/WarRoomCard.tsx` (171줄)

**변경 사항:**

```typescript
// Line 33-76: Badge 함수를 useMemo로 최적화
const statusBadge = useMemo(() => {
  return getStatusBadge(session.status);
}, [session.status]);

const finalDecisionBadge = useMemo(() => {
  return getFinalDecisionBadge(session.final_decision);
}, [session.final_decision]);

// Line 95-104: 날짜 포맷팅 최적화
const formattedKST = useMemo(() => {
  return new Date(session.created_at).toLocaleString('ko-KR', {
    timeZone: 'Asia/Seoul',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
}, [session.created_at]);

const formattedEST = useMemo(() => {
  return new Date(session.created_at).toLocaleString('en-US', {
    timeZone: 'America/New_York',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
}, [session.created_at]);

// 전체 컴포넌트를 React.memo로 래핑
export default React.memo(WarRoomCard);
```

**예상 소요**: 1시간
**예상 효과**: War Room 카드 렌더링 60% 개선

---

#### Phase 2C: High Priority - API 폴링 최적화

**1. WebSocket으로 전환 (War Room Sessions)**

**파일**: `frontend/src/components/war-room/WarRoomList.tsx` (Line 25)

**변경 전:**
```typescript
const { data: sessions } = useQuery({
  queryKey: ['war-room-sessions'],
  queryFn: fetchSessions,
  refetchInterval: 10000,  // 10초마다 폴링
});
```

**변경 후:**
```typescript
// WebSocket 훅 생성
const useWarRoomWebSocket = () => {
  const [sessions, setSessions] = useState([]);

  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8001/ws/war-room');

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setSessions(data.sessions);
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      // Fallback to polling
    };

    return () => ws.close();
  }, []);

  return sessions;
};

// 사용
const sessions = useWarRoomWebSocket();
```

**백엔드 WebSocket 엔드포인트 추가:**
```python
# backend/api/war_room_router.py
from fastapi import WebSocket

@router.websocket("/ws/war-room")
async def war_room_websocket(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            sessions = get_active_sessions()
            await websocket.send_json({"sessions": sessions})
            await asyncio.sleep(5)  # 5초마다 업데이트
    except WebSocketDisconnect:
        pass
```

**예상 소요**: 3시간
**예상 효과**: 360 calls/hour → 0 (WebSocket으로 전환)

---

**2. Signals 폴링 간격 증가**

**파일**: `frontend/src/components/Signals.tsx` (Lines 475, 481, 487)

**변경:**
```diff
  refetchInterval: 5000,   // 5초 (720 calls/hour)
+ refetchInterval: 30000,  // 30초 (120 calls/hour)
```

**예상 효과**: 720 calls/hour → 120 calls/hour (83% 감소)

---

#### Phase 2D: Medium Priority - 코드 스플리팅

**파일**: `frontend/src/App.tsx` 또는 라우터 설정

**변경:**
```typescript
import { lazy, Suspense } from 'react';

// Before: 모든 페이지 eager loading
import DataBackfill from './pages/DataBackfill';
import BacktestDashboard from './pages/BacktestDashboard';

// After: Lazy loading
const DataBackfill = lazy(() => import('./pages/DataBackfill'));
const BacktestDashboard = lazy(() => import('./pages/BacktestDashboard'));
const RssFeedManagement = lazy(() => import('./pages/RssFeedManagement'));
const NewsAggregation = lazy(() => import('./pages/NewsAggregation'));

// Router with Suspense
<Suspense fallback={<LoadingSpinner />}>
  <Routes>
    <Route path="/backfill" element={<DataBackfill />} />
    <Route path="/backtest" element={<BacktestDashboard />} />
    {/* ... */}
  </Routes>
</Suspense>
```

**예상 효과**: 초기 번들 크기 40% 감소

---

### 구현 로드맵 (성능 최적화)

**Week 1: 번들 최적화**
- [ ] `date-fns` 제거, `dayjs` 통일
- [ ] Vite 빌드 설정 업데이트
- [ ] 번들 크기 측정 (Before/After)

**Week 2: 컴포넌트 최적화**
- [ ] NewsAggregation 최적화
- [ ] WarRoomCard 최적화
- [ ] React.memo 적용
- [ ] 렌더링 성능 측정

**Week 3: 폴링 최적화**
- [ ] War Room WebSocket 구현
- [ ] Signals 폴링 간격 증가
- [ ] 네트워크 트래픽 측정

**Week 4: 코드 스플리팅**
- [ ] 대형 페이지 lazy loading
- [ ] Suspense 구현
- [ ] 최종 번들 분석

**예상 효과:**
- 초기 로딩 시간: 3초 → 2초 (33% 개선)
- 번들 크기: 500KB → 400KB (20% 감소)
- API 호출: 1,440 calls/hour → 240 calls/hour (83% 감소)

---

## Component 3: Auto Git Hooks (문서화 자동화)

### 목표
- Conventional commits 100% 준수
- 문서 자동 커밋 및 정리
- Pre-commit 검증 (secrets, 문법 오류)
- 문서화 작업 시간 50% 감소

### 설치 방법
```bash
npx claude-code-templates@latest --hook auto-git-add --yes
npx claude-code-templates@latest --hook smart-commit --yes
```

또는 수동 구성:
```bash
npm install --save-dev husky @commitlint/cli @commitlint/config-conventional
npx husky install
npm set-script prepare "husky install"
```

### 적용 전략

#### Phase 3A: Commitlint 설정

**파일**: `.commitlintrc.json` (신규)

```json
{
  "extends": ["@commitlint/config-conventional"],
  "rules": {
    "type-enum": [2, "always", [
      "feat",
      "fix",
      "docs",
      "refactor",
      "test",
      "chore",
      "perf",
      "ci",
      "build",
      "revert"
    ]],
    "subject-case": [0],
    "body-max-line-length": [0]
  }
}
```

**Husky commit-msg hook**: `.husky/commit-msg`

```bash
#!/bin/sh
. "$(dirname "$0")/_/husky.sh"

npx --no -- commitlint --edit "$1"
```

**예상 효과**: Conventional commits 35% → 100%

---

#### Phase 3B: Pre-commit Hooks

**파일**: `.husky/pre-commit`

```bash
#!/bin/sh
. "$(dirname "$0")/_/husky.sh"

# 1. Python 린팅 (backend/)
echo "🔍 Running Python linters..."
cd backend && python -m flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics

# 2. TypeScript 체크 (frontend/)
echo "🔍 Running TypeScript check..."
cd ../frontend && npm run type-check

# 3. Secrets 검사
echo "🔒 Checking for secrets..."
if git diff --cached --name-only | xargs grep -E "(OPENAI_API_KEY|GEMINI_API_KEY|DATABASE_URL)" > /dev/null 2>&1; then
  echo "❌ ERROR: Potential secrets found in staged files!"
  echo "Please remove secrets before committing."
  exit 1
fi

# 4. 큰 파일 검사 (> 10MB)
echo "📦 Checking file sizes..."
MAX_SIZE=10485760  # 10MB in bytes
for file in $(git diff --cached --name-only); do
  if [ -f "$file" ]; then
    size=$(wc -c <"$file")
    if [ $size -gt $MAX_SIZE ]; then
      echo "❌ ERROR: File $file is larger than 10MB ($size bytes)"
      exit 1
    fi
  fi
done

echo "✅ Pre-commit checks passed!"
```

**예상 효과**: Secrets 노출 방지 100%, 코드 품질 개선

---

#### Phase 3C: 문서 자동 커밋

**전략:**
- docs/ 폴더 변경 감지
- 일일 요약 자동 커밋
- 스키마 변경 자동 커밋

**구현 방법: GitHub Actions Workflow**

**파일**: `.github/workflows/auto-docs-commit.yml` (신규)

```yaml
name: Auto Documentation Commit

on:
  push:
    paths:
      - 'docs/**/*.md'
      - 'backend/ai/skills/**/schemas/*.json'
      - 'backend/database/migrations/*.sql'

jobs:
  auto-commit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0

      - name: Check for uncommitted doc changes
        id: check
        run: |
          if git diff --quiet docs/; then
            echo "changed=false" >> $GITHUB_OUTPUT
          else
            echo "changed=true" >> $GITHUB_OUTPUT
          fi

      - name: Commit documentation
        if: steps.check.outputs.changed == 'true'
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add docs/
          git commit -m "docs: Auto-commit documentation updates"
          git push
```

**예상 효과**: 문서 커밋 자동화 100%

---

#### Phase 3D: 문서 정리 자동화

**문제**: 380+ .md 파일 중 중복/오래된 문서 다수

**해결책**: 주간 정리 스크립트

**파일**: `scripts/cleanup_docs.py` (신규)

```python
#!/usr/bin/env python3
"""
문서 정리 자동화 스크립트

- 30일 이상 된 일일 요약 → docs/archive/YYYY/MM/ 이동
- 중복 문서 감지 (같은 날짜 3개 이상)
- 빈 문서 삭제
"""
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path

DOCS_DIR = Path("docs")
ARCHIVE_DIR = DOCS_DIR / "archive"
DAYS_TO_ARCHIVE = 30

def archive_old_daily_summaries():
    """30일 이상 된 일일 요약 아카이브"""
    cutoff_date = datetime.now() - timedelta(days=DAYS_TO_ARCHIVE)

    for file in DOCS_DIR.glob("*.md"):
        # YYMMDD_*.md 형식 파싱
        if len(file.stem) >= 6 and file.stem[:6].isdigit():
            try:
                file_date = datetime.strptime(file.stem[:6], "%y%m%d")
                if file_date < cutoff_date:
                    # 아카이브 디렉토리 생성
                    year_month = file_date.strftime("%Y/%m")
                    archive_path = ARCHIVE_DIR / year_month
                    archive_path.mkdir(parents=True, exist_ok=True)

                    # 파일 이동
                    shutil.move(str(file), archive_path / file.name)
                    print(f"✅ Archived: {file.name} → {archive_path}")
            except ValueError:
                pass

def detect_duplicates():
    """같은 날짜 중복 문서 감지"""
    date_files = {}
    for file in DOCS_DIR.glob("*.md"):
        if len(file.stem) >= 6 and file.stem[:6].isdigit():
            date = file.stem[:6]
            date_files.setdefault(date, []).append(file.name)

    for date, files in date_files.items():
        if len(files) > 2:
            print(f"⚠️  Duplicates on {date}: {files}")

if __name__ == "__main__":
    archive_old_daily_summaries()
    detect_duplicates()
```

**Cron/GitHub Actions로 주간 실행:**

```yaml
# .github/workflows/weekly-docs-cleanup.yml
name: Weekly Documentation Cleanup

on:
  schedule:
    - cron: '0 0 * * 0'  # 매주 일요일 자정

jobs:
  cleanup:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Run cleanup script
        run: python scripts/cleanup_docs.py

      - name: Commit changes
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add docs/
          git commit -m "chore: Weekly documentation cleanup" || echo "No changes"
          git push
```

**예상 효과**: docs/ 폴더 유지보수 자동화, 중복 파일 50% 감소

---

### 구현 로드맵 (Git Hooks)

**Week 1: Commitlint 설정**
- [ ] `.commitlintrc.json` 생성
- [ ] Husky 설치 및 구성
- [ ] commit-msg hook 활성화
- [ ] 팀원 교육 (conventional commits)

**Week 2: Pre-commit Hooks**
- [ ] pre-commit hook 구현
- [ ] Python 린팅 통합
- [ ] Secrets 검사 추가
- [ ] 파일 크기 검사

**Week 3: 문서 자동화**
- [ ] GitHub Actions 워크플로우 구성
- [ ] 문서 자동 커밋 테스트
- [ ] 정리 스크립트 작성

**Week 4: 유지보수 자동화**
- [ ] 주간 정리 스케줄 설정
- [ ] 아카이브 구조 구축
- [ ] 중복 감지 및 알림

**예상 효과:**
- Conventional commits: 35% → 100%
- Secrets 노출: 0건 (방지)
- 문서화 시간: 50% 감소
- docs/ 폴더 크기: 30% 감소

---

## 전체 구현 일정

### Month 1: 테스트 자동화 (Component 1)
- Week 1: Data Backfill Router 테스트 + Kill Switch 통합 테스트
- Week 2: Repository 테스트 (ON CONFLICT, 캐싱 검증)
- Week 3: War Room MVP 테스트
- Week 4: CI 통합 및 검증

**예상 효과**: 커버리지 60% → 90%, Kill Switch 안정성 보장

### Month 2: 프론트엔드 최적화 (Component 2)
- Week 1: 번들 최적화
- Week 2: 컴포넌트 최적화
- Week 3: 폴링 최적화
- Week 4: 코드 스플리팅

**예상 효과**: 로딩 시간 33% 개선, API 호출 83% 감소

### Month 3: Git 자동화 (Component 3)
- Week 1: Commitlint
- Week 2: Pre-commit hooks
- Week 3: 문서 자동화
- Week 4: 유지보수 자동화

**예상 효과**: Conventional commits 100%, 문서화 시간 50% 감소

---

## 성공 기준

### 테스트 자동화
- [ ] 테스트 커버리지 > 90%
- [ ] Data Backfill Router 테스트 통과
- [ ] Kill Switch 통합 테스트 통과
- [ ] Repository 테스트 통과 (ON CONFLICT, 캐싱)
- [ ] CI에서 테스트 자동 실행

### 프론트엔드 최적화
- [ ] 초기 로딩 시간 < 2초
- [ ] 번들 크기 < 400KB
- [ ] API 호출 < 240 calls/hour
- [ ] Lighthouse 점수 > 90

### Git 자동화
- [ ] Conventional commits 100% 준수
- [ ] Secrets 노출 0건
- [ ] 문서 자동 커밋 동작
- [ ] 주간 정리 자동화 동작

---

## 리스크 및 완화 전략

### 리스크

**1. 테스트 Mock 복잡도**
- SQLAlchemy ORM mocking이 복잡할 수 있음
- **완화책**: pytest-mock, MagicMock 활용, 간단한 패턴부터 시작

**2. 프론트엔드 브레이킹 체인지**
- React.memo 적용 시 기존 동작 변경 가능
- **완화책**: 단계적 적용, 각 컴포넌트별 테스트

**3. Git Hooks 팀원 불편**
- Pre-commit 검증이 개발 속도 저하 가능
- **완화책**: `--no-verify` 옵션 안내, 합리적 검증만 유지

**4. WebSocket 인프라**
- 백엔드 WebSocket 지원 필요
- **완화책**: 폴백 메커니즘 유지, 단계적 전환

### 롤백 전략

**테스트 자동화 롤백:**
```bash
# 테스트 파일 삭제
rm backend/tests/test_data_backfill_router.py
rm backend/tests/test_repository.py
rm backend/tests/test_kill_switch_integration.py

# CI 설정 원복
git checkout .github/workflows/ci.yml
```

**프론트엔드 최적화 롤백:**
```bash
# Vite 설정 원복
git checkout frontend/vite.config.ts

# React.memo 제거
git checkout frontend/src/pages/NewsAggregation.tsx
git checkout frontend/src/components/war-room/WarRoomCard.tsx
```

**Git Hooks 롤백:**
```bash
# Husky 비활성화
npm uninstall husky @commitlint/cli
rm -rf .husky/

# GitHub Actions 워크플로우 삭제
rm .github/workflows/auto-docs-commit.yml
rm .github/workflows/weekly-docs-cleanup.yml
```

---

## 최종 권장사항

### 즉시 실행 (사용자 승인 후)

**우선순위 1: 테스트 자동화**
1. ✅ Data Backfill Router 테스트 생성 (2시간)
2. ✅ Kill Switch 통합 테스트 (3시간)
3. ✅ Repository 단위 테스트 (4시간)
4. ✅ CI 통합 (1시간)

**예상 효과**: 커버리지 즉시 +15%, 버그 조기 발견, Kill Switch 안정성

**우선순위 2: 프론트엔드 최적화**
1. ✅ `date-fns` 제거 (1시간)
2. ✅ NewsAggregation React.memo (2시간)
3. ✅ Signals 폴링 간격 증가 (30분)

**예상 효과**: 번들 -25KB, 렌더링 50% 개선, API 호출 83% 감소

**우선순위 3: Git Hooks**
1. ✅ Commitlint 설정 (1시간)
2. ✅ Pre-commit secrets 검사 (1시간)

**예상 효과**: Secrets 노출 방지, Conventional commits 강제

### 차기 진행

3. ⏸️ War Room WebSocket 구현 (백엔드 작업 필요)
4. ⏸️ 코드 스플리팅 (Lazy loading)
5. ⏸️ 문서 정리 자동화 (주간 스케줄)

---

## 관련 문서

**완료된 작업 (2026-01-02):**
- [Work_Log_20260102.md](Work_Log_20260102.md) - DB 최적화 Phase 1 완료, Kill Switch 구현
- [260102_Database_Optimization_Plan.md](260102_Database_Optimization_Plan.md) - DB 최적화 전체 계획

**참고 자료:**
- [260102_Claude_Code_Templates_Review.md](260102_Claude_Code_Templates_Review.md) - 600+ 템플릿 분석
- [Shadow_Trading_Week1_Report.md](Shadow_Trading_Week1_Report.md) - Shadow Trading 모니터링
- [implementation_plan.md](implementation_plan.md) - 실거래 테스트 계획

---

**작성일**: 2026-01-03
**작성자**: AI Trading System Development Team
**기준**: 2026-01-02 작업 완료 후
**우선순위**: P1 (High - Development Efficiency)
**상태**: 📋 Ready for Implementation
**다음 리뷰**: Component 1 (테스트 자동화) 완료 후

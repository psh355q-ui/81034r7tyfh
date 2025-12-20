# 프론트엔드-백엔드 데이터 연동 종합 계획서

**작성일**: 2025-12-10
**목적**: 모든 프론트엔드 페이지를 실제 백엔드 데이터와 완전히 연결

---

## 📋 목차

1. [현재 상태 진단](#현재-상태-진단)
2. [페이지별 데이터 연동 계획](#페이지별-데이터-연동-계획)
3. [백엔드 API 수정 사항](#백엔드-api-수정-사항)
4. [프론트엔드 수정 사항](#프론트엔드-수정-사항)
5. [테스트 데이터 생성](#테스트-데이터-생성)
6. [실행 순서](#실행-순서)

---

## 현재 상태 진단

### ❌ 문제점

1. **Dashboard 페이지**
   - Total Value: $0.00 (실제 포트폴리오 가치 없음)
   - Daily P&L: $0.00 (일일 손익 계산 안됨)
   - Positions: 0 (활성 포지션 없음)
   - Cash: $0.00 (현금 잔고 없음)
   - Charts: 데이터 없어 표시 안됨

2. **백엔드 API 응답 불완전**
   ```json
   {
     "active_positions": [],
     "total_positions": 0,
     "avg_return": 0.0,
     "best_performer": null,
     "worst_performer": null
   }
   ```

   **누락된 필드**:
   - `total_value` (전체 포트폴리오 가치)
   - `cash` (현금 잔고)
   - `positions_value` (포지션 가치)
   - `daily_pnl` (일일 손익)
   - `total_pnl` (총 손익)
   - `daily_return_pct` (일일 수익률)
   - `total_return_pct` (총 수익률)

3. **데이터베이스 비어있음**
   - Docker/PostgreSQL이 실행되지 않음
   - TradingSignal 테이블에 데이터 없음
   - Position 테이블에 데이터 없음

---

## 페이지별 데이터 연동 계획

### 1. Dashboard (우선순위: 🔴 최고)

**파일**: `frontend/src/pages/Dashboard.tsx`

#### 필요한 데이터

| 표시 항목 | 데이터 소스 | 백엔드 API | 상태 |
|-----------|-------------|-----------|------|
| Total Value | Portfolio 총 가치 | `GET /api/portfolio` | ❌ 미구현 |
| Daily P&L | 일일 손익 | `GET /api/portfolio` | ❌ 미구현 |
| Positions Count | 활성 포지션 수 | `GET /api/portfolio` | ✅ 구현됨 |
| Available Cash | 현금 잔고 | `GET /api/portfolio` | ❌ 미구현 |
| Performance Chart | 일별 포트폴리오 가치 | `GET /api/performance/history` | ❌ 미구현 |
| Real-time Chart | 실시간 가격 | `GET /api/realtime/{ticker}` | ❌ 미구현 |
| Sector Allocation | 섹터별 분포 | `GET /api/portfolio/sectors` | ❌ 미구현 |
| Risk Metrics | 리스크 지표 | `GET /api/portfolio/risk` | ❌ 미구현 |
| Current Positions | 포지션 목록 | `GET /api/portfolio` | ⚠️ 부분 구현 |

#### 수정 필요 사항

**백엔드**:
1. `PortfolioResponse` 모델 확장
2. 포트폴리오 가치 계산 로직 추가
3. 일일 손익 계산 로직 추가
4. 현금 잔고 관리 시스템 추가

**프론트엔드**:
1. API 응답 변환 로직 이미 완료 ✅
2. 차트 데이터 없을 때 처리 추가 필요
3. 빈 포지션 메시지 개선

---

### 2. Trading Dashboard (우선순위: 🔴 최고)

**파일**: `frontend/src/pages/TradingDashboard.tsx`

#### 필요한 데이터

| 표시 항목 | 데이터 소스 | 백엔드 API | 상태 |
|-----------|-------------|-----------|------|
| AI Signals | AI 거래 시그널 | `GET /api/signals` | ✅ 구현됨 |
| Signal Detail | 시그널 상세 | `GET /api/signals/{id}` | ✅ 구현됨 |
| Auto Trade Status | 자동매매 상태 | `GET /api/auto-trade/status` | ✅ 구현됨 |
| Execute Trade | 거래 실행 | `POST /api/auto-trade/execute` | ✅ 구현됨 |
| Order History | 주문 내역 | `GET /api/orders` | ❌ 미구현 |

#### 수정 필요 사항

**백엔드**:
1. 주문 내역 API 추가

**프론트엔드**:
1. 시그널 없을 때 더미 데이터 표시
2. 거래 실행 성공/실패 알림 개선

---

### 3. Analysis (우선순위: 🟡 중)

**파일**: `frontend/src/pages/Analysis.tsx`

#### 필요한 데이터

| 표시 항목 | 데이터 소스 | 백엔드 API | 상태 |
|-----------|-------------|-----------|------|
| Ticker Analysis | 개별 종목 분석 | `POST /api/analyze` | ✅ 구현됨 |
| Batch Analysis | 다중 종목 분석 | `POST /api/analyze/batch` | ✅ 구현됨 |
| Historical Data | 과거 데이터 | `GET /api/history/{ticker}` | ❌ 미구현 |

---

### 4. Backtest (우선순위: 🟡 중)

**파일**: `frontend/src/pages/BacktestDashboard.tsx`

#### 필요한 데이터

| 표시 항목 | 데이터 소스 | 백엔드 API | 상태 |
|-----------|-------------|-----------|------|
| Backtest Run | 백테스트 실행 | `POST /api/backtest/run` | ✅ 구현됨 |
| Backtest Results | 백테스트 결과 | `GET /api/backtest/results/{id}` | ✅ 구현됨 |
| Consensus Test | 합의 백테스트 | `POST /api/backtest/consensus` | ✅ 구현됨 |

---

### 5. Reports (우선순위: 🟢 낮)

**파일**: `frontend/src/pages/Reports.tsx`

#### 필요한 데이터

| 표시 항목 | 데이터 소스 | 백엔드 API | 상태 |
|-----------|-------------|-----------|------|
| Performance Report | 성과 리포트 | `GET /api/reports/performance` | ✅ 구현됨 |
| Tax Report | 세금 리포트 | `GET /api/reports/tax` | ❌ 미구현 |
| Trade History | 거래 내역 | `GET /api/reports/trades` | ✅ 구현됨 |

---

### 6. Settings (우선순위: 🟢 낮)

**파일**: `frontend/src/pages/Settings.tsx`

#### 필요한 데이터

| 표시 항목 | 데이터 소스 | 백엔드 API | 상태 |
|-----------|-------------|-----------|------|
| User Settings | 사용자 설정 | `GET /api/settings` | ❌ 미구현 |
| API Keys | API 키 관리 | `GET /api/settings/keys` | ❌ 미구현 |
| Notifications | 알림 설정 | `GET /api/settings/notifications` | ❌ 미구현 |

---

## 백엔드 API 수정 사항

### Phase 1: Portfolio API 완성 (최우선)

**파일**: `backend/api/main.py`

#### 1.1. PortfolioResponse 모델 확장

```python
class PortfolioResponse(BaseModel):
    # 기존 필드
    active_positions: List[PortfolioPosition]
    total_positions: int
    avg_return: float
    best_performer: Optional[PortfolioPosition]
    worst_performer: Optional[PortfolioPosition]

    # 추가 필드 (프론트엔드 요구사항)
    total_value: float          # 전체 포트폴리오 가치
    cash: float                 # 현금 잔고
    positions_value: float      # 포지션 총 가치
    daily_pnl: float           # 일일 손익
    total_pnl: float           # 총 손익
    daily_return_pct: float    # 일일 수익률
    total_return_pct: float    # 총 수익률
    recent_trades: List[Trade] # 최근 거래 내역
```

#### 1.2. Portfolio 계산 로직 추가

```python
@app.get("/api/portfolio", response_model=PortfolioResponse)
async def get_portfolio(db: Session = Depends(get_db)):
    try:
        # 1. 활성 포지션 조회
        active_signals = db.query(TradingSignal).filter(
            TradingSignal.entry_price.isnot(None),
            TradingSignal.exit_price.is_(None)
        ).all()

        # 2. 현재 가격 조회
        tickers = [signal.ticker for signal in active_signals]
        current_prices = get_multiple_prices(tickers, use_cache=True)

        # 3. 포지션 가치 계산
        positions_value = 0.0
        total_cost = 0.0
        positions = []

        for signal in active_signals:
            current_price = current_prices.get(signal.ticker, signal.entry_price)
            quantity = signal.quantity or 10  # 기본 수량

            position_value = current_price * quantity
            cost_basis = signal.entry_price * quantity

            positions_value += position_value
            total_cost += cost_basis

            # Position 객체 생성
            # ...

        # 4. 현금 잔고 (초기 자본 - 투자 금액)
        initial_capital = 100000.0  # $100,000
        cash = initial_capital - total_cost

        # 5. 총 가치
        total_value = positions_value + cash

        # 6. 손익 계산
        total_pnl = positions_value - total_cost
        total_return_pct = (total_pnl / total_cost * 100) if total_cost > 0 else 0

        # 7. 일일 손익 (전일 종가 대비)
        # TODO: 전일 포트폴리오 가치를 DB에서 조회
        daily_pnl = 0.0
        daily_return_pct = 0.0

        # 8. 최근 거래 내역
        recent_trades = db.query(TradingSignal).filter(
            TradingSignal.exit_price.isnot(None)
        ).order_by(TradingSignal.exit_date.desc()).limit(10).all()

        return PortfolioResponse(
            active_positions=positions,
            total_positions=len(positions),
            avg_return=avg_return,
            best_performer=best,
            worst_performer=worst,
            total_value=total_value,
            cash=cash,
            positions_value=positions_value,
            daily_pnl=daily_pnl,
            total_pnl=total_pnl,
            daily_return_pct=daily_return_pct,
            total_return_pct=total_return_pct,
            recent_trades=convert_trades(recent_trades)
        )
    except Exception as e:
        logging.error(f"Error fetching portfolio: {e}")
        return PortfolioResponse(
            active_positions=[],
            total_positions=0,
            avg_return=0.0,
            best_performer=None,
            worst_performer=None,
            total_value=100000.0,  # 초기 자본
            cash=100000.0,
            positions_value=0.0,
            daily_pnl=0.0,
            total_pnl=0.0,
            daily_return_pct=0.0,
            total_return_pct=0.0,
            recent_trades=[]
        )
```

#### 1.3. 추가 필요 API

```python
# 성능 히스토리
@app.get("/api/performance/history")
async def get_performance_history(
    days: int = Query(30),
    db: Session = Depends(get_db)
):
    """일별 포트폴리오 가치 히스토리"""
    pass

# 섹터 분포
@app.get("/api/portfolio/sectors")
async def get_sector_allocation(db: Session = Depends(get_db)):
    """섹터별 자산 분포"""
    pass

# 리스크 메트릭
@app.get("/api/portfolio/risk")
async def get_risk_metrics(db: Session = Depends(get_db)):
    """포트폴리오 리스크 지표"""
    pass

# 실시간 가격
@app.get("/api/realtime/{ticker}")
async def get_realtime_price(ticker: str):
    """실시간 주가"""
    pass
```

---

### Phase 2: 테스트 데이터 생성

**파일**: `backend/scripts/seed_test_data.py`

```python
"""
테스트 데이터 생성 스크립트
실제 데이터처럼 보이는 더미 데이터 생성
"""

from datetime import datetime, timedelta
from backend.database.models import TradingSignal
from backend.database.repository import get_sync_session

def create_test_signals():
    """테스트용 트레이딩 시그널 생성"""
    db = get_sync_session()

    test_signals = [
        {
            "ticker": "AAPL",
            "signal_type": "BUY",
            "action": "BUY",
            "confidence": 0.85,
            "entry_price": 180.50,
            "current_price": 185.20,
            "quantity": 50,
            "generated_at": datetime.now() - timedelta(days=5),
            "reasoning": "Strong technical indicators, positive earnings"
        },
        {
            "ticker": "NVDA",
            "signal_type": "BUY",
            "action": "BUY",
            "confidence": 0.92,
            "entry_price": 480.00,
            "current_price": 495.30,
            "quantity": 20,
            "generated_at": datetime.now() - timedelta(days=3),
            "reasoning": "AI chip demand surge, beat earnings estimates"
        },
        {
            "ticker": "TSLA",
            "signal_type": "BUY",
            "action": "BUY",
            "confidence": 0.78,
            "entry_price": 245.00,
            "current_price": 238.50,
            "quantity": 30,
            "generated_at": datetime.now() - timedelta(days=7),
            "reasoning": "Oversold condition, delivery numbers expected"
        },
    ]

    for signal_data in test_signals:
        signal = TradingSignal(**signal_data)
        db.add(signal)

    db.commit()
    print(f"Created {len(test_signals)} test signals")

if __name__ == "__main__":
    create_test_signals()
```

---

### Phase 3: 프론트엔드 개선

#### 3.1. Dashboard 빈 데이터 처리

**파일**: `frontend/src/pages/Dashboard.tsx`

```typescript
// 데이터 없을 때 안내 메시지
{portfolio && portfolio.positions.length === 0 && (
  <div className="text-center py-12">
    <p className="text-gray-500 mb-4">
      포트폴리오가 비어있습니다.
    </p>
    <button
      onClick={() => navigate('/trading')}
      className="btn-primary"
    >
      거래 시작하기
    </button>
  </div>
)}
```

#### 3.2. 차트 데이터 없을 때 처리

```typescript
// Performance Chart
{performanceData && performanceData.length > 0 ? (
  <PortfolioPerformanceChart data={performanceData} />
) : (
  <div className="text-center py-8 text-gray-500">
    데이터가 충분히 쌓이면 차트가 표시됩니다.
  </div>
)}
```

---

## 실행 순서

### Step 1: 데이터베이스 시작 (필수)

```batch
# Docker Desktop 시작

# PostgreSQL + Redis 시작
start_database.bat

# 또는
docker-compose up -d timescaledb redis
```

### Step 2: 테스트 데이터 생성

```batch
# 백엔드 디렉토리로 이동
cd backend

# 테스트 데이터 생성 스크립트 실행
python scripts/seed_test_data.py
```

### Step 3: 백엔드 API 수정

1. PortfolioResponse 모델 확장
2. Portfolio 계산 로직 추가
3. 추가 API 엔드포인트 구현

### Step 4: 백엔드 재시작

```batch
# 기존 백엔드 종료 (Ctrl+C)

# 재시작
start_backend.bat
```

### Step 5: 프론트엔드 확인

```batch
# 브라우저에서
http://localhost:3002/dashboard

# 새로고침 (F5)
```

### Step 6: 각 페이지 검증

1. Dashboard - 포트폴리오 데이터 표시 확인
2. Trading - AI 시그널 표시 확인
3. Analysis - 종목 분석 동작 확인
4. Backtest - 백테스트 실행 확인
5. Reports - 리포트 생성 확인

---

## 예상 결과

### 수정 후 Dashboard

```
Portfolio Overview:
- Total Value: $98,450.50 (+2.35%)
- Daily P&L: +$1,234.50 (1.27% today)
- Positions: 3
- Available Cash: $73,425.50 (74.6% of portfolio)

Current Positions:
┌─────────┬────────┬──────────┬──────────┬─────────┐
│ Ticker  │ Action │ Quantity │ Entry    │ Current │
├─────────┼────────┼──────────┼──────────┼─────────┤
│ AAPL    │ BUY    │ 50       │ $180.50  │ $185.20 │
│ NVDA    │ BUY    │ 20       │ $480.00  │ $495.30 │
│ TSLA    │ BUY    │ 30       │ $245.00  │ $238.50 │
└─────────┴────────┴──────────┴──────────┴─────────┘
```

---

## 우선순위별 작업 목록

### 🔴 Phase 1 (최우선 - 오늘)
- [x] 현황 진단 완료
- [ ] PortfolioResponse 모델 확장
- [ ] Portfolio 계산 로직 구현
- [ ] 테스트 데이터 생성 스크립트
- [ ] Dashboard 데이터 표시 확인

### 🟡 Phase 2 (내일)
- [ ] Performance History API
- [ ] Sector Allocation API
- [ ] Risk Metrics API
- [ ] 차트 데이터 연동

### 🟢 Phase 3 (주말)
- [ ] Trading Dashboard 개선
- [ ] Analysis 페이지 개선
- [ ] Reports 페이지 개선
- [ ] 전체 테스트

---

## 체크리스트

### 백엔드
- [ ] PortfolioResponse 모델에 7개 필드 추가
- [ ] Portfolio 가치 계산 로직
- [ ] 현금 잔고 관리
- [ ] 일일 손익 계산
- [ ] 추가 API 4개 구현
- [ ] 에러 처리 강화

### 프론트엔드
- [x] API 응답 변환 로직 (완료)
- [ ] 빈 데이터 처리 UI
- [ ] 차트 fallback 처리
- [ ] 로딩 상태 개선

### 데이터베이스
- [ ] PostgreSQL 실행
- [ ] 테스트 데이터 생성
- [ ] 데이터 검증

### 테스트
- [ ] Portfolio API 응답 확인
- [ ] Dashboard 렌더링 확인
- [ ] 차트 표시 확인
- [ ] 전체 페이지 동작 확인

---

**다음 단계**: PortfolioResponse 모델 확장 및 계산 로직 구현부터 시작하겠습니다.

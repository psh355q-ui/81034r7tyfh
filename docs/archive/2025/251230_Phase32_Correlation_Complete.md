# Phase 32: Asset Correlation 자동 계산 시스템

**Date**: 2025-12-30
**Priority**: 4th (Phase 29 확장 → Phase 32)
**Status**: ✅ Complete

---

## 📋 Overview

자산 간 상관관계를 자동으로 계산하여 포트폴리오 분산 최적화를 지원하는 시스템입니다.

**핵심 기능**:
- 30d/90d/1y 기간별 상관계수 자동 계산
- Top 상관 페어 조회 (양의 상관계수)
- Uncorrelated/Negative 페어 조회 (음의 상관계수)
- 수동 계산 트리거 지원
- 계산 상태 모니터링 (coverage, last_calculated)

---

## 🎯 Business Value

### Portfolio Diversification
- **High Correlation (>0.7)**: 함께 움직이는 자산 → Momentum 전략에 유리, 분산에 불리
- **Low Correlation (<0.3)**: 독립적으로 움직이는 자산 → 분산에 유리
- **Negative Correlation (<0)**: 반대로 움직이는 자산 → Hedging에 유리

### Use Cases
1. **포트폴리오 구성**: 낮은 상관계수를 가진 자산 조합으로 리스크 감소
2. **Hedging 전략**: 음의 상관계수를 가진 자산으로 손실 방어
3. **Momentum 전략**: 높은 상관계수를 가진 자산으로 동반 상승 활용

---

## 🏗️ Architecture

### Database Schema

**Table**: `asset_correlations`
```sql
CREATE TABLE asset_correlations (
    id SERIAL PRIMARY KEY,
    symbol1 VARCHAR(20) NOT NULL,       -- 첫 번째 자산 심볼
    symbol2 VARCHAR(20) NOT NULL,       -- 두 번째 자산 심볼
    correlation_30d DECIMAL(10, 6),     -- 30일 상관계수
    correlation_90d DECIMAL(10, 6),     -- 90일 상관계수
    correlation_1y DECIMAL(10, 6),      -- 1년 상관계수
    calculated_at TIMESTAMP,            -- 계산 시각
    UNIQUE(symbol1, symbol2)            -- 페어 유일성 보장
);
```

**Indexes**:
- Primary Key: `id`
- Unique Constraint: `(symbol1, symbol2)`
- Created Index: `idx_correlation_pair` on `(symbol1, symbol2)`

---

## 📊 Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    Correlation Scheduler                     │
│                   (Daily 00:00 Auto-Run)                     │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
         ┌─────────────────────────────┐
         │  1. Fetch Active Assets     │
         │     (multi_asset_config)    │
         └─────────────┬───────────────┘
                       │
                       ▼
         ┌─────────────────────────────┐
         │  2. Download Price Data     │
         │     (YFinance API)          │
         │   - 30d, 90d, 1y periods    │
         └─────────────┬───────────────┘
                       │
                       ▼
         ┌─────────────────────────────┐
         │  3. Calculate Correlations  │
         │   - Pandas pct_change()     │
         │   - Pearson correlation     │
         │   - All asset pairs         │
         └─────────────┬───────────────┘
                       │
                       ▼
         ┌─────────────────────────────┐
         │  4. Upsert to Database      │
         │   (asset_correlations)      │
         └─────────────┬───────────────┘
                       │
                       ▼
         ┌─────────────────────────────┐
         │  5. Return Calculation      │
         │      Result Summary         │
         └─────────────────────────────┘
```

---

## 🔧 Backend Implementation

### 1. Correlation Scheduler

**File**: `backend/schedulers/correlation_scheduler.py` (300+ lines)

**Class**: `CorrelationScheduler`

**Key Methods**:

#### `fetch_price_data(symbols: List[str], period: str) -> pd.DataFrame`
```python
"""
YFinance에서 가격 데이터 다운로드

Args:
    symbols: 자산 심볼 리스트 (예: ['AAPL', 'GOOGL'])
    period: 기간 ('30d', '90d', '1y')

Returns:
    DataFrame with symbols as columns, dates as index

YFinance MultiIndex Handling:
- 단일 심볼: raw_data['Close']를 DataFrame으로 변환
- 복수 심볼: raw_data[(symbol, 'Close')] 추출 후 concat
"""
```

#### `calculate_correlation(prices: pd.DataFrame, symbol1: str, symbol2: str) -> Optional[float]`
```python
"""
두 자산 간 상관계수 계산

Process:
1. Calculate returns: pct_change()
2. Align data: dropna()
3. Check minimum data points (>=10)
4. Calculate Pearson correlation

Returns:
    Correlation coefficient (-1.0 ~ 1.0) or None
"""
```

#### `calculate_all_correlations() -> Dict`
```python
"""
모든 자산 페어의 상관계수 계산 및 저장

Process:
1. Fetch active assets from multi_asset_config
2. Download price data for 30d, 90d, 1y
3. Calculate all pairs (N * (N-1) / 2 combinations)
4. Upsert to asset_correlations table

Returns:
    {
        'timestamp': ISO datetime,
        'success': bool,
        'assets_count': int,
        'pairs_calculated': int,
        'records_saved': int,
        'message': str
    }
"""
```

**YFinance MultiIndex Issue**:
```python
# YFinance returns MultiIndex columns for multiple symbols
raw_data = yf.download(['AAPL', 'GOOGL'], period='1y')
# raw_data.columns = MultiIndex[('AAPL', 'Close'), ('AAPL', 'Open'), ...]

# Solution: Extract Close prices manually
prices = pd.DataFrame()
for symbol in symbols:
    if (symbol, 'Close') in raw_data.columns:
        prices[symbol] = raw_data[(symbol, 'Close')]
```

---

### 2. Correlation API Router

**File**: `backend/api/correlation_router.py` (400+ lines)

**Router**: `/api/correlation`

**Endpoints**:

#### `POST /api/correlation/calculate`
수동 상관계수 계산 트리거

**Request**: (Empty body)

**Response**:
```json
{
  "timestamp": "2025-12-30T10:00:00",
  "success": true,
  "assets_count": 27,
  "pairs_calculated": 351,
  "records_saved": 351,
  "message": "Calculated correlations for 351 asset pairs"
}
```

**Use Case**:
- 자동 스케줄 외에 수동으로 계산이 필요한 경우
- 새 자산 추가 후 즉시 상관계수 업데이트

---

#### `GET /api/correlation/status`
계산 상태 조회

**Response**:
```json
{
  "total_pairs": 351,
  "expected_pairs": 351,
  "coverage": 100.0,
  "last_calculated": "2025-12-30T00:00:00",
  "active_assets": 27
}
```

**Fields**:
- `total_pairs`: DB에 저장된 페어 수
- `expected_pairs`: 활성 자산 기준 기대 페어 수 (N*(N-1)/2)
- `coverage`: 커버리지 % (total_pairs / expected_pairs * 100)
- `last_calculated`: 마지막 계산 시각
- `active_assets`: 활성 자산 수

---

#### `GET /api/correlation/heatmap?period=90d&min_correlation=0.3`
상관계수 히트맵 데이터 조회

**Query Parameters**:
- `period`: '30d' | '90d' | '1y' (기본: '90d')
- `min_correlation`: 최소 상관계수 필터 (선택사항)

**Response**:
```json
{
  "period": "90d",
  "symbols": ["AAPL", "GOOGL", "MSFT", ...],
  "matrix": {
    "AAPL": {
      "AAPL": 1.0,
      "GOOGL": 0.85,
      "MSFT": 0.82,
      ...
    },
    ...
  },
  "heatmap_data": [
    {"x": "AAPL", "y": "GOOGL", "value": 0.85},
    {"x": "AAPL", "y": "MSFT", "value": 0.82},
    ...
  ],
  "generated_at": "2025-12-30T10:00:00"
}
```

**Use Case**: 히트맵 시각화용 데이터 (Recharts Heatmap)

---

#### `GET /api/correlation/pairs?period=90d&sort_by=highest&limit=20`
Top 상관 페어 조회

**Query Parameters**:
- `period`: '30d' | '90d' | '1y' (기본: '90d')
- `sort_by`: 'highest' | 'lowest' (기본: 'highest')
- `limit`: 최대 결과 수 (기본: 20, 최대 100)

**Response**:
```json
{
  "period": "90d",
  "sort_by": "highest",
  "count": 20,
  "pairs": [
    {
      "symbol1": "AAPL",
      "symbol2": "MSFT",
      "correlation": 0.92,
      "calculated_at": "2025-12-30T00:00:00"
    },
    ...
  ]
}
```

**Use Cases**:
- `sort_by=highest`: 높은 양의 상관계수 페어 → Momentum 전략
- `sort_by=lowest`: 낮은/음의 상관계수 페어 → Diversification/Hedging

---

## 🎨 Frontend Implementation

### Correlation Dashboard

**File**: `frontend/src/pages/CorrelationDashboard.tsx` (417 lines)

**Route**: `/correlation`

**Components**:

#### 1. Status Cards (4개)

```typescript
// Total Pairs Card
<Card title="Total Pairs">
  <p className="text-3xl font-bold">{status?.total_pairs || 0}</p>
  <p className="text-sm text-gray-600">
    Expected: {status?.expected_pairs || 0}
  </p>
</Card>

// Coverage Card (Progress Bar)
<Card title="Coverage">
  <p className="text-3xl font-bold">{status?.coverage || 0}%</p>
  <div className="w-full bg-gray-200 rounded-full h-2">
    <div
      className="h-2 rounded-full bg-blue-500"
      style={{ width: `${status?.coverage || 0}%` }}
    />
  </div>
</Card>

// Active Assets Card
<Card title="Active Assets">
  <p className="text-3xl font-bold">{status?.active_assets || 0}</p>
  <p className="text-sm text-gray-600">Multi-asset support</p>
</Card>

// Last Calculated Card
<Card title="Last Calculated">
  <div className="flex items-center gap-2 text-gray-700">
    <Clock className="h-4 w-4" />
    <span className="text-sm">{formatDate(status?.last_calculated)}</span>
  </div>
  <p className="text-xs text-gray-500">Auto-updates daily at 01:00</p>
</Card>
```

---

#### 2. Period Selector

```typescript
const [period, setPeriod] = useState<string>('90d');

<Card>
  <div className="flex items-center gap-4">
    <label className="font-medium">Time Period:</label>
    <div className="flex gap-2">
      {['30d', '90d', '1y'].map((p) => (
        <button
          key={p}
          onClick={() => setPeriod(p)}
          className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
            period === p
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          {p === '30d' ? '30 Days' : p === '90d' ? '90 Days' : '1 Year'}
        </button>
      ))}
    </div>
  </div>
</Card>
```

**Effect**: Period 변경 시 `useQuery` refetch 자동 실행

---

#### 3. Positive Correlations Table

```typescript
const { data: positivePairs } = useQuery({
  queryKey: ['correlation-pairs', period, 'highest'],
  queryFn: () => fetchPairs(period, 'highest'),
  refetchInterval: 60000  // 1분마다 자동 갱신
});

<Card title="Highly Correlated Pairs (Positive)">
  <p className="text-sm text-gray-600 mb-4">
    These assets tend to move together. Good for momentum strategies,
    but poor for diversification.
  </p>
  <table className="w-full text-sm">
    <thead>
      <tr className="border-b bg-gray-50">
        <th className="h-12 px-4 text-left">Asset 1</th>
        <th className="h-12 px-4 text-left">Asset 2</th>
        <th className="h-12 px-4 text-left">Correlation</th>
        <th className="h-12 px-4 text-left">Last Calculated</th>
      </tr>
    </thead>
    <tbody>
      {positivePairs.pairs.slice(0, 10).map((pair, idx) => (
        <tr key={idx} className="border-b">
          <td className="p-4 font-mono font-bold">{pair.symbol1}</td>
          <td className="p-4 font-mono font-bold">{pair.symbol2}</td>
          <td className="p-4">
            <div className="flex items-center gap-2">
              <TrendingUp className={`h-4 w-4 ${getCorrelationColor(pair.correlation)}`} />
              <span className={`font-semibold ${getCorrelationColor(pair.correlation)}`}>
                {pair.correlation.toFixed(3)}
              </span>
            </div>
          </td>
          <td className="p-4 text-gray-600 text-xs">
            {formatDate(pair.calculated_at)}
          </td>
        </tr>
      ))}
    </tbody>
  </table>
</Card>
```

**Color Coding**:
```typescript
const getCorrelationColor = (corr: number): string => {
  if (corr > 0.7) return 'text-blue-600';   // Strong positive
  if (corr > 0.3) return 'text-blue-400';   // Moderate positive
  if (corr > -0.3) return 'text-gray-600';  // Weak/no correlation
  if (corr > -0.7) return 'text-red-400';   // Moderate negative
  return 'text-red-600';                     // Strong negative
};
```

---

#### 4. Negative Correlations Table

```typescript
const { data: negativePairs } = useQuery({
  queryKey: ['correlation-pairs', period, 'lowest'],
  queryFn: () => fetchPairs(period, 'lowest'),
  refetchInterval: 60000
});

<Card title="Uncorrelated / Negatively Correlated Pairs">
  <p className="text-sm text-gray-600 mb-4">
    These assets move independently or inversely. Excellent for
    portfolio diversification and risk reduction.
  </p>
  {/* Same table structure, but with TrendingDown icon */}
</Card>
```

**Use Case**: 포트폴리오 분산을 위한 낮은 상관계수 페어 발견

---

#### 5. Calculate Button

```typescript
const calcMutation = useMutation({
  mutationFn: calculateCorrelations,
  onSuccess: (data) => {
    setLastCalcResult(data);
    // Refetch all data
    queryClient.invalidateQueries({ queryKey: ['correlation-status'] });
    queryClient.invalidateQueries({ queryKey: ['correlation-pairs'] });
  }
});

<Button
  onClick={() => calcMutation.mutate()}
  disabled={calcMutation.isPending}
  variant="primary"
>
  <div className="flex items-center gap-2">
    {calcMutation.isPending ? (
      <RefreshCw className="h-4 w-4 animate-spin" />
    ) : (
      <Play className="h-4 w-4" />
    )}
    Calculate Correlations
  </div>
</Button>
```

**Result Display**:
```typescript
{lastCalcResult && (
  <Card>
    <div className="flex items-center gap-4">
      {lastCalcResult.success ? (
        <CheckCircle className="h-8 w-8 text-green-500" />
      ) : (
        <AlertCircle className="h-8 w-8 text-red-500" />
      )}
      <div className="flex-1">
        <h3 className="font-semibold text-lg">
          {lastCalcResult.success ? 'Calculation Completed' : 'Calculation Failed'}
        </h3>
        <p className="text-sm text-gray-600">{lastCalcResult.message}</p>
      </div>
      <div className="text-right">
        <p className="text-2xl font-bold">{lastCalcResult.pairs_calculated}</p>
        <p className="text-sm text-gray-600">Pairs Calculated</p>
      </div>
    </div>
  </Card>
)}
```

---

#### 6. Info Card (Educational)

```typescript
<Card title="About Correlation">
  <div className="space-y-2 text-sm text-gray-700">
    <p>
      <strong>Correlation:</strong> Measures how two assets move together (-1.0 to +1.0)
    </p>
    <ul className="list-disc list-inside space-y-1 ml-4">
      <li><strong>+1.0:</strong> Perfect positive correlation (move together)</li>
      <li><strong>0.0:</strong> No correlation (move independently)</li>
      <li><strong>-1.0:</strong> Perfect negative correlation (move opposite)</li>
    </ul>
    <p className="mt-3">
      <strong>Portfolio Strategy:</strong> Combining low-correlated or
      negatively-correlated assets reduces overall portfolio risk
      without sacrificing returns.
    </p>
  </div>
</Card>
```

---

## 🔗 Integration Points

### 1. Main Router Registration

**File**: `backend/main.py` (Lines 461-469)

```python
# Phase 32: Asset Correlation
from backend.api.correlation_router import router as correlation_router
app.include_router(correlation_router)

logger.info("✅ Correlation router registered at /api/correlation")
```

---

### 2. Frontend Routing

**File**: `frontend/src/App.tsx` (Lines 37, 72)

```typescript
import CorrelationDashboard from './pages/CorrelationDashboard';

<Route path="/correlation" element={<CorrelationDashboard />} />
```

---

### 3. Sidebar Menu

**File**: `frontend/src/components/Layout/Sidebar.tsx` (Lines 8, 48)

```typescript
import { ..., Network } from 'lucide-react';

{
  title: 'Trading & Strategy',
  items: [
    ...
    { path: '/correlation', icon: Network, label: 'Asset Correlation' },
    ...
  ]
}
```

**Category**: "Trading & Strategy" (Portfolio Optimization 다음 위치)

---

## 📦 Dependencies

### Backend
- **yfinance**: Price data download from Yahoo Finance
- **pandas**: DataFrame manipulation, correlation calculation
- **numpy**: NaN handling
- **SQLAlchemy**: Database ORM
- **FastAPI**: API routing

### Frontend
- **react-query**: Data fetching, mutations, auto-refetch
- **lucide-react**: Icons (TrendingUp, TrendingDown, Network, etc.)
- **react-router-dom**: Routing

---

## 🧪 Testing Scenarios

### 1. Manual Calculation Test
```bash
# Trigger calculation via API
curl -X POST http://localhost:8000/api/correlation/calculate

# Expected Response:
{
  "timestamp": "2025-12-30T10:00:00",
  "success": true,
  "assets_count": 27,
  "pairs_calculated": 351,
  "records_saved": 351,
  "message": "Calculated correlations for 351 asset pairs"
}
```

---

### 2. Status Check Test
```bash
# Check calculation status
curl http://localhost:8000/api/correlation/status

# Expected Response:
{
  "total_pairs": 351,
  "expected_pairs": 351,
  "coverage": 100.0,
  "last_calculated": "2025-12-30T00:00:00",
  "active_assets": 27
}
```

---

### 3. Top Pairs Test
```bash
# Get top positive correlations
curl "http://localhost:8000/api/correlation/pairs?period=90d&sort_by=highest&limit=10"

# Expected: Top 10 pairs with highest correlation (>0.7)

# Get top negative correlations
curl "http://localhost:8000/api/correlation/pairs?period=90d&sort_by=lowest&limit=10"

# Expected: Top 10 pairs with lowest correlation (<0.3)
```

---

### 4. Heatmap Data Test
```bash
# Get heatmap data
curl "http://localhost:8000/api/correlation/heatmap?period=90d"

# Expected: Full correlation matrix + heatmap_data array
```

---

### 5. Frontend Navigation Test
1. 서버 재시작 후 `/correlation` 접속
2. Status cards에 데이터 표시 확인
3. Period 버튼 클릭 시 테이블 데이터 변경 확인
4. "Calculate Correlations" 버튼 클릭 시 계산 결과 표시 확인

---

## 🚀 Scheduler Setup (Future)

### Cron Job Configuration

**Frequency**: 매일 01:00 (KST)

**Command**:
```bash
# Using Python directly
python -m backend.schedulers.correlation_scheduler

# Or using APScheduler in main.py
from apscheduler.schedulers.background import BackgroundScheduler
from backend.schedulers.correlation_scheduler import CorrelationScheduler

scheduler = BackgroundScheduler()
scheduler.add_job(
    func=CorrelationScheduler().calculate_all_correlations,
    trigger='cron',
    hour=1,
    minute=0,
    id='correlation_calculation',
    name='Daily Correlation Calculation'
)
scheduler.start()
```

**Why 01:00?**:
- 미국 시장 종료 후 (16:00 EST = 06:00 KST 다음날)
- 한국 시장 개장 전 (09:00 KST)
- 데이터 완성도 보장

---

## 📈 Performance Considerations

### Calculation Complexity

**Asset Count**: N assets
**Pair Count**: N × (N-1) / 2

**Examples**:
- 10 assets → 45 pairs
- 27 assets → 351 pairs
- 50 assets → 1,225 pairs
- 100 assets → 4,950 pairs

**YFinance Rate Limit**:
- Public API: ~2,000 requests/hour
- Premium API: Unlimited

**Solution**: Batch download all symbols in single request
```python
# Good: Single request for all symbols
prices = yf.download(['AAPL', 'GOOGL', 'MSFT', ...], period='1y')

# Bad: Individual requests (slow + rate limit)
for symbol in symbols:
    prices[symbol] = yf.download(symbol, period='1y')['Close']
```

---

### Database Optimization

**Upsert Strategy**:
```python
# PostgreSQL ON CONFLICT
INSERT INTO asset_correlations (symbol1, symbol2, correlation_30d, ...)
VALUES (%s, %s, %s, ...)
ON CONFLICT (symbol1, symbol2)
DO UPDATE SET
    correlation_30d = EXCLUDED.correlation_30d,
    correlation_90d = EXCLUDED.correlation_90d,
    correlation_1y = EXCLUDED.correlation_1y,
    calculated_at = EXCLUDED.calculated_at
```

**Benefit**: 신규 페어는 INSERT, 기존 페어는 UPDATE (중복 방지)

---

## 🔍 Key Insights

### Correlation Interpretation

**Strong Positive (>0.7)**:
- 같은 섹터 주식 (예: AAPL + MSFT)
- 같은 산업 (예: XOM + CVX 석유)
- 같은 지수 구성종목 (예: SPY + QQQ)

**Low Correlation (<0.3)**:
- 다른 섹터 (예: Tech + Energy)
- 다른 자산군 (예: Stocks + Bonds)
- 지역 차이 (예: US + Emerging Markets)

**Negative Correlation (<0)**:
- Inverse relationship (예: VIX + SPY)
- Gold + USD
- Bonds + Stocks (위기 시)

---

### Portfolio Strategy

**Max Sharpe Ratio**:
- 높은 수익 자산 선택
- 낮은 상관계수로 변동성 감소
- = 위험 대비 최대 수익

**Min Volatility**:
- 낮은 변동성 자산 선택
- 음의 상관계수로 상쇄 효과
- = 안정적 수익 추구

**Risk Parity**:
- 각 자산의 위험 기여도 동일화
- 상관계수 고려하여 가중치 조정
- = 균형잡힌 리스크 분산

---

## ✅ Completion Checklist

- [x] Database schema: `asset_correlations` table
- [x] Backend scheduler: `correlation_scheduler.py`
- [x] Backend API: `correlation_router.py` (4 endpoints)
- [x] Router registration: `main.py`
- [x] Frontend dashboard: `CorrelationDashboard.tsx`
- [x] Frontend routing: `App.tsx`
- [x] Sidebar menu: `Sidebar.tsx`
- [x] Documentation: `251230_Phase32_Correlation_Complete.md`

---

## 🎉 Summary

Phase 32에서 구현한 Asset Correlation 시스템은 **포트폴리오 분산 최적화**를 위한 핵심 기능입니다.

**핵심 성과**:
1. ✅ 30d/90d/1y 기간별 자동 상관계수 계산
2. ✅ Top 상관 페어 조회 (양의/음의 상관계수)
3. ✅ 수동 계산 트리거 지원
4. ✅ 계산 상태 모니터링 (coverage, last_calculated)
5. ✅ 직관적인 Dashboard UI (테이블, 색상 코딩)

**다음 단계**:
- Phase 33: Correlation Heatmap 시각화 (Recharts)
- Phase 34: 상관계수 기반 포트폴리오 제안 자동화
- APScheduler 통합 (매일 01:00 자동 실행)

---

**End of Phase 32 Documentation**

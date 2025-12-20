# AI Trading System - React Frontend Development Guide

**For Claude Code** - Complete implementation instructions

---

## 프로젝트 개요

AI Trading System의 React 기반 웹 프론트엔드를 개발합니다.

**현재 상태**:
- ✅ 백엔드 완성 (FastAPI, 18개 엔드포인트)
- ✅ 기본 프론트엔드 구조 생성 (Vite + React + TypeScript + Tailwind CSS)
- ⏳ 실제 컴포넌트 및 페이지 구현 필요

**디렉토리**:
- Backend: `D:\code\ai-trading-system\backend\`
- Frontend: `D:\code\ai-trading-system\frontend\`

---

## 백엔드 API 엔드포인트 (FastAPI)

### 1. General
- `GET /` - API 정보
- `GET /health` - 상세 Health Check
- `GET /health/live` - Liveness Probe (K8s)
- `GET /health/ready` - Readiness Probe (K8s)

### 2. Trading (AI 분석 및 실행)
- `POST /analyze` - 단일 종목 AI 분석
  ```json
  Request: {"ticker": "AAPL"}
  Response: {
    "ticker": "AAPL",
    "action": "BUY",
    "conviction": 0.85,
    "reasoning": "...",
    "target_price": 280.0,
    "stop_loss": 260.0,
    "position_size": 5.0,
    "risk_factors": ["..."]
  }
  ```

- `POST /analyze/batch` - 여러 종목 일괄 분석
  ```json
  Request: {"tickers": ["AAPL", "NVDA", "MSFT"]}
  Response: [
    { "ticker": "AAPL", "action": "BUY", ... },
    { "ticker": "NVDA", "action": "HOLD", ... }
  ]
  ```

- `POST /execute` - 거래 실행 (Paper Trading)
  ```json
  Request: {
    "ticker": "AAPL",
    "action": "BUY",
    "shares": 10,
    "order_type": "MARKET"
  }
  Response: {
    "order_id": "...",
    "status": "FILLED",
    "filled_price": 273.20,
    "commission": 2.73
  }
  ```

### 3. Portfolio
- `GET /portfolio` - 현재 포트폴리오
  ```json
  Response: {
    "total_value": 105750.0,
    "cash": 45000.0,
    "positions": [
      {
        "ticker": "AAPL",
        "shares": 100,
        "avg_price": 270.0,
        "current_price": 273.2,
        "value": 27320.0,
        "unrealized_pnl": 320.0,
        "pnl_pct": 1.19
      }
    ],
    "total_pnl": 5750.0,
    "total_return_pct": 5.75
  }
  ```

- `GET /portfolio/daily` - 일일 포트폴리오 변화
  ```json
  Response: {
    "date": "2025-11-15",
    "starting_value": 100000.0,
    "ending_value": 105750.0,
    "daily_pnl": 1200.0,
    "daily_return_pct": 1.15,
    "trades_count": 5
  }
  ```

### 4. Risk Management
- `GET /risk/status` - 리스크 상태
  ```json
  Response: {
    "kill_switch_active": false,
    "daily_pnl": 1200.0,
    "daily_return_pct": 1.15,
    "max_drawdown_pct": 2.5,
    "position_concentration": {
      "AAPL": 25.8,
      "NVDA": 18.5
    },
    "sector_concentration": {
      "Technology": 65.0,
      "Healthcare": 20.0
    }
  }
  ```

- `POST /risk/kill-switch/activate` - Kill Switch 활성화
- `POST /risk/kill-switch/deactivate` - Kill Switch 비활성화

### 5. Alerts
- `GET /alerts` - 최근 알림 조회
- `POST /alerts/send` - 알림 전송 (Telegram)
- `POST /alerts/test` - 테스트 알림

### 6. System
- `GET /system/info` - 시스템 정보
- `GET /system/metrics/summary` - 메트릭 요약
- `GET /system/health/summary` - Health 요약
- `GET /metrics` - Prometheus 메트릭

---

## 프론트엔드 구조

```
frontend/
├── public/
│   └── index.html
├── src/
│   ├── components/          # 재사용 가능한 컴포넌트
│   │   ├── Layout/
│   │   │   ├── Header.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   └── Layout.tsx
│   │   ├── Dashboard/
│   │   │   ├── PortfolioSummary.tsx
│   │   │   ├── PositionsTable.tsx
│   │   │   ├── PerformanceChart.tsx
│   │   │   └── RecentTrades.tsx
│   │   ├── Analysis/
│   │   │   ├── TickerSearch.tsx
│   │   │   ├── AIDecisionCard.tsx
│   │   │   └── RiskFactorsList.tsx
│   │   ├── Monitor/
│   │   │   ├── LiveEngineStatus.tsx
│   │   │   ├── TradingLog.tsx
│   │   │   └── RateLimitIndicator.tsx
│   │   └── common/
│   │       ├── Button.tsx
│   │       ├── Card.tsx
│   │       ├── Badge.tsx
│   │       └── LoadingSpinner.tsx
│   ├── pages/
│   │   ├── Dashboard.tsx
│   │   ├── Analysis.tsx
│   │   ├── Monitor.tsx
│   │   └── Settings.tsx
│   ├── services/
│   │   └── api.ts            # Axios API 클라이언트
│   ├── hooks/
│   │   ├── usePortfolio.ts
│   │   ├── useAnalysis.ts
│   │   └── useWebSocket.ts
│   ├── types/
│   │   └── index.ts          # TypeScript 타입 정의
│   ├── utils/
│   │   ├── formatters.ts     # 숫자, 날짜 포맷
│   │   └── helpers.ts
│   ├── App.tsx
│   ├── main.tsx
│   └── index.css
├── package.json
├── vite.config.ts
├── tsconfig.json
└── tailwind.config.js
```

---

## 구현 우선순위

### Phase 1: 기본 구조 및 API 연동 (✅ 일부 완료)
- [x] Vite + React + TypeScript 설정
- [x] Tailwind CSS 설정
- [ ] API 서비스 레이어 (`services/api.ts`)
- [ ] TypeScript 타입 정의 (`types/index.ts`)
- [ ] Layout 컴포넌트 (Header, Sidebar)
- [ ] React Router 설정

### Phase 2: Dashboard 페이지
- [ ] PortfolioSummary (총 자산, 수익률)
- [ ] PositionsTable (보유 종목 테이블)
- [ ] PerformanceChart (P&L 차트)
- [ ] RecentTrades (최근 거래 내역)

### Phase 3: AI Analysis 페이지
- [ ] TickerSearch (종목 검색)
- [ ] AIDecisionCard (AI 분석 결과 카드)
- [ ] RiskFactorsList (리스크 요인)
- [ ] Batch Analysis (여러 종목 분석)

### Phase 4: Live Trading Monitor 페이지
- [ ] LiveEngineStatus (엔진 상태)
- [ ] TradingLog (실시간 로그)
- [ ] RateLimitIndicator (API 사용률)
- [ ] Kill Switch 컨트롤

### Phase 5: Settings 페이지
- [ ] Trading 모드 설정
- [ ] Ticker 리스트 관리
- [ ] Safety 설정 (limits, kill switch threshold)
- [ ] Telegram 알림 설정

---

## 주요 구현 사항

### 1. API 서비스 레이어 (`services/api.ts`)

```typescript
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Trading API
export const analyzeTicker = async (ticker: string) => {
  const { data } = await apiClient.post('/analyze', { ticker });
  return data;
};

export const analyzeBatch = async (tickers: string[]) => {
  const { data } = await apiClient.post('/analyze/batch', { tickers });
  return data;
};

export const executeTrade = async (params: ExecuteTradeParams) => {
  const { data } = await apiClient.post('/execute', params);
  return data;
};

// Portfolio API
export const getPortfolio = async () => {
  const { data } = await apiClient.get('/portfolio');
  return data;
};

export const getDailyPortfolio = async () => {
  const { data } = await apiClient.get('/portfolio/daily');
  return data;
};

// Risk API
export const getRiskStatus = async () => {
  const { data } = await apiClient.get('/risk/status');
  return data;
};

export const activateKillSwitch = async () => {
  const { data } = await apiClient.post('/risk/kill-switch/activate');
  return data;
};

export const deactivateKillSwitch = async () => {
  const { data } = await apiClient.post('/risk/kill-switch/deactivate');
  return data;
};

// System API
export const getSystemInfo = async () => {
  const { data } = await apiClient.get('/system/info');
  return data;
};

export const getHealthSummary = async () => {
  const { data } = await apiClient.get('/system/health/summary');
  return data;
};
```

### 2. TypeScript 타입 정의 (`types/index.ts`)

```typescript
export interface AIDecision {
  ticker: string;
  action: 'BUY' | 'SELL' | 'HOLD';
  conviction: number;
  reasoning: string;
  target_price?: number;
  stop_loss?: number;
  position_size: number;
  risk_factors: string[];
  timestamp?: string;
}

export interface Position {
  ticker: string;
  shares: number;
  avg_price: number;
  current_price: number;
  value: number;
  unrealized_pnl: number;
  pnl_pct: number;
}

export interface Portfolio {
  total_value: number;
  cash: number;
  positions: Position[];
  total_pnl: number;
  total_return_pct: number;
}

export interface RiskStatus {
  kill_switch_active: boolean;
  daily_pnl: number;
  daily_return_pct: number;
  max_drawdown_pct: number;
  position_concentration: Record<string, number>;
  sector_concentration: Record<string, number>;
}

export interface Trade {
  timestamp: string;
  ticker: string;
  action: 'BUY' | 'SELL';
  shares: number;
  price: number;
  value: number;
  commission: number;
}

export interface SystemInfo {
  version: string;
  environment: string;
  uptime_seconds: number;
  components: {
    redis: boolean;
    timescaledb: boolean;
    claude_api: boolean;
  };
}
```

### 3. React Query 활용 (`hooks/usePortfolio.ts`)

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getPortfolio, getDailyPortfolio } from '@/services/api';

export const usePortfolio = () => {
  return useQuery({
    queryKey: ['portfolio'],
    queryFn: getPortfolio,
    refetchInterval: 10000, // 10초마다 갱신
  });
};

export const useDailyPortfolio = () => {
  return useQuery({
    queryKey: ['portfolio', 'daily'],
    queryFn: getDailyPortfolio,
    refetchInterval: 60000, // 1분마다 갱신
  });
};
```

### 4. 공통 컴포넌트 예시

**Button.tsx**:
```typescript
interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  onClick?: () => void;
  children: React.ReactNode;
  disabled?: boolean;
}

export const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'md',
  onClick,
  children,
  disabled = false,
}) => {
  const baseStyles = 'font-semibold rounded-lg transition-colors';
  const variantStyles = {
    primary: 'bg-blue-600 hover:bg-blue-700 text-white',
    secondary: 'bg-gray-200 hover:bg-gray-300 text-gray-800',
    danger: 'bg-red-600 hover:bg-red-700 text-white',
  };
  const sizeStyles = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg',
  };

  return (
    <button
      className={`${baseStyles} ${variantStyles[variant]} ${sizeStyles[size]} ${
        disabled ? 'opacity-50 cursor-not-allowed' : ''
      }`}
      onClick={onClick}
      disabled={disabled}
    >
      {children}
    </button>
  );
};
```

**Card.tsx**:
```typescript
interface CardProps {
  title?: string;
  children: React.ReactNode;
  className?: string;
}

export const Card: React.FC<CardProps> = ({ title, children, className = '' }) => {
  return (
    <div className={`bg-white rounded-lg shadow-md p-6 ${className}`}>
      {title && <h3 className="text-lg font-semibold mb-4">{title}</h3>}
      {children}
    </div>
  );
};
```

---

## Dashboard 페이지 예시

```typescript
import { Card } from '@/components/common/Card';
import { usePortfolio, useDailyPortfolio } from '@/hooks/usePortfolio';
import { PortfolioSummary } from '@/components/Dashboard/PortfolioSummary';
import { PositionsTable } from '@/components/Dashboard/PositionsTable';
import { PerformanceChart } from '@/components/Dashboard/PerformanceChart';
import { RecentTrades } from '@/components/Dashboard/RecentTrades';

export const Dashboard = () => {
  const { data: portfolio, isLoading: portfolioLoading } = usePortfolio();
  const { data: daily, isLoading: dailyLoading } = useDailyPortfolio();

  if (portfolioLoading || dailyLoading) {
    return <LoadingSpinner />;
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Dashboard</h1>

      {/* Portfolio Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card title="Total Value">
          <p className="text-3xl font-bold">
            ${portfolio.total_value.toLocaleString()}
          </p>
          <p className={`text-sm ${portfolio.total_return_pct >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {portfolio.total_return_pct >= 0 ? '+' : ''}{portfolio.total_return_pct.toFixed(2)}%
          </p>
        </Card>

        <Card title="Daily P&L">
          <p className={`text-3xl font-bold ${daily.daily_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {daily.daily_pnl >= 0 ? '+' : ''}${daily.daily_pnl.toLocaleString()}
          </p>
          <p className="text-sm text-gray-600">
            {daily.daily_return_pct.toFixed(2)}% today
          </p>
        </Card>

        <Card title="Positions">
          <p className="text-3xl font-bold">{portfolio.positions.length}</p>
          <p className="text-sm text-gray-600">{daily.trades_count} trades today</p>
        </Card>
      </div>

      {/* Performance Chart */}
      <Card title="Performance">
        <PerformanceChart />
      </Card>

      {/* Positions Table */}
      <Card title="Current Positions">
        <PositionsTable positions={portfolio.positions} />
      </Card>

      {/* Recent Trades */}
      <Card title="Recent Trades">
        <RecentTrades />
      </Card>
    </div>
  );
};
```

---

## 스타일 가이드

### 색상 (Tailwind CSS)
- **Primary**: `bg-blue-600`, `text-blue-600`
- **Success/Buy**: `bg-green-600`, `text-green-600`
- **Danger/Sell**: `bg-red-600`, `text-red-600`
- **Warning**: `bg-yellow-600`, `text-yellow-600`
- **Gray**: `bg-gray-100`, `text-gray-600`

### 컴포넌트 크기
- **Card Padding**: `p-6`
- **Grid Gap**: `gap-6`
- **Space Between**: `space-y-6`

### 폰트
- **Title**: `text-3xl font-bold`
- **Subtitle**: `text-xl font-semibold`
- **Body**: `text-base`
- **Small**: `text-sm text-gray-600`

---

## 실행 방법

### 1. 패키지 설치
```bash
cd D:\code\ai-trading-system\frontend
npm install
```

### 2. 개발 서버 실행
```bash
npm run dev
# → http://localhost:3000
```

### 3. 백엔드 실행 (별도 터미널)
```bash
cd D:\code\ai-trading-system\backend
uvicorn main:app --reload --port 8000
# → http://localhost:8000
```

---

## 테스트 체크리스트

### Dashboard
- [ ] 포트폴리오 총 자산 표시
- [ ] 일일 수익률 표시
- [ ] 보유 포지션 테이블
- [ ] 차트 렌더링
- [ ] 실시간 데이터 갱신 (10초)

### AI Analysis
- [ ] 종목 검색 및 분석 요청
- [ ] AI 결과 표시 (action, conviction, reasoning)
- [ ] 리스크 요인 표시
- [ ] Batch 분석 (여러 종목)

### Monitor
- [ ] Live Trading Engine 상태 표시
- [ ] 실시간 로그 스트림
- [ ] Kill Switch 토글
- [ ] Rate Limit 사용률

### Settings
- [ ] Trading 모드 선택
- [ ] Ticker 리스트 CRUD
- [ ] Safety 설정 저장
- [ ] Telegram 알림 테스트

---

## 참고 자료

- **Recharts**: https://recharts.org/
- **Lucide Icons**: https://lucide.dev/
- **React Query**: https://tanstack.com/query/latest
- **Tailwind CSS**: https://tailwindcss.com/

---

## Claude Code에게 요청할 프롬프트

```
D:\code\ai-trading-system\frontend 프로젝트의 React 프론트엔드를 완성해주세요.

현재 상태:
- package.json, vite.config.ts, tsconfig.json 설정 완료
- 디렉토리 구조 생성 완료

요청 사항:
1. src/services/api.ts - API 클라이언트 구현
2. src/types/index.ts - TypeScript 타입 정의
3. src/components/Layout/ - Header, Sidebar, Layout 컴포넌트
4. src/components/common/ - Button, Card, Badge, LoadingSpinner
5. src/pages/Dashboard.tsx - 포트폴리오 대시보드
6. src/pages/Analysis.tsx - AI 분석 페이지
7. src/pages/Monitor.tsx - Live Trading 모니터
8. src/App.tsx - React Router 설정
9. src/main.tsx - 앱 진입점
10. src/index.css - Tailwind CSS 설정

백엔드 API:
- Base URL: http://localhost:8000
- 주요 엔드포인트: /analyze, /portfolio, /risk/status, /execute
- 자세한 API 스펙은 D:\code\ai-trading-system\docs\251210_Frontend_Development_Prompt.md 참고

디자인:
- Tailwind CSS 사용
- 파란색 primary 테마
- 카드 기반 레이아웃
- Recharts로 차트 구현

Phase 1 (우선): API 서비스, 타입 정의, Layout, Dashboard 페이지부터 구현해주세요.
```

---

**생성 일자**: 2025-11-15
**작성자**: AI Trading System Team

# 🎯 Claude Code 프롬프트 - React 프론트엔드 개발

**프로젝트**: AI Trading System React Frontend
**위치**: `D:\code\ai-trading-system\frontend`
**목표**: 완전한 웹 대시보드 구현

---

## 📋 Quick Start 프롬프트

```
D:\code\ai-trading-system\frontend 디렉토리에서 React 프론트엔드를 구현해주세요.

### 현재 상태
- ✅ package.json, vite.config.ts 설정 완료
- ✅ 디렉토리 구조 생성 (src/components, pages, services)
- ⏳ 실제 컴포넌트 구현 필요

### Phase 1 구현 (최우선)
1. src/services/api.ts - Axios API 클라이언트
2. src/types/index.ts - TypeScript 타입
3. src/components/Layout/ - Header, Sidebar
4. src/components/common/ - Button, Card
5. src/pages/Dashboard.tsx - 메인 대시보드
6. src/App.tsx - Router 설정
7. src/main.tsx, index.css

### 백엔드 API (http://localhost:8000)
- POST /analyze - 종목 분석
- GET /portfolio - 포트폴리오
- GET /risk/status - 리스크 상태
- POST /execute - 거래 실행

상세 스펙: docs/Frontend_Development_Prompt.md
```

---

## 🔧 실행 명령어

```bash
# 프론트엔드 설치 및 실행
cd D:\code\ai-trading-system\frontend
npm install
npm run dev
# → http://localhost:3000

# 백엔드 실행 (별도 터미널)
cd D:\code\ai-trading-system\backend
uvicorn main:app --reload --port 8000
```

---

## 📦 구현 우선순위

### Phase 1: 핵심 기능 (1-2시간)
- [x] 프로젝트 설정
- [ ] **API 서비스 레이어** (`services/api.ts`)
- [ ] **타입 정의** (`types/index.ts`)
- [ ] **Layout** (Header, Sidebar)
- [ ] **Dashboard 페이지**

### Phase 2: AI 분석 (30분-1시간)
- [ ] 종목 검색 컴포넌트
- [ ] AI 분석 결과 카드
- [ ] Batch 분석

### Phase 3: 모니터링 (30분-1시간)
- [ ] Live Trading 상태
- [ ] 실시간 로그
- [ ] Kill Switch 토글

### Phase 4: 설정 (30분)
- [ ] Trading 설정
- [ ] Ticker 관리

---

## 🎨 디자인 가이드

**테마**: 파란색 (`bg-blue-600`, `text-blue-600`)
**레이아웃**: 카드 기반 (`Card` 컴포넌트)
**차트**: Recharts 사용
**아이콘**: Lucide React

---

## 📊 주요 컴포넌트 구조

```
Dashboard
├── PortfolioSummary (총 자산, 수익률)
├── PerformanceChart (P&L 차트)
├── PositionsTable (보유 종목)
└── RecentTrades (거래 내역)

Analysis
├── TickerSearch (검색)
├── AIDecisionCard (AI 결과)
└── RiskFactorsList (리스크)

Monitor
├── LiveEngineStatus (엔진 상태)
├── TradingLog (로그)
└── KillSwitch (토글)
```

---

## 🔗 참고 문서

- **상세 가이드**: `docs/Frontend_Development_Prompt.md`
- **백엔드 API**: `backend/main.py` (18개 엔드포인트)
- **백엔드 문서**: `README.md`

---

**생성 일자**: 2025-11-15

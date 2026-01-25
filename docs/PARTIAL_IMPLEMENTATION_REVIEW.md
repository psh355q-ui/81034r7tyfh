# 부분 구현 기능 검토 (Partial Implementation Review)

**작성일**: 2026-01-25
**목적**: 부분 구현된 기능의 현황 파악 및 완성 계획 수립
**검토 대상**: Persona-based Trading, Real-time Execution, Advanced Risk Models

---

## 📋 목차

1. [Persona-based Trading (50%)](#1-persona-based-trading-50)
2. [Real-time Execution (70%)](#2-real-time-execution-70)
3. [Advanced Risk Models (30%)](#3-advanced-risk-models-30)
4. [미구현 계획 기능](#4-미구현-계획-기능)
5. [우선순위 및 완성 계획](#5-우선순위-및-완성-계획)

---

## 1. Persona-based Trading (50%)

### 구현 현황

#### ✅ 구현됨
- **Persona 프롬프트 시스템** (`backend/ai/intelligence/prompts/persona_tuned_prompts.py`)
  - SOSUMONKEY 페르소나 정의 완료
  - 한국식 투자 분석 스타일 (요약/배경/연결/반론/종합)
  - Style validation 로직 구현
  - Prompt version tracking

- **Strategy Registry** (`backend/database/models.py` - Strategy 모델)
  - `persona_type` 필드 존재 (varchar 50)
  - trading, long_term, dividend, aggressive 전략 정의
  - 우선순위 시스템 (Priority 30-100)

- **Strategy Router** (`backend/api/strategy_router.py`)
  - 전략 CRUD API 완료
  - 전략 활성화/비활성화 가능
  - WebSocket 지원 (ConflictWebSocketManager)

#### ⚠️ 미완성
- **Daily Briefing 페르소나 분리**
  - 현재: 단일 Briefing 출력 (페르소나 무관)
  - 목표: 페르소나별 맞춤 리포트 (trading용, long_term용 등)

- **UI 통합**
  - 현재: 백엔드 API만 존재
  - 목표: 프론트엔드에서 페르소나 선택/전환 UI

- **리포트별 페르소나 적용**
  - 현재: 소수몽키 스타일만 구현
  - 목표: 각 페르소나별 독립 리포트 생성

### 구현률 분석

| 컴포넌트 | 구현률 | 비고 |
|---------|--------|------|
| **Persona 프롬프트 시스템** | 100% | 완료 |
| **Strategy Registry (DB)** | 100% | 완료 |
| **Strategy API** | 100% | 완료 |
| **Daily Briefing 페르소나 분리** | 0% | 미완 |
| **UI 통합** | 0% | 미완 |
| **리포트별 페르소나 적용** | 30% | 부분 (소수몽키만) |

**전체 구현률**: 50% (6개 중 3.5개 완료)

---

### 완성 계획

#### Phase 1: Daily Briefing 페르소나 분리 (Week 1-2)

**목표**: 페르소나별 맞춤 브리핑 생성

**작업**:
1. **DailyBriefingService 수정**
   ```python
   # backend/services/daily_briefing_service.py

   async def generate_briefing_by_persona(
       self,
       persona: str = "trading"  # trading, long_term, dividend, aggressive
   ) -> Dict:
       """Generate persona-specific briefing"""

       # Persona별 프롬프트 분기
       if persona == "trading":
           # 단기: 1-5일 시간 프레임, 기술적 분석 중심
           prompt = self._build_trading_prompt()
       elif persona == "long_term":
           # 장기: 6-18개월, 펀더멘털/테마 중심
           prompt = self._build_long_term_prompt()
       # ...
   ```

2. **Persona별 프롬프트 차별화**
   | Persona | 시간 프레임 | 중점 사항 | 스타일 |
   |---------|------------|----------|--------|
   | trading | 1-5일 | 기술적 분석, 단기 촉매 | 간결, 액션 중심 |
   | long_term | 6-18개월 | 펀더멘털, 테마 | 심층 분석, 교육적 |
   | dividend | 1년+ | 배당 안정성, 밸류에이션 | 보수적, 리스크 중심 |
   | aggressive | 1일 이내 | 변동성, 모멘텀 | 빠른 판단, 수치 중심 |

3. **API 엔드포인트 추가**
   ```python
   @router.get("/api/briefing/persona/{persona}")
   async def get_persona_briefing(persona: str):
       """Get persona-specific briefing"""
       # ...
   ```

**예상 기간**: 2주

---

#### Phase 2: UI 통합 (Week 3-4)

**목표**: 프론트엔드에서 페르소나 선택 및 전환

**작업**:
1. **Persona 선택기 컴포넌트**
   ```tsx
   // frontend/src/components/PersonaSelector.tsx

   const PersonaSelector = () => {
     const [activePersona, setActivePersona] = useState('trading');

     return (
       <Select value={activePersona} onChange={setActivePersona}>
         <Option value="trading">Trading (1-5일)</Option>
         <Option value="long_term">Long-term (6-18개월)</Option>
         <Option value="dividend">Dividend (1년+)</Option>
         <Option value="aggressive">Aggressive (1일)</Option>
       </Select>
     );
   };
   ```

2. **페르소나별 대시보드 레이아웃**
   - Trading: 차트 중심, 실시간 시그널
   - Long-term: 뉴스/테마 중심, 월간 리포트
   - Dividend: 배당 달력, 배당 귀족주
   - Aggressive: 변동성 알림, 빠른 액션 버튼

3. **브리핑 표시 로직**
   ```tsx
   const { data: briefing } = useQuery(
     ['briefing', activePersona],
     () => fetchBriefing(activePersona)
   );
   ```

**예상 기간**: 2주

---

#### Phase 3: 리포트별 페르소나 적용 (Week 5-6)

**목표**: 모든 리포트에 페르소나 스타일 적용

**작업**:
1. **Weekly/Monthly/Annual Report 페르소나 확장**
   - 현재: 단일 리포트 스타일
   - 개선: 페르소나별 독립 섹션

2. **Chart Generation 페르소나별 최적화**
   - Trading: 1-5일 차트, 단기 지표
   - Long-term: 장기 트렌드 차트, 펀더멘털 지표

**예상 기간**: 2주

---

## 2. Real-time Execution (70%)

### 구현 현황

#### ✅ 구현됨
- **WebSocket 인프라** (`backend/api/strategy_router.py`)
  - ConflictWebSocketManager 구현
  - Real-time conflict alerts
  - Broadcast 시스템

- **Order Execution Pipeline**
  - Execution Router (Fast Track / Deep Dive)
  - Order Validator (Hard Rules)
  - KIS Broker Integration

- **Event Bus** (`backend/events/`)
  - Event 발행/구독 시스템
  - ORDER_CREATED, CONFLICT_DETECTED 등 이벤트

#### ⚠️ 미완성
- **실시간 시장 데이터 WebSocket**
  - 현재: REST API 폴링
  - 목표: WebSocket 실시간 스트리밍 (주가, 뉴스)

- **모바일 알림 (Push Notification)**
  - 현재: 텔레그램만 지원
  - 목표: iOS/Android Push, Email, SMS

- **Live Trading Monitoring Dashboard**
  - 현재: 정적 대시보드
  - 목표: 실시간 업데이트 대시보드 (WebSocket 연동)

### 구현률 분석

| 컴포넌트 | 구현률 | 비고 |
|---------|--------|------|
| **WebSocket 인프라** | 100% | Conflict 전용 완료 |
| **Order Execution Pipeline** | 100% | 완료 |
| **Event Bus** | 100% | 완료 |
| **실시간 시장 데이터 WebSocket** | 0% | 미완 |
| **모바일 알림** | 30% | 텔레그램만 |
| **Live Dashboard** | 50% | 정적만 |

**전체 구현률**: 70% (6개 중 4.3개 완료)

---

### 완성 계획

#### Phase 1: 실시간 시장 데이터 WebSocket (Week 1-3)

**목표**: 주가/뉴스 실시간 스트리밍

**작업**:
1. **Market Data WebSocket Manager**
   ```python
   # backend/api/market_data_ws.py

   class MarketDataWebSocketManager:
       """Real-time market data streaming"""

       async def connect(self, websocket: WebSocket):
           await websocket.accept()
           # Subscribe to market data feeds

       async def stream_quotes(self, symbols: List[str]):
           """Stream real-time quotes for symbols"""
           # Use KIS WebSocket or Alpha Vantage WebSocket

       async def stream_news(self):
           """Stream real-time news"""
           # Use RSS + polling or news API WebSocket
   ```

2. **프론트엔드 WebSocket 클라이언트**
   ```tsx
   // frontend/src/hooks/useMarketDataWebSocket.ts

   const useMarketDataWebSocket = (symbols: string[]) => {
     const [quotes, setQuotes] = useState<Quote[]>([]);

     useEffect(() => {
       const ws = new WebSocket('ws://localhost:8001/api/market-data/ws');

       ws.onmessage = (event) => {
         const data = JSON.parse(event.data);
         setQuotes((prev) => updateQuotes(prev, data));
       };

       return () => ws.close();
     }, [symbols]);

     return quotes;
   };
   ```

**예상 기간**: 3주

---

#### Phase 2: 모바일 알림 확장 (Week 4-5)

**목표**: Push Notification + Email + SMS

**작업**:
1. **Push Notification Service**
   ```python
   # backend/services/push_notification_service.py

   from firebase_admin import messaging

   class PushNotificationService:
       """Send push notifications to mobile devices"""

       async def send_conflict_alert(self, user_token: str, conflict: Dict):
           """Send conflict alert to mobile"""
           message = messaging.Message(
               notification=messaging.Notification(
                   title='⚠️ Strategy Conflict Detected',
                   body=conflict['message'],
               ),
               token=user_token,
           )
           await messaging.send_async(message)
   ```

2. **Email/SMS Service (기존 확장)**
   - SendGrid (Email)
   - Twilio (SMS)

**예상 기간**: 2주

---

#### Phase 3: Live Dashboard (Week 6)

**목표**: 실시간 업데이트 대시보드

**작업**:
1. **Dashboard WebSocket Integration**
   ```tsx
   const LiveDashboard = () => {
     const quotes = useMarketDataWebSocket(['NVDA', 'MSFT']);
     const conflicts = useConflictWebSocket();

     return (
       <Dashboard>
         <RealTimeChart data={quotes} />
         <ConflictAlert conflicts={conflicts} />
       </Dashboard>
     );
   };
   ```

**예상 기간**: 1주

---

## 3. Advanced Risk Models (30%)

### 구현 현황

#### ✅ 구현됨
- **Order Validator Hard Rules**
  - Max position size: 30%
  - Max portfolio risk: 5%
  - Min cash reserve: 5%
  - Stop loss: 0.1% - 10%

- **Basic Risk Metrics**
  - Position size 제한
  - Portfolio exposure 추적
  - Cash reserve 강제

#### ⚠️ 미완성
- **VaR (Value at Risk) 계산**
  - 목표: Historical VaR, Monte Carlo VaR

- **Sharpe Ratio / Sortino Ratio**
  - 목표: 전략별 Risk-adjusted return

- **Beta / Correlation Analysis**
  - 목표: 포트폴리오 상관관계 분석

### 구현률 분석

| 컴포넌트 | 구현률 | 비고 |
|---------|--------|------|
| **Hard Rules Validator** | 100% | 완료 |
| **Basic Risk Metrics** | 100% | 완료 |
| **VaR Calculation** | 0% | 미완 |
| **Sharpe/Sortino Ratio** | 0% | 미완 |
| **Beta/Correlation** | 0% | 미완 |

**전체 구현률**: 30% (5개 중 1.5개 완료)

---

### 완성 계획

#### Phase 1: VaR 계산 (Week 1-2)

**목표**: Historical VaR 및 Monte Carlo VaR

**작업**:
1. **VaR Calculator**
   ```python
   # backend/analytics/var_calculator.py

   class VaRCalculator:
       """Value at Risk Calculator"""

       def calculate_historical_var(
           self,
           returns: np.ndarray,
           confidence_level: float = 0.95
       ) -> float:
           """Historical VaR calculation"""
           return np.percentile(returns, (1 - confidence_level) * 100)

       def calculate_monte_carlo_var(
           self,
           portfolio: Portfolio,
           simulations: int = 10000,
           days: int = 1
       ) -> float:
           """Monte Carlo VaR simulation"""
           # ...
   ```

2. **DB 모델 추가**
   ```python
   class PortfolioRisk(Base):
       __tablename__ = 'portfolio_risk'

       id = Column(Integer, primary_key=True)
       portfolio_id = Column(UUID, ForeignKey('portfolios.id'))
       var_1day_95 = Column(Float)  # 1-day 95% VaR
       var_1day_99 = Column(Float)  # 1-day 99% VaR
       var_10day_95 = Column(Float)  # 10-day 95% VaR
       calculated_at = Column(DateTime, default=datetime.utcnow)
   ```

**예상 기간**: 2주

---

#### Phase 2: Sharpe/Sortino Ratio (Week 3)

**목표**: Risk-adjusted return 측정

**작업**:
1. **Risk-Adjusted Return Calculator**
   ```python
   # backend/analytics/risk_adjusted_metrics.py

   class RiskAdjustedMetrics:
       """Calculate Sharpe, Sortino, Calmar ratios"""

       def calculate_sharpe_ratio(
           self,
           returns: np.ndarray,
           risk_free_rate: float = 0.04  # 4% 연간
       ) -> float:
           """Sharpe Ratio = (Return - RFR) / Std Dev"""
           excess_return = np.mean(returns) - risk_free_rate / 252
           return excess_return / np.std(returns)

       def calculate_sortino_ratio(
           self,
           returns: np.ndarray,
           risk_free_rate: float = 0.04
       ) -> float:
           """Sortino Ratio = (Return - RFR) / Downside Dev"""
           excess_return = np.mean(returns) - risk_free_rate / 252
           downside_returns = returns[returns < 0]
           downside_std = np.std(downside_returns)
           return excess_return / downside_std
   ```

2. **전략별 Ratio 추적**
   ```python
   class StrategyPerformance(Base):
       __tablename__ = 'strategy_performance'

       strategy_id = Column(UUID, ForeignKey('strategies.id'))
       sharpe_ratio = Column(Float)
       sortino_ratio = Column(Float)
       calmar_ratio = Column(Float)
       measured_at = Column(DateTime)
   ```

**예상 기간**: 1주

---

#### Phase 3: Beta/Correlation (Week 4)

**목표**: 포트폴리오 상관관계 분석

**작업**:
1. **Correlation Analyzer**
   ```python
   # backend/analytics/correlation_analyzer.py

   class CorrelationAnalyzer:
       """Analyze portfolio correlations"""

       def calculate_beta(
           self,
           stock_returns: np.ndarray,
           market_returns: np.ndarray  # SPY
       ) -> float:
           """Calculate beta to market"""
           covariance = np.cov(stock_returns, market_returns)[0][1]
           market_variance = np.var(market_returns)
           return covariance / market_variance

       def calculate_correlation_matrix(
           self,
           portfolio_returns: Dict[str, np.ndarray]
       ) -> pd.DataFrame:
           """Calculate correlation matrix"""
           return pd.DataFrame(portfolio_returns).corr()
   ```

2. **Diversification Score**
   ```python
   def calculate_diversification_score(
       self,
       correlation_matrix: pd.DataFrame
   ) -> float:
       """Calculate diversification score (0-100)"""
       # Lower avg correlation = higher diversification
       avg_corr = correlation_matrix.values[np.triu_indices_from(correlation_matrix.values, k=1)].mean()
       return (1 - avg_corr) * 100
   ```

**예상 기간**: 1주

---

## 4. 미구현 계획 기능

### 완전 미구현 (Priority: LOW)

| 기능 | 계획 문서 | 상태 | 이유 |
|------|----------|------|------|
| **Reinforcement Learning** | `docs/deleted/08-execution-rl-spec.md` | ❌ 삭제됨 | 실험적, 복잡도 높음 |
| **Graph Neural Networks** | `docs/deleted/09-gnn-impact-spec.md` | ❌ 삭제됨 | 실험적, 데이터 부족 |
| **Multimodal Fusion** | `docs/deleted/10-multimodal-fusion-spec.md` | ❌ 삭제됨 | 실험적, 비용 높음 |
| **Advanced Options Analysis** | - | 🟡 기본만 | 옵션 거래 미지원 |
| **Multi-Currency Support** | - | 🟡 US만 | 글로벌 확장 시 필요 |
| **Real-time WebSocket** | - | 🟡 부분 | Phase 2-1 계획 |
| **Mobile App** | - | ❌ 없음 | React 웹만 존재 |

### 권장 사항

#### 유지 (Keep)
- ✅ **Advanced Options Analysis**: 기본 분석기 유지, 옵션 거래 시 확장
- ✅ **Multi-Currency Support**: US 주식 focus, 글로벌 확장 시 고려

#### 제거 (Remove)
- ❌ **RL/GNN/Multimodal**: 이미 삭제됨, 복구 불필요
  - 복잡도 대비 효과 낮음
  - 데이터/비용 요구 높음
  - 프로덕션 안정성 우려

#### 완성 (Complete)
- 🚀 **Real-time WebSocket**: 높은 우선순위 (Phase 2-1)
- 🚀 **Mobile App**: 중기 계획 (React Native 또는 PWA)

---

## 5. 우선순위 및 완성 계획

### 우선순위 매트릭스

| 기능 | 구현률 | 사용자 가치 | 기술 복잡도 | 우선순위 |
|------|--------|------------|------------|----------|
| **Persona-based Trading** | 50% | HIGH | MEDIUM | 🥇 P1 |
| **Real-time Execution** | 70% | HIGH | HIGH | 🥈 P2 |
| **Advanced Risk Models** | 30% | MEDIUM | LOW | 🥉 P3 |

### 전체 완성 계획

#### Q1 2026 (현재 ~ 2026-03-31)

**Week 1-6: Persona-based Trading 완성**
- Week 1-2: Daily Briefing 페르소나 분리
- Week 3-4: UI 통합
- Week 5-6: 리포트별 페르소나 적용

**Week 7-12: Real-time Execution 완성**
- Week 7-9: 실시간 시장 데이터 WebSocket
- Week 10-11: 모바일 알림 확장
- Week 12: Live Dashboard

#### Q2 2026 (2026-04-01 ~ 2026-06-30)

**Week 1-4: Advanced Risk Models 완성**
- Week 1-2: VaR 계산
- Week 3: Sharpe/Sortino Ratio
- Week 4: Beta/Correlation

**Week 5-8: Mobile App (신규)**
- Week 5-6: PWA 설계
- Week 7-8: 기본 기능 구현

### 최종 목표 (2026-06-30)

- ✅ **Persona-based Trading**: 100% 완성
- ✅ **Real-time Execution**: 100% 완성
- ✅ **Advanced Risk Models**: 100% 완성
- 🆕 **Mobile App (PWA)**: 80% 완성 (MVP)

---

## 참고 문서

- [SYSTEM_STATUS_MAP.md](SYSTEM_STATUS_MAP.md) - 전체 시스템 현황
- [LEGACY_CLEANUP_PLAN.md](LEGACY_CLEANUP_PLAN.md) - 레거시 정리 계획
- [Market Intelligence Roadmap](../docs/planning/260118_market_intelligence_roadmap.md)
- [Multi-Strategy Orchestration](../docs/planning/01-multi-strategy-orchestration-plan.md)

---

**작성자**: AI Trading System Team
**최종 업데이트**: 2026-01-25
**다음 리뷰**: 2026-02-01

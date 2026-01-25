# 프론트엔드 통합 구현 계획 (Daily Briefing 데이터 파이프라인 포함)

## 목표
백엔드 AI 결과물(리포트, 의사결정, 주문 상태)을 프론트엔드 UI에 통합하여 사용자가 피드백을 주고 상황을 파악할 수 있도록 합니다.
또한, Daily Briefing을 위한 포괄적인 데이터 파이프라인(Gap, Dark Pool, Sector, Sentiment, Earnings, Macro)을 구축합니다.

## 사용자 검토 필요 사항
현재 없음.

## 변경 제안

### Backend (Data & Analytics)
#### [NEW] [daily_briefing_service.py](file:///D:/code/ai-trading-system/backend/services/daily_briefing_service.py)
- **Role**: Orchestrator that gathers data from 5 sources and generates the Markdown report.
- **Data Sources**:
  1. **Pre-market Gap**: `MarketGapAnalyzer` (using KISBroker/yfinance).
  2. **Dark Pool/Options**: `OptionsDataFetcher` (using `options_flow_tracker.py`).
  3. **Sector Rotation**: `SectorRotationAnalyzer` (new logic using yfinance for XLK, XLV, etc.).
  4. **Sentiment**: `NewsPoller` aggregation (using `NewsAnalysis` DB records).
  5. **Earnings**: `EarningsCalendarService` (using yfinance calendar).
  6. **Macro Economy**: `EconomicCalendarService` (Tracking Key Events: CPI, PPI, FOMC, Unemployment Rate).

#### [MODIFY] [models.py](file:///D:/code/ai-trading-system/backend/database/models.py)
- **New Model**: `DailyBriefing`
  - `id`: Integer, PK
  - `date`: Date, Unique
  - `content`: Text (Markdown)
  - `metrics`: JSONB (Structured data for charts if needed)
  - `created_at`: DateTime

### Backend (API 지원)
#### [MODIFY] [orders_router.py](file:///D:/code/ai-trading-system/backend/api/orders_router.py)
- 새로운 `Order` 필드(`status`, `filled_quantity`, `order_metadata`)를 포함하도록 응답 모델 업데이트.
- `OrderState` 열거형(Enum)이 올바르게 직렬화되도록 보장.

#### [NEW] [feedback_router.py](file:///D:/code/ai-trading-system/backend/api/feedback_router.py)
- AI 의사결정/시그널에 대한 사용자 피드백(좋아요/싫어요) 제출용 API 엔드포인트.

### Frontend (React/Next.js)
#### [NEW] [FeedbackComponent.tsx](file:///D:/code/ai-trading-system/frontend/src/components/FeedbackComponent.tsx)
- 시그널/주문에 투표할 수 있는 UI 컴포넌트.

#### [NEW] [ReportViewer.tsx](file:///D:/code/ai-trading-system/frontend/src/components/ReportViewer.tsx)
- AI가 생성한 마크다운/HTML 리포트를 렌더링하는 뷰어.

#### [MODIFY] [Dashboard.tsx](file:///D:/code/ai-trading-system/frontend/src/pages/Dashboard.tsx)
- "Daily Briefing" 탭 추가.
- `ReportViewer` 및 `FeedbackComponent` 통합.

## 검증 계획
### 수동 검증
- 프론트엔드 실행 (`npm run dev`).
- 대시보드에 새로운 탭이 로드되는지 확인.
- 리포트 뷰어가 최신 생성 리포트를 표시하는지 확인.
- 피드백을 제출하고 백엔드에 저장되는지 확인.

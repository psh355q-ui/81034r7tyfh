# 03. AI Trading System - 구현 현황 및 코드 위치

**문서 시리즈**: AI Trading System Spec-Kit 문서  
**문서 번호**: 03/06  
**작성일**: 2025-12-06  
**이전**: [251210_02_Development_Roadmap.md](251210_02_Development_Roadmap.md) | **다음**: [04_Next_Action_Plan.md](04_Next_Action_Plan.md)

---

## 📁 Backend 구조 (d:\code\ai-trading-system\backend\)

### AI 모듈 (`ai/` - 58개 파일)

| 모듈 | 파일 | 설명 | Phase |
|------|------|------|-------|
| **Core AI Clients** | | | |
| Trading Agent | `trading_agent.py` | 10-Point Checklist 기반 매매 결정 | 3 |
| Claude Client | `claude_client.py` | Claude API 클라이언트 | 3 |
| ChatGPT Client | `chatgpt_client.py` | ChatGPT API 클라이언트 | 5 |
| Gemini Client | `gemini_client.py` | Gemini API 클라이언트 | 14 |
| AI Factory | `ai_client_factory.py` | Model-Agnostic Factory | 14 |
| Failover Manager | `failover_manager.py` | AI API 장애 복구 | 7 |
| **Consensus/** (3개) | | **3-AI 투표 시스템** | E1 |
|| `consensus_engine.py` | 3-AI 투표 엔진 (550 lines) | E1 |
|| `consensus_models.py` | 투표 데이터 모델 (250 lines) | E1 |
|| `voting_rules.py` | 비대칭 의사결정 규칙 | E1 |
| **Reasoning/** (5개) | | **Deep Reasoning 전략** | 14 |
|| `deep_reasoning.py` | 3-Step CoT 전략 | 14 |
|| `cot_prompts.py` | Chain-of-Thought 프롬프트 | 14 |
|| `rag_deep_reasoning.py` | RAG 기반 Deep Reasoning | 14 |
|| `models.py` | Reasoning 데이터 모델 | 14 |
| **Strategies/** (3개) | | **트레이딩 전략** | |
|| `dca_strategy.py` | DCA (Dollar Cost Averaging) | B |
|| `deep_reasoning_strategy.py` | Deep Reasoning 매매 전략 | 14 |
|| `global_macro_strategy.py` | 글로벌 매크로 전략 | C |
| **Economics/** (3개) | | **AI 칩 경제 분석** | A |
|| `unit_economics_engine.py` | Unit Economics 엔진 | A |
|| `chip_efficiency_comparator.py` | AI 칩 효율성 비교 | A |
| **News/** (2개) | | **뉴스 분석** | A |
|| `news_segment_classifier.py` | 뉴스 세그먼트 분류 | A |
| **Monitoring/** (2개) | | **AI 모니터링** | C |
|| `bias_monitor.py` | Bias 감지 및 모니터링 | C |
| **Debate/** (2개) | | **AI 토론 엔진** | C |
|| `ai_debate_engine.py` | AI 토론 엔진 | C |
| **Collective/** (2개) | | **집단 지성** | C |
|| `ai_role_manager.py` | AI 역할 관리자 | C |
| **Core/** (2개) | | **결정 프로토콜** | E |
|| `decision_protocol.py` | 의사결정 프로토콜 | E |
| **Cost/** (2개) | | **비용 관리** | B |
|| `subscription_manager.py` | AI 구독 관리 | B |
| **Macro/** (3개) | | **매크로 분석** | C |
|| `country_risk_engine.py` | 국가 리스크 엔진 | C |
|| `global_market_map.py` | 글로벌 시장 맵 | C |
| **Meta/** (4개) | | **메타 학습** | C |
|| `agent_weight_trainer.py` | AI 가중치 학습 | C |
|| `debate_logger.py` | 토론 로거 | C |
|| `strategy_refiner.py` | 전략 개선 | C |
| **Risk/** (2개) | | **리스크 관리** | B |
|| `theme_risk_detector.py` | 테마 리스크 탐지 | B |
| **RAG \u0026 분석** | | | |
| RAG Analysis | `rag_enhanced_analysis.py` | RAG 기반 분석 | 13 |
| Embedding Engine | `embedding_engine.py` | 임베딩 엔진 | 13 |
| Vector Search | `vector_search.py` | 벡터 검색 | 13 |
| SEC Analyzer | `sec_analyzer.py` | SEC 문서 분석 | 15 |
| SEC Prompts | `sec_prompts.py` | SEC 분석 프롬프트 | 15 |
| **기타** | | | |
| Market Regime | `market_regime.py` | 시장 체제 감지 | 15.5 |
| Regime Detector | `regime_detector.py` | 체제 탐지기 | 15.5 |
| Ensemble Optimizer | `ensemble_optimizer.py` | 앙상블 최적화 | 5 |
| Model Comparison | `model_comparison.py` | 모델 비교 | 14 |
| Analysis Validator | `analysis_validator.py` | 분석 검증 | 9 |
| AI Review Models | `ai_review_models.py` | AI 검토 모델 | 12 |
| Enhanced Cache | `enhanced_analysis_cache.py` | 분석 캐시 | 7 |
| News Context Filter | `news_context_filter.py` | 뉴스 컨텍스트 필터 | 8 |
| Trading Terms Parser | `trading_terms_parser.py` | 트레이딩 용어 파서 | 3 |

### 데이터 레이어 (`data/` - 42개 파일)

| 모듈 | 파일/폴더 | 설명 | Phase |
|------|-----------|------|-------|
| **feature_store/** | `store.py` | FeatureStore 메인 (600 lines) | 1 |
|| `cache_layer.py` | Redis + TimescaleDB (400 lines) | 1 |
|| `features.py` | Feature 계산 로직 (500 lines) | 1 |
| **collectors/** | `yahoo_collector.py` | Yahoo Finance 수집 | 2 |
|| `sec_collector.py` | SEC EDGAR 수집 | 13 |
|| `incremental_updater.py` | 증분 업데이트 | 16 |
| **knowledge_graph/** | `knowledge_graph.py` | 기업 관계 그래프 (450 lines) | 14 |
| **vector_store/** | 3개 파일 | pgvector 벡터 DB | 13 |
| News | `news_models.py` | 뉴스 DB 모델 (SQLite) | 8 |
|| `news_analyzer.py` | AI 뉴스 분석 (700 lines) | 8 |
|| `rss_crawler.py` | RSS 피드 크롤러 | 8 |

### 시그널 \u0026 백테스팅 (`signals/`, `backtesting/`)

| 모듈 | 파일 | 설명 | Phase |
|------|------|------|-------|
| Signal | `news_signal_generator.py` | 뉴스 기반 시그널 | 9 |
|| `signal_validator.py` | 시그널 검증 | 9 |
|| `sector_throttling.py` | 섹터별 포지션 제한 | 9 |
| Backtest | `signal_backtest_engine.py` | 뉴스 시그널 백테스트 | 10 |
|| `pit_backtest_engine.py` | Point-in-Time 엔진 | C |
|| `event_driven.py` | 이벤트 기반 시뮬레이션 | 4 |
|| `ab_backtest.py` | A/B 백테스트 (Keyword vs CoT) | 14 |

### API 라우터 (`api/` - 36개 파일)

| 중요도 | 파일 | 엔드포인트 | Phase |
|-------|------|-----------|-------|
| ⭐⭐⭐ | `consensus_router.py` | `/api/consensus/*` (5개) | E1 |
| ⭐⭐⭐ | `reasoning_api.py` | `/api/reasoning/*` | 14 |
| ⭐⭐⭐ | `signals_router.py` | `/api/signals/*` | 9 |
| ⭐⭐⭐ | `ai_signals_router.py` | `/api/ai-signals/*` | E |
| ⭐⭐⭐ | `news_router.py` | `/api/news/*` | 8 |
| ⭐⭐ | `backtest_router.py` | `/api/backtest/*` | 10 |
| ⭐⭐ | `kis_integration_router.py` | `/api/kis/*` (KIS API) | 11 |
| ⭐⭐ | `kis_sync_router.py` | `/api/kis-sync/*` | 11 |
| ⭐⭐ | `position_router.py` | `/api/positions/*` | E3 |
| ⭐⭐ | `auto_trade_router.py` | `/api/auto-trade/*` | B |
| ⭐⭐ | `reports_router.py` | `/api/reports/*` | 15 |
| ⭐⭐ | `monitoring_router.py` | `/api/monitoring/*` | 7 |
| ⭐ | `ai_review_router.py` | `/api/ai-review/*` | 12 |
| ⭐ | `ai_chat_router.py` | `/api/ai-chat/*` | 14 |
| ⭐ | `ai_quality_router.py` | `/api/ai-quality/*` | C |
| ⭐ | `ceo_analysis_router.py` | `/api/ceo-analysis/*` | 15 |
| ⭐ | `sec_router.py` | `/api/sec/*` | 15 |
| ⭐ | `sec_semantic_search.py` | `/api/sec-search/*` | 15 |
| ⭐ | `feeds_router.py` | `/api/feeds/*` (RSS 관리) | 16 |
| ⭐ | `incremental_router.py` | `/api/incremental/*` | 16 |
| ⭐ | `forensics_router.py` | `/api/forensics/*` | 15 |
| ⭐ | `options_flow_router.py` | `/api/options-flow/*` | 15 |
| ⭐ | `global_macro_router.py` | `/api/global-macro/*` | C |
| ⭐ | `tax_routes.py` | `/api/tax/*` | Option 10 |
| ⭐ | `notifications_router.py` | `/api/notifications/*` | 9 |
| ⭐ | `logs_router.py` | `/api/logs/*` | 7 |
| ⭐ | `auth_router.py` | `/api/auth/*` | 7 |
| ⭐ | `phase_integration_router.py` | `/api/phase/*` | E |
| ⭐ | `cost_monitoring.py` | `/api/cost/*` | B |
| ⭐ | `news_filter.py` | `/api/news-filter/*` | 8 |
| ⭐ | `simple_news_router.py` | `/api/simple-news/*` | 8 |
| | `gemini_free_router.py` | `/api/gemini-free/*` | 14 |
| | `mock_router.py` | `/api/mock/*` (테스트용) | - |
| | `fix_db_errors.py` | DB 오류 수정 유틸 | - |
| | `main.py` | API 메인 진입점 (별도) | - |

### 자동화 \u0026 매크로 (`automation/`, `analytics/`)

| 모듈 | 파일 | 설명 | Phase |
|------|------|------|-------|
| **automation/** | `auto_trading_scheduler.py` | APScheduler 24시간 스케줄러 | B |
|| `signal_to_order_converter.py` | Constitution 6+4 규칙 | B |
| **analytics/** | `buffett_index_monitor.py` | 시장 과열 탐지 | B |
|| `peri_calculator.py` | 정책 리스크 지수 | B |
|| `performance_attribution.py` | 성과 귀속 분석 | 15.5 |
|| `risk_analytics.py` | VaR, CVaR, Stress Test | 15.5 |
|| `trade_analytics.py` | 거래 분석 | 15.5 |

### 보안 (`security/` - 4개 파일)

| 파일 | 방어 위협 | 방어율 | 코드량 |
|------|----------|--------|--------|
| `input_guard.py` | Prompt Injection | 95% | 450 lines |
| `webhook_security.py` | SSRF, MITM, Replay | 100% | 380 lines |
| `unicode_security.py` | Homograph Attack | 85% | 330 lines |
| `url_security.py` | Data Exfiltration | 90% | 407 lines |

### 브로커 \u0026 실행 (`brokers/`, `execution/`)

| 모듈 | 파일 | 설명 | Phase |
|------|------|------|-------|
| **brokers/** | `kis_broker.py` | 한국투자증권 API (1,100 lines) | 11 |
| **execution/** | `smart_execution.py` | TWAP/VWAP 알고리즘 | 6 |
|| `broker.py` | Broker 추상화 | 6 |

### 모니터링 \u0026 알림 (`monitoring/`, `notifications/`)

| 모듈 | 파일 | 설명 | Phase |
|------|------|------|-------|
| **monitoring/** | `metrics_collector.py` | Prometheus 메트릭 | 7 |
|| `health_monitor.py` | Health Check | 7 |
|| `alert_manager.py` | 알림 관리 | 7 |
|| `cost_analytics.py` | AI 비용 추적 | 7 |
| **notifications/** | `telegram_notifier.py` | Telegram Bot | 9 |
|| `slack_notifier.py` | Slack Webhook | 9 |

### 스키마 \u0026 DB (`schemas/`, `database/`)

| 파일 | 설명 | Phase |
|------|------|-------|
| `schemas/base_schema.py` | Pydantic 모델 (SignalAction 확장) | 0, E |
| `database/models.py` | SQLAlchemy 모델 (Position 등) | E3 |

---

## 📁 Frontend 구조 (d:\code\ai-trading-system\frontend\src\)

### 페이지 (`pages/`)

| 파일 | 설명 | 코드량 |
|------|------|--------|
| `Dashboard.tsx` | 메인 대시보드 (포트폴리오, 시그널) | ~800 lines |
| `AdvancedAnalytics.tsx` | 성과/리스크/트레이드 분석 | ~1,200 lines |
| `CEOAnalysis.tsx` | SEC CEO 발언 분석 | ~600 lines |
| `RssFeedManagement.tsx` | RSS 피드 관리 UI | ~500 lines |
| `AIReviewPage.tsx` | AI 검토 결과 | ~450 lines |
| `Analysis.tsx` | 종목 분석 | ~700 lines |
| `Reports.tsx` | 리포트 생성/조회 | ~550 lines |
| `NewsAggregation.tsx` | 뉴스 모아보기 | ~600 lines |

### 컴포넌트 (`components/`)

| 폴더 | 주요 컴포넌트 | 설명 |
|------|-------------|------|
| `Analytics/` | `PerformanceAttribution.tsx` | 성과 귀속 차트 |
|| `RiskAnalytics.tsx` | VaR, CVaR 시각화 |
|| `TradeAnalytics.tsx` | 거래 패턴 분석 |
| `Layout/` | `Sidebar.tsx`, `Header.tsx` | 레이아웃 구성 |
| `common/` | 재사용 가능 컴포넌트 | 버튼, 카드, 모달 등 |

### 서비스 (`services/`)

| 파일 | 설명 |
|------|------|
| `api.ts` | 메인 API 클라이언트 (Axios) |
| `analyticsApi.ts` | Advanced Analytics API |
| `reportsApi.ts` | Reports API |
| `consensusApi.ts` | Consensus API (예정) |

---

## 📊 문서 위치 (d:\code\ai-trading-system\docs\)

### 핵심 가이드 (7개)

| 파일 | 설명 | 페이지 수 |
|------|------|----------|
| `251210_MASTER_GUIDE.md` | 전체 시스템 가이드 | 2,229 lines |
| `README.md` | 프로젝트 README | 749 lines |
| `251210_Project_Total_Docs.md` | 종합 프로젝트 문서 (최신) | 30,000+ words |
| `251210_NEXT_STEPS.md` | 다음 작업 계획 (v2.0) | 10 options |
| `251210_QUICKSTART.md` | 5분 빠른 시작 | - |
| `251210_API_DOCUMENTATION.md` | 전체 API 레퍼런스 | - |
| `251210_FINAL_SYSTEM_REPORT.md` | 시스템 완성 보고서 | 416 lines |

### Phase 완료 보고서 (10개)

- `251210_PHASE_0_COMPLETION_REPORT.md` (BaseSchema)
- `251210_PHASE_A_COMPLETION_REPORT.md` (AI 칩 분석, 2,200 lines)
- `251210_PHASE_B_COMPLETION_REPORT.md` (자동화, 1,340 lines)
- `251210_PHASE_C_COMPLETE_REPORT.md` (고급 AI, 2,130 lines)
- `251210_PHASE_BAC_COMPLETE.md` (통합)
- `PHASE_E1_Consensus_Engine_Complete.md` (Consensus, 950 lines)
- `251210_10_Phase_E1_Consensus_Engine_Complete.md` (상세, 534 lines)
- 기타 Phase 완료 보고서

### 기능별 가이드 (20+개)

- `251210_Phase14_DeepReasoning.md` (410 lines)
- `251210_RAG_251210_QUICKSTART.md` (RAG 시작)
- `251210_KIS_INTEGRATION_COMPLETE.md` (KIS API)
- `251210_Live_Trading.md`, `251210_PaperTrading_Guide.md`
- `251210_Production_Deployment_Guide.md`, `251210_Production_Monitoring_Guide.md`
- `251210_Telegram_Notifications.md`
- `251210_Network_Access_Guide.md`, `251210_NAS_Deployment_Guide.md`
- 기타 설정 \u0026 가이드

### Spec-Kit 스타일 문서 (신규, 6개)

- `251210_00_Project_Overview.md` (프로젝트 종합 개요) ⭐
- `251210_01_System_Architecture.md` (시스템 아키텍처) ⭐
- `251210_02_Development_Roadmap.md` (개발 로드맵) ⭐
- `251210_03_Implementation_Status.md` (이 문서) ⭐
- `04_Next_Action_Plan.md` (다음 작업 계획) ⭐
- `05_Gap_Analysis.md` (갭 분석) ⭐

---

## 🗂️ Docker 구성 (`docker-compose.yml`)

```yaml
services:
  redis:           # Port 6379
  timescaledb:     # Port 5432
  postgres:        # Port 5433 (RAG + pgvector)
  prometheus:      # Port 9090
  grafana:         # Port 3001
```

---

## 📈 코드 통계 종합

### Backend 파일 통계 (최신)
```
총 Python 파일: ~300+개
총 코드량: 45,000+ lines (추정)
디렉토리 구조:
  - ai/: 58개 모듈 (~8,000 lines)
    - consensus/: 3개 파일
    - reasoning/: 5개 파일
    - strategies/: 3개 파일
    - economics/: 3개 파일
    - news/: 2개 파일
    - monitoring/: 2개 파일
    - debate/: 2개 파일
    - collective/: 2개 파일
    - core/: 2개 파일
    - cost/: 2개 파일
    - macro/: 3개 파일
    - meta/: 4개 파일
    - risk/: 2개 파일
  - api/: 36개 라우터 (~10,000 lines)
  - data/: 42개 모듈 (~8,000 lines)
  - backtesting/: 11개 파일 (~4,000 lines)
  - analytics/: 6개 파일 (~3,000 lines)
  - security/: 4개 파일 (~1,567 lines)
  - monitoring/: 5개 파일 (~2,000 lines)
  - notifications/: 2개 파일 (~800 lines)
  - brokers/: 2개 파일 (~1,500 lines)
  - execution/: 2개 파일 (~800 lines)
  - signals/: 3개 파일 (~1,500 lines)
  - 기타: ~3,833 lines
```

### Frontend 파일 통계
```
총 TypeScript/TSX 파일: ~80개
총 코드량: 12,000+ lines
페이지: 8개 (~5,000 lines)
컴포넌트: ~40개 (~4,000 lines)
서비스: 5개 (~1,000 lines)
기타: ~2,000 lines
```

### 문서 통계
```
Markdown 파일: 89개
주요 가이드: 7개
Phase 보고서: 10개
기능 가이드: 20+개
Spec-Kit 문서: 6개 (신규)
총 단어 수: 약 100,000+ words
```

---

## 🔍 주요 파일 빠른 찾기

### 핵심 진입점
```
Backend: backend/main.py (FastAPI app)
Frontend: frontend/src/App.tsx
Docker: docker-compose.yml
환경 변수: .env
```

### Phase별 핵심 파일
```
Phase 1: backend/data/feature_store/store.py
Phase 3: backend/ai/trading_agent.py
Phase 8: backend/data/news_analyzer.py
Phase 10: backend/backtesting/signal_backtest_engine.py
Phase 11: backend/brokers/kis_broker.py
Phase 14: backend/ai/reasoning/deep_reasoning.py
Phase E1: backend/ai/consensus/consensus_engine.py
Security: backend/security/input_guard.py
```

### 자주 사용하는 테스트
```
Feature Store: backend/test_feature_store_full.py
Trading Agent: backend/test_trading_agent.py
KIS API: test_kis_integration.py
Phase E: scripts/test_consensus.py (생성 예정)
```

---

## 🔗 관련 문서

- **이전**: [251210_02_Development_Roadmap.md](251210_02_Development_Roadmap.md)
- **다음**: [04_Next_Action_Plan.md](04_Next_Action_Plan.md)
- **참조**: [251210_Project_Total_Docs.md](251210_Project_Total_Docs.md)

---

**문서 버전**: 1.1
**작성자**: AI Trading System Team
**마지막 업데이트**: 2025-12-12
**변경 사항**: 실제 파일 개수 반영 (AI: 58개, API: 36개), 디렉토리 구조 상세화

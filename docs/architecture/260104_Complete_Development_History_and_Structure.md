# AI Trading System - 완전한 개발 히스토리 및 프로젝트 구조

**작성일**: 2026-01-04
**목적**: 프로젝트 전체 개발 히스토리 및 현재 시스템 구조 종합 정리
**문서 버전**: 1.0

---

## 📋 목차

1. [프로젝트 개요](#1-프로젝트-개요)
2. [개발 타임라인 (시간순)](#2-개발-타임라인-시간순)
3. [프로젝트 구조 (상세)](#3-프로젝트-구조-상세)
4. [핵심 시스템 아키텍처](#4-핵심-시스템-아키텍처)
5. [현재 상태 (2026-01-04)](#5-현재-상태-2026-01-04)
6. [주요 기능 목록](#6-주요-기능-목록)
7. [데이터베이스 스키마](#7-데이터베이스-스키마)
8. [API 엔드포인트 전체](#8-api-엔드포인트-전체)
9. [문서 구조](#9-문서-구조)

---

## 1. 프로젝트 개요

### 1.1 프로젝트 정보

**프로젝트명**: AI Trading System
**개발 기간**: 2024-12-20 ~ 현재 진행 중
**현재 버전**: v2.0 (MVP Production Ready)
**개발 철학**:
- AI Agent 기반 집단 지성 의사결정
- 점진적 개선 (Phase 기반 개발)
- Production-First (실거래 준비)
- 자기학습 시스템

### 1.2 시스템 특징

**핵심 개념**:
- ✅ **8개 Legacy Agent → 3+1 MVP Agent** (2025-12-31 전환 완료)
- ✅ **War Room 심의 시스템** (Weighted Voting)
- ✅ **Shadow Trading** (3개월 검증 중, 2025-12-31 시작)
- ✅ **자기학습** (Agent 가중치 자동 조정)
- ✅ **Hallucination Prevention** (3-gate 검증)
- ✅ **Position Sizing** (Risk-based formula)
- ✅ **Fast Track vs Deep Dive** (실행 라우팅)

**성과 (MVP 전환)**:
- 비용: 67% 절감 (8 agents → 3+1 agents)
- 속도: 67% 향상 (30초 → 10초)
- API 호출: 8회 → 3회

---

## 2. 개발 타임라인 (시간순)

### 2.1 초기 Phase (2024-12 ~ 2025-12-14)

#### Phase 0-15 (문서 105개, 2025-12-10 집중)

**Phase 0**: 기본 인프라 구축
- PostgreSQL + TimescaleDB 설치
- FastAPI 백엔드 기본 구조
- React 프론트엔드 기본 구조
- `.env` 환경 설정

**Phase A-D** (2025-12-14 완료):
- Phase A: AI Skills Layer
- Phase B: Token Optimization
- Phase C: System Integration
- Phase D: Production Monitoring

**Phase E-15** (기능 확장):
- E1: Consensus Engine
- Option 1-4: 통합, 자동매매, 백테스팅, 리스크 관리
- Option 7: CI/CD Pipeline
- Option 9: ELK Stack
- Phase 14: 전체 통합
- Phase 15: Analytics & Reporting

**주요 문서** (2025-12-10):
- `251210_00_Project_Overview.md`
- `251210_01_System_Architecture.md`
- `251210_02_Development_Roadmap.md`
- `251210_PHASE_A_COMPLETION_REPORT.md` ~ `PHASE_C_COMPLETE_REPORT.md`

---

### 2.2 시스템 재설계 (2025-12-15)

**배경**: 외부 시스템 분석 및 재설계

**주요 작업**:
- 외부 시스템 분석 (251215_External_System_Analysis.md)
- 시스템 재설계 청사진 (251215_System_Redesign_Blueprint.md)
- Gap Analysis (251215_Redesign_Gap_Analysis.md)

**재설계 핵심**:
- 8개 독립 Agent 시스템 확립
- War Room 투표 시스템 도입
- Agent 가중치 시스템

**최종 정리**:
- `251215_ULTIMATE_SUMMARY.md`
- `251215_FINAL_COMPLETION_REPORT.md`

---

### 2.3 War Room 시스템 구축 (2025-12-16 ~ 2025-12-23)

#### 2025-12-16: 시스템 통합 및 War Room 초기 구현
- `251216_System_Integration_and_War_Room.md`
- War Room Guide 작성
- 8개 Agent 통합 테스트

#### 2025-12-17: 사용자 매뉴얼 작성
- `251217_User_Manual_v2.md`

#### 2025-12-19 ~ 12-23: Phase 18-25 (War Room 고도화)

**Phase 18-21** (기능 추가):
- Phase 18: War Room Debate 시스템
- Phase 19-20: 성과 추적 시스템
- Phase 21: Agent 독립 학습 시스템

**Phase 22-25** (Agent 개선):
- Phase 22: War Room 안정화
- Phase 23: War Room 테스트
- Phase 24: Agent 가중치 시스템
- Phase 25: 에이전트별 성과추적 + 가중치 자동조정

**주요 문서**:
- `251222_War_Room_Test_Results.md`
- `251223_Phase24_Complete.md`
- `251223_Phase25.4_가중치_자동조정_완료.md`

---

### 2.4 프로덕션 준비 (2025-12-27 ~ 12-29)

#### 2025-12-27: 인프라 및 배포 준비

**주요 작업**:
- Database Standards 정립
- Schema Compliance Report
- NAS Deployment Guide 작성
- Infrastructure Management

**문서**:
- `251227_Complete_System_Overview.md`
- `251227_Agent_Analysis_Report.md`
- `06_Infrastructure/` 폴더 생성 (7개 문서)

#### 2025-12-28: War Room 완성 및 14일 데이터 수집

**War Room 완성**:
- `251228_War_Room_System_Complete.md`
- `251228_Option3_Complete.md`
- War Room 통합 테스트 100% 통과

**14일 데이터 수집 시작**:
- `251228_14Day_Collection_Guide.md`
- 티커: AAPL, NVDA, MSFT
- 간격: 1시간
- 목표: 336 사이클, 1,008 데이터 포인트

#### 2025-12-29: 실거래 환경 준비

**주요 작업**:
- UnifiedShadowTracker 구현
- KIS Broker 인증 테스트 성공
- KISBrokerAdapter 구현 (240줄)
- GitHub CI/CD 파이프라인 간소화

**Phase 완료**:
- Phase 1-4 Completion Reports 작성
- `251229_Final_Integrated_Development_Plan.md`

---

### 2.5 MVP 전환 (2025-12-30 ~ 12-31)

#### 2025-12-30: Phase 29-32 완료

**Phase 29**: Extension Complete
**Phase 30-31**: 통합 완료
**Phase 32**: Correlation Complete

**문서**:
- `251230_Phase29_Extension_Complete.md`
- `251230_Phase30_31_Completion.md`
- `251230_Development_Complete.md`
- `DB_SCHEMA_VERIFICATION_REPORT.md`
- `PHASE_MASTER_INDEX.md`

#### 2025-12-31: MVP 시스템 전환 🎉

**역사적 전환점**: Legacy 8-Agent → MVP 3+1 Agent

**MVP 구현**:
- `MVP_IMPLEMENTATION_PLAN.md` 작성
- MVP Agent 5개 파일 생성:
  - `trader_agent_mvp.py` (35% weight) - Attack
  - `risk_agent_mvp.py` (35% weight) - Defense + **Position Sizing**
  - `analyst_agent_mvp.py` (30% weight) - Information
  - `pm_agent_mvp.py` - Final Decision Maker
  - `war_room_mvp.py` - Orchestrator

**Execution Layer 구현**:
- `execution_router.py` - Fast Track vs Deep Dive
- `order_validator.py` - Hard Rules (8개 규칙)
- `shadow_trading_mvp.py` - Shadow Trading Engine

**Shadow Trading Phase 1 시작**:
- 시작일: 2025-12-31
- 초기 자본: $100,000 (virtual)
- 목표 기간: 3개월 (~ 2026-03-31)
- `Shadow_Trading_Phase1_Started.md`

**최종 문서**:
- `251231_MVP_Implementation_Complete.md`
- `MVP_Integration_Verification.md`
- `MVP_Frontend_Integration_Complete.md`

**성과**:
- 비용 67% 절감
- 속도 67% 향상
- API 호출 8회 → 3회

---

### 2.6 Claude 신기능 통합 (2026-01-01)

#### Deep Reasoning 통합

**작업**:
- Deep Reasoning 분석 이력 DB 저장 구현
- REST API 엔드포인트 추가
- 프론트엔드 통합

**문서**:
- `260101_Deep_Reasoning_History_Implementation.md`
- `260101_Work_Summary.md`

#### Claude 신기능 분석

**작업**:
- Prompt Caching 분석
- Structured Outputs 분석
- Extended Thinking 분석
- PDF Support 분석

**문서**:
- `260101_Claude_Features_Analysis.md`
- `260101_Claude_Features_Implementation_Plan.md`

---

### 2.7 War Room MVP Skills 전환 (2026-01-02)

#### Skills Migration 완료

**배경**: Agent Skills 형식으로 전환

**작업**:
- 5개 Skill 파일 생성 (SKILL.md + handler.py)
- Dual Mode 지원 (Direct Class vs Skill Handler)
- API Router 업데이트

**파일**:
- `backend/ai/skills/war_room_mvp/` 폴더 생성
  - `trader_agent_mvp/SKILL.md` + `handler.py`
  - `risk_agent_mvp/SKILL.md` + `handler.py`
  - `analyst_agent_mvp/SKILL.md` + `handler.py`
  - `pm_agent_mvp/SKILL.md` + `handler.py`
  - `orchestrator_mvp/SKILL.md` + `handler.py`

**환경 변수**:
```bash
WAR_ROOM_MVP_USE_SKILLS=false  # true: Skill mode, false: Direct mode
```

**문서**:
- `260102_War_Room_MVP_Skills_Migration_Plan.md` (1,096줄)
- `260102_War_Room_MVP_Skills_Final_Report.md`
- `260102_War_Room_Phase_B_Implementation_Plan.md`

#### 데이터베이스 최적화 Phase 1

**작업**:
- 복합 인덱스 추가 (models.py)
- N+1 쿼리 패턴 제거 (repository.py)
- TTL 캐싱 구현 (5분 캐시)

**성과**:
- War Room MVP DB 쿼리: 0.5-1.0s → 0.3-0.5s
- War Room MVP 전체 응답: 12.76s (목표 <15s 달성)

**문서**:
- `260102_Database_Optimization_Plan.md` (884줄)

#### 프론트엔드 Bug Fix

**작업**:
- News Page 500 에러 수정 (10개 attribute 불일치)
- 한국어 날짜 포맷팅 추가

**문서**:
- `260102_Frontend_News_Page_Fix.md` (596줄)

#### Data Backfill 수정

**작업**:
- `data_collection_progress` 테이블 생성
- `news_sources` 테이블 생성
- Yahoo Finance API 제한사항 검증 추가

**문서**:
- `260102_Data_Backfill_Fix.md` (456줄)
- `260102_Price_Backfill_Validation.md` (371줄)

#### Claude Code Templates 검토

**작업**:
- 600+ 템플릿 검토
- 15개 유용한 컴포넌트 식별

**문서**:
- `260102_Claude_Code_Templates_Review.md` (894줄)

#### Shadow Trading Week 1

**성과**:
- 2 포지션 진입: NKE, LULU
- 1 포지션 청산: LULU (+$13.85)
- 1 포지션 유지: NKE (진행 중)

**문서**:
- `Shadow_Trading_Week1_Report.md`

#### 일일 요약

**문서**:
- `Work_Log_20260102.md` (468줄)
- `260102_Daily_Summary.md`

---

### 2.8 Claude Code Templates 구현 (2026-01-03)

#### P1-P5 구현 계획 수립

**P1 (High Priority)**:
- /generate-tests Command (테스트 자동화)
- React Performance Optimizer
- Auto Git Hooks

**P2-P5** (Medium-Low):
- Security Auditor Agent
- DevOps Engineer Agent
- Performance Monitoring
- Data Scientist Agent (Shadow Trading Analytics)
- NLP Engineer Agent (Local Embeddings)

**문서**:
- `260103_Claude_Code_Templates_Implementation_Plan.md` (1,183줄)
- `260103_Remaining_Components_Implementation_Plan.md` (1,891줄)
- `260103_Security_DevOps_Advanced_Plan.md` (39,114 tokens, 첫 100줄만)

#### Shadow Trading 데이터 복원

**작업**:
- DB 테이블 생성:
  - `shadow_trading_sessions`
  - `shadow_trading_positions`
  - `agent_weights_history`
- Kill Switch 통합 검증
- Telegram 알림 테스트

**문서**:
- `Work_Log_20260103.md` (473줄)

#### Daily Report 생성 시스템 계획

**작업**:
- 일일 PDF 보고서 자동 생성 시스템 설계
- 5개 섹션: Shadow Trading, War Room, Deep Reasoning, 배당주, 성과 차트
- Telegram + 로컬 저장

**문서**:
- `260103_Daily_Report_Generation_Pipeline` (1,231줄)

---

### 2.9 즉시 착수 (2026-01-04)

#### Shadow Trading 모니터링 스크립트 개선

**작업**:
- API 엔드포인트 개선 (`/shadow/status`)
- 포지션 세부 정보 테이블 추가
- Stop Loss 체크 로직 구현
- Decimal/float 타입 충돌 해결

**현재 포지션** (2026-01-04 18:00):
- NKE: 259주, Entry $63.03, Current $63.28, **+$64.75**
- AAPL: 10주, Entry $150.00, Current $271.01, **+$1,210.10**
- **Total P&L: +$1,274.85 (+1.27%)**

**파일**:
- `backend/routers/war_room_mvp_router.py` (수정)
- `backend/scripts/shadow_trading_monitor.py` (수정)

#### Macro Context Updater 검증

**작업**:
- 기존 구현 확인 (`backend/automation/macro_context_updater.py`, 373줄)
- 실행 테스트 완료
- Claude API 통합 정상 작동

**결과** (2026-01-04):
- Regime: RISK_ON
- Fed Stance: HAWKISH
- VIX: 15.5 (NORMAL)
- S&P 500 Trend: STRONG_UPTREND

**문서**:
- `Work_Log_20260104.md` (351줄)

---

## 3. 프로젝트 구조 (상세)

### 3.1 전체 디렉토리 구조

```
ai-trading-system/
├── backend/                    # FastAPI 백엔드
│   ├── ai/                    # AI Agent 시스템
│   │   ├── mvp/              # MVP Agents (3+1) ⭐ ACTIVE
│   │   │   ├── trader_agent_mvp.py      # 35% weight, Attack
│   │   │   ├── risk_agent_mvp.py        # 35% weight, Defense + Position Sizing
│   │   │   ├── analyst_agent_mvp.py     # 30% weight, Information
│   │   │   ├── pm_agent_mvp.py          # Final Decision Maker
│   │   │   └── war_room_mvp.py          # Orchestrator
│   │   │
│   │   ├── skills/           # Agent Skills (NEW, 2026-01-02)
│   │   │   └── war_room_mvp/
│   │   │       ├── trader_agent_mvp/
│   │   │       │   ├── SKILL.md
│   │   │       │   └── handler.py
│   │   │       ├── risk_agent_mvp/
│   │   │       ├── analyst_agent_mvp/
│   │   │       ├── pm_agent_mvp/
│   │   │       └── orchestrator_mvp/
│   │   │
│   │   ├── legacy/           # Legacy 8 Agents (DEPRECATED)
│   │   │   └── debate/
│   │   │       ├── trader_agent.py
│   │   │       ├── risk_agent.py
│   │   │       ├── sentiment_agent.py
│   │   │       ├── news_agent.py
│   │   │       ├── analyst_agent.py
│   │   │       ├── macro_agent.py
│   │   │       ├── institutional_agent.py
│   │   │       └── chip_war_agent.py
│   │   │
│   │   ├── learning/         # 자기학습 시스템
│   │   │   ├── agent_weight_adjuster.py
│   │   │   ├── agent_weight_manager.py
│   │   │   ├── news_agent_learning.py
│   │   │   ├── trader_agent_learning.py
│   │   │   └── remaining_agents_learning.py
│   │   │
│   │   ├── war_room/         # War Room 유틸리티
│   │   │   ├── shadow_trading_tracker.py  # UnifiedShadowTracker
│   │   │   └── debate_visualizer.py
│   │   │
│   │   └── reasoning/        # Deep Reasoning
│   │       └── deep_reasoning_store.py
│   │
│   ├── api/                  # API 라우터 (53개 파일)
│   │   ├── war_room_mvp_router.py         # War Room MVP API
│   │   ├── war_room_analytics_router.py   # Analytics API
│   │   ├── data_backfill_router.py        # 데이터 백필
│   │   ├── backtest_router.py
│   │   ├── ai_signals_router.py
│   │   └── ... (50+ routers)
│   │
│   ├── execution/            # 실행 레이어
│   │   ├── execution_router.py         # Fast Track vs Deep Dive
│   │   ├── order_validator.py          # Hard Rules (8개)
│   │   ├── shadow_trading_mvp.py       # Shadow Trading Engine
│   │   ├── kis_broker_adapter.py       # KIS Broker Adapter (2025-12-29)
│   │   └── order_executor.py
│   │
│   ├── database/             # 데이터베이스
│   │   ├── models.py                   # SQLAlchemy Models (17개 테이블)
│   │   ├── repository.py               # Data Access Layer (1,512줄)
│   │   └── session.py
│   │
│   ├── core/                 # 핵심 모델
│   │   └── models/
│   │       ├── analytics_models.py
│   │       ├── news_models.py
│   │       ├── dividend_models.py
│   │       └── embedding_models.py
│   │
│   ├── automation/           # 자동화 스크립트
│   │   ├── macro_context_updater.py    # Macro Context 업데이트 (373줄)
│   │   └── scheduler.py
│   │
│   ├── scripts/              # 유틸리티 스크립트
│   │   ├── shadow_trading_monitor.py   # Shadow Trading 모니터링
│   │   └── collect_14day_data.py       # 14일 데이터 수집
│   │
│   ├── notifications/        # 알림 시스템
│   │   └── telegram_notifier.py
│   │
│   └── main.py               # FastAPI 애플리케이션 진입점
│
├── frontend/                 # React 프론트엔드
│   ├── src/
│   │   ├── pages/
│   │   │   ├── NewsAggregation.tsx     # 뉴스 페이지 (421줄, 2026-01-02 수정)
│   │   │   ├── DataBackfill.tsx        # 데이터 백필 (917줄)
│   │   │   ├── BacktestDashboard.tsx   # 백테스트 (896줄)
│   │   │   └── ... (40+ pages)
│   │   │
│   │   ├── components/
│   │   │   └── war-room/
│   │   │       ├── WarRoomCard.tsx     # War Room 카드 (171줄)
│   │   │       └── WarRoomList.tsx
│   │   │
│   │   └── services/
│   │       └── api.ts
│   │
│   └── package.json
│
├── docs/                     # 문서 (388개 Markdown 파일)
│   ├── 00_Spec_Kit/         # 사양 문서
│   ├── 01_Quick_Start/      # 시작 가이드
│   ├── 02_Phase_Reports/    # Phase 보고서 (90+ 파일)
│   ├── 02_Development_Plans/ # 개발 계획
│   ├── 03_Integration_Guides/ # 통합 가이드
│   ├── 04_Feature_Guides/   # 기능 가이드
│   ├── 05_Deployment/       # 배포 가이드
│   ├── 06_Infrastructure/   # 인프라 관리
│   ├── 09_User_Manuals/     # 사용자 매뉴얼
│   ├── 10_Progress_Reports/ # 진행 보고서
│   ├── 11_Archive/          # 아카이브
│   │
│   ├── Work_Log_YYYYMMDD.md  # 일일 작업 로그 (4개)
│   ├── Shadow_Trading_*.md   # Shadow Trading 보고서
│   └── PROJECT_OVERVIEW.md   # 프로젝트 개요
│
├── .env                      # 환경 변수
├── .github/
│   └── workflows/
│       └── ci.yml           # GitHub Actions (간소화, 2025-12-29)
│
└── requirements.txt         # Python 의존성
```

---

### 3.2 핵심 파일 상세

#### Backend 핵심 파일

**AI Agents (MVP)**:
1. `backend/ai/mvp/trader_agent_mvp.py` (35% weight)
   - 공격적 트레이딩 기회 포착
   - 단기 모멘텀 분석
   - Absorbed: Trader Agent, ChipWar Agent (opportunity)

2. `backend/ai/mvp/risk_agent_mvp.py` (35% weight)
   - 방어적 리스크 관리
   - **Position Sizing** (NEW, MVP 핵심 기능)
   - Stop Loss 설정
   - Absorbed: Risk Agent, Sentiment Agent, DividendRisk Agent

3. `backend/ai/mvp/analyst_agent_mvp.py` (30% weight)
   - 종합 정보 분석
   - 뉴스, 매크로, 기관 투자자, 칩워 지정학
   - Absorbed: News, Macro, Institutional, ChipWar (geopolitics)

4. `backend/ai/mvp/pm_agent_mvp.py`
   - 최종 의사결정
   - Hard Rules 검증
   - Silence Policy (판단 거부 권한)

5. `backend/ai/mvp/war_room_mvp.py`
   - Orchestrator (3+1 Agent 조율)
   - Weighted Voting 집계
   - Consensus Confidence 계산

**Execution Layer**:
1. `backend/execution/execution_router.py`
   - Fast Track vs Deep Dive 라우팅
   - Fast Track 조건: Stop Loss hit, 일일 손실 > -5%, VIX > 40

2. `backend/execution/order_validator.py`
   - 8개 Hard Rules 검증
   - Code-enforced (AI 해석 불가)

3. `backend/execution/shadow_trading_mvp.py`
   - Shadow Trading Engine
   - 조건부 실행 (3개월 검증)

**API Routers (53개)**:
- `war_room_mvp_router.py` - War Room MVP API (8 endpoints)
- `war_room_analytics_router.py` - Analytics API (8 endpoints)
- `data_backfill_router.py` - 데이터 백필 (675줄)
- (기타 50+ routers)

**Database**:
1. `backend/database/models.py`
   - 17개 테이블 정의
   - SQLAlchemy ORM

2. `backend/database/repository.py` (1,512줄)
   - Data Access Layer
   - 2026-01-02: N+1 쿼리 제거, TTL 캐싱 추가

**Automation**:
1. `backend/automation/macro_context_updater.py` (373줄)
   - 매일 09:00 KST 자동 실행
   - Claude API로 서사 생성
   - DB 저장

**Scripts**:
1. `backend/scripts/shadow_trading_monitor.py`
   - 2026-01-04 개선
   - 포지션 세부 정보, Stop Loss 체크

2. `backend/scripts/collect_14day_data.py`
   - 14일 데이터 수집 (2025-12-28 시작)

---

#### Frontend 핵심 파일

**Pages (40+ 페이지)**:
- `NewsAggregation.tsx` (421줄, 2026-01-02 수정)
- `DataBackfill.tsx` (917줄)
- `BacktestDashboard.tsx` (896줄)
- `RssFeedManagement.tsx` (847줄)

**Components**:
- `war-room/WarRoomCard.tsx` (171줄)
- `war-room/WarRoomList.tsx`

---

## 4. 핵심 시스템 아키텍처

### 4.1 War Room MVP 시스템

```
┌─────────────────────────────────────────────────────────────────┐
│                  1. Data Collection (Real-time)                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │  Yahoo   │  │   FRED   │  │  FinViz  │  │  Social  │       │
│  │ Finance  │  │  (Macro) │  │  (News)  │  │(Sentiment)│       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
│  주가, RSI     금리, 유가    뉴스 감성    Twitter/Reddit      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│         2. War Room MVP (3+1 Agents, Weighted Voting)           │
│  ┌────────────────┐ ┌────────────────┐ ┌────────────────┐     │
│  │  Trader MVP    │ │   Risk MVP     │ │ Analyst MVP    │     │
│  │    35%         │ │     35%        │ │     30%        │     │
│  │   (Attack)     │ │   (Defense)    │ │ (Information)  │     │
│  └────────────────┘ └────────────────┘ └────────────────┘     │
│                              ↓                                  │
│                     ┌────────────────┐                          │
│                     │   PM Agent     │                          │
│                     │ (Final Decision)│                         │
│                     └────────────────┘                          │
│                                                                 │
│  각 Agent → Action (7개) + Confidence (0.0~1.0)                │
│  PM Agent → approve/reject/reduce_size/silence                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              3. Execution Router (NEW, 2025-12-31)              │
│  ┌────────────────────┐         ┌────────────────────┐         │
│  │   Fast Track       │         │   Deep Dive        │         │
│  │   (< 1 second)     │         │   (~10 seconds)    │         │
│  │                    │         │                    │         │
│  │ • Stop Loss hit    │         │ • New position     │         │
│  │ • Daily loss > -5% │         │ • Rebalancing      │         │
│  │ • VIX > 40         │         │ • Large position   │         │
│  └────────────────────┘         └────────────────────┘         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    4. Order Validator                           │
│                                                                 │
│  8 Hard Rules (Code-Enforced):                                 │
│  1. Position size > 30% → REJECT                               │
│  2. Portfolio risk > 5% → REJECT                               │
│  3. No Stop Loss → REJECT                                      │
│  4. Insufficient cash → REJECT                                 │
│  5. Blacklist symbol → REJECT                                  │
│  6. Market closed (buy) → REJECT                               │
│  7. Duplicate order (5min) → REJECT                            │
│  8. Position count > 20 → REJECT                               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              5. Shadow Trading Engine (Conditional)             │
│                                                                 │
│  • 3개월 검증 기간 (2025-12-31 ~ 2026-03-31)                  │
│  • Initial Capital: $100,000 (virtual)                         │
│  • Current Status (2026-01-04):                                │
│    - 2 Positions: NKE (+$64.75), AAPL (+$1,210.10)            │
│    - Total P&L: +$1,274.85 (+1.27%)                           │
│                                                                 │
│  Success Criteria:                                             │
│  - Risk-Adjusted Alpha > 1.0                                   │
│  - Win Rate > 55%                                              │
│  - Sharpe Ratio > 1.0                                          │
│  - Max Drawdown < -15%                                         │
└─────────────────────────────────────────────────────────────────┘
```

---

### 4.2 Position Sizing System (NEW, MVP)

Risk Agent MVP의 핵심 기능

**Formula**:
```python
# Step 1: Base Size (Risk-based)
account_risk = portfolio_value × 0.02  # 2% risk per trade
stop_loss_distance = (entry_price - stop_loss_price) / entry_price
base_size = account_risk / stop_loss_distance

# Step 2: Confidence Adjustment
confidence_adjusted = base_size × agent_confidence  # 0.0 ~ 1.0

# Step 3: Risk Multiplier
volatility = calculate_volatility(symbol)
if volatility > 0.30:
    risk_multiplier = 0.5   # High volatility → reduce
elif volatility > 0.20:
    risk_multiplier = 0.75  # Medium
else:
    risk_multiplier = 1.0   # Normal

risk_adjusted = confidence_adjusted × risk_multiplier

# Step 4: Hard Cap
HARD_CAP = portfolio_value × 0.10  # 10% max position
final_size = min(risk_adjusted, HARD_CAP)
```

**예시**:
- Portfolio Value: $100,000
- Account Risk: $2,000 (2%)
- Stop Loss Distance: 10%
- Base Size: $20,000
- Confidence: 0.8
- Confidence Adjusted: $16,000
- Volatility: 25% (Medium)
- Risk Multiplier: 0.75
- Risk Adjusted: $12,000
- Hard Cap: $10,000
- **Final Size: $10,000**

---

## 5. 현재 상태 (2026-01-04)

### 5.1 시스템 상태

**Production Ready**: ✅

**활성 시스템**:
- ✅ War Room MVP (3+1 Agents)
- ✅ Shadow Trading (Day 4)
- ✅ Execution Router (Fast Track vs Deep Dive)
- ✅ Order Validator (8 Hard Rules)
- ✅ Position Sizing (Risk-based formula)
- ✅ Macro Context Updater (매일 09:00 KST)

**테스트 완료**:
- ✅ War Room Agent 통합 테스트: 100% (3/3 agents)
- ✅ KIS Broker 인증: 성공
- ✅ Shadow Trading 모니터링: 정상
- ✅ Macro Context Updater: 정상

---

### 5.2 Shadow Trading 현황 (2026-01-04)

**시작일**: 2025-12-31
**현재 Day**: 4
**목표 기간**: 3개월 (90일)

**Capital Overview**:
- Initial: $100,000.00
- Current: $100,000.00
- Available: $80,675.23
- Invested: $19,324.77 (19.3%)

**포지션**:
| Symbol | Qty | Entry Price | Current Price | P&L | Status |
|--------|-----|-------------|---------------|-----|--------|
| NKE | 259 | $63.03 | $63.28 | **+$64.75** | ✅ Safe |
| AAPL | 10 | $150.00 | $271.01 | **+$1,210.10** | ✅ Safe |
| **Total** | - | - | - | **+$1,274.85 (+1.27%)** | - |

**Week 1 성과** (2025-12-31 ~ 2026-01-06):
- 진행 중 (Day 4/7)
- 누적 P&L: +$1,274.85
- Win Rate: 100% (1 trade closed, LULU +$13.85)

---

### 5.3 진행 중인 작업

**P0 (즉시 착수)**:
- ✅ Task 1: Shadow Trading 모니터링 (2026-01-04 완료)
- ✅ Task 2: Macro Context Updater 검증 (2026-01-04 완료)
- 🔄 Task 3: News Agent Enhancement (1/6~1/17, 12일)

**14일 데이터 수집** (백그라운드):
- 시작: 2025-12-29 09:24
- 완료 예정: 2026-01-12
- 진행률: ~20% (Day 6/14)
- 티커: AAPL, NVDA, MSFT

---

### 5.4 다음 단계

**단기 (1주일)**:
1. News Agent Enhancement 시작 (Phase 3.1)
2. Shadow Trading Week 1 보고서 작성 (2026-01-08)
3. 일일 모니터링 지속

**중기 (1개월)**:
1. Daily PDF Report 생성 시스템 구현
2. Claude Code Templates P1-P5 구현
3. Shadow Trading Month 1 보고서

**장기 (3개월)**:
1. Shadow Trading Phase 1 완료 (2026-03-31)
2. Production 전환 여부 결정
3. 자기학습 시스템 고도화

---

## 6. 주요 기능 목록

### 6.1 Core Features

1. **War Room MVP**
   - 3+1 Agent 시스템
   - Weighted Voting (35%, 35%, 30%)
   - Final Decision by PM Agent
   - 7 Actions: BUY, SELL, HOLD, MAINTAIN, REDUCE, INCREASE, DCA

2. **Position Sizing**
   - Risk-based formula
   - Confidence adjustment
   - Volatility adjustment
   - Hard cap enforcement (10%)

3. **Execution Router**
   - Fast Track (< 1s)
   - Deep Dive (~10s)
   - 자동 라우팅

4. **Order Validator**
   - 8 Hard Rules
   - Code-enforced (AI 불가)

5. **Shadow Trading**
   - Conditional execution
   - 3개월 검증 기간
   - Success/Failure criteria

---

### 6.2 Data & Analytics

1. **Data Collection**
   - Yahoo Finance (주가, RSI, 볼륨)
   - FRED (금리, 유가, GDP)
   - FinViz (뉴스 감성)
   - Social Sentiment (Twitter, Reddit)

2. **Macro Context**
   - Market Regime (RISK_ON/OFF/TRANSITION)
   - Fed Stance (HAWKISH/DOVISH/NEUTRAL)
   - VIX Categorization
   - S&P 500 Trend
   - Geopolitical Risk
   - Sector Rotation

3. **Performance Analytics**
   - Agent별 성과 추적
   - 가중치 자동 조정 (30일 기반)
   - Sharpe Ratio, Sortino Ratio
   - Max Drawdown, Win Rate

4. **Deep Reasoning**
   - Extended Thinking (Claude)
   - DB 저장 및 이력 관리
   - REST API 제공

---

### 6.3 Automation

1. **자기학습 시스템**
   - 매일 00:00 UTC 실행
   - 6개 Agent 독립 학습
   - Hallucination Prevention (3-gate)
   - 가중치 자동 조정

2. **스케줄링**
   - Macro Context 업데이트 (매일 09:00 KST)
   - Shadow Trading 모니터링 (매일 09:00, 16:00 KST)
   - 14일 데이터 수집 (1시간 간격)

3. **알림**
   - Telegram 통합
   - Stop Loss 경고
   - 일일 성과 요약

---

### 6.4 Frontend Features

1. **대시보드**
   - War Room 심의 이력
   - Shadow Trading 포지션
   - 성과 차트
   - Agent 가중치 현황

2. **뉴스 페이지**
   - 실시간 뉴스 수집
   - 감성 분석
   - 티커별 필터링

3. **데이터 백필**
   - Yahoo Finance API 통합
   - 간격별 제한사항 검증 (1m: 7일, 1h: 730일)
   - 진행 상태 추적

4. **백테스팅**
   - 과거 데이터 기반 시뮬레이션
   - Multi-capital 테스트
   - 성과 분석

---

## 7. 데이터베이스 스키마

### 7.1 주요 테이블 (17개)

#### Core Tables

1. **stock_prices** (TimescaleDB)
   - 주가 데이터 (OHLCV)
   - time, ticker, open, high, low, close, volume

2. **news_articles**
   - 뉴스 기사
   - title, content, published_date, source, sentiment_score
   - embedding (1536 차원, OpenAI)
   - tickers (ARRAY)

3. **trading_signals**
   - 트레이딩 신호
   - ticker, action, confidence, reasoning
   - signal_type, source_agent

4. **signal_performance**
   - 신호 성과 추적
   - signal_id, outcome (WIN/LOSS), profit_loss
   - exit_price, exit_date

---

#### Shadow Trading Tables (2026-01-03 추가)

5. **shadow_trading_sessions**
   - Shadow Trading 세션
   - initial_capital, current_capital, total_pnl
   - sharpe_ratio, max_drawdown, win_rate
   - status (ACTIVE/PAUSED/COMPLETED)

6. **shadow_trading_positions**
   - Shadow Trading 포지션
   - symbol, quantity, entry_price, current_price
   - stop_loss, take_profit, entry_date
   - status (OPEN/CLOSED), pnl

---

#### War Room Tables

7. **war_room_decisions**
   - War Room 심의 결정
   - symbol, final_decision, confidence
   - agent_opinions (JSONB), pm_decision (JSONB)

8. **agent_weights_history** (2026-01-03 추가)
   - Agent 가중치 이력
   - agent_name, weight, updated_at
   - performance_30d

---

#### Macro & Context

9. **macro_context_snapshots**
   - 거시경제 스냅샷
   - date, regime, fed_stance, vix_level
   - market_sentiment, sp500_trend
   - dominant_narrative (Claude 생성)

10. **news_interpretations**
    - 뉴스 해석 (AI 생성)
    - news_id, interpretation, impact_level
    - created_at

---

#### Data Collection

11. **data_collection_progress** (2026-01-02 추가)
    - 데이터 수집 진행 상태
    - task_name, source, collection_type
    - status, progress_pct, items_processed

12. **news_sources** (2026-01-02 추가)
    - 뉴스 소스 관리
    - name, url, source_type, is_active
    - last_crawled, crawl_interval_minutes

---

#### Analytics

13. **deep_reasoning_analyses**
    - Deep Reasoning 분석 이력
    - theme, beneficiaries, reasoning_trace
    - importance_score, created_at

14. **daily_analytics**
    - 일일 성과 분석
    - date, portfolio_value_eod, daily_pnl
    - win_rate, sharpe_ratio, max_drawdown_pct
    - volatility_30d

---

### 7.2 DB 최적화 (2026-01-02)

**복합 인덱스**:
```sql
-- news_articles
CREATE INDEX idx_news_ticker_date ON news_articles(tickers, published_date);
CREATE INDEX idx_news_processed ON news_articles(published_date)
  WHERE processed_at IS NOT NULL;

-- trading_signals
CREATE INDEX idx_signal_ticker_date ON trading_signals(ticker, created_at);
CREATE INDEX idx_signal_pending_alert ON trading_signals(ticker)
  WHERE alert_sent = FALSE;

-- stock_prices
CREATE INDEX idx_stock_ticker_time_desc ON stock_prices(ticker, time DESC);

-- shadow_trading_sessions
CREATE INDEX idx_session_status_updated ON shadow_trading_sessions(status, updated_at DESC);
```

**N+1 쿼리 제거**:
```python
# Before: N+1 query
signals = session.query(TradingSignal).join(SignalPerformance).filter(...).all()

# After: Eager loading
from sqlalchemy.orm import selectinload
signals = session.query(TradingSignal).options(
    selectinload(TradingSignal.performance)
).filter(...).all()
```

**TTL 캐싱**:
```python
@cache_with_ttl(300)  # 5분 캐시
def get_recent_articles(self, hours=24, limit=50):
    ...
```

---

## 8. API 엔드포인트 전체

### 8.1 War Room MVP API

**Base URL**: `http://localhost:8001/api/war-room-mvp`

| Method | Endpoint | Description | Response |
|--------|----------|-------------|----------|
| POST | `/deliberate` | War Room 심의 실행 | Decision result |
| GET | `/info` | War Room 정보 조회 | System info, agents |
| GET | `/history` | 결정 이력 조회 | List of decisions |
| GET | `/performance` | 성과 측정 | Performance metrics |
| POST | `/shadow/start` | Shadow Trading 시작 | Session ID |
| POST | `/shadow/execute` | Shadow Trade 실행 | Trade result |
| GET | `/shadow/status` | Shadow Trading 상태 | Portfolio status, positions |
| POST | `/shadow/update` | 포지션 업데이트 | Update result |

---

### 8.2 War Room Analytics API

**Base URL**: `http://localhost:8001/api/war-room-analytics`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/offensive-performance` | 공격적 트레이딩 성과 |
| GET | `/defensive-report` | 방어적 트래킹 리포트 |
| GET | `/vote-distribution` | Agent별 투표 분포 |
| GET | `/agent-agreement` | Agent 간 합의도 분석 |
| GET | `/decision-patterns` | 의사결정 패턴 분석 |
| GET | `/confidence-distribution` | Confidence 분포 통계 |
| GET | `/combined-performance` | 통합 성과 리포트 |
| GET | `/full-analytics` | 전체 분석 데이터 |

---

### 8.3 Data Backfill API

**Base URL**: `http://localhost:8001/api/backfill`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/prices` | 주가 백필 시작 |
| POST | `/news` | 뉴스 백필 시작 |
| GET | `/jobs` | 백필 작업 목록 |
| GET | `/jobs/{job_id}` | 작업 상세 조회 |

**Yahoo Finance 제한사항** (2026-01-02 검증 추가):
- 1분 봉: 최근 7일
- 1시간 봉: 최근 730일 (2년)
- 1일 봉: 무제한

---

### 8.4 기타 주요 API (50+ 엔드포인트)

**카테고리별**:
- **Backtest**: `/api/backtest/*` (10+ endpoints)
- **AI Signals**: `/api/ai-signals/*` (5+ endpoints)
- **News**: `/api/feeds/*`, `/api/news/*` (15+ endpoints)
- **Macro**: `/api/macro/*` (8+ endpoints)
- **Correlation**: `/api/correlation/*` (6+ endpoints)
- **Dividend**: `/api/dividend/*` (4+ endpoints)
- **Emergency**: `/api/emergency/*` (3+ endpoints)

**총 API 엔드포인트**: **100+ endpoints**

---

## 9. 문서 구조

### 9.1 문서 통계 (2026-01-04 기준)

**총 문서 수**: 388개 Markdown 파일

**날짜별 분포**:
```
2024-12-20: 6 files    (초기 개발)
2025-12-10: 105 files  (Phase 0-15 집중)
2025-12-14: 16 files   (Phase A-D 완료)
2025-12-15: 18 files   (시스템 재설계)
2025-12-16: 2 files    (War Room 시작)
2025-12-21: 8 files
2025-12-22: 8 files    (War Room 테스트)
2025-12-23: 21 files   (Phase 24-25)
2025-12-27: 12 files   (인프라 정리)
2025-12-28: 10 files   (War Room 완성)
2025-12-29: 11 files   (실거래 준비)
2025-12-30: 5 files    (Phase 29-32)
2025-12-31: 1 file     (MVP 전환)
2026-01-01: 4 files    (Claude 신기능)
2026-01-02: 11 files   (Skills Migration, DB 최적화)
2026-01-03: 4 files    (Claude Templates)
2026-01-04: 2 files    (즉시 착수)
```

---

### 9.2 문서 카테고리

#### 폴더별 구조

```
docs/
├── 00_Spec_Kit/              (15 files)
│   ├── 251210_00_Project_Overview.md
│   ├── 251210_01_System_Architecture.md
│   ├── 251214_Integrated_Development_Plan.md
│   └── 251228_War_Room_Complete.md
│
├── 01_Quick_Start/           (6 files)
│   ├── 251210_QUICKSTART.md
│   ├── 251210_SERVER_START_GUIDE.md
│   └── 251210_Setup_Wizard_Guide.md
│
├── 02_Phase_Reports/         (90+ files)
│   ├── 251210_PHASE_0_COMPLETION_REPORT.md
│   ├── 251210_PHASE_A_COMPLETION_REPORT.md ~ C
│   ├── 251214_Phase_ABCD_Complete.md
│   ├── 251215_Phase_E_Complete.md
│   └── ... (Phase 18-32)
│
├── 02_Development_Plans/     (12 files)
│   ├── 251229_Phase1_Completion_Report.md
│   ├── 251229_Phase2_Completion_Report.md
│   ├── 251229_Phase3_Completion_Report.md
│   ├── 251229_Phase4_Completion_Report.md
│   └── 251229_Final_Integrated_Development_Plan.md
│
├── 03_Integration_Guides/    (10 files)
│   ├── 251214_AI_Skills_Integration.md
│   └── Phase_ABCD_Integration_Guide.md
│
├── 04_Feature_Guides/        (5 files)
│   ├── War_Room_Guide.md
│   └── 251227_AI_Model_Management.md
│
├── 05_Deployment/            (9 files)
│   ├── 251214_CICD_Guide.md
│   ├── 251214_Security_Best_Practices.md
│   ├── 251214_Performance_Tuning.md
│   └── 251227_NAS_Deployment_Checklist.md
│
├── 06_Infrastructure/        (7 files, 2025-12-27 생성)
│   ├── Database_Standards.md
│   ├── Schema_Compliance_Report.md
│   ├── Storage_Optimization.md
│   ├── Infrastructure_Management.md
│   ├── NAS_Deployment_Guide.md
│   └── Completion_Report_20251227.md
│
├── 09_User_Manuals/          (2 files)
│   └── 251217_User_Manual_v2.md
│
├── 10_Progress_Reports/      (30+ files)
│   ├── 251222_Phase20_Complete.md
│   ├── 251223_Phase24_Complete.md
│   ├── 251223_Phase25_Complete.md
│   └── 260104_News_Agent_and_Structured_Outputs.md
│
└── 11_Archive/               (Legacy)
    └── CACHE_CLEARED.md
```

---

#### 최상위 주요 문서

**현재 상태**:
- `PROJECT_OVERVIEW.md` (2025-12-28, 200줄)
- `SYSTEM_ARCHITECTURE.md` (2025-12-31)
- `ARCHITECTURE.md` (2025-12-15)

**실행 가이드**:
- `QUICK_START.md` (2025-12-15)
- `DATABASE_SETUP.md` (2025-12-15)
- `DEPLOYMENT.md` (2025-12-15)

**작업 로그** (Work_Log):
- `Work_Log_20251229.md` (468줄)
- `Work_Log_20260102.md` (468줄)
- `Work_Log_20260103.md` (473줄)
- `Work_Log_20260104.md` (351줄)

**MVP 관련**:
- `MVP_IMPLEMENTATION_PLAN.md` (2025-12-31)
- `251231_MVP_Implementation_Complete.md` (200줄)
- `MVP_Integration_Verification.md`
- `MVP_Frontend_Integration_Complete.md`

**War Room**:
- `251216_System_Integration_and_War_Room.md`
- `251228_War_Room_System_Complete.md`
- `260102_War_Room_MVP_Skills_Migration_Plan.md` (1,096줄)
- `260102_War_Room_MVP_Skills_Final_Report.md`

**Shadow Trading**:
- `Shadow_Trading_Phase1_Started.md` (2025-12-31)
- `Shadow_Trading_Week1_Report.md` (2026-01-02)

**Claude 신기능**:
- `260101_Claude_Features_Analysis.md`
- `260101_Claude_Features_Implementation_Plan.md`
- `260102_Claude_Code_Templates_Review.md` (894줄)

**구현 계획**:
- `260103_Claude_Code_Templates_Implementation_Plan.md` (1,183줄)
- `260103_Remaining_Components_Implementation_Plan.md` (1,891줄)
- `260103_Daily_Report_Generation_Pipeline` (1,231줄)

**Daily Summary**:
- `260102_Daily_Summary.md`
- `251225_work_summary.md`
- `251227_Daily_Development_Summary.md`

---

### 9.3 문서 작성 규칙

**파일명 규칙**:
```
YYMMDD_Topic_Description.md
```

**예시**:
- `260102_War_Room_MVP_Skills_Migration_Plan.md`
- `251231_MVP_Implementation_Complete.md`
- `Work_Log_20260104.md`

**문서 구조**:
```markdown
# 제목

**작성일**: YYYY-MM-DD
**우선순위**: P0/P1/P2
**상태**: 진행 중/완료/보류

---

## Executive Summary
(3-5 문장 요약)

## 주요 내용
...

## 생성/수정된 파일
...

## 다음 단계
...
```

---

## 10. 마치며

### 10.1 프로젝트 현황 요약

**개발 기간**: 2024-12-20 ~ 현재 (45일)
**총 문서**: 388개 Markdown
**총 코드**: Backend 100+ 파일, Frontend 40+ 페이지
**총 API**: 100+ 엔드포인트
**DB 테이블**: 17개

**핵심 마일스톤**:
- 2025-12-10: Phase 0-15 완료 (기본 인프라)
- 2025-12-15: 시스템 재설계 (8 Agents)
- 2025-12-23: Phase 24-25 (Agent 가중치 자동조정)
- 2025-12-28: War Room 완성
- 2025-12-31: **MVP 전환** (8 → 3+1 Agents)
- 2026-01-02: Skills Migration, DB 최적화
- 2026-01-04: 즉시 착수 작업 진행 중

**현재 상태**: Production Ready, Shadow Trading Day 4

---

### 10.2 시스템 성과

**MVP 전환 효과**:
- 비용: 67% 절감
- 속도: 67% 향상
- API 호출: 8회 → 3회
- 응답 시간: 30초 → 10초

**Shadow Trading**:
- Day 4, Total P&L: **+$1,274.85 (+1.27%)**
- Win Rate: 100% (1 trade)
- 2 Active Positions: NKE, AAPL

**테스트 완료**:
- War Room Agent 통합: 100%
- KIS Broker 인증: 성공
- Macro Context Updater: 정상

---

### 10.3 다음 단계 (2026-01-05 ~)

**P0 (즉시 착수, 계속)**:
- News Agent Enhancement (Phase 3.1)
- Shadow Trading 일일 모니터링
- 14일 데이터 수집 모니터링

**P1 (단기, 1주일)**:
- Shadow Trading Week 1 보고서 작성
- Daily PDF Report 시스템 구현 시작

**P2 (중기, 1개월)**:
- Claude Code Templates P1-P5 구현
- Shadow Trading Month 1 보고서

**P3 (장기, 3개월)**:
- Shadow Trading Phase 1 완료 평가
- Production 전환 여부 결정

---

**작성 완료**: 2026-01-04
**다음 업데이트**: 2026-01-08 (Shadow Trading Week 1 보고서 작성 시)
**작성자**: AI Trading System Development Team

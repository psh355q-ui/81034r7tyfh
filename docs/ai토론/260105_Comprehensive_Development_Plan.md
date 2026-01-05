# 260105 종합 개발 계획 (Total Consolidation)
**작성일**: 2026-01-05
**목적**: `docs/ai토론` 내의 모든 260105_계열 문서(아이디어, 비평, 검토, 통합안)를 하나로 집대성한 최종 실행 가이드.

---

## 🚀 1. Executive Summary: "The Companion AI"
우리는 기존의 "스마트 트레이더(Smart Trader)"를 넘어, 사용자의 성향과 책임을 공유하는 **"평생 투자 파트너(Lifetime Companion)"**로 시스템을 진화시킵니다.

### 3대 핵심 기둥 (Based on ChatGPT / Gemini / Claude)
1.  **Investment Journey Memory (ChatGPT)**: 사용자의 성공/실패 패턴을 기억하고 코칭.
2.  **Safety & Responsibility (Gemini)**: 계좌 분리(Partitioning)와 위험 제한(Hard Rules).
3.  **Efficiency & Architecture (Claude)**: 비용 효율적인 Persona Router 및 한국형 세금 최적화.

---

## 🏗️ 2. 통합 아키텍처: "Persona Router System"

단일 War Room MVP 엔진을 사용하되, **Persona Router**가 사용자의 '가면(Mode)'을 바꿔주어 마치 4개의 다른 AI처럼 동작하게 합니다.

### 2.1 Persona Modes
| 모드 | 대상 사용자 | 가중치 전략 (Trader / Risk / Analyst) | 핵심 기능 |
| :--- | :--- | :--- | :--- |
| **Dividend Mode** | 배당/안정 추구 | 10% / 40% / 50% | Yield Trap 방지, 배당 캘린더, Total Return 예측 |
| **Long-Term Mode** | 가치/성장 추구 | 15% / 25% / 60% | Thesis Violation 감지, 노이즈 필터링 |
| **Trading Mode** | 단기/모멘텀 | 35% / 35% / 30% | 실시간 뉴스 반응, 빠른 차익 실현 (기존) |
| **Aggressive Mode** | 레버리지/헤지 | 50% / 30% / 20% | FOMO 제어, Leverage Guardian (10% 캡) |

### 2.2 System Flow
```mermaid
graph TD
    User --> Router[Persona Router]
    Router --> Mode[Select Mode & DB Partition]
    Mode --> Weights[Set Dynamic Weights]
    Weights --> WarRoom[War Room MVP Engine]
    WarRoom --> Safety[Safety Layer (Tax/Kick-out)]
    Safety --> Action[Final Execution]
```

---

## 🧠 3. 심층 추론 (Deep Reasoning) 로직

### 3.1 RSS to Event Vector (정량화)
비정형 뉴스를 구조화된 JSON 벡터로 변환하여 '느낌'이 아닌 '데이터'로 처리합니다.
- **구조**: `{ "event_type": "War", "severity": 4, "confidence": 0.8, "momentum": "Escalating" }`
- **핵심**: "단순 발언(Rhetoric)" vs "실제 행동(Action)" 구분.

### 3.2 GRS (Geopolitical Risk Score) 모델
$$ GRS = Severity \times Confidence \times Exposure \times Duration $$
- **Price Confirmation**: 뉴스만 보지 않고 실제 가격(ETF 등)이 반응할 때만 확신도 가산.

### 3.3 Failure Playbook (청산 전략)
진입보다 청산이 중요합니다.
- **Profit Taking**: GRS가 고점 대비 30% 하락 시 자동 익절.
- **Stop Loss**: "협상(Negotiation)" 키워드 감지 시 즉시 청산.
- **Scenario D(Stagnation)**: 뉴스는 많으나 심각도 변화가 없으면(Flat) 변동성 축소 대응.

---

## 🛡️ 4. 안전 장치 (Safety Layer)

### 4.1 Leverage Guardian
- **논리**: 레버리지(3x)는 장기 보유 시 반드시 손해(Volatility Drag).
- **규칙**: 전체 자산의 **10%** 이내(Satellite Wallet)에서만 허용. 초과 시 거부.

### 4.2 Explicit Responsibility
- **UX**: 위험 거래 시 "이 손실의 가능성을 인지했습니다" 체크박스 강제.

---

## 📅 5. 단계별 구현 로드맵 (Roadmap)

### Phase 1: Foundation (1주)
- [ ] **Persona Router 구현**: `backend/ai/router/persona_router.py`
- [ ] **Dynamic Weight System**: 모드별 가중치 설정 로직 `backend/ai/mvp/war_room_mvp.py`
- [ ] **DB Update**: `users` 테이블에 `persona_mode`, `wallet_partitions` 추가.

### Phase 2: Safety First (1주)
- [ ] **Leverage Guardian**: Risk Agent에 Hard Rule 추가.
- [ ] **Disclaimer Middleware**: 모든 API 응답에 법적 면책 조항 자동 첨부.

### Phase 3: Deep Intelligence (2주)
- [ ] **DeepReasoningAgent Upgrade**: Event Vector & GRS 로직 탑재.
- [ ] **Thesis Violation Detector**: Analyst Agent에 펀더멘털 손상 감지 프롬프트 추가.

### Phase 4: Expansion (지속)
- [ ] **한국형 기능**: 세금 최적화(250만원 공제), 환율 리스크 관리.
- [ ] **Dashboard**: 모드별 UI/UX 차별화 (색상, 정보 밀도).

---

## 📚 6. 참조 원천 (Source Ideas)
이 계획은 다음 문서들의 핵심을 통합했습니다.
- `260104_Chatgptideas2`: 투자 여정 기억, 행동 코칭.
- `260104_geminiideas2`: 계좌 파티셔닝, 배당 함정 필터.
- `260105_Claudecodeideas3`: 페르소나 라우터 구현 상세, 한국 시장 특화.
- `260105_Grand_Unified_Strategy_Synthesis`: 통합 아키텍처 설계도.
- `260105_Implementation_Deep_Dive`: 기술적 검증 질문.

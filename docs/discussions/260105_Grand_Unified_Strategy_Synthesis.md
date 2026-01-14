# 종합 AI 전략 통합 마스터 플랜 v2.0
**작성일**: 2026-01-05
**기반 문서**: ChatGPT(철학), Gemini(안전/논리), Claude(구현/한국형) 아이디어 2.0 버전 종합

## 1. Executive Summary: "The Companion AI"
기존 시스템이 "똑똑한 트레이더(Smart Trader)"였다면, 새로운 시스템은 **"평생의 투자 파트너(Lifetime Investment Partner)"**를 지향합니다.
단순히 종목을 추천하는 것을 넘어, 사용자의 **투자 여정(Journey)**을 기억하고, **페르소나(Persona)**에 맞춰 행동하며, **안전(Safety)**을 책임지는 구조로 진화합니다.

### 핵심 철학 3대장
1.  **Investment Journey Memory**: 실패와 성공의 역사를 기억하여 사용자를 코칭. (ChatGPT)
2.  **Account Partitioning**: 하나의 계정 내에서 '안전'과 '재미'를 분리. (Gemini)
3.  **Persona Router**: 단일 AI 엔진으로 다양한 투자 성향 대응. (Claude)

---

## 2. 통합 아키텍처: "Persona Router & Safety Layer"
기존 3+1 MVP Agent 구조를 유지하면서, 입/출력 단에 지능형 제어 레이어를 추가하여 무거워지지 않게 설계했습니다.

```mermaid
graph TD
    User[User Input] --> Router{Persona Router}
    
    subgraph "Phase 4.1: The Brain (Mode Switching)"
    Router -->|Conservative| Mode1[Dividend/LongTerm Mode]
    Router -->|Aggressive| Mode2[Trading/Leverage Mode]
    end
    
    subgraph "Dynamic Weights System"
    Mode1 -->|Analyst++ / Trader--| WarRoom[War Room MVP (3+1 Agents)]
    Mode2 -->|Trader++ / Risk--| WarRoom
    end
    
    WarRoom --> RawAction[Raw AI Action]
    
    subgraph "Phase 4.2: The Seatbelt (Safety Layer)"
    RawAction --> Safety{Leverage Guardian & Tax Optimizer}
    Safety -->|Reject/Warn| Feedback[Feedback Loop]
    Safety -->|Approve| Exec[Execution]
    end
```

---

## 3. 핵심 기능 상세 (Key Features)

### 3.1 Persona Router (모드 전환 시스템)
사용자를 단일 성향으로 규정하지 않고, **계좌(Wallet)별로 다른 페르소나**를 적용합니다.

| 모드 | Core Focus | 가중치 변화 (Trader/Risk/Analyst) | 주요 기능 |
| :--- | :--- | :--- | :--- |
| **Dividend** | 현금흐름, 안정성 | 10% / 40% / 50% | Yield Trap 감지, 배당 캘린더 |
| **Long-Term** | 펀더멘털, 성장성 | 15% / 25% / 60% | Thesis Violation 감지, 노이즈 필터 |
| **Trading** | 모멘텀, 기술적 | 35% / 35% / 30% (기존) | 뉴스 속보, 단기 수급 |
| **Aggressive** | 변동성, 레버리지 | 50% / 30% / 20% | FOMO Mode, Leverage Guardian |

### 3.2 Safety Layer (안전 장치)
Gemini와 ChatGPT가 강조한 '책임'과 '보호'를 담당하는 미들웨어입니다.

-   **Leverage Guardian**: 
    -   레버리지(3x) 매수 시도 시 **"위성 계좌(Satellite Wallet, 자산의 10%) 한도 내에서만 허용"** 강제.
    -   "감정 쓰레기통(Emotional Trash Can)": 위험한 베팅은 90% 모의투자 + 10% 실전투자로 유도.
-   **Explicit Responsibility (책임 전가)**:
    -   경고를 무시하고 진행 시, **"이 손실의 가능성을 인지했습니다"** 체크박스 강제 (로그 기록).
-   **Tax Optimizer (한국형)**:
    -   해외주식 양도세(250만원 공제) 및 배당소득세(15.4%) 고려하여 매도 수량 최적화 제안.

### 3.3 Investment Journey Memory (투자 여정 기억)
-   **Thesis Violation Detector**: 
    -   가격이 떨어져서 파는 게 아니라, **"점유율 하락", "경영진 매도"** 등 투자 아이디어가 훼손됐을 때만 매도 알림.
-   **Retrospective Coaching**:
    -   "3개월 전 비슷한 장세에서 패닉 셀링으로 -15% 손실을 봤습니다. 이번엔 홀딩해볼까요?"

---

## 4. 구현 로드맵 (Phased Implementation)

현재 MVP 시스템(가볍고 빠름)의 장점을 해치지 않도록 단계적으로 도입합니다.

### Phase 1: 기반 구축 (Foundation) - 1주
-   [ ] **Persona Router**: 사용자 설정에 따라 Agent 가중치(`AGENT_WEIGHTS`)를 동적으로 변경하는 로직 구현.
-   [ ] **Account Partitioning DB**: `users` 테이블에 `persona_type`, `wallet_type` 컬럼 추가.

### Phase 2: 안전망 확보 (Safety First) - 1주
-   [ ] **Leverage Guardian**: `PM Agent`의 Hard Rule에 레버리지 ETF 목록 및 한도 로직 추가.
-   [ ] **Disclaimer System**: API 응답에 면책 조항 자동 첨부 미들웨어 구현.

### Phase 3: 지능형 기능 (Intelligence) - 2주
-   [ ] **Thesis Violation**: `Analyst Agent`에 펀더멘털 악재(재무, M/S 하락) 감지 프롬프트 추가.
-   [ ] **KRW/Tax Patch**: 한국 시장 특화 로직(환율 변동성, 세금)을 `Analyst Agent`에 주입.

---

## 5. 결론
이 통합 계획은 **"기술적 우위(Claude)"**와 **"사용자 보호(Gemini/ChatGPT)"**를 완벽하게 결합합니다.
특히 **Persona Router**를 통해 복잡한 코드 추가 없이 **Agent 가중치 조절만으로** 다양한 투자 성향을 커버하는 것이 핵심 효율화 전략입니다.

**Next Action**: `Persona Router` 설계를 위한 `backend/ai/router/persona_router.py` 프로토타이핑 착수.

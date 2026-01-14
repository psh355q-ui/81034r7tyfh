# TASKS: AI Trading System v2.0 - Autonomous Hedge Fund

## MVP 캡슐
1. **목표**: "예측-관계-집행"이 분리된 전문가 에이전트들의 협업 시스템 구축 (v2.0)
2. **페르소나**: 안정적인 수익을 추구하면서도 논리적인 설명을 요구하는 퀀트 펀드매니저
3. **핵심 기능**: 
    - Execution RL (VWAP 우위 집행)
    - GNN Impact Analysis (뉴스 전파 경로 분석)
    - Multi-Modal Fusion (설명 가능한 통합 의사결정)
4. **제외 기능**: 실시간 초단타(HFT), 복잡한 파생상품, 완전 자율 입출금
5. **성공 지표**: 
    - Execution Slippage < 5bps (vs Arrival VWAP)
    - GNN 2-Hop 전파 설명력 (테마 확산 포착 여부)
    - Fusion Gate 작동 로그 (하락장 차트 신호 차단 등)
6. **기술 스택**: Python, PyTorch(RL), NetworkX(Graph), FastAPI, React
7. **일정**: 4주 (Phase 25.0 ~ 28.0)
8. **위험 요소**: KIS API Rate Limit, RL 학습 데이터(Tick) 부족
9. **의존성**: KIS Open API, OpenAI Embeddings
10. **다음 단계**: v2.5 (매도/리스크 관리 전용 RL)

---

## 마일스톤 개요

| 마일스톤 | 설명 | 주요 기능 | Phase |
|----------|------|-----------|-------|
| M1 | The Hands (실행) | Execution RL, Tick Flow Calculator | Phase 25 |
| M2 | The Eyes (관계) | GNN Dynamic Graph, News Co-occurrence | Phase 26 |
| M3 | The Brain (통합) | Gated Fusion, Multi-modal Intent | Phase 27 |
| M4 | The Face (관제) | Dashboard Update, Shadow Trading Report | Phase 28 |

---

## M1: The Hands - Execution RL (Phase 25)
*Target: "싸게, 티 안 나게 산다"*

### [x] T1.1: TickFlow & VWAP Calculator (Infra)
**담당**: Backend Engineer
**목표**: RL State 생성을 위한 기초 데이터 모듈 구현
- `backend/execution/data/tick_flow.py`: 최근 N초 Tick Flow 계산
- `backend/execution/data/vwap.py`: 주문 기간 Arrival VWAP 실시간 계산
- **TDD**: Mock Tick Data로 10초/30초 Flow 계산 정확도 검증

### [x] T1.2: Execution RL Environment (RL)
**담당**: AI Researcher
**목표**: Gym-compatible Custom Environment 구현
- `backend/execution/rl/env.py`: `ExecutionEnv` 클래스
- State: `[remaining_ratio, time_ratio, tick_flow_10s, tick_flow_30s]`
- Reward: Main(VWAP Delta) + Aux(Step Advantage)
- **TDD**: Random Action 실행 시 Step/Reset 정상 동작 확인

### [x] T1.3: PPO Agent & Training Pipeline (RL)
**담당**: AI Researcher
**목표**: Stable-Baselines3 기반 에이전트 학습 파이프라인
- `backend/execution/rl/agent.py`: PPO 모델 설정
- `backend/execution/rl/train.py`: Mock Data 기반 학습 스크립트
- **Validation**: 학습 곡선(Reward) 우상향 확인

### [x] T1.4: Fail-safe State Machine (System)
**담당**: Backend Engineer
**목표**: RL 오작동 시 Rule-based 전환 안전장치
- `backend/execution/safety/watchdog.py`: 가격/시간/에러 감시
- Trigger 발동 시 `SmartExecutor`(TWAP)로 권한 이양
- **TDD**: Trigger 조건 강제 주입 시 Fallback 전환 테스트

---

## M2: The Eyes - GNN Impact Analysis (Phase 26)
*Target: "뉴스의 나비효과를 본다"*

### [x] T2.1: News Co-occurrence Builder (Data)
**담당**: Data Engineer
**목표**: 뉴스 텍스트에서 동시 언급 종목 추출 및 Edge 생성
- `backend/gnn/builder.py`: 뉴스 파싱 -> `(Ticker A, Ticker B)` 추출
- **TDD**: 샘플 뉴스("Samsung and SK Hynix agreed...")에서 Edge 추출 확인

### [x] T2.2: Propagation Engine (2-Hop) (Algo)
**담당**: Algorithm Engineer
**목표**: 시그널 확산 및 감쇠(Decay) 로직 구현
- `backend/gnn/propagator.py`: BFS 기반 2-Hop 탐색
- Decay Factor 적용 (Hop1: 0.7, Hop2: 0.4)
- **TDD**: A(Source) -> B(Hop1) -> C(Hop2) 점수 전파 계산 검증

### [x] T2.3: Knowledge & Correlation Gate (Filter)
**담당**: Data Scientist
**목표**: 무의미한 연결 필터링
- `backend/gnn/gate.py`: Sector 일치 여부, Price Correlation 확인
- **Output**: Adjusted Edge Weight
- **TDD**: 상관관계 낮은 Edge의 Weight가 0이 되는지 확인

---

## M3: The Brain - Multi-Modal Fusion (Phase 27)
*Target: "맥락을 보고 결정한다"*

### [x] T3.1: Signal Standardizer (Infra)
**담당**: Backend Engineer
**목표**: 이종 데이터(뉴스, 차트, GNN)의 점수 스케일 통일
- `backend/fusion/normalizer.py`: Score (-1.0 ~ 1.0), Confidence (0.0 ~ 1.0)
- Interface: `BaseSignal`

### [x] T3.2: Logic Gates Implementation (Logic)
**담당**: AI Engineer
**목표**: Liquidity, GNN Confidence, Event Priority Gate 구현
- `backend/fusion/gates/liquidity.py`
- `backend/fusion/gates/event_priority.py`
- **TDD**: 거래량 부족 시 차트 신호 Weight=0 검증

### [x] T3.3: Fusion Engine & Intent Generation
**담당**: System Architect
**목표**: 최종 `TradingIntent` 생성
- `backend/fusion/engine.py`: Weighted Sum + Gating 적용
- Output: `TradingIntent` (JSON)
- **TDD**: 뉴스 강세 + 차트 약세 + EventGate ON -> 매수 우위 결과 확인

---

## M4: The Face - Integration & Dashboard (Phase 28)
*Target: "결과를 증명한다"*

### [x] T4.1: Shadow Trading Runner
**담당**: DevOps
**목표**: 운영 모드(Live)와 별개로 검증 모드(Shadow) 실행 환경 구축
- `backend/runners/shadow_runner.py`: 실제 주문 없이 로직만 수행하고 로그 기록
- 기존 `SignalExecutor`와 병렬 실행

### [ ] T4.2: Dashboard Visualization (Fusion & GNN)
**담당**: Frontend Engineer
**목표**: 의사결정 과정(Why) 시각화
- GNN Graph View: 중심 노드와 확산 경로 시각화
- Fusion Scorecard: 각 모달의 기여도 표

---

## Update History
- 2026-01-14: v2.0 Architecture Tasks (Execution RL, GNN, Fusion) 생성

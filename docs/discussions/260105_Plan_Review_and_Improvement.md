# 계획서 검토 및 개선 제안 보고서
**작성일**: 2026-01-05
**참조 문서**: 
- `260104_Venezuela_Crisis_Deep_Reasoning_Master_Plan.md` (마스터 플랜)
- `260105_New_Idea_Integration_Plan.md` (신규 아이디어 통합 계획)
- `Work_Log_20260104.md` (작업 로그)

## 1. 개요 및 정합성 분석
두 계획서는 상호 보완적으로 잘 구성되어 있습니다.
- **마스터 플랜 (260104)**: 전략적 방향(시나리오 A/B/C/D), 섹터별 대응(Long/Short), 데이터 프록시(XLE/USO) 등 **"무엇을(What)"** 할 것인가에 집중.
- **통합 계획 (260105)**: 이벤트 벡터, GRS 공식 등 RSS 데이터를 처리하는 **"어떻게(How)"**에 집중.

그러나 작업 로그 및 마스터 플랜의 세부 사항(`Scenario D`, `Failure Playbook`)이 통합 구현 계획에 일부 누락되어 있어 이를 보완해야 합니다.

## 2. 주요 개선 제안

### 2.1 Failure Playbook (청산 규칙)의 통합
마스터 플랜에 명시된 **"진입만큼 중요한 청산 규칙"**이 통합 계획의 구현 단계에는 구체화되지 않았습니다. GRS(지정학적 리스크 점수)가 하락할 때의 로직을 추가해야 합니다.

- **제안**: `GRS_Calculator`에 **Exit Threshold** 추가.
  - GRS > 6 (진입)
  - GRS < 4로 하락 시: **Profit Taking (50%)** 자동 발동.
  - "Negotiation(협상)" 키워드 벡터 감지 시: **Stop Loss** 즉시 발동.

### 2.2 데이터 프록시(Data Proxy) 구체화
마스터 플랜은 `Mars-WTI Spread`의 대체재로 `XLE/USO` 괴리율을 제안했으나, 통합 계획은 뉴스(RSS) 위주입니다. 정량적 가격 데이터와 뉴스 데이터를 결합해야 합니다.

- **제안**: `DeepReasoningAgent`가 이벤트를 분석할 때, **가격 데이터(Yahoo Finance API)**를 참조하도록 로직 보강.
  - 뉴스에서 "공급 차질" 감지 + `XLE` 상승 & `USO` 횡보 = **확신도(Confidence) 가산 (+0.2)**.

### 2.3 시나리오 D (Stagnation) 대응 추가
마스터 플랜의 'Scenario D(지루한 공방)'는 변동성 축소 구간입니다. 통합 계획의 GRS 모델은 '심각도' 위주라 이를 놓칠 수 있습니다.

- **제안**: 이벤트 벡터에 `change_rate` (변화율) 속성 추가.
  - 뉴스는 많으나(Noise High), 심각도 변화가 없으면(Severity Flat) → **Scenario D** 판정.
  - 대응: 양방향 포지션 축소 또는 옵션 매도 시그널 생성.

## 3. 수정된 실행 계획 (Action Items)

기존 `260105` 계획을 아래와 같이 구체화하여 진행할 것을 제안합니다.

1.  **Event Vector 확장**:
    - `change_momentum`: 사건이 곪아가는지(Stagnation) 터지는지(Escalation) 속성 추가.
2.  **GRS with Price Check**:
    - 공식 수정: $$ GRS_{final} = GRS_{news} \times PriceConfirmationFactor $$
    - 가격 반응(ETF)이 뉴스 방향과 일치할 때 가중치 부여.
3.  **Exit Strategy 코딩**:
    - 진입(Entry) 로직뿐만 아니라 청산(Exit) 로직을 `TraderAgent`가 아닌 `DeepReasoningAgent` 결과에 포함시켜 명확히 지시.

## 4. 결론
`260105` 계획서는 훌륭한 출발점이나, 실전(Real-world)의 복잡성(청산, 속임수 패턴)을 다루기 위해 **마스터 플랜의 Failure Playbook을 코드 레벨로 끌어와야** 합니다. 위 개선안을 반영하여 구현을 시작하는 것이 좋습니다.

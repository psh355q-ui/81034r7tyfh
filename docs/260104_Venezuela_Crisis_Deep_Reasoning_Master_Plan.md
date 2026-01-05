# 260104 베네수엘라 위기 대응 및 Deep Reasoning 통합 마스터 플랜

## 1. 개요 (Executive Summary)
본 문서는 2026년 1월 4일 트럼프 행정부의 베네수엘라 군사 작전 시나리오를 기점으로, AI 트레이딩 시스템에 **"지정학적 심층 추론(Geopolitical Deep Reasoning)"** 능력을 탑재하기 위한 종합 전략 및 개발 계획이다.

기존의 단순 키워드 감지(News Agent)를 넘어, **구조적 위험(Structural Risk)**과 **일시적 노이즈(Noise)**를 구분하고, 원유-금리-환율의 3각 상관관계를 분석하여 정교한 섹터별 매매 신호를 생성하는 것을 목표로 한다.

---

## 2. 정세 분석 및 시나리오 (Situation Analysis)

### 핵심 관점
- **Event Nature**: 전면전(Full Invasion)보다는 **최대 압박(Maximum Pressure)** 및 **제한적 군사 옵션(해상 봉쇄)** 성격.
- **Key Factor**: 단순 유가(WTI) 상승이 아닌, **중질유(Heavy Crude)** 수급 불균형에 따른 미국 내 정제 마진 및 내수 휘발유 가격(Pump Price)의 비대칭적 급등.
- **Game Changer**: 중국의 실질적 대응(국채 매도, 에너지 파이프라인 방어) 여부.

### 시나리오 모델링 (Scenario Modeling)

| 시나리오 | 확률 | 트리거 (Trigger) | 시장 성격 | 대응 전략 |
| :--- | :--- | :--- | :--- | :--- |
| **A: 조기 타결** | 40% | "협상 개시", "제재 유예" | **V-Shape Recovery** | **Buy the Dip**: 과매도 기술주(QQQ), 소비재(XLY) |
| **B: 스태그플레이션** | 40% | "제재 장기화", "수출 봉쇄" | **Stagflationary Grind** | **Inflation Hedge**: 에너지(XLE), 방산(ITA) Long / 항공(JETS) Short |
| **C: 글로벌 확전** | 20% | "군사 충돌", "중국 보복" | **Systemic Shock** | **Risk Off**: 현금(USD), 금(GLD) 확보, 주식 비중 축소 |

---

## 3. 섹터별 대응 전략 (Sector Strategy)

### 📈 Long (매수)
1.  **Energy (XLE, XOM, CVX)**: 중질유 공급 쇼크의 직접 수혜. Mars-WTI Spread 확대 시 비중 확대.
2.  **Defense (ITA, LMT, RTX)**: 지정학적 긴장감 고조에 따른 방위비 증액 기대감.

### 📉 Short (매도/공매도)
1.  **Airlines (JETS, DAL, UAL)**: Jet Fuel 가격 급등으로 인한 영업이익 직격탄. 헷지 비중 낮은 항공사 우선 타격.
2.  **Low-margin Retail (DG, DLTR)**: Pump Price 상승 → 저소득층 가처분 소득 감소 → 매출 타격.
3.  **Transport (IYT)**: 운송비 증가 부담.

### ⚠️ Conditional (조건부 관망)
1.  **Tech (NVDA, QQQ)**: 금리(10Y Yield) 상승 동반 시 밸류에이션 부담으로 비중 축소. 금리 안정 시 저가 매수 기회.

---

## 4. 심층 추론 지표 (Key Indicators)

AI는 단순 텍스트가 아닌 아래 데이터를 기준으로 판단한다.

1.  **Mars-WTI Spread**: $8 이상 확대 시 "구조적 공급망 붕괴" 판단.
2.  **US Pump Price vs Global Oil**: 미국 내수가격 상승률이 더 높으면 "비대칭 인플레이션" 경보.
3.  **CNY 환율**: 위안화 급락 동반 시 "중국 리스크 전이"로 판단하여 Systemic Risk 격상.

---

## 5. 개발 구현 계획 (Development Roadmap)

### Phase 3: 비용 효율적 모니터링 & 전략 확장 (Updated)

#### Goal 1: 하이브리드 폴링 시스템 (The Watchtower)
- **Polling Interval**: 기존 30분 → **5분**으로 단축 (RSS는 무료이므로 속도 우선).
- **Structure**:
    ```python
    RSS_FEEDS = ["Reuters", "CNN", "Fox(Trump Check)"]
    KEYWORDS = ["Venezuela", "Maduro", "Blockade", "Sanction"]
    if keyword_detected and (time_since_last > 5min):
        call_deep_reasoning_agent()
    ```

#### Goal 2: 데이터 프록시 & 지표 고도화 (Data Proxies)
실시간 데이터 확보가 어려운 지표를 위한 대리 변수(Proxy) 설정.
1.  **Mars-WTI Spread Proxy**:
    -   `XLE`(Energy ETF)와 `USO`(WTI ETF)의 괴리율 모니터링.
    -   `VLO`, `MPC` (정유주)의 상대 강도 확인.
2.  **Tech Valuation Check**:
    -   단순 금리가 아닌 **Real Yield (10Y TIPS)** 적용. (실질 금리 상승 시에만 Tech 매도).

#### Goal 3: 청산 및 실패 대응 (Failure Playbook)
진입만큼 중요한 청산 규칙 명문화.
1.  **Profit Taking (이익 실현)**: Mars-WTI 스프레드(또는 Proxy)가 완화되면 에너지주 50% 분할 매도.
2.  **Stop Loss (손절)**: "협상 재개" 뉴스 감지 시 Short 포지션 즉시 청산.
3.  **Scenario D (Stagnation)**: 
    -   **상황**: "관리 선언" 후 실제 변화 없이 지루한 공방 지속.
    -   **대응**: 변동성 축소 구간. 양방향 베팅 축소 및 옵션 매도 관점.

---

## 6. 결론
이 시스템은 단순한 뉴스 알림이가 아니다. 지정학적 이벤트의 **성격(Nature)**을 규명하고, **파급 경로(Transmission Channel)**를 시뮬레이션하여, 남들이 공포에 질려있을 때 **냉철한 "Short/Long" 포트폴리오 재편**을 제안하는 **AI 펀드매니저**로 진화할 것이다.

> **"남은 건 경계 조건과 실패 대응 규칙뿐이다."** - 이 마스터 플랜은 이제 운용 가능한 시스템이다.

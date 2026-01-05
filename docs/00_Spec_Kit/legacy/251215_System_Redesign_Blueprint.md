# AI Trading System - 근본 아키텍처 재설계 (2025-12-15)

**출처**: ChatGPT + Gemini 공동 아이디어 (`chatgpt_ideas_251215_v2.txt`)  
**핵심**: "자동매매 봇" → "판단 책임을 외주화하는 AI 투자 위원회(Institution)"

---

## 🎯 핵심 패러다임 전환

### 기존 시스템 (현재)
- **정체성**: AI 기반 자동매매 봇
- **구조**: 단일 의사결정 흐름
- **사용자 역할**: 시스템 설정자
- **AI 역할**: 분석 및 실행

### 새로운 시스템 (제안)
- **정체성**: AI 투자 위원회 (Investment Committee)
- **구조**: 3권 분립 (입법/사법/행정)
- **사용자 역할**: Commander (최종 승인권자)
- **AI 역할**: Staff (치열한 토론 후 제안)

---

## 🏛️ 1. 3권 분립 아키텍처

### A. 입법부 (bac kend.constitution)
**역할**: 불변의 규칙 정의

**특징**:
- Pure Python (외부 라이브러리 의존성 없음)
- Runtime 해시 검증 (변조 시 시스템 중단)
- AI가 수정 불가 (Read-Only)

**핵심 파일**:
```
backend/constitution/
├── risk_limits.py      # 손절 라인, MDD 제한
├── allocation_rules.py # 자산 배분 원칙
└── constitution.py     # 헌법 통합
```

**예시 규칙**:
```python
class RiskLimits:
    MAX_DAILY_LOSS = 0.05  # -5%
    MAX_DRAWDOWN = 0.10     # -10%
    MAX_POSITION_SIZE = 0.20 # 20%
```

---

### B. 사법부 (backend.intelligence)
**역할**: 데이터 분석, 치열한 토론, 제안서 작성

**Multi-Agent 구성**:

1. **Trader Agent** (공격수)
   - 매수 기회 포착
   - 수급, 차트 분석

2. **Risk Agent** (수비수, Devil's Advocate)
   - 리스크 지적
   - 반대 논리 전개

3. **Analyst Agent** (팩트 체커)
   - ETF Flow 분석
   - SEC 공시 추적
   - Macro 일관성 검증

4. **PM Agent** (중재자, Orchestrator)
   - **중요**: 새로운 논리 창조 금지
   - 하위 Agent 의견 중 선택/거부만 가능
   - Proposal 객체 생성

**핵심**:
```python
class Proposal:
    ticker: str
    action: BUY/SELL/HOLD
    trader_argument: str  # Trader가 작성
    risk_argument: str    # Risk가 작성
    pm_verdict: str       # PM은 선택만 함
    is_approved: bool = False  # Commander 승인 대기
```

---

### C. 행정부 (backend.execution)
**역할**: 승인된 제안의 기계적 실행

**기능**:
- Smart Order Queue (Rate Limit 제어)
- Governance Ledger (위변조 불가 기록)
- Notification Manager

**핵심 제약**:
```python
def execute_order(proposal: Proposal):
    assert proposal.is_approved == True, "No approval!"
    # 이후 실행...
```

---

## 💡 2. 핵심 운영 기능

### ① The War Room (워 룸)
**기능**: AI 간 토론 과정을 "카카오톡 회의록" 형태로 시각화

**구조**:
```
[Trader 🧑‍💻]: "엔비디아 지금 사야 합니다! 수급 300% 증가!"
[Risk 👮]: "안 됩니다. VIX 22 돌파. 헌법 제3조 위반입니다."
[Analy st 🕵️]: "SEC 공시 확인: 대주주 매도 예정..."
[PM 🤵]: "Risk의 의견을 채택합니다. HOLD."
```

**원칙**:
- 확신도의 미세한 진동(Trembling Hand) 제거
- 확정된 이견(Dissent)만 기록

---

### ② Shadow Trade (그림자 거래)
**기능**: AI가 거부한 거래를 가상으로 추적

**목적**: "안 샀기 때문에 손실을 피했다" 증명

**리포트 예시**:
```
🛡️ [방어 성공]
3일 전: 테슬라 매수 제안 거부
이유: RSI 과열
현재 결과: -5.7% 하락
방어한 금액: 만약 ₩1,000,000 투자했으면 -₩57,000 손실
```

**주의**:
- 수익률에 합산 금지
- "방어한 손실"만 표시
- "놓친 수익" 표시 금지 (사용자 FOMO 방지)

---

### ③ Trust Mileage & Circuit Breaker
**Trust Mileage**:
- AI 방어 성공 누적 → 위임 한도 단계적 확대
- 사용자 승인 필수

**Circuit Breaker**:
- VIX 급등, MDD 임계 도달 시
- 자동 발동 (사용자 동의 불필요)
- Trust Mileage 즉시 회수

**알림 예시**:
```
⚠️ [긴급 안전 조치]
VIX 25 돌파로 '중립' → '방어' 모드 자동 전환
투자 비중 20% → 10% 강제 축소
이는 헌법적 의무입니다.
```

---

### ④ Governance Ledger (거버넌스 장부)
**기능**: 모든 의사결정 위변조 불가 기록

**스키마**:
```sql
governance_logs:
- proposal_id (UUID)
- action (APPROVE/REJECT/VETO)
- actor (USER/SYSTEM/OPERATOR)
- reason (헌법 조항 명시)
- context_hash (당시 시장 상황)
- hash_chain (이전 로그 해시)
```

---

## 🎭 3. 사용자 역할 재정의

### Commander (지휘관 = 사용자)
**권한**:
- 최종 승인 버튼 (Approve)
- 거부 버튼 (Reject)
- 설정 조정 (헌법 범위 내)

**책임**:
- 무행동 아님
- 적극적 방어 (Active Defense)

**UX**:
```
텔레그램 알림:
"엔비디아 매수 제안이 상정되었습니다"
[승인] [거부]
```

---

### Steward (관리자 = 운영자)
**권한**:
- 헌법 수정 (코드 레벨)
- System Freeze (비상사태 선포)
- AI 청원 승인/거부

**경고**:
- "안도감"은 책임의 포기
- AI 결정에 안도하면 즉시 Kill Switch

**일일 리트머스 질문**:
```
"만약 오늘 AI의 결정이 -10% 손실로 이어진다면,
나는 고객에게 그 기술적 원인을 3문장으로 설명할 수 있는가?"

→ 설명 못 하면 = 위험 (통제 상실)
```

---

## 📊 4. KPI 재정의

### 기존 KPI (삭제)
- ❌ 총 수익률 (Total Return)
- ❌ 수익 금액

### 새로운 KPI
- ✅ 자본 보존율 (Capital Preserved): 98.5%
- ✅ 방어한 손실 금액 (Avoided Loss): -₩540,000
- ✅ Max Drawdown: -0.01%
- ✅ 스트레스 지수 비교:
  - 시장: 🌊 (높은 파도)
  - 내 계좌: ⎯ (잔잔한 호수)

**리포트 구조**:
```markdown
# 월간 Shield Report (방패 보고서)

## 이번 달 성과
- 자본 보존율: 99.2%
- 시장 변동성: ±15%
- 내 계좌 변동성: ±2%

## The Graveyard (기각된 위험들)
- 거부한 제안: 14건
- 방어한 손실: -₩1,200,000

주요 사례:
1. 화요일: 테슬라 추격 매수 거부 → -4.2% 방어
2. 목요일: 엔비디아 풋옵션 거부 → 헌법 제2조 수호
```

---

## 🚨 5. 운영 원칙 (헌법적 원칙)

### 원칙 1: 실패의 규범화
"우리는 틀리는 것을 두려워하지 않는다.  
틀린 이유를 기록하지 않는 것을 두려워한다."

**AI 오답 노트**:
- 매주 금요일 장 마감 후 발행
- "이번 주 3가지 규칙 업데이트"
- 실패 → 개선의 서사

---

### 원칙 2: 헌법 우위
"사용자의 취향보다 시스템의 생존(Risk Management)이 우선이다."

**헌법 집행관**:
```
사용자: "리스크 설정 '공격형'으로 변경"
시스템: "❌ 헌법 제3조 위반. 
        이 설정은 파산 확률 80%.
        변경을 거부합니다."
```

---

### 원칙 3: 지휘권의 상품화
"AI는 참모이고, 사용자는 지휘관이다.  
우리는 그 '지휘의 경험'을 판매한다."

**가격 정책**:
| 등급 | 역할 | 권한 | 가격 |
|---|---|---|---|
| Observer | 참관인 | 보고만 받음 | $9/월 |
| Commander | 지휘관 | 승인/거부 | $49/월 |

---

## 🛠️ 6. 기술 구현 요구사항

### PM Agent 권한 제한 (중요!)
**문제**: PM이 새로운 논리를 창조하면 하위 Agent는 들러리

**해결**: ID-Based Selector Pattern

```python
# Trader가 제출
{
  "id": "A1",
  "text": "수급 300% 증가"
}

# Risk가 제출
{
  "id": "B1",
  "text": "VIX 22, RSI 과열"
}

# PM은 선택만 함
{
  "verdict": "HOLD",
  "selected_ids": ["B1"],  # Risk 채택
  "rationale_id": "B1"
}

# 시스템이 조립
final_report = get_text_by_id("B1")
```

**강제 방법**:
- PM 시스템 프롬프트: "새로운 문장 생성 금지 . ID만 반환"
- Pydantic Schema로 Output 검증

---

### 헌법 불변성 강제
```python
# backend/constitution/check_integrity.py
import hashlib

EXPECTED_HASH = "abc123..."

def verify_constitution():
    current_hash = hashlib.sha256(
        open('constitution.py', 'rb').read()
    ).hexdigest()
    
    if current_hash != EXPECTED_HASH:
        raise SystemFreeze("헌법 변조 감지!")
```

---

## 💰 7. 수익 모델

### 금지: 성과 보수 (Performance Fee)
- 수익의 N%를 떼가면 운영자가 수익을 쫓게 됨
- 헌법이 방해물이 됨

### 권장: 관리 보수 (Security Service Model)
**예시**: 세콤(보안업체) 모델
- "도둑이 안 들었다고 돈을 안 내나요?"
- "우리는 자산을 지키는 경비 용역비를 받습니다"

**메시지**:
```
"우리는 당신의 자산을 지키는 
경비 용역비로 월 $49를 받습니다.
수익은 덤입니다."
```

---

## 📂 8. 디렉토리 구조 (최종)

```
backend/
├── constitution/       # [Core] 불변의 법칙
│   ├── risk_limits.py
│   ├── allocation_rules.py
│   └── check_integrity.py
│
├── intelligence/       # [Brain] AI, Debate
│   ├── trader_agent.py
│   ├── risk_agent.py
│   ├── analyst_agent.py
│   ├── pm_agent.py
│   └── debate_engine.py
│
├── execution/          # [Body] 주문 집행
│   ├── order_executor.py
│   ├── smart_order_queue.py
│   └── kis_broker.py
│
├── governance/         # [Memory] 거버넌스
│   ├── governance_ledger.py
│   └── shadow_trade_tracker.py
│
└── api/                # [Mouth] 외부 통신
    ├── telegram_bot.py
    └── web_api.py
```

---

## 🎬 9. 3일 온보딩 시나리오

### Day 1: 목격 (Witness)
**미션**: "싸우는 AI를 보여주라"

```
가입 직후 → 테슬라 분석 War Room 강제 표시
Trader: "사야 합니다!"
Risk: "위험합니다!"
PM: "HOLD"

메시지: "안 사는 것도 능력입니다"
```

---

### Day 2: 충돌 (Conflict)
**미션**: "헌법의 벽을 만져보게 하라"

```
튜토리얼: "리스크 설정을 '공격형'으로 바꿔보세요"
사용자가 슬라이더 끝까지 올림

시스템: "❌ 헌법 제3조 위반입니다.
        이 설정은 귀하의 자산을 위험에 빠뜨립니다."

메시지: "이 시스템은 나를 진짜로 지켜주는구나"
```

---

### Day 3: 위임 (Delegation)
**미션**: "첫 번째 명령을 내리라"

```
Acting Commander 기능 해제
"'MDD -5% 이하일 때 자동 방어' 규칙을 승인하시겠습니까?"

[승인] 버튼 클릭

메시지: "지휘관의 명령이 접수되었습니다.
        지금부터 AI 위원회가 귀하의 자산을 불침번 섭니다."
```

---

## 🚀 10. Claude Code IDE 실행 명령 (순서대로)

```bash
# Step 1: 헌법 제정 (가장 중요!)
claude "Read docs/MASTER_BLUEPRINT_FINAL.md.
Create 'backend/constitution' package using Pure Python only.
Implement RiskLimits, AllocationRules, and check_integrity.py"

# Step 2: Multi-Agent Intelligence
claude "Implement 'backend/intelligence'.
Create TraderAgent, RiskAgent, AnalystAgent, PMAgent.
PMAgent must use ID-Based Selector Pattern - no new text generation.
Implement DebateEngine that orchestrates agents."

# Step 3: Execution & Governance
claude "Implement 'backend/execution' and 'backend/governance'.
Create GovernanceLedger with hash chaining.
Implement ShadowTradeTracker.
Ensure execution fails if Proposal.is_approved is False."

# Step 4: 검증
claude "Create verify_architecture.py that:
1. Attempts to import execution from constitution (should fail)
2. Verifies PM cannot generate new text
3. Validates hash chain in GovernanceLedger"
```

---

## ⚠️ 11. 경고 및 주의사항

### 운영자에게

**1년 뒤 망하는 원인**:
- ❌ 기술 버그 (X)
- ❌ 수익률 저조 (X)
- ✅ **운영 포퓰리즘** (O)

**징조**:
```
사용자 불만 → "잠깐만 헌법 완화해서 수익 내볼까?"
→ 원칙을 깬 순간 붕괴
```

**자가 진단**:
```
AI 결정에 "다행이다"라는 안도감을 느끼면
→ 즉시 Kill Switch
→ 책임을 포기한 것
```

---

### 개발자에게

**절대 자동화 금지**:
- ❌ 완전 자동매매
- ❌ "확실하면 알아서 사줘"
- ❌ "손절은 내가, 익절은 자동"

**핵 버튼 원칙**:
```
"핵미사일 발사는 대통령도 혼자 못 누릅니다.
우리는 당신의 자산을 핵 버튼처럼 다룹니다.
최종 실행은 반드시 인간의 생체 신호(클릭)가 필요합니다."
```

---

## 📝 12. 요약

이 아이디어는 현재 시스템의 **근본적인 재설계**를 요구합니다:

### 철학적 전환
- "돈 벌어주는 봇" → "판단 부담 덜어주는 위원회"
- "자동화" → "승인 매매"
- "수익률" → "방어 성과"

### 구조적 전환
- 단일 흐름 → 3권 분립
- AI 단독 결정 → Multi-Agent 토론
- 실행 중심 → 거버넌스 중심

### 제품적 전환
- 기술 자랑 → 신뢰 장치
- 복잡함 숨김 → 투명한 회의록
- 수익 판매 → 안전 판매

---

**다음 단계**:
1. 현재 시스템과 비교 분석
2. 마이그레이션 계획 수립
3. 단계별 구현 로드맵

**시작 여부 결정 필요!**

---

**작성일**: 2025-12-15 19:02 KST  
**작성자**: AI Trading System Design Team  
**문서 버전**: BLUEPRINT_FINAL_v1

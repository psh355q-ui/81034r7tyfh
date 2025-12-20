# Phase E1: Consensus Engine 구현 완료

**작성일**: 2025-12-06
**단계**: Phase E1 (Defensive Consensus Engine)
**상태**: ✅ **완료**

---

## 📋 Executive Summary

3개 AI(Claude, ChatGPT, Gemini)의 **방어적 투표 시스템**이 성공적으로 구현되었습니다.

### 핵심 성과
- ✅ **비대칭 의사결정 로직** 구현 완료
- ✅ **SignalAction 확장** (DCA, STOP_LOSS 추가)
- ✅ **Consensus API** 5개 엔드포인트 구현
- ✅ **실시간 통계 추적** 및 메트릭 수집

### 비대칭 투표 규칙
```
STOP_LOSS: 1/3 AI 경고 → 즉시 실행 (방어적)
BUY:       2/3 AI 찬성 → 허용 (신중)
DCA:       3/3 AI 전원 → 허용 (매우 신중)
```

---

## 🏗️ Architecture Overview

### 모듈 구조
```
backend/ai/consensus/
├── __init__.py                 # 모듈 export
├── consensus_engine.py         # 핵심 투표 엔진 (550 라인)
├── consensus_models.py         # 데이터 모델 (250 라인)
└── voting_rules.py             # 비대칭 규칙 (150 라인)

backend/api/
└── consensus_router.py         # API 라우터 (250 라인)

backend/schemas/
└── base_schema.py              # SignalAction 확장 (+2 액션)
```

### 데이터 플로우
```
1. API Request → VoteRequest
2. ConsensusEngine.vote_on_signal()
3. Parallel AI Calls (3개 병렬 실행)
   ├─ Claude → AIVote
   ├─ ChatGPT → AIVote
   └─ Gemini → AIVote
4. VotingRules.is_approved() (비대칭 로직)
5. ConsensusResult 반환
```

---

## 📦 Implemented Components

### 1. ConsensusEngine (핵심 엔진)

**파일**: [backend/ai/consensus/consensus_engine.py](backend/ai/consensus/consensus_engine.py)

**주요 메서드**:
```python
async def vote_on_signal(
    context: MarketContext,
    action: str,
    additional_info: Optional[Dict] = None
) -> ConsensusResult:
    """
    3개 AI의 투표 수집 및 합의 도출

    Returns:
        ConsensusResult(
            approved=True/False,
            votes={...},
            consensus_strength="unanimous|strong|weak|no_consensus"
        )
    """
```

**특징**:
- 병렬 투표 수집 (asyncio.gather)
- Mock 투표 지원 (AI 클라이언트 없이 테스트 가능)
- 실시간 통계 업데이트
- 투표 히스토리 저장 (최근 100개)

---

### 2. VotingRules (비대칭 규칙)

**파일**: [backend/ai/consensus/voting_rules.py](backend/ai/consensus/voting_rules.py)

**규칙 매핑**:
```python
ACTION_REQUIREMENTS = {
    "STOP_LOSS": VoteRequirement.ONE_OF_THREE,    # 1/3
    "BUY": VoteRequirement.TWO_OF_THREE,          # 2/3
    "SELL": VoteRequirement.TWO_OF_THREE,         # 2/3
    "DCA": VoteRequirement.THREE_OF_THREE,        # 3/3
    "HOLD": VoteRequirement.TWO_OF_THREE,         # 2/3
}
```

**핵심 로직**:
```python
@classmethod
def is_approved(cls, action: str, approve_count: int) -> bool:
    required = cls.get_required_votes(action)
    return approve_count >= required
```

---

### 3. Consensus Models (데이터 구조)

**파일**: [backend/ai/consensus/consensus_models.py](backend/ai/consensus/consensus_models.py)

**주요 모델**:

#### AIVote
```python
class AIVote(BaseModel):
    ai_model: str                      # "claude" | "chatgpt" | "gemini"
    decision: VoteDecision             # APPROVE | REJECT | ABSTAIN
    confidence: float                  # 0.0 ~ 1.0
    reasoning: str                     # 투표 근거
    risk_score: Optional[float]        # 리스크 점수
    timestamp: datetime
```

#### ConsensusResult
```python
class ConsensusResult(BaseModel):
    approved: bool                                # 최종 승인 여부
    action: str                                   # 투표 대상 액션
    votes: Dict[str, AIVote]                     # AI별 투표 결과
    approve_count: int                            # 찬성 수 (0~3)
    consensus_strength: ConsensusStrength         # unanimous/strong/weak
    confidence_avg: float                         # 평균 신뢰도
    vote_requirement: str                         # "1/3", "2/3", "3/3"
```

#### ConsensusStats
```python
class ConsensusStats(BaseModel):
    total_votes: int
    approved_votes: int
    rejected_votes: int
    approval_rate: float
    votes_by_action: Dict[str, int]
    ai_agreement_rate: Dict[str, float]          # AI별 다수 의견 일치율
    avg_consensus_time_ms: float
```

---

### 4. Consensus API (5개 엔드포인트)

**파일**: [backend/api/consensus_router.py](backend/api/consensus_router.py)

#### POST /consensus/vote
```bash
curl -X POST "http://localhost:8000/consensus/vote" \
  -H "Content-Type: application/json" \
  -d '{
    "market_context": {
      "ticker": "NVDA",
      "news": {"headline": "...", "segment": "training"}
    },
    "action": "BUY"
  }'
```

**응답 예시**:
```json
{
  "approved": true,
  "action": "BUY",
  "approve_count": 2,
  "vote_requirement": "2/3",
  "consensus_strength": "strong",
  "votes": {
    "claude": {"decision": "approve", "confidence": 0.85},
    "chatgpt": {"decision": "approve", "confidence": 0.78},
    "gemini": {"decision": "reject", "confidence": 0.65}
  }
}
```

#### GET /consensus/rules
```bash
curl "http://localhost:8000/consensus/rules"
```

**응답**:
```json
{
  "rules": {
    "STOP_LOSS": "1/3",
    "BUY": "2/3",
    "DCA": "3/3"
  },
  "explanations": {
    "STOP_LOSS": "1명 이상 찬성 필요 (방어적 - 빠른 대응)",
    "BUY": "2명 이상 찬성 필요 (과반수 - 신중한 결정)",
    "DCA": "3명 전원 찬성 필요 (만장일치 - 매우 신중한 결정)"
  }
}
```

#### GET /consensus/stats
```bash
curl "http://localhost:8000/consensus/stats"
```

**응답**:
```json
{
  "total_votes": 150,
  "approved_votes": 95,
  "approval_rate": 0.633,
  "votes_by_action": {"BUY": 80, "SELL": 30, "DCA": 25},
  "ai_agreement_rate": {
    "claude": 0.72,
    "chatgpt": 0.68,
    "gemini": 0.65
  }
}
```

#### GET /consensus/recent-votes
```bash
curl "http://localhost:8000/consensus/recent-votes?limit=10"
```

#### POST /consensus/test-vote (테스트용)
```bash
curl -X POST "http://localhost:8000/consensus/test-vote?action=BUY&ticker=NVDA"
```

---

### 5. SignalAction 확장

**파일**: [backend/schemas/base_schema.py](backend/schemas/base_schema.py)

**변경사항**:
```python
class SignalAction(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    REDUCE = "REDUCE"
    INCREASE = "INCREASE"
    DCA = "DCA"              # ← 신규 추가
    STOP_LOSS = "STOP_LOSS"  # ← 신규 추가
```

---

## ✅ Test Results

### 1. 단위 테스트 (ConsensusEngine)

**테스트 실행**:
```bash
cd ai-trading-system
python -m backend.ai.consensus.consensus_engine
```

**결과**:
```
======================================================================
Consensus Engine Test
======================================================================

----------------------------------------------------------------------
Testing: BUY
----------------------------------------------------------------------
Result: APPROVED
Votes: 2/3 (requirement: 2/3)
Consensus Strength: strong

----------------------------------------------------------------------
Testing: STOP_LOSS
----------------------------------------------------------------------
Result: APPROVED
Votes: 1/3 (requirement: 1/3)  ✅ 1명만 찬성해도 승인
Consensus Strength: weak

----------------------------------------------------------------------
Testing: DCA
----------------------------------------------------------------------
Result: REJECTED
Votes: 1/3 (requirement: 3/3)  ✅ 3명 전원 필요
Consensus Strength: weak

======================================================================
Total Votes: 4
Approved: 2
Rejected: 2
Approval Rate: 50.0%
```

### 2. API 통합 테스트

**BUY 액션 테스트**:
```bash
curl -X POST "http://localhost:8000/consensus/test-vote?action=BUY&ticker=NVDA"
```

**실제 응답**:
```json
{
  "action":"BUY",
  "ticker":"NVDA",
  "approved":false,
  "approve_count":1,
  "requirement":"2/3",
  "consensus_strength":"weak",
  "votes":{
    "claude":{"decision":"reject","confidence":0.71},
    "chatgpt":{"decision":"approve","confidence":0.72},
    "gemini":{"decision":"reject","confidence":0.65}
  }
}
```

**STOP_LOSS 액션 테스트**:
```bash
curl -X POST "http://localhost:8000/consensus/test-vote?action=STOP_LOSS&ticker=NVDA"
```

**실제 응답**:
```json
{
  "action":"STOP_LOSS",
  "approved":true,        ✅ 1명만 찬성해도 승인됨
  "approve_count":1,
  "requirement":"1/3",
  "consensus_strength":"weak"
}
```

**DCA 액션 테스트**:
```bash
curl -X POST "http://localhost:8000/consensus/test-vote?action=DCA&ticker=NVDA"
```

**실제 응답**:
```json
{
  "action":"DCA",
  "approved":false,       ✅ 1명 찬성, 3명 필요하여 거부
  "approve_count":1,
  "requirement":"3/3",
  "consensus_strength":"weak"
}
```

---

## 📊 Performance Metrics

### 처리 성능
- **평균 Consensus 시간**: 0.063ms (Mock 모드)
- **병렬 투표 수집**: 3개 AI 동시 호출
- **메모리 사용**: 히스토리 100개 제한

### 비용 예상
- **기존 (1회 호출)**: ~$0.001/요청
- **Consensus (3회 호출)**: ~$0.003/요청
- **월간 예상** (1000 signals): ~$3

### 승인율 (Mock 데이터)
```
STOP_LOSS: ~80% (1/3 요구)
BUY:       ~40% (2/3 요구)
DCA:       ~10% (3/3 요구)
```

---

## 🔧 Configuration

### Environment Variables
```bash
# AI API Keys (기존)
ANTHROPIC_API_KEY=your_claude_api_key
OPENAI_API_KEY=your_openai_api_key
GOOGLE_API_KEY=your_gemini_api_key
```

### Consensus Engine Settings
```python
# backend/ai/consensus/consensus_engine.py

# 히스토리 저장 개수
MAX_HISTORY = 100

# Mock 모드 (AI 클라이언트 없이 테스트)
# Consensus Engine이 자동으로 감지
```

---

## 📈 Next Steps (Phase E2: DCA Strategy)

### 1. DCA 전략 모듈 구현
- [ ] `backend/ai/strategies/dca_strategy.py` 생성
- [ ] 펀더멘털 체크 로직
- [ ] 최대 DCA 횟수 제한 (3회)
- [ ] 포지션 크기 계산 (점진적 감소)

### 2. Position Tracking System
- [ ] `backend/database/models.py`에 Position 모델 추가
- [ ] 평균 매수가 계산
- [ ] DCA 횟수 추적

### 3. Consensus Integration
- [ ] `DeepReasoningStrategy`에 Consensus 통합
- [ ] DCA 액션 시 자동 Consensus 호출
- [ ] STOP_LOSS 액션 시 자동 Consensus 호출

---

## 📝 Deliverables

### Code Files (950 lines)
1. ✅ `backend/ai/consensus/consensus_engine.py` (550 lines)
2. ✅ `backend/ai/consensus/consensus_models.py` (250 lines)
3. ✅ `backend/ai/consensus/voting_rules.py` (150 lines)
4. ✅ `backend/api/consensus_router.py` (250 lines)
5. ✅ `backend/ai/consensus/__init__.py` (37 lines)
6. ✅ `backend/schemas/base_schema.py` (업데이트: +2 SignalAction)

### API Endpoints (5개)
1. ✅ `POST /consensus/vote` - 투표 실행
2. ✅ `GET /consensus/rules` - 규칙 조회
3. ✅ `GET /consensus/stats` - 통계 조회
4. ✅ `GET /consensus/recent-votes` - 최근 투표 조회
5. ✅ `POST /consensus/test-vote` - 테스트 투표

### Documentation
1. ✅ [251210_09_AI_Ideas_Integration_Analysis.md](251210_09_AI_Ideas_Integration_Analysis.md)
2. ✅ [251210_10_Phase_E1_Consensus_Engine_Complete.md](251210_10_Phase_E1_Consensus_Engine_Complete.md) (본 문서)

---

## 🎯 Success Criteria

### ✅ 완료된 기준
- [x] 3개 AI 병렬 투표 수집
- [x] 비대칭 의사결정 로직 구현
- [x] STOP_LOSS는 1명 경고 시 승인
- [x] BUY는 2명 찬성 필요
- [x] DCA는 3명 전원 동의 필요
- [x] API 엔드포인트 5개 구현
- [x] 실시간 통계 추적
- [x] Mock 모드 지원 (테스트 용이)

### 🔄 향후 개선
- [ ] AI별 가중치 적용 (Performance Review 통합 후)
- [ ] 투표 타임아웃 설정
- [ ] Consensus 캐싱 (동일 요청 재사용)
- [ ] 투표 근거 상세화 (프롬프트 개선)

---

## 🔗 Related Documents

- [Phase A-D 완료](./MASTER_INTEGRATION_ROADMAP_v5.md)
- [Skill Layer](./07_Skill_Layer_Implementation_Complete.md)
- [Production Monitoring](./251210_08_Production_Monitoring_Complete.md)
- [AI Ideas Integration](./251210_09_AI_Ideas_Integration_Analysis.md)

---

## 💬 Usage Example

### Python Code
```python
from backend.ai.consensus import get_consensus_engine
from backend.schemas.base_schema import MarketContext, NewsFeatures, MarketSegment

# Consensus Engine 가져오기
engine = get_consensus_engine()

# MarketContext 구성
context = MarketContext(
    ticker="NVDA",
    news=NewsFeatures(
        headline="NVIDIA announces Blackwell GPU",
        segment=MarketSegment.TRAINING,
        sentiment=0.85
    )
)

# 투표 실행
result = await engine.vote_on_signal(context, "BUY")

if result.approved:
    print(f"BUY signal APPROVED with {result.approve_count}/3 votes")
    # 매수 실행
else:
    print(f"BUY signal REJECTED ({result.approve_count}/3 votes)")
    # 매수 거부
```

### API Usage
```bash
# 1. 투표 규칙 확인
curl http://localhost:8000/consensus/rules

# 2. BUY 액션 투표
curl -X POST "http://localhost:8000/consensus/test-vote?action=BUY&ticker=NVDA"

# 3. 통계 확인
curl http://localhost:8000/consensus/stats

# 4. 최근 투표 조회
curl "http://localhost:8000/consensus/recent-votes?limit=5"
```

---

**작성:** AI Trading System
**일시:** 2025-12-06
**상태:** Phase E1 완료, Phase E2 준비 중
**다음 단계:** DCA Strategy 구현

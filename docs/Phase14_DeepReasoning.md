# 📚 Phase 14: Deep Reasoning Strategy

**Version**: 1.0  
**Date**: 2025-11-26  
**Status**: 구현 완료  

---

## 🎯 개요

Phase 14는 **"꼬리에 꼬리를 무는" 3단계 심층 추론(Deep Reasoning)** 전략을 구현합니다.

### 왜 필요한가?

**단순 뉴스 분석 (기존)**
```
뉴스: "Google TPU v6 발표"
→ 1차원 판단: "Google 호재, 매수"
문제: 시장은 이미 알고 있음. 숨은 수혜자 놓침.
```

**심층 추론 (Phase 14)**
```
뉴스: "Google TPU v6 발표"
→ Step 1: Google 직접 호재
→ Step 2: TPU 확대 → Nvidia 의존↓ → Broadcom(TPU 설계) 수혜
→ Step 3: Hidden Beneficiary = AVGO (브로드컴)
결론: "남들이 GOOGL 살 때, 우리는 AVGO를 산다"
```

---

## 🏗️ 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│                    Deep Reasoning Pipeline                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  News Input                                                      │
│      ↓                                                           │
│  [Entity Extraction] - 핵심 기업/키워드 추출                      │
│      ↓                                                           │
│  [Knowledge Graph Lookup] - 기존 관계 조회                       │
│      ↓                                                           │
│  [Live Verification] - 실시간 검색으로 관계 검증                  │
│      ↓                                                           │
│  [3-Step CoT Reasoning]                                          │
│      │                                                           │
│      ├─ Step 1: Direct Impact (직접 영향)                        │
│      │     "Google TPU → Google 호재"                            │
│      │                                                           │
│      ├─ Step 2: Secondary Impact (꼬리 물기)                     │
│      │     "TPU 확대 → Nvidia 의존↓ → Broadcom 수혜"             │
│      │                                                           │
│      └─ Step 3: Strategic Conclusion                             │
│            "Primary: GOOGL, Hidden: AVGO, Loser: NVDA"           │
│      ↓                                                           │
│  [Action Items] - 실행 가능한 매매 신호                          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 파일 구조

```
backend/
├── config_phase14.py              # Phase 14 설정 (AI 역할 배정)
├── ai/
│   ├── ai_client_factory.py       # AI 클라이언트 추상화 팩토리
│   └── reasoning/
│       ├── deep_reasoning.py      # 핵심 Deep Reasoning 전략
│       └── cot_prompts.py         # CoT 프롬프트 템플릿 (Claude/Gemini/GPT)
├── data/
│   └── knowledge_graph/
│       └── knowledge_graph.py     # Knowledge Graph (관계 저장/검색)
├── backtesting/
│   └── ab_backtest.py             # A/B 백테스트 (Keyword vs CoT+RAG)
├── apis/
│   └── reasoning_api.py           # REST API 엔드포인트
scripts/
└── run_deep_reasoning.py          # 실행 스크립트
docs/
└── Phase14_DeepReasoning.md       # 이 문서
```

---

## 🚀 빠른 시작

### 1. 설치

```bash
cd ai-trading-system

# 의존성 설치
pip install pydantic-settings google-generativeai anthropic openai

# 선택적 (A/B 백테스트용)
pip install yfinance pandas numpy
```

### 2. 환경 변수 설정

```bash
# .env
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=AIza...
OPENAI_API_KEY=sk-...  # 선택 (임베딩용)

# Phase 14 설정 (선택)
PHASE14_REASONING_MODEL_NAME=gemini-1.5-pro
PHASE14_ENABLE_LIVE_KNOWLEDGE_CHECK=true
```

### 3. 데모 실행

```bash
# 전체 데모 (Mock 모드)
python scripts/run_deep_reasoning.py --mode demo

# 특정 뉴스 분석
python scripts/run_deep_reasoning.py --mode reasoning \
    --news "Google announced TPU v6 with Anthropic signing 1M TPU contract"

# A/B 백테스트
python scripts/run_deep_reasoning.py --mode backtest
```

---

## 🧠 핵심 컴포넌트

### 1. AI Client Factory

**Model-Agnostic 설계** - 어떤 AI든 교체 가능

```python
from backend.ai.ai_client_factory import AIClientFactory

# Gemini 클라이언트
client = AIClientFactory.create("gemini-1.5-pro")

# Claude 클라이언트
client = AIClientFactory.create("claude-3-haiku-20240307")

# OpenAI 클라이언트  
client = AIClientFactory.create("gpt-4o-mini")

# 모두 동일한 인터페이스
response = await client.call_api("Your prompt here")
search_result = await client.search_web("Your query")
```

### 2. Knowledge Graph

**기업 간 관계를 그래프로 저장**

```python
from backend.data.knowledge_graph.knowledge_graph import KnowledgeGraph

kg = KnowledgeGraph()

# 관계 추가
await kg.add_relationship(
    subject="Google",
    relation="partner",
    obj="Broadcom",
    evidence_text="Broadcom designs TPU interconnects"
)

# 관계 조회
relations = await kg.get_relationships("Google")
# → [{"subject": "Google", "relation": "partner", "object": "Broadcom"}, ...]

# 경로 탐색 (꼬리 물기)
paths = await kg.find_path("Google", "Nvidia", max_depth=2)
# → Google → competitor → Nvidia
# → Google → partner → Broadcom → customer → Nvidia
```

### 3. Deep Reasoning Strategy

```python
from backend.ai.reasoning.deep_reasoning import DeepReasoningStrategy

strategy = DeepReasoningStrategy()

result = await strategy.analyze_news(
    "Google announced Gemini 3 trained entirely on TPUs"
)

# 결과 확인
print(result.theme)               # "Rise of Custom AI Silicon"
print(result.primary_beneficiary) # {"ticker": "GOOGL", "action": "BUY", "confidence": 0.85}
print(result.hidden_beneficiary)  # {"ticker": "AVGO", "action": "BUY", "confidence": 0.90}
print(result.loser)               # {"ticker": "NVDA", "action": "TRIM", "confidence": 0.60}
print(result.reasoning_trace)     # ["1. Google TPU success...", "2. Broadcom benefits..."]
```

---

## 📊 A/B 백테스트

### 비교 방법

| 방법 | 설명 | 장점 | 단점 |
|------|------|------|------|
| **Keyword-only** | 키워드 매칭 규칙 | 빠름, 저비용 | 숨은 수혜자 놓침 |
| **CoT+RAG** | 심층 추론 + 지식 그래프 | Hidden Beneficiary 발굴 | AI 비용 발생 |

### 실행

```bash
python scripts/run_deep_reasoning.py --mode backtest
```

### 예상 결과

```
===============================================================================
                    A/B BACKTEST COMPARISON REPORT
===============================================================================

┌─────────────────────┬──────────────────┬────────────────────────┐
│ Metric              │ Keyword-only     │ CoT+RAG                │
├─────────────────────┼──────────────────┼────────────────────────┤
│ Avg Abnormal Return │          5.20%   │                12.40%  │
│ Hit Rate            │         60.00%   │                80.00%  │
│ Sharpe Ratio        │           0.45   │                  1.12  │
│ Total Signals       │              8   │                    12  │
└─────────────────────┴──────────────────┴────────────────────────┘

🏆 WINNER: CoT+RAG (+138.5% improvement)
```

---

## 🔌 API 엔드포인트

### POST /api/v1/reasoning/analyze

```bash
curl -X POST http://localhost:8000/api/v1/reasoning/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "news_text": "Google announced TPU v6",
    "enable_verification": true
  }'
```

**응답:**
```json
{
  "success": true,
  "theme": "Rise of Custom AI Silicon",
  "primary_beneficiary": {
    "ticker": "GOOGL",
    "action": "BUY",
    "confidence": 0.85
  },
  "hidden_beneficiary": {
    "ticker": "AVGO",
    "action": "BUY",
    "confidence": 0.90
  },
  "reasoning_trace": [
    "1. Google TPU v6 reduces Nvidia dependency",
    "2. Broadcom designs TPU → hidden beneficiary"
  ]
}
```

### GET /api/v1/reasoning/knowledge/{entity}

```bash
curl http://localhost:8000/api/v1/reasoning/knowledge/Google
```

### GET /api/v1/reasoning/backtest

```bash
curl http://localhost:8000/api/v1/reasoning/backtest
```

---

## ⚙️ 설정 옵션

### config_phase14.py

```python
class Phase14Settings:
    # AI 모델 역할 배정
    REASONING_MODEL_NAME = "gemini-1.5-pro"  # 심층 추론용
    SCREENER_MODEL_NAME = "gemini-1.5-flash"  # 빠른 스크리닝
    
    # 실시간 검증
    ENABLE_LIVE_KNOWLEDGE_CHECK = True
    KNOWLEDGE_VERIFY_INTERVAL_HOURS = 24
    
    # 추론 설정
    REASONING_STEPS = 3
    MAX_REASONING_DEPTH = 3
    CONFIDENCE_THRESHOLD = 0.6
    
    # 비용 관리
    DAILY_REASONING_LIMIT = 10
    MAX_REASONING_TOKENS = 4000
    REASONING_CACHE_TTL_HOURS = 12
```

---

## 💰 비용 분석

| 모델 | 역할 | 비용/호출 | 일 10회 | 월 비용 |
|------|------|----------|---------|---------|
| Gemini 1.5 Pro | Reasoning | ~$0.007 | $0.07 | **$2.10** |
| Gemini 1.5 Flash | Screener | ~$0.0003 | $0.003 | $0.09 |
| Claude Haiku | Decision | ~$0.001 | $0.01 | $0.30 |

**총 예상 비용: ~$2.50/월** (일 10회 심층 추론 기준)

---

## 🔧 확장 가이드

### 새 AI 공급자 추가

```python
# backend/ai/ai_client_factory.py

class MyCustomClient(BaseAIClient):
    async def call_api(self, prompt, max_tokens=2000, temperature=0.3, system_prompt=None):
        # 구현
        pass
    
    async def search_web(self, query):
        # 구현
        pass

# 팩토리에 등록
AIClientFactory._providers["mycustom"] = MyCustomClient
```

### 새 관계 타입 추가

```python
# backend/config_phase14.py

RELATIONSHIP_TYPES = [
    "partner",
    "competitor",
    "supplier",
    "customer",
    "investor",
    # 새 타입 추가
    "acquirer",      # 인수자
    "joint_venture"  # 합작 투자
]
```

---

## 🎓 핵심 인사이트 (Gemini + ChatGPT 제안)

### 1. 엔비디아 독점의 균열
- Google TPU + Anthropic 계약 = "반(反) 엔비디아 연합"
- 빅테크 자체 칩 개발 가속화
- Broadcom = "AI 시대의 숨은 수혜자"

### 2. 에너지 위기 연결고리
```
AI 폭발 → 데이터센터 확대 → 전력 부족 → 원자력/SMR 수요
→ 숨은 수혜자: Vistra, Constellation Energy, 변압기 관련주
```

### 3. 메모리 슈퍼사이클 역설
- "스마트폰 메모리 조달 중단" = 겉보기 악재
- 실제: 공급자 우위 시장 = 가격 결정권 = **호재**
- AI가 "역발상" 분석을 수행하도록 컨텍스트 주입

---

## 📝 Changelog

### v1.0.0 (2025-11-26)
- 초기 구현
- Deep Reasoning Strategy
- Knowledge Graph
- AI Client Factory (Model-Agnostic)
- A/B Backtest Engine
- REST API
- CoT 프롬프트 템플릿 (Claude/Gemini/GPT)

---

## 🔗 관련 문서

- [MASTER_GUIDE.md](../MASTER_GUIDE.md) - 전체 프로젝트 가이드
- [config_phase14.py](../backend/config_phase14.py) - 설정 파일
- [Spec-Kit 문서](https://github.com/github/spec-kit)

---

*"The market can stay irrational longer than you can stay solvent, but deep reasoning helps you stay rational."*

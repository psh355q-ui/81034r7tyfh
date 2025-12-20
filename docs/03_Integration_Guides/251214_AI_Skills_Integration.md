# AI Skills Integration Guide

## 개요

본 문서는 Claude, Gemini, ChatGPT의 고급 Skills를 AI Trading System에 통합하는 방법을 설명합니다.

작성일: 2025-12-14

## AI 모델별 고급 Skills

### 1. Gemini Skills

#### Google Search Tool
- **기능**: 실시간 웹 검색 및 사실 검증
- **활용 아이디어**: Wall Street Intelligence, Macro Consistency Checker
- **통합 우선순위**: 🔥 최우선

#### Video/Audio Analysis
- **기능**: 비디오 직접 분석, 멀티모달 입력
- **활용 아이디어**: Video Analysis Engine
- **통합 우선순위**: 높음

#### Extended Context (2M tokens)
- **기능**: 초장문 컨텍스트 처리
- **활용 아이디어**: Deep Profiling Agent
- **통합 우선순위**: 중간

### 2. Claude Skills

#### Extended Thinking
- **기능**: 심층 논리 추론
- **활용 아이디어**: Skeptic Agent, Macro Consistency Checker
- **통합 우선순위**: 🔥 최우선 (이미 사용 중)

#### Computer Use
- **기능**: 브라우저 제어
- **활용 아이디어**: 동적 웹페이지 크롤링
- **통합 우선순위**: 낮음

### 3. ChatGPT/OpenAI Skills

#### Whisper (STT)
- **기능**: 음성 → 텍스트 변환
- **활용 아이디어**: Video Analysis Engine
- **통합 우선순위**: 높음

#### Code Interpreter
- **기능**: Python 코드 실행 환경
- **활용 아이디어**: Scenario Simulator
- **통합 우선순위**: 중간

## 즉시 구현 가능 (Quick Wins)

### 1. Gemini Search Tool 통합 (1일)

**위치**: `backend/ai/tools/search_grounding.py` (신규)

```python
import google.generativeai as genai

class SearchGroundingTool:
    """Gemini Google Search Tool Wrapper"""
    
    def __init__(self):
        self.model = genai.GenerativeModel(
            'gemini-2.0-flash-exp',
            tools='google_search'  # Search Tool 활성화
        )
    
    async def verify_news(self, headline: str) -> dict:
        """뉴스 사실 검증"""
        prompt = f"""
        다음 뉴스가 사실인지 Google 검색으로 확인하세요:
        "{headline}"
        
        최소 3개 신뢰 출처에서 확인하세요.
        """
        response = self.model.generate_content(prompt)
        return {"verified": True, "sources": [...]}
    
    async def profile_person(self, name: str) -> dict:
        """인물 프로파일링"""
        prompt = f"{name}의 과거 발언, 정책 성향, 편향 패턴 검색"
        response = self.model.generate_content(prompt)
        return response
```

**통합 위치**:
- `Wall Street Intelligence Collector`
- `Deep Profiling Agent`

### 2. Skeptic Agent 추가 (1일)

**위치**: `backend/ai/debate/skeptic_agent.py` (신규)

```python
from backend.ai.claude_client import ClaudeClient

class SkepticAgent:
    """악마의 변호인 - 강제 비관론자"""
    
    PERSONA = """
    당신은 회의론자(Skeptic)입니다.
    다른 AI들이 "매수"를 외칠 때:
    1. 데이터가 틀렸을 가능성
    2. 시장이 간과한 악재
    3. 최악의 시나리오
    만 찾으세요.
    """
    
    def __init__(self):
        self.claude = ClaudeClient()
    
    async def challenge(self, consensus_view: str) -> str:
        """합의 의견에 도전"""
        prompt = f"{self.PERSONA}\n\n합의: {consensus_view}\n\n약점 찾기"
        return await self.claude.generate(prompt)
```

**통합 위치**: `AIDebateEngine` (4번째 에이전트)

## 단기 구현 (2-4주)

### 3. Whisper STT 통합

**필요 라이브러리**:
```bash
pip install openai yt-dlp
```

**구현 예시**:
```python
import openai

audio_file = open("speech.mp3", "rb")
transcript = client.audio.transcriptions.create(
    model="whisper-1",
    file=audio_file,
    response_format="verbose_json",
    timestamp_granularities=["segment"]
)
```

### 4. Macro Consistency Checker

**위치**: `backend/ai/reasoning/macro_consistency.py` (신규)

```python
class MacroConsistencyChecker:
    """경제 지표 간 모순 탐지"""
    
    async def detect_contradictions(self, indicators: dict):
        """
        GDP vs Interest Rate 모순 탐지
        
        예: GDP 상승 + 금리 인하 = 모순!
        """
        if indicators["gdp_trend"] == "UP" and indicators["rate_trend"] == "DOWN":
            return {
                "contradiction": True,
                "type": "Over-Stimulus Warning",
                "scenarios": [
                    "정치적 압력",
                    "숨은 유동성 위기",
                    "데이터 조작 가능성"
                ]
            }
```

## 구현 로드맵

```
Phase 1 (1주): Quick Wins
├── Gemini Search Tool
└── Skeptic Agent

Phase 2 (2주): 핵심 기능
├── Macro Consistency Checker
└── Whisper STT

Phase 3 (1개월): 고급 기능
├── Video Analysis
└── Code Interpreter
```

## 예상 비용

| Skill | 비용 | 비고 |
|-------|------|------|
| Gemini Search | $0 | 무료 티어 활용 |
| Whisper STT | ~$0.006/분 | 영상 분석 시 |
| Extended Thinking | 포함 | 기존 Claude API |
| Code Interpreter | $0.03/세션 | Sandbox 필요 시 |

## 통합 체크리스트

- [ ] Gemini Search Tool 활성화
- [ ] Skeptic Agent 구현
- [ ] AIDebateEngine 통합 (Skeptic)
- [ ] Macro Consistency Checker 구현
- [ ] Whisper STT 테스트
- [ ] Video Analysis POC
- [ ] Code Interpreter Sandbox

---

**다음 문서**: `251214_Phase_B_Implementation_Plan.md`

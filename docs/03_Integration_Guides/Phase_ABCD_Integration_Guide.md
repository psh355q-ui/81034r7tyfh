# Phase A-D 통합 사용 가이드

**대상**: 개발자 및 사용자  
**업데이트**: 2025-12-14

---

## 🎯 전체 시스템 워크플로우

```
뉴스 입력
    ↓
[1] 사실 검증 (Gemini Search Tool)
[2] 찌라시 체크 (Theme Risk Detector)
    ↓
[3] AI 토론 (Debate Engine)
    - Claude, GPT-4, Gemini
    ↓
[4] Skeptic 도전 (맹점 발견)
    ↓
[5] 경제 모순 체크 (Macro Consistency)
    ↓
[6] 글로벌 영향 분석 (Event Graph)
    ↓
[7] 시나리오 생성 (Scenario Simulator)
    ↓
[8] 전문가 리포트 (Market Reporter)
    ↓
[9] 자동 기록 (Debate Logger)
[10] 가중치 학습 (Weight Trainer)
```

---

## 📚 모듈별 사용법

### 1. Gemini Search Tool

```python
from backend.ai.tools.search_grounding import get_search_tool

search = get_search_tool()

# 뉴스 사실 검증
result = await search.verify_news(
    headline="NVIDIA 신제품 발표",
    min_sources=3
)
```

### 2. Skeptic Agent

```python
from backend.ai.debate.skeptic_agent import get_skeptic_agent

skeptic = get_skeptic_agent()

# 합의 도전
challenge = await skeptic.challenge(
    consensus_view="NVDA BUY 85%",
    reasoning="AI 붐 지속",
    confidence=0.85
)
```

### 3. Macro Consistency Checker

```python
from backend.ai.reasoning.macro_consistency import get_consistency_checker

checker = get_consistency_checker()

# 지표 모순 탐지
contradictions = await checker.check_consistency([
    gdp_indicator,
    rate_indicator
])
```

### 4. AI Market Reporter

```python
from backend.ai.reporters.ai_market_reporter import get_market_reporter

reporter = get_market_reporter()

# 일일 브리핑 생성
briefing = await reporter.generate_daily_briefing()
markdown = reporter.format_markdown(briefing)
```

---

## 🔧 설정 방법

### 환경 변수 (.env)

```bash
# 필수
GEMINI_API_KEY=your_key
ANTHROPIC_API_KEY=your_key

# 선택
OPENAI_API_KEY=your_key  # Video Analysis
NEWSAPI_KEY=your_key     # News Collection
```

### AIDebateEngine 설정

```python
from backend.ai.debate.ai_debate_engine import AIDebateEngine

# Skeptic Agent 포함
engine = AIDebateEngine(
    enable_logging=True,
    enable_weight_training=True,
    enable_skeptic=True  # 🆕
)

# 토론 실행
result = await engine.debate(market_context)

# 결과
print(result.blind_spots)  # Skeptic이 발견한 맹점
```

---

## 📖 추가 가이드

- [Phase A 구현 보고서](../02_Phase_Reports/251214_Phase_A_Implementation_Report.md)
- [Phase B 완료 보고서](../02_Phase_Reports/phase_b_completion_report.md)
- [AI Skills 통합](251214_AI_Skills_Integration.md)

---

**작성일**: 2025-12-14

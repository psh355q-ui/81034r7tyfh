# 통합 개발 계획 (2025-12-14)

## 📋 문서 개요

**작성일**: 2025-12-14
**버전**: 1.0
**목적**: Ideas 폴더 분석 결과를 바탕으로 한 Phase A 완료 및 Phase B 이후 개발 로드맵

---

## 🎯 전체 목표

**비전**: 데이터를 의심하고 스스로 학습하는 자율형 AI 헤지펀드 시스템

### 핵심 차별화 요소
1. **모순 탐지** - 경제 지표 간 논리적 충돌 감지
2. **자율 학습** - AI 성과 기반 자동 최적화
3. **전문가 수준** - Wall Street 애널리스트급 분석

---

## ✅ Phase A: AI Self-Learning Foundation (완료)

### 기간
2025-12-14 (당일 완료)

### 구현 항목
1. ✅ **Debate Logger**
   - 모든 AI 토론 자동 기록
   - PnL 추적 및 성과 분석
   - 파일: `backend/ai/meta/debate_logger.py`

2. ✅ **Agent Weight Trainer**
   - 성과 기반 가중치 자동 조정
   - 가중치 범위: 0.1 ~ 3.0
   - 파일: `backend/ai/meta/agent_weight_trainer.py`

3. ✅ **AIDebateEngine 통합**
   - 자동 로깅 연동
   - 동적 가중치 로드
   - 주기적 재조정 메서드

### 성과
- 구현 완료율: 100%
- AI 자율 학습 기반 완성
- 투명성 및 추적성 확보

**관련 문서**:
- `docs/02_Phase_Reports/251214_Phase_A_Implementation_Report.md`
- `walkthrough.md`

---

## 🔥 Phase B: Critical Intelligence (우선순위 - 1-2주)

### 최우선 구현 (Week 1)

#### 1. Macro Consistency Checker ⭐ 필수
**목적**: 경제 지표 간 논리적 모순 탐지

**핵심 개념**:
```python
# GDP 상승인데 금리 인하? = 정치적 압력 or 숨은 위기!
if gdp_trend == "UP" and rate_trend == "DOWN":
    flag_as_contradiction("Over-Stimulus Warning")
```

**구현 위치**: `backend/ai/reasoning/macro_consistency.py`

**필요 기능**:
- GDP vs Interest Rate 모순 탐지
- Unemployment vs Inflation 모순 탐지
- 정치적 압력 추론
- 3가지 시나리오 자동 생성

**활용 AI**: Claude (Extended Thinking) + Gemini (Search)

---

#### 2. Skeptic Agent (악마의 변호인) ⭐ 필수
**목적**: 과최적화 방지, 강제 비관론자

**핵심 개념**:
- 다수 의견에 무조건 반대
- "시장 맹점(Blind Spot)" 발견
- Devil's Advocate 역할

**구현 위치**: `backend/ai/debate/skeptic_agent.py`

**통합**: `AIDebateEngine`에 4번째 에이전트로 추가

**프롬프트**:
```
당신은 회의론자입니다.
다른 AI가 "매수"를 외칠 때:
1. 데이터가 틀렸을 가능성
2. 시장이 간과한 악재
3. 최악의 시나리오
만 찾으세요.
```

---

#### 3. Gemini Search Tool 통합 ⭐ Quick Win
**목적**: 실시간 웹 검색으로 사실 검증

**구현 위치**: `backend/ai/tools/search_grounding.py`

**코드** (5줄 추가로 완성!):
```python
model = genai.GenerativeModel(
    'gemini-2.0-flash-exp',
    tools='google_search'  # 이것만 추가!
)
```

**활용**:
- 뉴스 헤드라인 사실 검증
- 인물 과거 이력 검색
- Fed 발언 교차 확인

---

### 추가 구현 (Week 2)

#### 4. Global Event Graph
**목적**: 국가 간 영향 전파 분석

**예시**:
```
일본 금리 인상 → 엔캐리 트레이드 청산 
  → 나스닥 유동성 축소 → 코스피 하락
```

**구현**: `backend/ai/macro/global_event_graph.py`

#### 5. Scenario Simulator
**목적**: "만약 ~한다면?" 시뮬레이션

**시나리오**:
- Bullish: 금리 인하 + 고용 둔화
- Neutral: Fed 데이터 의존
- Bearish: 인플레 재가속

---

## 💎 Phase C: Professional Intelligence (3-4주)

### Week 3-4

#### 6. Wall Street Intelligence Collector ⭐
**목적**: 전문가 수준 리포팅

**수집 대상**:
- Fed 캘린더 및 발언
- 경제 지표 일정 (CPI, PCE, NFP)
- 전문가 코멘트 ("JP모건에 따르면...")
- 애널리스트 의견

**출력 형식**:
```
📊 오늘의 시황
S&P 500: +1.2% (CPI 예상 하회)

💬 월가 의견
- JP모건: "신중한 낙관론"
- 골드만: "인플레 리스크"

🔮 시나리오
신뢰도: 78%
```

**파일**: `backend/data/collectors/wall_street_intel.py`

---

#### 7. AI Market Reporter
**목적**: 일일 브리핑 자동 생성

**생성 콘텐츠**:
- 간밤 시황 요약
- Fed/경제 이벤트 분석
- 전문가 의견 인용
- 투자 시사점

---

#### 8. Theme Risk Detector
**목적**: 한국 특화 찌라시/정치테마 감지

**리스크 점수**:
```
ThemeRiskScore = 
  PriceSpikeScore + 
  VolumeSpikeScore + 
  (No-DART-News Penalty) + 
  CommunitySource Weight
```

---

## 🚀 Phase D: Advanced Features (1-2개월)

### 고급 기능

#### 9. Video Analysis Engine
**기술 스택**:
- Gemini Video API (직접 분석) or
- Whisper STT (음성 → 텍스트)
- NLP 토픽 추출

**대상**: "김현석의 월스트리트나우" 등

---

#### 10. Deep Profiling Agent
**기능**:
- Vector DB에서 인물 이력 검색
- 편향 패턴 분석
- 정책 신뢰도 평가

---

#### 11. Strategy Refiner (자율 개선)
**기능**:
- AI가 매매 복기
- Config 수정 제안
- 자율 진화

**파일**: `backend/ai/meta/strategy_refiner.py` (존재하나 통합 안됨)

---

## 📊 전체 로드맵 타임라인

```
2025-12-14 (D+0)  : ✅ Phase A 완료
2025-12-21 (D+7)  : Phase B Week 1 완료 목표
2025-12-28 (D+14) : Phase B Week 2 완료 목표
2026-01-11 (D+28) : Phase C 완료 목표
2026-02-14 (D+60) : Phase D 완료 목표
```

---

## 🎯 우선순위 매트릭스

| 아이디어 | 영향도 | 난이도 | 우선순위 | Phase |
|---------|-------|-------|---------|-------|
| Macro Consistency Checker | 🔥🔥🔥 | 중 | 1 | B |
| Skeptic Agent | 🔥🔥🔥 | 낮 | 1 | B |
| Gemini Search Tool | 🔥🔥🔥 | 낮 | 1 | B |
| Global Event Graph | 🔥🔥 | 중 | 2 | B |
| Scenario Simulator | 🔥🔥 | 중 | 2 | B |
| Wall Street Intelligence | 🔥🔥 | 중 | 3 | C |
| AI Market Reporter | 🔥🔥 | 중 | 3 | C |
| Video Analysis | 🔥 | 높 | 4 | D |
| Strategy Refiner | 🔥🔥 | 높 | 3 | C-D |

---

## 💰 예상 비용

### API 비용 (월간)
- 기존 (Phase A): ~$3/월
- + Phase B: ~$5/월 (Gemini Search 무료)
- + Phase C: ~$10/월
- + Phase D: ~$15/월 (Video Analysis 추가)

**총 예상**: ~$15/월 (헤지펀드급 시스템 치고는 극히 저렴)

---

## 📚 관련 문서

### Phase Reports
- `docs/02_Phase_Reports/251214_Phase_A_Implementation_Report.md`

### Integration Guides
- `docs/03_Integration_Guides/251214_AI_Skills_Integration.md`

### Feature Guides
- (Phase B 시작 시 생성 예정)

### Artifacts
- `ideas_implementation_audit.md` - 전체 아이디어 구현 상태
- `ai_skills_mapping.md` - AI Skills 매핑 분석
- `walkthrough.md` - Phase A 완료 보고서

---

## 🔄 진행 상황 추적

### 완료
- [x] Phase A: AI Self-Learning Foundation

### 진행 중
- [ ] Phase B 준비 (문서화 완료)

### 대기 중
- [ ] Phase B 실행
- [ ] Phase C 계획
- [ ] Phase D 계획

---

## ✅ 다음 액션 아이템

### 즉시 (D+0 ~ D+3)
1. Gemini Search Tool 통합 (1일)
2. Skeptic Agent 구현 (1일)
3. Macro Consistency Checker 설계 (1일)

### 단기 (D+4 ~ D+7)
4. Macro Consistency Checker 구현
5. AIDebateEngine에 Skeptic 통합
6. End-to-end 테스트

---

**작성일**: 2025-12-14
**작성자**: AI Trading System Development Team
**버전**: 1.0
**다음 업데이트**: Phase B 시작 시

# 동적 뉴스 감지 시스템 구현 완료

**Date**: 2026-01-21
**Category**: Enhancement
**Status**: Completed ✅

## 문제점

사용자 피드백:
> "최근 이슈가 되는 뉴스에 해당하는 걸 검토해서 메인에 표시하게 구성해줘야지 무조건 다보스, 백악관 이런 걸로 하드코딩하지 말고"

### 기존 시스템의 문제점

**하드코딩된 키워드**:
```python
MAJOR_EVENT_KEYWORDS = [
    'Davos', 'WEF', 'World Economic Forum',  # 다보스
    'Fed', 'Federal Reserve', 'FOMC', 'Powell',  # Fed
    'Trump', 'Biden', 'White House', 'President',  # 백악관
    ...
]
```

**문제**:
- ❌ 다보스가 없는 날에도 "다보스" 키워드로 검색
- ❌ 실제 최근 이슈(예: 새로운 AI 규제, 반도체 수출 규제)를 놓칠 수 있음
- ❌ 시간이 지나도 키워드가 업데이트되지 않음
- ❌ 유연성 부족

## 해결책: 동적 트렌딩 뉴스 감지 시스템

### 핵심 아이디어

**"최근 24시간 뉴스에서 자주 등장하는 키워드 → 토픽 클러스터링 → 중요도 평가 → 자동 우선순위 결정"**

### 구현 단계

#### 1. 키워드 빈도 분석

```python
# 최근 24시간 뉴스에서 키워드 추출
keywords = []
for article in recent_news:
    keywords.extend(extract_keywords(article.title))
    keywords.extend(extract_keywords(article.summary))

# 빈도 계산
freq = Counter(keywords)
# {'Trump': 15, 'AI': 12, 'Semiconductor': 10, ...}
```

#### 2. 토픽 클러스터링 (LLM 사용)

유사한 키워드를 토픽으로 그룹화:

```python
# 입력
keywords = ['Trump', 'Trump administration', 'President Trump', 'Fed', 'Powell', 'Federal Reserve']

# LLM 클러스터링
topics = [
    {
        'topic': 'Trump Administration Policies',
        'keywords': ['Trump', 'Trump administration', 'President Trump'],
        'frequency': 15
    },
    {
        'topic': 'Federal Reserve Policy',
        'keywords': ['Fed', 'Powell', 'Federal Reserve'],
        'frequency': 12
    }
]
```

#### 3. 시장 영향력 분석

트레이딩 시그널 생성 여부로 시장 영향력 측정:

```python
for topic in topics:
    # 관련 시그널 찾기
    related_signals = [s for s in signals if topic_matches(s, topic)]

    if len(related_signals) >= 3:
        topic['market_impact'] = 'HIGH'
    elif len(related_signals) >= 1:
        topic['market_impact'] = 'MEDIUM'
    else:
        topic['market_impact'] = 'LOW'
```

#### 4. LLM으로 중요도 평가 (0-100점)

```python
# LLM 프롬프트
"""
다음 토픽들의 중요도를 0-100점으로 평가:

1. Trump Administration Policies (빈도: 15, 영향력: HIGH)
2. Federal Reserve Policy (빈도: 12, 영향력: HIGH)
3. K-pop Concert (빈도: 20, 영향력: LOW)

평가 기준:
- 시장 영향력 (40점)
- 글로벌 영향력 (30점)
- 시의성 (20점)
- 빈도 (10점)
"""

# 결과
[
    {'topic': 'Federal Reserve Policy', 'score': 92},
    {'topic': 'Trump Administration Policies', 'score': 85},
    {'topic': 'K-pop Concert', 'score': 25}  # 빈도는 높지만 시장 영향력 낮음
]
```

#### 5. 뉴스에 토픽 매칭

```python
for news in recent_news:
    for topic in trending_topics:
        if any(keyword in news.title.lower() for keyword in topic['keywords']):
            news['topic'] = topic['topic']
            news['topic_score'] = topic['score']
            news['priority'] = int(topic['score'] / 20)  # 0-5점
```

## 구현된 파일

### 1. TrendingNewsDetector

**파일**: [backend/ai/reporters/trending_news_detector.py](../backend/ai/reporters/trending_news_detector.py)

**주요 메서드**:

```python
class TrendingNewsDetector:
    async def detect_trending_topics(lookback_hours=24, top_n=10):
        """최근 트렌딩 토픽 감지"""

    async def _analyze_keyword_frequency(news_articles):
        """키워드 빈도 분석"""

    async def _cluster_keywords_to_topics(keyword_freq):
        """LLM으로 토픽 클러스터링"""

    async def _analyze_market_impact(topics):
        """시장 영향력 분석"""

    async def _score_topics_with_llm(topics):
        """LLM으로 중요도 평가 (0-100점)"""

    async def get_key_news_for_topic(topic):
        """특정 토픽의 주요 뉴스 가져오기"""
```

### 2. EnhancedDailyReporter 통합

**파일**: [backend/ai/reporters/enhanced_daily_reporter.py](../backend/ai/reporters/enhanced_daily_reporter.py)

**변경 사항**:

```python
class EnhancedDailyReporter:
    def __init__(self):
        # Trending News Detector 초기화
        self.trending_detector = TrendingNewsDetector()

    async def generate_enhanced_briefing(date_str):
        # 1. 트렌딩 토픽 감지 (동적)
        trending_topics = await self.trending_detector.detect_trending_topics()

        # 2. 토픽 기반으로 주요 뉴스 수집
        major_news = await self._get_major_global_news(session, trending_topics)

        # 3. 브리핑 생성 시 토픽 정보 포함
        briefing = await self._synthesize_enhanced_report(
            trending_topics=trending_topics,
            major_news=major_news,
            ...
        )
```

**폴백 메커니즘**:
```python
# Trending Detector 실패 시 하드코딩된 키워드 사용
FALLBACK_EVENT_KEYWORDS = [
    'Davos', 'Fed', 'Trump', 'China', ...
]
```

## 사용 예시

### 1. 직접 실행

```python
from backend.ai.reporters.trending_news_detector import TrendingNewsDetector

detector = TrendingNewsDetector()

# 트렌딩 토픽 감지
topics = await detector.detect_trending_topics(lookback_hours=24, top_n=10)

for topic in topics:
    print(f"{topic['topic']} (Score: {topic['score']}/100)")
    print(f"  Frequency: {topic['frequency']}")
    print(f"  Market Impact: {topic['market_impact']}")
    print(f"  Sentiment: {topic['sentiment']}")
```

### 2. 일일 브리핑에서 자동 사용

```bash
# Enhanced Daily Briefing 생성
python backend/ai/reporters/enhanced_daily_reporter.py

# 결과
# ✅ Detected 8 trending topics:
# 1. AI Regulation Debate (95/100)
# 2. Semiconductor Export Controls (88/100)
# 3. Fed Rate Decision Expectations (82/100)
# ...
```

### 3. API 엔드포인트

```bash
GET /api/reports/daily?enhanced=true

# 응답
{
    "date": "2026-01-21",
    "content": "# 📢 AI 일일 투자 브리핑\n\n## 1. 🌍 오늘의 주요 뉴스\n\n### 최근 이슈 (동적 감지)\n\n**최근 24시간 트렌딩 토픽:**\n1. AI Regulation Debate (95/100)\n2. Semiconductor Export Controls (88/100)\n...",
    "enhanced": true
}
```

## 실행 결과 예시

### 시나리오 1: 다보스 포럼 기간

```
📊 Detected 10 trending topics:

1. Davos Forum (Score: 95/100)
   Frequency: 45 mentions
   Market Impact: HIGH
   Sentiment: BULLISH
   Reasoning: Global leaders discussing AI regulation, climate change

2. AI Safety Standards (Score: 88/100)
   Frequency: 32 mentions
   Market Impact: HIGH
   Sentiment: BULLISH

3. China Economic Slowdown (Score: 72/100)
   Frequency: 28 mentions
   Market Impact: HIGH
   Sentiment: BEARISH
```

### 시나리오 2: 다보스 없는 평일

```
📊 Detected 10 trending topics:

1. Fed Rate Decision (Score: 92/100)
   Frequency: 38 mentions
   Market Impact: HIGH
   Sentiment: NEUTRAL

2. Tech Earnings Season (Score: 85/100)
   Frequency: 35 mentions
   Market Impact: HIGH
   Sentiment: BULLISH

3. Semiconductor Shortage (Score: 78/100)
   Frequency: 25 mentions
   Market Impact: MEDIUM
   Sentiment: BEARISH
```

**차이점**: 다보스가 없으면 자동으로 다른 최근 이슈(Fed, 실적 시즌)로 교체됨!

## 개선 전후 비교

### 개선 전 (하드코딩)

```markdown
# 📢 일일 브리핑

## 1. 오늘의 주요 뉴스

- 🔴 다보스 포럼: (관련 뉴스 없음)
- 🔵 Fed: (관련 뉴스 없음)
- 🟡 백악관: (관련 뉴스 1건)
```

**문제**: 다보스가 없는데도 표시됨, 실제 이슈(AI 규제 등) 누락

### 개선 후 (동적 감지)

```markdown
# 📢 일일 브리핑

## 1. 오늘의 주요 뉴스 (동적 감지)

**최근 24시간 트렌딩 토픽:**
1. AI Regulation Debate (95/100)
2. Semiconductor Export Controls (88/100)
3. Fed Rate Decision Expectations (82/100)

### AI Regulation Debate (95/100)
- 🔴 **EU AI Act 2.0 발표**: 미국/중국도 참여 예정
  - 핵심: 고위험 AI 시스템에 대한 강화된 규제
  - 시장 영향: **긍정적** - 규제 명확성으로 투자 확대
  - 수혜주: NVDA, MSFT, GOOGL

### Semiconductor Export Controls (88/100)
- 🔵 **미국, 중국 반도체 수출 규제 강화**
  - ASML EUV 장비 수출 완전 금지
  - 시장 반응: **혼조** - 단기 악재, 장기 국산화 수혜
```

**개선**: 실제 최근 이슈를 자동으로 감지하여 표시!

## 기술 세부사항

### 키워드 추출 알고리즘

```python
def _extract_keywords_from_text(text: str) -> List[str]:
    """
    대문자로 시작하는 단어 (고유명사) 추출

    예:
    "Trump announces new AI regulation" → ['Trump', 'AI']
    "The Federal Reserve raises rates" → ['Federal', 'Reserve']
    """
    words = re.findall(r'\b[A-Z][a-zA-Z]+\b', text)
    return [w for w in words if len(w) >= 2 and not w.isdigit()]
```

### 토픽 클러스터링 프롬프트

```python
prompt = f"""
다음 키워드들을 의미가 유사한 것끼리 그룹화하여 "토픽"으로 만들어주세요:

{top_keywords}

출력 형식 (JSON):
[
    {{
        "topic": "Trump Administration Policies",
        "keywords": ["Trump", "President Trump", "Trump administration"],
        "description": "토픽 설명"
    }},
    ...
]
"""
```

### 중요도 평가 공식

```python
# 빈도 기반 점수 (최대 30점)
freq_score = min(frequency * 2, 30)

# 시장 영향력 점수 (최대 40점)
impact_score = {
    'HIGH': 40,
    'MEDIUM': 20,
    'LOW': 10
}[market_impact]

# 총점
total_score = freq_score + impact_score + llm_adjustment
```

## 성능 최적화

### 1. 캐싱

```python
# 트렌딩 토픽 캐싱 (1시간)
@cached(ttl=3600)
async def detect_trending_topics():
    ...
```

### 2. 배치 처리

```python
# 뉴스 100개 → 키워드 추출 → 한 번에 LLM 호출
keywords = extract_keywords_batch(news_articles[:100])
topics = await llm_cluster_keywords(keywords)
```

### 3. 폴백 메커니즘

```python
try:
    topics = await trending_detector.detect_trending_topics()
except Exception as e:
    logger.error(f"Trending detection failed: {e}")
    # 폴백: 하드코딩된 키워드 사용
    topics = fallback_keywords_detection()
```

## 다음 단계

### 1. 실시간 업데이트

```python
# WebSocket으로 트렌딩 토픽 실시간 갱신
async def stream_trending_topics():
    while True:
        topics = await detector.detect_trending_topics()
        await websocket.send(json.dumps(topics))
        await asyncio.sleep(300)  # 5분마다
```

### 2. 사용자 커스터마이징

```python
# 사용자별 관심 토픽 설정
user_preferences = {
    'focus_keywords': ['AI', 'Semiconductor', 'Fed'],
    'ignore_keywords': ['Sports', 'Entertainment']
}
```

### 3. 토픽 히스토리 추적

```python
# 토픽별 트렌드 변화 추적
topic_history = {
    'AI Regulation': [
        {'date': '2026-01-20', 'score': 75},
        {'date': '2026-01-21', 'score': 95}  # 상승 중!
    ]
}
```

### 4. 멀티 소스 통합

```python
# 트위터, Reddit, 블룸버그 터미널 등 추가
sources = [
    NewsArticleSource(),
    TwitterSource(),
    RedditSource()
]

topics = await detector.detect_from_multiple_sources(sources)
```

## 트러블슈팅

### 1. LLM 클러스터링 실패

**증상**: JSON 파싱 에러

**해결**:
```python
try:
    topics = json.loads(response)
except JSONDecodeError:
    # 폴백: 상위 키워드를 토픽으로 사용
    topics = [{'topic': kw, 'keywords': [kw]} for kw, _ in keyword_freq.most_common(10)]
```

### 2. 트렌딩 토픽이 비어있음

**증상**: `topics = []`

**해결**:
```python
if not topics:
    logger.warning("No trending topics detected, using fallback")
    return await fallback_keywords_detection()
```

### 3. 중요도 평가가 부정확함

**증상**: K-pop 뉴스가 95점

**해결**:
```python
# LLM 프롬프트 개선
"""
평가 기준:
- 시장 영향력 (40점): 주식/채권/외환 시장에 미치는 영향
- 글로벌 영향력 (30점): 전 세계적 경제/정치적 관심도
- 시의성 (20점): 현재 진행 중이거나 곧 발생할 이벤트
- 빈도 (10점): 뉴스 등장 횟수

**중요**: 엔터테인먼트, 스포츠 뉴스는 빈도가 높아도 시장 영향력이 낮으면 낮은 점수를 부여하세요.
"""
```

## 결론

하드코딩된 키워드 대신 **동적 트렌딩 뉴스 감지 시스템**을 구현하여:

**달성 사항**:
- ✅ 최근 이슈를 자동으로 감지
- ✅ 다보스가 없는 날에는 자동으로 다른 이슈로 교체
- ✅ 시장 영향력 기반 우선순위 결정
- ✅ LLM을 통한 객관적 중요도 평가
- ✅ 시간 경과에 따른 자연스러운 토픽 변화
- ✅ 폴백 메커니즘으로 안정성 보장

**다음 단계**:
1. 실시간 WebSocket 스트리밍
2. 사용자 커스터마이징
3. 토픽 히스토리 추적
4. 멀티 소스 통합 (Twitter, Reddit 등)

---

**작성자**: Claude Sonnet 4.5
**검토자**: 사용자 확인 필요
**다음 단계**: 프론트엔드 통합 및 실시간 업데이트

---

📊 **Messages**: 75 | **Est. Tokens**: ~106,000 | **Since**: 대화 시작

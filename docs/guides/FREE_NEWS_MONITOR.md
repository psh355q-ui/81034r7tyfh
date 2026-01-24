# 무료 뉴스 모니터링 가이드 💰

**100% 무료**로 백악관 연설 등 중요 뉴스를 실시간 모니터링하는 방법입니다.

## 왜 무료인가요?

- ❌ **Financial Times**: 유료 구독 필요 ($75/월)
- ❌ **Wall Street Journal**: 유료 구독 필요 ($40/월)
- ❌ **Bloomberg**: 유료 구독 필요 ($35/월)

- ✅ **White House**: 무료, 공식 사이트
- ✅ **Reuters**: 무료, 속보 빠름
- ✅ **AP News**: 무료, 신뢰도 높음
- ✅ **CNBC**: 무료, 금융 뉴스
- ✅ **C-SPAN**: 무료, 의회/백악관 생중계

## 빠른 시작

### 1. 가장 간단한 방법 (배치 파일)

```bash
# 메뉴 방식 (권장)
6_무료뉴스_모니터링.bat

# 백악관만 빠르게 실행
6_백악관_모니터링.bat
```

### 2. Python으로 직접 실행

```bash
# 백악관 공식 사이트만 (가장 신뢰도 높음)
python backend/scripts/monitor_free_news.py whitehouse

# 속보 중심 (Reuters + AP + CNBC)
python backend/scripts/monitor_free_news.py breaking

# 모든 무료 소스
python backend/scripts/monitor_free_news.py all

# RSS 피드만 (가장 가볍고 빠름)
python backend/scripts/monitor_free_news.py rss
```

## 무료 소스 상세 설명

### 1️⃣ 백악관 공식 사이트 (추천!)

**장점**:
- 🏛️ **공식 소스**: 가장 신뢰도 높음
- 🆓 **완전 무료**: 페이월 없음
- ⚡ **빠른 업데이트**: 연설/성명 발표 즉시 게시
- 📝 **전체 텍스트**: 전문 제공

**모니터링 URL**:
- https://www.whitehouse.gov/briefing-room/speeches-remarks/
- https://www.whitehouse.gov/briefing-room/statements-releases/

**간격**: 2분마다

**사용법**:
```bash
python backend/scripts/monitor_free_news.py whitehouse
```

### 2️⃣ 속보 중심 (Reuters + AP + CNBC)

**장점**:
- 📰 **빠른 속보**: 뉴스 발생 즉시 업데이트
- 🌍 **글로벌 커버리지**: 전 세계 뉴스
- 💼 **금융 뉴스**: 시장 영향력 있는 뉴스 우선

**포함 소스**:
- **Reuters**: 국제 통신사, 속보 빠름
- **AP News**: 미국 대표 통신사
- **CNBC**: 금융/비즈니스 뉴스

**간격**: 3분마다 (소스별)

**사용법**:
```bash
python backend/scripts/monitor_free_news.py breaking
```

### 3️⃣ 모든 무료 소스 (종합)

**포함 소스**:
- White House (2분 간격)
- Reuters (3분 간격)
- AP News (3분 간격)
- CNBC (3분 간격)
- C-SPAN (2분 간격) - 의회/백악관 생중계
- Bloomberg (5분 간격) - 무료 기사만

**사용법**:
```bash
python backend/scripts/monitor_free_news.py all
```

### 4️⃣ RSS 피드만 (가장 가볍고 빠름)

**장점**:
- 🚀 **서버 부담 없음**: RSS는 크롤링용으로 제공됨
- ⚡ **빠른 처리**: HTML 파싱 불필요
- 📊 **구조화된 데이터**: 제목, 링크, 요약 제공

**포함 RSS**:
- White House Feed
- Reuters Business News
- AP News Feed
- CNBC Business Feed

**간격**: 2-3분마다

**사용법**:
```bash
python backend/scripts/monitor_free_news.py rss
```

## 실행 로그 예시

### 백악관 모니터링

```
========================================
White House Official Site Monitor
========================================
Monitoring:
  - whitehouse.gov/briefing-room/speeches-remarks/
  - whitehouse.gov/briefing-room/statements-releases/

Interval: 2±0.5 minutes
Started at: 2026-01-21 14:30:00
========================================

Press Ctrl+C to stop

🔍 Fetching [1]: https://www.whitehouse.gov/briefing-room/speeches-remarks/
📝 Initial content captured (hash: 3a7b2c1d...)
✅ Saved: President Biden Delivers Remarks on the Economy...
⏰ Next fetch in 2.2 minutes (at 14:32:12)

🔍 Fetching [2]: https://www.whitehouse.gov/briefing-room/speeches-remarks/
🆕 Content CHANGED!
🔔 NEW CONTENT DETECTED!
========================================
Title: President Trump Announces New Trade Policy
Source: White House Official
URL: https://www.whitehouse.gov/...
Content Length: 3,450 chars
========================================
✅ Saved: President Trump Announces New Trade Policy...
⏰ Next fetch in 1.8 minutes (at 14:34:01)
```

### RSS 피드 모니터링

```
========================================
RSS Feed Monitor (Lightweight)
========================================
RSS Feeds:
  - White House (whitehouse.gov/feed/)
  - Reuters (reuters.com/rssfeed/businessNews)
  - AP News (apnews.com/rss)
  - CNBC (cnbc.com/...rss)

Interval: 2~3 minutes per feed
========================================

📡 RSS Article: Trump administration announces tariffs on Chinese imports
   Link: https://www.reuters.com/world/us/...

📡 RSS Article: Federal Reserve signals potential rate cut
   Link: https://apnews.com/article/...

📡 RSS Article: Stock futures rise as investors await jobs data
   Link: https://www.cnbc.com/2026/01/21/...
```

## 코드 사용 예시

### Python에서 직접 사용

```python
from backend.data.collectors.free_news_monitor import FreeNewsMonitor

# 콜백 함수 정의
def on_new_content(data):
    print(f"새 뉴스: {data['title']}")
    print(f"URL: {data['url']}")

    # 여기서 AI 분석 트리거
    # from backend.ai.intelligence.enhanced_news_pipeline import EnhancedNewsPipeline
    # pipeline = EnhancedNewsPipeline()
    # await pipeline.process_urgent_news(data)

# 모니터 초기화
monitor = FreeNewsMonitor()

# 백악관만 추가
monitor.add_whitehouse_only(callback=on_new_content)

# 또는 속보 소스 추가
monitor.add_breaking_news_sources(callback=on_new_content)

# 모니터링 시작
await monitor.start()
```

### RSS 피드만 사용

```python
from backend.data.collectors.free_news_monitor import RSSFeedMonitor

rss_monitor = RSSFeedMonitor()

# 단일 RSS 피드 모니터링
await rss_monitor.monitor_rss(
    "https://www.whitehouse.gov/feed/",
    interval_minutes=2.0,
    callback=lambda article: print(article['title'])
)
```

### 커스텀 소스 추가

```python
monitor = FreeNewsMonitor()

# 개별 소스 추가
monitor.add_source('whitehouse', callback=on_new_content)
monitor.add_source('reuters', callback=on_new_content)
monitor.add_source('cnbc', callback=on_new_content, custom_interval=5.0)

await monitor.start()
```

## 성능 비교

| 방법 | 메모리 | CPU | 네트워크 | 속도 | 신뢰도 |
|------|--------|-----|----------|------|--------|
| 백악관만 | 30MB | 3% | 10MB/h | 빠름 | ⭐⭐⭐⭐⭐ |
| 속보 중심 | 100MB | 8% | 30MB/h | 빠름 | ⭐⭐⭐⭐ |
| 모든 소스 | 200MB | 15% | 60MB/h | 보통 | ⭐⭐⭐⭐⭐ |
| RSS만 | 20MB | 1% | 5MB/h | 매우 빠름 | ⭐⭐⭐⭐ |

## 유료 vs 무료 비교

### Financial Times (유료)
- ✅ 깊이 있는 분석
- ✅ 전문가 의견
- ❌ $75/월 구독료
- ❌ 페이월

### 백악관 공식 (무료)
- ✅ 100% 무료
- ✅ 공식 발표 전문
- ✅ 페이월 없음
- ⚠️ 분석 없음 (원문만)

### Reuters/AP (무료)
- ✅ 100% 무료
- ✅ 빠른 속보
- ✅ 글로벌 커버리지
- ⚠️ 깊이 있는 분석 제한적

## AI 분석 파이프라인 연동

무료 뉴스도 AI 분석 파이프라인과 연동할 수 있습니다:

```python
def on_new_content(data: dict):
    """새 콘텐츠 발견 시 AI 분석"""
    from backend.ai.intelligence.enhanced_news_pipeline import EnhancedNewsPipeline

    # 뉴스 분석
    pipeline = EnhancedNewsPipeline()
    await pipeline.process_urgent_news(data)

    # War Room MVP로 트레이딩 결정
    from backend.ai.mvp.war_room_mvp import WarRoomMVP
    war_room = WarRoomMVP()
    decision = await war_room.make_decision(
        news_context=data['content']
    )

    # 결정에 따라 주문 실행
    if decision['action'] in ['BUY', 'SELL']:
        from backend.ai.order_execution.shadow_order_executor import ShadowOrderExecutor
        executor = ShadowOrderExecutor()
        await executor.execute(decision)
```

## 트러블슈팅

### RSS 피드가 동작하지 않음

**원인**: `feedparser` 미설치

**해결**:
```bash
pip install feedparser
```

### 콘텐츠가 비어있음

**원인**: 사이트 구조 변경

**해결**: `stealth_web_crawler.py`의 selector 수정
```python
# 백악관 사이트 전용 selector
article = soup.find('div', class_='body-content')
```

### 중복 저장됨

**정상 동작**: URL 기반 중복 제거가 작동하지 않은 경우
- 콘텐츠 해시가 다르면 업데이트로 간주됨

## 추천 설정

### 초보자
```bash
# 백악관만 모니터링 (가장 단순)
6_백악관_모니터링.bat
```

### 중급자
```bash
# 속보 중심 (빠른 뉴스)
python backend/scripts/monitor_free_news.py breaking
```

### 고급자
```bash
# RSS + AI 분석 파이프라인
python backend/scripts/monitor_free_news.py rss
# + AI 분석 연동 코드 추가
```

### 서버 자동 실행
```bash
# Windows 작업 스케줄러에 등록
# 또는 backend/automation/scheduler.py에 추가
```

## FAQ

### Q: 백악관 유튜브 라이브도 무료인가요?

A: 네, YouTube는 무료입니다. `yt-dlp`로 라이브 스트림 모니터링 가능:

```python
import yt_dlp

ydl_opts = {'format': 'best', 'quiet': True}
with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    info = ydl.extract_info(youtube_url, download=False)
    is_live = info.get('is_live', False)
```

### Q: FT 기사를 무료로 볼 수 있나요?

A: FT는 유료 구독 필요합니다. 대신 다음 무료 소스 추천:
- Reuters (비슷한 품질, 무료)
- AP News (속보 빠름, 무료)
- Bloomberg 무료 기사 (일부만)

### Q: RSS가 웹 크롤링보다 좋나요?

A: RSS의 장단점:
- ✅ 서버 부담 없음 (크롤링용으로 제공됨)
- ✅ 빠른 처리
- ✅ 구조화된 데이터
- ❌ 전체 콘텐츠 제공 안 할 수도 있음 (요약만)
- ❌ 업데이트 주기가 느릴 수 있음

**추천**: RSS로 빠르게 감지 → 웹 크롤링으로 전체 콘텐츠 가져오기

### Q: 크롤링이 합법인가요?

A: 일반적으로:
- ✅ 백악관 공식 사이트: 공공 정보, 합법
- ✅ RSS 피드: 크롤링용으로 제공됨, 합법
- ⚠️ 뉴스 사이트: 이용 약관 확인 필요, robots.txt 준수

**권장**: RSS 피드 우선 사용

## 다음 단계

### 1. YouTube 라이브 스트림 추가
```python
# backend/data/collectors/youtube_monitor.py
```

### 2. Discord/Telegram 알림
```python
# backend/services/notification_service.py
```

### 3. 프론트엔드 통합
```typescript
// frontend/src/pages/NewsMonitor.tsx
```

## 관련 문서

- [Stealth Web Crawler](./FT_STEALTH_MONITOR.md) - 유료 사이트용
- [Repository Pattern](../../backend/database/repository.py) - DB 저장
- [Enhanced News Pipeline](../../backend/ai/intelligence/enhanced_news_pipeline.py) - AI 분석

---

**작성일**: 2026-01-21
**버전**: 1.0.0
**라이선스**: 개인 투자 목적으로만 사용

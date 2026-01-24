# FT Stealth Monitor - 사용 가이드

백악관 연설 등 중요 뉴스를 실시간으로 모니터링하는 스텔스 크롤러입니다.

## 주요 기능

### 🕵️ 스텔스 모드
- **User-Agent 로테이션**: 5가지 실제 브라우저 User-Agent 랜덤 사용
- **랜덤 딜레이**: 정확히 3분이 아닌 2.5~3.5분 사이 랜덤 간격
- **브라우저 헤더 스푸핑**: Accept, Referer, DNT 등 실제 브라우저 헤더 모방
- **콘텐츠 변경 감지**: SHA-256 해시로 콘텐츠 변경 감지

### 📰 자동 저장
- DB에 자동 저장 (중복 제거)
- 콘텐츠 변경 시에만 업데이트
- 메타 태그 우선 추출 (Open Graph, description)

### 🔔 실시간 알림
- 콘텐츠 변경 시 콜백 함수 호출
- AI 분석 파이프라인 트리거 가능

## 빠른 시작

### 1. 배치 파일로 실행 (권장)

```bash
# 포그라운드 실행 (콘솔 창에서)
6_FT_모니터링_시작.bat

# 백그라운드 실행
6_FT_모니터링_백그라운드.bat
```

### 2. Python으로 직접 실행

```bash
# 가상환경 활성화
venv\Scripts\activate

# 단일 URL 모니터링
python backend/scripts/monitor_ft.py

# 여러 URL 동시 모니터링
python backend/scripts/monitor_ft.py multi
```

### 3. 중지 방법

- **포그라운드**: `Ctrl+C`
- **백그라운드**: 작업 관리자에서 `python.exe` 프로세스 종료

## 사용 예시

### 단일 URL 모니터링

```python
from backend.data.collectors.stealth_web_crawler import StealthWebCrawler

# 콜백 함수 정의 (새 콘텐츠 발견 시)
def on_new_content(data):
    print(f"새 콘텐츠 발견: {data['title']}")
    # 여기서 AI 분석 트리거

# 크롤러 초기화
crawler = StealthWebCrawler(
    url="https://www.ft.com/content/1369a45e-e39b-4aaa-a347-b1800da7fd31",
    interval_minutes=3.0,      # 3분 간격
    variance_minutes=0.5,      # ±30초 랜덤
    callback=on_new_content
)

# 모니터링 시작
await crawler.start_monitoring()
```

### 여러 URL 동시 모니터링

```python
from backend.data.collectors.stealth_web_crawler import MultiSiteMonitor

monitor = MultiSiteMonitor()

# 사이트 추가
monitor.add_site(
    url="https://www.ft.com/content/...",
    interval_minutes=3.0,
    callback=on_new_content
)

monitor.add_site(
    url="https://www.reuters.com/...",
    interval_minutes=5.0,
    callback=on_new_content
)

# 모든 사이트 모니터링 시작
await monitor.start_all()
```

## 설정 옵션

### StealthWebCrawler 파라미터

| 파라미터 | 기본값 | 설명 |
|---------|--------|------|
| `url` | 필수 | 모니터링할 URL |
| `interval_minutes` | 3.0 | 기본 크롤링 간격 (분) |
| `variance_minutes` | 0.5 | 랜덤 편차 (±값, 분) |
| `proxy` | None | 프록시 서버 (예: "http://proxy:8080") |
| `callback` | None | 새 콘텐츠 발견 시 호출할 함수 |

### User-Agent 목록

시스템이 사용하는 5가지 실제 브라우저 User-Agent:

1. Chrome on Windows
2. Chrome on Mac
3. Firefox on Windows
4. Safari on Mac
5. Edge on Windows

## 로그 확인

### 실시간 로그 보기

```bash
# Windows
type logs\ft_monitor.log

# 실시간 tail (PowerShell)
Get-Content logs\ft_monitor.log -Wait
```

### 로그 레벨

- `INFO`: 크롤링 실행, 콘텐츠 변경 감지
- `DEBUG`: 콘텐츠 변경 없음 (해시 동일)
- `WARNING`: HTTP 에러, DB 저장 실패
- `ERROR`: 크롤링 실패, 예외 발생

## 트러블슈팅

### 1. HTTP 403 Forbidden

프리미엄 사이트가 차단한 경우:

```python
# 프록시 사용
crawler = StealthWebCrawler(
    url="...",
    proxy="http://proxy.example.com:8080"
)
```

### 2. Timeout 에러

네트워크가 느린 경우, 소스 코드에서 timeout 값 증가:

```python
# stealth_web_crawler.py 에서
timeout = aiohttp.ClientTimeout(total=60)  # 30 → 60초
```

### 3. 콘텐츠 추출 실패

사이트 구조가 다른 경우, `_fetch_content()` 메서드에서 selector 수정:

```python
# 특정 클래스명으로 추출
article = soup.find('div', class_='article-body')
```

### 4. DB 저장 실패

중복 콘텐츠인 경우 정상 (경고만 표시):

```
WARNING: Failed to save article (duplicate?): ...
```

## 고급 설정

### AI 분석 파이프라인 연동

`backend/scripts/monitor_ft.py`의 `on_new_content()` 함수에서:

```python
def on_new_content(data: dict):
    # AI 분석 트리거
    from backend.ai.intelligence.enhanced_news_pipeline import EnhancedNewsPipeline

    pipeline = EnhancedNewsPipeline()
    await pipeline.process_urgent_news(data)

    # 트레이딩 시그널 생성
    from backend.ai.mvp.war_room_mvp import WarRoomMVP

    war_room = WarRoomMVP()
    decision = await war_room.make_decision(
        news_context=data['content']
    )
```

### 스케줄러 통합

`backend/automation/scheduler.py`에 추가:

```python
def setup_schedules(self):
    # 기존 스케줄...

    # FT 모니터링 시작 (시스템 시작 시)
    schedule.every().day.at("00:00").do(self.start_ft_monitoring)
```

### 프록시 사용

환경변수로 프록시 설정:

```bash
# .env에 추가
FT_MONITOR_PROXY=http://proxy.example.com:8080
```

```python
# monitor_ft.py에서 읽기
proxy = os.getenv('FT_MONITOR_PROXY')
crawler = StealthWebCrawler(url=url, proxy=proxy)
```

## 보안 및 주의사항

### ⚠️ 법적 고려사항

- **이용 약관 확인**: 크롤링 전 사이트 이용 약관(Terms of Service) 확인
- **robots.txt 확인**: 크롤링이 허용된 경로인지 확인
- **Rate Limiting**: 과도한 요청으로 서버에 부담 주지 않기
- **저작권**: 크롤링한 콘텐츠의 저작권 준수

### 🔒 개인정보 보호

- User-Agent 로테이션으로 개인 식별 방지
- 쿠키 저장 안 함 (세션마다 새로 시작)
- 프록시 사용 시 익명성 보장

### 📊 윤리적 크롤링

- **최소 간격**: 3분 이상 (서버 부담 최소화)
- **헤더 포함**: 실제 브라우저처럼 행동
- **에러 처리**: 403/429 응답 시 자동 중지
- **캐싱**: 동일 콘텐츠는 중복 저장하지 않음

## 성능 최적화

### 메모리 사용량

- **단일 URL**: ~50MB
- **10개 URL 동시**: ~200MB
- **100개 URL 동시**: ~1GB

### CPU 사용량

- 크롤링 중: ~5-10%
- 대기 중: ~0%

### 네트워크 사용량

- 평균 페이지 크기: 200KB~1MB
- 시간당 트래픽: ~20MB (3분 간격 기준)

## FAQ

### Q: 백악관 유튜브 영상도 크롤링 가능한가요?

A: 네, `yt-dlp`가 이미 설치되어 있습니다. 영상 크롤러는 별도로 구현 필요:

```python
# backend/data/collectors/youtube_monitor.py 생성 필요
import yt_dlp

# 라이브 스트림 모니터링
ydl_opts = {'format': 'best'}
with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    info = ydl.extract_info(youtube_url, download=False)
```

### Q: 다른 뉴스 사이트도 추가 가능한가요?

A: 네, `MultiSiteMonitor`로 여러 사이트 동시 모니터링 가능합니다:

```python
monitor.add_site("https://www.reuters.com/...")
monitor.add_site("https://www.bloomberg.com/...")
monitor.add_site("https://www.wsj.com/...")
```

### Q: 크롤링 간격을 더 짧게 할 수 있나요?

A: 가능하지만 비권장. 1분 이하는 서버에 부담을 주고 차단될 위험이 높습니다.

### Q: VPN이 필요한가요?

A: 일반적으로 불필요하지만, 지역 제한 콘텐츠는 VPN/프록시가 필요할 수 있습니다.

## 다음 단계

### 1. AI 분석 연동

[backend/api/intelligence_router.py](../backend/api/intelligence_router.py)와 연동하여 실시간 분석

### 2. 알림 시스템

Discord/Telegram 봇으로 중요 뉴스 알림

### 3. 트레이딩 자동화

War Room MVP와 연동하여 자동 트레이딩 결정

### 4. 대시보드 통합

프론트엔드에 실시간 크롤링 상태 표시

## 참고 자료

- [aiohttp 문서](https://docs.aiohttp.org/)
- [BeautifulSoup 문서](https://www.crummy.com/software/BeautifulSoup/)
- [Repository Pattern](../../backend/database/repository.py)
- [뉴스 크롤러](../../backend/news/news_crawler.py)

---

**작성일**: 2026-01-21
**버전**: 1.0.0
**문의**: AI Trading System Team

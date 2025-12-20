# 🔍 News API Troubleshooting Guide

**작성일**: 2025-12-03
**문제**: `/news/realtime/*` 엔드포인트 404 에러

---

## ✅ 확인된 사항

### 1. 라우터 등록 확인
```python
# backend/main.py:236
app.include_router(news_router)
```
✅ 등록됨

### 2. 라우터 Import 확인
```python
# backend/main.py:63
from backend.api.news_router import router as news_router
```
✅ Import됨

### 3. 라우터 Prefix 확인
```python
# backend/api/news_router.py:41
router = APIRouter(prefix="/news", tags=["News Aggregation"])
```
✅ `/news` prefix 설정됨

### 4. 엔드포인트 정의 확인
```python
# backend/api/news_router.py
@router.get("/realtime/latest")      # Line 643
@router.get("/realtime/raw")          # Line 693
@router.get("/realtime/ticker/{ticker}")  # Line 724
@router.get("/realtime/health")       # Line 755
```
✅ 모두 정의됨

---

## 🐛 문제 원인

**가능성 1**: 서버가 `--reload` 모드에서 파일 변경을 감지하지 못함
- `news_router.py`에 엔드포인트를 추가한 후 서버 재시작 안함

**가능성 2**: Import 오류
- `EnhancedNewsCrawler` import가 실패했을 가능성
- `NewsContextFilter` import가 실패했을 가능성

---

## 🔧 해결 방법

### 1️⃣ 서버 완전 재시작 (가장 확실)

**PowerShell에서**:
```powershell
# 1. 실행 중인 모든 Python 프로세스 종료
taskkill /IM python.exe /F

# 2. 프로젝트 루트로 이동
cd d:\code\ai-trading-system

# 3. 백엔드 서버 재시작
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 2️⃣ Import 오류 확인

서버 시작 시 로그에서 다음 메시지 확인:
```
INFO - News router registered
```

만약 이 메시지 전에 오류가 있다면:
```python
# Import 오류 가능성
ModuleNotFoundError: No module named 'backend.news.enhanced_news_crawler'
```

### 3️⃣ 수동 테스트

Python 콘솔에서:
```python
# backend 디렉토리에서
from backend.news.enhanced_news_crawler import EnhancedNewsCrawler
from backend.news.news_context_filter import NewsContextFilter

crawler = EnhancedNewsCrawler()
print("✅ Import 성공!")
```

---

## 🧪 테스트 절차

### Step 1: 서버 재시작 후 Health Check
```
http://localhost:8000/news/realtime/health
```

**예상 응답**:
```json
{
  "status": "operational",
  "enhanced_crawler": "available",
  "context_filter": "enabled",
  "newsapi_enabled": true,
  "database": "connected"
}
```

### Step 2: Swagger UI 확인
```
http://localhost:8000/docs
```

**확인 사항**:
- "News Aggregation" 섹션에 다음 엔드포인트들이 보이는가?
  - `GET /news/realtime/latest`
  - `GET /news/realtime/raw`
  - `GET /news/realtime/ticker/{ticker}`
  - `GET /news/realtime/health`

### Step 3: 실제 뉴스 크롤링
```
http://localhost:8000/news/realtime/latest?hours=24&max_articles=50
```

**예상 응답 (NewsAPI 키 있을 때)**:
```json
{
  "success": true,
  "count": 23,
  "filter_applied": true,
  "filter_threshold": 0.7,
  "articles": [
    {
      "title": "...",
      "tickers": ["NVDA"],
      "market_segment": "training",
      "risk_score": 0.85
    }
  ]
}
```

**예상 응답 (Mock 데이터)**:
```json
{
  "success": true,
  "count": 2,
  "filter_applied": false,
  "articles": [
    {
      "title": "NVIDIA announces Blackwell B200...",
      "tickers": ["NVDA"]
    }
  ]
}
```

---

## 🚨 여전히 404가 나온다면?

### Debug Mode 실행

**news_router.py** 최상단에 추가:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

logger.info("🚀 News Router Loading...")

@router.get("/realtime/test")
async def test_endpoint():
    """Simple test endpoint"""
    return {"status": "News router is working!"}
```

그리고 테스트:
```
http://localhost:8000/news/realtime/test
```

이것도 404면 라우터 자체가 등록 안된 것입니다.

---

## 📋 체크리스트

서버 재시작 전:
- [ ] 모든 Python 프로세스 종료 (`taskkill /IM python.exe /F`)
- [ ] `news_router.py` 파일 저장 확인
- [ ] `enhanced_news_crawler.py` 파일 존재 확인
- [ ] `news_context_filter.py` 파일 존재 확인

서버 시작 후:
- [ ] "News router registered" 로그 확인
- [ ] `http://localhost:8000/docs`에서 엔드포인트 목록 확인
- [ ] `/news/realtime/health` 접속 테스트
- [ ] 오류 메시지가 있다면 전체 복사

---

## 💡 빠른 진단

**터미널에서 실행**:
```powershell
# 1. News router 파일 존재 확인
ls D:\code\ai-trading-system\backend\api\news_router.py

# 2. Enhanced Crawler 파일 존재 확인
ls D:\code\ai-trading-system\backend\news\enhanced_news_crawler.py

# 3. Context Filter 파일 존재 확인
ls D:\code\ai-trading-system\backend\news\news_context_filter.py

# 4. Import 테스트
cd D:\code\ai-trading-system
python -c "from backend.news.enhanced_news_crawler import EnhancedNewsCrawler; print('✅ Import OK')"
```

모두 성공하면 → 서버 재시작만 하면 됩니다!

---

## 🎯 최종 해결책

**가장 확실한 방법**:
```powershell
# 1. 모든 Python 종료
taskkill /IM python.exe /F

# 2. 새 PowerShell 창 열기
# 3. 다음 명령 실행
cd D:\code\ai-trading-system\backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 4. 브라우저에서 테스트
# http://localhost:8000/docs
```

---

**작성일**: 2025-12-03
**상태**: 진단 중 🔍

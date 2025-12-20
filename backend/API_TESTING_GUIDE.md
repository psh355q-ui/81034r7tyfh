# 백엔드 서버 시작 가이드

## 문제 해결: ModuleNotFoundError

### 원인
`backend` 디렉토리 안에서 `python main.py`를 실행하면 absolute import (`from backend.monitoring...`)가 실패합니다.

### ✅ 해결 방법

#### 방법 1: 프로젝트 루트에서 실행 (권장)
```powershell
cd d:\code\ai-trading-system
python -m backend.main
```

#### 방법 2: uvicorn 직접 사용
```powershell
cd d:\code\ai-trading-system\backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

---

## 뉴스 API 테스트 URL

### Enhanced News Crawler (4-way Filter)

#### 1. 실시간 뉴스 (필터링)
```
http://localhost:8000/news/realtime/latest?hours=24&max_articles=50&filter_threshold=0.7
```
**설명**: 4-way 필터(위험 클러스터, 섹터 벡터, 폭락 패턴, 감성 시계열)를 적용한 고품질 뉴스

**파라미터**:
- `hours`: 최근 몇 시간 (1-168)
- `max_articles`: 최대 기사 수 (1-200)
- `filter_threshold`: 필터 임계값 (0.0-1.0, 기본 0.7)

#### 2. 원본 뉴스 (필터 없음)
```
http://localhost:8000/news/realtime/raw?hours=24&max_articles=50
```
**설명**: 4-way 필터를 적용하지 않은 모든 뉴스

#### 3. 티커별 뉴스
```
http://localhost:8000/news/realtime/ticker/NVDA?days=1
http://localhost:8000/news/realtime/ticker/GOOGL?days=7
```
**설명**: 특정 티커의 캐시된 뉴스 조회

**지원 티커**:
- NVDA, GOOGL, AMD, INTC, TSM, AVGO, MSFT, AMZN, META, ORCL

#### 4. Health Check
```
http://localhost:8000/news/realtime/health
```
**설명**: Enhanced News Crawler 상태 확인

---

## API 문서

### Swagger UI
```
http://localhost:8000/docs
```

### ReDoc
```
http://localhost:8000/redoc
```

---

## 응답 예시

### `/news/realtime/latest` 응답
```json
{
  "success": true,
  "count": 23,
  "filter_applied": true,
  "filter_threshold": 0.7,
  "articles": [
    {
      "id": 1,
      "title": "NVIDIA announces new AI chip...",
      "tickers": ["NVDA"],
      "keywords": ["AI chip", "GPU", "training"],
      "tags": ["training"],
      "market_segment": "training",
      "risk_score": 0.85,
      "published_at": "2025-12-03T12:00:00Z",
      "source": "TechCrunch"
    },
    ...
  ]
}
```

---

## 프론트엔드 연동

### React 예시
```typescript
// fetch news with filter
async function fetchNews() {
  const response = await fetch(
    'http://localhost:8000/news/realtime/latest?hours=24&filter_threshold=0.7'
  );
  const data = await response.json();
  
  console.log(`Found ${data.count} articles`);
  console.log(`Filter applied: ${data.filter_applied}`);
  
  return data.articles;
}

// fetch ticker news
async function fetchTickerNews(ticker: string) {
  const response = await fetch(
    `http://localhost:8000/news/realtime/ticker/${ticker}?days=1`
  );
  const data = await response.json();
  
  return data.articles;
}
```

---

## 주의사항

1. **NEWS_API_KEY 필수**: `.env` 파일에 `NEWS_API_KEY` 설정 필요
2. **Rate Limiting**: NewsAPI 무료 플랜은 100 requests/day
3. **4-way Filter**: Mock 데이터로 동작 (실제 학습 모델은 별도 구축 필요)
4. **캐시 DB**: SQLite `enhanced_news_cache.db` 자동 생성

---

## 트러블슈팅

### 문제: "Enhanced News Crawler not available"
**해결**: 
```powershell
pip install newsapi-python python-dotenv
```

### 문제: "NEWS_API_KEY not set"
**해결**: `.env` 파일에 추가
```
NEWS_API_KEY=your_api_key_here
```

### 문제: 뉴스 0개 반환
**원인**: NewsAPI 무료 플랜 제한 또는 키워드 매칭 없음
**해결**: 
1. Mock 데이터로 테스트 (API 키 없이)
2. 시간 범위 늘리기 (`hours=168`)

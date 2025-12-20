# News Intelligence API Reference
**버전**: 1.0  
**Base URL**: `http://localhost:8001/api/news`

---

## 📋 Endpoints

### 1. News Analysis

#### POST /analyze
AI 분석 실행

**Query Parameters**:
- `max_count` (int, default=10): 분석할 기사 수

**Response**:
```json
{
  "analyzed": 9,
  "skipped": 0,
  "errors": 1,
  "remaining_requests": 1490,
  "details": [
    {
      "article_id": 1,
      "title": "Article Title",
      "status": "success",
      "sentiment": "positive",
      "sentiment_score": 0.7
    }
  ]
}
```

**Example**:
```bash
curl -X POST http://localhost:8001/api/news/analyze?max_count=10
```

---

### 2. Processing Pipeline

#### POST /process/{article_id}
단일 기사 처리 (분석 + 태깅 + 임베딩)

**Path Parameters**:
- `article_id` (int): 기사 ID

**Response**:
```json
{
  "article_id": 1,
  "analyzed": true,
  "tagged": true,
  "embedded": true,
  "rag_indexed": true,
  "tag_count": 8,
  "embedding_dimensions": 384,
  "processing_time_ms": 1234
}
```

**Example**:
```bash
curl -X POST http://localhost:8001/api/news/process/1
```

---

#### POST /batch-process
배치 처리

**Query Parameters**:
- `max_articles` (int, default=10): 처리할 기사 수
- `force_reprocess` (bool, default=false): 이미 처리된 기사 재처리

**Response**:
```json
{
  "processed": 45,
  "failed": 5,
  "skipped": 0,
  "total_tags": 360,
  "total_embeddings": 45,
  "processing_time_seconds": 135.5,
  "details": [...]
}
```

**Example**:
```bash
curl -X POST "http://localhost:8001/api/news/batch-process?max_articles=50"
```

---

### 3. Search

#### GET /search/ticker/{ticker}
티커 기반 검색

**Path Parameters**:
- `ticker` (str): 주식 티커 (예: NVDA, AAPL)

**Query Parameters**:
- `limit` (int, default=20): 결과 수
- `min_relevance` (float, default=0.5): 최소 관련도 (0.0-1.0)

**Response**:
```json
{
  "ticker": "NVDA",
  "total": 25,
  "articles": [
    {
      "id": 123,
      "title": "NVIDIA Announces New AI Chip",
      "sentiment": "positive",
      "sentiment_score": 0.8,
      "relevance_score": 0.95,
      "published_at": "2025-12-19T10:00:00Z",
      "source": "TechCrunch"
    }
  ]
}
```

**Example**:
```bash
curl http://localhost:8001/api/news/search/ticker/NVDA?limit=10
```

---

#### GET /search/tag/{tag}
태그 기반 검색

**Path Parameters**:
- `tag` (str): 태그 이름 (예: bullish, high_impact)

**Query Parameters**:
- `limit` (int, default=20): 결과 수

**Response**:
```json
{
  "tag": "bullish",
  "total": 15,
  "articles": [
    {
      "id": 45,
      "title": "Market Rallies on Strong Earnings",
      "sentiment": "positive",
      "tags": ["bullish", "high_impact", "earnings"],
      "published_at": "2025-12-19T14:30:00Z"
    }
  ]
}
```

**Example**:
```bash
curl http://localhost:8001/api/news/search/tag/bullish
```

---

### 4. Article Details

#### GET /articles/{article_id}/tags
기사 태그 조회

**Path Parameters**:
- `article_id` (int): 기사 ID

**Response**:
```json
{
  "article_id": 1,
  "tags": [
    {
      "tag_type": "sentiment",
      "tag_value": "positive",
      "confidence": 0.85
    },
    {
      "tag_type": "impact",
      "tag_value": "high_impact",
      "confidence": 0.75
    },
    {
      "tag_type": "ticker",
      "tag_value": "NVDA",
      "confidence": 0.95
    }
  ]
}
```

---

#### GET /articles/{article_id}/similar
유사 기사 검색

**Path Parameters**:
- `article_id` (int): 기사 ID

**Query Parameters**:
- `top_k` (int, default=5): 반환할 유사 기사 수

**Response**:
```json
{
  "article_id": 1,
  "similar_articles": [
    {
      "id": 45,
      "title": "Similar Article Title",
      "similarity": 0.92,
      "sentiment": "positive",
      "published_at": "2025-12-18T15:30:00Z"
    },
    {
      "id": 67,
      "title": "Another Similar Article",
      "similarity": 0.88,
      "sentiment": "neutral",
      "published_at": "2025-12-17T09:00:00Z"
    }
  ]
}
```

**Example**:
```bash
curl http://localhost:8001/api/news/articles/1/similar?top_k=5
```

---

#### GET /articles/{article_id}/status
처리 상태 조회

**Path Parameters**:
- `article_id` (int): 기사 ID

**Response**:
```json
{
  "article_id": 1,
  "has_analysis": true,
  "has_tags": true,
  "has_embedding": true,
  "rag_indexed": true,
  "tag_count": 8,
  "last_processed": "2025-12-19T12:00:00Z",
  "analysis_details": {
    "sentiment": "positive",
    "sentiment_score": 0.7,
    "urgency": "medium",
    "actionable": true
  }
}
```

---

## 🔑 Authentication

현재 버전: **인증 불필요**

향후 버전에서 JWT 토큰 기반 인증 추가 예정.

---

## ⚠️ Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid article ID"
}
```

### 404 Not Found
```json
{
  "detail": "Article not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Analysis failed (no content or parse error)"
}
```

---

## 📊 Rate Limits

### Gemini API
- **무료 티어**: 1,500 requests/day
- **재설정**: UTC 기준 매일 자정
- **초과 시**: 429 Too Many Requests

### 권장 사용량
- 배치 처리: 50개씩
- API 호출 간격: 1초
- 일일 처리량: ~500 articles

---

## 🔗 Related APIs

### RSS Crawling
```bash
POST /api/news/crawl/stream?extract_content=true
```

### Statistics
```bash
GET /api/news/stats
```

### Articles List
```bash
GET /api/news/articles?limit=50&hours=24
```

---

## 📝 Response Models

### ArticleAnalysis
```typescript
{
  article_id: number;
  sentiment: "positive" | "negative" | "neutral" | "mixed";
  sentiment_score: number;  // -1.0 to 1.0
  urgency: "low" | "medium" | "high" | "critical";
  market_impact_short: "bullish" | "bearish" | "neutral" | "uncertain";
  market_impact_long: "bullish" | "bearish" | "neutral" | "uncertain";
  impact_magnitude: number;  // 0.0 to 1.0
  actionable: boolean;
  risk_category: "legal" | "regulatory" | "operational" | "financial" | "strategic" | "none";
}
```

### ArticleTag
```typescript
{
  tag_type: "sentiment" | "impact" | "urgency" | "ticker" | "keyword" | "actionable";
  tag_value: string;
  confidence: number;  // 0.0 to 1.0
}
```

### ArticleEmbedding
```typescript
{
  dimensions: 384;
  model: "all-MiniLM-L6-v2";
  vector: number[];  // 384-dimensional array
}
```

---

## 🧪 Testing

### Python Example
```python
import requests

# Analyze articles
response = requests.post(
    "http://localhost:8001/api/news/analyze?max_count=10"
)
print(response.json())

# Search by ticker
response = requests.get(
    "http://localhost:8001/api/news/search/ticker/NVDA"
)
print(response.json())

# Find similar articles
response = requests.get(
    "http://localhost:8001/api/news/articles/1/similar?top_k=5"
)
print(response.json())
```

### JavaScript Example
```javascript
// Analyze articles
const response = await fetch(
  'http://localhost:8001/api/news/analyze?max_count=10',
  { method: 'POST' }
);
const data = await response.json();
console.log(data);

// Search by ticker
const articles = await fetch(
  'http://localhost:8001/api/news/search/ticker/NVDA'
);
const tickerNews = await articles.json();
console.log(tickerNews);
```

---

## 📚 Additional Resources

- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc
- **Source Code**: `backend/api/news_processing_router.py`

# News Intelligence Feature Guide
**버전**: 1.0  
**최종 업데이트**: 2025-12-20

---

## 📋 개요

AI 트레이딩 시스템의 뉴스 인텔리전스 기능은 **Gemini AI**를 활용하여 뉴스 기사를 자동으로 분석하고, 태그를 생성하며, 벡터 임베딩을 통해 유사 기사를 찾는 완전한 파이프라인을 제공합니다.

---

## 🎯 핵심 기능

### 1. **Gemini 실시간 검색** 🆕 (2024-12-20)
티커별 실시간 뉴스 검색:
- **모델**: gemini-2.0-flash (무료)
- **속도**: 2-3초 응답
- **구조화**: JSON 자동 파싱
- **메타데이터**: 감정, 긴급도, 영향도, 관련 티커
- **할루시네이션 방지**: Temperature 0.2, URL 검증
- **비용**: 현재 무료 (추후 ~$0.04/검색)
- **엔드포인트**: `/api/news/gemini/search/ticker/{ticker}`

### 2. AI 뉴스 분석
Gemini 2.5 Flash를 사용한 심층 분석:
- 감정 분석 (긍정/부정/중립/혼합)
- 감정 점수 (-1.0 ~ 1.0)
- 긴급도 (낮음/중간/높음/위급)
- 시장 영향 (단기/장기)
- 행동 가능 여부
- 리스크 카테고리

### 3. 자동 태깅
AI 분석 결과를 기반으로 자동 태그 생성:
- Sentiment Tags: positive, negative, neutral
- Impact Tags: high_impact, medium_impact, low_impact
- Urgency Tags: critical, high, medium, low
- Ticker Tags: AAPL, NVDA, TSLA, etc.
- Keyword Tags: AI, tech, earnings, etc.
- Actionable Tags: buy, sell, hold, watch

### 3. 벡터 임베딩
Sentence-Transformers로 384차원 벡터 생성:
- 모델: all-MiniLM-L6-v2
- 유사도 검색 (코사인 유사도)
- Top-K 유사 기사 추천

### 4. 검색 기능
- **티커 검색**: 특정 주식 관련 뉴스
- **태그 검색**: 태그별 필터링
- **유사 기사**: 임베딩 기반 추천
- **Gemini 실시간 검색**: 티커별 최신 뉴스 (2-3초) 🆕

---

## 🚀 사용법

### 0. **Gemini 실시간 검색** 🆕

#### Frontend (UI)
```typescript
// NewsAggregation.tsx에서 티커 검색
1. 티커 검색 바에 "NVDA" 입력
2. "🔍 실시간 검색 (Gemini)" 버튼 클릭
3. 2-3초 대기
4. Alert로 결과 확인 (현재)
```

#### Backend API
```bash
# 티커별 검색
GET /api/news/gemini/search/ticker/NVDA?max_articles=5

# 응답
{
  "ticker": "NVDA",
  "query": "latest news about NVDA stock",
  "articles": [
    {
      "title": "Nvidia Q4 earnings exceed expectations",
      "url": "https://...",
      "source": "Reuters",
      "published_date": "2024-12-20T10:00:00Z",
      "summary": "Nvidia's Q4 revenue...",
      "sentiment": "positive",
      "urgency": "high",
      "market_impact": "bullish",
      "tickers": ["NVDA"],
      "actionable": true,
      "fetched_at": "2024-12-20T19:34:00Z",
      "model_version": "gemini-2.0-flash"
    }
  ],
  "source_type": "gemini_llm",
  "cost_info": {
    "current_cost": "$0.00 (무료)",
    "future_cost": "~$0.04 per search"
  }
}
```

### 1. 뉴스 분석

#### Frontend
http://localhost:3002/news 페이지에서:
1. "RSS 크롤링" 버튼 클릭
2. "AI 분석 (10개)" 버튼 클릭
3. 분석 결과 자동 표시

#### API
```bash
# 10개 기사 분석
POST http://localhost:8001/api/news/analyze?max_count=10

# 응답
{
  "analyzed": 9,
  "skipped": 0,
  "errors": 1,
  "remaining_requests": 1490
}
```

### 2. 처리 파이프라인

#### 단일 기사 처리
```bash
POST /api/news/process/1

# 응답
{
  "article_id": 1,
  "analyzed": true,
  "tagged": true,
  "embedded": true,
  "rag_indexed": true,
  "tag_count": 8,
  "processing_time_ms": 1234
}
```

#### 배치 처리
```bash
POST /api/news/batch-process?max_articles=50

# 응답
{
  "processed": 45,
  "failed": 5,
  "skipped": 0,
  "total_tags": 360,
  "total_embeddings": 45
}
```

### 3. 검색

#### 티커 검색
```bash
GET /api/news/search/ticker/NVDA?limit=10

# 응답
{
  "ticker": "NVDA",
  "total": 25,
  "articles": [
    {
      "id": 123,
      "title": "NVIDIA Announces New AI Chip",
      "sentiment": "positive",
      "relevance_score": 0.95,
      "published_at": "2025-12-19T10:00:00"
    }
  ]
}
```

#### 태그 검색
```bash
GET /api/news/search/tag/bullish?limit=20

# 응답
{
  "tag": "bullish",
  "total": 15,
  "articles": [...]
}
```

#### 유사 기사 검색
```bash
GET /api/news/articles/1/similar?top_k=5

# 응답
{
  "article_id": 1,
  "similar_articles": [
    {
      "id": 45,
      "title": "Similar Article",
      "similarity": 0.92,
      "published_at": "2025-12-18T15:30:00"
    }
  ]
}
```

### 4. 상태 조회

```bash
GET /api/news/articles/1/status

# 응답
{
  "article_id": 1,
  "has_analysis": true,
  "has_tags": true,
  "has_embedding": true,
  "rag_indexed": true,
  "tag_count": 8,
  "last_processed": "2025-12-19T12:00:00"
}
```

---

## ⚙️ 설정

### Environment Variables

```env
# .env 파일
GOOGLE_API_KEY=your_google_api_key_here
GEMINI_MODEL=gemini-2.5-flash
```

### Model Options
- `gemini-2.5-flash`: 빠르고 저렴 ✅ 권장
- `gemini-2.5-pro`: 더 정확하지만 느림
- `gemini-2.0-flash-exp`: 실험 버전

### Cost
- **무료 티어**: 1,500 requests/day
- **비용**: $0 (무료 크레딧 사용 시)
- **토큰 사용**: ~1,000 tokens/article

---

## 📊 분석 결과 예시

### Example 1: POSITIVE Sentiment
```json
{
  "title": "SILJ: Junior Miners Alternative To Physical Silver",
  "sentiment": "POSITIVE",
  "sentiment_score": 0.70,
  "urgency": "MEDIUM",
  "market_impact_short": "bullish",
  "market_impact_long": "neutral",
  "impact_magnitude": 0.50,
  "actionable": true,
  "risk_category": "financial"
}
```

### Example 2: NEGATIVE Sentiment
```json
{
  "title": "Company Faces Regulatory Investigation",
  "sentiment": "NEGATIVE",
  "sentiment_score": -0.65,
  "urgency": "HIGH",
  "market_impact_short": "bearish",
  "market_impact_long": "bearish",
  "impact_magnitude": 0.75,
  "actionable": true,
  "risk_category": "regulatory"
}
```

---

## 🔧 Troubleshooting

### 분석이 안 됨
**문제**: API 호출했는데 0개 분석

**해결**:
1. API Key 확인: `.env`에 `GOOGLE_API_KEY` 설정
2. 모델 확인: `GEMINI_MODEL=gemini-2.5-flash`
3. 백엔드 재시작
4. 로그 확인: `⚠️ Parse error` 메시지

### Parse Error 발생
**문제**: JSON parse failed

**원인**: Gemini가 잘못된 JSON 반환

**해결**:
- 이미 90% 성공률로 개선됨
- Temperature = 0.1 (낮음)
- response_mime_type = "application/json"

### Quota Exceeded
**문제**: 429 You exceeded your current quota

**해결**:
1. Google AI Studio에서 새 API Key 생성
2. 결제 계정 연결
3. `.env` 파일 업데이트

---

## 📈 Performance Metrics

### Current Stats
- 총 기사: 650개
- 분석 완료: 12개
- 성공률: 90%
- 평균 처리 시간: 3-5초/article

### Targets
- 목표 성공률: >95%
- 목표 처리 속도: <3초/article
- 목표 분석량: 100+ articles/day

---

## 🔗 API Reference

전체 API 문서: http://localhost:8001/docs

### Endpoints Summary
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/news/analyze` | AI 분석 실행 |
| POST | `/api/news/process/{id}` | 단일 기사 처리 |
| POST | `/api/news/batch-process` | 배치 처리 |
| GET | `/api/news/search/ticker/{ticker}` | 티커 검색 |
| GET | `/api/news/search/tag/{tag}` | 태그 검색 |
| GET | `/api/news/articles/{id}/tags` | 태그 조회 |
| GET | `/api/news/articles/{id}/similar` | 유사 기사 |
| GET | `/api/news/articles/{id}/status` | 상태 조회 |

---

## 📝 Notes

### Content Fallback
기사 본문이 없을 때 자동으로 summary 사용:
```python
content = article.content_text or article.content_summary or ""
```

### Minimum Length
분석 최소 길이: 50자 이상

### Duplicate Prevention
이미 처리된 기사는 자동 스킵:
```python
if article.has_tags and article.has_embedding:
    return {"skipped": "Already processed"}
```

---

## 🎓 Best Practices

1. **배치 처리 권장**: 단일 기사보다 batch-process 사용
2. **적절한 max_count**: 10-50개씩 처리
3. **정기적 실행**: Cron job으로 자동화
4. **모니터링**: 성공률 추적 및 에러 로그 확인
5. **API Key 관리**: 환경 변수 사용, 버전 관리 제외

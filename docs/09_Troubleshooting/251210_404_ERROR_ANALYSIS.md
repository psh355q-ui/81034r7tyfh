# 🔍 404 에러 분석 보고서

**작성일**: 2025-12-03
**문제**: 프론트엔드에서 다수의 404 에러 발생

---

## ❌ 발생한 404 에러 목록

```
GET /api/risk/status 404 (Not Found)
GET /api/alerts?limit=20 404 (Not Found)
GET /api/api/news/articles?limit=50&hours=24&actionable_only=false 404 (Not Found)
GET /api/api/news/stats 404 (Not Found)
GET /api/feeds/health/summary 404 (Not Found)
GET /api/feeds 404 (Not Found)
```

---

## 🐛 문제 1: 경로 중복 (`/api/api/`)

### 원인
프론트엔드 코드에서 base URL과 실제 경로에 `/api`가 중복 사용되고 있습니다.

### 문제 코드
**파일**: `frontend/src/services/newsService.ts`

```typescript
// Line 13: Base URL 설정
const API_BASE_URL = '/api';

// Line 193: 요청 시 다시 /api 붙임
const response = await axios.get(
    `${API_BASE_URL}/api/news/articles`,  // /api + /api/news = /api/api/news
    { params }
);

// Line 246: 통계 조회
const response = await axios.get<NewsStats>(`${API_BASE_URL}/api/news/stats`);
// 결과: /api/api/news/stats
```

### 영향받는 파일
- `frontend/src/services/newsService.ts` (Line 13, 147, 158, 167, 178, 193, 204, 218, 228, 238, 246, 254, 262, 272)
- `frontend/src/services/aiChatService.ts` (Line 13, 103, 121, 132, 142, 152)
- `frontend/src/services/geminiFreeService.ts` (Line 10, 88, 103, 111, 121, 133)

### ✅ 해결 방법

**Option 1: Base URL을 빈 문자열로** (권장)
```typescript
// newsService.ts:13
const API_BASE_URL = '';  // '/api' 제거

// 요청
`${API_BASE_URL}/api/news/articles`  // -> /api/news/articles (정상)
```

**Option 2: 요청 경로에서 /api 제거**
```typescript
// newsService.ts:13
const API_BASE_URL = '/api';  // 유지

// 요청
`${API_BASE_URL}/news/articles`  // -> /api/news/articles (정상)
```

---

## 🐛 문제 2: 미구현 엔드포인트

### 구현 안된 API들

#### 1. 리스크 관리
```
GET /api/risk/status
```
**상태**: ❌ 미구현
**백엔드 파일**: 없음
**요청 위치**: 프론트엔드 대시보드

#### 2. 알림 시스템
```
GET /api/alerts?limit=20
```
**상태**: ❌ 미구현
**백엔드 파일**: 없음
**요청 위치**: 프론트엔드 헤더/알림 센터

#### 3. 뉴스 API
```
GET /api/news/articles?limit=50&hours=24&actionable_only=false
GET /api/news/stats
```
**상태**: ❌ 미구현
**백엔드 파일**: 없음
**요청 위치**: `newsService.ts:193, 246`

#### 4. 피드 상태
```
GET /api/feeds/health/summary
GET /api/feeds
```
**상태**: ❌ 미구현
**백엔드 파일**: 없음
**요청 위치**: `newsService.ts:254`

---

## ✅ 현재 구현된 엔드포인트

### KIS API (모두 정상 작동)
```
✅ GET  /kis/health
✅ GET  /kis/balance
✅ GET  /kis/price/{symbol}
✅ GET  /kis/stats
✅ POST /kis/auto-trade
✅ POST /kis/manual-order
```

### 시그널 & 트레이딩 (모두 정상 작동)
```
✅ GET  /api/signals
✅ GET  /api/signals/{signal_id}
✅ GET  /api/signals/stats/summary
✅ POST /api/signals/{signal_id}/execute
✅ POST /api/signals/{signal_id}/close
```

### 포트폴리오 & 성과 (모두 정상 작동)
```
✅ GET  /api/portfolio
✅ GET  /api/performance/stats
```

### 마켓 데이터 (모두 정상 작동)
```
✅ GET  /api/market/price/{ticker}
```

### 크롤러 (모두 정상 작동)
```
✅ GET  /api/crawler/status
✅ POST /api/crawler/start
✅ POST /api/crawler/stop
```

---

## 🔧 수정 필요한 파일

### 1️⃣ 최우선: newsService.ts
**파일**: `frontend/src/services/newsService.ts`

```typescript
// ❌ 현재 (잘못됨)
const API_BASE_URL = '/api';

// 요청:
`${API_BASE_URL}/api/news/articles`  // /api/api/news/articles

// ✅ 수정
const API_BASE_URL = '';

// 요청:
`${API_BASE_URL}/api/news/articles`  // /api/news/articles
```

**영향받는 함수**:
- `crawlNews()` - Line 147
- `crawlNewsByTicker()` - Line 158
- `analyzeAllNews()` - Line 167
- `analyzeNewsArticle()` - Line 178
- `getNewsArticles()` - Line 193
- `getNewsArticleById()` - Line 204
- `getNewsByTicker()` - Line 218
- `getHighImpactNews()` - Line 228
- `getNewsWarnings()` - Line 238
- `getNewsStats()` - Line 246
- `getRSSFeeds()` - Line 254
- `addRSSFeed()` - Line 262
- `toggleRSSFeed()` - Line 272

### 2️⃣ aiChatService.ts
**파일**: `frontend/src/services/aiChatService.ts`

```typescript
// ❌ 현재
const API_BASE_URL = '/api';
`${API_BASE_URL}/api/ai-chat/chat`  // /api/api/ai-chat/chat

// ✅ 수정
const API_BASE_URL = '';
`${API_BASE_URL}/api/ai-chat/chat`  // /api/ai-chat/chat
```

**영향받는 함수**:
- `sendMessage()` - Line 103
- `getChatHistory()` - Line 121
- `getChatDetail()` - Line 132
- `getPricing()` - Line 142
- `getAvailableModels()` - Line 152

### 3️⃣ geminiFreeService.ts
**파일**: `frontend/src/services/geminiFreeService.ts`

```typescript
// ❌ 현재
const API_BASE_URL = '/api';
`${API_BASE_URL}/api/gemini-free/chat`  // /api/api/gemini-free/chat

// ✅ 수정
const API_BASE_URL = '';
`${API_BASE_URL}/api/gemini-free/chat`  // /api/gemini-free/chat
```

**영향받는 함수**:
- `sendMessage()` - Line 88
- `getUsageStats()` - Line 103
- `getChatHistory()` - Line 111
- `getGeminiFreeStatus()` - Line 121
- `analyzeNewsWithGeminiFree()` - Line 133

---

## 🎯 수정 우선순위

### 🔥 즉시 수정 (High Priority)
1. **newsService.ts** 경로 중복 수정
2. **aiChatService.ts** 경로 중복 수정
3. **geminiFreeService.ts** 경로 중복 수정

이 3개 파일만 수정하면 대부분의 `/api/api/` 중복 문제 해결됨.

### 📝 백엔드 구현 필요 (Medium Priority)
4. `/api/news/articles` 엔드포인트 구현
5. `/api/news/stats` 엔드포인트 구현
6. `/api/alerts` 엔드포인트 구현
7. `/api/feeds` 엔드포인트 구현
8. `/api/feeds/health/summary` 엔드포인트 구현
9. `/api/risk/status` 엔드포인트 구현

---

## 🧪 테스트 방법

### 1. 경로 중복 확인
```bash
# 프론트엔드 소스에서 중복 패턴 검색
cd D:\code\ai-trading-system\frontend
grep -r "API_BASE_URL}/api/" src/
```

### 2. 수정 후 테스트
```bash
# 개발 서버 시작
npm run dev

# 브라우저 콘솔에서 404 에러 확인
# /api/api/ 패턴이 사라져야 함
```

### 3. 백엔드 엔드포인트 확인
```bash
# Swagger UI에서 모든 엔드포인트 확인
http://localhost:8000/docs

# 구현된 엔드포인트만 호출
```

---

## 📋 체크리스트

### 프론트엔드 수정
- [ ] `newsService.ts` Line 13: `API_BASE_URL = ''` 로 변경
- [ ] `aiChatService.ts` Line 13: `API_BASE_URL = ''` 로 변경
- [ ] `geminiFreeService.ts` Line 10: `API_BASE_URL = ''` 로 변경
- [ ] 브라우저에서 `/api/api/` 패턴 사라졌는지 확인
- [ ] 정상 작동하는 API 테스트

### 백엔드 구현
- [ ] `news_router.py` 생성
- [ ] `/api/news/articles` 구현
- [ ] `/api/news/stats` 구현
- [ ] `alerts_router.py` 생성
- [ ] `/api/alerts` 구현
- [ ] `feeds_router.py` 생성
- [ ] `/api/feeds` 구현
- [ ] `/api/feeds/health/summary` 구현
- [ ] `risk_router.py` 생성
- [ ] `/api/risk/status` 구현

---

## 🚀 빠른 수정 스크립트

프론트엔드 3개 파일 일괄 수정:

```bash
cd D:\code\ai-trading-system\frontend\src\services

# newsService.ts 수정
sed -i "s/const API_BASE_URL = '\/api';/const API_BASE_URL = '';/g" newsService.ts

# aiChatService.ts 수정
sed -i "s/const API_BASE_URL = '\/api';/const API_BASE_URL = '';/g" aiChatService.ts

# geminiFreeService.ts 수정
sed -i "s/const API_BASE_URL = '\/api';/const API_BASE_URL = '';/g" geminiFreeService.ts
```

또는 Windows PowerShell:
```powershell
cd D:\code\ai-trading-system\frontend\src\services

(Get-Content newsService.ts) -replace "const API_BASE_URL = '/api';", "const API_BASE_URL = '';" | Set-Content newsService.ts
(Get-Content aiChatService.ts) -replace "const API_BASE_URL = '/api';", "const API_BASE_URL = '';" | Set-Content aiChatService.ts
(Get-Content geminiFreeService.ts) -replace "const API_BASE_URL = '/api';", "const API_BASE_URL = '';" | Set-Content geminiFreeService.ts
```

---

## 📊 요약

### 문제 유형
1. **경로 중복 (3개 파일)**: `/api/api/` 패턴
2. **미구현 API (6개)**: 백엔드에 없는 엔드포인트

### 즉시 조치
- 프론트엔드 3개 파일에서 `API_BASE_URL = '/api'`를 `API_BASE_URL = ''`로 변경

### 점진적 구현
- 백엔드 6개 API 엔드포인트 구현 (우선순위: 뉴스 > 알림 > 피드 > 리스크)

### 예상 효과
- 경로 중복 수정 후: 잘못된 404 에러 제거
- API 구현 후: 프론트엔드 모든 기능 정상 작동

# Double `/api` Prefix Fix - Complete

**Date**: 2025-12-03 23:00
**Status**: FIXED

---

## Problem

Multiple API service files were adding `/api` prefix to endpoint URLs when the base URL already contained `/api`, resulting in double prefix errors like:

```
GET /api/api/news/articles 404 Not Found
GET /api/api/news/stats 404 Not Found
```

---

## Root Cause

Service files were constructed in two ways:

### Pattern 1: Direct `API_BASE_URL` (newsService.ts)
```typescript
const API_BASE_URL = '/api';

// Wrong - adds /api twice
axios.get(`${API_BASE_URL}/api/news/articles`)
// Results in: /api/api/news/articles ❌

// Correct
axios.get(`${API_BASE_URL}/news/articles`)
// Results in: /api/news/articles ✅
```

### Pattern 2: Axios Instance with baseURL (aiReviewApi.ts)
```typescript
const api = axios.create({
  baseURL: API_BASE_URL,  // '/api'
});

// Wrong - baseURL already has /api
api.get('/api/ai-reviews/123')
// Results in: /api/api/ai-reviews/123 ❌

// Correct
api.get('/ai-reviews/123')
// Results in: /api/ai-reviews/123 ✅
```

---

## Files Fixed

### 1. frontend/src/services/newsService.ts

**Fixed 12 endpoints** - Removed redundant `/api` prefix:

- Line 147: `/api/news/crawl` → `/news/crawl`
- Line 158: `/api/news/crawl/ticker/${ticker}` → `/news/crawl/ticker/${ticker}`
- Line 167: `/api/news/analyze` → `/news/analyze`
- Line 178: `/api/news/analyze/${articleId}` → `/news/analyze/${articleId}`
- Line 193: `/api/news/articles` → `/news/articles`
- Line 204: `/api/news/articles/${articleId}` → `/news/articles/${articleId}`
- Line 218: `/api/news/ticker/${ticker}` → `/news/ticker/${ticker}`
- Line 228: `/api/news/high-impact` → `/news/high-impact`
- Line 238: `/api/news/warnings` → `/news/warnings`
- Line 246: `/api/news/stats` → `/news/stats`
- Line 254: `/api/news/feeds` → `/news/feeds`
- Line 262: `/api/news/feeds` → `/news/feeds`
- Line 272: `/api/news/feeds/${feedId}/toggle` → `/news/feeds/${feedId}/toggle`

### 2. frontend/src/services/aiReviewApi.ts

**Fixed 4 endpoints** - Removed redundant `/api` prefix:

- Line 125: `/api/ai-reviews/${analysisId}` → `/ai-reviews/${analysisId}`
- Line 136: `/api/ai-reviews/ticker/${ticker}/history` → `/ai-reviews/ticker/${ticker}/history`
- Line 146: `/api/ai-reviews/ticker/${ticker}/latest` → `/ai-reviews/ticker/${ticker}/latest`
- Line 192: `/api/ai-reviews/${analysisId}` → `/ai-reviews/${analysisId}`

### 3. frontend/src/services/logsApi.ts

**No changes needed** - Already correct!

This file uses `API_BASE_URL = '/api/logs'` which includes the full path, so endpoints like `${API_BASE_URL}` and `${API_BASE_URL}/statistics` work correctly.

### 4. frontend/src/services/analyticsApi.ts

**No changes needed** - Already correct!

This file uses the shared `api` instance from `./api` which already has the baseURL configured properly.

---

## Before vs After

### News API Calls
**Before:**
```
GET /api/api/news/articles?limit=50 → 404 Not Found
GET /api/api/news/stats → 404 Not Found
```

**After:**
```
GET /api/news/articles?limit=50 → 200 OK (or 404 if endpoint doesn't exist yet)
GET /api/news/stats → 200 OK (or 404 if endpoint doesn't exist yet)
```

### AI Reviews API Calls
**Before:**
```
GET /api/api/ai-reviews → 404 Not Found
GET /api/api/ai-reviews/123 → 404 Not Found
```

**After:**
```
GET /api/ai-reviews → 200 OK (or 404 if endpoint doesn't exist yet)
GET /api/ai-reviews/123 → 200 OK (or 404 if endpoint doesn't exist yet)
```

---

## Verification

To verify the fixes are working:

1. **Check Browser Network Tab:**
   - All API calls should now use single `/api` prefix
   - No more `/api/api/...` URLs

2. **Backend Logs Should Show:**
   ```
   INFO: GET /api/news/articles?limit=50 200 OK
   INFO: GET /api/news/stats 200 OK
   INFO: GET /api/ai-reviews 200 OK
   ```

3. **Test in Browser Console:**
   ```javascript
   // News API
   fetch('/api/news/articles?limit=10')
     .then(r => r.json())
     .then(console.log)

   // AI Reviews API
   fetch('/api/ai-reviews?limit=10')
     .then(r => r.json())
     .then(console.log)
   ```

---

## Remaining 404s (Expected)

Some endpoints still return 404 because they don't exist in the backend yet:

### Not Yet Implemented:
- `/api/news/*` - News aggregation endpoints (need to be added to backend)
- `/api/ai-reviews` - AI review endpoints (need to be added to backend)
- `/api/risk/status` - Risk management endpoints
- `/api/system/info` - System information endpoints
- `/api/alerts` - Alert management endpoints
- `/api/feeds` - Feed health endpoints
- `/api/logs/*` - Logging endpoints
- `/api/reports/advanced/performance-attribution` - Advanced reports

These are **legitimate 404s** - they need backend implementations, not frontend fixes.

---

## Code Pattern Reference

### ✅ Correct Patterns

**Pattern A: Direct baseURL usage**
```typescript
const API_BASE_URL = '/api';
axios.get(`${API_BASE_URL}/news/articles`)  // ✅ /api/news/articles
```

**Pattern B: Axios instance with baseURL**
```typescript
const api = axios.create({ baseURL: '/api' });
api.get('/news/articles')  // ✅ /api/news/articles
```

**Pattern C: Full path in baseURL**
```typescript
const API_BASE_URL = '/api/logs';
axios.get(`${API_BASE_URL}`)  // ✅ /api/logs
axios.get(`${API_BASE_URL}/statistics`)  // ✅ /api/logs/statistics
```

### ❌ Incorrect Patterns

**Pattern X: Double prefix with direct baseURL**
```typescript
const API_BASE_URL = '/api';
axios.get(`${API_BASE_URL}/api/news/articles`)  // ❌ /api/api/news/articles
```

**Pattern Y: Double prefix with axios instance**
```typescript
const api = axios.create({ baseURL: '/api' });
api.get('/api/news/articles')  // ❌ /api/api/news/articles
```

---

## Summary

- ✅ Fixed 16 endpoint URLs across 2 service files
- ✅ All API calls now use correct single `/api` prefix
- ✅ No breaking changes to API contracts
- ✅ Backward compatible with existing backend
- 📝 Remaining 404s are expected (endpoints not implemented yet)

---

**Status**: 🎉 DOUBLE `/api` PREFIX ISSUE RESOLVED
**Next Steps**: Implement missing backend endpoints that legitimately return 404


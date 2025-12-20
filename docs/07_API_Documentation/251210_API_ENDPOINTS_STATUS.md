# 📊 API 엔드포인트 상태 보고서

**작성일**: 2025-12-03
**서버**: http://localhost:8000

---

## ✅ 현재 구현된 엔드포인트

### 기본 엔드포인트
| 메서드 | 경로 | 설명 | 파일 |
|--------|------|------|------|
| GET | `/` | API 랜딩 페이지 (HTML) | main.py:200 |
| GET | `/favicon.ico` | 파비콘 | main.py:194 |

### KIS 통합 엔드포인트 (`/kis`)
| 메서드 | 경로 | 설명 | 파일 |
|--------|------|------|------|
| POST | `/kis/auto-trade` | 자동 트레이딩 (뉴스 분석 → 주문) | kis_integration_router.py:141 |
| GET | `/kis/balance` | 계좌 잔고 조회 | kis_integration_router.py:239 |
| GET | `/kis/price/{symbol}` | 실시간 주가 조회 | kis_integration_router.py:272 |
| GET | `/kis/health` | KIS API 헬스 체크 | kis_integration_router.py:298 |
| POST | `/kis/manual-order` | 수동 주문 실행 | kis_integration_router.py:309 |
| GET | `/kis/stats` | KIS 통계 | kis_integration_router.py:356 |

### 시그널 엔드포인트 (`/api/signals`)
| 메서드 | 경로 | 설명 | 파일 |
|--------|------|------|------|
| GET | `/api/signals` | 시그널 목록 조회 | main.py:342 |
| GET | `/api/signals/{signal_id}` | 시그널 상세 조회 | main.py:407 |
| GET | `/api/signals/stats/summary` | 시그널 통계 요약 | main.py:507 |
| POST | `/api/signals/{signal_id}/execute` | 트레이드 실행 | main.py:678 |
| POST | `/api/signals/{signal_id}/close` | 포지션 종료 | main.py:727 |

### 포트폴리오 & 성과 엔드포인트
| 메서드 | 경로 | 설명 | 파일 |
|--------|------|------|------|
| GET | `/api/performance/stats` | 성과 통계 | main.py:554 |
| GET | `/api/portfolio` | 포트폴리오 조회 | main.py:596 |

### 마켓 데이터 엔드포인트
| 메서드 | 경로 | 설명 | 파일 |
|--------|------|------|------|
| GET | `/api/market/price/{ticker}` | 시장 가격 조회 | main.py:781 |

### 크롤러 엔드포인트
| 메서드 | 경로 | 설명 | 파일 |
|--------|------|------|------|
| GET | `/api/crawler/status` | 크롤러 상태 | main.py:905 |
| POST | `/api/crawler/start` | 크롤러 시작 | main.py:933 |
| POST | `/api/crawler/stop` | 크롤러 중지 | main.py:949 |

---

## ❌ 구현되지 않은 엔드포인트 (404 발생)

프론트엔드가 호출하려는 엔드포인트들:

### 리스크 관리
- `GET /api/risk/status` - 리스크 상태 조회
- 기능: 포트폴리오 리스크 지표, VaR, 포지션 집중도 등

### 알림 시스템
- `GET /api/alerts?limit=20` - 최근 알림 조회
- 기능: 거래 알림, 리스크 알림, 시스템 알림 등

### 뉴스 & 분석
- `GET /api/api/news/articles?limit=50&hours=24&actionable_only=false` - 뉴스 기사 조회
- `GET /api/api/news/stats` - 뉴스 통계
- 기능: 크롤링된 뉴스, 감성 분석 결과, 실행 가능한 뉴스 필터링

### 피드 상태
- `GET /api/feeds/health/summary` - 피드 헬스 요약
- `GET /api/feeds` - 피드 목록
- 기능: 뉴스 피드 소스 상태, 크롤러 헬스 체크

---

## 🔍 문제 분석

### 1. 경로 중복 (`/api/api/`)
프론트엔드 요청에서 `/api/api/news/...` 처럼 `api`가 중복되고 있습니다.

**원인**:
- 프론트엔드에서 base URL에 `/api` 포함
- API 경로에도 `/api` 포함
- 결과: `/api` + `/api/news` = `/api/api/news`

**해결 방안**:
1. 프론트엔드 base URL을 `/api` 없이 설정
2. 또는 백엔드 경로에서 `/api` 제거

### 2. 미구현 기능
다음 기능들이 프론트엔드에는 있지만 백엔드에는 미구현:
- 리스크 관리 모듈
- 알림 시스템
- 뉴스 아티클 조회 API
- 피드 헬스 체크

---

## 🎯 권장 조치 사항

### 단기 (즉시)
1. **프론트엔드 base URL 수정**
   ```javascript
   // 현재 (잘못됨)
   const BASE_URL = "http://localhost:8000/api";

   // 수정
   const BASE_URL = "http://localhost:8000";
   ```

2. **404 에러 핸들링 개선**
   - 미구현 API에 대한 fallback UI 표시
   - "Coming Soon" 메시지 또는 기능 숨김

### 중기 (백엔드 구현 필요)
1. **뉴스 API 구현**
   ```python
   @app.get("/api/news/articles")
   async def get_news_articles(
       limit: int = 50,
       hours: int = 24,
       actionable_only: bool = False
   ):
       # TimescaleDB에서 뉴스 조회
       pass
   ```

2. **알림 API 구현**
   ```python
   @app.get("/api/alerts")
   async def get_alerts(limit: int = 20):
       # Redis 또는 PostgreSQL에서 알림 조회
       pass
   ```

3. **리스크 관리 API 구현**
   ```python
   @app.get("/api/risk/status")
   async def get_risk_status():
       # 포트폴리오 리스크 계산
       pass
   ```

4. **피드 헬스 API 구현**
   ```python
   @app.get("/api/feeds/health/summary")
   async def get_feeds_health():
       # 크롤러 상태 집계
       pass

   @app.get("/api/feeds")
   async def get_feeds():
       # 피드 소스 목록
       pass
   ```

### 장기 (아키텍처 개선)
1. **API 라우터 분리**
   - `news_router.py` - 뉴스 관련 엔드포인트
   - `alerts_router.py` - 알림 관련 엔드포인트
   - `risk_router.py` - 리스크 관리 엔드포인트
   - `feeds_router.py` - 피드 관련 엔드포인트

2. **통합 API 문서**
   - Swagger UI에서 모든 엔드포인트 확인 가능
   - 구현 상태 명시 (Implemented, Coming Soon, Deprecated)

---

## 🧪 테스트 방법

### 1. 구현된 엔드포인트 테스트
```bash
# KIS Health Check
curl http://localhost:8000/kis/health

# 시그널 목록
curl http://localhost:8000/api/signals

# 포트폴리오
curl http://localhost:8000/api/portfolio

# Swagger UI
http://localhost:8000/docs
```

### 2. 404 엔드포인트 확인
```bash
# 아직 구현 안됨 - 404 반환
curl http://localhost:8000/api/risk/status
curl http://localhost:8000/api/alerts
curl http://localhost:8000/api/news/articles
curl http://localhost:8000/api/feeds
```

---

## 📋 구현 우선순위

### High Priority (프론트엔드가 즉시 필요)
1. ⚠️ `/api/news/articles` - 뉴스 조회 (프론트엔드 메인 기능)
2. ⚠️ `/api/alerts` - 알림 조회 (사용자 피드백)
3. ⚠️ `/api/feeds/health/summary` - 피드 상태 (시스템 모니터링)

### Medium Priority (중요하지만 대체 가능)
4. `/api/risk/status` - 리스크 상태 (포트폴리오로 대체 가능)
5. `/api/feeds` - 피드 목록 (크롤러 상태로 대체 가능)
6. `/api/news/stats` - 뉴스 통계 (시그널 통계로 대체 가능)

### Low Priority (Nice to have)
7. 추가 대시보드 위젯
8. 고급 분석 엔드포인트
9. 관리자 전용 엔드포인트

---

## 🔧 다음 단계

1. **프론트엔드 base URL 확인 및 수정**
   - 파일: `frontend/src/config.js` 또는 유사 파일
   - `/api/api/` 중복 제거

2. **백엔드 API 구현 시작**
   - 우선순위대로 엔드포인트 구현
   - 각 기능마다 테스트 작성

3. **API 문서 업데이트**
   - Swagger에 구현 상태 명시
   - 프론트엔드 개발자에게 공유

---

**요약**:
- ✅ **13개 엔드포인트** 구현 완료 (KIS, 시그널, 포트폴리오, 크롤러)
- ❌ **6개 엔드포인트** 미구현 (뉴스, 알림, 리스크, 피드)
- 🔧 프론트엔드 base URL 중복 문제 수정 필요
- 📝 백엔드 API 구현 우선순위 명시

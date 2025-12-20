# Network Access Guide - IP 자동 감지

## 문제 상황

로컬 IP가 변경되거나 다른 기기에서 접속할 때마다 코드에 하드코딩된 `localhost`를 수동으로 변경해야 하는 불편함.

## 해결 방법

이제 **자동으로 현재 호스트를 감지**하고, 환경변수로 커스터마이징 가능하게 변경되었습니다.

---

## 1. Backend (FastAPI)

### CORS 설정 변경

**이전:**
```python
allow_origins=["http://localhost:3000", "http://localhost:5173"]
```

**변경 후:**
```python
# 환경변수에서 읽거나 모든 origin 허용
FRONTEND_URLS = os.getenv("FRONTEND_URLS", "").split(",") if os.getenv("FRONTEND_URLS") else []
ALLOW_ORIGINS = FRONTEND_URLS if FRONTEND_URLS else ["*"]  # 개발: *, 프로덕션: 명시적 지정
```

### 환경변수 설정 (.env)

```bash
# 개발 환경 (모든 origin 허용)
# FRONTEND_URLS는 비워둠 (주석 처리)

# 네트워크 접근 (특정 IP만 허용)
FRONTEND_URLS=http://192.168.0.100:3000,http://192.168.0.100:5173,http://localhost:3000,http://localhost:5173

# 프로덕션 (명시적 지정 필수)
FRONTEND_URLS=https://yourdomain.com,https://www.yourdomain.com
```

---

## 2. Frontend (React)

### API URL 자동 감지

**이전:**
```typescript
const API_BASE_URL = 'http://localhost:8000';
const WS_URL = 'ws://localhost:8000/ws/signals';
```

**변경 후:**
```typescript
// 자동 감지: 현재 브라우저의 hostname 사용
const API_BASE_URL = import.meta.env.VITE_API_URL ||
  (window.location.hostname === 'localhost'
    ? 'http://localhost:8000'
    : `http://${window.location.hostname}:8000`);

const WS_URL = import.meta.env.VITE_WS_URL ||
  (window.location.hostname === 'localhost'
    ? 'ws://localhost:8000/ws/signals'
    : `ws://${window.location.hostname}:8000/ws/signals`);
```

### 환경변수 설정 (frontend/.env)

**Option 1: 자동 감지 (권장)**
```bash
# .env 파일에 아무것도 설정하지 않음
# → 현재 브라우저의 hostname 자동 사용
```

**Option 2: 명시적 지정**
```bash
# frontend/.env (로컬)
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws/signals

# frontend/.env.local (네트워크)
VITE_API_URL=http://192.168.0.100:8000
VITE_WS_URL=ws://192.168.0.100:8000/ws/signals

# frontend/.env.production (프로덕션)
VITE_API_URL=https://api.yourdomain.com
VITE_WS_URL=wss://api.yourdomain.com/ws/signals
```

---

## 3. 사용 시나리오

### Scenario 1: 로컬 개발 (localhost)

**아무 설정 없이 그냥 실행:**
```bash
# Backend
python scripts/run_api_server.py

# Frontend
cd frontend
npm run dev
```

**결과:**
- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8000`
- WebSocket: `ws://localhost:8000/ws/signals`
- ✅ 자동으로 localhost 사용

---

### Scenario 2: 같은 네트워크의 다른 기기에서 접근

**예: PC IP가 192.168.0.100일 때**

**1. Backend 실행 (PC):**
```bash
python scripts/run_api_server.py --host 0.0.0.0 --port 8000
```

**2. Frontend 실행 (PC):**
```bash
cd frontend
npm run dev --host 0.0.0.0
```

**3. 스마트폰/태블릿에서 접속:**
- 브라우저 주소: `http://192.168.0.100:5173`
- ✅ 자동으로 `http://192.168.0.100:8000` API 사용
- ✅ 자동으로 `ws://192.168.0.100:8000/ws/signals` WebSocket 사용

**아무런 설정 변경 없이 자동으로 작동!**

---

### Scenario 3: IP가 변경된 경우

**예: 192.168.0.100 → 192.168.0.150**

**변경 전:**
- 하드코딩: 코드 수정 + 재배포 필요

**변경 후:**
- ✅ **아무것도 안 해도 됨!** 자동 감지

---

### Scenario 4: 특정 IP만 강제 지정 (환경변수 사용)

**frontend/.env.local 생성:**
```bash
VITE_API_URL=http://192.168.0.200:8000
VITE_WS_URL=ws://192.168.0.200:8000/ws/signals
```

**Backend .env:**
```bash
FRONTEND_URLS=http://192.168.0.100:5173,http://192.168.0.150:5173
```

**재시작:**
```bash
# Frontend
npm run dev

# Backend
python scripts/run_api_server.py
```

---

## 4. 동작 원리

### Frontend 자동 감지 로직

```typescript
const API_BASE_URL = import.meta.env.VITE_API_URL ||  // 1순위: 환경변수
  (window.location.hostname === 'localhost'           // 2순위: 자동 감지
    ? 'http://localhost:8000'                         //   - localhost면 localhost:8000
    : `http://${window.location.hostname}:8000`);     //   - 아니면 현재 hostname:8000
```

**예시:**
- 브라우저 주소: `http://localhost:5173` → API: `http://localhost:8000`
- 브라우저 주소: `http://192.168.0.100:5173` → API: `http://192.168.0.100:8000`
- 브라우저 주소: `http://myserver.com` → API: `http://myserver.com:8000`

### Backend CORS 로직

```python
FRONTEND_URLS = os.getenv("FRONTEND_URLS", "").split(",") if os.getenv("FRONTEND_URLS") else []
ALLOW_ORIGINS = FRONTEND_URLS if FRONTEND_URLS else ["*"]
```

**예시:**
- 환경변수 없음 → CORS: `["*"]` (모든 origin 허용, 개발 환경)
- `FRONTEND_URLS=http://192.168.0.100:3000` → CORS: `["http://192.168.0.100:3000"]`

---

## 5. 환경변수 파일 위치

### Backend
```
ai-trading-system/
├── .env                    # 실제 사용 (gitignore됨)
└── .env.example            # 템플릿 (git에 포함)
```

### Frontend
```
ai-trading-system/frontend/
├── .env                    # 모든 환경 공통
├── .env.local              # 로컬 개발 (gitignore됨)
├── .env.production         # 프로덕션 빌드
└── .env.example            # 템플릿 (git에 포함)
```

---

## 6. 빠른 설정 가이드

### 개발 환경 (localhost)

**아무 설정 없이 실행:**
```bash
# Backend
python scripts/run_api_server.py

# Frontend
cd frontend
npm run dev
```

✅ 끝! 자동으로 localhost 사용.

---

### 네트워크 접근 (같은 Wi-Fi)

**1. 내 PC IP 확인:**
```bash
# Windows
ipconfig

# Mac/Linux
ifconfig
```

**2. Backend 실행 (모든 IP에서 접근 가능하게):**
```bash
python scripts/run_api_server.py --host 0.0.0.0
```

**3. Frontend 실행 (모든 IP에서 접근 가능하게):**
```bash
cd frontend
npm run dev --host 0.0.0.0
```

**4. 다른 기기에서 접속:**
- 브라우저: `http://192.168.0.XXX:5173`

✅ 끝! 자동으로 API도 같은 IP 사용.

---

### 프로덕션 배포

**backend/.env:**
```bash
FRONTEND_URLS=https://yourdomain.com,https://www.yourdomain.com
```

**frontend/.env.production:**
```bash
VITE_API_URL=https://api.yourdomain.com
VITE_WS_URL=wss://api.yourdomain.com/ws/signals
```

**빌드:**
```bash
cd frontend
npm run build
```

---

## 7. 트러블슈팅

### 문제: CORS 에러
```
Access to XMLHttpRequest blocked by CORS policy
```

**해결:**
1. Backend `.env`에 `FRONTEND_URLS` 추가
2. 또는 개발 환경에서는 `FRONTEND_URLS` 주석 처리 (모든 origin 허용)

```bash
# .env (개발)
# FRONTEND_URLS=   # 주석 처리 또는 삭제 → 모든 origin 허용

# .env (프로덕션)
FRONTEND_URLS=http://192.168.0.100:5173
```

### 문제: WebSocket 연결 실패
```
WebSocket connection failed
```

**확인:**
1. Backend가 실행 중인지 확인: `http://localhost:8000/docs`
2. 방화벽이 8000 포트를 차단하는지 확인
3. Frontend 환경변수 확인:
   ```bash
   # frontend/.env.local
   VITE_WS_URL=ws://192.168.0.100:8000/ws/signals
   ```

### 문제: API 404 에러
```
Failed to fetch
```

**확인:**
1. Backend API 서버가 실행 중인지 확인
2. 브라우저 개발자 도구(F12) → Network 탭에서 실제 요청 URL 확인
3. Frontend 콘솔에서 `API_BASE_URL` 출력:
   ```typescript
   console.log('API URL:', API_BASE_URL);
   ```

---

## 8. 체크리스트

### 로컬 개발
- [ ] Backend 실행: `python scripts/run_api_server.py`
- [ ] Frontend 실행: `cd frontend && npm run dev`
- [ ] 브라우저: `http://localhost:5173`
- [ ] API 문서: `http://localhost:8000/docs`

### 네트워크 접근
- [ ] 내 IP 확인: `ipconfig` or `ifconfig`
- [ ] Backend: `--host 0.0.0.0`
- [ ] Frontend: `npm run dev --host 0.0.0.0`
- [ ] 방화벽 8000, 5173 포트 허용
- [ ] 다른 기기에서 `http://[내IP]:5173` 접속

### 프로덕션
- [ ] `.env` 파일 보안 설정 확인
- [ ] `FRONTEND_URLS` 명시적 지정
- [ ] HTTPS/WSS 설정
- [ ] API 키 확인

---

## 9. 요약

### 핵심 변경 사항

1. **Backend CORS**: 환경변수 `FRONTEND_URLS` 지원, 없으면 모든 origin 허용
2. **Frontend API URL**: `window.location.hostname` 자동 감지
3. **WebSocket URL**: `window.location.hostname` 자동 감지

### 주요 이점

✅ **IP 변경 시 코드 수정 불필요**
✅ **다른 기기에서 자동으로 올바른 API 호출**
✅ **개발/프로덕션 환경 분리 용이**
✅ **환경변수로 커스터마이징 가능**

### 기본 동작

- **개발**: 아무 설정 없이 localhost 자동 사용
- **네트워크**: 브라우저 주소의 hostname 자동 사용
- **프로덕션**: 환경변수로 명시적 지정

---

**Updated**: 2025-11-28
**Version**: 1.0.0

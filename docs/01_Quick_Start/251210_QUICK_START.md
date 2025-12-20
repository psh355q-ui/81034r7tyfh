# ⚡ 빠른 시작 가이드

## 🚀 서버 시작하기 (3가지 방법)

### 방법 1️⃣: 배치 파일 사용 (가장 간단!)

```batch
# start_server.bat 더블클릭
start_server.bat
```

### 방법 2️⃣: localhost + 네트워크 IP 모두 사용

```batch
cd D:\code\ai-trading-system
python -X utf8 -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8002 --reload
```

접속 가능:
- ✅ http://localhost:8002
- ✅ http://127.0.0.1:8002
- ✅ http://192.168.50.148:8002

### 방법 3️⃣: 특정 IP만 사용

```batch
cd D:\code\ai-trading-system
python -X utf8 -m uvicorn backend.api.main:app --host 192.168.50.148 --port 8002 --reload
```

접속 가능:
- ❌ http://localhost:8002 (불가)
- ✅ http://192.168.50.148:8002

---

## 🌐 접속 확인

### 1. 브라우저에서 확인

**Swagger UI** (API 문서):
```
http://192.168.50.148:8002/docs
```

또는 (0.0.0.0으로 시작했다면):
```
http://localhost:8002/docs
```

**Health Check**:
```
http://192.168.50.148:8002/kis/health
```

### 2. 명령어로 확인

```batch
# Health Check
curl http://192.168.50.148:8002/kis/health

# 또는 PowerShell에서
Invoke-WebRequest -Uri http://192.168.50.148:8002/kis/health
```

### 3. Python 스크립트로 테스트

```batch
python test_kis_api.py
```

---

## 📊 예상 출력

서버가 정상적으로 시작되면:

```
INFO:     Uvicorn running on http://192.168.50.148:8002 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using StatReload
INFO:     Started server process [67890]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

---

## 🔧 문제 해결

### 문제: "localhost로 접속 안됨"

**해결**: 서버를 `0.0.0.0`으로 시작하세요
```batch
python -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8002 --reload
```

### 문제: "포트가 이미 사용 중"

**해결**: 실행 중인 서버 종료
```batch
# 1. 포트 사용 프로세스 찾기
netstat -ano | findstr :8002

# 2. 프로세스 종료 (PID 확인 후)
taskkill /PID <PID> /F
```

### 문제: "ModuleNotFoundError"

**해결**: 프로젝트 루트에서 실행
```batch
cd D:\code\ai-trading-system
python -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8002 --reload
```

---

## 🎯 다음 단계

1. **Swagger UI 열기**: http://localhost:8002/docs (또는 192.168.50.148:8002/docs)
2. **Health Check 테스트**: `/kis/health` 엔드포인트 실행
3. **Auto Trade 테스트**: `/kis/auto-trade` 엔드포인트로 뉴스 분석
4. **Balance 조회**: `/kis/balance` 엔드포인트로 계좌 확인

---

## 📝 추천 설정

**개발 중**: `0.0.0.0`으로 시작 (모든 인터페이스)
```batch
python -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8002 --reload
```

**프로덕션**: 특정 IP로 제한
```batch
python -m uvicorn backend.api.main:app --host 192.168.50.148 --port 8002
```

---

## 🛑 서버 중지

**Ctrl + C** 키를 눌러 서버를 중지하세요.

---

**작성**: 2025-12-03

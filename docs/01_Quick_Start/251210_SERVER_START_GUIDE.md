# Backend Server 실행 가이드

## ✅ 간단한 방법 (권장)

**새로 만든 bat 파일 실행**:
```
start_backend.bat
```

더블클릭하면 됩니다!

---

## 📋 3가지 방법 설명

### ❌ 잘못된 이해
"3가지를 동시에 실행" → **NO!**

### ✅ 올바른 이해
"3가지 중 **하나만** 선택해서 실행" → **YES!**

---

## 방법 비교

### 1️⃣ start_server_localhost.bat (기존)
```batch
:: 기존 파일, 경로 확인 필요
```

### 2️⃣ backend 디렉토리에서 실행
```powershell
cd d:\code\ai-trading-system\backend
uvicorn main:app --reload --host 0.0.0.0 --port 8002
```

### 3️⃣ 프로젝트 루트에서 실행
```powershell
cd d:\code\ai-trading-system
uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8002
```

---

## 🆕 통합 솔루션 (추천)

**`start_backend.bat`** 파일을 만들었습니다:
- 자동으로 backend 디렉토리로 이동
- 의존성 확인/설치
- 서버 시작
- 끝!

### 사용법
```powershell
# 프로젝트 루트에서
.\start_backend.bat

# 또는 더블클릭
```

---

## 테스트 URL

서버 시작 후:

1. **Health Check**
   ```
   http://localhost:8002/news/realtime/health
   ```

2. **API 문서**
   ```
   http://localhost:8002/docs
   ```

3. **뉴스 가져오기**
   ```
   http://localhost:8002/news/realtime/latest?hours=24
   ```

---

## ⚠️ 문제 해결

### "ModuleNotFoundError: No module named 'fastapi'"
```powershell
pip install fastapi uvicorn[standard]
```

### 포트 8002 이미 사용 중
```powershell
# 다른 포트 사용
uvicorn main:app --reload --port 8002
```

### 404 에러
- 서버 재시작 (Ctrl+C 후 다시 실행)
- 브라우저 캐시 clear (Ctrl+Shift+R)

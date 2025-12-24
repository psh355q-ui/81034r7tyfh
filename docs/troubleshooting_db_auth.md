# 현재 상황 및 해결 방법

## 문제
DB 인증 실패가 계속 발생:
```
사용자 "ai_trading_user"의 password 인증을 실패했습니다
```

## 원인
**백엔드가 재시작되지 않음**
- WatchFiles는 Python 파일만 감지
- `.env` 파일 변경은 자동 재시작 안 됨
- 서버가 이전 설정으로 여전히 실행 중

## 해결 방법

### 1. 백엔드 재시작 (필수)
```bash
# 터미널에서 Ctrl+C 눌러서 서버 중지
# 그 다음 다시 실행
python run_backend.bat
```

### 2. 확인할 `.env` 설정
```dotenv
# Option A: postgres 사용자 (권장)
DB_USER=postgres
DB_PASSWORD=Qkqhdi1!
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ai_trading

# Option B: ai_trading_user (PostgreSQL에 사용자 생성 필요)
DB_USER=ai_trading_user
DB_PASSWORD=Qkqhdi1!
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ai_trading
```

### 3. PostgreSQL 사용자 생성 (Option B 선택 시)
```sql
psql -U postgres
CREATE USER ai_trading_user WITH PASSWORD 'Qkqhdi1!';
CREATE DATABASE ai_trading;
GRANT ALL PRIVILEGES ON DATABASE ai_trading TO ai_trading_user;
\q
```

## 재시작 후 테스트
```bash
# API 테스트
curl http://localhost:8001/api/weights/current
curl http://localhost:8001/api/alerts/summary
```

**참고**: DB 없이도 War Room은 정상 작동합니다 ✅

# Security Best Practices - AI Trading System

**작성일**: 2025-12-10
**문서 버전**: 1.0
**옵션**: Option 5 - 문서화 보완

---

## 📋 목차 (Table of Contents)

1. [개요](#개요)
2. [InputGuard 사용법](#inputguard-사용법)
3. [WebhookSecurity 사용법](#webhooksecurity-사용법)
4. [API 키 관리](#api-키-관리)
5. [데이터베이스 보안](#데이터베이스-보안)
6. [네트워크 보안](#네트워크-보안)
7. [로깅 및 모니터링](#로깅-및-모니터링)
8. [정기 보안 점검](#정기-보안-점검)

---

## 개요

AI Trading System은 **4계층 방어 시스템**으로 95% 방어율을 달성했습니다.

### 보안 계층 구조

```
Layer 1: InputGuard (입력 검증)
    ↓
Layer 2: API Key Validation (인증)
    ↓
Layer 3: Rate Limiting (속도 제한)
    ↓
Layer 4: WebhookSecurity (Webhook 검증)
```

### 주요 보안 기능

- ✅ SQL Injection 방어
- ✅ XSS (Cross-Site Scripting) 방어
- ✅ Path Traversal 방어
- ✅ Command Injection 방어
- ✅ HMAC 기반 Webhook 검증
- ✅ Rate Limiting (속도 제한)
- ✅ API 키 암호화 저장

---

## InputGuard 사용법

### 1. InputGuard란?

**InputGuard**는 모든 사용자 입력을 검증하여 보안 취약점을 사전에 차단하는 유틸리티입니다.

**위치**: `backend/utils/input_guard.py`

### 2. 기본 사용법

```python
from backend.utils.input_guard import InputGuard

# 티커 심볼 검증
ticker = InputGuard.validate_ticker("AAPL")
# ✅ 허용: "AAPL", "MSFT", "GOOGL"
# ❌ 거부: "'; DROP TABLE stocks;--", "../etc/passwd"

# 날짜 검증
date = InputGuard.validate_date("2024-12-01")
# ✅ 허용: "2024-12-01", "2023-01-15"
# ❌ 거부: "2024-13-32", "DROP TABLE", "' OR '1'='1"

# 숫자 범위 검증
price = InputGuard.validate_number(150.5, min_val=0, max_val=10000)
# ✅ 허용: 0 ~ 10000 사이 숫자
# ❌ 거부: 음수, 범위 초과, 문자열

# 텍스트 검증 (XSS 방어)
text = InputGuard.sanitize_text("<script>alert('XSS')</script>")
# ✅ 결과: "&lt;script&gt;alert('XSS')&lt;/script&gt;"
```

### 3. API 엔드포인트에서 사용

```python
from fastapi import APIRouter, HTTPException
from backend.utils.input_guard import InputGuard

router = APIRouter()

@router.get("/stock/{ticker}")
async def get_stock_data(ticker: str):
    # 입력 검증
    try:
        safe_ticker = InputGuard.validate_ticker(ticker)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 안전한 티커로 데이터베이스 조회
    data = await db.query(f"SELECT * FROM stocks WHERE ticker = '{safe_ticker}'")
    return data
```

### 4. 지원되는 검증 메서드

| 메서드 | 설명 | 예시 |
|--------|------|------|
| `validate_ticker(ticker)` | 주식 티커 검증 (영문 대문자 1-5자) | "AAPL" ✅, "123" ❌ |
| `validate_date(date_str)` | ISO 8601 날짜 형식 검증 | "2024-12-01" ✅ |
| `validate_number(num, min_val, max_val)` | 숫자 범위 검증 | 150 (0-1000) ✅ |
| `sanitize_text(text)` | HTML/스크립트 태그 이스케이프 | `<script>` → `&lt;script&gt;` |
| `validate_path(path)` | 경로 탐색 공격 방어 | "../etc/passwd" ❌ |
| `validate_email(email)` | 이메일 형식 검증 | "user@example.com" ✅ |

### 5. 커스텀 검증 추가

```python
# backend/utils/input_guard.py에 추가

@staticmethod
def validate_order_side(side: str) -> str:
    """주문 방향 검증 (BUY/SELL만 허용)"""
    allowed_sides = ["BUY", "SELL"]

    if side not in allowed_sides:
        raise ValueError(f"Invalid order side: {side}")

    return side
```

---

## WebhookSecurity 사용법

### 1. WebhookSecurity란?

**WebhookSecurity**는 외부 서비스(Telegram, Slack 등)로부터 받는 Webhook 요청을 HMAC 서명으로 검증합니다.

**위치**: `backend/utils/webhook_security.py`

### 2. 기본 사용법

```python
from backend.utils.webhook_security import WebhookSecurity

# Webhook Secret 설정 (환경 변수에서 로드)
webhook_secret = os.getenv("WEBHOOK_SECRET")
security = WebhookSecurity(webhook_secret)

# Webhook 검증
@router.post("/webhook/telegram")
async def telegram_webhook(request: Request):
    # 요청 본문과 서명 헤더 가져오기
    body = await request.body()
    signature = request.headers.get("X-Telegram-Signature")

    # 서명 검증
    if not security.verify_signature(body, signature):
        raise HTTPException(status_code=401, detail="Invalid signature")

    # 검증 통과 후 처리
    data = await request.json()
    await process_telegram_message(data)

    return {"status": "ok"}
```

### 3. HMAC 서명 생성 (외부 서비스 설정용)

Telegram/Slack에서 Webhook 발송 시 서명을 포함하도록 설정:

```python
import hmac
import hashlib

def generate_signature(payload: bytes, secret: str) -> str:
    """Webhook 서명 생성"""
    signature = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    return signature

# 예시: Telegram Bot에서 사용
payload = b'{"message": "Hello"}'
signature = generate_signature(payload, webhook_secret)

# HTTP 헤더에 추가
headers = {
    "X-Telegram-Signature": signature
}
```

### 4. 환경 변수 설정

```bash
# .env 파일
WEBHOOK_SECRET=your-random-secret-key-here-min-32-chars
```

**보안 팁**:
- Webhook Secret은 최소 32자 이상
- 영문 대소문자 + 숫자 + 특수문자 조합
- 정기적으로 갱신 (3개월마다)

### 5. Rate Limiting 적용

```python
from fastapi_limiter.depends import RateLimiter

@router.post("/webhook/telegram")
@limiter.limit("10/minute")  # 분당 10회 제한
async def telegram_webhook(request: Request):
    # Webhook 처리
    pass
```

---

## API 키 관리

### 1. API 키 저장 방식

**절대 하지 말 것**:
```python
# ❌ 코드에 직접 저장
API_KEY = "sk-1234567890abcdef"
```

**올바른 방법**:
```python
# ✅ 환경 변수 사용
import os
API_KEY = os.getenv("OPENAI_API_KEY")
```

### 2. 환경 변수 설정

```bash
# .env 파일 (절대 Git에 커밋하지 말 것!)
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx
KIS_APP_KEY=PSxxxxxxxxxxxxxxxx
KIS_APP_SECRET=xxxxxxxxxxxxxxxx
DATABASE_URL=postgresql://user:pass@localhost/db
REDIS_URL=redis://localhost:6379
```

**.gitignore에 추가**:
```
.env
.env.local
.env.production
```

### 3. API 키 암호화 저장 (선택)

```python
from cryptography.fernet import Fernet

# 암호화 키 생성 (한 번만 실행)
key = Fernet.generate_key()

# API 키 암호화
cipher = Fernet(key)
encrypted_api_key = cipher.encrypt(b"sk-1234567890abcdef")

# API 키 복호화
decrypted_api_key = cipher.decrypt(encrypted_api_key).decode()
```

### 4. API 키 권한 최소화

- **OpenAI**: 사용하는 모델만 활성화 (GPT-4, GPT-3.5)
- **KIS API**: 거래 권한은 모의투자 계좌로 먼저 테스트
- **Database**: Read-only 계정과 Write 계정 분리

---

## 데이터베이스 보안

### 1. SQL Injection 방어

**위험한 코드** (❌):
```python
# 사용자 입력을 직접 쿼리에 삽입
ticker = request.query_params.get("ticker")
query = f"SELECT * FROM stocks WHERE ticker = '{ticker}'"
result = db.execute(query)
```

**안전한 코드** (✅):
```python
# 파라미터 바인딩 사용
ticker = request.query_params.get("ticker")
query = "SELECT * FROM stocks WHERE ticker = :ticker"
result = db.execute(query, {"ticker": ticker})
```

### 2. 데이터베이스 접근 제어

```sql
-- Read-only 사용자 생성
CREATE USER app_readonly WITH PASSWORD 'secure_password';
GRANT SELECT ON ALL TABLES IN SCHEMA public TO app_readonly;

-- Write 사용자 생성
CREATE USER app_writer WITH PASSWORD 'secure_password';
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_writer;
```

### 3. 연결 문자열 보안

```python
# ❌ 평문 비밀번호
DATABASE_URL = "postgresql://user:password123@localhost/mydb"

# ✅ 환경 변수 사용
DATABASE_URL = os.getenv("DATABASE_URL")
```

---

## 네트워크 보안

### 1. HTTPS/TLS 사용

```python
# FastAPI HTTPS 설정
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=443,
        ssl_keyfile="/path/to/key.pem",
        ssl_certfile="/path/to/cert.pem"
    )
```

### 2. CORS 설정

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

### 3. 방화벽 설정

```bash
# UFW (Ubuntu)
sudo ufw allow 443/tcp  # HTTPS
sudo ufw allow 22/tcp   # SSH
sudo ufw deny 5432/tcp  # PostgreSQL (외부 접근 차단)
sudo ufw enable
```

---

## 로깅 및 모니터링

### 1. 보안 이벤트 로깅

```python
import logging

logger = logging.getLogger("security")

# 의심스러운 활동 로깅
@router.post("/api/trade")
async def execute_trade(request: Request):
    try:
        data = await request.json()
        ticker = InputGuard.validate_ticker(data['ticker'])
    except ValueError as e:
        # 보안 경고 로깅
        logger.warning(
            f"Security violation: Invalid ticker from {request.client.host}",
            extra={"ip": request.client.host, "input": data.get('ticker')}
        )
        raise HTTPException(status_code=400, detail="Invalid input")
```

### 2. 실패한 로그인 모니터링

```python
failed_login_attempts = defaultdict(int)

@router.post("/login")
async def login(username: str, password: str, request: Request):
    ip = request.client.host

    if not verify_credentials(username, password):
        failed_login_attempts[ip] += 1

        # 5회 실패 시 IP 차단
        if failed_login_attempts[ip] >= 5:
            logger.critical(f"Possible brute force attack from {ip}")
            # IP 차단 로직

        raise HTTPException(status_code=401, detail="Invalid credentials")
```

### 3. Grafana 알림 설정

```yaml
# grafana/alerts.yml
alerts:
  - name: Security Violation
    condition: rate(security_violations_total[5m]) > 10
    notification: slack
    message: "High rate of security violations detected"
```

---

## 정기 보안 점검

### 매주 체크리스트

- [ ] 의심스러운 로그 확인 (`/var/log/security.log`)
- [ ] 실패한 로그인 시도 검토
- [ ] Rate Limiting 통계 확인
- [ ] 데이터베이스 접근 로그 검토

### 매월 체크리스트

- [ ] API 키 갱신 확인
- [ ] 의존성 보안 업데이트 (`pip install --upgrade`)
- [ ] SSL 인증서 만료일 확인
- [ ] 백업 암호화 상태 확인

### 분기별 체크리스트

- [ ] Webhook Secret 갱신
- [ ] 전체 보안 감사 (Penetration Testing)
- [ ] 사용자 권한 검토
- [ ] 재해 복구 훈련

---

## 보안 사고 대응

### 1. API 키 유출 시

```bash
# 즉시 API 키 무효화
# OpenAI Dashboard: https://platform.openai.com/api-keys
# KIS Dashboard: https://apiportal.koreainvestment.com

# 새 키 발급 및 환경 변수 업데이트
vim .env
# API_KEY=new-key-here

# 서비스 재시작
docker-compose restart
```

### 2. 데이터베이스 침해 의심 시

```bash
# 데이터베이스 연결 차단
sudo ufw deny 5432/tcp

# 백업 복원
psql < backup.sql

# 비밀번호 변경
ALTER USER app_user WITH PASSWORD 'new_secure_password';
```

### 3. DDoS 공격 시

```bash
# Nginx Rate Limiting 활성화
limit_req_zone $binary_remote_addr zone=one:10m rate=1r/s;

# CloudFlare 활성화 (권장)
```

---

## 참고 자료

- **OWASP Top 10**: https://owasp.org/www-project-top-ten/
- **FastAPI Security**: https://fastapi.tiangolo.com/tutorial/security/
- **PostgreSQL Security**: https://www.postgresql.org/docs/current/auth-pg-hba-conf.html

---

**문서 버전**: 1.0
**최종 업데이트**: 2025-12-10
**작성자**: AI Trading System Team

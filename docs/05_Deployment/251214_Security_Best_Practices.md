# Security Best Practices - AI Trading System

**Last Updated**: 2025-12-14
**Category**: Deployment & Security
**Audience**: Developers, DevOps, System Administrators

---

## 📋 목차

1. [개요](#개요)
2. [환경 변수 보안](#환경-변수-보안)
3. [API 키 관리](#api-키-관리)
4. [데이터베이스 보안](#데이터베이스-보안)
5. [네트워크 보안](#네트워크-보안)
6. [인증 및 권한](#인증-및-권한)
7. [로깅 및 모니터링](#로깅-및-모니터링)
8. [프로덕션 체크리스트](#프로덕션-체크리스트)

---

## 개요

AI Trading System은 금융 데이터와 거래를 다루므로 보안이 매우 중요합니다. 이 가이드는 시스템을 안전하게 운영하기 위한 모범 사례를 제공합니다.

### 보안 원칙

1. **최소 권한 원칙**: 필요한 최소한의 권한만 부여
2. **심층 방어**: 여러 계층의 보안 조치
3. **암호화**: 전송 중/저장 중 데이터 암호화
4. **감사 추적**: 모든 중요 작업 로깅
5. **정기 점검**: 보안 취약점 주기적 검토

---

## 환경 변수 보안

### 1. .env 파일 관리

#### ✅ DO (해야 할 것)

```bash
# .env 파일을 .gitignore에 추가
echo ".env" >> .gitignore

# 강력한 비밀키 생성
openssl rand -hex 32  # SECRET_KEY
openssl rand -base64 32  # TIMESCALE_PASSWORD

# 파일 권한 제한 (Linux/Mac)
chmod 600 .env
```

#### ❌ DON'T (하지 말아야 할 것)

```bash
# 절대 Git에 커밋하지 말 것
git add .env  # ❌ NEVER!

# 기본값 사용 금지
SECRET_KEY=CHANGE_THIS_SECRET_KEY_IMMEDIATELY  # ❌ 변경 필수!
TIMESCALE_PASSWORD=CHANGE_THIS_STRONG_PASSWORD  # ❌ 변경 필수!
```

### 2. 필수 변경 사항

프로덕션 배포 전 반드시 변경:

```bash
# .env 파일에서 다음 값 변경 필수
SECRET_KEY=<openssl rand -hex 32 출력값>
TIMESCALE_PASSWORD=<openssl rand -base64 32 출력값>
GRAFANA_PASSWORD=<강력한 비밀번호>
REDIS_PASSWORD=<강력한 비밀번호>

# DB 사용자 비밀번호
DB_PASSWORD=<강력한 비밀번호>
```

### 3. 환경별 설정

```bash
# 개발 환경
APP_ENV=development
APP_DEBUG=true

# 프로덕션 환경
APP_ENV=production
APP_DEBUG=false  # 반드시 false!
```

---

## API 키 관리

### 1. API 키 저장

#### ✅ 안전한 방법

```python
# backend/auth.py
import os
from typing import Optional

class APIKeyConfig:
    """API 키 중앙 관리"""

    def __init__(self):
        # 환경 변수에서만 로드
        self.claude_api_key = os.getenv("CLAUDE_API_KEY")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")

        # KIS API (한국투자증권)
        self.kis_app_key = os.getenv("KIS_APP_KEY")
        self.kis_app_secret = os.getenv("KIS_APP_SECRET")

    def validate(self) -> bool:
        """필수 API 키 존재 여부 확인"""
        required = [
            self.claude_api_key,
            self.gemini_api_key,
        ]
        return all(required)
```

#### ❌ 위험한 방법

```python
# 코드에 직접 하드코딩 ❌
CLAUDE_API_KEY = "sk-ant-xxxxxxxxxxxxx"  # 절대 금지!

# 주석에 API 키 ❌
# My Claude API key: sk-ant-xxxxxxxxxxxxx  # 절대 금지!

# 로그에 출력 ❌
logger.info(f"Using API key: {api_key}")  # 절대 금지!
```

### 2. API 키 로테이션

```bash
# 정기적으로 API 키 교체 (권장: 3개월마다)
# 1. 새 API 키 발급
# 2. .env 파일 업데이트
# 3. 서비스 재시작
# 4. 이전 API 키 비활성화
```

### 3. InputGuard 사용

시스템에 내장된 InputGuard를 사용하여 민감 정보 필터링:

```python
# backend/security/input_guard.py 활용
from backend.security.input_guard import InputGuard

guard = InputGuard()

# API 키가 포함될 수 있는 입력 검증
safe_input = guard.sanitize(user_input)

# 로깅 시 자동 마스킹
logger.info(guard.mask_sensitive_data(message))
```

---

## 데이터베이스 보안

### 1. PostgreSQL 보안

#### 비밀번호 정책

```bash
# 강력한 비밀번호 생성
openssl rand -base64 32

# .env 설정
DB_PASSWORD=<생성된 강력한 비밀번호>
TIMESCALE_PASSWORD=<생성된 강력한 비밀번호>
```

#### 접근 제어

```yaml
# docker-compose.yml
services:
  postgres:
    image: timescale/timescaledb:latest-pg15
    environment:
      POSTGRES_PASSWORD: ${TIMESCALE_PASSWORD}
    ports:
      - "127.0.0.1:5432:5432"  # localhost만 접근 가능
```

### 2. Redis 보안

```yaml
# docker-compose.yml
services:
  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    ports:
      - "127.0.0.1:6379:6379"  # localhost만 접근 가능
```

```bash
# .env
REDIS_PASSWORD=<강력한 비밀번호>
REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
```

### 3. SQL Injection 방지

#### ✅ 안전한 쿼리

```python
# Pydantic + SQLAlchemy 사용 (파라미터화된 쿼리)
from sqlalchemy import select

# 안전: 파라미터 바인딩 사용
stmt = select(User).where(User.email == user_email)
result = await session.execute(stmt)
```

#### ❌ 위험한 쿼리

```python
# 절대 사용 금지: 문자열 포맷팅
query = f"SELECT * FROM users WHERE email = '{user_email}'"  # ❌ SQL Injection 위험!
```

---

## 네트워크 보안

### 1. CORS 설정

```python
# backend/main.py
from fastapi.middleware.cors import CORSMiddleware

# 개발 환경: 모든 origin 허용
if os.getenv("APP_ENV") == "development":
    origins = ["*"]
else:
    # 프로덕션: 특정 도메인만 허용
    origins = [
        "https://yourdomain.com",
        "https://www.yourdomain.com",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

### 2. 방화벽 설정

```bash
# 프로덕션 서버 (NAS)
# 필요한 포트만 개방
PORT  SERVICE         ACCESS
8001  Backend API     LAN only
3002  Frontend        LAN only
5432  PostgreSQL      localhost only
6379  Redis           localhost only
9200  Elasticsearch   localhost only
5601  Kibana          LAN only
```

### 3. HTTPS 설정

```nginx
# nginx.conf (프로덕션)
server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;

    # 강력한 SSL 설정
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    location / {
        proxy_pass http://backend:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 인증 및 권한

### 1. JWT 토큰 보안

```python
# backend/auth.py
from datetime import datetime, timedelta
from jose import JWTError, jwt

SECRET_KEY = os.getenv("SECRET_KEY")  # 환경 변수에서만
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # 짧게 유지

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
```

### 2. API 키 인증

```python
# backend/api/dependencies.py
from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(api_key: str = Security(api_key_header)):
    """API 키 검증"""
    valid_keys = os.getenv("VALID_API_KEYS", "").split(",")

    if not api_key or api_key not in valid_keys:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key"
        )
    return api_key
```

### 3. Rate Limiting

```python
# backend/middleware/rate_limit.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.get("/api/expensive-operation")
@limiter.limit("10/minute")  # 분당 10회 제한
async def expensive_operation():
    ...
```

---

## 로깅 및 모니터링

### 1. 보안 로깅

```python
# backend/core/logging_config.py 활용
from backend.core.logging_config import get_logger

logger = get_logger(__name__)

# 로그인 시도 기록
logger.warning(
    "Failed login attempt",
    user_email=email,
    ip_address=request.client.host,
    timestamp=datetime.utcnow()
)

# API 키 사용 기록 (키 값은 제외)
logger.info(
    "API key used",
    key_id=api_key[:8] + "...",  # 일부만 로깅
    endpoint=request.url.path
)
```

### 2. 민감 정보 마스킹

```python
# 로그에서 자동으로 민감 정보 제거
import re

def mask_sensitive_data(text: str) -> str:
    """민감 정보 마스킹"""
    patterns = {
        r'sk-ant-[a-zA-Z0-9]{40,}': 'sk-ant-***MASKED***',  # Claude API
        r'sk-proj-[a-zA-Z0-9]{40,}': 'sk-proj-***MASKED***',  # OpenAI API
        r'\d{3}-\d{2}-\d{4}': '***-**-****',  # SSN
        r'\d{4}-\d{4}-\d{4}-\d{4}': '****-****-****-****',  # Card
    }

    for pattern, replacement in patterns.items():
        text = re.sub(pattern, replacement, text)

    return text
```

### 3. 이상 탐지

```python
# 비정상적인 활동 감지
class SecurityMonitor:
    def detect_anomalies(self, user_id: str, action: str):
        """이상 행위 감지"""
        # 짧은 시간 내 과도한 요청
        request_count = self.get_request_count(user_id, minutes=5)
        if request_count > 100:
            logger.error(
                "Possible attack detected",
                user_id=user_id,
                request_count=request_count
            )
            self.alert_admin()

        # 비정상 시간대 접근
        if self.is_unusual_time():
            logger.warning(
                "Unusual access time",
                user_id=user_id,
                hour=datetime.utcnow().hour
            )
```

---

## 프로덕션 체크리스트

### 배포 전 필수 확인

#### 1. 환경 변수

- [ ] `SECRET_KEY` 변경됨
- [ ] `TIMESCALE_PASSWORD` 변경됨
- [ ] `GRAFANA_PASSWORD` 변경됨
- [ ] `REDIS_PASSWORD` 설정됨
- [ ] `DB_PASSWORD` 변경됨
- [ ] `APP_ENV=production` 설정
- [ ] `APP_DEBUG=false` 설정
- [ ] API 키 모두 설정됨 (Claude, Gemini, etc.)

#### 2. CORS 설정

- [ ] `FRONTEND_URLS` 프로덕션 도메인으로 설정
- [ ] 개발용 `*` origin 제거됨

#### 3. 데이터베이스

- [ ] PostgreSQL 비밀번호 변경됨
- [ ] 외부 접근 차단 (127.0.0.1만)
- [ ] 백업 설정됨

#### 4. 네트워크

- [ ] HTTPS 설정됨
- [ ] 방화벽 규칙 적용됨
- [ ] 불필요한 포트 닫힘

#### 5. 모니터링

- [ ] ELK Stack 설정됨
- [ ] 보안 로그 수집 중
- [ ] Alert 설정됨

#### 6. Kill Switch

- [ ] `KILL_SWITCH_ENABLED=true`
- [ ] `KILL_SWITCH_DAILY_LOSS_PCT` 적절히 설정 (권장: 2.0)

---

## 보안 사고 대응

### 1. API 키 유출 시

```bash
# 즉시 조치
1. 해당 API 키 비활성화
2. 새 API 키 발급
3. .env 파일 업데이트
4. 서비스 재시작
5. 로그 확인 (유출된 키 사용 내역)
6. Git 히스토리 정리 (git filter-branch)
```

### 2. 비인가 접근 탐지 시

```bash
# 즉시 조치
1. 의심스러운 IP 차단
2. 모든 세션 무효화
3. 비밀번호 재설정
4. 로그 분석
5. 취약점 패치
```

### 3. 데이터 유출 의심 시

```bash
# 즉시 조치
1. 서비스 일시 중단
2. DB 백업
3. 로그 수집 및 분석
4. 영향 범위 파악
5. 사용자 통보 (필요시)
6. 당국 신고 (필요시)
```

---

## 보안 도구

### 1. 취약점 스캔

```bash
# Python 패키지 취약점 검사
pip install safety
safety check

# Docker 이미지 스캔
docker scan ai-trading-backend:latest

# Trivy 스캔 (CI/CD에 포함됨)
trivy fs .
```

### 2. 비밀 정보 스캔

```bash
# Git 히스토리에서 비밀 정보 검색
pip install detect-secrets
detect-secrets scan > .secrets.baseline
```

### 3. 코드 보안 검사

```bash
# Bandit (Python 보안 검사)
pip install bandit
bandit -r backend/

# Semgrep
pip install semgrep
semgrep --config auto backend/
```

---

## 참고 자료

### 보안 표준
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CWE Top 25](https://cwe.mitre.org/top25/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)

### FastAPI 보안
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [FastAPI CORS](https://fastapi.tiangolo.com/tutorial/cors/)

### Python 보안
- [Python Security Best Practices](https://python.readthedocs.io/en/latest/library/security_warnings.html)
- [PEP 543](https://www.python.org/dev/peps/pep-0543/) - TLS/SSL

---

## 정기 보안 점검

### 월간 점검

- [ ] 모든 패키지 업데이트 확인
- [ ] 보안 패치 적용
- [ ] 로그 리뷰
- [ ] 접근 권한 검토

### 분기별 점검

- [ ] API 키 로테이션
- [ ] 비밀번호 변경
- [ ] 백업 복원 테스트
- [ ] 침투 테스트 (선택)

### 연간 점검

- [ ] 전체 보안 감사
- [ ] 재해 복구 훈련
- [ ] 보안 정책 업데이트

---

**Last Updated**: 2025-12-14
**Maintained by**: AI Trading System Team
**Classification**: Internal Use Only

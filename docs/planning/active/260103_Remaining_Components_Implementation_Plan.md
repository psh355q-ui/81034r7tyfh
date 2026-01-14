# Claude Code Templates 남은 컴포넌트 구현 계획

**작성일**: 2026-01-03
**기준**: 2026-01-02 작업 완료 후
**우선순위**: P2-P3 (Medium to Low Priority)
**상태**: 📋 Ready for Planning

---

## Executive Summary

Claude Code Templates 중 아직 구현 계획을 세우지 않은 **13개 컴포넌트**에 대한 통합 구현 계획입니다.

**이미 계획 완료된 컴포넌트 (별도 문서):**
- ✅ `/generate-tests` Command - [260103_Claude_Code_Templates_Implementation_Plan.md](260103_Claude_Code_Templates_Implementation_Plan.md)
- ✅ React Performance Optimizer Agent - 상동
- ✅ Auto Git Hooks - 상동
- ✅ Database Architect Agent - [260102_Database_Optimization_Plan.md](260102_Database_Optimization_Plan.md)

**남은 컴포넌트 (본 문서):**
- **High Priority (6개)**: Security Auditor, DevOps Engineer, 4개 Commands, 2개 MCPs, 2개 Settings, 2개 Hooks
- **Medium Priority (7개)**: Data Scientist, NLP Engineer, 2개 MCPs, 2개 Skills

---

## 현재 시스템 상태 (2026-01-03 기준)

### 보안 현황
- ❌ API 키 관리: .env 파일에 평문 저장
- ❌ 보안 스캔: 정기적 감사 없음
- ❌ OWASP Top 10: 미검증
- ⚠️ OpenAI API 할당량 초과 발생 (2026-01-02 이전)
- ✅ Kill Switch 시스템 구현 완료 (2026-01-02)

### DevOps 현황
- ❌ CI/CD: GitHub Actions 기본만 구성 (테스트 미실행)
- ❌ 자동 배포: 없음
- ❌ 모니터링: 수동 확인만 가능
- ✅ Docker Compose: 구성 완료
- ✅ Shadow Trading 모니터링 스크립트 (2026-01-02)

### 데이터 분석 현황
- ⚠️ Shadow Trading 분석: 수동 스크립트만 존재
- ❌ 백테스팅 통계: 기본 메트릭만 (Win Rate, PF, MDD)
- ❌ Agent 성과 분석: 자동화 없음
- ✅ War Room MVP: 12.76초 응답 (성능 목표 달성)

### NLP/AI 현황
- ⚠️ 뉴스 감성 분석: Gemini API 기반 (할당량 제한)
- ❌ 티커 추출: 정확도 60% 추정
- ❌ 로컬 임베딩: 미구현 (OpenAI Embedding 의존)
- ✅ News Aggregation 정상 작동

---

## Component Group 1: Security & Compliance (보안 및 규정 준수)

### 1.1 Security Auditor Agent

**목표**: 자동화된 보안 감사 시스템 구축

**설치 방법**:
```bash
npx claude-code-templates@latest --agent security-auditor --yes
```

**적용 전략**:

#### Phase 1A: API 키 보안 강화

**현재 문제**:
```python
# .env 파일 (평문 저장)
OPENAI_API_KEY=sk-proj-xxxxx
GEMINI_API_KEY=AIzaSyxxxxx
KIS_APP_KEY=PSxxxxx
KIS_APP_SECRET=xxxxx
DATABASE_URL=postgresql://user:password@localhost:5433/trading
```

**해결 방법**:

**1. Secrets 암호화**

**파일**: `backend/config/secrets_manager.py` (신규)

```python
"""
Secrets Manager - 환경 변수 암호화 저장

Date: 2026-01-03
Phase: Security Enhancement
"""
import os
from cryptography.fernet import Fernet
from pathlib import Path
import json

class SecretsManager:
    """암호화된 시크릿 관리"""

    def __init__(self, key_file: str = ".secrets.key"):
        self.key_file = Path(key_file)
        self.secrets_file = Path(".secrets.enc")
        self.key = self._load_or_create_key()
        self.fernet = Fernet(self.key)

    def _load_or_create_key(self) -> bytes:
        """암호화 키 로드 또는 생성"""
        if self.key_file.exists():
            return self.key_file.read_bytes()

        # 새 키 생성
        key = Fernet.generate_key()
        self.key_file.write_bytes(key)
        self.key_file.chmod(0o600)  # 소유자만 읽기 가능
        return key

    def encrypt_secrets(self, secrets: dict) -> None:
        """시크릿 암호화 저장"""
        json_data = json.dumps(secrets).encode()
        encrypted = self.fernet.encrypt(json_data)
        self.secrets_file.write_bytes(encrypted)
        self.secrets_file.chmod(0o600)

    def decrypt_secrets(self) -> dict:
        """시크릿 복호화 로드"""
        if not self.secrets_file.exists():
            raise FileNotFoundError("Encrypted secrets file not found")

        encrypted = self.secrets_file.read_bytes()
        decrypted = self.fernet.decrypt(encrypted)
        return json.loads(decrypted.decode())

    def get_secret(self, key: str, default=None):
        """개별 시크릿 조회"""
        secrets = self.decrypt_secrets()
        return secrets.get(key, default)

# 사용 예시
secrets_manager = SecretsManager()

# 초기 암호화 (한 번만 실행)
secrets_manager.encrypt_secrets({
    "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
    "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY"),
    "KIS_APP_KEY": os.getenv("KIS_APP_KEY"),
    "KIS_APP_SECRET": os.getenv("KIS_APP_SECRET"),
    "DATABASE_URL": os.getenv("DATABASE_URL")
})

# 런타임 사용
openai_key = secrets_manager.get_secret("OPENAI_API_KEY")
```

**2. .env 파일 제거 및 마이그레이션 스크립트**

**파일**: `scripts/migrate_secrets.py` (신규)

```python
#!/usr/bin/env python3
"""
.env → 암호화된 secrets 마이그레이션

Usage:
    python scripts/migrate_secrets.py
"""
from dotenv import load_dotenv
import os
from backend.config.secrets_manager import SecretsManager

def migrate():
    # 기존 .env 로드
    load_dotenv()

    secrets = {
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY"),
        "KIS_APP_KEY": os.getenv("KIS_APP_KEY"),
        "KIS_APP_SECRET": os.getenv("KIS_APP_SECRET"),
        "DATABASE_URL": os.getenv("DATABASE_URL"),
        "TELEGRAM_BOT_TOKEN": os.getenv("TELEGRAM_BOT_TOKEN"),
        "TELEGRAM_CHAT_ID": os.getenv("TELEGRAM_CHAT_ID")
    }

    # 암호화 저장
    manager = SecretsManager()
    manager.encrypt_secrets(secrets)

    print("✅ Secrets encrypted successfully")
    print("⚠️  Please backup .secrets.key securely")
    print("⚠️  Add .secrets.key to .gitignore")
    print("⚠️  Remove .env file after verification")

if __name__ == "__main__":
    migrate()
```

**3. .gitignore 업데이트**

```bash
# .gitignore
.env
.secrets.key
.secrets.enc
```

**예상 효과**: API 키 노출 위험 100% 제거

---

#### Phase 1B: OWASP Top 10 자동 스캔

**파일**: `scripts/security_audit.py` (신규)

```python
#!/usr/bin/env python3
"""
OWASP Top 10 자동 보안 스캔

Checks:
1. SQL Injection
2. XSS (Cross-Site Scripting)
3. Broken Authentication
4. Sensitive Data Exposure
5. XML External Entities (XXE)
6. Broken Access Control
7. Security Misconfiguration
8. Insecure Deserialization
9. Using Components with Known Vulnerabilities
10. Insufficient Logging & Monitoring
"""
import re
from pathlib import Path
from typing import List, Dict

class SecurityAuditor:
    """보안 감사 도구"""

    def __init__(self, base_path: str = "."):
        self.base_path = Path(base_path)
        self.issues = []

    def scan_sql_injection(self) -> List[Dict]:
        """SQL Injection 취약점 스캔"""
        issues = []

        # repository.py 스캔
        repo_files = self.base_path.glob("backend/database/*.py")

        for file in repo_files:
            content = file.read_text()

            # 위험 패턴: f-string 또는 % 포맷팅
            if re.search(r'f".*SELECT.*{.*}"', content):
                issues.append({
                    "type": "SQL_INJECTION",
                    "severity": "HIGH",
                    "file": str(file),
                    "message": "Potential SQL injection via f-string"
                })

            if re.search(r'%.*SELECT', content):
                issues.append({
                    "type": "SQL_INJECTION",
                    "severity": "HIGH",
                    "file": str(file),
                    "message": "Potential SQL injection via % formatting"
                })

        return issues

    def scan_xss(self) -> List[Dict]:
        """XSS 취약점 스캔"""
        issues = []

        # 프론트엔드 파일 스캔
        tsx_files = self.base_path.glob("frontend/src/**/*.tsx")

        for file in tsx_files:
            content = file.read_text()

            # dangerouslySetInnerHTML 사용
            if "dangerouslySetInnerHTML" in content:
                issues.append({
                    "type": "XSS",
                    "severity": "MEDIUM",
                    "file": str(file),
                    "message": "dangerouslySetInnerHTML detected - verify sanitization"
                })

        return issues

    def scan_secrets_exposure(self) -> List[Dict]:
        """시크릿 노출 스캔"""
        issues = []

        # 모든 Python 파일 스캔
        py_files = self.base_path.glob("**/*.py")

        secret_patterns = [
            (r'sk-[a-zA-Z0-9]{48}', 'OpenAI API Key'),
            (r'AIzaSy[a-zA-Z0-9_-]{33}', 'Google API Key'),
            (r'ghp_[a-zA-Z0-9]{36}', 'GitHub Token'),
            (r'postgresql://[^:]+:[^@]+@', 'Database Password in URL')
        ]

        for file in py_files:
            if '.venv' in str(file) or 'node_modules' in str(file):
                continue

            content = file.read_text()

            for pattern, secret_type in secret_patterns:
                if re.search(pattern, content):
                    issues.append({
                        "type": "SECRET_EXPOSURE",
                        "severity": "CRITICAL",
                        "file": str(file),
                        "message": f"Potential {secret_type} hardcoded"
                    })

        return issues

    def scan_broken_access_control(self) -> List[Dict]:
        """접근 제어 취약점 스캔"""
        issues = []

        # API 라우터 스캔
        router_files = self.base_path.glob("backend/api/*_router.py")

        for file in router_files:
            content = file.read_text()

            # DELETE 엔드포인트에 인증 없음
            if re.search(r'@router\.delete\(.*\)\s+async def', content):
                if 'Depends(get_current_user)' not in content:
                    issues.append({
                        "type": "BROKEN_ACCESS_CONTROL",
                        "severity": "HIGH",
                        "file": str(file),
                        "message": "DELETE endpoint without authentication"
                    })

        return issues

    def run_full_audit(self) -> Dict:
        """전체 보안 감사 실행"""
        all_issues = []

        all_issues.extend(self.scan_sql_injection())
        all_issues.extend(self.scan_xss())
        all_issues.extend(self.scan_secrets_exposure())
        all_issues.extend(self.scan_broken_access_control())

        # 심각도별 분류
        critical = [i for i in all_issues if i['severity'] == 'CRITICAL']
        high = [i for i in all_issues if i['severity'] == 'HIGH']
        medium = [i for i in all_issues if i['severity'] == 'MEDIUM']

        return {
            "total_issues": len(all_issues),
            "critical": len(critical),
            "high": len(high),
            "medium": len(medium),
            "issues": all_issues
        }

# 사용
if __name__ == "__main__":
    auditor = SecurityAuditor()
    results = auditor.run_full_audit()

    print(f"🔍 Security Audit Results")
    print(f"Total Issues: {results['total_issues']}")
    print(f"  Critical: {results['critical']}")
    print(f"  High: {results['high']}")
    print(f"  Medium: {results['medium']}")

    if results['critical'] > 0:
        print("\n❌ CRITICAL ISSUES FOUND:")
        for issue in results['issues']:
            if issue['severity'] == 'CRITICAL':
                print(f"  {issue['file']}: {issue['message']}")
```

**예상 소요**: 4시간
**예상 효과**: 보안 취약점 자동 감지, OWASP Top 10 준수

---

#### Phase 1C: `/check-security` Command 통합

**설치**:
```bash
npx claude-code-templates@latest --command check-security --yes
```

**사용**:
```bash
# 전체 코드베이스 스캔
/check-security

# 특정 파일 스캔
/check-security backend/api/war_room_router.py
```

**예상 효과**: 커밋 전 자동 보안 검사

---

### 1.2 구현 로드맵 (보안)

**Week 1: Secrets 암호화**
- [ ] SecretsManager 클래스 구현
- [ ] 마이그레이션 스크립트 작성
- [ ] .env → .secrets.enc 전환
- [ ] .gitignore 업데이트

**Week 2: 보안 감사 자동화**
- [ ] SecurityAuditor 구현
- [ ] OWASP Top 10 스캔 로직
- [ ] GitHub Actions 통합
- [ ] `/check-security` 명령 설치

**Week 3: 지속적 모니터링**
- [ ] 주간 보안 스캔 스케줄
- [ ] Telegram 알림 통합
- [ ] 보안 대시보드 구축

**예상 효과**:
- API 키 노출 위험: 100% → 0%
- OWASP Top 10 준수: 0% → 90%
- 보안 취약점 발견 시간: 수동 → 자동 (즉시)

---

## Component Group 2: DevOps & CI/CD (배포 자동화)

### 2.1 DevOps Engineer Agent

**목표**: CI/CD 파이프라인 구축 및 자동 배포

**설치 방법**:
```bash
npx claude-code-templates@latest --agent devops-engineer --yes
```

**적용 전략**:

#### Phase 2A: GitHub Actions CI/CD 파이프라인

**현재 상태**:
```yaml
# .github/workflows/ - 기본만 존재
- ci.yml (테스트 미실행)
```

**목표 파이프라인**:
```
Push → Lint → Test → Build → Deploy (Staging) → Deploy (Production)
```

**파일**: `.github/workflows/ci-cd.yml` (신규)

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  lint:
    name: Code Linting
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd backend
          pip install flake8 black mypy

      - name: Lint with flake8
        run: |
          cd backend
          flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics

      - name: Check formatting with black
        run: |
          cd backend
          black --check .

      - name: Type check with mypy
        run: |
          cd backend
          mypy --ignore-missing-imports .

  test-backend:
    name: Backend Tests
    runs-on: ubuntu-latest
    needs: lint

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: trading_test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest pytest-cov pytest-asyncio

      - name: Run tests with coverage
        env:
          DATABASE_URL: postgresql://test:test@localhost:5432/trading_test
        run: |
          cd backend
          pytest --cov=. --cov-report=xml --cov-report=term

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: ./backend/coverage.xml
          flags: backend

  test-frontend:
    name: Frontend Tests
    runs-on: ubuntu-latest
    needs: lint

    steps:
      - uses: actions/checkout@v3

      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install dependencies
        run: |
          cd frontend
          npm ci

      - name: Run tests
        run: |
          cd frontend
          npm test -- --coverage

      - name: Build
        run: |
          cd frontend
          npm run build

  security-scan:
    name: Security Scan
    runs-on: ubuntu-latest
    needs: [test-backend, test-frontend]

    steps:
      - uses: actions/checkout@v3

      - name: Run security audit
        run: |
          python scripts/security_audit.py

  deploy-staging:
    name: Deploy to Staging
    runs-on: ubuntu-latest
    needs: [security-scan]
    if: github.ref == 'refs/heads/develop'

    steps:
      - uses: actions/checkout@v3

      - name: Deploy to Staging
        run: |
          echo "🚀 Deploying to Staging..."
          # Docker Compose 배포 스크립트
          # ssh staging-server "cd /app && docker-compose pull && docker-compose up -d"

      - name: Health Check
        run: |
          sleep 10
          curl -f http://staging.example.com/health || exit 1

  deploy-production:
    name: Deploy to Production
    runs-on: ubuntu-latest
    needs: [security-scan]
    if: github.ref == 'refs/heads/main'

    steps:
      - uses: actions/checkout@v3

      - name: Deploy to Production
        run: |
          echo "🚀 Deploying to Production..."
          # Blue-Green 배포
          # 1. 새 컨테이너 시작 (Green)
          # 2. Health Check
          # 3. 트래픽 전환
          # 4. 이전 컨테이너 종료 (Blue)

      - name: Rollback on Failure
        if: failure()
        run: |
          echo "❌ Deployment failed, rolling back..."
          # 이전 버전으로 롤백
```

**예상 소요**: 6시간
**예상 효과**: 배포 시간 60분 → 5분, 자동화된 테스트/배포

---

#### Phase 2B: `/setup-ci-cd-pipeline` Command

**설치**:
```bash
npx claude-code-templates@latest --command setup-ci-cd-pipeline --yes
```

**사용**:
```bash
# 자동 CI/CD 설정
/setup-ci-cd-pipeline

# 생성되는 파일:
# - .github/workflows/ci-cd.yml
# - .github/workflows/deploy-staging.yml
# - .github/workflows/deploy-production.yml
# - scripts/deploy.sh
```

---

#### Phase 2C: Docker 최적화

**현재 docker-compose.yml 개선**

**파일**: `docker-compose.yml`

```yaml
version: '3.8'

services:
  postgres:
    image: timescale/timescaledb:latest-pg15
    container_name: trading-postgres
    environment:
      POSTGRES_USER: ${DB_USER:-trading}
      POSTGRES_PASSWORD: ${DB_PASSWORD:-trading123}
      POSTGRES_DB: ${DB_NAME:-ai_trading}
    ports:
      - "5433:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backend/database/migrations:/docker-entrypoint-initdb.d
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U trading"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: trading-backend
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      DATABASE_URL: postgresql://trading:trading123@postgres:5432/ai_trading
    ports:
      - "8001:8000"
    volumes:
      - ./backend:/app
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: trading-frontend
    depends_on:
      - backend
    ports:
      - "3002:3000"
    environment:
      VITE_API_URL: http://localhost:8001
    volumes:
      - ./frontend:/app
      - /app/node_modules
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    container_name: trading-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
  redis_data:
```

**Dockerfile 최적화** (Backend)

**파일**: `backend/Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 설치 (레이어 캐싱)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 헬스체크 스크립트
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 비루트 사용자로 실행
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**예상 효과**: 컨테이너 시작 시간 30초 → 10초, 헬스체크 자동화

---

### 2.2 구현 로드맵 (DevOps)

**Week 1: CI 파이프라인**
- [ ] GitHub Actions 워크플로우 작성
- [ ] Lint/Test 단계 구성
- [ ] 커버리지 리포트 통합

**Week 2: CD 파이프라인**
- [ ] Staging 배포 자동화
- [ ] Production 배포 (Blue-Green)
- [ ] 롤백 메커니즘

**Week 3: Docker 최적화**
- [ ] Dockerfile 멀티스테이지 빌드
- [ ] docker-compose 헬스체크
- [ ] Redis 캐싱 통합

**Week 4: 모니터링**
- [ ] 배포 알림 (Telegram)
- [ ] 에러 추적 (Sentry 통합)
- [ ] 성능 모니터링 대시보드

**예상 효과**:
- 배포 시간: 60분 → 5분
- 테스트 커버리지: 자동 측정 및 리포트
- 롤백 시간: 수동 30분 → 자동 2분

---

## Component Group 3: Performance & Monitoring (성능 및 모니터링)

### 3.1 `/performance-audit` Command

**목표**: 코드 성능 자동 분석 및 병목 지점 식별

**설치**:
```bash
npx claude-code-templates@latest --command performance-audit --yes
```

**사용 시나리오**:

#### Scenario 1: War Room MVP 응답 시간 분석

**현재 상태**: 12.76초 (목표 달성, 추가 최적화 가능)

**실행**:
```bash
/performance-audit backend/ai/mvp/war_room_mvp.py

# 출력 예상:
# 🔍 Performance Audit - war_room_mvp.py
#
# Bottlenecks:
# 1. deliberate() - 12.5s
#    - Gemini API calls: 8.2s (3 agents)
#    - Database queries: 0.8s
#    - JSON parsing: 0.3s
#
# Recommendations:
# - Parallelize agent calls (8.2s → 3s)
# - Cache portfolio state (0.2s saved)
# - Use async/await for DB queries
```

**최적화 적용**:

**파일**: `backend/ai/mvp/war_room_mvp.py`

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

class WarRoomMVP:
    async def deliberate_parallel(self, symbol, ...):
        """병렬 처리로 Agent 호출 시간 단축"""

        # Before: 순차 실행 (8.2초)
        # trader_result = self.trader_agent.analyze(...)
        # risk_result = self.risk_agent.analyze(...)
        # analyst_result = self.analyst_agent.analyze(...)

        # After: 병렬 실행 (3초)
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(self.trader_agent.analyze, ...),
                executor.submit(self.risk_agent.analyze, ...),
                executor.submit(self.analyst_agent.analyze, ...)
            ]

            trader_result, risk_result, analyst_result = [
                f.result() for f in futures
            ]

        # PM Agent 최종 결정
        return self.pm_agent.make_final_decision(...)
```

**예상 효과**: War Room MVP 12.76초 → 7.5초 (41% 개선)

---

#### Scenario 2: 뉴스 백필 메모리 최적화

**현재 문제**: 20개 기사 처리 시 메모리 스파이크

**실행**:
```bash
/performance-audit backend/data/processors/news_processor.py

# 출력:
# 🔍 Memory Usage
# process_articles() - 450MB peak
#   - Article list: 120MB
#   - Embeddings: 280MB (OpenAI API)
#   - Intermediate data: 50MB
#
# Recommendations:
# - Use generator instead of list
# - Batch embedding API calls
# - Clear intermediate results
```

**최적화**:

```python
# Before
def process_articles(self, articles: List[Article]):
    embeddings = [self.get_embedding(a.content) for a in articles]
    # 280MB 메모리 사용

# After
def process_articles_batched(self, articles: List[Article], batch_size=5):
    for i in range(0, len(articles), batch_size):
        batch = articles[i:i+batch_size]
        embeddings = self.get_embeddings_batch(batch)  # 배치 API 호출
        self.save_embeddings(embeddings)
        # 메모리 해제
        del embeddings
        gc.collect()
```

**예상 효과**: 메모리 사용 450MB → 100MB

---

### 3.2 Performance Monitor Hook

**목표**: 실시간 성능 모니터링 및 알림

**설치**:
```bash
npx claude-code-templates@latest --hook performance-monitor --yes
```

**구현**:

**파일**: `backend/monitoring/performance_monitor.py` (신규)

```python
"""
Performance Monitor - 실시간 성능 추적

Date: 2026-01-03
Phase: Monitoring
"""
import time
import psutil
from functools import wraps
from typing import Callable
import asyncio

class PerformanceMonitor:
    """성능 모니터링 데코레이터 및 유틸리티"""

    def __init__(self, threshold_seconds: float = 1.0):
        self.threshold = threshold_seconds
        self.metrics = []

    def monitor(self, func: Callable):
        """함수 실행 시간 모니터링"""
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB

            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                elapsed = time.time() - start_time
                end_memory = psutil.Process().memory_info().rss / 1024 / 1024

                metric = {
                    'function': func.__name__,
                    'elapsed': elapsed,
                    'memory_delta': end_memory - start_memory,
                    'timestamp': time.time()
                }

                self.metrics.append(metric)

                # 임계값 초과 시 알림
                if elapsed > self.threshold:
                    await self._send_alert(metric)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            start_memory = psutil.Process().memory_info().rss / 1024 / 1024

            try:
                result = func(*args, **kwargs)
                return result
            finally:
                elapsed = time.time() - start_time
                end_memory = psutil.Process().memory_info().rss / 1024 / 1024

                metric = {
                    'function': func.__name__,
                    'elapsed': elapsed,
                    'memory_delta': end_memory - start_memory,
                    'timestamp': time.time()
                }

                self.metrics.append(metric)

                if elapsed > self.threshold:
                    # Sync 함수에서는 blocking 알림
                    print(f"⚠️  Performance Alert: {func.__name__} took {elapsed:.2f}s")

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    async def _send_alert(self, metric: dict):
        """성능 알림 전송"""
        from backend.notifications.telegram_notifier import create_telegram_notifier

        telegram = create_telegram_notifier()
        await telegram.send_message(
            f"⚠️ Performance Alert\n\n"
            f"Function: {metric['function']}\n"
            f"Time: {metric['elapsed']:.2f}s\n"
            f"Memory: +{metric['memory_delta']:.1f}MB"
        )

# 글로벌 모니터 인스턴스
perf_monitor = PerformanceMonitor(threshold_seconds=5.0)

# 사용 예시
@perf_monitor.monitor
async def deliberate(self, symbol, ...):
    # War Room MVP deliberation
    ...
```

**적용**:

```python
# backend/ai/mvp/war_room_mvp.py
from backend.monitoring.performance_monitor import perf_monitor

class WarRoomMVP:
    @perf_monitor.monitor
    async def deliberate(self, symbol, ...):
        # 5초 초과 시 자동 알림
        ...
```

**예상 효과**: 성능 저하 즉시 감지, Telegram 알림

---

### 3.3 구현 로드맵 (성능 모니터링)

**Week 1: 성능 감사 도구**
- [ ] `/performance-audit` 설치 및 테스트
- [ ] War Room MVP 병렬화
- [ ] 뉴스 백필 메모리 최적화

**Week 2: 실시간 모니터링**
- [ ] PerformanceMonitor 구현
- [ ] 주요 함수에 데코레이터 적용
- [ ] Telegram 알림 통합

**Week 3: 대시보드**
- [ ] 성능 메트릭 시각화
- [ ] 히스토리 추적
- [ ] 자동 리포트 생성

**예상 효과**:
- War Room MVP: 12.76초 → 7.5초
- 메모리 사용: 450MB → 100MB
- 성능 저하 감지: 수동 → 자동 (실시간)

---

## Component Group 4: Advanced Analytics (고급 분석)

### 4.1 Data Scientist Agent

**목표**: Shadow Trading 성과 분석 고도화

**설치**:
```bash
npx claude-code-templates@latest --agent data-scientist --yes
```

**적용 전략**:

#### Phase 4A: Shadow Trading 통계 분석

**파일**: `backend/analytics/shadow_trading_analyzer.py` (신규)

```python
"""
Shadow Trading 통계 분석

Date: 2026-01-03
Phase: Advanced Analytics
"""
import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, List

class ShadowTradingAnalyzer:
    """Shadow Trading 성과 통계 분석"""

    def __init__(self, trades: List[Dict]):
        self.trades_df = pd.DataFrame(trades)

    def calculate_sharpe_ratio(self, risk_free_rate: float = 0.02) -> float:
        """샤프 비율 계산"""
        if len(self.trades_df) < 2:
            return 0.0

        returns = self.trades_df['pnl_pct'].values
        excess_returns = returns - risk_free_rate / 252  # 일별 무위험 수익률

        if np.std(excess_returns) == 0:
            return 0.0

        return np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252)

    def calculate_sortino_ratio(self, risk_free_rate: float = 0.02) -> float:
        """소르티노 비율 (하방 리스크만 고려)"""
        returns = self.trades_df['pnl_pct'].values
        excess_returns = returns - risk_free_rate / 252

        downside_returns = excess_returns[excess_returns < 0]
        if len(downside_returns) == 0:
            return 0.0

        downside_std = np.std(downside_returns)
        if downside_std == 0:
            return 0.0

        return np.mean(excess_returns) / downside_std * np.sqrt(252)

    def calculate_calmar_ratio(self) -> float:
        """칼마 비율 (연간 수익률 / MDD)"""
        annual_return = self.trades_df['pnl_pct'].mean() * 252
        mdd = self.calculate_max_drawdown()

        if mdd == 0:
            return 0.0

        return annual_return / abs(mdd)

    def calculate_max_drawdown(self) -> float:
        """최대 낙폭"""
        cumulative = (1 + self.trades_df['pnl_pct']).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max

        return drawdown.min()

    def analyze_win_streaks(self) -> Dict:
        """연승/연패 분석"""
        wins = (self.trades_df['pnl'] > 0).astype(int).values

        # 연승 카운트
        current_streak = 0
        max_win_streak = 0
        max_loss_streak = 0

        for win in wins:
            if win == 1:
                current_streak = current_streak + 1 if current_streak > 0 else 1
                max_win_streak = max(max_win_streak, current_streak)
            else:
                current_streak = current_streak - 1 if current_streak < 0 else -1
                max_loss_streak = max(max_loss_streak, abs(current_streak))

        return {
            'max_win_streak': max_win_streak,
            'max_loss_streak': max_loss_streak,
            'current_streak': current_streak
        }

    def statistical_significance_test(self) -> Dict:
        """통계적 유의성 검정 (Win Rate > 50%?)"""
        wins = len(self.trades_df[self.trades_df['pnl'] > 0])
        total = len(self.trades_df)

        # 이항 검정
        p_value = stats.binom_test(wins, total, 0.5, alternative='greater')

        return {
            'win_rate': wins / total if total > 0 else 0,
            'p_value': p_value,
            'significant': p_value < 0.05,
            'confidence_level': (1 - p_value) * 100
        }

    def generate_report(self) -> Dict:
        """종합 통계 리포트"""
        return {
            'basic_metrics': {
                'total_trades': len(self.trades_df),
                'win_rate': len(self.trades_df[self.trades_df['pnl'] > 0]) / len(self.trades_df),
                'avg_pnl': self.trades_df['pnl'].mean(),
                'total_pnl': self.trades_df['pnl'].sum()
            },
            'risk_metrics': {
                'sharpe_ratio': self.calculate_sharpe_ratio(),
                'sortino_ratio': self.calculate_sortino_ratio(),
                'calmar_ratio': self.calculate_calmar_ratio(),
                'max_drawdown': self.calculate_max_drawdown()
            },
            'streak_analysis': self.analyze_win_streaks(),
            'statistical_test': self.statistical_significance_test()
        }

# 사용
if __name__ == "__main__":
    # Shadow Trading 데이터 로드
    from backend.execution.shadow_trading import ShadowTradingEngine

    engine = ShadowTradingEngine()
    trades = engine.get_trade_history()

    analyzer = ShadowTradingAnalyzer(trades)
    report = analyzer.generate_report()

    print("📊 Shadow Trading Statistical Analysis")
    print(f"Sharpe Ratio: {report['risk_metrics']['sharpe_ratio']:.2f}")
    print(f"Sortino Ratio: {report['risk_metrics']['sortino_ratio']:.2f}")
    print(f"Statistical Significance: {report['statistical_test']['significant']}")
```

**예상 효과**: 샤프 비율, 소르티노 비율 등 고급 메트릭 자동 계산

---

### 4.2 NLP Engineer Agent

**목표**: 뉴스 감성 분석 및 티커 추출 정확도 향상

**설치**:
```bash
npx claude-code-templates@latest --agent nlp-engineer --yes
```

**적용 전략**:

#### Phase 4B: 로컬 임베딩 모델 도입

**현재 문제**: OpenAI Embedding API 의존 (비용, 할당량)

**해결책**: HuggingFace Sentence Transformers

**파일**: `backend/ml/local_embeddings.py` (신규)

```python
"""
로컬 임베딩 모델

Date: 2026-01-03
Phase: NLP Enhancement
"""
from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List

class LocalEmbeddingModel:
    """로컬 임베딩 생성 (OpenAI 대체)"""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        # 384차원 경량 모델
        self.model = SentenceTransformer(model_name)

    def get_embedding(self, text: str) -> List[float]:
        """단일 텍스트 임베딩"""
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """배치 임베딩 (빠름)"""
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()

    def similarity(self, text1: str, text2: str) -> float:
        """텍스트 유사도"""
        emb1 = self.model.encode(text1, convert_to_numpy=True)
        emb2 = self.model.encode(text2, convert_to_numpy=True)

        # 코사인 유사도
        similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
        return float(similarity)

# 사용
embedding_model = LocalEmbeddingModel()

# 뉴스 기사 임베딩
article_text = "Apple announces new iPhone with AI features"
embedding = embedding_model.get_embedding(article_text)  # 384차원 벡터

# 유사 기사 검색
query = "Apple product launch"
similarity = embedding_model.similarity(query, article_text)  # 0.85
```

**마이그레이션**:

```python
# backend/data/processors/news_processor.py

# Before
from openai import OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_embedding(self, text):
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding  # 1536차원

# After
from backend.ml.local_embeddings import LocalEmbeddingModel
embedding_model = LocalEmbeddingModel()

def get_embedding(self, text):
    return embedding_model.get_embedding(text)  # 384차원
```

**예상 효과**:
- 비용: $0.02/1000 articles → $0 (무료)
- 속도: 200ms/article → 50ms/article
- 할당량: 제한 없음

---

#### Phase 4C: 티커 추출 정확도 향상

**현재 문제**: Regex 기반 티커 추출 (정확도 ~60%)

**해결책**: Named Entity Recognition (NER) 모델

**파일**: `backend/ml/ticker_extractor.py` (신규)

```python
"""
NER 기반 티커 추출

Date: 2026-01-03
Phase: NLP Enhancement
"""
import spacy
from typing import List, Set
import re

class TickerExtractor:
    """고급 티커 추출 (NER + 규칙 기반)"""

    def __init__(self):
        # spaCy 영어 모델 (조직명 인식)
        self.nlp = spacy.load("en_core_web_sm")

        # S&P 500 티커 사전 (캐시)
        self.known_tickers = self._load_ticker_dict()

        # 회사명 → 티커 매핑
        self.company_to_ticker = {
            "Apple": "AAPL",
            "Microsoft": "MSFT",
            "Amazon": "AMZN",
            "Google": "GOOGL",
            "Alphabet": "GOOGL",
            "Tesla": "TSLA",
            "Nvidia": "NVDA",
            "Meta": "META",
            "Facebook": "META",
            # ... (500개 회사 매핑)
        }

    def extract_tickers(self, text: str) -> Set[str]:
        """티커 추출 (다단계)"""
        tickers = set()

        # 1. Regex 패턴 (전통적 방식)
        regex_tickers = self._extract_regex(text)
        tickers.update(regex_tickers)

        # 2. NER 기반 조직명 추출
        ner_tickers = self._extract_ner(text)
        tickers.update(ner_tickers)

        # 3. 컨텍스트 기반 검증
        validated = self._validate_tickers(tickers, text)

        return validated

    def _extract_regex(self, text: str) -> Set[str]:
        """Regex 티커 추출"""
        # $AAPL 형식
        pattern1 = r'\$([A-Z]{1,5})\b'
        # (NASDAQ:AAPL) 형식
        pattern2 = r'\((?:NYSE|NASDAQ):([A-Z]{1,5})\)'

        matches = set(re.findall(pattern1, text))
        matches.update(re.findall(pattern2, text))

        return {m for m in matches if m in self.known_tickers}

    def _extract_ner(self, text: str) -> Set[str]:
        """NER 기반 조직명 → 티커 변환"""
        doc = self.nlp(text)
        tickers = set()

        for ent in doc.ents:
            if ent.label_ == "ORG":
                # 회사명을 티커로 변환
                company = ent.text
                if company in self.company_to_ticker:
                    tickers.add(self.company_to_ticker[company])

        return tickers

    def _validate_tickers(self, tickers: Set[str], text: str) -> Set[str]:
        """컨텍스트 기반 검증"""
        validated = set()

        for ticker in tickers:
            # 주변 단어 확인 (긍정적 신호)
            positive_keywords = [
                "earnings", "revenue", "stock", "shares", "analyst",
                "upgrade", "downgrade", "buy", "sell", "target price"
            ]

            if any(kw in text.lower() for kw in positive_keywords):
                validated.add(ticker)
            elif ticker in self.known_tickers:
                # 유명 티커는 무조건 포함
                validated.add(ticker)

        return validated

    def _load_ticker_dict(self) -> Set[str]:
        """S&P 500 티커 사전 로드"""
        # 실제로는 DB 또는 파일에서 로드
        return {"AAPL", "MSFT", "AMZN", "GOOGL", "TSLA", "NVDA", "META", ...}

# 사용
extractor = TickerExtractor()

article_text = """
Apple Inc. (NASDAQ:AAPL) reported strong earnings today.
The company's revenue exceeded analyst expectations.
CEO Tim Cook announced new AI features for iPhone.
"""

tickers = extractor.extract_tickers(article_text)
# Output: {'AAPL'}
```

**예상 효과**: 티커 추출 정확도 60% → 90%

---

### 4.3 구현 로드맵 (고급 분석)

**Week 1: Shadow Trading 통계**
- [ ] ShadowTradingAnalyzer 구현
- [ ] 샤프/소르티노 비율 계산
- [ ] 통계적 유의성 검정
- [ ] 주간 리포트 자동 생성

**Week 2: 로컬 임베딩**
- [ ] Sentence Transformers 설치
- [ ] LocalEmbeddingModel 구현
- [ ] OpenAI API 마이그레이션
- [ ] 성능 비교 테스트

**Week 3: 티커 추출 개선**
- [ ] spaCy 모델 설치
- [ ] TickerExtractor 구현
- [ ] 회사명 → 티커 매핑 DB
- [ ] 정확도 측정 (Before/After)

**예상 효과**:
- Shadow Trading 분석: 수동 → 자동 (주간)
- 임베딩 비용: $20/month → $0
- 티커 추출 정확도: 60% → 90%

---

## Component Group 5: Cloud & Infrastructure (클라우드 확장)

### 5.1 AWS Integration MCP

**목표**: 데이터 백업 및 서버리스 백필

**설치**:
```bash
npx claude-code-templates@latest --mcp aws-integration --yes
```

**적용 전략**:

#### Phase 5A: S3 백업 시스템

**파일**: `backend/cloud/s3_backup.py` (신규)

```python
"""
S3 자동 백업

Date: 2026-01-03
Phase: Cloud Integration
"""
import boto3
from datetime import datetime, timedelta
import gzip
import json
from pathlib import Path

class S3BackupManager:
    """PostgreSQL → S3 자동 백업"""

    def __init__(self, bucket_name: str = "ai-trading-backups"):
        self.s3 = boto3.client('s3')
        self.bucket = bucket_name

    def backup_database(self):
        """전체 DB 백업"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"db_backup_{timestamp}.sql.gz"

        # pg_dump로 백업
        import subprocess

        dump_cmd = [
            "pg_dump",
            "-h", "localhost",
            "-p", "5433",
            "-U", "trading",
            "-d", "ai_trading",
            "-F", "c",  # Custom format
            "-f", f"/tmp/{backup_file}"
        ]

        subprocess.run(dump_cmd, check=True)

        # S3 업로드
        with open(f"/tmp/{backup_file}", "rb") as f:
            self.s3.upload_fileobj(
                f,
                self.bucket,
                f"database/{backup_file}"
            )

        print(f"✅ Database backed up to S3: {backup_file}")

    def backup_news_articles(self, days: int = 30):
        """최근 뉴스 기사 백업 (JSON)"""
        from backend.database.repository import NewsRepository

        repo = NewsRepository()
        articles = repo.get_recent_articles(hours=days*24)

        timestamp = datetime.now().strftime("%Y%m%d")
        backup_file = f"news_{timestamp}.json.gz"

        # JSON 압축
        with gzip.open(f"/tmp/{backup_file}", "wt") as f:
            json.dump([a.to_dict() for a in articles], f)

        # S3 업로드
        with open(f"/tmp/{backup_file}", "rb") as f:
            self.s3.upload_fileobj(
                f,
                self.bucket,
                f"news/{backup_file}"
            )

    def schedule_backups(self):
        """백업 스케줄 (Cron)"""
        # 매일 자정 DB 백업
        # 매주 일요일 뉴스 백업
        pass

# GitHub Actions 워크플로우
# .github/workflows/backup.yml
"""
name: Daily Backup

on:
  schedule:
    - cron: '0 0 * * *'  # 매일 자정

jobs:
  backup:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Backup to S3
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        run: |
          python backend/cloud/s3_backup.py
"""
```

**예상 효과**: 자동 백업, 데이터 손실 위험 0%

---

#### Phase 5B: Lambda 서버리스 백필

**목적**: 주가/뉴스 백필을 Lambda로 오프로드 (백엔드 부하 감소)

**파일**: `lambda/news_backfill/handler.py` (신규)

```python
"""
AWS Lambda - 뉴스 백필

Date: 2026-01-03
Phase: Serverless
"""
import json
import requests
from datetime import datetime, timedelta

def lambda_handler(event, context):
    """Lambda 핸들러 - 뉴스 백필"""

    # 파라미터
    source = event.get('source', 'reuters')
    days = event.get('days', 7)

    # RSS 크롤링
    articles = fetch_rss_articles(source, days)

    # 백엔드 API로 전송
    backend_url = "https://api.trading.example.com/api/news/bulk"
    response = requests.post(backend_url, json=articles)

    return {
        'statusCode': 200,
        'body': json.dumps({
            'articles_fetched': len(articles),
            'backend_response': response.status_code
        })
    }

def fetch_rss_articles(source, days):
    # RSS 파싱 로직
    pass
```

**배포**:
```bash
# Serverless Framework
serverless deploy

# CloudWatch Events로 스케줄
# 매 시간 뉴스 백필
```

**예상 효과**: 백엔드 부하 30% 감소, 비용 절감

---

### 5.2 구현 로드맵 (클라우드)

**Week 1: S3 백업**
- [ ] S3 버킷 생성
- [ ] S3BackupManager 구현
- [ ] GitHub Actions 워크플로우
- [ ] 백업 복원 테스트

**Week 2: Lambda 백필**
- [ ] Lambda 함수 작성
- [ ] Serverless Framework 설정
- [ ] CloudWatch Events 스케줄
- [ ] 백엔드 통합

**예상 효과**:
- 백업 자동화: 100%
- 백엔드 부하: -30%
- 비용: Lambda 프리티어 활용

---

## Component Group 6: Communication & Notifications (알림 시스템)

### 6.1 Discord/Slack Notifications Hook

**목표**: 중요 이벤트 실시간 알림

**설치**:
```bash
npx claude-code-templates@latest --hook discord-notifications --yes
# 또는
npx claude-code-templates@latest --hook slack-notifications --yes
```

**적용 시나리오**:

#### Scenario 1: Shadow Trading 매매 신호 알림

**파일**: `backend/notifications/discord_notifier.py` (신규)

```python
"""
Discord 알림

Date: 2026-01-03
Phase: Notifications
"""
import requests
from typing import Dict

class DiscordNotifier:
    """Discord 웹훅 알림"""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def send_trade_signal(self, signal: Dict):
        """매매 신호 알림"""
        embed = {
            "title": f"🎯 {signal['action']} Signal - {signal['ticker']}",
            "description": signal['reasoning'],
            "color": 0x00ff00 if signal['action'] == 'BUY' else 0xff0000,
            "fields": [
                {"name": "Confidence", "value": f"{signal['confidence']:.1%}", "inline": True},
                {"name": "Target Price", "value": f"${signal['target_price']:.2f}", "inline": True},
                {"name": "Agent", "value": signal['agent'], "inline": True}
            ],
            "timestamp": signal['created_at']
        }

        requests.post(self.webhook_url, json={"embeds": [embed]})

    def send_deployment_notification(self, status: str, commit: str):
        """배포 알림"""
        color = 0x00ff00 if status == "success" else 0xff0000

        embed = {
            "title": f"🚀 Deployment {status.upper()}",
            "description": f"Commit: {commit[:7]}",
            "color": color
        }

        requests.post(self.webhook_url, json={"embeds": [embed]})

# 사용
discord = DiscordNotifier(os.getenv("DISCORD_WEBHOOK_URL"))

# War Room MVP에서 호출
@router.post("/shadow/execute")
async def execute_shadow_trade(request):
    result = shadow_trading.execute_trade(...)

    # Discord 알림
    discord.send_trade_signal({
        'action': result['action'],
        'ticker': result['ticker'],
        'confidence': result['confidence'],
        'reasoning': result['reasoning'],
        'agent': 'War Room MVP',
        'created_at': datetime.now().isoformat()
    })

    return result
```

**예상 효과**: 실시간 매매 알림, 팀 협업 강화

---

### 6.2 구현 로드맵 (알림)

**Week 1: Discord 통합**
- [ ] DiscordNotifier 구현
- [ ] 웹훅 설정
- [ ] War Room MVP 통합
- [ ] 배포 알림

**Week 2: Slack 통합** (선택)
- [ ] SlackNotifier 구현
- [ ] 채널별 알림 분리
- [ ] 인터랙티브 버튼

**예상 효과**:
- 매매 신호 즉시 확인
- 배포 상태 실시간 추적
- 팀 협업 개선

---

## 전체 구현 타임라인

### Month 1: 보안 & DevOps (High Priority)
- Week 1-2: Security Auditor (Secrets 암호화, OWASP 스캔)
- Week 3-4: DevOps Engineer (CI/CD 파이프라인, Docker 최적화)

**예상 효과**: 보안 취약점 0건, 배포 시간 60분 → 5분

### Month 2: 성능 & 분석 (Medium Priority)
- Week 1-2: Performance Monitoring (성능 감사, 실시간 모니터링)
- Week 3-4: Data Scientist (Shadow Trading 통계, 고급 메트릭)

**예상 효과**: War Room MVP 7.5초, 샤프 비율 자동 계산

### Month 3: NLP & 클라우드 (Medium Priority)
- Week 1-2: NLP Engineer (로컬 임베딩, 티커 추출 90%)
- Week 3-4: AWS Integration (S3 백업, Lambda 백필)

**예상 효과**: 임베딩 비용 $0, 티커 정확도 90%

### Month 4: 알림 & 고급 기능 (Low Priority)
- Week 1-2: Discord/Slack 알림
- Week 3-4: PDF Processing, Excel Automation

**예상 효과**: 실시간 알림, SEC 보고서 자동 파싱

---

## 최종 성공 기준

### 보안 (P1)
- [ ] API 키 암호화 100%
- [ ] OWASP Top 10 스캔 자동화
- [ ] Secrets 노출 0건
- [ ] 보안 감사 주간 자동 실행

### DevOps (P1)
- [ ] CI/CD 파이프라인 구축
- [ ] 테스트 자동 실행 (커버리지 80%+)
- [ ] 배포 시간 < 5분
- [ ] 롤백 시간 < 2분

### 성능 (P2)
- [ ] War Room MVP < 8초
- [ ] 성능 저하 자동 감지
- [ ] 메모리 사용 < 200MB (뉴스 백필)

### 분석 (P2)
- [ ] 샤프 비율 자동 계산
- [ ] Shadow Trading 주간 리포트 자동 생성
- [ ] 통계적 유의성 검정

### NLP (P2)
- [ ] 로컬 임베딩 (비용 $0)
- [ ] 티커 추출 정확도 > 90%

### 클라우드 (P3)
- [ ] S3 자동 백업 (일일)
- [ ] Lambda 백필 (시간당)

### 알림 (P3)
- [ ] Discord/Slack 실시간 알림
- [ ] 배포 상태 알림

---

## 관련 문서

**이미 계획 완료:**
- [260103_Claude_Code_Templates_Implementation_Plan.md](260103_Claude_Code_Templates_Implementation_Plan.md) - 테스트, 프론트엔드, Git Hooks
- [260102_Database_Optimization_Plan.md](260102_Database_Optimization_Plan.md) - DB 최적화
- [Work_Log_20260102.md](Work_Log_20260102.md) - 2026-01-02 작업 완료

**참고 자료:**
- [260102_Claude_Code_Templates_Review.md](260102_Claude_Code_Templates_Review.md) - 600+ 템플릿 분석
- [Shadow_Trading_Week1_Report.md](Shadow_Trading_Week1_Report.md) - Shadow Trading 모니터링

---

**작성일**: 2026-01-03
**작성자**: AI Trading System Development Team
**우선순위**: P2-P3 (Medium to Low Priority)
**상태**: 📋 Ready for Implementation
**다음 리뷰**: Month 1 완료 후 (보안 & DevOps)
**총 예상 소요**: 4개월 (16주)

# CI/CD Setup Guide - GitHub Actions

**작성일**: 2025-12-10
**문서 버전**: 1.0
**옵션**: Option 7 - CI/CD 파이프라인 구축

---

## 📋 목차

1. [개요](#개요)
2. [GitHub Secrets 설정](#github-secrets-설정)
3. [워크플로우 구조](#워크플로우-구조)
4. [로컬 배포 스크립트](#로컬-배포-스크립트)
5. [환경별 설정](#환경별-설정)
6. [문제 해결](#문제-해결)

---

## 개요

AI Trading System의 CI/CD 파이프라인은 **GitHub Actions**를 사용하여 자동화되어 있습니다.

### 주요 기능

- ✅ **자동 테스트**: 코드 푸시 시 자동으로 테스트 실행
- ✅ **코드 품질 검사**: Linting, 타입 체크, 보안 스캔
- ✅ **자동 빌드**: Docker 이미지 자동 빌드 및 푸시
- ✅ **자동 배포**: Staging/Production 자동 배포
- ✅ **알림**: Slack/Email 알림

### 워크플로우 트리거

```yaml
on:
  push:
    branches: [main, develop]    # main/develop 푸시 시
  pull_request:
    branches: [main]               # main PR 시
```

---

## GitHub Secrets 설정

### 1. Repository Secrets 추가

GitHub 저장소 → Settings → Secrets and variables → Actions

### 필수 Secrets

| Secret 이름 | 설명 | 예시 |
|-------------|------|------|
| `OPENAI_API_KEY` | OpenAI API 키 | `sk-xxxxxxxxxxxxxxxx` |
| `DOCKER_USERNAME` | Docker Hub 사용자명 | `myusername` |
| `DOCKER_PASSWORD` | Docker Hub 비밀번호/토큰 | `dckr_pat_xxxxxxx` |

### 배포 관련 Secrets (선택사항)

#### Staging 환경

| Secret 이름 | 설명 |
|-------------|------|
| `STAGING_HOST` | 스테이징 서버 IP/도메인 |
| `STAGING_USER` | SSH 사용자명 |
| `STAGING_SSH_KEY` | SSH Private Key |

#### Production 환경

| Secret 이름 | 설명 |
|-------------|------|
| `PRODUCTION_HOST` | 프로덕션 서버 IP/도메인 |
| `PRODUCTION_USER` | SSH 사용자명 |
| `PRODUCTION_SSH_KEY` | SSH Private Key |

#### 알림 (선택사항)

| Secret 이름 | 설명 |
|-------------|------|
| `SLACK_WEBHOOK_URL` | Slack Webhook URL |

### 2. Secrets 추가 방법

#### OpenAI API Key
```bash
# GitHub 웹에서:
# Settings → Secrets → New repository secret
# Name: OPENAI_API_KEY
# Value: sk-xxxxxxxxxxxxxxxx
```

#### Docker Hub Token 생성
1. Docker Hub 로그인 (https://hub.docker.com)
2. Account Settings → Security → New Access Token
3. Token 이름: `github-actions`
4. Permissions: `Read, Write, Delete`
5. 생성된 토큰을 복사하여 `DOCKER_PASSWORD`에 저장

#### SSH Key 생성
```bash
# 로컬에서 SSH 키 생성
ssh-keygen -t ed25519 -C "github-actions" -f ~/.ssh/github_actions

# Public Key를 서버에 추가
ssh-copy-id -i ~/.ssh/github_actions.pub user@your-server.com

# Private Key를 GitHub Secret에 추가
cat ~/.ssh/github_actions
# 출력된 내용을 STAGING_SSH_KEY 또는 PRODUCTION_SSH_KEY에 추가
```

---

## 워크플로우 구조

### Job 흐름도

```
┌─────────────┐
│   Lint      │ (코드 품질 검사)
└──────┬──────┘
       │
┌──────▼──────────────────────┐
│  Test Backend & Frontend    │ (병렬 실행)
│  + Security Scan            │
└──────┬──────────────────────┘
       │
┌──────▼──────┐
│   Build     │ (Docker 이미지)
└──────┬──────┘
       │
       ├─────────────┬─────────────┐
       │             │             │
┌──────▼──────┐ ┌───▼────┐ ┌──────▼────────┐
│  Deploy     │ │Deploy  │ │   Notify      │
│  Staging    │ │Prod    │ │               │
│  (develop)  │ │(main)  │ │               │
└─────────────┘ └────────┘ └───────────────┘
```

### Job 상세 설명

#### 1. Lint (코드 품질 검사)
```yaml
- Black: 코드 포맷 검사
- isort: Import 정렬 검사
- Flake8: Python 문법 검사
- MyPy: 타입 체크
```

**실행 시간**: ~2분

#### 2. Test Backend
```yaml
Services:
  - PostgreSQL (TimescaleDB)
  - Redis

Tests:
  - pytest with coverage
  - Coverage upload to Codecov
```

**실행 시간**: ~5-10분

#### 3. Test Frontend
```yaml
- ESLint: JavaScript/TypeScript 검사
- Jest: 단위 테스트
- Coverage report
```

**실행 시간**: ~3-5분

#### 4. Security Scan
```yaml
- Safety: 의존성 보안 검사
- Bandit: Python 코드 보안 검사
```

**실행 시간**: ~2분

#### 5. Build Docker Images
```yaml
- Backend 이미지 빌드
- Frontend 이미지 빌드
- Docker Hub 푸시 (main 브랜치만)
- 캐시 활용 (빌드 속도 향상)
```

**실행 시간**: ~10-15분 (캐시 사용 시 ~5분)

#### 6. Deploy
```yaml
Staging (develop 브랜치):
  - SSH 접속
  - Git pull
  - Docker compose up
  - Health check

Production (main 브랜치):
  - 위와 동일
  - Slack 알림 추가
```

**실행 시간**: ~3-5분

---

## 로컬 배포 스크립트

### 사용법

```bash
# 권한 부여 (한 번만)
chmod +x scripts/deploy.sh

# Staging 배포
./scripts/deploy.sh staging

# Production 배포
./scripts/deploy.sh production

# 테스트 건너뛰기
./scripts/deploy.sh staging --skip-tests

# 확인 없이 강제 배포
./scripts/deploy.sh production --force
```

### 스크립트가 하는 일

1. **사전 검사**
   - Git 상태 확인
   - 브랜치 확인 (production은 main 필수)

2. **테스트 실행**
   - Backend pytest
   - Frontend jest

3. **Docker 빌드**
   - 이미지 태그: `{환경}-{commit hash}-{timestamp}`
   - 예: `staging-abc1234-20241210-143022`

4. **환경 설정 로드**
   - `.env.staging` 또는 `.env.production`

5. **백업** (Production만)
   - PostgreSQL 백업: `backups/backup-{timestamp}.sql`

6. **배포**
   - 기존 컨테이너 중지
   - 새 컨테이너 시작
   - 데이터베이스 마이그레이션

7. **Health Check**
   - Backend API 확인
   - Frontend 확인

8. **알림**
   - Slack 알림 (설정된 경우)

---

## 환경별 설정

### Staging 환경

**파일**: `.env.staging`

```bash
# API Keys
OPENAI_API_KEY=sk-staging-xxxxxxxx
KIS_APP_KEY=PS_STAGING_xxxxxxxx
KIS_BASE_URL=https://openapivts.koreainvestment.com:29443

# Database
DATABASE_URL=postgresql://user:pass@staging-db:5432/ai_trading_staging

# Redis
REDIS_URL=redis://staging-redis:6379

# API URL
API_BASE_URL=https://staging-api.ai-trading-system.com

# Feature Flags
ENABLE_REAL_TRADING=false
ENABLE_AI_ANALYSIS=true
```

**Docker Compose**: `docker-compose.staging.yml`

```yaml
version: '3.8'

services:
  backend:
    image: ai-trading-backend:staging-latest
    environment:
      - ENVIRONMENT=staging
    ports:
      - "8000:8000"

  frontend:
    image: ai-trading-frontend:staging-latest
    environment:
      - REACT_APP_API_URL=https://staging-api.ai-trading-system.com
    ports:
      - "3000:3000"
```

### Production 환경

**파일**: `.env.production`

```bash
# API Keys
OPENAI_API_KEY=sk-production-xxxxxxxx
KIS_APP_KEY=PS_PRODUCTION_xxxxxxxx
KIS_BASE_URL=https://openapi.koreainvestment.com:9443

# Database
DATABASE_URL=postgresql://user:pass@prod-db:5432/ai_trading

# Redis
REDIS_URL=redis://prod-redis:6379

# API URL
API_BASE_URL=https://api.ai-trading-system.com

# Feature Flags
ENABLE_REAL_TRADING=true
ENABLE_AI_ANALYSIS=true

# Monitoring
SENTRY_DSN=https://xxx@sentry.io/yyy
```

---

## 배포 전 체크리스트

### Staging 배포

- [ ] `.env.staging` 파일 확인
- [ ] Staging 서버 접근 가능 확인
- [ ] 데이터베이스 백업 존재 확인
- [ ] 테스트 통과 확인

### Production 배포

- [ ] Staging 테스트 완료
- [ ] `.env.production` 파일 확인
- [ ] 프로덕션 서버 접근 가능 확인
- [ ] **데이터베이스 백업 필수**
- [ ] 모든 테스트 통과
- [ ] 팀원에게 배포 알림
- [ ] 모니터링 대시보드 준비

---

## 문제 해결

### 문제 1: GitHub Actions 실패

**증상**: CI/CD 워크플로우가 실패함

**해결**:
```bash
# 1. GitHub Actions 탭에서 로그 확인
# 2. 로컬에서 동일 명령 실행
pytest backend/tests/ -v

# 3. Secrets 확인
# Settings → Secrets → Actions
```

### 문제 2: Docker 빌드 실패

**증상**: `docker build` 단계에서 실패

**해결**:
```bash
# 로컬에서 테스트
docker build -f backend/Dockerfile .

# 캐시 삭제 후 재시도
docker build --no-cache -f backend/Dockerfile .
```

### 문제 3: SSH 연결 실패

**증상**: 배포 단계에서 SSH 연결 실패

**해결**:
```bash
# 1. SSH 키 확인
ssh -i ~/.ssh/github_actions user@server

# 2. 서버 방화벽 확인
sudo ufw status

# 3. GitHub Secret 재확인
# STAGING_SSH_KEY에 Private Key 전체 내용 포함되었는지 확인
```

### 문제 4: Health Check 실패

**증상**: 배포 후 Health Check 실패

**해결**:
```bash
# 1. 컨테이너 상태 확인
docker-compose ps

# 2. 로그 확인
docker-compose logs backend

# 3. 수동 Health Check
curl http://localhost:8000/health

# 4. 환경 변수 확인
docker-compose exec backend env
```

---

## 모니터링

### GitHub Actions 대시보드

```
Repository → Actions → CI/CD Pipeline
```

- 실시간 워크플로우 상태 확인
- 각 Job 로그 조회
- 실패 시 알림 확인

### Codecov 통합

```
https://codecov.io/gh/your-username/ai-trading-system
```

- 코드 커버리지 추이
- PR별 커버리지 변화
- 커버되지 않은 코드 확인

### Slack 알림

배포 성공/실패 시 Slack 알림:

```
✅ Production Deployment
Commit: abc1234
Author: @username
Time: 2024-12-10 14:30:22
```

---

## Best Practices

### 1. 브랜치 전략

```
main (production)
  ↑
develop (staging)
  ↑
feature/xxx (개발)
```

- `feature/*`: 기능 개발
- `develop`: 통합 테스트 (Staging 배포)
- `main`: 프로덕션 릴리즈

### 2. 커밋 메시지

```
feat: Add real-time notification system
fix: Fix CORS issue in API
docs: Update deployment guide
test: Add integration tests for AutoTrader
```

### 3. PR 체크리스트

- [ ] 모든 테스트 통과
- [ ] 코드 리뷰 완료
- [ ] 문서 업데이트
- [ ] CHANGELOG 업데이트

### 4. 배포 시간

- **Staging**: 언제든지 가능
- **Production**: 업무 시간 외 (예: 오전 2-4시)

---

## 참고 자료

- **GitHub Actions 문서**: https://docs.github.com/en/actions
- **Docker Hub**: https://hub.docker.com
- **Codecov**: https://docs.codecov.com

---

**문서 버전**: 1.0
**최종 업데이트**: 2025-12-10
**작성자**: AI Trading System Team

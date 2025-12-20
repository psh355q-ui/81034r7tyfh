# CI/CD Pipeline Documentation

**Version**: 1.0  
**Last Updated**: 2025-12-14  
**Status**: Active

---

## Overview

AI Trading System CI/CD pipeline using GitHub Actions for automated testing, building, and deployment.

### Key Features

- Automated backend testing (pytest)
- Automated frontend build
- Docker image builds
- Security scanning (Trivy)
- Code coverage reporting
- Automatic production deployment

---

## GitHub Actions Workflow

### File Location
`.github/workflows/ci.yml`

### Triggers
- Push to `main` or `develop` branches
- Pull requests to `main`

### Jobs

#### 1. backend-test
- Python 3.11
- PostgreSQL 15 + Redis 7
- pytest with coverage
- Upload to Codecov

#### 2. frontend-test
- Node.js 18
- ESLint
- Production build

#### 3. docker-build
- Build backend image
- Build frontend image
- Only on `main` branch

#### 4. security-scan
- Trivy vulnerability scanner
- SARIF report upload

#### 5. deploy-production
- SSH deployment to NAS
- docker-compose restart
- Only on `main` branch

---

## Local Testing

### Backend Tests
```bash
cd backend
pytest tests/ -v --cov=. --cov-report=term
```

### Frontend Build
```bash
cd frontend
npm run build
```

---

## Docker Deployment

### Services
- PostgreSQL (TimescaleDB)
- Redis
- Backend (FastAPI)
- Frontend (React + Nginx)

### Deploy Commands
```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# Check status
docker-compose ps
```

### Deploy Script
```bash
./scripts/deploy.sh
```

### Health Check
```bash
./scripts/health_check.sh
```

---

## Environment Variables

### GitHub Secrets Required
- `DOCKER_USERNAME`
- `DOCKER_PASSWORD`
- `NAS_HOST`
- `NAS_USERNAME`
- `NAS_SSH_KEY`

### .env File Template
```bash
DATABASE_URL=postgresql://postgres:password@localhost:5432/ai_trading
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key
KIS_APP_KEY=your_kis_key
KIS_APP_SECRET=your_kis_secret
GEMINI_API_KEY=your_gemini_key
```

---

## Test Structure

### Backend Tests
- `backend/tests/conftest.py` - pytest fixtures
- `backend/tests/test_health.py` - health checks
- `backend/tests/test_reasoning_api.py` - API tests
- `backend/tests/test_models.py` - model tests

---

## Deployment Flow

### Develop Branch
1. Push code
2. Run tests
3. Build frontend
4. Security scan
5. NO deployment

### Main Branch
1. Push/Merge code
2. Run tests
3. Build frontend
4. Build Docker images
5. Security scan
6. **Deploy to production**

---

## Troubleshooting

### Test Failures
```bash
export PYTHONPATH=$(pwd)
pytest tests/
```

### Docker Build Failures
```bash
docker-compose build --no-cache
```

### Health Check Failures
```bash
docker-compose logs backend
docker-compose restart backend
```

---

## Next Steps

- [ ] E2E testing (Playwright)
- [ ] Performance testing
- [ ] Rollback automation
- [ ] Blue-Green deployment
- [ ] Kubernetes support

---

**Maintained by**: AI Trading System Team

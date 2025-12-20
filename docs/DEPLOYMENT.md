# Deployment Guide

**AI Constitutional Trading System - Production Deployment**

---

## 📋 체크리스트

배포 전 반드시 확인:

- [ ] PostgreSQL 설치 및 실행
- [ ] `.env` 파일 설정
- [ ] Constitution 해시 업데이트 완료
- [ ] DB 마이그레이션 실행
- [ ] 테스트 통과 확인
- [ ] 백업 계획 수립

---

## 🚀 Step-by-Step Deployment

### Phase 1: 환경 준비 (15분)

#### 1.1 PostgreSQL 설치

**Windows**:
```powershell
# PostgreSQL 다운로드
# https://www.postgresql.org/download/windows/

# 설치 후 서비스 시작
net start postgresql-x64-14
```

**macOS**:
```bash
brew install postgresql@14
brew services start postgresql@14
```

**Linux (Ubuntu)**:
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

#### 1.2 데이터베이스 생성

```bash
# PostgreSQL 접속
psql -U postgres

# 프로덕션 DB 생성
CREATE DATABASE ai_trading_prod;

# 전용 사용자 생성 (보안 강화)
CREATE USER trading_user WITH ENCRYPTED PASSWORD 'your_strong_password_here';

# 권한 부여
GRANT ALL PRIVILEGES ON DATABASE ai_trading_prod TO trading_user;

# 확인
\l
\q
```

#### 1.3 환경 변수 설정

```bash
# .env.example을 복사
cp .env.example .env

# 편집 (.env 파일)
nano .env
```

**최소 필수 설정**:
```env
DATABASE_URL=postgresql://trading_user:your_strong_password@localhost:5432/ai_trading_prod
```

---

### Phase 2: Constitution 무결성 (5분)

#### 2.1 해시 검증

```bash
# Constitution 해시 확인
python backend/constitution/check_integrity.py
```

**예상 출력**:
```
✅ 헌법 무결성 검증 성공
✅ 시스템 시작 가능
```

#### 2.2 해시 업데이트 (파일 수정 시)

```bash
# 해시 재계산
python backend/constitution/check_integrity.py --update

# 출력된 해시값을 check_integrity.py에 복사
```

---

### Phase 3: 데이터베이스 마이그레이션 (5분)

#### 3.1 Alembic 마이그레이션

```bash
cd backend

# 현재 상태 확인
alembic current

# 마이그레이션 실행
alembic upgrade head
```

**예상 출력**:
```
INFO  [alembic.runtime.migration] Running upgrade -> 251215_shadow_trades
INFO  [alembic.runtime.migration] Running upgrade 251215_shadow_trades -> 251215_proposals
```

#### 3.2 테이블 확인

```bash
psql -U trading_user -d ai_trading_prod

# 테이블 리스트
\dt

# 예상:
#   proposals
#   shadow_trades
#   alembic_version

\q
```

---

### Phase 4: 시스템 테스트 (10분)

#### 4.1 Constitution Test

```bash
python test_constitutional_system.py
```

**예상**:
```
Constitution Integrity      ✅ PASS
Constitution Validation     ✅ PASS
Risk Limits                 ✅ PASS
Allocation Rules            ✅ PASS
Trading Constraints         ✅ PASS

Total: 5/5 (100%)
```

#### 4.2 Demo Workflow

```bash
python demo_constitutional_workflow.py
```

**예상**:
```
AI Debate: 4/5 agents → BUY
Constitutional Validation: ❌ FAIL
Commander: ❌ REJECT
Shadow Trade: ✅ Created
```

#### 4.3 Backtest

```bash
python backend/backtest/constitutional_backtest_engine.py
```

**예상**:
```
자본 보존율: 100.00%
방어 성공: 15/15
```

---

### Phase 5: 백엔드 실행 (프로덕션)

#### 5.1 Gunicorn (WSGI Server)

```bash
# Gunicorn 설치
pip install gunicorn

# 실행
cd backend
gunicorn main:app \
  --workers 4 \
  --bind 0.0.0.0:8000 \
  --access-logfile logs/access.log \
  --error-logfile logs/error.log \
  --log-level info
```

#### 5.2 systemd 서비스 (자동 시작)

`/etc/systemd/system/ai-trading.service`:
```ini
[Unit]
Description=AI Constitutional Trading System
After=postgresql.service

[Service]
User=your_user
WorkingDirectory=/path/to/ai-trading-system/backend
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/gunicorn main:app --workers 4 --bind 0.0.0.0:8000

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl start ai-trading
sudo systemctl enable ai-trading
sudo systemctl status ai-trading
```

---

### Phase 6: Frontend 배포 (선택)

#### 6.1 Build

```bash
cd frontend
npm run build
```

#### 6.2 Nginx 설정

`/etc/nginx/sites-available/ai-trading`:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Frontend (빌드된 정적 파일)
    location / {
        root /path/to/ai-trading-system/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/ai-trading /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## 🔒 보안 체크리스트

### Database Security

- [ ] 강력한 비밀번호 사용 (16자 이상)
- [ ] 외부 접근 차단 (localhost만 허용)
- [ ] SSL/TLS 연결 사용
- [ ] 정기 백업 설정

```bash
# PostgreSQL 백업
pg_dump -U trading_user ai_trading_prod > backup_$(date +%Y%m%d).sql

# 복원
psql -U trading_user ai_trading_prod < backup_20251215.sql
```

### Application Security

- [ ] `.env` 파일 권한: `chmod 600 .env`
- [ ] API 키 환경 변수로만 관리
- [ ] HTTPS 사용 (프로덕션)
- [ ] Rate Limiting 설정
- [ ] CORS 설정 확인

### Constitution Security

- [ ] 해시 검증 활성화 (check_integrity.py)
- [ ] 파일 권한: `chmod 444 backend/constitution/*.py`
- [ ] Git에서 헌법 변경 추적
- [ ] 변경 시 승인 프로세스

---

## 📊 모니터링

### Logging

```python
# backend/main.py
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)
```

### Health Check

```bash
# API 엔드포인트
curl http://localhost:8000/health

# 예상:
# {"status": "healthy", "constitution": "verified"}
```

### Metrics

중요 지표:
- 일일 제안 수
- 헌법 통과율
- Shadow Trade 수
- 자본 보존율
- API 응답 시간

---

## 🚨 장애 대응

### Constitution 무결성 실패

```bash
# 증상
🚨 System Freeze
헌법 무결성 검증 실패

# 조치
1. 백업에서 헌법 파일 복구
2. Git 히스토리 확인
3. 의도적 수정이면 해시 업데이트
```

### Database 연결 실패

```bash
# 증상
ConnectionError: could not connect to server

# 조치
1. PostgreSQL 상태 확인
   systemctl status postgresql
   
2. 재시작
   systemctl restart postgresql
   
3. 연결 설정 확인
   /etc/postgresql/14/main/pg_hba.conf
```

### Telegram Bot 응답 없음

```bash
# 증상
Timeout: Bot not responding

# 조치
1. Token 검증
2. Chat ID 확인
3. 네트워크 확인
4. Bot 재시작
```

---

## 📈 성능 최적화

### Database

```sql
-- 인덱스 추가 (이미 마이그레이션에 포함)
CREATE INDEX idx_proposals_status ON proposals(status);
CREATE INDEX idx_shadow_trades_status ON shadow_trades(status);

-- VACUUM (정기 실행)
VACUUM ANALYZE proposals;
VACUUM ANALYZE shadow_trades;
```

### Application

```python
# Connection Pooling
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20
)
```

### Caching (선택)

```bash
# Redis 설치
sudo apt install redis-server

# Python
pip install redis
```

---

## 🔄 업데이트 절차

### Code Update

```bash
# 1. 백업
pg_dump -U trading_user ai_trading_prod > backup_before_update.sql

# 2. Git pull
git pull origin main

# 3. 의존성 업데이트
pip install -r requirements.txt

# 4. 마이그레이션
cd backend
alembic upgrade head

# 5. 테스트
python test_constitutional_system.py

# 6. 재시작
sudo systemctl restart ai-trading
```

### Constitution Update

```bash
# 1. 헌법 파일 수정
# backend/constitution/*.py

# 2. 해시 업데이트
python backend/constitution/check_integrity.py --update

# 3. check_integrity.py에 해시 복사

# 4. Git commit
git add backend/constitution/
git commit -m "Update constitution: [설명]"

# 5. 재시작
sudo systemctl restart ai-trading
```

---

## 📞 Support

### Documentation
- README.md - 프로젝트 개요
- ARCHITECTURE.md - 시스템 구조
- QUICK_START.md - 빠른 시작
- DATABASE_SETUP.md - DB 설정

### Troubleshooting
- Logs: `backend/logs/`
- Constitution Status: `python backend/constitution/check_integrity.py`
- DB Status: `psql -U trading_user -d ai_trading_prod`

---

**배포 성공을 축하합니다!** 🎉

**Version**: 2.0.0  
**Last Updated**: 2025-12-15

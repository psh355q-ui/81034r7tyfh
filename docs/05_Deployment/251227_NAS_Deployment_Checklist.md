# NAS 서버 배포 체크리스트

**날짜**: 2025-12-27
**목표**: NAS 서버에 AI Trading System 배포 및 24/7 운영
**현재 상태**: 로컬 개발 완료, 배포 준비 중

---

## 🔍 배포 전 필수 확인 사항

### 1. Constitutional 통과율 문제 해결 (❌ 중요!)

**현재 상태**: 37.5% (목표: 90%+)

**문제점**:
- 통과율이 낮으면 대부분의 토론이 무용지물
- 시그널 생성 안됨 (32개 세션 중 1개만 시그널 생성)
- 실거래 불가능

**배포 전 필수 조치**:
```bash
# Constitutional 검증 로직 확인
1. backend/constitution/constitution.py 로그 추가
2. 실패 이유 분석
3. 임계값 조정 또는 로직 수정
4. 통과율 90%+ 확인 후 배포
```

**예상 원인**:
- 신뢰도 임계값이 너무 높음 (현재 평균 45-50%)
- 포지션 크기 제한이 너무 엄격
- 검증 로직 버그

**조치 방법**:
1. 로컬에서 여러 종목 토론 (10개+)
2. Constitutional 실패 로그 분석
3. 임계값 조정
4. 통과율 90%+ 달성 확인
5. **이후 NAS 배포**

### 2. 환경 변수 설정

**필수 환경 변수**:
```bash
# .env 파일 확인
DATABASE_URL=postgresql://user:password@localhost:5432/ai_trading
KIS_ACCOUNT_NUMBER=           # Optional (Yahoo Finance fallback 있음)
KIS_IS_VIRTUAL=true          # 반드시 true!
GEMINI_API_KEY=your_key
CLAUDE_API_KEY=your_key      # Optional
OPENAI_API_KEY=your_key      # Optional
```

**보안 확인**:
- [ ] .env 파일이 .gitignore에 포함되어 있는지
- [ ] API 키가 노출되지 않았는지
- [ ] KIS_IS_VIRTUAL=true인지 (실거래 방지)

### 3. 데이터베이스 마이그레이션

**NAS에서 PostgreSQL 설정**:
```bash
# Docker Compose 사용 권장
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: ai_trading
      POSTGRES_USER: trading_user
      POSTGRES_PASSWORD: secure_password
    volumes:
      - ./postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
```

**테이블 생성**:
```bash
# 모든 테이블 생성 스크립트 실행
psql -U trading_user -d ai_trading < backend/database/schema.sql

# 또는 개별 테이블
psql < backend/database/create_price_tracking_table.sql
psql < backend/database/create_agent_vote_tracking_table.sql
```

### 4. 의존성 설치

**Python 패키지**:
```bash
cd backend
pip install -r requirements.txt
```

**확인 사항**:
- [ ] Python 3.11+ 설치
- [ ] PostgreSQL 클라이언트 라이브러리
- [ ] yfinance, requests 등 외부 라이브러리

### 5. 포트 설정

**현재 포트**:
- Backend: 8001
- Frontend: 3002

**NAS 방화벽 설정**:
```bash
# 외부 접근 허용 (필요 시)
- 8001 (Backend API)
- 3002 (Frontend)
- 5432 (PostgreSQL - 내부만)
```

**보안 권장사항**:
- Frontend만 외부 노출
- Backend는 내부 네트워크만
- PostgreSQL은 localhost만

---

## 📋 NAS 배포 단계별 가이드

### Phase 1: 사전 테스트 (로컬, 1-2일)

**목표**: Constitutional 통과율 90%+ 달성

**작업**:
1. **Constitutional 로직 분석**
   ```python
   # backend/constitution/constitution.py 수정
   # 실패 이유 로깅 추가
   logger.warning(f"Constitutional validation failed: {reason}")
   logger.warning(f"  Proposal: {proposal}")
   logger.warning(f"  Context: {context}")
   ```

2. **테스트 토론 실행** (10개 종목)
   ```bash
   python backend/scripts/test_war_room_single.py NVDA
   python backend/scripts/test_war_room_single.py GOOGL
   python backend/scripts/test_war_room_single.py AAPL
   python backend/scripts/test_war_room_single.py MSFT
   python backend/scripts/test_war_room_single.py TSLA
   # ... 5개 더
   ```

3. **통과율 확인**
   ```sql
   SELECT
       COUNT(*) FILTER (WHERE constitutional_valid) as passed,
       COUNT(*) as total,
       ROUND(COUNT(*) FILTER (WHERE constitutional_valid)::numeric / COUNT(*) * 100, 1) as pass_rate
   FROM ai_debate_sessions
   WHERE created_at >= NOW() - INTERVAL '1 day';
   ```

4. **목표 달성 확인**
   - [ ] 통과율 >= 90%
   - [ ] 시그널 생성율 >= 70%
   - [ ] 에이전트 투표 정상 저장

### Phase 2: Docker 이미지 빌드 (1일)

**Dockerfile 작성** (`backend/Dockerfile`):
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스 코드 복사
COPY . .

# 환경 변수
ENV PYTHONPATH=/app
ENV PORT=8001

# 실행
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
```

**Frontend Dockerfile** (`frontend/Dockerfile`):
```dockerfile
FROM node:22-alpine

WORKDIR /app

# 의존성 설치
COPY package*.json ./
RUN npm install

# 소스 코드 복사
COPY . .

# 빌드
RUN npm run build

# Nginx 서빙
FROM nginx:alpine
COPY --from=0 /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 3002
CMD ["nginx", "-g", "daemon off;"]
```

**docker-compose.yml**:
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: ai_trading
      POSTGRES_USER: trading_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backend/database:/docker-entrypoint-initdb.d
    ports:
      - "5432:5432"
    restart: unless-stopped

  backend:
    build: ./backend
    environment:
      DATABASE_URL: postgresql://trading_user:${DB_PASSWORD}@postgres:5432/ai_trading
      KIS_IS_VIRTUAL: "true"
      GEMINI_API_KEY: ${GEMINI_API_KEY}
      CLAUDE_API_KEY: ${CLAUDE_API_KEY}
      OPENAI_API_KEY: ${OPENAI_API_KEY}
    depends_on:
      - postgres
    ports:
      - "8001:8001"
    restart: unless-stopped
    volumes:
      - ./backend:/app
      - ./logs:/app/logs

  frontend:
    build: ./frontend
    ports:
      - "3002:3002"
    depends_on:
      - backend
    restart: unless-stopped

  scheduler:
    build: ./backend
    command: python backend/automation/war_room_scheduler.py
    environment:
      DATABASE_URL: postgresql://trading_user:${DB_PASSWORD}@postgres:5432/ai_trading
    depends_on:
      - postgres
      - backend
    restart: unless-stopped

volumes:
  postgres_data:
```

**빌드 및 테스트**:
```bash
# 로컬에서 먼저 테스트
docker-compose build
docker-compose up -d
docker-compose logs -f

# 확인
curl http://localhost:8001/health
curl http://localhost:3002
```

### Phase 3: NAS 업로드 및 배포 (0.5일)

**파일 전송**:
```bash
# rsync 사용 (권장)
rsync -avz --exclude 'node_modules' --exclude '__pycache__' \
  d:/code/ai-trading-system/ \
  nas_user@nas_ip:/volume1/docker/ai-trading-system/

# 또는 Git clone
ssh nas_user@nas_ip
cd /volume1/docker/ai-trading-system
git clone https://github.com/psh355q-ui/564w7yt3w45.git .
```

**NAS에서 실행**:
```bash
# SSH로 NAS 접속
ssh nas_user@nas_ip

# 프로젝트 디렉토리 이동
cd /volume1/docker/ai-trading-system

# .env 파일 생성
nano .env
# (환경 변수 입력)

# Docker Compose 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f backend
```

### Phase 4: 자동화 설정 (0.5일)

**War Room 스케줄러 확인**:
```bash
# scheduler 컨테이너 로그
docker-compose logs -f scheduler

# 수동 테스트
docker-compose exec backend python backend/automation/war_room_scheduler.py
```

**Cron 설정** (Alternative):
```bash
# NAS crontab
crontab -e

# 매일 오전 9시, 오후 3시 War Room 실행
0 9 * * * docker-compose -f /volume1/docker/ai-trading-system/docker-compose.yml exec -T backend python backend/automation/war_room_scheduler.py
0 15 * * * docker-compose -f /volume1/docker/ai-trading-system/docker-compose.yml exec -T backend python backend/automation/war_room_scheduler.py
```

### Phase 5: 모니터링 설정 (1일)

**로그 수집**:
```bash
# docker-compose.yml에 logging 추가
services:
  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

**헬스체크**:
```yaml
services:
  backend:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

**Slack 알림** (Optional):
```python
# backend/monitoring/slack_notifier.py
import requests

def send_slack_notification(message: str):
    webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
    if webhook_url:
        requests.post(webhook_url, json={"text": message})

# 일일 요약 전송
send_slack_notification(f"""
📊 AI Trading System Daily Report
- War Room Sessions: {session_count}
- Constitutional Pass Rate: {pass_rate:.1%}
- Agent Votes: {vote_count}
- Top Performer: {best_agent}
""")
```

---

## ⚠️ 중요 주의사항

### 1. 실거래 방지

**반드시 확인**:
```bash
# .env 파일
KIS_IS_VIRTUAL=true  # 절대 false로 설정하지 말 것!

# 코드에서도 확인
if os.environ.get("KIS_IS_VIRTUAL", "true").lower() != "true":
    raise Exception("❌ REAL TRADING IS DISABLED!")
```

### 2. API 키 보안

**절대 하지 말 것**:
- ❌ .env 파일을 Git에 커밋
- ❌ API 키를 코드에 하드코딩
- ❌ 로그에 API 키 노출

**올바른 방법**:
- ✅ .env 파일은 NAS에만 존재
- ✅ .env.example만 Git에 커밋
- ✅ 환경 변수로만 접근

### 3. 데이터 백업

**일일 백업 스크립트**:
```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d)
BACKUP_DIR=/volume1/backups/ai-trading

# PostgreSQL 백업
docker-compose exec -T postgres pg_dump -U trading_user ai_trading > $BACKUP_DIR/db_$DATE.sql

# 로그 백업
cp -r logs $BACKUP_DIR/logs_$DATE

# 7일 이상 된 백업 삭제
find $BACKUP_DIR -type f -mtime +7 -delete
```

**Cron 설정**:
```bash
# 매일 자정 백업
0 0 * * * /volume1/docker/ai-trading-system/backup.sh
```

---

## 📊 배포 후 모니터링

### 일일 체크리스트

**매일 확인**:
```bash
# 1. 서비스 상태
docker-compose ps

# 2. 데이터 축적 현황
docker-compose exec backend python backend/scripts/check_data_readiness.py

# 3. 에러 로그
docker-compose logs --tail=100 backend | grep ERROR

# 4. Constitutional 통과율
docker-compose exec postgres psql -U trading_user -d ai_trading -c "
SELECT
    COUNT(*) FILTER (WHERE constitutional_valid) * 100.0 / COUNT(*) as pass_rate
FROM ai_debate_sessions
WHERE created_at >= NOW() - INTERVAL '1 day';
"
```

### 주간 리뷰

**매주 일요일**:
```bash
# 1. 누적 데이터 통계
python backend/scripts/weekly_report.py

# 2. 에이전트 성과 분석
curl -X POST http://localhost:8001/api/performance/calculate-weights

# 3. 데이터베이스 정리
docker-compose exec postgres vacuumdb -U trading_user -d ai_trading

# 4. 로그 정리 (30일 이상)
find logs -type f -mtime +30 -delete
```

---

## 🎯 배포 결정 기준

### ✅ 배포 가능 조건

- [x] Constitutional 통과율 >= 90%
- [x] 에이전트 투표 정상 저장
- [x] Price tracking 정상 작동
- [ ] 로컬에서 24시간 안정 운영
- [ ] Docker 이미지 빌드 성공
- [ ] 모든 환경 변수 설정 완료

### ⚠️ 배포 보류 조건

- [ ] Constitutional 통과율 < 90%
- [ ] 에이전트 오류 빈발
- [ ] DB 연결 불안정
- [ ] API 키 없음

---

## 📝 권장 배포 순서

### 현재 상태 (2025-12-27)

**완료**:
- ✅ 시스템 구축 완료
- ✅ Yahoo Finance fallback
- ✅ DB 저장 정상

**미완료**:
- ❌ Constitutional 통과율 (37.5%)
- ⏳ 충분한 데이터 축적
- ⏳ 로컬 안정성 검증

### 권장 순서

1. **로컬 테스트 (1-2일)**
   - Constitutional 통과율 90%+ 달성
   - 10개 종목 토론 성공
   - 에이전트 투표 정상 확인

2. **Docker 빌드 (1일)**
   - Dockerfile 작성
   - docker-compose.yml 작성
   - 로컬에서 Docker 테스트

3. **NAS 배포 (0.5일)**
   - 파일 업로드
   - 환경 변수 설정
   - Docker Compose 실행

4. **자동화 설정 (0.5일)**
   - War Room 스케줄러
   - 24시간 평가 스케줄러
   - 백업 스크립트

5. **모니터링 (1일)**
   - 로그 수집
   - 헬스체크
   - Slack 알림

**총 예상 기간**: 3-4일

---

## 🚀 최종 결론

### 지금 바로 NAS 배포?

**❌ 권장하지 않음**

**이유**:
1. Constitutional 통과율이 너무 낮음 (37.5%)
2. 대부분의 토론이 시그널 생성 안됨
3. 자동화해봤자 무용지물

### 권장 순서

**1단계** (1-2일): 로컬에서 Constitutional 문제 해결
```bash
# 오늘 오후 ~ 내일
- Constitutional 로직 분석
- 10개 종목 테스트
- 통과율 90%+ 달성
```

**2단계** (1일): Docker 빌드 및 로컬 테스트
```bash
# 모레
- Dockerfile 작성
- docker-compose 테스트
- 로컬에서 24시간 운영
```

**3단계** (1일): NAS 배포
```bash
# 그 다음날
- NAS 업로드
- 환경 설정
- 자동화 시작
```

**목표 날짜**: 2025-12-30 ~ 2025-12-31 NAS 배포

---

**작성일**: 2025-12-27
**다음 체크포인트**: Constitutional 통과율 90% 달성 시
**최종 목표**: NAS에서 24/7 자동 데이터 축적 → 1-2주 후 실거래

🎯 **먼저 Constitutional 문제를 해결하고, 그 다음 NAS 배포를 진행하는 것이 안전합니다!**

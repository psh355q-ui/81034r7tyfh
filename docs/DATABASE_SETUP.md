# Database Setup Guide

**작성일**: 2025-12-15  
**목적**: Constitutional AI Trading System 데이터베이스 설정

---

## 📋 필요한 테이블

### 1. `shadow_trades`
거부된 AI 제안의 가상 추적

**목적**: "방어한 손실" 측정

**주요 컬럼**:
- `ticker`, `action`, `entry_price`
- `virtual_pnl`, `virtual_pnl_pct`
- `rejection_reason`, `violated_articles`
- `status` (TRACKING, DEFENSIVE_WIN, MISSED_OPPORTUNITY)

---

### 2. `proposals`
AI 제안 및 Commander 승인 워크플로우

**목적**: 헌법 제3조 (인간 최종 결정권)

**주요 컬럼**:
- `ticker`, `action`, `target_price`
- `is_constitutional`, `violated_articles`
- `status` (PENDING, APPROVED, REJECTED)
- `telegram_message_id`
- `approved_by`, `approved_at`

---

## 🚀 마이그레이션 실행

### Option 1: Alembic 사용 (권장)

```bash
# 1. Backend 디렉토리로 이동
cd backend

# 2. 현재 상태 확인
alembic current

# 3. 마이그레이션 히스토리
alembic history

# 4. 최신 버전으로 업그레이드
alembic upgrade head

# 5. 결과 확인
alembic current
```

---

### Option 2: SQL 직접 실행

PostgreSQL에 직접 연결하여 실행:

```sql
-- shadow_trades 테이블
CREATE TABLE shadow_trades (
    id UUID PRIMARY KEY,
    proposal_id UUID,
    ticker VARCHAR(10) NOT NULL,
    action VARCHAR(10) NOT NULL,
    entry_price FLOAT NOT NULL,
    exit_price FLOAT,
    shares INTEGER DEFAULT 0,
    virtual_pnl FLOAT DEFAULT 0.0,
    virtual_pnl_pct FLOAT DEFAULT 0.0,
    rejection_reason VARCHAR(200),
    violated_articles TEXT,
    status VARCHAR(20) DEFAULT 'TRACKING',
    tracking_days INTEGER DEFAULT 7,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    closed_at TIMESTAMP,
    notes TEXT
);

CREATE INDEX idx_shadow_trades_ticker ON shadow_trades(ticker);
CREATE INDEX idx_shadow_trades_status ON shadow_trades(status);
CREATE INDEX idx_shadow_trades_created_at ON shadow_trades(created_at);

-- proposals 테이블
CREATE TABLE proposals (
    id UUID PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    action VARCHAR(10) NOT NULL,
    target_price FLOAT NOT NULL,
    position_size FLOAT DEFAULT 0.0,
    order_value_usd FLOAT DEFAULT 0.0,
    shares INTEGER DEFAULT 0,
    reasoning TEXT,
    confidence FLOAT DEFAULT 0.0,
    consensus_level FLOAT DEFAULT 0.0,
    debate_summary TEXT,
    model_votes JSONB,
    is_constitutional BOOLEAN DEFAULT FALSE,
    violated_articles TEXT,
    constitutional_warnings TEXT,
    status VARCHAR(20) DEFAULT 'PENDING',
    is_approved BOOLEAN DEFAULT FALSE,
    approved_by VARCHAR(100),
    approved_at TIMESTAMP,
    rejection_reason VARCHAR(200),
    rejected_at TIMESTAMP,
    executed_at TIMESTAMP,
    execution_price FLOAT,
    market_regime VARCHAR(20),
    vix FLOAT,
    news_title VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    telegram_message_id VARCHAR(50),
    notes TEXT
);

CREATE INDEX idx_proposals_ticker ON proposals(ticker);
CREATE INDEX idx_proposals_status ON proposals(status);
CREATE INDEX idx_proposals_created_at ON proposals(created_at);
CREATE INDEX idx_proposals_approved_at ON proposals(approved_at);
```

---

## 🔧 환경 설정

### 1. PostgreSQL 연결

`.env` 파일에 추가:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/ai_trading
```

**현재 설정** (alembic.ini):
```
postgresql://postgres:postgres@localhost:5434/ai_trading
```

---

### 2. 데이터베이스 생성

```bash
# PostgreSQL 접속
psql -U postgres

# 데이터베이스 생성
CREATE DATABASE ai_trading;

# 확인
\l

# 연결
\c ai_trading

# 테이블 확인
\dt
```

---

## ✅ 검증

### 1. 테이블 생성 확인

```sql
-- 테이블 리스트
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public';

-- 컬럼 확인
\d shadow_trades
\d proposals
```

---

### 2. 인덱스 확인

```sql
SELECT indexname, tablename 
FROM pg_indexes 
WHERE schemaname = 'public';
```

---

### 3. 샘플 데이터 삽입

```sql
-- Shadow Trade 테스트
INSERT INTO shadow_trades (
    id, ticker, action, entry_price, rejection_reason, status
) VALUES (
    gen_random_uuid(),
    'AAPL',
    'BUY',
    195.50,
    '헌법 위반',
    'TRACKING'
);

-- Proposal 테스트
INSERT INTO proposals (
    id, ticker, action, target_price, status, is_constitutional
) VALUES (
    gen_random_uuid(),
    'NVDA',
    'BUY',
    500.00,
    'PENDING',
    FALSE
);

-- 확인
SELECT * FROM shadow_trades;
SELECT * FROM proposals;
```

---

## 📊 마이그레이션 상태

**생성된 마이그레이션**:
- ✅ `251215_shadow_trades.py`
- ✅ `251215_proposals.py`

**실행 상태**:
- ⏳ 대기 중 (PostgreSQL 연결 필요)

---

## 🚨 문제 해결

### PostgreSQL이 실행되지 않음
```bash
# Windows
net start postgresql-x64-14

# macOS
brew services start postgresql

# Linux
sudo systemctl start postgresql
```

---

### 연결 거부 (Connection refused)
- 포트 확인: 5432 or 5434?
- 방화벽 확인
- pg_hba.conf 권한 확인

---

### Alembic 버전 충돌
```bash
# 현재 버전 확인
alembic current

# 강제 스탬프
alembic stamp head

# 재시도
alembic upgrade head
```

---

## 📝 다음 단계

1. ✅ PostgreSQL 실행
2. ✅ 데이터베이스 생성
3. ⏳ 마이그레이션 실행
4. ⏳ 테이블 확인
5. ⏳ Python 코드로 연결 테스트

---

**작성일**: 2025-12-15 20:10 KST  
**상태**: 마이그레이션 준비 완료

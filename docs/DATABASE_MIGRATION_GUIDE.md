# Database Migration Guide

## Current Issue

Migration 실행 시 PostgreSQL 연결 오류가 발생했습니다.

**Error**: `sqlalchemy.exc.OperationalError: could not connect to server`

**Database URL**: `postgresql://postgres:postgres@localhost:5434/ai_trading`

---

## Solutions

### Option 1: PostgreSQL 시작 (권장)

#### Windows

1. **서비스에서 시작**:
   - `Win + R` → `services.msc`
   - "PostgreSQL" 서비스 찾기
   - 우클릭 → "시작"

2. **pgAdmin 사용**:
   - pgAdmin 실행
   - 서버 연결 확인

3. **명령어로 확인**:
   ```bash
   # PostgreSQL 실행 확인
   psql -U postgres -p 5434 -l
   ```

#### Database 생성 (필요한 경우)

```sql
-- psql에 접속 후
CREATE DATABASE ai_trading;

-- 확인
\l
```

#### Migration 실행

```bash
cd D:\code\ai-trading-system\backend

# Migration 생성
python -m alembic revision --autogenerate -m "Add UserFCMToken table"

# Migration 실행
python -m alembic upgrade head

# 확인
python -m alembic current
```

---

### Option 2: 수동 Migration 파일 생성

데이터베이스 없이도 migration 파일만 먼저 생성할 수 있습니다.

#### 파일 위치
`backend/alembic/versions/XXXX_add_userfcmtoken_table.py`

#### 파일 내용

```python
"""Add UserFCMToken table

Revision ID: XXXX
Revises: 
Create Date: 2026-01-25

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'XXXX_add_fcm_token'
down_revision = None  # 이전 migration ID로 변경
branch_labels = None
depends_on = None


def upgrade() -> None:
    # UserFCMToken 테이블 생성
    op.create_table('user_fcm_tokens',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.String(length=100), nullable=False),
        sa.Column('token', sa.String(length=300), nullable=False),
        sa.Column('device_type', sa.String(length=50), nullable=True),
        sa.Column('device_id', sa.String(length=200), nullable=True),
        sa.Column('device_name', sa.String(length=200), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('app_version', sa.String(length=50), nullable=True),
        sa.Column('os_version', sa.String(length=50), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Indexes
    op.create_index('idx_fcm_user_id', 'user_fcm_tokens', ['user_id'])
    op.create_index('idx_fcm_token', 'user_fcm_tokens', ['token'], unique=True)
    op.create_index('idx_fcm_active', 'user_fcm_tokens', ['is_active'], 
                   postgresql_where=sa.text('is_active = TRUE'))
    op.create_index('idx_fcm_user_active', 'user_fcm_tokens', ['user_id', 'is_active'])


def downgrade() -> None:
    # Rollback
    op.drop_index('idx_fcm_user_active', table_name='user_fcm_tokens')
    op.drop_index('idx_fcm_active', table_name='user_fcm_tokens')
    op.drop_index('idx_fcm_token', table_name='user_fcm_tokens')
    op.drop_index('idx_fcm_user_id', table_name='user_fcm_tokens')
    op.drop_table('user_fcm_tokens')
```

#### 실행 (나중에 PostgreSQL 실행 시)

```bash
python -m alembic upgrade head
```

---

### Option 3: SQLite 사용 (테스트용)

개발/테스트 환경에서만 사용하세요.

#### alembic.ini 수정

```ini
# Line 60 변경
# Before:
sqlalchemy.url = postgresql://postgres:postgres@localhost:5434/ai_trading

# After:
sqlalchemy.url = sqlite:///./ai_trading.db
```

#### Migration 실행

```bash
python -m alembic revision --autogenerate -m "Add UserFCMToken table"
python -m alembic upgrade head
```

---

## Verification

Migration이 성공적으로 실행되었는지 확인:

```bash
# 현재 migration 버전 확인
python -m alembic current

# 테이블 확인 (PostgreSQL)
psql -U postgres -p 5434 -d ai_trading -c "\dt user_fcm_tokens"

# 테이블 구조 확인
psql -U postgres -p 5434 -d ai_trading -c "\d user_fcm_tokens"
```

---

## Troubleshooting

### Port 5434가 사용 중이 아닌 경우

기본 포트 5432를 사용할 수 있습니다:

```ini
# alembic.ini
sqlalchemy.url = postgresql://postgres:postgres@localhost:5432/ai_trading
```

### 권한 오류

```sql
-- Database 권한 부여
GRANT ALL PRIVILEGES ON DATABASE ai_trading TO postgres;
```

### Connection Refused

1. PostgreSQL 서비스 상태 확인
2. 방화벽 설정 확인
3. pg_hba.conf 설정 확인

---

## Next Steps

Migration 완료 후:

1. Backend 시작: `python main.py`
2. Live Dashboard 테스트: http://localhost:3000/live-dashboard
3. FCM Token 등록 테스트

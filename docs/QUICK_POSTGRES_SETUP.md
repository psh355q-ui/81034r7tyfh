# PostgreSQL 18 빠른 설정 가이드

**현재 상황**: PostgreSQL 18 설치 완료 ✅  
**남은 작업**: 데이터베이스 생성 + 설정 (5분)

---

## Step 1: 데이터베이스 생성 (2분)

### 방법 A: pgAdmin 사용 (GUI)

1. **pgAdmin 실행**
   - 시작 메뉴 → PostgreSQL 18 → pgAdmin 4

2. **서버 연결**
   - 좌측: Servers → PostgreSQL 18
   - 비밀번호 입력

3. **데이터베이스 생성**
   - Databases 우클릭 → Create → Database
   - Database: `ai_trading`
   - Owner: `postgres`
   - Save 클릭

✅ 완료!

---

### 방법 B: SQL Shell 사용 (명령줄)

```powershell
# 1. SQL Shell (psql) 실행
# 시작 메뉴 → PostgreSQL 18 → SQL Shell (psql)

# Server, Database, Port, Username 모두 Enter (기본값)
# Password: (설치 시 설정한 비밀번호 입력)

# 2. 데이터베이스 생성
CREATE DATABASE ai_trading;

# 3. 확인
\l
# → ai_trading이 목록에 있으면 성공

# 4. 종료
\q
```

✅ 완료!

---

## Step 2: DATABASE_URL 설정 (1분)

### .env 파일 수정

파일: `d:\code\ai-trading-system\.env`

**추가/수정할 내용**:
```env
# PostgreSQL 18 연결
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/ai_trading
```

**예시**:
```env
# 비밀번호가 "mypassword"인 경우
DATABASE_URL=postgresql://postgres:mypassword@localhost:5432/ai_trading
```

**주의**:
- `YOUR_PASSWORD`를 실제 PostgreSQL 비밀번호로 변경
- 포트는 기본값 5432

✅ 저장!

---

## Step 3: 연결 테스트 (1분)

```powershell
# 디렉토리: d:\code\ai-trading-system

python check_env.py
```

**기대 출력**:
```
Database: ✅ postgresql://postgres:***@localhost:5432/ai_trading
```

**오류 발생 시**:
- 비밀번호 확인
- PostgreSQL 서비스 실행 확인
- 포트 번호 확인 (5432)

---

## Step 4: 마이그레이션 실행 (2분)

```powershell
# backend 폴더로 이동
cd backend

# Alembic 마이그레이션 실행
alembic upgrade head
```

**예상 출력**:
```
INFO  [alembic.runtime.migration] Running upgrade -> 251215_shadow_trades
INFO  [alembic.runtime.migration] Running upgrade 251215_shadow_trades -> 251215_proposals
```

**성공!** ✅

---

## Step 5: 테이블 확인 (선택)

```powershell
# SQL Shell에서
psql -U postgres -d ai_trading

# 테이블 목록
\dt

# 예상 출력:
#  public | alembic_version | table | postgres
#  public | proposals       | table | postgres
#  public | shadow_trades   | table | postgres

# 종료
\q
```

---

## ✅ 완료! 이제 사용 가능:

### 1. Commander Mode
```python
# Telegram으로 승인/거부
# → DB에 자동 저장
```

### 2. Shadow Trade 추적
```python
# 거부된 제안 → DB 저장
# → 7일 추적
# → 성과 측정
```

### 3. 히스토리 관리
```python
# 모든 제안 기록
# → 통계 분석
# → 성과 리포트
```

---

## 🎯 전체 시스템 테스트

```powershell
# 1. 환경 변수 확인
python check_env.py

# 2. 전체 시스템 테스트
python test_full_system.py

# 3. Constitutional 테스트
python test_constitutional_system.py
```

**기대 결과**:
```
총 환경 변수: 12개
설정된 변수: 12개 (100%)

✅ Constitutional System
✅ Yahoo Finance
✅ FRED API
✅ Telegram Bot
✅ AI Models
✅ KIS Trading
✅ Database ← NEW!
✅ Commander ← NEW!

→ 100% 완성! 🎉
```

---

**소요 시간**: 5분  
**난이도**: ⭐☆☆☆☆ (매우 쉬움)

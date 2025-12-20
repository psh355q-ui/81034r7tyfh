# PostgreSQL & Telegram Commander 설정 가이드

**작성일**: 2025-12-15 21:40 KST  
**소요 시간**: PostgreSQL (15분) + Telegram (5분) = **20분**

---

## 1️⃣ PostgreSQL 설정 (15분)

### Step 1: PostgreSQL 설치 (5분)

#### Windows
```powershell
# 1. PostgreSQL 다운로드
# https://www.postgresql.org/download/windows/
# PostgreSQL 16.x 다운로드

# 2. 설치 중 설정
비밀번호: (원하는 비밀번호 입력 - 기억해두세요!)
포트: 5432 (기본값)
로케일: Korean, Korea

# 3. 설치 완료 후 확인
psql --version
# → postgresql (PostgreSQL) 16.x
```

#### macOS
```bash
# Homebrew로 설치
brew install postgresql@16
brew services start postgresql@16

# 확인
psql --version
```

#### Linux (Ubuntu)
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

---

### Step 2: 데이터베이스 생성 (3분)

```powershell
# 1. PostgreSQL 접속 (Windows)
# 시작 메뉴 → PostgreSQL → SQL Shell (psql)

# 또는 PowerShell에서:
psql -U postgres

# 2. 비밀번호 입력
# (설치 시 설정한 비밀번호)

# 3. 데이터베이스 생성
CREATE DATABASE ai_trading;

# 4. 확인
\l
# → ai_trading 있는지 확인

# 5. 종료
\q
```

---

### Step 3: DATABASE_URL 설정 (2분)

**1. .env 파일 열기**
```
d:\code\ai-trading-system\.env
```

**2. DATABASE_URL 추가/수정**
```env
# PostgreSQL 연결
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/ai_trading
```

**예시**:
```env
# 비밀번호가 "mypassword123"인 경우
DATABASE_URL=postgresql://postgres:mypassword123@localhost:5432/ai_trading
```

**주의**: 
- `YOUR_PASSWORD`를 실제 비밀번호로 변경
- 특수문자가 있으면 URL 인코딩 필요

---

### Step 4: 마이그레이션 실행 (5분)

```powershell
# 1. backend 폴더로 이동
cd d:\code\ai-trading-system\backend

# 2. Alembic 마이그레이션 실행
alembic upgrade head
```

**예상 출력**:
```
INFO  [alembic.runtime.migration] Running upgrade -> 251215_shadow_trades
INFO  [alembic.runtime.migration] Running upgrade 251215_shadow_trades -> 251215_proposals
```

**3. 확인**:
```powershell
# PostgreSQL 재접속
psql -U postgres -d ai_trading

# 테이블 확인
\dt

# 예상 결과:
#  public | alembic_version | table | postgres
#  public | proposals       | table | postgres
#  public | shadow_trades   | table | postgres

\q
```

---

### ✅ PostgreSQL 설정 완료!

**테스트**:
```powershell
cd d:\code\ai-trading-system
python check_env.py
```

**예상 출력**:
```
Database: ✅ (postgresql://postgres:***@localhost:5432/ai_trading)
```

---

## 2️⃣ Telegram Commander Chat ID 설정 (5분)

### 현재 상태 확인

```powershell
python check_env.py
```

**현재**:
- ✅ TELEGRAM_BOT_TOKEN: 설정됨
- ✅ TELEGRAM_CHAT_ID: 설정됨
- ❌ TELEGRAM_COMMANDER_CHAT_ID: 없음

**목적**:
- `TELEGRAM_CHAT_ID`: 일반 알림용
- `TELEGRAM_COMMANDER_CHAT_ID`: 승인/거부 버튼용

---

### 방법 1: 같은 ID 사용 (1분) - **추천**

**가장 간단한 방법**: 기존 Chat ID 재사용

**1. .env 파일 열기**

**2. 추가**:
```env
# 기존
TELEGRAM_BOT_TOKEN=8537935678...FVQfA
TELEGRAM_CHAT_ID=68690...

# 추가 (같은 값 복사)
TELEGRAM_COMMANDER_CHAT_ID=68690...
```

**완료!** ✅

---

### 방법 2: 별도 Chat ID 사용 (5분)

**시나리오**: 알림과 승인을 분리하고 싶을 때

#### Step 1: 그룹 생성 (2분)

1. **Telegram 앱 열기**
2. **새 그룹 만들기**
   - 이름: "AI Trading Commander"
   - 멤버: 본인만
3. **봇 추가**
   - 앞에서 만든 봇 추가
   - 관리자 권한 부여

#### Step 2: Chat ID 확인 (3분)

**방법 A: 브라우저 사용**
```
1. 그룹에 아무 메시지 보내기 (예: "test")

2. 브라우저에서 접속:
https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates

3. JSON에서 "chat":{"id":-1001234567890} 찾기
   → 이 숫자가 그룹 Chat ID
   
4. .env에 추가:
TELEGRAM_COMMANDER_CHAT_ID=-1001234567890
```

**방법 B: Python 스크립트**
```python
# get_chat_id.py
import os
from dotenv import load_dotenv
import requests

load_dotenv()
token = os.getenv('TELEGRAM_BOT_TOKEN')

response = requests.get(f'https://api.telegram.org/bot{token}/getUpdates')
data = response.json()

print("모든 Chat ID:")
for update in data['result']:
    if 'message' in update:
        chat = update['message']['chat']
        print(f"  {chat['type']:10} | {chat['id']:15} | {chat.get('title', chat.get('first_name'))}")
```

실행:
```powershell
python get_chat_id.py
```

---

### ✅ Telegram 설정 완료!

**테스트**:
```powershell
python check_env.py
```

**예상 출력**:
```
Telegram Bot: ✅
Commander Chat ID: ✅
```

---

## 🎯 통합 테스트

### 모든 설정 확인

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

핵심 기능:
  Constitutional System: ✅
  Yahoo Finance: ✅
  FRED API: ✅
  Telegram Bot: ✅
  AI Models: ✅
  KIS Trading: ✅
  Database: ✅ ← NEW!
  Commander: ✅ ← NEW!
```

---

## 🚀 이제 사용 가능한 모든 기능

### 1. Commander Mode (승인/거부) ✅

```python
# Telegram으로 제안 받기
# → [승인] [거부] 버튼
# → 클릭으로 결정
# → DB에 저장
```

### 2. Shadow Trade 추적 ✅

```python
# 거부된 제안 → DB 저장
# → 7일 추적
# → DEFENSIVE_WIN or MISSED_OPPORTUNITY
# → Shield Report 생성
```

### 3. 히스토리 관리 ✅

```python
# 모든 제안 DB 저장
# → 언제든지 조회
# → 통계 분석
# → 성과 측정
```

---

## ⚠️ 문제 해결

### PostgreSQL 연결 실패

**증상**:
```
could not connect to server
```

**해결**:
```powershell
# 1. PostgreSQL 실행 확인
# 작업 관리자 → 서비스 → postgresql-x64-16

# 2. 서비스 시작
net start postgresql-x64-16

# 3. 재시도
```

---

### Telegram Bot 응답 없음

**증상**:
```
Bot not responding
```

**해결**:
```
1. Bot Token 확인
2. Chat ID 확인
3. 그룹에서 Bot 관리자 권한 확인
4. 방화벽 확인
```

---

### 마이그레이션 실패

**증상**:
```
alembic: command not found
```

**해결**:
```powershell
# Alembic 설치
pip install alembic

# 재시도
cd backend
alembic upgrade head
```

---

## 📝 요약

### Before
```
✅ Constitutional System
✅ Yahoo Finance API
✅ FRED API
✅ Telegram 알림
✅ AI Models
✅ KIS Trading

❌ Database (없음)
❌ Commander (Chat ID 없음)
```

### After (20분 후)
```
✅ Constitutional System
✅ Yahoo Finance API
✅ FRED API
✅ Telegram 알림
✅ AI Models
✅ KIS Trading
✅ Database (PostgreSQL) ← NEW!
✅ Commander (승인/거부) ← NEW!

→ 100% 완성! 🎉
```

---

**작성일**: 2025-12-15 21:40 KST  
**소요 시간**: 20분  
**난이도**: ⭐⭐☆☆☆ (쉬움)

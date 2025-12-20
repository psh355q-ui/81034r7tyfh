# Setup Wizard Guide - AI Trading System
## 초보자용 설치 가이드

**작성일**: 2025-12-10
**문서 버전**: 1.0
**옵션**: Option 5 - 문서화 보완

---

## 🎯 이 가이드의 목적

이 문서는 **프로그래밍 경험이 없거나 적은** 사용자도 AI Trading System을 설치하고 실행할 수 있도록 **단계별로 상세하게** 안내합니다.

### 예상 소요 시간
- ⏱️ 전체 설치: 약 30-45분
- 💻 필요한 사전 지식: 없음 (모두 설명됨)

---

## 📋 시작하기 전에

### 필요한 것들

1. **컴퓨터 사양**
   - OS: Windows 10 이상, macOS, 또는 Linux
   - RAM: 최소 4GB (권장 8GB 이상)
   - 저장공간: 최소 10GB

2. **인터넷 연결**
   - 안정적인 인터넷 연결 필요

3. **API 키** (나중에 발급 가능)
   - OpenAI API 키
   - KIS 증권 API 키 (선택사항)

---

## 📦 Step 1: 필수 프로그램 설치

### 1.1 Git 설치

**Git이란?** 코드를 다운로드하고 관리하는 도구입니다.

#### Windows
1. https://git-scm.com/download/win 방문
2. `64-bit Git for Windows Setup` 다운로드
3. 다운로드한 파일 실행
4. 모든 옵션 기본값으로 "Next" 클릭
5. 설치 완료 후 "Finish"

#### macOS
```bash
# 터미널을 열고 (Spotlight에서 "Terminal" 검색)
xcode-select --install
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install git
```

**설치 확인**:
```bash
# 터미널/명령 프롬프트를 열고 실행
git --version
# 예상 출력: git version 2.40.0
```

### 1.2 Docker Desktop 설치

**Docker란?** 프로그램을 컨테이너에 담아 쉽게 실행할 수 있게 해주는 도구입니다.

#### Windows / macOS
1. https://www.docker.com/products/docker-desktop 방문
2. "Download for Windows" 또는 "Download for Mac" 클릭
3. 다운로드한 파일 실행
4. 설치 마법사 따라가기
5. 설치 후 컴퓨터 재시작

#### Linux (Ubuntu)
```bash
# 1. Docker 설치
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 2. 현재 사용자를 docker 그룹에 추가
sudo usermod -aG docker $USER

# 3. 재로그인 또는 재부팅
```

**설치 확인**:
```bash
docker --version
# 예상 출력: Docker version 24.0.0

docker-compose --version
# 예상 출력: Docker Compose version 2.20.0
```

### 1.3 Python 설치 (선택사항)

**Python이란?** AI Trading System이 사용하는 프로그래밍 언어입니다.

> **참고**: Docker를 사용하면 Python을 별도로 설치하지 않아도 됩니다. 하지만 개발에 참여하려면 설치하는 것이 좋습니다.

#### Windows
1. https://www.python.org/downloads/ 방문
2. "Download Python 3.11" 클릭
3. 다운로드한 파일 실행
4. **중요**: "Add Python to PATH" 체크박스 선택!
5. "Install Now" 클릭

#### macOS
```bash
# Homebrew 설치 (패키지 관리자)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Python 설치
brew install python@3.11
```

#### Linux
```bash
sudo apt update
sudo apt install python3.11 python3-pip
```

**설치 확인**:
```bash
python --version
# 예상 출력: Python 3.11.0

pip --version
# 예상 출력: pip 23.0.0
```

---

## 💾 Step 2: 프로젝트 다운로드

### 2.1 프로젝트 폴더 만들기

**Windows**:
```cmd
# 명령 프롬프트 (CMD) 열기 (Win + R → "cmd" 입력 → Enter)

# 원하는 위치로 이동 (예: Documents)
cd %USERPROFILE%\Documents

# 프로젝트 폴더 생성
mkdir ai-trading-workspace
cd ai-trading-workspace
```

**macOS / Linux**:
```bash
# 터미널 열기

# 홈 디렉토리로 이동
cd ~

# 프로젝트 폴더 생성
mkdir ai-trading-workspace
cd ai-trading-workspace
```

### 2.2 GitHub에서 코드 다운로드

```bash
# Git Clone 실행
git clone https://github.com/your-username/ai-trading-system.git

# 프로젝트 폴더로 이동
cd ai-trading-system

# 파일 확인
ls
# 예상 출력: backend, frontend, docs, docker-compose.yml, ...
```

---

## 🔑 Step 3: API 키 설정

### 3.1 OpenAI API 키 발급

1. https://platform.openai.com/signup 방문
2. 계정 생성 (Google/Microsoft 계정으로 가능)
3. 로그인 후 https://platform.openai.com/api-keys 방문
4. "Create new secret key" 클릭
5. 키 이름 입력 (예: "AI Trading System")
6. **중요**: 생성된 키를 복사하여 안전한 곳에 저장
   - 형식: `sk-xxxxxxxxxxxxxxxxxxxxxxxx`
   - **주의**: 이 키는 다시 볼 수 없으므로 반드시 저장!

### 3.2 KIS 증권 API 키 발급 (선택사항)

> **참고**: 실제 거래를 하지 않고 시스템만 테스트하려면 이 단계는 건너뛰어도 됩니다.

1. https://www.koreainvestment.com/ 방문
2. 계좌 개설 (없는 경우)
3. https://apiportal.koreainvestment.com/ 방문
4. 로그인 후 "모의투자 신청"
5. APP KEY와 APP SECRET 복사

### 3.3 환경 변수 파일 생성

```bash
# .env.example 파일을 .env로 복사
cp .env.example .env

# .env 파일 편집
# Windows: notepad .env
# macOS: open -e .env
# Linux: nano .env
```

**.env 파일 내용 (예시)**:
```bash
# OpenAI API
OPENAI_API_KEY=sk-your-actual-key-here

# KIS API (선택사항)
KIS_APP_KEY=PSyour-app-key-here
KIS_APP_SECRET=your-app-secret-here
KIS_BASE_URL=https://openapivts.koreainvestment.com:29443  # 모의투자

# Database (기본값 사용)
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/ai_trading

# Redis (기본값 사용)
REDIS_URL=redis://redis:6379

# 보안
WEBHOOK_SECRET=your-random-32-character-secret-key-here
```

**중요**:
- `OPENAI_API_KEY`는 반드시 입력 (필수)
- `KIS_APP_KEY`와 `KIS_APP_SECRET`은 선택사항
- 나머지는 기본값 사용 가능

---

## 🚀 Step 4: 시스템 실행

### 4.1 Docker로 전체 시스템 시작

```bash
# 터미널/명령 프롬프트에서 프로젝트 폴더로 이동
cd ai-trading-system

# Docker Compose로 전체 시스템 시작
docker-compose up -d

# 실행 확인
docker-compose ps
```

**예상 출력**:
```
NAME                SERVICE             STATUS
backend             backend             running
frontend            frontend            running
postgres            postgres            running
redis               redis               running
```

**시간**: 첫 실행 시 5-10분 소요 (이미지 다운로드)

### 4.2 시스템 접속 확인

1. **프론트엔드 (웹 인터페이스)**
   - 브라우저에서 http://localhost:3000 접속
   - AI Trading Dashboard가 보이면 성공!

2. **백엔드 API (선택사항)**
   - 브라우저에서 http://localhost:8000/docs 접속
   - API 문서가 보이면 성공!

3. **데이터베이스 (선택사항)**
   ```bash
   docker exec -it postgres psql -U postgres -d ai_trading
   # SQL 프롬프트: ai_trading=#
   \dt  # 테이블 목록 확인
   \q   # 종료
   ```

---

## 🧪 Step 5: 첫 번째 테스트

### 5.1 간단한 주식 조회

1. 브라우저에서 http://localhost:3000 접속
2. 상단 검색창에 "AAPL" 입력
3. Apple 주식 정보가 표시되면 성공!

### 5.2 API 테스트 (선택사항)

```bash
# 터미널에서 실행
curl http://localhost:8000/api/v1/stock/AAPL

# 예상 응답: JSON 형식의 AAPL 주식 데이터
```

### 5.3 AI 분석 테스트

1. 프론트엔드에서 "NVDA" 검색
2. "AI 분석" 버튼 클릭
3. AI가 생성한 분석 리포트 확인

---

## ⚙️ Step 6: 추가 설정 (선택사항)

### 6.1 Telegram 알림 설정

1. Telegram에서 @BotFather 검색
2. `/newbot` 명령 실행
3. 봇 이름 및 username 설정
4. 생성된 API Token 복사

**.env 파일에 추가**:
```bash
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=your-chat-id
```

### 6.2 실거래 계좌 연결

> **경고**: 실거래는 실제 돈을 사용합니다. 충분히 테스트한 후에만 진행하세요!

1. KIS 증권에서 실거래 API 신청
2. `.env` 파일 수정:
```bash
# 모의투자 → 실거래로 변경
KIS_BASE_URL=https://openapi.koreainvestment.com:9443
```

3. 시스템 재시작:
```bash
docker-compose restart
```

---

## 🛑 Step 7: 시스템 중지 및 재시작

### 중지
```bash
# 모든 컨테이너 중지
docker-compose stop

# 또는 완전 삭제 (데이터베이스 포함)
docker-compose down
```

### 재시작
```bash
# 중지된 컨테이너 재시작
docker-compose start

# 또는 새로 시작
docker-compose up -d
```

### 로그 확인
```bash
# 전체 로그
docker-compose logs

# 특정 서비스 로그
docker-compose logs backend

# 실시간 로그 (Ctrl+C로 종료)
docker-compose logs -f
```

---

## 🔧 문제 해결 (Troubleshooting)

### 문제 1: Docker가 실행되지 않음

**증상**:
```
Cannot connect to the Docker daemon
```

**해결**:
- Docker Desktop이 실행 중인지 확인
- Windows: 시스템 트레이에서 Docker 아이콘 확인
- macOS: 상단 메뉴바에서 Docker 아이콘 확인

### 문제 2: 포트가 이미 사용 중

**증상**:
```
Error starting userland proxy: listen tcp 0.0.0.0:8000: bind: address already in use
```

**해결**:
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID번호> /F

# macOS/Linux
lsof -ti:8000 | xargs kill -9
```

### 문제 3: API 키 오류

**증상**:
```
OpenAI API error: Incorrect API key provided
```

**해결**:
1. `.env` 파일에서 `OPENAI_API_KEY` 확인
2. 키가 `sk-`로 시작하는지 확인
3. 키에 공백이나 따옴표가 없는지 확인
4. 시스템 재시작: `docker-compose restart`

### 더 많은 문제 해결 방법

상세한 문제 해결은 [Troubleshooting Guide](../09_Troubleshooting/251210_Troubleshooting_Guide.md)를 참고하세요.

---

## 📚 다음 단계

시스템이 정상 작동하면:

1. **[User Manual](../09_User_Manuals/251210_01_Quick_Start_Guide.md)** - 기본 사용법 학습
2. **[API Documentation](../07_API_Documentation/251210_API_DOCUMENTATION.md)** - API 사용법
3. **[Security Best Practices](../09_Troubleshooting/251210_Security_Best_Practices.md)** - 보안 설정
4. **[Performance Tuning](../09_Troubleshooting/251210_Performance_Tuning.md)** - 성능 최적화

---

## 💬 도움 받기

문제가 계속되면:

1. **GitHub Issues**: https://github.com/your-repo/ai-trading-system/issues
2. **Discord 커뮤니티**: https://discord.gg/your-server
3. **이메일**: support@example.com

**질문할 때 포함할 정보**:
- 운영체제 (Windows/macOS/Linux)
- 오류 메시지 (전체 복사)
- `docker-compose logs` 출력

---

## ✅ 체크리스트

설치가 완료되었는지 확인하세요:

- [ ] Git 설치됨 (`git --version`)
- [ ] Docker 설치됨 (`docker --version`)
- [ ] 프로젝트 다운로드 완료
- [ ] `.env` 파일 생성 및 API 키 입력
- [ ] `docker-compose up -d` 성공
- [ ] http://localhost:3000 접속 가능
- [ ] AAPL 주식 조회 성공
- [ ] AI 분석 테스트 성공

모두 체크되었다면 축하합니다! 🎉

---

## 🎓 용어 설명

초보자를 위한 용어 설명:

- **API**: 프로그램끼리 데이터를 주고받는 방법
- **Docker**: 프로그램을 쉽게 실행하게 해주는 도구
- **Container**: Docker 안에서 실행되는 프로그램 단위
- **Backend**: 데이터를 처리하는 서버 프로그램
- **Frontend**: 사용자가 보는 웹 화면
- **Database**: 데이터를 저장하는 곳
- **Redis**: 빠른 데이터 저장소 (캐시)
- **환경 변수**: 프로그램 설정 값 (.env 파일)

---

**문서 버전**: 1.0
**최종 업데이트**: 2025-12-10
**작성자**: AI Trading System Team

**피드백**: 이 가이드가 도움이 되었나요? 개선 제안은 GitHub Issues로 보내주세요!

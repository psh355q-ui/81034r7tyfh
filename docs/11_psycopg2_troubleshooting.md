# psycopg2 연결 실패 트러블슈팅 가이드

**작성일**: 2025-12-09  
**환경**: Windows 11 + Docker Desktop + Python 3.14

---

## ❌ 문제 현상

```python
import psycopg2
conn = psycopg2.connect(host='localhost', port=5434, dbname='ai_trading', 
                        user='postgres', password='postgres123')
```

**에러 메시지:**
```
UnicodeDecodeError: 'utf-8' codec can't decode byte 0xb8 in position 63: invalid start byte
```

---

## 🔍 시도한 해결 방법

| # | 시도 내용 | 결과 |
|---|----------|------|
| 1 | 호스트 주소 변경 (localhost → 127.0.0.1 → Docker IP) | ❌ 실패 |
| 2 | psycopg → psycopg2-binary 변경 | ❌ 같은 오류 |
| 3 | pg_hba.conf → md5 인증으로 변경 | ❌ 실패 |
| 4 | postgresql.conf → password_encryption=md5 | ❌ 실패 |
| 5 | postgresql.conf → lc_messages=C | ❌ 실패 |
| 6 | docker-compose → LC_ALL=C, LANG=C | ❌ 실패 |
| 7 | Windows 코드 페이지 → chcp 65001 | ❌ 실패 |
| 8 | PGCLIENTENCODING=UTF8 환경변수 | ❌ 실패 |
| 9 | WSL + Docker Desktop 재시작 | ❌ 실패 |
| 10 | 볼륨 삭제 및 재생성 | ❌ 실패 |

---

## 🎯 근본 원인 분석

### 1. libpq 레벨 인코딩 문제

psycopg2는 PostgreSQL과 통신할 때 **libpq** (PostgreSQL C 클라이언트 라이브러리)를 사용합니다. 
이 라이브러리가 서버에서 받은 에러 메시지를 디코딩할 때 **Windows 로케일(CP949/EUC-KR)**과 
**Python의 UTF-8** 사이에서 충돌이 발생합니다.

```
PostgreSQL Server (Docker, UTF-8) 
    ↓ 에러 메시지
libpq (Windows, CP949로 해석)
    ↓ 잘못된 바이트
Python (UTF-8로 디코딩 시도)
    ↓ 실패
UnicodeDecodeError
```

### 2. Windows 시스템 로케일 영향

```
제어판 → 지역 → 관리 → 시스템 로캘
현재: 한국어(한국)
```

Windows의 시스템 로캘이 한국어로 설정되어 있으면, 일부 C 라이브러리가 
한국어 인코딩(CP949)을 기본으로 사용합니다.

---

## 🔧 확인해야 할 사항

### 1. Windows 설정

| 항목 | 확인 방법 | 예상 문제 |
|------|----------|----------|
| 시스템 로캘 | `제어판 → 지역 → 관리` | 한국어 설정 시 libpq 인코딩 문제 |
| 베타: UTF-8 사용 | `제어판 → 지역 → 관리 → 시스템 로캘 변경 → Beta: UTF-8` | 미적용 시 문제 |
| 환경변수 LANG | `echo %LANG%` | 미설정 시 시스템 로캘 따름 |

### 2. Python 환경

| 항목 | 확인 방법 | 예상 문제 |
|------|----------|----------|
| Python 버전 | `python --version` | 3.14 (최신 버전, 일부 호환성 이슈 가능) |
| psycopg2-binary 버전 | `pip show psycopg2-binary` | 2.9.11 |
| 설치 위치 | `pip show -f psycopg2-binary` | 가상환경 vs 글로벌 |

### 3. Docker 환경

| 항목 | 확인 방법 | 예상 문제 |
|------|----------|----------|
| Docker Desktop 버전 | Docker Desktop → About | WSL2 백엔드 확인 |
| WSL 배포판 | `wsl -l -v` | Ubuntu/Debian 권장 |
| 컨테이너 로케일 | `docker exec ai-trading-timescaledb locale` | C 또는 en_US.UTF-8 권장 |

### 4. 네트워크

| 항목 | 확인 방법 | 예상 문제 |
|------|----------|----------|
| 포트 리스닝 | `netstat -an \| findstr 5434` | LISTENING 확인 |
| 방화벽 규칙 | `netsh advfirewall firewall show rule name=all` | 5434 허용 필요 (관리자 권한) |
| Docker 네트워크 | `docker network ls` | bridge 네트워크 확인 |

---

## 🛠️ 잠재적 누락 프로그램/설정

### 1. Visual C++ Redistributable

psycopg2-binary는 C 확장을 사용하므로 Visual C++ Redistributable이 필요할 수 있습니다.

```powershell
# 설치 확인
Get-WmiObject Win32_Product | Where-Object { $_.Name -like "*Visual C++*" }

# 필요시 설치
# https://aka.ms/vs/17/release/vc_redist.x64.exe
```

### 2. PostgreSQL 클라이언트 (psql)

로컬에 PostgreSQL 클라이언트가 설치되어 있으면 libpq가 시스템에 이미 있어서 충돌 가능.

```powershell
# 확인
where psql

# PATH에서 제거하거나 psycopg2와 버전 맞추기
```

### 3. OpenSSL

일부 psycopg2 빌드는 OpenSSL이 필요합니다.

```powershell
# 확인
where openssl
openssl version
```

---

## ✅ 권장 해결 방법

### 방법 1: Windows UTF-8 모드 활성화 (권장)

```
1. 제어판 → 지역 → 관리 탭
2. "시스템 로캘 변경" 클릭
3. "Beta: 세계 언어 지원을 위해 Unicode UTF-8 사용" 체크
4. 재부팅
```

### 방법 2: WSL2 내에서 Python 실행

```bash
# WSL2 Ubuntu에서
pip install psycopg2-binary
python -c "import psycopg2; print('OK')"
```

### 방법 3: 백엔드 asyncpg 사용 (현재 상태)

FastAPI 백엔드는 **asyncpg** 또는 다른 비동기 드라이버를 사용하므로,
psycopg2 문제와 무관하게 정상 작동합니다.

```bash
# 백엔드 실행 (정상 작동)
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

---

## 📌 현재 상태 요약

| 항목 | 상태 |
|------|------|
| Docker TimescaleDB | ✅ 정상 (포트 5434) |
| Docker Redis | ✅ 정상 (포트 6379) |
| 테이블 생성 | ✅ 4개 생성됨 |
| FastAPI 백엔드 | ✅ 정상 작동 |
| psycopg2 직접 연결 | ❌ UnicodeDecodeError |
| Docker exec 연결 | ✅ 정상 |

### 결론

**실제 운영에는 영향 없음**. FastAPI 백엔드가 정상 작동하므로,
psycopg2 직접 연결 문제는 개발/디버깅 편의성 문제일 뿐입니다.

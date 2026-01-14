# 14일 데이터 수집 - 실행 가이드

**시작 시간**: 2025-12-28 22:52 KST  
**예상 완료**: 2026-01-11 22:52 KST

---

## 🚀 현재 실행 중

### 실행 명령어
```bash
python scripts\collect_14day_data.py --tickers AAPL NVDA MSFT --interval-hours 1 --duration-days 14
```

### 수집 설정
- **티커**: AAPL, NVDA, MSFT (3개)
- **간격**: 1시간 (하루 24회)
- **기간**: 14일 (336 사이클)
- **총 데이터 포인트**: 1,008개

---

## 📊 모니터링 방법

### 별도 터미널에서 실행
```powershell
cd d:\code\ai-trading-system\backend
python scripts\monitor_collection.py --task-name 14day_collection
```

### 로그 파일 확인
```powershell
# 실시간 로그 보기
Get-Content backend\logs\data_collection_20251228.log -Wait -Tail 20

# 또는
tail -f backend/logs/data_collection_20251228.log
```

---

## ⏸️ 중단 및 재개

### 중단
- 실행 중인 창에서 `Ctrl+C`
- 현재 사이클 번호가 표시됩니다

### 재개
```bash
cd d:\code\ai-trading-system\backend
python scripts\collect_14day_data.py --resume
```

**참고**: 재개 기능은 DB 연동 후 완전히 작동합니다. 현재는 처음부터 다시 시작됩니다.

---

## 📅 일일 체크리스트

### 매일 확인 사항 (하루 2회 권장)

#### 오전 체크 (9:00-10:00)
- [ ] 수집 프로세스 실행 중 확인
- [ ] 로그 파일에서 에러 확인
- [ ] 진행률 확인 (모니터 스크립트)

#### 저녁 체크 (21:00-22:00)
- [ ] 수집 프로세스 실행 중 확인
- [ ] 당일 수집된 데이터 개수 확인
- [ ] 누적 성공률 확인

### 체크 명령어
```powershell
# 프로세스 실행 확인
Get-Process python | Where-Object {$_.MainWindowTitle -like "*collect_14day*"}

# 오늘 로그 확인
Select-String -Path "backend\logs\data_collection_*.log" -Pattern "ERROR" -CaseSensitive

# 모니터 실행
python scripts\monitor_collection.py
```

---

## ⚠️ 주의사항

### 1. PC 절전 모드 방지
```powershell
# PowerShell에서 절전 방지 (14일간 유지)
powercfg /change standby-timeout-ac 0
powercfg /change monitor-timeout-ac 30
```

### 2. 네트워크 연결 유지
- Wi-Fi 자동 연결 설정 확인
- 고정 IP 사용 권장

### 3. 디스크 공간
- 최소 1GB 여유 공간 필요
- 디스크 공간 부족 시 수집 중단될 수 있음

### 4. Python 프로세스 종료 방지
- 터미널 창을 닫지 마세요
- 백그라운드로 실행한 경우, 프로세스 ID 기록

---

## 🔍 문제 해결

### 수집이 멈춘 경우
```bash
# 1. 로그 확인
tail -n 50 backend/logs/data_collection_20251228.log

# 2. 프로세스 확인
Get-Process python

# 3. 재시작 (필요시)
python scripts\collect_14day_data.py --tickers AAPL NVDA MSFT --interval-hours 1 --duration-days 14
```

### 에러가 반복되는 경우
- 로그 파일에서 에러 메시지 확인
- API 키 또는 네트워크 연결 확인
- 필요시 재시작

---

## ✅ 완료 후 검증 (14일 후)

### 1. 데이터 검증 실행
```bash
cd d:\code\ai-trading-system\backend
python scripts\validate_collection.py --task-name 14day_collection
```

### 2. 검증 항목
- 총 336개 사이클 완료 확인
- 3개 티커 데이터 모두 수집 확인
- 성공률 > 95% 확인

### 3. 보고서 생성
```bash
python scripts\validate_collection.py --output validation_report_$(date +%Y%m%d).txt
```

---

## 📞 문제 발생 시

### 로그 파일 위치
- `backend/logs/data_collection_20251228.log`

### 체크 포인트
1. 프로세스 실행 중인지 확인
2. 로그 파일에 최근 기록 있는지 확인 (1시간 이내)
3. 디스크 공간 충분한지 확인
4. 네트워크 연결 확인

---

**업데이트**: 2025-12-28 22:52  
**상태**: 실행 중 🚀

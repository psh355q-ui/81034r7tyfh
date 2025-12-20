# AI Trading System: Quick Start Guide

**Version**: 1.0
**Date**: 2025-12-06
**Language**: Korean (한국어)

이 가이드는 AI 트레이딩 시스템의 3대 핵심 기능(백테스팅, 리스크 관리, 페이퍼 트레이딩)을 실행하는 방법을 설명합니다.

---

## 1. 백테스팅 (Backtesting)
과거 데이터를 기반으로 AI 전략(Consensus + DCA)의 수익성을 검증합니다.

- **기능**: Yahoo Finance 실제 데이터 + 실제 AI(또는 Mock) 투표
- **실행 명령**:
  ```bash
  # 기본 실행 (최근 30일, AAPL/NVDA/TSLA)
  python scripts/run_consensus_backtest.py
  
  # 실전 모드 (Mock 사용 안 함 - API 키 필요)
  # scripts/verify_real_data_integration.py 참고
  ```
- **결과 확인**:
  - `backtest_report.txt`: 상세 분석 보고서
  - 수익률, 승률, MDD(최대 낙폭) 확인 가능

## 2. 리스크 관리 (Risk Management)
현재 포트폴리오의 위험도를 분석하고 리밸런싱(매도)을 제안합니다.

- **기능**: 집중 투자 위험 감지, VaR(위험 가치) 계산
- **실행 명령**:
  ```bash
  python scripts/run_risk_analysis.py
  ```
- **주요 시나리오**:
  - 특정 종목 비중이 20%를 넘으면 "비중 축소(SELL)" 경고 발생
  - 포트폴리오 낙폭이 심하면 "위험 경고" 발생

## 3. 페이퍼 트레이딩 (Paper Trading)
실전과 동일한 환경에서 가상 머니로 자동 매매를 수행합니다.

- **기능**: 실시간 시세 조회 -> AI 합의(Consensus) -> 자동 주문(AutoTrader)
- **실행 명령**:
  ```bash
  python scripts/run_paper_trading.py
  ```
- **작동 방식**:
  1. `KIS Broker`가 실시간 호가를 가져옵니다.
  2. `Consensus Engine`이 뉴스와 시세를 보고 투표합니다.
  3. 투표가 통과되면 `AutoTrader`가 가상 주문을 전송합니다.
  4. API Key가 없으면 안전하게 "Dry-Run" 모드로 작동하여 로그만 남깁니다.

---

## 🔑 4. 필수 설정 (Configuration)

### 4.1 API 키 설정하기 (Key Setup)
시스템을 작동시키려면 API 키가 담긴 `.env` 파일이 필요합니다.
`d:\code\ai-trading-system\.env` 파일을 생성하고 아래 내용을 채워주세요.

```ini
# --- [1] 한국투자증권 (KIS) ---
# 실전(Live) 계좌
KIS_APP_KEY=Your_Live_App_Key
KIS_APP_SECRET=Your_Live_App_Secret
KIS_ACCOUNT_NO=12345678-01

# 모의(Paper) 계좌 (페이퍼 트레이딩용)
KIS_APP_KEY_PAPER=Your_Paper_App_Key
KIS_APP_SECRET_PAPER=Your_Paper_App_Secret
KIS_ACCOUNT_NO_PAPER=88888888-01

# --- [2] AI 모델 (Consensus Engine) ---
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AIza...

# --- [3] 시스템 설정 ---
# True: 실제 주문 실행 / False: 로그만 남김 (안전모드)
TRADE_AUTO_EXECUTE=True 
```

### 4.2 시스템 켜고 끄기 (ON/OFF)

**Q. 시스템을 켜는 방법은?**
- **단순 실행**: 터미널에서 `python scripts/run_paper_trading.py` 입력.
- **백그라운드 실행**: (윈도우 서비스 등록 예정)

**Q. 시스템을 끄는 방법은?**
- 실행 중인 터미널에서 `Ctrl + C`를 눌러 강제 종료합니다.
- (향후 대시보드에서 'Stop' 버튼 제공 예정)

**Q. 안전 모드(Dry-Run)란?**
- `.env` 파일에서 `TRADE_AUTO_EXECUTE=False`로 설정하면, AI가 매수 사인을 보내도 **실제 주문은 나가지 않습니다.**
- 처음에는 반드시 `False`로 설정하여 로그를 확인하세요.

---

## 🛠 문제 해결 (Troubleshooting)

**1. "ModuleNotFoundError" 에러가 나요.**
- 프로젝트 루트 폴더(`d:\code\ai-trading-system`)에서 명령어를 실행했는지 확인하세요.
- `pip install -r requirements.txt`로 필요한 라이브러리를 설치했는지 확인하세요.

**2. "API Key Error"가 나요.**
- `.env` 파일이 존재하는지, 키 값이 정확한지 확인하세요.
- 모의투자인데 실전투자 키를 넣었는지 확인하세요.

**3. 아무 반응이 없어요.**
- 장 운영 시간(09:00 ~ 15:30)이 아니면 조용할 수 있습니다.
- 로그 파일(`logs/`)을 열어보세요.


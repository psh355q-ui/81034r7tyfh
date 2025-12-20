# .env 파일 수정 가이드

## 문제
TIMESCALE_PORT가 5541로 설정되어 있어서 백엔드가 DB에 연결하지 못함

## 해결
.env 파일에서 다음 값들을 수정하세요:

```env
# PostgreSQL / TimescaleDB 설정
TIMESCALE_HOST=localhost
TIMESCALE_PORT=5432           # ✅ 5541 → 5432로 변경
TIMESCALE_USER=postgres       # ✅ ai_trading_user → postgres로 변경  
TIMESCALE_PASSWORD=postgres   # ✅ 긴 패스워드 → postgres로 변경
TIMESCALE_DATABASE=ai_trading
```

## 수정 후
1. 백엔드 재시작: `python backend/main.py`
2. 프론트엔드 확인: http://localhost:3002

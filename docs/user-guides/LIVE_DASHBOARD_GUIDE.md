# Live Dashboard User Guide

**Phase 4 - Real-time Execution**  
**Version**: 1.0  
**Last Updated**: 2026-01-25

---

## Introduction

Live Dashboard는 실시간 시장 데이터를 모니터링할 수 있는 대시보드입니다. WebSocket을 사용하여 5초마다 자동으로 데이터가 업데이트됩니다.

---

## Accessing the Dashboard

1. Backend 실행
   ```bash
   python backend/main.py
   ```

2. Frontend 실행
   ```bash
   cd frontend
   npm run dev
   ```

3. 브라우저에서 접속
   ```
   http://localhost:3000/live-dashboard
   ```

---

## Dashboard Layout

### Header Section

![Header](../screenshots/live-dashboard-header.png)

- **Page Title**: "Live Trading Dashboard"
- **Connection Status**: Market Data와 Conflict WebSocket 연결 상태
- **Reconnect Button**: 연결이 끊어졌을 때 수동 재연결
- **Last Update Time**: 마지막 업데이트 시간

### Summary Statistics

4개의 카드로 요약 정보를 표시합니다:

1. **Watchlist Symbols**: 감시 중인 종목 수 / 업데이트된 종목 수
2. **Active Conflicts**: 현재 활성 충돌 수
3. **Top Gainer**: 최대 상승 종목
4. **Top Loser**: 최대 하락 종목

### Main Content Area

#### Left Column (70%)

**Real-time Market Data**
- 실시간 주가 표시
- 변동률 표시 (색상: 상승=초록, 하락=빨강)
- 거래량 정보
- 마지막 업데이트 시간

#### Right Column (30%)

**Conflict Alerts**
- 전략 충돌 알림 표시
- 최근 5개 알림만 표시
- 충돌 종목, 전략, 해결 방안 표시

**Live Signals**
- 실시간 트레이딩 시그널
- 신뢰도 표시
- Buy/Sell 액션 버튼

### Market Movers Section

**Top Gainers** (좌측)
- 상위 3개 상승 종목
- 종목명, 가격, 변동률

**Top Losers** (우측)
- 상위 3개 하락 종목
- 종목명, 가격, 변동률

---

## Features

### 1. Real-time Updates

- 5초마다 자동 업데이트
- WebSocket 기반 실시간 스트리밍
- 네트워크 끊김 시 자동 재연결 (5초 후)

### 2. Connection Monitoring

연결 상태 표시:
- 🟢 **Connected**: 정상 연결
- 🔴 **Disconnected**: 연결 끊김

연결이 끊어지면:
1. 자동으로 5초 후 재연결 시도
2. 수동 재연결 버튼 표시

### 3. Symbol Watchlist

기본 감시 종목:
- NVDA
- MSFT
- AAPL
- GOOGL
- AMZN
- TSLA
- META

> **Note**: 향후 업데이트에서 사용자 정의 watchlist 기능 추가 예정

### 4. Conflict Monitoring

전략 충돌이 발생하면:
1. 실시간으로 알림 표시
2. 충돌 종목, 전략 정보 표시
3. 해결 방안 제시
4. 최대 5개까지 표시 (최신순)

---

## Customization

### Changing Default Watchlist

`LiveDashboard.tsx` 파일 수정:

```typescript
const DEFAULT_WATCHLIST = ['NVDA', 'MSFT', 'AAPL', 'GOOGL', 'AMZN', 'TSLA', 'META'];
```

원하는 종목으로 변경:

```typescript
const DEFAULT_WATCHLIST = ['SPY', 'QQQ', 'IWM', 'DIA'];
```

### Changing Update Frequency

Market Data WebSocket Manager에서 변경:

`backend/api/market_data_ws.py`:
```python
UPDATE_INTERVAL = 5  # 5초 → 원하는 값으로 변경
```

---

## Troubleshooting

### Problem: No Data Showing

**해결 방법**:
1. Backend가 실행 중인지 확인
2. WebSocket 연결 상태 확인 (Header의 Status Badge)
3. Browser Console에서 에러 메시지 확인 (F12)

### Problem: Connection Keeps Dropping

**해결 방법**:
1. 네트워크 안정성 확인
2. 방화벽 설정 확인
3. Backend 로그 확인: `backend/logs/main.log`

### Problem: Quotes Not Updating

**해결 방법**:
1. yfinance rate limit 확인 (2000 req/hour)
2. Backend 로그에서 에러 확인
3. 종목 심볼이 유효한지 확인

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| R | Manual Reconnect |
| F5 | Refresh Page |

---

## Mobile Support

Live Dashboard는 반응형 디자인으로 모바일에서도 사용 가능합니다:

- **Tablet (768px+)**: 2열 레이아웃
- **Mobile (<768px)**: 1열 레이아웃

---

## Tips

1. **성능 최적화**: 감시 종목을 10개 이하로 제한
2. **배터리 절약**: 모바일에서는 화면이 켜져있을 때만 사용
3. **네트워크 절약**: Wi-Fi 연결 시 사용 권장

---

## FAQ

### Q: 왜 5초마다 업데이트되나요?

A: yfinance의 rate limit을 고려한 최적 주기입니다. 더 빠른 업데이트가 필요하면 유료 데이터 제공업체를 사용하세요.

### Q: 몇 개의 종목을 추가할 수 있나요?

A: 제한은 없지만, 성능과 rate limit을 고려하여 10개 이하를 권장합니다.

### Q: 과거 데이터를 볼 수 있나요?

A: 현재는 실시간 데이터만 표시합니다. 과거 데이터는 Trading Dashboard에서 확인하세요.

### Q: Push 알림을 받을 수 있나요?

A: 네, FCM 토큰을 등록하면 모바일로 push 알림을 받을 수 있습니다.

---

## Next Steps

- [ ] 사용자 정의 watchlist 기능
- [ ] 과거 데이터 차트
- [ ] 알림 설정 (가격 알림, 변동률 알림)
- [ ] 다크 모드 지원

---

## Support

문제가 있으면 다음을 확인하세요:
- Backend logs: `backend/logs/main.log`
- Browser Console (F12)
- WebSocket tab in DevTools

Issue 신고: [GitHub Issues](https://github.com/your-repo/issues)

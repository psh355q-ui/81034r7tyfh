# Live Dashboard Manual Test Checklist

**Date**: 2026-01-25  
**Frontend**: http://localhost:3002/live-dashboard  
**Backend**: http://localhost:8001

---

## Pre-Test Verification

- [x] Backend running on port 8001
- [x] Frontend running on port 3002
- [ ] PostgreSQL Docker container running (port 5433)

---

## Test 1: Page Load ✅

**URL**: http://localhost:3002/live-dashboard

**Expected**:
- Page loads without errors
- Title shows "Live Trading Dashboard" or similar
- Layout displays properly (header, content areas, sidebars)

**Checklist**:
- [ ] Page loads successfully
- [ ] No blank screen
- [ ] Layout is responsive

---

## Test 2: WebSocket Connection Status 🔌

**Location**: Top of dashboard (connection indicators)

**Expected**:
- Market Data WebSocket: 🟢 "Connected" (green)
- Conflict WebSocket: 🟢 "Connected" (green)

**If Disconnected**:
- Check if Backend is running: `http://localhost:8001/docs`
- Check browser console (F12) for WebSocket errors
- Look for errors like: `WebSocket connection failed`

**Checklist**:
- [ ] Market Data WebSocket shows "Connected"
- [ ] Conflict WebSocket shows "Connected"
- [ ] No red "Disconnected" status
- [ ] Auto-reconnect works (if you refresh the page)

---

## Test 3: Summary Statistics Cards 📊

**Location**: Top section with 4 cards

**Expected Cards**:
1. **Watchlist Symbols**: Shows `X / Y` (monitoring / updated)
2. **Active Conflicts**: Shows number (e.g., `0`)
3. **Top Gainer**: Shows ticker and percentage (e.g., `NVDA +2.5%`)
4. **Top Loser**: Shows ticker and percentage (e.g., `TSLA -1.2%`)

**Checklist**:
- [ ] All 4 cards are visible
- [ ] Numbers are displayed (not "0 / 0" or empty)
- [ ] Top Gainer/Loser show actual tickers

---

## Test 4: Real-time Market Data 📈

**Location**: Main content area (left side)

**Expected**:
- Table or cards showing stock quotes
- Default watchlist: NVDA, MSFT, AAPL, GOOGL, AMZN, TSLA, META
- Columns: Symbol, Price, Change %, Volume, Last Update

**Real-time Update Test**:
1. Note the current price of NVDA
2. Wait 5 seconds
3. Check if the price updates (timestamp changes)
4. Prices should update every ~5 seconds

**Checklist**:
- [ ] Market data table/cards are visible
- [ ] At least 5 stocks are displayed
- [ ] Prices are shown (not "---" or "N/A")
- [ ] Timestamps are recent (within last 10 seconds)
- [ ] **CRITICAL**: Prices update automatically every 5 seconds
- [ ] Change % shows colors (green for positive, red for negative)

---

## Test 5: Conflict Alerts Panel 🚨

**Location**: Right sidebar

**Expected**:
- Section titled "Conflict Alerts" or "Recent Conflicts"
- Shows recent 5 conflicts (may be empty if no conflicts)
- Each alert shows: Ticker, Strategy, Message, Resolution

**Checklist**:
- [ ] Conflict alerts section is visible
- [ ] If no conflicts, shows "No conflicts" or empty state
- [ ] If conflicts exist, they display properly

---

## Test 6: Market Movers Section 📊

**Location**: Bottom section

**Expected**:
- **Top Gainers** (left): Top 3 stocks with highest % gain
- **Top Losers** (right): Top 3 stocks with highest % loss
- Each shows: Ticker, Price, Change %

**Checklist**:
- [ ] Top Gainers section visible
- [ ] Top Losers section visible
- [ ] At least 1 stock in each section
- [ ] Percentages are color-coded (green/red)

---

## Test 7: Browser Console (Developer Tools) 🔧

**How to Open**: Press `F12` or `Ctrl+Shift+I`

**Expected**:
- No red error messages
- WebSocket messages like: `"WebSocket connected"` or `"Subscribed to symbols"`
- Quote messages updating every 5 seconds

**Common Errors to Check**:
- ❌ `WebSocket connection to 'ws://localhost:8001/api/market-data/ws' failed`
  - **Fix**: Check if Backend is running
- ❌ `Failed to fetch`
  - **Fix**: Check CORS settings or Backend availability
- ❌ `yfinance` rate limit errors
  - **Note**: This is expected if too many requests. Wait 1 hour.

**Checklist**:
- [ ] Console tab open
- [ ] No critical errors (red messages)
- [ ] WebSocket connection logs visible
- [ ] Quote update messages every 5 seconds

---

## Test 8: Auto-Reconnect Test 🔄

**Steps**:
1. Note the "Connected" status
2. Stop the Backend server (`Ctrl+C` in terminal)
3. Watch the status change to "Disconnected" (red)
4. Restart the Backend
5. Wait 5 seconds
6. Status should change back to "Connected" (green)

**Checklist**:
- [ ] Status changes to "Disconnected" when Backend stops
- [ ] Status changes to "Connected" when Backend restarts
- [ ] Auto-reconnect happens within 5 seconds
- [ ] Market data resumes after reconnect

---

## Test 9: Network Tab Verification 🌐

**How to Open**: F12 → Network tab → Filter: WS (WebSocket)

**Expected**:
- 2 WebSocket connections:
  1. `ws://localhost:8001/api/market-data/ws`
  2. `ws://localhost:8001/api/conflicts/ws`
- Both show status: `101 Switching Protocols`
- Messages tab shows ongoing communication

**Checklist**:
- [ ] Network tab shows 2 WS connections
- [ ] Both connections are active (green indicators)
- [ ] Messages are being sent/received

---

## Test 10: FCM Token API Test (Optional) 🔔

**Endpoint**: `http://localhost:8001/api/fcm/stats`

**Steps**:
1. Open new browser tab
2. Navigate to: `http://localhost:8001/api/fcm/stats`
3. Should see JSON response

**Expected Response**:
```json
{
  "total_tokens": 0,
  "active_tokens": 0,
  "inactive_tokens": 0,
  "device_distribution": []
}
```

**Checklist**:
- [ ] API endpoint responds
- [ ] JSON is valid
- [ ] No error messages

---

## Test Results Summary

**Overall Status**: ⬜ PASS / ⬜ FAIL

**Issues Found**:
- 

**Notes**:
- 

**Screenshots**:
- [ ] Initial page load
- [ ] Connected state
- [ ] Real-time updates
- [ ] Console logs

---

## Next Steps After Testing

✅ **If all tests pass**:
- PHASE 4 is complete!
- Ready for production deployment
- Consider Firebase configuration for push notifications

❌ **If tests fail**:
1. Check error messages in browser console
2. Verify Backend logs: `backend/logs/main.log`
3. Ensure PostgreSQL is running (port 5433)
4. Check network connectivity

---

## Quick Commands

```bash
# Check if Backend is running
curl http://localhost:8001/health

# Check if Frontend is running
curl http://localhost:3002

# Check PostgreSQL
docker ps | grep postgres

# View Backend logs
tail -f backend/logs/main.log

# Restart services if needed
docker-compose restart
```

---

**Test Completed By**: _______________  
**Date**: 2026-01-25  
**Result**: ⬜ PASS ⬜ FAIL

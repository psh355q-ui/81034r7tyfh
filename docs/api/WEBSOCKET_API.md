# WebSocket API Documentation

**Phase 4 - Real-time Execution**  
**Version**: 1.0  
**Last Updated**: 2026-01-25

---

## Overview

AI Trading System provides two WebSocket endpoints for real-time data streaming:

1. **Market Data WebSocket**: Real-time stock quotes
2. **Conflict WebSocket**: Real-time conflict alerts

---

## Market Data WebSocket

### Endpoint

```
ws://localhost:8001/api/market-data/ws
```

### Connection

```javascript
const ws = new WebSocket('ws://localhost:8001/api/market-data/ws');

ws.onopen = () => {
  console.log('Connected to Market Data WebSocket');
};
```

### Subscription

Subscribe to symbols to receive real-time quotes:

```javascript
// Subscribe to symbols
ws.send(JSON.stringify({
  type: 'subscribe',
  symbols: ['NVDA', 'AAPL', 'TSLA']
}));
```

### Unsubscribe

```javascript
// Unsubscribe from symbols
ws.send(JSON.stringify({
  type: 'unsubscribe',
  symbols: ['AAPL']
}));
```

### Receiving Quotes

```javascript
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  
  if (message.type === 'quote') {
    const quote = message.data;
    console.log(`${quote.symbol}: $${quote.price} (${quote.change}%)`);
  }
};
```

#### Quote Message Format

```json
{
  "type": "quote",
  "data": {
    "symbol": "NVDA",
    "price": 500.25,
    "change": 2.5,
    "volume": 15000000,
    "timestamp": "2026-01-25T06:00:00Z"
  }
}
```

### Error Handling

```javascript
ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('WebSocket disconnected');
  // Implement auto-reconnect logic
  setTimeout(() => {
    // Reconnect
  }, 5000);
};
```

---

## Conflict WebSocket

### Endpoint

```
ws://localhost:8001/api/conflicts/ws
```

### Connection

```javascript
const ws = new WebSocket('ws://localhost:8001/api/conflicts/ws');

ws.onopen = () => {
  console.log('Connected to Conflict WebSocket');
};
```

### Receiving Conflict Alerts

```javascript
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  
  if (message.type === 'conflict_detected') {
    const conflict = message.data;
    console.log(`Conflict detected for ${conflict.ticker}`);
    // Display alert to user
  }
};
```

#### Conflict Message Format

```json
{
  "type": "conflict_detected",
  "data": {
    "ticker": "NVDA",
    "conflicting_strategy": "Momentum",
    "owning_strategy": "Value",
    "message": "이미 보유 중인 종목입니다",
    "resolution": "보유량 유지",
    "timestamp": "2026-01-25T06:00:00Z"
  }
}
```

---

## React Hook Usage

### useMarketDataWebSocket

```typescript
import { useMarketDataWebSocket } from '@/hooks/useMarketDataWebSocket';

function MyComponent() {
  const { quotes, isConnected, error, subscribe, unsubscribe } = 
    useMarketDataWebSocket(['NVDA', 'AAPL']);

  return (
    <div>
      <p>Status: {isConnected ? 'Connected' : 'Disconnected'}</p>
      {Object.values(quotes).map(quote => (
        <div key={quote.symbol}>
          {quote.symbol}: ${quote.price} ({quote.change}%)
        </div>
      ))}
    </div>
  );
}
```

### useConflictWebSocket

```typescript
import { useConflictWebSocket } from '@/hooks/useMarketDataWebSocket';

function ConflictPanel() {
  const { conflicts, isConnected } = useConflictWebSocket();

  return (
    <div>
      <p>Conflicts: {conflicts.length}</p>
      {conflicts.map((conflict, idx) => (
        <div key={idx}>
          {conflict.ticker}: {conflict.message}
        </div>
      ))}
    </div>
  );
}
```

---

## Rate Limits

### yfinance (Free Tier)
- **Limit**: ~2000 requests/hour
- **Recommendation**: Limit to 10 symbols per client
- **Mitigation**: Use paid data provider for production (Polygon.io, Alpha Vantage)

---

## Best Practices

### 1. Auto-Reconnect

Always implement auto-reconnect logic:

```javascript
let reconnectAttempts = 0;
const maxReconnectAttempts = 5;

function connect() {
  const ws = new WebSocket('ws://localhost:8001/api/market-data/ws');
  
  ws.onclose = () => {
    if (reconnectAttempts < maxReconnectAttempts) {
      reconnectAttempts++;
      setTimeout(connect, 5000);
    }
  };
  
  ws.onopen = () => {
    reconnectAttempts = 0; // Reset on successful connection
  };
}
```

### 2. Subscription Management

Unsubscribe when components unmount:

```javascript
useEffect(() => {
  subscribe(['NVDA']);
  
  return () => {
    unsubscribe(['NVDA']);
  };
}, []);
```

### 3. Error Handling

Always handle errors gracefully:

```javascript
if (error) {
  return <Alert type="error">{error.message}</Alert>;
}
```

---

## Troubleshooting

### Connection Refused

**Problem**: `WebSocket connection to 'ws://localhost:8001/...' failed`

**Solution**:
1. Verify backend is running: `python backend/main.py`
2. Check firewall settings
3. Verify port 8001 is not blocked

### No Quotes Received

**Problem**: WebSocket connected but no quotes

**Solution**:
1. Check subscription message format
2. Verify symbols exist in yfinance
3. Check backend logs for errors

### Frequent Disconnects

**Problem**: WebSocket keeps disconnecting

**Solution**:
1. Implement heartbeat/ping mechanism
2. Check network stability
3. Reduce subscription count

---

## Security Considerations

### Production Deployment

1. **Use WSS (Secure WebSocket)**
   ```javascript
   const ws = new WebSocket('wss://yourdomain.com/api/market-data/ws');
   ```

2. **Authentication**
   - Add API key in query params or headers
   - Implement token-based authentication

3. **Rate Limiting**
   - Limit connections per IP
   - Throttle message frequency

---

## Performance Tips

1. **Batch Subscriptions**: Subscribe to multiple symbols at once
2. **Debounce Updates**: If rendering performance is poor, debounce quote updates
3. **Lazy Loading**: Only subscribe when component is visible
4. **Cleanup**: Always unsubscribe on unmount

---

## Support

For issues or questions:
- Check logs: `backend/logs/main.log`
- Verify WebSocket in Browser DevTools → Network → WS
- Test connection: `wscat -c ws://localhost:8001/api/market-data/ws`

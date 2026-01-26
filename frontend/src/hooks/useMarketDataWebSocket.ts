/**
 * Market Data WebSocket Hook
 *
 * 실시간 시장 데이터 스트리밍을 위한 React Hook
 *
 * 기능:
 * 1. WebSocket 연결 관리
 * 2. 심볼 구독/구독 해제
 * 3. 실시간 시가 데이터 상태 관리
 * 4. 연결 상태 모니터링
 *
 * 참고: Phase 4 - Real-time Execution 완성
 */

import { useState, useEffect, useRef, useCallback } from 'react';

export interface Quote {
  symbol: string;
  price: number | null;
  change: number | null;
  volume: number | null;
  timestamp: string;
}

export interface UseMarketDataWebSocketReturn {
  quotes: Record<string, Quote>;
  isConnected: boolean;
  error: Error | null;
  subscribe: (symbols: string[]) => void;
  unsubscribe: (symbols: string[]) => void;
  reconnect: () => void;
}

export const useMarketDataWebSocket = (
  symbols: string[],
  wsUrl: string = 'ws://localhost:8001/api/market-data/ws'
): UseMarketDataWebSocketReturn => {
  const [quotes, setQuotes] = useState<Record<string, Quote>>({});
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const subscribedSymbolsRef = useRef<Set<string>>(new Set());

  // WebSocket 연결 함수
  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('[MarketDataWS] Connected');
        setIsConnected(true);
        setError(null);

        // 초기 심볼 구독
        if (symbols.length > 0) {
          ws.send(JSON.stringify({
            type: 'subscribe',
            symbols: symbols
          }));
          subscribedSymbolsRef.current = new Set(symbols);
        }
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);

          if (message.type === 'quote') {
            const quote = message.data as Quote;
            setQuotes((prev) => ({
              ...prev,
              [quote.symbol]: quote
            }));
          }
        } catch (err) {
          console.error('[MarketDataWS] Message parse error:', err);
        }
      };

      ws.onerror = (err) => {
        console.error('[MarketDataWS] WebSocket error:', err);
        setError(new Error('WebSocket connection error'));
      };

      ws.onclose = () => {
        console.log('[MarketDataWS] Disconnected');
        setIsConnected(false);
        wsRef.current = null;

        // 자동 재연결 (5초 후)
        setTimeout(() => {
          console.log('[MarketDataWS] Attempting to reconnect...');
          connect();
        }, 5000);
      };
    } catch (err) {
      console.error('[MarketDataWS] Connection error:', err);
      setError(err as Error);
    }
  }, [wsUrl, symbols]);

  // 연결 해제 함수
  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsConnected(false);
  }, []);

  // 심볼 구독 함수
  const subscribe = useCallback((newSymbols: string[]) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      console.warn('[MarketDataWS] Cannot subscribe: WebSocket not connected');
      return;
    }

    const symbolsToSubscribe = newSymbols.filter(
      (s) => !subscribedSymbolsRef.current.has(s)
    );

    if (symbolsToSubscribe.length === 0) {
      return;
    }

    wsRef.current.send(JSON.stringify({
      type: 'subscribe',
      symbols: symbolsToSubscribe
    }));

    symbolsToSubscribe.forEach((s) => subscribedSymbolsRef.current.add(s));
    console.log(`[MarketDataWS] Subscribed to: ${symbolsToSubscribe.join(', ')}`);
  }, []);

  // 심볼 구독 해제 함수
  const unsubscribe = useCallback((symbolsToRemove: string[]) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      return;
    }

    const symbolsToUnsubscribe = symbolsToRemove.filter((s) =>
      subscribedSymbolsRef.current.has(s)
    );

    if (symbolsToUnsubscribe.length === 0) {
      return;
    }

    wsRef.current.send(JSON.stringify({
      type: 'unsubscribe',
      symbols: symbolsToUnsubscribe
    }));

    symbolsToUnsubscribe.forEach((s) => subscribedSymbolsRef.current.delete(s));

    // 상태에서도 제거
    setQuotes((prev) => {
      const newQuotes = { ...prev };
      symbolsToUnsubscribe.forEach((s) => delete newQuotes[s]);
      return newQuotes;
    });

    console.log(`[MarketDataWS] Unsubscribed from: ${symbolsToUnsubscribe.join(', ')}`);
  }, []);

  // 재연결 함수
  const reconnect = useCallback(() => {
    disconnect();
    setTimeout(() => {
      connect();
    }, 1000);
  }, [disconnect, connect]);

  // 마운트 시 연결
  useEffect(() => {
    connect();

    // 언마운트 시 연결 해제
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  // 심볼 목록 변경 시 구독 업데이트
  useEffect(() => {
    if (!isConnected) {
      return;
    }

    const currentSymbols = subscribedSymbolsRef.current;
    const newSymbols = new Set(symbols);

    // 새로운 심볼 구독
    const toSubscribe = symbols.filter((s) => !currentSymbols.has(s));
    if (toSubscribe.length > 0) {
      subscribe(toSubscribe);
    }

    // 제거된 심볼 구독 해제
    const toUnsubscribe = Array.from(currentSymbols).filter((s) => !newSymbols.has(s));
    if (toUnsubscribe.length > 0) {
      unsubscribe(toUnsubscribe);
    }
  }, [symbols, isConnected, subscribe, unsubscribe]);

  return {
    quotes,
    isConnected,
    error,
    subscribe,
    unsubscribe,
    reconnect
  };
};


/**
 * Conflict WebSocket Hook
 *
 * 실시간 충돌 알림 스트리밍을 위한 React Hook
 */

export interface ConflictAlert {
  ticker: string;
  conflicting_strategy: string;
  owning_strategy: string;
  message: string;
  resolution: string;
  timestamp: string;
}

export const useConflictWebSocket = (
  wsUrl: string = 'ws://localhost:8001/api/conflicts/ws'
) => {
  const [conflicts, setConflicts] = useState<ConflictAlert[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('[ConflictWS] Connected');
      setIsConnected(true);
    };

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);

        if (message.type === 'conflict_detected') {
          setConflicts((prev) => [message.data, ...prev].slice(0, 100)); // 최대 100개 유지
        }
      } catch (err) {
        console.error('[ConflictWS] Message parse error:', err);
      }
    };

    ws.onerror = (err) => {
      console.error('[ConflictWS] WebSocket error:', err);
    };

    ws.onclose = () => {
      console.log('[ConflictWS] Disconnected');
      setIsConnected(false);

      // 자동 재연결
      setTimeout(() => {
        console.log('[ConflictWS] Attempting to reconnect...');
      }, 5000);
    };

    return () => {
      ws.close();
    };
  }, [wsUrl]);

  return { conflicts, isConnected };
};

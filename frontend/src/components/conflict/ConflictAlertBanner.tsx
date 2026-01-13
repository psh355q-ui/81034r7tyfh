/**
 * Conflict Alert Banner Component
 *
 * Phase 5, T5.5: Conflict Alert UI
 *
 * Real-time conflict alert banner that:
 * - Subscribes to CONFLICT_DETECTED events via WebSocket
 * - Displays recent conflicts in a prominent banner
 * - Shows ticker, conflicting strategies, and resolution
 * - Auto-dismissible with manual close option
 */

import React, { useState, useEffect } from 'react';
import type { OrderConflict } from '../../types/strategy';
import { PERSONA_NAMES, STRATEGY_COLORS } from '../../types/strategy';

interface ConflictAlertBannerProps {
  maxConflicts?: number;
  autoDismissMs?: number;
}

const WS_URL = window.location.hostname === 'localhost'
  ? 'ws://127.0.0.1:8001/api/conflicts/ws'
  : `ws://${window.location.hostname}:8001/api/conflicts/ws`;

export function ConflictAlertBanner({
  maxConflicts = 3,
  autoDismissMs = 10000
}: ConflictAlertBannerProps) {
  const [conflicts, setConflicts] = useState<OrderConflict[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isDismissed, setIsDismissed] = useState(false);

  useEffect(() => {
    // WebSocket connection for real-time conflict events
    const ws = new WebSocket(WS_URL);

    ws.onopen = () => {
      console.log('[ConflictWS] Connected to conflict event stream');
      setIsConnected(true);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log('[ConflictWS] Message:', data);

        if (data.type === 'CONFLICT_DETECTED') {
          const conflict: OrderConflict = data.data;

          // Add to conflicts list (keep only maxConflicts)
          setConflicts((prev) => {
            const updated = [conflict, ...prev].slice(0, maxConflicts);
            return updated;
          });

          // Reset dismissed state when new conflict arrives
          setIsDismissed(false);

          // Auto-dismiss after delay
          if (autoDismissMs > 0) {
            setTimeout(() => {
              setIsDismissed(true);
            }, autoDismissMs);
          }
        }
      } catch (error) {
        console.error('[ConflictWS] Parse error:', error);
      }
    };

    ws.onerror = (error) => {
      console.error('[ConflictWS] Error:', error);
      setIsConnected(false);
    };

    ws.onclose = () => {
      console.log('[ConflictWS] Disconnected');
      setIsConnected(false);
    };

    return () => {
      ws.close();
    };
  }, [maxConflicts, autoDismissMs]);

  const handleDismiss = () => {
    setIsDismissed(true);
  };

  const handleClearAll = () => {
    setConflicts([]);
    setIsDismissed(true);
  };

  // Don't render if no conflicts or dismissed
  if (conflicts.length === 0 || isDismissed) {
    return null;
  }

  const getConflictTypeLabel = (type: string) => {
    switch (type) {
      case 'position_conflict':
        return '포지션 충돌';
      case 'priority_conflict':
        return '우선순위 충돌';
      case 'ownership_locked':
        return '소유권 잠금';
      default:
        return '알 수 없는 충돌';
    }
  };

  const getResolutionLabel = (resolution: string) => {
    switch (resolution) {
      case 'blocked':
        return '차단됨';
      case 'override':
        return '오버라이드';
      case 'pending':
        return '대기 중';
      default:
        return '알 수 없음';
    }
  };

  const getResolutionColor = (resolution: string) => {
    switch (resolution) {
      case 'blocked':
        return 'bg-red-100 text-red-800';
      case 'override':
        return 'bg-yellow-100 text-yellow-800';
      case 'pending':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="bg-red-50 border-l-4 border-red-500 rounded-lg shadow-md mb-6">
      <div className="p-4">
        {/* Header */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-3">
            <span className="text-red-500 text-2xl">⚠️</span>
            <div>
              <h3 className="text-red-800 font-semibold text-lg">
                전략 충돌 감지
              </h3>
              <p className="text-red-600 text-sm mt-1">
                {conflicts.length}개의 충돌이 감지되었습니다
                {!isConnected && ' (WebSocket 연결 끊김)'}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleClearAll}
              className="px-3 py-1 text-xs text-red-600 hover:text-red-800 font-medium"
            >
              모두 지우기
            </button>
            <button
              onClick={handleDismiss}
              className="text-red-400 hover:text-red-600 transition-colors"
              aria-label="닫기"
            >
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>
        </div>

        {/* Conflict List */}
        <div className="space-y-2">
          {conflicts.map((conflict) => (
            <div
              key={conflict.id}
              className="bg-white rounded-lg border border-red-200 p-3"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3 flex-1">
                  {/* Ticker */}
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-bold text-gray-900">
                      {conflict.ticker}
                    </span>
                  </div>

                  {/* Strategies */}
                  <div className="flex items-center gap-2">
                    {conflict.strategy && (
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                          STRATEGY_COLORS[conflict.strategy.persona_type]
                        }`}
                      >
                        {PERSONA_NAMES[conflict.strategy.persona_type]}
                      </span>
                    )}
                    <span className="text-gray-400 text-xs">vs</span>
                    {conflict.conflicting_strategy && (
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                          STRATEGY_COLORS[conflict.conflicting_strategy.persona_type]
                        }`}
                      >
                        {PERSONA_NAMES[conflict.conflicting_strategy.persona_type]}
                      </span>
                    )}
                  </div>

                  {/* Conflict Type */}
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-gray-500">
                      {getConflictTypeLabel(conflict.conflict_type)}
                    </span>
                  </div>
                </div>

                {/* Resolution Badge */}
                <div>
                  <span
                    className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getResolutionColor(
                      conflict.resolution
                    )}`}
                  >
                    {getResolutionLabel(conflict.resolution)}
                  </span>
                </div>
              </div>

              {/* Reason */}
              {conflict.reason && (
                <p className="text-xs text-gray-600 mt-2 ml-2">
                  {conflict.reason}
                </p>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

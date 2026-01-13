/**
 * Position Ownership Table Component
 *
 * Phase 5, T5.4: Position Ownership Table
 *
 * Displays position ownership data with:
 * - Ticker, Strategy, Ownership Type
 * - Lock status and expiration time
 * - Pagination controls
 * - Filtering by ticker/strategy
 */

import React, { useState, useEffect } from 'react';
import { useOwnerships } from '../../hooks/useOwnerships';
import type { PositionOwnership } from '../../types/strategy';
import { PERSONA_NAMES, STRATEGY_COLORS } from '../../types/strategy';

interface PositionOwnershipTableProps {
  maxRows?: number;
  showPagination?: boolean;
}

export function PositionOwnershipTable({
  maxRows = 10,
  showPagination = true
}: PositionOwnershipTableProps) {
  const [page, setPage] = useState(1);
  const [tickerFilter, setTickerFilter] = useState('');
  const [tickerInput, setTickerInput] = useState(''); // Input field value
  const [strategyFilter, setStrategyFilter] = useState('');

  // Debounce ticker input (500ms delay)
  useEffect(() => {
    const timer = setTimeout(() => {
      setTickerFilter(tickerInput);
      setPage(1); // Reset to first page when filter changes
    }, 500);

    return () => clearTimeout(timer);
  }, [tickerInput]);

  const { data, isLoading, error } = useOwnerships({
    page,
    pageSize: maxRows,
    ticker: tickerFilter || undefined,
    strategyId: strategyFilter || undefined
  });

  const formatDate = (dateString: string | null) => {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleString('ko-KR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const isLocked = (lockedUntil: string | null) => {
    if (!lockedUntil) return false;
    return new Date(lockedUntil) > new Date();
  };

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <span className="text-red-500 text-xl">⚠️</span>
            <div>
              <h4 className="text-red-800 font-semibold text-sm">소유권 로딩 오류</h4>
              <p className="text-red-600 text-xs mt-1">
                {error instanceof Error ? error.message : '소유권 데이터를 불러오는데 실패했습니다'}
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="space-y-3">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="h-12 bg-gray-100 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  const ownerships = data?.items || [];
  const totalPages = data?.total_pages || 0;

  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden">
      {/* Filters */}
      <div className="p-4 border-b border-gray-200 bg-gray-50">
        <div className="flex gap-4">
          <div className="flex-1">
            <input
              type="text"
              placeholder="티커 검색 (예: AAPL)"
              value={tickerInput}
              onChange={(e) => setTickerInput(e.target.value.toUpperCase())}
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <button
            onClick={() => {
              setTickerInput('');
              setTickerFilter('');
              setStrategyFilter('');
              setPage(1);
            }}
            className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800 border border-gray-300 rounded-md hover:border-gray-400 transition-colors"
          >
            필터 초기화
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                티커
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                전략
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                소유권 유형
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                잠금 상태
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                생성일
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {ownerships.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-6 py-8 text-center">
                  <div className="text-gray-400 text-4xl mb-2">📭</div>
                  <p className="text-gray-500 text-sm">소유권 데이터가 없습니다</p>
                  <p className="text-gray-400 text-xs mt-1">전략이 포지션을 소유하면 여기에 표시됩니다</p>
                </td>
              </tr>
            ) : (
              ownerships.map((ownership) => (
                <tr key={ownership.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <span className="text-sm font-semibold text-gray-900">{ownership.ticker}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {ownership.strategy ? (
                      <div className="flex items-center gap-2">
                        <span
                          className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                            STRATEGY_COLORS[ownership.strategy.persona_type]
                          }`}
                        >
                          {PERSONA_NAMES[ownership.strategy.persona_type]}
                        </span>
                        <span className="text-xs text-gray-500">
                          (우선순위 {ownership.strategy.priority})
                        </span>
                      </div>
                    ) : (
                      <span className="text-sm text-gray-400">-</span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        ownership.ownership_type === 'primary'
                          ? 'bg-blue-100 text-blue-800'
                          : 'bg-purple-100 text-purple-800'
                      }`}
                    >
                      {ownership.ownership_type === 'primary' ? '독점 소유' : '공유 소유'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {isLocked(ownership.locked_until) ? (
                      <div className="flex items-center gap-2">
                        <span className="text-red-500">🔒</span>
                        <div className="text-xs">
                          <div className="text-gray-900 font-medium">잠금</div>
                          <div className="text-gray-500">{formatDate(ownership.locked_until)}</div>
                        </div>
                      </div>
                    ) : (
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                        잠금 해제
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {formatDate(ownership.created_at)}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {showPagination && totalPages > 1 && (
        <div className="px-6 py-4 border-t border-gray-200 bg-gray-50">
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-500">
              전체 {data?.total || 0}개 중 {((page - 1) * maxRows) + 1}-
              {Math.min(page * maxRows, data?.total || 0)}개 표시
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                이전
              </button>
              <span className="text-sm text-gray-700">
                {page} / {totalPages}
              </span>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                다음
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

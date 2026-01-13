/**
 * Strategy Dashboard Page
 *
 * Phase 5, T5.3: Multi-Strategy Orchestration Dashboard
 *
 * Main dashboard for viewing and managing strategies:
 * - Strategy cards grid (4 strategies)
 * - Position ownership table (to be added in T5.4)
 * - Conflict alerts (to be added in T5.5)
 */

import React, { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { StrategyCardGrid } from '../components/strategy/StrategyCardGrid';
import { PositionOwnershipTable } from '../components/ownership/PositionOwnershipTable';
import { ConflictAlertBanner } from '../components/conflict/ConflictAlertBanner';
import { useStrategies } from '../hooks/useStrategies';
import type { Strategy } from '../types/strategy';

export default function StrategyDashboard() {
  const navigate = useNavigate();
  const { data: strategies, isLoading, error } = useStrategies();

  // Sort strategies by priority (descending)
  const sortedStrategies = useMemo(() => {
    if (!strategies) return [];
    return [...strategies].sort((a, b) => b.priority - a.priority);
  }, [strategies]);

  // Calculate position counts (placeholder - will be implemented with ownership data)
  const positionCounts = useMemo(() => {
    // TODO: Fetch actual ownership data and count positions per strategy
    // For now, return mock counts
    return sortedStrategies.reduce((acc, strategy) => {
      acc[strategy.id] = 0; // Will be updated with real data
      return acc;
    }, {} as Record<string, number>);
  }, [sortedStrategies]);

  const handleStrategyClick = (strategy: Strategy) => {
    // Navigate to strategy detail page (to be implemented)
    console.log('Strategy clicked:', strategy);
    // navigate(`/strategies/${strategy.id}`);
  };

  if (error) {
    return (
      <div className="p-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <div className="flex items-start gap-3">
            <span className="text-red-500 text-2xl">⚠️</span>
            <div>
              <h3 className="text-red-800 font-semibold mb-1">전략 로딩 오류</h3>
              <p className="text-red-600 text-sm">
                {error instanceof Error ? error.message : '전략을 불러오는데 실패했습니다'}
              </p>
              <button
                onClick={() => window.location.reload()}
                className="mt-3 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 text-sm"
              >
                다시 시도
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                멀티 전략 오케스트레이터
              </h1>
              <p className="text-sm text-gray-500 mt-1">
                트레이딩 전략 및 포지션 소유권 관리
              </p>
            </div>
            <div className="flex items-center gap-3">
              {isLoading && (
                <div className="flex items-center gap-2 text-gray-500">
                  <div className="animate-spin h-4 w-4 border-2 border-blue-500 border-t-transparent rounded-full"></div>
                  <span className="text-sm">로딩 중...</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Conflict Alert Banner */}
        <ConflictAlertBanner maxConflicts={3} autoDismissMs={10000} />

        {/* Strategy Cards Section */}
        <section className="mb-12">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold text-gray-800">
              활성 전략
            </h2>
            <div className="text-sm text-gray-500">
              {sortedStrategies.length}개 전략
            </div>
          </div>

          {isLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {[1, 2, 3, 4].map((i) => (
                <div
                  key={i}
                  className="bg-white rounded-lg shadow-md p-6 animate-pulse"
                >
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 bg-gray-200 rounded"></div>
                    <div className="flex-1">
                      <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                      <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                    </div>
                  </div>
                  <div className="h-6 bg-gray-200 rounded w-1/2 mb-4"></div>
                  <div className="border-t border-gray-200 my-4"></div>
                  <div className="h-8 bg-gray-200 rounded mb-4"></div>
                  <div className="h-6 bg-gray-200 rounded"></div>
                </div>
              ))}
            </div>
          ) : (
            <StrategyCardGrid
              strategies={sortedStrategies}
              positionCounts={positionCounts}
              onStrategyClick={handleStrategyClick}
            />
          )}
        </section>

        {/* Position Ownership Table */}
        <section>
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold text-gray-800">
              포지션 소유권
            </h2>
          </div>

          <PositionOwnershipTable maxRows={10} showPagination={true} />
        </section>
      </main>
    </div>
  );
}

/**
 * Correlation Dashboard
 *
 * Phase 32: Asset Correlation
 * Date: 2025-12-30
 *
 * 📊 Data Sources:
 *   - API: GET /api/correlation/status - 계산 상태
 *   - API: GET /api/correlation/pairs - Top 상관 페어
 *   - API: POST /api/correlation/calculate - 계산 트리거
 *
 * 🔗 Dependencies:
 *   - react: useState
 *   - @tanstack/react-query: useQuery, useMutation
 *   - lucide-react: Icons
 *
 * 📤 Features:
 *   - Top correlated pairs (양의 상관계수)
 *   - Uncorrelated pairs (음의 상관계수)
 *   - 수동 계산 트리거
 *   - 계산 상태 모니터링
 *
 * 🔄 Used By:
 *   - App.tsx (route: /correlation)
 */

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import {
  TrendingUp,
  TrendingDown,
  Play,
  RefreshCw,
  CheckCircle,
  AlertCircle,
  Clock
} from 'lucide-react';

// ============================================================================
// Types
// ============================================================================

/** Correlation status */
interface CorrelationStatus {
  total_pairs: number;
  expected_pairs: number;
  coverage: number;
  last_calculated: string | null;
  active_assets: number;
}

/** Correlated pair */
interface CorrelatedPair {
  symbol1: string;
  symbol2: string;
  correlation: number;
  calculated_at: string;
}

/** Calculation result */
interface CalculationResult {
  timestamp: string;
  success: boolean;
  assets_count: number;
  pairs_calculated: number;
  records_saved: number;
  message: string;
}

// ============================================================================
// API Functions
// ============================================================================

/** Fetch correlation status */
const fetchStatus = async (): Promise<CorrelationStatus> => {
  const response = await fetch('/api/correlation/status');
  if (!response.ok) throw new Error('Failed to fetch status');
  return response.json();
};

/** Fetch top correlated pairs */
const fetchPairs = async (period: string, sortBy: string): Promise<{ pairs: CorrelatedPair[] }> => {
  const response = await fetch(`/api/correlation/pairs?period=${period}&sort_by=${sortBy}&limit=20`);
  if (!response.ok) throw new Error('Failed to fetch pairs');
  return response.json();
};

/** Calculate correlations */
const calculateCorrelations = async (): Promise<CalculationResult> => {
  const response = await fetch('/api/correlation/calculate', { method: 'POST' });
  if (!response.ok) throw new Error('Failed to calculate correlations');
  return response.json();
};

// ============================================================================
// Component
// ============================================================================

export const CorrelationDashboard: React.FC = () => {
  // ========================================================================
  // State Management
  // ========================================================================

  const queryClient = useQueryClient();
  const [period, setPeriod] = useState<string>('90d');
  const [lastCalcResult, setLastCalcResult] = useState<CalculationResult | null>(null);

  // ========================================================================
  // Data Fetching
  // ========================================================================

  /** Fetch status */
  const { data: status, isLoading: statusLoading } = useQuery({
    queryKey: ['correlation-status'],
    queryFn: fetchStatus,
    refetchInterval: 60000
  });

  /** Fetch positive correlations */
  const { data: positivePairs, isLoading: positiveLoading } = useQuery({
    queryKey: ['correlation-pairs', period, 'highest'],
    queryFn: () => fetchPairs(period, 'highest'),
    refetchInterval: 60000
  });

  /** Fetch negative correlations */
  const { data: negativePairs, isLoading: negativeLoading } = useQuery({
    queryKey: ['correlation-pairs', period, 'lowest'],
    queryFn: () => fetchPairs(period, 'lowest'),
    refetchInterval: 60000
  });

  /** Calculation mutation */
  const calcMutation = useMutation({
    mutationFn: calculateCorrelations,
    onSuccess: (data) => {
      setLastCalcResult(data);
      // Refetch all data
      queryClient.invalidateQueries({ queryKey: ['correlation-status'] });
      queryClient.invalidateQueries({ queryKey: ['correlation-pairs'] });
    }
  });

  // ========================================================================
  // Helper Functions
  // ========================================================================

  /** Format date */
  const formatDate = (dateStr: string | null): string => {
    if (!dateStr) return 'Never';
    const date = new Date(dateStr);
    return date.toLocaleString('ko-KR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  /** Get correlation color */
  const getCorrelationColor = (corr: number): string => {
    if (corr > 0.7) return 'text-blue-600';
    if (corr > 0.3) return 'text-blue-400';
    if (corr > -0.3) return 'text-gray-600';
    if (corr > -0.7) return 'text-red-400';
    return 'text-red-600';
  };

  // ========================================================================
  // Render
  // ========================================================================

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Asset Correlation Dashboard</h1>
          <p className="text-gray-600 mt-2">
            Phase 32: 자산 간 상관관계 분석 - 포트폴리오 분산 최적화
          </p>
        </div>
        <Button
          onClick={() => calcMutation.mutate()}
          disabled={calcMutation.isPending}
          variant="primary"
        >
          <div className="flex items-center gap-2">
            {calcMutation.isPending ? (
              <RefreshCw className="h-4 w-4 animate-spin" />
            ) : (
              <Play className="h-4 w-4" />
            )}
            Calculate Correlations
          </div>
        </Button>
      </div>

      {/* Last Calculation Result */}
      {lastCalcResult && (
        <Card>
          <div className="flex items-center gap-4">
            {lastCalcResult.success ? (
              <CheckCircle className="h-8 w-8 text-green-500" />
            ) : (
              <AlertCircle className="h-8 w-8 text-red-500" />
            )}
            <div className="flex-1">
              <h3 className="font-semibold text-lg">
                {lastCalcResult.success ? 'Calculation Completed' : 'Calculation Failed'}
              </h3>
              <p className="text-sm text-gray-600">{lastCalcResult.message}</p>
              <p className="text-xs text-gray-500 mt-1">
                {formatDate(lastCalcResult.timestamp)}
              </p>
            </div>
            <div className="text-right">
              <p className="text-2xl font-bold">{lastCalcResult.pairs_calculated}</p>
              <p className="text-sm text-gray-600">Pairs Calculated</p>
            </div>
          </div>
        </Card>
      )}

      {/* Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card title="Total Pairs">
          {statusLoading ? (
            <p className="text-gray-600">Loading...</p>
          ) : (
            <div className="space-y-2">
              <p className="text-3xl font-bold">{status?.total_pairs || 0}</p>
              <p className="text-sm text-gray-600">
                Expected: {status?.expected_pairs || 0}
              </p>
            </div>
          )}
        </Card>

        <Card title="Coverage">
          {statusLoading ? (
            <p className="text-gray-600">Loading...</p>
          ) : (
            <div className="space-y-2">
              <p className="text-3xl font-bold">{status?.coverage || 0}%</p>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="h-2 rounded-full bg-blue-500"
                  style={{ width: `${status?.coverage || 0}%` }}
                />
              </div>
            </div>
          )}
        </Card>

        <Card title="Active Assets">
          {statusLoading ? (
            <p className="text-gray-600">Loading...</p>
          ) : (
            <div className="space-y-2">
              <p className="text-3xl font-bold">{status?.active_assets || 0}</p>
              <p className="text-sm text-gray-600">Multi-asset support</p>
            </div>
          )}
        </Card>

        <Card title="Last Calculated">
          {statusLoading ? (
            <p className="text-gray-600">Loading...</p>
          ) : (
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-gray-700">
                <Clock className="h-4 w-4" />
                <span className="text-sm">{formatDate(status?.last_calculated || null)}</span>
              </div>
              <p className="text-xs text-gray-500">Auto-updates daily at 01:00</p>
            </div>
          )}
        </Card>
      </div>

      {/* Period Selector */}
      <Card>
        <div className="flex items-center gap-4">
          <label className="font-medium">Time Period:</label>
          <div className="flex gap-2">
            {['30d', '90d', '1y'].map((p) => (
              <button
                key={p}
                onClick={() => setPeriod(p)}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  period === p
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {p === '30d' ? '30 Days' : p === '90d' ? '90 Days' : '1 Year'}
              </button>
            ))}
          </div>
        </div>
      </Card>

      {/* Positive Correlations */}
      <Card title="Highly Correlated Pairs (Positive)">
        <p className="text-sm text-gray-600 mb-4">
          These assets tend to move together. Good for momentum strategies, but poor for diversification.
        </p>
        {positiveLoading ? (
          <p className="text-gray-600">Loading...</p>
        ) : positivePairs?.pairs && positivePairs.pairs.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-gray-50">
                  <th className="h-12 px-4 text-left align-middle font-medium">Asset 1</th>
                  <th className="h-12 px-4 text-left align-middle font-medium">Asset 2</th>
                  <th className="h-12 px-4 text-left align-middle font-medium">Correlation</th>
                  <th className="h-12 px-4 text-left align-middle font-medium">Last Calculated</th>
                </tr>
              </thead>
              <tbody>
                {positivePairs.pairs.slice(0, 10).map((pair, idx) => (
                  <tr key={idx} className="border-b">
                    <td className="p-4 align-middle font-mono font-bold">{pair.symbol1}</td>
                    <td className="p-4 align-middle font-mono font-bold">{pair.symbol2}</td>
                    <td className="p-4 align-middle">
                      <div className="flex items-center gap-2">
                        <TrendingUp className={`h-4 w-4 ${getCorrelationColor(pair.correlation)}`} />
                        <span className={`font-semibold ${getCorrelationColor(pair.correlation)}`}>
                          {pair.correlation.toFixed(3)}
                        </span>
                      </div>
                    </td>
                    <td className="p-4 align-middle text-gray-600 text-xs">
                      {formatDate(pair.calculated_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-gray-600">No data available</p>
        )}
      </Card>

      {/* Negative Correlations */}
      <Card title="Uncorrelated / Negatively Correlated Pairs">
        <p className="text-sm text-gray-600 mb-4">
          These assets move independently or inversely. Excellent for portfolio diversification and risk reduction.
        </p>
        {negativeLoading ? (
          <p className="text-gray-600">Loading...</p>
        ) : negativePairs?.pairs && negativePairs.pairs.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-gray-50">
                  <th className="h-12 px-4 text-left align-middle font-medium">Asset 1</th>
                  <th className="h-12 px-4 text-left align-middle font-medium">Asset 2</th>
                  <th className="h-12 px-4 text-left align-middle font-medium">Correlation</th>
                  <th className="h-12 px-4 text-left align-middle font-medium">Last Calculated</th>
                </tr>
              </thead>
              <tbody>
                {negativePairs.pairs.slice(0, 10).map((pair, idx) => (
                  <tr key={idx} className="border-b">
                    <td className="p-4 align-middle font-mono font-bold">{pair.symbol1}</td>
                    <td className="p-4 align-middle font-mono font-bold">{pair.symbol2}</td>
                    <td className="p-4 align-middle">
                      <div className="flex items-center gap-2">
                        <TrendingDown className={`h-4 w-4 ${getCorrelationColor(pair.correlation)}`} />
                        <span className={`font-semibold ${getCorrelationColor(pair.correlation)}`}>
                          {pair.correlation.toFixed(3)}
                        </span>
                      </div>
                    </td>
                    <td className="p-4 align-middle text-gray-600 text-xs">
                      {formatDate(pair.calculated_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-gray-600">No data available</p>
        )}
      </Card>

      {/* Info Card */}
      <Card title="About Correlation">
        <div className="space-y-2 text-sm text-gray-700">
          <p>
            <strong>Correlation:</strong> Measures how two assets move together (-1.0 to +1.0)
          </p>
          <ul className="list-disc list-inside space-y-1 ml-4">
            <li><strong>+1.0:</strong> Perfect positive correlation (move together)</li>
            <li><strong>0.0:</strong> No correlation (move independently)</li>
            <li><strong>-1.0:</strong> Perfect negative correlation (move opposite)</li>
          </ul>
          <p className="mt-3">
            <strong>Portfolio Strategy:</strong> Combining low-correlated or negatively-correlated assets reduces overall portfolio risk without sacrificing returns.
          </p>
        </div>
      </Card>
    </div>
  );
};

export default CorrelationDashboard;

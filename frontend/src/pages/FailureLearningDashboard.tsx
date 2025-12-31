/**
 * Failure Learning Dashboard
 *
 * Phase 29 확장: 자동 학습 시스템
 * Date: 2025-12-30
 *
 * 📊 Data Sources:
 *   - API: GET /api/learning/nia - NIA 점수
 *   - API: GET /api/learning/history - 가중치 조정 히스토리
 *   - API: GET /api/learning/current-weights - 현재 가중치
 *   - API: POST /api/learning/run - 학습 사이클 실행
 *
 * 🔗 Dependencies:
 *   - react: useState
 *   - @tanstack/react-query: useQuery, useMutation
 *   - recharts: LineChart, BarChart
 *   - lucide-react: Icons
 *
 * 📤 Features:
 *   - NIA 점수 추적
 *   - 가중치 변경 히스토리
 *   - 수동 학습 사이클 실행
 *   - 가중치 트렌드 시각화
 *
 * 🔄 Used By:
 *   - App.tsx (route: /learning)
 */

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import {
  Brain,
  TrendingUp,
  TrendingDown,
  Play,
  Clock,
  AlertCircle,
  CheckCircle,
  RefreshCw
} from 'lucide-react';

// ============================================================================
// Types
// ============================================================================

/** NIA Score response */
interface NIAScore {
  nia_score: number | null;
  total_predictions: number;
  period_start: string;
  period_end: string;
  message?: string;
}

/** Weight adjustment history item */
interface WeightHistory {
  id: number;
  changed_at: string;
  changed_by: string;
  reason: string;
  weights: Record<string, number>;
}

/** Current weights response */
interface CurrentWeights {
  weights: Record<string, number>;
  last_updated: string | null;
  updated_by: string;
  reason: string;
}

/** Learning cycle result */
interface LearningCycleResult {
  timestamp: string;
  success: boolean;
  nia_score: number | null;
  weight_adjusted: boolean;
  message: string;
}

// ============================================================================
// API Functions
// ============================================================================

/** Fetch NIA score */
const fetchNIAScore = async (): Promise<NIAScore> => {
  const response = await fetch('/api/learning/nia?lookback_days=30');
  if (!response.ok) throw new Error('Failed to fetch NIA score');
  return response.json();
};

/** Fetch weight history */
const fetchWeightHistory = async (): Promise<{ history: WeightHistory[] }> => {
  const response = await fetch('/api/learning/history?limit=20');
  if (!response.ok) throw new Error('Failed to fetch weight history');
  return response.json();
};

/** Fetch current weights */
const fetchCurrentWeights = async (): Promise<CurrentWeights> => {
  const response = await fetch('/api/learning/current-weights');
  if (!response.ok) throw new Error('Failed to fetch current weights');
  return response.json();
};

/** Run learning cycle */
const runLearningCycle = async (): Promise<LearningCycleResult> => {
  const response = await fetch('/api/learning/run', { method: 'POST' });
  if (!response.ok) throw new Error('Failed to run learning cycle');
  return response.json();
};

// ============================================================================
// Component
// ============================================================================

export const FailureLearningDashboard: React.FC = () => {
  // ========================================================================
  // State Management
  // ========================================================================

  const queryClient = useQueryClient();
  const [lastRunResult, setLastRunResult] = useState<LearningCycleResult | null>(null);

  // ========================================================================
  // Data Fetching
  // ========================================================================

  /** Fetch NIA score */
  const { data: niaData, isLoading: niaLoading } = useQuery({
    queryKey: ['nia-score'],
    queryFn: fetchNIAScore,
    refetchInterval: 60000 // 60초마다 갱신
  });

  /** Fetch weight history */
  const { data: historyData, isLoading: historyLoading } = useQuery({
    queryKey: ['weight-history'],
    queryFn: fetchWeightHistory,
    refetchInterval: 60000
  });

  /** Fetch current weights */
  const { data: currentWeights, isLoading: weightsLoading } = useQuery({
    queryKey: ['current-weights'],
    queryFn: fetchCurrentWeights,
    refetchInterval: 60000
  });

  /** Learning cycle mutation */
  const learningMutation = useMutation({
    mutationFn: runLearningCycle,
    onSuccess: (data) => {
      setLastRunResult(data);
      // Refetch all data
      queryClient.invalidateQueries({ queryKey: ['nia-score'] });
      queryClient.invalidateQueries({ queryKey: ['weight-history'] });
      queryClient.invalidateQueries({ queryKey: ['current-weights'] });
    }
  });

  // ========================================================================
  // Helper Functions
  // ========================================================================

  /** Get NIA score badge variant */
  const getNIABadgeVariant = (score: number): 'danger' | 'warning' | 'success' => {
    if (score < 0.60) return 'danger';
    if (score < 0.80) return 'warning';
    return 'success';
  };

  /** Get NIA score label */
  const getNIALabel = (score: number): string => {
    if (score < 0.60) return 'Poor';
    if (score < 0.70) return 'Fair';
    if (score < 0.80) return 'Good';
    return 'Excellent';
  };

  /** Format date */
  const formatDate = (dateStr: string): string => {
    const date = new Date(dateStr);
    return date.toLocaleString('ko-KR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  /** Prepare weight trend data */
  const prepareWeightTrendData = () => {
    if (!historyData?.history) return [];

    return historyData.history
      .slice()
      .reverse()
      .slice(-10) // Last 10 changes
      .map((item) => ({
        date: formatDate(item.changed_at).split(' ')[0],
        news_agent: (item.weights.news_agent * 100).toFixed(1),
        trader_agent: (item.weights.trader_agent * 100).toFixed(1),
        risk_agent: (item.weights.risk_agent * 100).toFixed(1)
      }));
  };

  /** Prepare current weights bar chart data */
  const prepareCurrentWeightsData = () => {
    if (!currentWeights?.weights) return [];

    return Object.entries(currentWeights.weights)
      .filter(([agent]) => agent !== 'pm_agent') // Exclude PM (always 0)
      .map(([agent, weight]) => ({
        agent: agent.replace('_agent', '').replace('_', ' '),
        weight: (weight * 100).toFixed(1)
      }))
      .sort((a, b) => parseFloat(b.weight) - parseFloat(a.weight));
  };

  // ========================================================================
  // Render
  // ========================================================================

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Failure Learning Dashboard</h1>
          <p className="text-gray-600 mt-2">
            Phase 29 확장: 자동 학습 시스템 - NIA 점수 기반 가중치 자동 조정
          </p>
        </div>
        <Button
          onClick={() => learningMutation.mutate()}
          disabled={learningMutation.isPending}
          variant="primary"
        >
          <div className="flex items-center gap-2">
            {learningMutation.isPending ? (
              <RefreshCw className="h-4 w-4 animate-spin" />
            ) : (
              <Play className="h-4 w-4" />
            )}
            Run Learning Cycle
          </div>
        </Button>
      </div>

      {/* Last Run Result */}
      {lastRunResult && (
        <Card>
          <div className="flex items-center gap-4">
            {lastRunResult.success ? (
              <CheckCircle className="h-8 w-8 text-green-500" />
            ) : (
              <AlertCircle className="h-8 w-8 text-red-500" />
            )}
            <div>
              <h3 className="font-semibold text-lg">
                {lastRunResult.success ? 'Learning Cycle Completed' : 'Learning Cycle Failed'}
              </h3>
              <p className="text-sm text-gray-600">{lastRunResult.message}</p>
              <p className="text-xs text-gray-500 mt-1">
                {formatDate(lastRunResult.timestamp)}
              </p>
            </div>
            {lastRunResult.nia_score && (
              <Badge variant={getNIABadgeVariant(lastRunResult.nia_score)} className="ml-auto">
                NIA: {(lastRunResult.nia_score * 100).toFixed(1)}%
              </Badge>
            )}
          </div>
        </Card>
      )}

      {/* NIA Score Card */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card title="NIA Score (30 Days)">
          {niaLoading ? (
            <p className="text-gray-600">Loading...</p>
          ) : niaData?.nia_score !== null && niaData?.nia_score !== undefined ? (
            <div className="space-y-3">
              <div className="flex items-baseline gap-2">
                <span className="text-4xl font-bold">
                  {(niaData.nia_score * 100).toFixed(1)}%
                </span>
                <Badge variant={getNIABadgeVariant(niaData.nia_score)}>
                  {getNIALabel(niaData.nia_score)}
                </Badge>
              </div>
              <p className="text-sm text-gray-600">
                Based on {niaData.total_predictions} predictions
              </p>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className={`h-2 rounded-full ${
                    niaData.nia_score >= 0.80
                      ? 'bg-green-500'
                      : niaData.nia_score >= 0.60
                      ? 'bg-yellow-500'
                      : 'bg-red-500'
                  }`}
                  style={{ width: `${niaData.nia_score * 100}%` }}
                />
              </div>
            </div>
          ) : (
            <p className="text-gray-600">{niaData?.message || 'No data available'}</p>
          )}
        </Card>

        <Card title="Last Weight Update">
          {weightsLoading ? (
            <p className="text-gray-600">Loading...</p>
          ) : currentWeights?.last_updated ? (
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-gray-700">
                <Clock className="h-4 w-4" />
                <span className="text-sm">{formatDate(currentWeights.last_updated)}</span>
              </div>
              <p className="text-sm text-gray-600">By: {currentWeights.updated_by}</p>
              <p className="text-xs text-gray-500 mt-2">{currentWeights.reason}</p>
            </div>
          ) : (
            <p className="text-gray-600">No updates yet</p>
          )}
        </Card>

        <Card title="Auto-Learning Status">
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <Brain className="h-5 w-5 text-blue-500" />
              <span className="font-medium">Active</span>
            </div>
            <p className="text-sm text-gray-600">
              Daily cycle runs at 00:00 KST
            </p>
            <div className="flex items-center gap-2 text-sm">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
              <span className="text-gray-600">Monitoring NIA score</span>
            </div>
          </div>
        </Card>
      </div>

      {/* Current Weights */}
      <Card title="Current War Room Weights">
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={prepareCurrentWeightsData()}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="agent" angle={-45} textAnchor="end" height={80} />
            <YAxis label={{ value: 'Weight (%)', angle: -90, position: 'insideLeft' }} />
            <Tooltip formatter={(value) => `${value}%`} />
            <Bar dataKey="weight" fill="#3b82f6" />
          </BarChart>
        </ResponsiveContainer>
      </Card>

      {/* Weight Trend */}
      <Card title="Weight Adjustment Trend (Last 10 Changes)">
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={prepareWeightTrendData()}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis label={{ value: 'Weight (%)', angle: -90, position: 'insideLeft' }} />
            <Tooltip formatter={(value) => `${value}%`} />
            <Legend />
            <Line type="monotone" dataKey="news_agent" stroke="#3b82f6" name="News Agent" strokeWidth={2} />
            <Line type="monotone" dataKey="trader_agent" stroke="#10b981" name="Trader Agent" strokeWidth={2} />
            <Line type="monotone" dataKey="risk_agent" stroke="#f59e0b" name="Risk Agent" strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      </Card>

      {/* Weight History Table */}
      <Card title="Weight Adjustment History">
        {historyLoading ? (
          <p className="text-gray-600">Loading...</p>
        ) : historyData?.history && historyData.history.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-gray-50">
                  <th className="h-12 px-4 text-left align-middle font-medium">Date</th>
                  <th className="h-12 px-4 text-left align-middle font-medium">Changed By</th>
                  <th className="h-12 px-4 text-left align-middle font-medium">Reason</th>
                  <th className="h-12 px-4 text-left align-middle font-medium">News Agent</th>
                  <th className="h-12 px-4 text-left align-middle font-medium">Change</th>
                </tr>
              </thead>
              <tbody>
                {historyData.history.slice(0, 10).map((item, index) => {
                  const prevItem = historyData.history[index + 1];
                  const newsChange = prevItem
                    ? ((item.weights.news_agent - prevItem.weights.news_agent) * 100)
                    : 0;

                  return (
                    <tr key={item.id} className="border-b">
                      <td className="p-4 align-middle">{formatDate(item.changed_at)}</td>
                      <td className="p-4 align-middle">
                        <Badge variant={item.changed_by.includes('Scheduler') ? 'info' : 'default'}>
                          {item.changed_by}
                        </Badge>
                      </td>
                      <td className="p-4 align-middle text-gray-600">{item.reason}</td>
                      <td className="p-4 align-middle font-mono">
                        {(item.weights.news_agent * 100).toFixed(1)}%
                      </td>
                      <td className="p-4 align-middle">
                        {newsChange !== 0 && (
                          <div className="flex items-center gap-1">
                            {newsChange > 0 ? (
                              <TrendingUp className="h-4 w-4 text-green-500" />
                            ) : (
                              <TrendingDown className="h-4 w-4 text-red-500" />
                            )}
                            <span className={newsChange > 0 ? 'text-green-600' : 'text-red-600'}>
                              {newsChange > 0 ? '+' : ''}{newsChange.toFixed(2)}%
                            </span>
                          </div>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-gray-600">No history available</p>
        )}
      </Card>
    </div>
  );
};

export default FailureLearningDashboard;

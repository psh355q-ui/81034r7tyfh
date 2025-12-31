/**
 * Accountability Dashboard
 *
 * Phase 29: AI Prediction Accuracy Tracking
 * Date: 2025-12-30
 *
 * 📊 Data Sources:
 *   - API: GET /api/accountability/status - Scheduler status
 *   - API: GET /api/accountability/nia - News Interpretation Accuracy score
 *   - API: GET /api/accountability/interpretations - List of interpretations
 *   - API: GET /api/accountability/failed - Failed predictions
 *
 * 🔗 Dependencies:
 *   - react: useState, useEffect
 *   - @tanstack/react-query: useQuery
 *   - recharts: LineChart, BarChart, PieChart
 *   - lucide-react: Icons
 *
 * 📤 Components:
 *   - NIAScoreCard: Overall NIA score display
 *   - NIATrendChart: NIA trend over time
 *   - InterpretationsTable: List of all interpretations
 *   - FailedPredictionsCard: Failed predictions for review
 *
 * 🔄 Used By:
 *   - App.tsx (route: /accountability)
 */

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Target,
  TrendingUp,
  TrendingDown,
  AlertCircle,
  CheckCircle,
  XCircle,
  Clock,
  RefreshCw,
  Activity,
  BarChart2
} from 'lucide-react';
import { Card } from '../components/common/Card';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';

// ============================================================================
// Types
// ============================================================================

interface NIAScore {
  overall_nia: number;
  total_interpretations: number;
  verified_interpretations: number;
  pending_interpretations: number;
  nia_by_time_horizon: {
    '1h': number;
    '1d': number;
    '3d': number;
  };
  nia_by_impact: {
    HIGH: number;
    MEDIUM: number;
    LOW: number;
  };
}

interface InterpretationItem {
  id: number;
  ticker: string;
  headline_bias: string;
  expected_impact: string;
  time_horizon: string;
  confidence: number;
  reasoning: string;
  interpreted_at: string;
  accuracy_1h: number | null;
  accuracy_1d: number | null;
  accuracy_3d: number | null;
  is_verified: boolean;
}

interface FailedInterpretation {
  interpretation_id: number;
  ticker: string;
  headline_bias: string;
  expected_impact: string;
  time_horizon: string;
  confidence: number;
  actual_direction: string;
  price_change: number;
  interpreted_at: string;
  verified_at: string;
}

interface SchedulerStatus {
  is_running: boolean;
  last_run: string | null;
  next_run: string | null;
  run_interval_minutes: number;
  total_verifications_today: number;
}

// ============================================================================
// API Functions
// ============================================================================

const fetchNIAScore = async (): Promise<NIAScore> => {
  const response = await fetch('/api/accountability/nia?lookback_days=30');
  if (!response.ok) throw new Error('Failed to fetch NIA score');
  return response.json();
};

const fetchInterpretations = async (): Promise<InterpretationItem[]> => {
  const response = await fetch('/api/accountability/interpretations?limit=50');
  if (!response.ok) throw new Error('Failed to fetch interpretations');
  return response.json();
};

const fetchFailedPredictions = async (): Promise<FailedInterpretation[]> => {
  const response = await fetch('/api/accountability/failed?lookback_days=7');
  if (!response.ok) throw new Error('Failed to fetch failed predictions');
  return response.json();
};

const fetchSchedulerStatus = async (): Promise<SchedulerStatus> => {
  const response = await fetch('/api/accountability/status');
  if (!response.ok) throw new Error('Failed to fetch scheduler status');
  return response.json();
};

// ============================================================================
// Main Component
// ============================================================================

export const AccountabilityDashboard: React.FC = () => {
  const [selectedTimeHorizon, setSelectedTimeHorizon] = useState<'1h' | '1d' | '3d'>('1d');

  // Fetch data
  const { data: niaScore, isLoading: loadingNIA, refetch: refetchNIA } = useQuery({
    queryKey: ['accountability', 'nia'],
    queryFn: fetchNIAScore,
    refetchInterval: 60000 // Refresh every 1 min
  });

  const { data: interpretations, isLoading: loadingInterpretations } = useQuery({
    queryKey: ['accountability', 'interpretations'],
    queryFn: fetchInterpretations,
    refetchInterval: 60000
  });

  const { data: failedPredictions, isLoading: loadingFailed } = useQuery({
    queryKey: ['accountability', 'failed'],
    queryFn: fetchFailedPredictions,
    refetchInterval: 60000
  });

  const { data: schedulerStatus, isLoading: loadingScheduler } = useQuery({
    queryKey: ['accountability', 'status'],
    queryFn: fetchSchedulerStatus,
    refetchInterval: 30000
  });

  if (loadingNIA || loadingInterpretations || loadingFailed || loadingScheduler) {
    return <LoadingSpinner />;
  }

  if (!niaScore) {
    return <div className="error-message">Failed to load Accountability data</div>;
  }

  // Prepare chart data
  const timeHorizonData = [
    { name: '1 Hour', accuracy: niaScore.nia_by_time_horizon['1h'] * 100 },
    { name: '1 Day', accuracy: niaScore.nia_by_time_horizon['1d'] * 100 },
    { name: '3 Days', accuracy: niaScore.nia_by_time_horizon['3d'] * 100 }
  ];

  const impactData = [
    { name: 'HIGH', accuracy: niaScore.nia_by_impact.HIGH * 100, fill: '#ef4444' },
    { name: 'MEDIUM', accuracy: niaScore.nia_by_impact.MEDIUM * 100, fill: '#f59e0b' },
    { name: 'LOW', accuracy: niaScore.nia_by_impact.LOW * 100, fill: '#10b981' }
  ];

  // Calculate accuracy rate from interpretations
  const verifiedCount = interpretations?.filter(i => i.is_verified).length || 0;
  const totalCount = interpretations?.length || 0;

  return (
    <div className="accountability-dashboard">
      <div className="dashboard-header">
        <h1>
          <Target className="inline-block mr-2" size={32} />
          Accountability Dashboard
        </h1>
        <p className="text-gray-600">AI Prediction Accuracy Tracking (Phase 29)</p>
      </div>

      {/* Scheduler Status Banner */}
      {schedulerStatus && (
        <Card className="scheduler-status-banner">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-4">
              <Activity className={schedulerStatus.is_running ? "text-green-500" : "text-red-500"} />
              <div>
                <h3 className="font-semibold">
                  {schedulerStatus.is_running ? "✅ Scheduler Running" : "⚠️ Scheduler Stopped"}
                </h3>
                <p className="text-sm text-gray-600">
                  Verifies predictions every {schedulerStatus.run_interval_minutes} minutes
                </p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-sm">Verifications Today: {schedulerStatus.total_verifications_today}</p>
              {schedulerStatus.last_run && (
                <p className="text-xs text-gray-500">
                  Last Run: {new Date(schedulerStatus.last_run).toLocaleTimeString()}
                </p>
              )}
            </div>
          </div>
        </Card>
      )}

      {/* NIA Score Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Overall NIA Score</p>
              <h2 className="text-3xl font-bold" style={{ color: getNIAColor(niaScore.overall_nia) }}>
                {(niaScore.overall_nia * 100).toFixed(1)}%
              </h2>
              <p className="text-xs text-gray-500">
                {niaScore.verified_interpretations} verified / {niaScore.total_interpretations} total
              </p>
            </div>
            <Target size={48} style={{ color: getNIAColor(niaScore.overall_nia), opacity: 0.3 }} />
          </div>
        </Card>

        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Verified Interpretations</p>
              <h2 className="text-3xl font-bold text-blue-600">{niaScore.verified_interpretations}</h2>
              <p className="text-xs text-gray-500">
                {niaScore.pending_interpretations} pending verification
              </p>
            </div>
            <CheckCircle size={48} className="text-blue-600 opacity-30" />
          </div>
        </Card>

        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Accuracy Rate</p>
              <h2 className="text-3xl font-bold text-green-600">
                {verifiedCount > 0 ? ((verifiedCount / totalCount) * 100).toFixed(1) : 0}%
              </h2>
              <p className="text-xs text-gray-500">
                {verifiedCount} / {totalCount} predictions
              </p>
            </div>
            <Activity size={48} className="text-green-600 opacity-30" />
          </div>
        </Card>
      </div>

      {/* NIA by Time Horizon & Impact */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <Card>
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Clock size={20} />
            NIA by Time Horizon
          </h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={timeHorizonData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis domain={[0, 100]} />
              <Tooltip formatter={(value: number) => `${value.toFixed(1)}%`} />
              <Bar dataKey="accuracy" fill="#3b82f6" />
            </BarChart>
          </ResponsiveContainer>
        </Card>

        <Card>
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <BarChart2 size={20} />
            NIA by Impact Level
          </h3>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={impactData}
                dataKey="accuracy"
                nameKey="name"
                cx="50%"
                cy="50%"
                outerRadius={80}
                label={(entry) => `${entry.name}: ${entry.accuracy.toFixed(1)}%`}
              >
                {impactData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.fill} />
                ))}
              </Pie>
              <Tooltip formatter={(value: number) => `${value.toFixed(1)}%`} />
            </PieChart>
          </ResponsiveContainer>
        </Card>
      </div>

      {/* Failed Predictions Table */}
      {failedPredictions && failedPredictions.length > 0 && (
        <Card className="mb-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <XCircle size={20} className="text-red-500" />
            Failed Predictions (Last 7 Days)
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full table-auto">
              <thead className="bg-gray-100">
                <tr>
                  <th className="px-4 py-2 text-left">Ticker</th>
                  <th className="px-4 py-2 text-left">Predicted</th>
                  <th className="px-4 py-2 text-left">Actual</th>
                  <th className="px-4 py-2 text-right">Price Change</th>
                  <th className="px-4 py-2 text-center">Confidence</th>
                  <th className="px-4 py-2 text-left">Verified</th>
                </tr>
              </thead>
              <tbody>
                {failedPredictions.map((failed) => (
                  <tr key={failed.interpretation_id} className="border-b hover:bg-gray-50">
                    <td className="px-4 py-2 font-mono font-bold">{failed.ticker}</td>
                    <td className="px-4 py-2">
                      <span className={`px-2 py-1 rounded text-xs ${getBiasColor(failed.headline_bias)}`}>
                        {failed.headline_bias}
                      </span>
                    </td>
                    <td className="px-4 py-2">
                      <span className={`px-2 py-1 rounded text-xs ${getDirectionColor(failed.actual_direction)}`}>
                        {failed.actual_direction}
                      </span>
                    </td>
                    <td className={`px-4 py-2 text-right font-semibold ${failed.price_change > 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {failed.price_change > 0 ? '+' : ''}{failed.price_change.toFixed(2)}%
                    </td>
                    <td className="px-4 py-2 text-center">{failed.confidence}%</td>
                    <td className="px-4 py-2 text-xs text-gray-500">
                      {new Date(failed.verified_at).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* All Interpretations Table */}
      {interpretations && (
        <Card>
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Activity size={20} />
            Recent Interpretations
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full table-auto">
              <thead className="bg-gray-100">
                <tr>
                  <th className="px-4 py-2 text-left">Ticker</th>
                  <th className="px-4 py-2 text-left">Bias</th>
                  <th className="px-4 py-2 text-left">Impact</th>
                  <th className="px-4 py-2 text-center">Confidence</th>
                  <th className="px-4 py-2 text-center">1h</th>
                  <th className="px-4 py-2 text-center">1d</th>
                  <th className="px-4 py-2 text-center">3d</th>
                  <th className="px-4 py-2 text-left">Status</th>
                </tr>
              </thead>
              <tbody>
                {interpretations.slice(0, 20).map((interp) => (
                  <tr key={interp.id} className="border-b hover:bg-gray-50">
                    <td className="px-4 py-2 font-mono font-bold">{interp.ticker}</td>
                    <td className="px-4 py-2">
                      <span className={`px-2 py-1 rounded text-xs ${getBiasColor(interp.headline_bias)}`}>
                        {interp.headline_bias}
                      </span>
                    </td>
                    <td className="px-4 py-2">
                      <span className={`px-2 py-1 rounded text-xs ${getImpactColor(interp.expected_impact)}`}>
                        {interp.expected_impact}
                      </span>
                    </td>
                    <td className="px-4 py-2 text-center">{interp.confidence}%</td>
                    <td className="px-4 py-2 text-center">
                      {interp.accuracy_1h !== null ? (
                        <span style={{ color: getAccuracyColor(interp.accuracy_1h) }}>
                          {(interp.accuracy_1h * 100).toFixed(0)}%
                        </span>
                      ) : (
                        <span className="text-gray-400">-</span>
                      )}
                    </td>
                    <td className="px-4 py-2 text-center">
                      {interp.accuracy_1d !== null ? (
                        <span style={{ color: getAccuracyColor(interp.accuracy_1d) }}>
                          {(interp.accuracy_1d * 100).toFixed(0)}%
                        </span>
                      ) : (
                        <span className="text-gray-400">-</span>
                      )}
                    </td>
                    <td className="px-4 py-2 text-center">
                      {interp.accuracy_3d !== null ? (
                        <span style={{ color: getAccuracyColor(interp.accuracy_3d) }}>
                          {(interp.accuracy_3d * 100).toFixed(0)}%
                        </span>
                      ) : (
                        <span className="text-gray-400">-</span>
                      )}
                    </td>
                    <td className="px-4 py-2">
                      {interp.is_verified ? (
                        <span className="text-green-600 flex items-center gap-1">
                          <CheckCircle size={14} /> Verified
                        </span>
                      ) : (
                        <span className="text-gray-400 flex items-center gap-1">
                          <Clock size={14} /> Pending
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );
};

// ============================================================================
// Helper Functions
// ============================================================================

function getNIAColor(nia: number): string {
  if (nia >= 0.7) return '#10b981'; // Green
  if (nia >= 0.5) return '#f59e0b'; // Orange
  return '#ef4444'; // Red
}

function getAccuracyColor(accuracy: number): string {
  if (accuracy >= 0.7) return '#10b981';
  if (accuracy >= 0.5) return '#f59e0b';
  return '#ef4444';
}

function getBiasColor(bias: string): string {
  if (bias === 'BULLISH') return 'bg-green-100 text-green-800';
  if (bias === 'BEARISH') return 'bg-red-100 text-red-800';
  return 'bg-gray-100 text-gray-800';
}

function getDirectionColor(direction: string): string {
  if (direction === 'UP') return 'bg-green-100 text-green-800';
  if (direction === 'DOWN') return 'bg-red-100 text-red-800';
  return 'bg-gray-100 text-gray-800';
}

function getImpactColor(impact: string): string {
  if (impact === 'HIGH') return 'bg-red-100 text-red-800';
  if (impact === 'MEDIUM') return 'bg-yellow-100 text-yellow-800';
  return 'bg-blue-100 text-blue-800';
}

export default AccountabilityDashboard;

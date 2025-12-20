/**
 * Trade Analytics Component
 * Analyzes win/loss patterns, execution quality, hold duration, and confidence impact
 */

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ZAxis,
} from 'recharts';
import { TrendingUp, Clock, Target } from 'lucide-react';
import { Card } from '../common/Card';
import { getTradeInsights, analyticsKeys } from '../../services/analyticsApi';

interface TradeAnalyticsProps {
  startDate: string;
  endDate: string;
}

const TradeAnalytics: React.FC<TradeAnalyticsProps> = ({ startDate, endDate }) => {
  const [analysis, setAnalysis] = useState<string>('win_loss');

  const { data, isLoading, error } = useQuery({
    queryKey: analyticsKeys.trade(startDate, endDate, analysis),
    queryFn: () => getTradeInsights(startDate, endDate, analysis),
    enabled: !!startDate && !!endDate,
  });

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
    }).format(value);
  };

  const formatPercentage = (value: number) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  const renderWinLossPatterns = () => {
    if (!data?.win_loss_patterns) return null;

    const patterns = data.win_loss_patterns;
    const streaksData = [
      { name: 'Longest Win Streak', value: patterns.longest_win_streak },
      { name: 'Longest Loss Streak', value: patterns.longest_loss_streak },
      { name: 'Current Streak', value: Math.abs(patterns.current_streak_length) },
    ];

    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Win Rate</p>
                <p className="text-2xl font-bold text-green-600">
                  {(patterns.win_rate * 100).toFixed(1)}%
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  {patterns.total_wins} wins / {patterns.total_trades} trades
                </p>
              </div>
              <TrendingUp className="h-8 w-8 text-green-400" />
            </div>
          </Card>

          <Card>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Profit Factor</p>
                <p className="text-2xl font-bold text-blue-600">
                  {parseFloat(patterns.profit_factor).toFixed(2)}
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  Wins / Losses Ratio
                </p>
              </div>
              <Target className="h-8 w-8 text-blue-400" />
            </div>
          </Card>

          <Card>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Avg Win</p>
                <p className="text-2xl font-bold text-green-600">
                  {formatCurrency(parseFloat(patterns.avg_win))}
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  Per winning trade
                </p>
              </div>
            </div>
          </Card>

          <Card>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Avg Loss</p>
                <p className="text-2xl font-bold text-red-600">
                  {formatCurrency(parseFloat(patterns.avg_loss))}
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  Per losing trade
                </p>
              </div>
            </div>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <h3 className="text-lg font-semibold mb-4">Win/Loss Distribution</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart
                data={[
                  { name: 'Wins', count: patterns.total_wins, amount: parseFloat(patterns.total_win_pnl) },
                  { name: 'Losses', count: patterns.total_losses, amount: Math.abs(parseFloat(patterns.total_loss_pnl)) },
                ]}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="count" fill="#3b82f6" name="Trade Count" />
              </BarChart>
            </ResponsiveContainer>
          </Card>

          <Card>
            <h3 className="text-lg font-semibold mb-4">Streak Analysis</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={streaksData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" fill="#10b981" name="Streak Length" />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </div>

        <Card>
          <h3 className="text-lg font-semibold mb-4">Current Status</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-gray-50 p-4 rounded-lg">
              <p className="text-sm text-gray-500">Current Streak</p>
              <p className="text-xl font-bold">
                {patterns.current_streak_length > 0
                  ? `${patterns.current_streak_length} Wins`
                  : patterns.current_streak_length < 0
                  ? `${Math.abs(patterns.current_streak_length)} Losses`
                  : 'No Active Streak'}
              </p>
            </div>
            <div className="bg-gray-50 p-4 rounded-lg">
              <p className="text-sm text-gray-500">Best Win</p>
              <p className="text-xl font-bold text-green-600">
                {formatCurrency(parseFloat(patterns.best_win))}
              </p>
            </div>
            <div className="bg-gray-50 p-4 rounded-lg">
              <p className="text-sm text-gray-500">Worst Loss</p>
              <p className="text-xl font-bold text-red-600">
                {formatCurrency(parseFloat(patterns.worst_loss))}
              </p>
            </div>
          </div>
        </Card>
      </div>
    );
  };

  const renderExecutionQuality = () => {
    if (!data?.execution_quality) return null;

    const quality = data.execution_quality;

    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <div>
              <p className="text-sm text-gray-500">Avg Slippage</p>
              <p className="text-2xl font-bold text-orange-600">
                {parseFloat(quality.avg_slippage_bps).toFixed(2)} bps
              </p>
              <p className="text-xs text-gray-500 mt-1">
                Median: {parseFloat(quality.median_slippage_bps).toFixed(2)} bps
              </p>
            </div>
          </Card>

          <Card>
            <div>
              <p className="text-sm text-gray-500">Avg Execution Time</p>
              <p className="text-2xl font-bold text-blue-600">
                {parseFloat(quality.avg_execution_time_ms).toFixed(0)} ms
              </p>
              <p className="text-xs text-gray-500 mt-1">
                Median: {parseFloat(quality.median_execution_time_ms).toFixed(0)} ms
              </p>
            </div>
          </Card>

          <Card>
            <div>
              <p className="text-sm text-gray-500">Total Commissions</p>
              <p className="text-2xl font-bold text-gray-700">
                {formatCurrency(parseFloat(quality.total_commissions))}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                Avg: {formatCurrency(parseFloat(quality.avg_commission))} per trade
              </p>
            </div>
          </Card>
        </div>

        <Card>
          <h3 className="text-lg font-semibold mb-4">Slippage Impact</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-gray-50 p-4 rounded-lg">
              <p className="text-sm text-gray-500">Positive Slippage</p>
              <p className="text-xl font-bold text-green-600">
                {quality.positive_slippage_trades} trades ({((quality.positive_slippage_trades / quality.total_analyzed_trades) * 100).toFixed(1)}%)
              </p>
            </div>
            <div className="bg-gray-50 p-4 rounded-lg">
              <p className="text-sm text-gray-500">Negative Slippage</p>
              <p className="text-xl font-bold text-red-600">
                {quality.negative_slippage_trades} trades ({((quality.negative_slippage_trades / quality.total_analyzed_trades) * 100).toFixed(1)}%)
              </p>
            </div>
          </div>
        </Card>
      </div>
    );
  };

  const renderHoldDuration = () => {
    if (!data?.hold_duration_analysis) return null;

    const duration = data.hold_duration_analysis;
    const durationData = Object.entries(duration.duration_buckets || {}).map(([bucket, stats]: [string, any]) => ({
      bucket,
      count: stats.count,
      winRate: stats.win_rate * 100,
      avgPnl: parseFloat(stats.avg_pnl),
    }));

    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Avg Hold Duration</p>
                <p className="text-2xl font-bold text-blue-600">
                  {parseFloat(duration.avg_hold_hours).toFixed(1)} hrs
                </p>
              </div>
              <Clock className="h-8 w-8 text-blue-400" />
            </div>
          </Card>

          <Card>
            <div>
              <p className="text-sm text-gray-500">Median Duration</p>
              <p className="text-2xl font-bold text-purple-600">
                {parseFloat(duration.median_hold_hours).toFixed(1)} hrs
              </p>
            </div>
          </Card>

          <Card>
            <div>
              <p className="text-sm text-gray-500">Optimal Duration</p>
              <p className="text-2xl font-bold text-green-600">
                {duration.optimal_hold_time_bucket}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                Best win rate
              </p>
            </div>
          </Card>
        </div>

        <Card>
          <h3 className="text-lg font-semibold mb-4">Performance by Hold Duration</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={durationData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="bucket" />
              <YAxis yAxisId="left" />
              <YAxis yAxisId="right" orientation="right" />
              <Tooltip />
              <Legend />
              <Bar yAxisId="left" dataKey="count" fill="#3b82f6" name="Trade Count" />
              <Bar yAxisId="right" dataKey="winRate" fill="#10b981" name="Win Rate %" />
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </div>
    );
  };

  const renderConfidenceImpact = () => {
    if (!data?.confidence_impact) return null;

    const confidence = data.confidence_impact;
    const bucketData = Object.entries(confidence.confidence_buckets || {}).map(([bucket, stats]: [string, any]) => ({
      bucket,
      count: stats.count,
      winRate: stats.win_rate * 100,
      avgPnl: parseFloat(stats.avg_pnl),
    }));

    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card>
            <div>
              <p className="text-sm text-gray-500">Avg Confidence</p>
              <p className="text-2xl font-bold text-blue-600">
                {(parseFloat(confidence.avg_confidence) * 100).toFixed(1)}%
              </p>
            </div>
          </Card>

          <Card>
            <div>
              <p className="text-sm text-gray-500">Correlation (Confidence ↔ PnL)</p>
              <p className="text-2xl font-bold text-purple-600">
                {parseFloat(confidence.correlation_confidence_pnl).toFixed(3)}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                {parseFloat(confidence.correlation_confidence_pnl) > 0.3 ? 'Strong positive' : parseFloat(confidence.correlation_confidence_pnl) > 0 ? 'Weak positive' : 'Negative'}
              </p>
            </div>
          </Card>
        </div>

        <Card>
          <h3 className="text-lg font-semibold mb-4">Performance by Confidence Level</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={bucketData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="bucket" />
              <YAxis yAxisId="left" />
              <YAxis yAxisId="right" orientation="right" />
              <Tooltip />
              <Legend />
              <Bar yAxisId="left" dataKey="count" fill="#3b82f6" name="Trade Count" />
              <Bar yAxisId="right" dataKey="winRate" fill="#10b981" name="Win Rate %" />
            </BarChart>
          </ResponsiveContainer>
        </Card>

        <Card>
          <h3 className="text-lg font-semibold mb-4">Confidence Buckets Performance</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Confidence Range
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Trades
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Win Rate
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Avg PnL
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {bucketData.map((bucket) => (
                  <tr key={bucket.bucket} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {bucket.bucket}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-900">
                      {bucket.count}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right">
                      <span
                        className={`inline-flex px-2 py-1 rounded-full text-xs font-semibold ${
                          bucket.winRate >= 50
                            ? 'bg-green-100 text-green-800'
                            : 'bg-red-100 text-red-800'
                        }`}
                      >
                        {bucket.winRate.toFixed(1)}%
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right">
                      <span className={bucket.avgPnl >= 0 ? 'text-green-600' : 'text-red-600'}>
                        {formatCurrency(bucket.avgPnl)}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      </div>
    );
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
        Error loading trade analytics data
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Analysis Selector */}
      <Card>
        <div className="flex items-center gap-4">
          <label className="text-sm font-medium text-gray-700">Trade Analysis:</label>
          <select
            value={analysis}
            onChange={(e) => setAnalysis(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="win_loss">Win/Loss Patterns</option>
            <option value="execution">Execution Quality</option>
            <option value="hold_duration">Hold Duration</option>
            <option value="confidence">Confidence Impact</option>
          </select>
        </div>
      </Card>

      {/* Content */}
      {analysis === 'win_loss' && renderWinLossPatterns()}
      {analysis === 'execution' && renderExecutionQuality()}
      {analysis === 'hold_duration' && renderHoldDuration()}
      {analysis === 'confidence' && renderConfidenceImpact()}
    </div>
  );
};

export default TradeAnalytics;

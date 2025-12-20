/**
 * Risk Analytics Component
 * Provides VaR, drawdown, concentration, correlation, and stress test metrics
 */

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
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
  ResponsiveContainer,
} from 'recharts';
import { AlertTriangle, TrendingDown, Shield } from 'lucide-react';
import { Card } from '../common/Card';
import { getRiskMetrics, analyticsKeys } from '../../services/analyticsApi';

interface RiskAnalyticsProps {
  startDate: string;
  endDate: string;
}

const RiskAnalytics: React.FC<RiskAnalyticsProps> = ({ startDate, endDate }) => {
  const [metric, setMetric] = useState<string>('var');

  const { data, isLoading, error } = useQuery({
    queryKey: analyticsKeys.risk(startDate, endDate, metric),
    queryFn: () => getRiskMetrics(startDate, endDate, metric),
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

  const renderVaRMetrics = () => {
    if (!data?.var_metrics) return null;

    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">VaR (95%)</p>
                <p className="text-2xl font-bold text-red-600">
                  {formatCurrency(parseFloat(data.var_metrics.var_95_usd))}
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  {formatPercentage(parseFloat(data.var_metrics.var_95_pct))}
                </p>
              </div>
              <AlertTriangle className="h-8 w-8 text-red-400" />
            </div>
          </Card>

          <Card>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">VaR (99%)</p>
                <p className="text-2xl font-bold text-red-700">
                  {formatCurrency(parseFloat(data.var_metrics.var_99_usd))}
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  {formatPercentage(parseFloat(data.var_metrics.var_99_pct))}
                </p>
              </div>
              <AlertTriangle className="h-8 w-8 text-red-500" />
            </div>
          </Card>

          <Card>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">CVaR (95%)</p>
                <p className="text-2xl font-bold text-orange-600">
                  {formatCurrency(parseFloat(data.var_metrics.cvar_95_usd))}
                </p>
                <p className="text-xs text-gray-500 mt-1">Expected Shortfall</p>
              </div>
              <Shield className="h-8 w-8 text-orange-400" />
            </div>
          </Card>

          <Card>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">CVaR (99%)</p>
                <p className="text-2xl font-bold text-orange-700">
                  {formatCurrency(parseFloat(data.var_metrics.cvar_99_usd))}
                </p>
                <p className="text-xs text-gray-500 mt-1">Tail Risk</p>
              </div>
              <Shield className="h-8 w-8 text-orange-500" />
            </div>
          </Card>
        </div>

        <Card>
          <h3 className="text-lg font-semibold mb-4">Historical Returns Distribution</h3>
          <p className="text-sm text-gray-500 mb-4">
            Portfolio Value: {formatCurrency(parseFloat(data.var_metrics.portfolio_value))} |
            Sample Size: {data.var_metrics.sample_size} trades
          </p>
          <div className="text-sm text-gray-600">
            <p>• Value at Risk (VaR) shows the maximum expected loss at different confidence levels</p>
            <p>• Conditional VaR (CVaR) represents the average loss beyond the VaR threshold</p>
            <p>• 95% VaR means there's a 5% chance of losing more than the displayed amount in a single period</p>
          </div>
        </Card>
      </div>
    );
  };

  const renderDrawdownMetrics = () => {
    if (!data?.drawdown_metrics) return null;

    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Max Drawdown</p>
                <p className="text-2xl font-bold text-red-600">
                  {formatPercentage(parseFloat(data.drawdown_metrics.max_drawdown_pct))}
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  {formatCurrency(parseFloat(data.drawdown_metrics.max_drawdown_usd))}
                </p>
              </div>
              <TrendingDown className="h-8 w-8 text-red-400" />
            </div>
          </Card>

          <Card>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Current Drawdown</p>
                <p className="text-2xl font-bold text-orange-600">
                  {formatPercentage(parseFloat(data.drawdown_metrics.current_drawdown_pct))}
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  {formatCurrency(parseFloat(data.drawdown_metrics.current_drawdown_usd))}
                </p>
              </div>
              <TrendingDown className="h-8 w-8 text-orange-400" />
            </div>
          </Card>

          <Card>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Recovery Days</p>
                <p className="text-2xl font-bold text-blue-600">
                  {data.drawdown_metrics.recovery_days || 'N/A'}
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  {data.drawdown_metrics.is_recovered ? 'Recovered' : 'In Drawdown'}
                </p>
              </div>
              <Shield className="h-8 w-8 text-blue-400" />
            </div>
          </Card>
        </div>

        <Card>
          <h3 className="text-lg font-semibold mb-4">Drawdown Periods</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Start Date
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    End Date
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Drawdown %
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Duration (days)
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Recovery Days
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {(data.drawdown_metrics.drawdown_periods || []).map((period: any, idx: number) => (
                  <tr key={idx} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {period.start_date}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {period.end_date}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-red-600">
                      {formatPercentage(parseFloat(period.drawdown_pct))}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-900">
                      {period.duration_days}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-900">
                      {period.recovery_days || 'N/A'}
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

  const renderConcentrationMetrics = () => {
    if (!data?.concentration_metrics) return null;

    const topHoldings = data.concentration_metrics.top_holdings || [];

    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card>
            <div>
              <p className="text-sm text-gray-500">HHI Index</p>
              <p className="text-2xl font-bold text-blue-600">
                {parseFloat(data.concentration_metrics.hhi_index).toFixed(2)}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                {parseFloat(data.concentration_metrics.hhi_index) < 1500
                  ? 'Low Concentration'
                  : parseFloat(data.concentration_metrics.hhi_index) < 2500
                  ? 'Moderate Concentration'
                  : 'High Concentration'}
              </p>
            </div>
          </Card>

          <Card>
            <div>
              <p className="text-sm text-gray-500">Top 5 Concentration</p>
              <p className="text-2xl font-bold text-orange-600">
                {formatPercentage(parseFloat(data.concentration_metrics.top_5_concentration_pct))}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                Of Total Portfolio
              </p>
            </div>
          </Card>
        </div>

        <Card>
          <h3 className="text-lg font-semibold mb-4">Top Holdings</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Symbol
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Exposure
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Concentration %
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {topHoldings.map((holding: any) => (
                  <tr key={holding.symbol} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-gray-900">
                      {holding.symbol}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-900">
                      {formatCurrency(parseFloat(holding.exposure_usd))}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-900">
                      {formatPercentage(parseFloat(holding.concentration_pct))}
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
    const errorMessage = (error as any)?.response?.data?.detail || 'Error loading risk analytics data';
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <p className="text-yellow-800 font-medium">Risk Analytics Unavailable</p>
        <p className="text-yellow-700 text-sm mt-1">{errorMessage}</p>
        <p className="text-yellow-600 text-sm mt-2">
          Risk analytics requires sufficient historical data. Please ensure you have at least 30 days of trading history.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Metric Selector */}
      <Card>
        <div className="flex items-center gap-4">
          <label className="text-sm font-medium text-gray-700">Risk Metric:</label>
          <select
            value={metric}
            onChange={(e) => setMetric(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="var">Value at Risk (VaR)</option>
            <option value="drawdown">Drawdown Analysis</option>
            <option value="concentration">Concentration Risk</option>
          </select>
        </div>
      </Card>

      {/* Content */}
      {metric === 'var' && renderVaRMetrics()}
      {metric === 'drawdown' && renderDrawdownMetrics()}
      {metric === 'concentration' && renderConcentrationMetrics()}
    </div>
  );
};

export default RiskAnalytics;

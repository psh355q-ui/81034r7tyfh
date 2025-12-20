/**
 * Performance Attribution Component
 * Analyzes performance by strategy, sector, AI source, position, and time
 */

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
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
  ResponsiveContainer,
} from 'recharts';
import { TrendingUp, TrendingDown, DollarSign } from 'lucide-react';
import { Card } from '../common/Card';
import { getPerformanceAttribution, analyticsKeys } from '../../services/analyticsApi';

interface PerformanceAttributionProps {
  startDate: string;
  endDate: string;
}

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16'];

const PerformanceAttribution: React.FC<PerformanceAttributionProps> = ({ startDate, endDate }) => {
  const [dimension, setDimension] = useState<string>('strategy');

  const { data, isLoading, error } = useQuery({
    queryKey: analyticsKeys.performance(startDate, endDate, dimension),
    queryFn: () => getPerformanceAttribution(startDate, endDate, dimension),
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

  const renderStrategyAttribution = () => {
    if (!data?.strategy_attribution) return null;

    const chartData = Object.entries(data.strategy_attribution).map(([strategy, stats]: [string, any]) => ({
      name: strategy,
      pnl: parseFloat(stats.total_pnl),
      contribution: parseFloat(stats.contribution_pct),
      winRate: stats.win_rate,
      trades: stats.total_trades,
    }));

    return (
      <div className="space-y-6">
        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <h3 className="text-lg font-semibold mb-4">PnL by Strategy</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip formatter={(value: number) => formatCurrency(value)} />
                <Legend />
                <Bar dataKey="pnl" fill="#3b82f6" name="PnL (USD)" />
              </BarChart>
            </ResponsiveContainer>
          </Card>

          <Card>
            <h3 className="text-lg font-semibold mb-4">Contribution by Strategy</h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={chartData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, contribution }) => `${name}: ${contribution.toFixed(1)}%`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="contribution"
                >
                  {chartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </Card>
        </div>

        {/* Table */}
        <Card>
          <h3 className="text-lg font-semibold mb-4">Strategy Details</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Strategy
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Total PnL
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Contribution %
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
                {Object.entries(data.strategy_attribution).map(([strategy, stats]: [string, any]) => (
                  <tr key={strategy} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {strategy}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right">
                      <span className={parseFloat(stats.total_pnl) >= 0 ? 'text-green-600' : 'text-red-600'}>
                        {formatCurrency(parseFloat(stats.total_pnl))}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-900">
                      {formatPercentage(parseFloat(stats.contribution_pct))}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-900">
                      {stats.total_trades}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right">
                      <span
                        className={`inline-flex px-2 py-1 rounded-full text-xs font-semibold ${
                          stats.win_rate >= 0.5
                            ? 'bg-green-100 text-green-800'
                            : 'bg-red-100 text-red-800'
                        }`}
                      >
                        {(stats.win_rate * 100).toFixed(1)}%
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-900">
                      {formatCurrency(parseFloat(stats.avg_pnl))}
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

  const renderOtherDimensions = () => {
    if (dimension === 'sector' && data?.sector_attribution) {
      const chartData = Object.entries(data.sector_attribution).map(([sector, stats]: [string, any]) => ({
        name: sector,
        pnl: parseFloat(stats.total_pnl),
        trades: stats.total_trades,
      }));

      return (
        <Card>
          <h3 className="text-lg font-semibold mb-4">PnL by Sector</h3>
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip formatter={(value: number) => formatCurrency(value)} />
              <Legend />
              <Bar dataKey="pnl" fill="#10b981" name="PnL (USD)" />
            </BarChart>
          </ResponsiveContainer>
        </Card>
      );
    }

    if (dimension === 'ai_source' && data?.ai_source_attribution) {
      return (
        <Card>
          <h3 className="text-lg font-semibold mb-4">AI Source Performance</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    AI Source
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Total PnL
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Trades
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Win Rate
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Avg Confidence
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {Object.entries(data.ai_source_attribution).map(([source, stats]: [string, any]) => (
                  <tr key={source} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {source}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right">
                      <span className={parseFloat(stats.total_pnl) >= 0 ? 'text-green-600' : 'text-red-600'}>
                        {formatCurrency(parseFloat(stats.total_pnl))}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-900">
                      {stats.total_trades}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right">
                      <span
                        className={`inline-flex px-2 py-1 rounded-full text-xs font-semibold ${
                          stats.win_rate >= 0.5
                            ? 'bg-green-100 text-green-800'
                            : 'bg-red-100 text-red-800'
                        }`}
                      >
                        {(stats.win_rate * 100).toFixed(1)}%
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-900">
                      {(stats.avg_confidence * 100).toFixed(1)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      );
    }

    if (dimension === 'position' && data?.position_attribution) {
      return (
        <Card>
          <h3 className="text-lg font-semibold mb-4">Top Positions by PnL</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Symbol
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Total PnL
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Contribution %
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Trades
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Win Rate
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {data.position_attribution.map((position: any) => (
                  <tr key={position.symbol} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-gray-900">
                      {position.symbol}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right">
                      <span className={parseFloat(position.total_pnl) >= 0 ? 'text-green-600' : 'text-red-600'}>
                        {formatCurrency(parseFloat(position.total_pnl))}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-900">
                      {formatPercentage(parseFloat(position.contribution_pct))}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-900">
                      {position.total_trades}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right">
                      <span
                        className={`inline-flex px-2 py-1 rounded-full text-xs font-semibold ${
                          position.win_rate >= 0.5
                            ? 'bg-green-100 text-green-800'
                            : 'bg-red-100 text-red-800'
                        }`}
                      >
                        {(position.win_rate * 100).toFixed(1)}%
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      );
    }

    if (dimension === 'time' && data?.time_attribution) {
      const dailyData = data.time_attribution.daily?.map((item: any) => ({
        date: item.date,
        pnl: parseFloat(item.total_pnl),
      })) || [];

      return (
        <Card>
          <h3 className="text-lg font-semibold mb-4">Daily PnL Trend</h3>
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={dailyData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip formatter={(value: number) => formatCurrency(value)} />
              <Legend />
              <Bar dataKey="pnl" fill="#3b82f6" name="Daily PnL" />
            </BarChart>
          </ResponsiveContainer>
        </Card>
      );
    }

    return null;
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
        Error loading performance attribution data
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Dimension Selector */}
      <Card>
        <div className="flex items-center gap-4">
          <label className="text-sm font-medium text-gray-700">Attribution Dimension:</label>
          <select
            value={dimension}
            onChange={(e) => setDimension(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="strategy">By Strategy</option>
            <option value="sector">By Sector</option>
            <option value="ai_source">By AI Source</option>
            <option value="position">By Position</option>
            <option value="time">By Time</option>
          </select>
        </div>
      </Card>

      {/* Content */}
      {dimension === 'strategy' ? renderStrategyAttribution() : renderOtherDimensions()}
    </div>
  );
};

export default PerformanceAttribution;

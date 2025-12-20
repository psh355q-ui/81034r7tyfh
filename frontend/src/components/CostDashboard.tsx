/**
 * Cost Monitoring Dashboard Component
 *
 * Features:
 * - Daily/monthly cost summary
 * - Budget status with alerts
 * - Cost trends (7d/30d)
 * - Cost breakdown by category
 * - Real-time updates
 */

import React, { useState, useEffect } from 'react';
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
  ResponsiveContainer,
} from 'recharts';

interface CostSummary {
  total_cost_usd: number;
  embeddings_generated: number;
}

interface BudgetStatus {
  status: 'OK' | 'WARNING' | 'CRITICAL';
  daily: {
    cost: number;
    limit: number;
    percentage: number;
  };
  monthly: {
    cost: number;
    limit: number;
    percentage: number;
  };
  alerts: Array<{
    level: string;
    type: string;
    message: string;
  }>;
}

interface CostTrend {
  summary: {
    total_cost: number;
    avg_daily: number;
    max_daily: number;
    min_daily: number;
  };
  daily_costs: Array<{
    date: string;
    cost: number;
    embeddings: number;
  }>;
  projections: {
    next_7_days: number;
    next_30_days: number;
  };
}

interface DashboardData {
  today: CostSummary;
  monthly_total: number;
  budget: BudgetStatus;
  trends_7d: CostTrend;
  trends_30d: CostTrend;
  breakdown_7d: {
    total: {
      cost_usd: number;
      embeddings: number;
      tokens: number;
    };
    by_document_type: Record<string, {
      cost_usd: number;
      embeddings: number;
      tokens: number;
      avg_cost: number;
    }>;
    projections: {
      daily_avg: number;
      monthly_projected: number;
    };
  };
}

const COLORS = {
  primary: '#3b82f6',
  success: '#10b981',
  warning: '#f59e0b',
  danger: '#ef4444',
  sec_filing: '#8b5cf6',
  news_article: '#06b6d4',
  other: '#6b7280',
};

const CostDashboard: React.FC = () => {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshInterval, setRefreshInterval] = useState(60000); // 1 minute

  // Fetch dashboard data
  const fetchDashboardData = async () => {
    try {
      const response = await fetch('/api/cost/dashboard');
      if (!response.ok) {
        throw new Error('Failed to fetch dashboard data');
      }
      const dashboardData = await response.json();
      setData(dashboardData);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  // Initial fetch and auto-refresh
  useEffect(() => {
    fetchDashboardData();

    const interval = setInterval(fetchDashboardData, refreshInterval);

    return () => clearInterval(interval);
  }, [refreshInterval]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-xl text-gray-600">Loading cost dashboard...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-xl text-red-600">Error: {error}</div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-xl text-gray-600">No data available</div>
      </div>
    );
  }

  // Budget status color
  const budgetColor =
    data.budget.status === 'OK'
      ? COLORS.success
      : data.budget.status === 'WARNING'
      ? COLORS.warning
      : COLORS.danger;

  // Prepare pie chart data
  const pieChartData = Object.entries(data.breakdown_7d.by_document_type).map(
    ([type, stats]) => ({
      name: type.replace('_', ' ').toUpperCase(),
      value: stats.cost_usd,
    })
  );

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Cost Monitoring Dashboard</h1>
        <p className="text-gray-600 mt-2">
          Real-time cost tracking and budget monitoring
        </p>
      </div>

      {/* Budget Alerts */}
      {data.budget.alerts.length > 0 && (
        <div className="mb-6">
          {data.budget.alerts.map((alert, idx) => (
            <div
              key={idx}
              className={`p-4 rounded-lg mb-2 ${
                alert.level === 'CRITICAL'
                  ? 'bg-red-100 border border-red-400 text-red-700'
                  : 'bg-yellow-100 border border-yellow-400 text-yellow-700'
              }`}
            >
              <span className="font-semibold">{alert.level}:</span> {alert.message}
            </div>
          ))}
        </div>
      )}

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {/* Today's Cost */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-gray-600 text-sm font-medium">Today's Cost</div>
          <div className="text-3xl font-bold text-gray-900 mt-2">
            ${data.today.total_cost_usd.toFixed(4)}
          </div>
          <div className="text-sm text-gray-500 mt-1">
            {data.today.embeddings_generated} embeddings
          </div>
        </div>

        {/* Monthly Total */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-gray-600 text-sm font-medium">Monthly Total</div>
          <div className="text-3xl font-bold text-gray-900 mt-2">
            ${data.monthly_total.toFixed(2)}
          </div>
          <div className="text-sm text-gray-500 mt-1">
            ${data.breakdown_7d.projections.daily_avg.toFixed(4)}/day avg
          </div>
        </div>

        {/* Daily Budget */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-gray-600 text-sm font-medium">Daily Budget</div>
          <div className="flex items-baseline mt-2">
            <div className="text-3xl font-bold" style={{ color: budgetColor }}>
              {data.budget.daily.percentage.toFixed(0)}%
            </div>
            <div className="text-sm text-gray-500 ml-2">
              of ${data.budget.daily.limit.toFixed(2)}
            </div>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2 mt-3">
            <div
              className="h-2 rounded-full transition-all"
              style={{
                width: `${Math.min(data.budget.daily.percentage, 100)}%`,
                backgroundColor: budgetColor,
              }}
            />
          </div>
        </div>

        {/* Monthly Budget */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-gray-600 text-sm font-medium">Monthly Budget</div>
          <div className="flex items-baseline mt-2">
            <div className="text-3xl font-bold" style={{ color: budgetColor }}>
              {data.budget.monthly.percentage.toFixed(0)}%
            </div>
            <div className="text-sm text-gray-500 ml-2">
              of ${data.budget.monthly.limit.toFixed(2)}
            </div>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2 mt-3">
            <div
              className="h-2 rounded-full transition-all"
              style={{
                width: `${Math.min(data.budget.monthly.percentage, 100)}%`,
                backgroundColor: budgetColor,
              }}
            />
          </div>
        </div>
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* 7-Day Cost Trend */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            7-Day Cost Trend
          </h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={data.trends_7d.daily_costs}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="date"
                tickFormatter={(date) => new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
              />
              <YAxis
                tickFormatter={(value) => `$${value.toFixed(3)}`}
              />
              <Tooltip
                formatter={(value: number) => [`$${value.toFixed(5)}`, 'Cost']}
                labelFormatter={(label) => new Date(label).toLocaleDateString()}
              />
              <Legend />
              <Line
                type="monotone"
                dataKey="cost"
                stroke={COLORS.primary}
                strokeWidth={2}
                dot={{ fill: COLORS.primary }}
              />
            </LineChart>
          </ResponsiveContainer>
          <div className="mt-4 text-sm text-gray-600">
            Avg: ${data.trends_7d.summary.avg_daily.toFixed(5)}/day
            {' • '}
            Projected next 7 days: ${data.trends_7d.projections.next_7_days.toFixed(3)}
          </div>
        </div>

        {/* Cost Breakdown by Type */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Cost by Document Type (Last 7 Days)
          </h2>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={pieChartData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(1)}%`}
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
              >
                {pieChartData.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={
                      entry.name.includes('SEC')
                        ? COLORS.sec_filing
                        : entry.name.includes('NEWS')
                        ? COLORS.news_article
                        : COLORS.other
                    }
                  />
                ))}
              </Pie>
              <Tooltip formatter={(value: number) => `$${value.toFixed(5)}`} />
            </PieChart>
          </ResponsiveContainer>
          <div className="mt-4 text-sm text-gray-600">
            Total: ${data.breakdown_7d.total.cost_usd.toFixed(4)}
            {' • '}
            {data.breakdown_7d.total.embeddings.toLocaleString()} embeddings
          </div>
        </div>
      </div>

      {/* Charts Row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* 30-Day Cost Trend */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            30-Day Cost Trend
          </h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={data.trends_30d.daily_costs}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="date"
                tickFormatter={(date) => new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                interval={4}
              />
              <YAxis tickFormatter={(value) => `$${value.toFixed(2)}`} />
              <Tooltip
                formatter={(value: number) => [`$${value.toFixed(5)}`, 'Cost']}
                labelFormatter={(label) => new Date(label).toLocaleDateString()}
              />
              <Legend />
              <Bar dataKey="cost" fill={COLORS.primary} />
            </BarChart>
          </ResponsiveContainer>
          <div className="mt-4 text-sm text-gray-600">
            Avg: ${data.trends_30d.summary.avg_daily.toFixed(5)}/day
            {' • '}
            Projected next 30 days: ${data.trends_30d.projections.next_30_days.toFixed(2)}
          </div>
        </div>

        {/* Detailed Breakdown Table */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Detailed Breakdown (Last 7 Days)
          </h2>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Type
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    Cost
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    Count
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    Avg
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {Object.entries(data.breakdown_7d.by_document_type).map(([type, stats]) => (
                  <tr key={type}>
                    <td className="px-4 py-3 text-sm font-medium text-gray-900">
                      {type.replace('_', ' ').toUpperCase()}
                    </td>
                    <td className="px-4 py-3 text-sm text-right text-gray-900">
                      ${stats.cost_usd.toFixed(5)}
                    </td>
                    <td className="px-4 py-3 text-sm text-right text-gray-600">
                      {stats.embeddings.toLocaleString()}
                    </td>
                    <td className="px-4 py-3 text-sm text-right text-gray-600">
                      ${stats.avg_cost.toFixed(6)}
                    </td>
                  </tr>
                ))}
                <tr className="bg-gray-50 font-semibold">
                  <td className="px-4 py-3 text-sm text-gray-900">TOTAL</td>
                  <td className="px-4 py-3 text-sm text-right text-gray-900">
                    ${data.breakdown_7d.total.cost_usd.toFixed(5)}
                  </td>
                  <td className="px-4 py-3 text-sm text-right text-gray-900">
                    {data.breakdown_7d.total.embeddings.toLocaleString()}
                  </td>
                  <td className="px-4 py-3 text-sm text-right text-gray-900">
                    -
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="text-center text-sm text-gray-500">
        Last updated: {new Date().toLocaleString()}
        {' • '}
        Auto-refresh every {refreshInterval / 1000} seconds
      </div>
    </div>
  );
};

export default CostDashboard;

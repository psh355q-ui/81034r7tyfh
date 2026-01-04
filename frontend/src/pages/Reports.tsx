/**
 * Reports Page - View and download trading reports
 *
 * Features:
 * - Daily/Weekly/Monthly report viewer
 * - Performance charts
 * - PDF/CSV export
 * - Date range selection
 * - Performance analytics
 *
 * @author AI Trading System Team
 * @date 2025-11-25
 */

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
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
import {
  FileText,
  Download,
  Calendar,
  TrendingUp,
  TrendingDown,
  DollarSign,
  Activity,
  AlertTriangle,
} from 'lucide-react';
import dayjs from 'dayjs';




import {
  getDailyReport,
  getDailySummaries,
  getPerformanceSummary,
  downloadDailyReportPDF,
  downloadCSV,
  reportsKeys,
  DailyReport,
  PerformanceSummary,
} from '../services/reportsApi';

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

const Reports: React.FC = () => {
  // State
  const [selectedDate, setSelectedDate] = useState<string>(
    dayjs().subtract(1, 'day').format('YYYY-MM-DD')
  );
  const [reportType, setReportType] = useState<'daily' | 'weekly' | 'monthly'>('daily');
  const [lookbackDays, setLookbackDays] = useState<number>(30);

  // Queries
  const { data: dailyReport, isLoading: reportLoading } = useQuery({
    queryKey: reportsKeys.daily(selectedDate),
    queryFn: () => getDailyReport(selectedDate, 'json') as Promise<DailyReport>,
    enabled: reportType === 'daily',
  });

  const { data: dailySummaries, isLoading: summariesLoading } = useQuery({
    queryKey: reportsKeys.dailySummaries(
      dayjs().subtract(lookbackDays, 'day').format('YYYY-MM-DD'),
      dayjs().format('YYYY-MM-DD')
    ),
    queryFn: () =>
      getDailySummaries(
        dayjs().subtract(lookbackDays, 'day').format('YYYY-MM-DD'),
        dayjs().format('YYYY-MM-DD')
      ),
  });

  const { data: performanceSummary, isLoading: perfLoading } = useQuery({
    queryKey: reportsKeys.performanceSummary(lookbackDays),
    queryFn: () => getPerformanceSummary(lookbackDays),
  });

  // Handlers
  const handleDownloadPDF = async () => {
    try {
      await downloadDailyReportPDF(selectedDate);
    } catch (error) {
      console.error('Error downloading PDF:', error);
      alert('Failed to download PDF report');
    }
  };

  const handleDownloadCSV = async () => {
    try {
      await downloadCSV(
        dayjs().subtract(lookbackDays, 'day').format('YYYY-MM-DD'),
        dayjs().format('YYYY-MM-DD')
      );
    } catch (error) {
      console.error('Error downloading CSV:', error);
      alert('Failed to download CSV');
    }
  };

  // Render helpers
  const formatCurrency = (value: number): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value);
  };

  const formatPercent = (value: number): string => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  // Metric card component
  const MetricCard: React.FC<{
    label: string;
    value: string;
    change?: string;
    changeType?: 'positive' | 'negative' | 'neutral';
    icon: React.ReactNode;
  }> = ({ label, value, change, changeType, icon }) => (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium text-gray-600">{label}</span>
        <div className="text-gray-400">{icon}</div>
      </div>
      <div className="text-2xl font-bold text-gray-900">{value}</div>
      {change && (
        <div className="flex items-center mt-2">
          {changeType === 'positive' && <TrendingUp className="w-4 h-4 text-green-500 mr-1" />}
          {changeType === 'negative' && <TrendingDown className="w-4 h-4 text-red-500 mr-1" />}
          <span
            className={`text-sm font-medium ${changeType === 'positive'
              ? 'text-green-600'
              : changeType === 'negative'
                ? 'text-red-600'
                : 'text-gray-600'
              }`}
          >
            {change}
          </span>
        </div>
      )}
    </div>
  );

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Trading Reports</h1>
        <p className="text-gray-600">Performance analytics and detailed trading reports</p>
      </div>

      {/* Controls */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Report Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Report Type
            </label>
            <select
              value={reportType}
              onChange={(e) => setReportType(e.target.value as any)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="daily">Daily</option>
              <option value="weekly">Weekly</option>
              <option value="monthly">Monthly</option>
            </select>
          </div>

          {/* Date Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Report Date
            </label>
            <input
              type="date"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Lookback Period */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Analytics Period
            </label>
            <select
              value={lookbackDays}
              onChange={(e) => setLookbackDays(Number(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value={7}>Last 7 days</option>
              <option value={30}>Last 30 days</option>
              <option value={90}>Last 90 days</option>
              <option value={180}>Last 6 months</option>
              <option value={365}>Last year</option>
            </select>
          </div>

          {/* Export Buttons */}
          <div className="flex items-end gap-2">
            <button
              onClick={handleDownloadPDF}
              disabled={!dailyReport}
              className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
            >
              <Download className="w-4 h-4" />
              PDF
            </button>
            <button
              onClick={handleDownloadCSV}
              className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
            >
              <Download className="w-4 h-4" />
              CSV
            </button>
          </div>
        </div>
      </div>

      {/* Performance Summary */}
      {performanceSummary && (
        <div className="mb-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">
            Performance Summary ({lookbackDays} days)
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <MetricCard
              label="Portfolio Value"
              value={formatCurrency(performanceSummary.current.portfolio_value)}
              icon={<DollarSign className="w-5 h-5" />}
            />
            <MetricCard
              label="Total P&L"
              value={formatCurrency(performanceSummary.performance.total_pnl)}
              change={formatPercent(
                (performanceSummary.performance.total_pnl /
                  performanceSummary.current.portfolio_value) *
                100
              )}
              changeType={
                performanceSummary.performance.total_pnl > 0
                  ? 'positive'
                  : performanceSummary.performance.total_pnl < 0
                    ? 'negative'
                    : 'neutral'
              }
              icon={<TrendingUp className="w-5 h-5" />}
            />
            <MetricCard
              label="Total Trades"
              value={performanceSummary.performance.total_trades.toString()}
              icon={<Activity className="w-5 h-5" />}
            />
            <MetricCard
              label="Win Rate"
              value={
                performanceSummary.performance.win_rate
                  ? `${(performanceSummary.performance.win_rate * 100).toFixed(1)}%`
                  : 'N/A'
              }
              icon={<FileText className="w-5 h-5" />}
            />
          </div>
        </div>
      )}

      {/* Daily Report Details */}
      {dailyReport && (
        <div className="space-y-6">
          {/* Executive Summary */}
          {dailyReport.executive_summary && (
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-4">Executive Summary</h2>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                <div>
                  <div className="text-sm text-gray-600">Portfolio Value</div>
                  <div className="text-2xl font-bold">
                    {formatCurrency(dailyReport.executive_summary.portfolio_value)}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-gray-600">Daily P&L</div>
                  <div
                    className={`text-2xl font-bold ${dailyReport.executive_summary.daily_pnl >= 0
                      ? 'text-green-600'
                      : 'text-red-600'
                      }`}
                  >
                    {formatCurrency(dailyReport.executive_summary.daily_pnl)}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-gray-600">Daily Return</div>
                  <div
                    className={`text-2xl font-bold ${dailyReport.executive_summary.daily_return_pct >= 0
                      ? 'text-green-600'
                      : 'text-red-600'
                      }`}
                  >
                    {formatPercent(dailyReport.executive_summary.daily_return_pct)}
                  </div>
                </div>
              </div>

              {/* Highlights */}
              {dailyReport.executive_summary.highlights.length > 0 && (
                <div className="mb-4">
                  <h3 className="text-sm font-semibold text-gray-700 mb-2">Highlights</h3>
                  <ul className="space-y-1">
                    {dailyReport.executive_summary.highlights.map((highlight, idx) => (
                      <li key={idx} className="text-sm text-gray-600">
                        • {highlight}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Risk Alerts */}
              {dailyReport.executive_summary.risk_alerts.length > 0 && (
                <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <AlertTriangle className="w-5 h-5 text-yellow-600" />
                    <h3 className="text-sm font-semibold text-yellow-800">Risk Alerts</h3>
                  </div>
                  <ul className="space-y-1">
                    {dailyReport.executive_summary.risk_alerts.map((alert, idx) => (
                      <li key={idx} className="text-sm text-yellow-700">
                        {alert}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {/* Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Performance Chart */}
            {dailyReport.performance_chart && (
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-bold text-gray-900 mb-4">
                  {dailyReport.performance_chart.title}
                </h3>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart
                    data={dailyReport.performance_chart.x_labels.map((label, idx) => ({
                      date: label,
                      value: dailyReport.performance_chart!.datasets[0].data[idx],
                    }))}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip
                      formatter={(value: number) => formatCurrency(value)}
                    />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="value"
                      stroke="#10b981"
                      strokeWidth={2}
                      dot={false}
                      name="Portfolio Value"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}

            {/* P&L Chart */}
            {dailyReport.pnl_chart && (
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-bold text-gray-900 mb-4">
                  {dailyReport.pnl_chart.title}
                </h3>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart
                    data={dailyReport.pnl_chart.x_labels.map((label, idx) => ({
                      date: label,
                      pnl: dailyReport.pnl_chart!.datasets[0].data[idx],
                    }))}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip
                      formatter={(value: number) => formatCurrency(value)}
                    />
                    <Bar dataKey="pnl">
                      {dailyReport.pnl_chart.x_labels.map((_, idx) => (
                        <Cell
                          key={idx}
                          fill={
                            dailyReport.pnl_chart!.datasets[0].data[idx] >= 0
                              ? '#10b981'
                              : '#ef4444'
                          }
                        />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>

          {/* Portfolio Overview */}
          {dailyReport.portfolio_overview && (
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-4">Portfolio Overview</h2>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Sector Allocation */}
                {dailyReport.portfolio_overview.sector_allocation &&
                  Object.keys(dailyReport.portfolio_overview.sector_allocation).length > 0 && (
                    <div>
                      <h3 className="text-sm font-semibold text-gray-700 mb-3">
                        Sector Allocation
                      </h3>
                      <ResponsiveContainer width="100%" height={250}>
                        <PieChart>
                          <Pie
                            data={Object.entries(
                              dailyReport.portfolio_overview.sector_allocation
                            ).map(([name, value]) => ({
                              name,
                              value,
                            }))}
                            cx="50%"
                            cy="50%"
                            labelLine={false}
                            label={({ name, percent }) =>
                              `${name}: ${(percent * 100).toFixed(1)}%`
                            }
                            outerRadius={80}
                            fill="#8884d8"
                            dataKey="value"
                          >
                            {Object.keys(
                              dailyReport.portfolio_overview.sector_allocation
                            ).map((_, index) => (
                              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                            ))}
                          </Pie>
                          <Tooltip />
                        </PieChart>
                      </ResponsiveContainer>
                    </div>
                  )}

                {/* Metrics */}
                <div>
                  <h3 className="text-sm font-semibold text-gray-700 mb-3">Metrics</h3>
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Total Value</span>
                      <span className="text-sm font-medium">
                        {formatCurrency(dailyReport.portfolio_overview.total_value)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Cash</span>
                      <span className="text-sm font-medium">
                        {formatCurrency(dailyReport.portfolio_overview.cash)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Invested</span>
                      <span className="text-sm font-medium">
                        {formatCurrency(dailyReport.portfolio_overview.invested_value)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Positions</span>
                      <span className="text-sm font-medium">
                        {dailyReport.portfolio_overview.positions_count}
                      </span>
                    </div>
                    {dailyReport.portfolio_overview.cash_pct && (
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Cash %</span>
                        <span className="text-sm font-medium">
                          {(dailyReport.portfolio_overview.cash_pct * 100).toFixed(1)}%
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Loading State */}
      {(reportLoading || perfLoading) && (
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-500">Loading report...</div>
        </div>
      )}

      {/* Empty State */}
      {!reportLoading && !dailyReport && reportType === 'daily' && (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <FileText className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Report Available</h3>
          <p className="text-gray-600">
            No data available for the selected date. Please select a different date.
          </p>
        </div>
      )}
    </div>
  );
};

export default Reports;

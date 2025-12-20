import React, { useState, useEffect } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  AreaChart,
  Area
} from 'recharts';
import { RefreshCw, TrendingUp, AlertTriangle, CheckCircle, ExternalLink } from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_URL !== undefined
  ? import.meta.env.VITE_API_URL
  : (window.location.hostname === 'localhost' ? '' : `http://${window.location.hostname}:8002`);

interface APIUsageStats {
  current: {
    timestamp: string;
    requests_last_minute: number;
    requests_today: number;
    tokens_last_minute: number;
    tokens_today: number;
    estimated_cost_today: number;
    rate_limit_status: 'OK' | 'WARNING' | 'EXCEEDED';
    next_reset_time: string;
  };
  limits: {
    model: string;
    rpm: number;
    rpd: number;
    tpm: number;
  };
  utilization: {
    rpm_percent: number;
    rpd_percent: number;
    tpm_percent: number;
  };
  recommendations: string[];
}

interface UsageHistoryPoint {
  timestamp: string;
  requests_last_minute: number;
  requests_today: number;
  tokens_last_minute: number;
  rate_limit_status: string;
}

const APIUsageMonitor: React.FC = () => {
  const [usageStats, setUsageStats] = useState<APIUsageStats | null>(null);
  const [history, setHistory] = useState<UsageHistoryPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const fetchUsageData = async () => {
    try {
      // Fetch current stats
      const statsResponse = await fetch(`${API_BASE_URL}/api/monitoring/api-usage`);
      if (!statsResponse.ok) throw new Error('Failed to fetch usage stats');
      const statsData = await statsResponse.json();
      setUsageStats(statsData.data);

      // Fetch history (last 60 minutes)
      const historyResponse = await fetch(`${API_BASE_URL}/api/monitoring/api-usage/history?minutes=60`);
      if (!historyResponse.ok) throw new Error('Failed to fetch usage history');
      const historyData = await historyResponse.json();
      setHistory(historyData.data);

      setError(null);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsageData();

    if (autoRefresh) {
      const interval = setInterval(fetchUsageData, 10000); // Refresh every 10 seconds
      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'OK':
        return 'text-green-600 bg-green-50 border-green-200';
      case 'WARNING':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'EXCEEDED':
        return 'text-red-600 bg-red-50 border-red-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'OK':
        return <CheckCircle className="w-5 h-5 text-green-600" />;
      case 'WARNING':
        return <AlertTriangle className="w-5 h-5 text-yellow-600" />;
      case 'EXCEEDED':
        return <AlertTriangle className="w-5 h-5 text-red-600" />;
      default:
        return null;
    }
  };

  const getUtilizationColor = (percent: number) => {
    if (percent >= 90) return 'bg-red-500';
    if (percent >= 80) return 'bg-yellow-500';
    if (percent >= 50) return 'bg-blue-500';
    return 'bg-green-500';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-4 text-blue-600" />
          <p className="text-gray-600">Loading API usage data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center bg-red-50 border border-red-200 rounded-lg p-6">
          <AlertTriangle className="w-8 h-8 mx-auto mb-4 text-red-600" />
          <p className="text-red-600 font-semibold mb-2">Error Loading Data</p>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={fetchUsageData}
            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!usageStats) return null;

  // Format chart data
  const chartData = history.map(point => ({
    time: new Date(point.timestamp).toLocaleTimeString(),
    RPM: point.requests_last_minute,
    'RPD (scaled)': Math.floor(point.requests_today / 100), // Scale down for visibility
    Tokens: Math.floor(point.tokens_last_minute / 1000), // Scale to thousands
  }));

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6 flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">API Usage Monitor</h1>
            <p className="text-gray-600 mt-1">Gemini API Rate Limits & Usage Tracking</p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={() => setAutoRefresh(!autoRefresh)}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                autoRefresh
                  ? 'bg-blue-600 text-white hover:bg-blue-700'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              {autoRefresh ? 'Auto-Refresh ON' : 'Auto-Refresh OFF'}
            </button>
            <button
              onClick={fetchUsageData}
              className="px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center gap-2"
            >
              <RefreshCw className="w-4 h-4" />
              Refresh
            </button>
          </div>
        </div>

        {/* Status Card */}
        <div className={`mb-6 p-6 rounded-lg border-2 ${getStatusColor(usageStats.current.rate_limit_status)}`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {getStatusIcon(usageStats.current.rate_limit_status)}
              <div>
                <h2 className="text-xl font-bold">
                  Status: {usageStats.current.rate_limit_status}
                </h2>
                <p className="text-sm mt-1">Model: {usageStats.limits.model}</p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-sm font-medium">Next Reset</p>
              <p className="text-lg font-mono">
                {new Date(usageStats.current.next_reset_time).toLocaleString()}
              </p>
            </div>
          </div>
        </div>

        {/* Metrics Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          {/* RPM Card */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex justify-between items-start mb-4">
              <div>
                <p className="text-sm text-gray-600 font-medium">Requests Per Minute</p>
                <p className="text-3xl font-bold text-gray-900 mt-1">
                  {usageStats.current.requests_last_minute}
                  <span className="text-lg text-gray-500">/{usageStats.limits.rpm}</span>
                </p>
              </div>
              <TrendingUp className="w-8 h-8 text-blue-500" />
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3">
              <div
                className={`h-3 rounded-full transition-all ${getUtilizationColor(usageStats.utilization.rpm_percent)}`}
                style={{ width: `${Math.min(usageStats.utilization.rpm_percent, 100)}%` }}
              />
            </div>
            <p className="text-sm text-gray-600 mt-2">
              {usageStats.utilization.rpm_percent.toFixed(1)}% utilized
            </p>
          </div>

          {/* RPD Card */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex justify-between items-start mb-4">
              <div>
                <p className="text-sm text-gray-600 font-medium">Requests Today</p>
                <p className="text-3xl font-bold text-gray-900 mt-1">
                  {usageStats.current.requests_today.toLocaleString()}
                  <span className="text-lg text-gray-500">/{usageStats.limits.rpd.toLocaleString()}</span>
                </p>
              </div>
              <TrendingUp className="w-8 h-8 text-purple-500" />
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3">
              <div
                className={`h-3 rounded-full transition-all ${getUtilizationColor(usageStats.utilization.rpd_percent)}`}
                style={{ width: `${Math.min(usageStats.utilization.rpd_percent, 100)}%` }}
              />
            </div>
            <p className="text-sm text-gray-600 mt-2">
              {usageStats.utilization.rpd_percent.toFixed(1)}% utilized
            </p>
          </div>

          {/* Tokens Card */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex justify-between items-start mb-4">
              <div>
                <p className="text-sm text-gray-600 font-medium">Tokens Per Minute</p>
                <p className="text-3xl font-bold text-gray-900 mt-1">
                  {usageStats.current.tokens_last_minute.toLocaleString()}
                  <span className="text-lg text-gray-500">/{(usageStats.limits.tpm / 1000).toFixed(0)}K</span>
                </p>
              </div>
              <TrendingUp className="w-8 h-8 text-green-500" />
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3">
              <div
                className={`h-3 rounded-full transition-all ${getUtilizationColor(usageStats.utilization.tpm_percent)}`}
                style={{ width: `${Math.min(usageStats.utilization.tpm_percent, 100)}%` }}
              />
            </div>
            <p className="text-sm text-gray-600 mt-2">
              {usageStats.utilization.tpm_percent.toFixed(1)}% utilized
            </p>
          </div>
        </div>

        {/* Chart */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h3 className="text-lg font-bold text-gray-900 mb-4">Usage Trend (Last Hour)</h3>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Area
                type="monotone"
                dataKey="RPM"
                stackId="1"
                stroke="#3b82f6"
                fill="#3b82f6"
                fillOpacity={0.6}
              />
              <Area
                type="monotone"
                dataKey="Tokens"
                stackId="2"
                stroke="#10b981"
                fill="#10b981"
                fillOpacity={0.6}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Recommendations */}
        {usageStats.recommendations.length > 0 && (
          <div className="bg-white rounded-lg shadow p-6 mb-6">
            <h3 className="text-lg font-bold text-gray-900 mb-4">Recommendations</h3>
            <ul className="space-y-2">
              {usageStats.recommendations.map((rec, idx) => (
                <li key={idx} className="flex items-start gap-2">
                  <span className="text-blue-600 mt-1">•</span>
                  <span className="text-gray-700">{rec}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Upgrade Card */}
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg shadow-lg p-6 text-white">
          <h3 className="text-2xl font-bold mb-2">Need Higher Limits?</h3>
          <p className="mb-4 opacity-90">
            Upgrade to Gemini API Paid Tier for unlimited requests and higher rate limits
          </p>
          <ul className="mb-6 space-y-2">
            <li className="flex items-center gap-2">
              <CheckCircle className="w-5 h-5" />
              <span>No daily request limits</span>
            </li>
            <li className="flex items-center gap-2">
              <CheckCircle className="w-5 h-5" />
              <span>Up to 1000 RPM</span>
            </li>
            <li className="flex items-center gap-2">
              <CheckCircle className="w-5 h-5" />
              <span>Priority support</span>
            </li>
          </ul>
          <a
            href="https://ai.google.dev/pricing"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-6 py-3 bg-white text-blue-600 rounded-lg font-semibold hover:bg-gray-100 transition-colors"
          >
            View Pricing
            <ExternalLink className="w-4 h-4" />
          </a>
        </div>
      </div>
    </div>
  );
};

export default APIUsageMonitor;

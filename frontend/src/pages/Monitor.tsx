import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Power, Activity, AlertTriangle, CheckCircle, XCircle,
  Server, Shield, Terminal, TrendingDown, Database, Clock,
  DollarSign, Zap, Play, Square, RefreshCw
} from 'lucide-react';
import {
  BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis,
  CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';

import {
  getRiskStatus,
  activateKillSwitch,
  deactivateKillSwitch,
  getSystemInfo,
  getAlerts,
  getShadowLogs,
} from '../services/api';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { Alert } from '../components/common/Alert';

// --- Types ---
interface ShadowLog {
  timestamp: string;
  ticker: string;
  intent: { direction: 'BUY' | 'SELL' | 'HOLD'; score: number; rationale: string[] };
  status: 'SHADOW_FILLED' | 'SKIPPED';
  execution?: { action: number; price: number };
}

// --- Mock Data for System Health (from IncrementalDashboard) ---
const mockStats = {
  total_tickers: 100,
  total_rows_stored: 125800,
  last_update_date: '2025-11-23',
  avg_rows_per_ticker: 1258,
};

const mockCostSavings = {
  api_calls: { before_per_day: 182500, after_per_day: 100, reduction_pct: 99.95 },
  performance: { speedup_factor: 50 },
  estimated_monthly_cost: { before_usd: 10.55, after_usd: 1.51, savings_usd: 9.04, savings_pct: 86 },
};

const mockStorage = {
  total_size_gb: 2.5,
  total_files: 1523,
  locations: {
    sec_filings: { size_mb: 450, file_count: 234, usage_pct: 18 },
    stock_prices: { size_mb: 1200, file_count: 856, usage_pct: 48 },
    ai_cache: { size_mb: 350, file_count: 189, usage_pct: 14 },
    news_archive: { size_mb: 300, file_count: 156, usage_pct: 12 },
    embeddings: { size_mb: 200, file_count: 88, usage_pct: 8 },
  },
};

const COLORS = ['#3b82f6', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981'];

export const Monitor: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'live' | 'shadow' | 'system'>('live');
  const queryClient = useQueryClient();

  // --- Queries (Live Monitor) ---
  const { data: riskStatus, isLoading: riskLoading } = useQuery({
    queryKey: ['risk', 'status'],
    queryFn: getRiskStatus,
    refetchInterval: 5000,
  });

  const { data: systemInfo, isLoading: systemLoading } = useQuery({
    queryKey: ['system', 'info'],
    queryFn: getSystemInfo,
  });

  const { data: alertsData, isLoading: alertsLoading } = useQuery({
    queryKey: ['alerts'],
    queryFn: () => getAlerts(20),
    refetchInterval: 10000,
  });
  const alerts = Array.isArray(alertsData) ? alertsData : [];

  // --- Queries (Shadow) ---
  // Placeholder for now, can be connected to /api/shadow/logs later
  const shadowLogs: ShadowLog[] = [
    { timestamp: "2024-05-20T10:00:00", ticker: "AAPL", intent: { direction: "BUY", score: 0.8, rationale: ["News Positive"] }, status: "SHADOW_FILLED", execution: { action: 2, price: 150.0 } },
    { timestamp: "2024-05-20T10:05:00", ticker: "NVDA", intent: { direction: "HOLD", score: 0.1, rationale: ["Low Volume"] }, status: "SKIPPED" }
  ];

  // --- Mutations ---
  const activateMutation = useMutation({
    mutationFn: activateKillSwitch,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['risk', 'status'] }),
  });

  const deactivateMutation = useMutation({
    mutationFn: deactivateKillSwitch,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['risk', 'status'] }),
  });

  const handleKillSwitchToggle = () => {
    if (riskStatus?.kill_switch_active) {
      deactivateMutation.mutate();
    } else {
      activateMutation.mutate();
    }
  };

  const getAlertVariant = (level: string): 'info' | 'success' | 'warning' | 'error' => {
    switch (level) {
      case 'CRITICAL': return 'error';
      case 'HIGH': return 'warning';
      case 'MEDIUM': return 'warning';
      case 'LOW': return 'info';
      default: return 'info';
    }
  };

  const formatUptime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };

  if (riskLoading || systemLoading) {
    return <div className="flex items-center justify-center h-screen"><LoadingSpinner size="lg" /></div>;
  }

  // Chart Data preparation for System Health
  const costComparisonData = [
    { name: 'Before', cost: mockCostSavings.estimated_monthly_cost.before_usd, fill: '#ef4444' },
    { name: 'After', cost: mockCostSavings.estimated_monthly_cost.after_usd, fill: '#22c55e' },
  ];
  const storageData = Object.entries(mockStorage.locations).map(([name, data]) => ({
    name: name.replace(/_/g, ' '), value: data.size_mb, files: data.file_count,
  }));

  return (
    <div className="space-y-6 p-6">
      {/* Header & Tabs */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">System Monitor</h1>
          <p className="text-gray-600 mt-1">Control center for AI Trading System</p>
        </div>
        <div className="flex bg-white rounded-lg p-1 shadow-sm border border-gray-200">
          <button onClick={() => setActiveTab('live')} className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all ${activeTab === 'live' ? 'bg-red-50 text-red-700 shadow-sm' : 'text-gray-600 hover:bg-gray-50'}`}>
            <Shield size={16} /> Live Control
          </button>
          <button onClick={() => setActiveTab('shadow')} className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all ${activeTab === 'shadow' ? 'bg-gray-100 text-gray-900 shadow-sm' : 'text-gray-600 hover:bg-gray-50'}`}>
            <Terminal size={16} /> Shadow Trading
          </button>
          <button onClick={() => setActiveTab('system')} className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all ${activeTab === 'system' ? 'bg-blue-50 text-blue-700 shadow-sm' : 'text-gray-600 hover:bg-gray-50'}`}>
            <Server size={16} /> System Health
          </button>
        </div>
      </div>

      {/* --- TAB: LIVE CONTROL --- */}
      {activeTab === 'live' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Kill Switch Card */}
            <Card title="Kill Switch" className="bg-gradient-to-br from-red-50 to-orange-50">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600 mb-1">Trading Status</p>
                    <p className={`text-2xl font-bold ${riskStatus?.kill_switch_active ? 'text-red-600' : 'text-green-600'}`}>
                      {riskStatus?.kill_switch_active ? 'STOPPED' : 'ACTIVE'}
                    </p>
                  </div>
                  <div className={`p-4 rounded-full ${riskStatus?.kill_switch_active ? 'bg-red-100' : 'bg-green-100'}`}>
                    {riskStatus?.kill_switch_active ? <XCircle className="text-red-600" size={32} /> : <CheckCircle className="text-green-600" size={32} />}
                  </div>
                </div>
                <Button
                  variant={riskStatus?.kill_switch_active ? 'success' : 'danger'}
                  size="lg"
                  onClick={handleKillSwitchToggle}
                  disabled={activateMutation.isPending || deactivateMutation.isPending}
                  className="w-full flex items-center justify-center gap-2"
                >
                  <Power size={20} />
                  {riskStatus?.kill_switch_active ? 'Resume Trading' : 'Emergency Stop'}
                </Button>
                <p className="text-xs text-gray-600 text-center">
                  {riskStatus?.kill_switch_active ? 'All trading operations are paused. Click to resume.' : 'Click to immediately stop all trading operations.'}
                </p>
              </div>
            </Card>

            {/* System Info Card */}
            <Card title="System Information">
              <div className="space-y-3">
                <div className="flex justify-between"><span className="text-gray-600">Version</span><span className="font-semibold">{systemInfo?.version}</span></div>
                <div className="flex justify-between"><span className="text-gray-600">Environment</span><Badge variant={systemInfo?.environment === 'production' ? 'danger' : 'info'}>{systemInfo?.environment}</Badge></div>
                <div className="flex justify-between"><span className="text-gray-600">Uptime</span><span className="font-semibold">{systemInfo?.uptime_seconds ? formatUptime(systemInfo.uptime_seconds) : 'N/A'}</span></div>
                <div className="flex justify-between"><span className="text-gray-600">Start Time</span><span className="text-sm">{systemInfo?.start_time ? new Date(systemInfo.start_time).toLocaleString() : 'N/A'}</span></div>
              </div>
              {/* Component Health */}
              <div className="mt-4 pt-4 border-t border-gray-200">
                <h4 className="text-sm font-medium text-gray-700 mb-2">Components</h4>
                <div className="space-y-2">
                  {systemInfo?.components && Object.entries(systemInfo.components).map(([name, status]) => (
                    <div key={name} className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">{name}</span>
                      {status ? <Badge variant="success"><CheckCircle size={12} className="inline mr-1" />Healthy</Badge> : <Badge variant="danger"><XCircle size={12} className="inline mr-1" />Down</Badge>}
                    </div>
                  ))}
                </div>
              </div>
            </Card>
          </div>

          {/* Risk Dashboard */}
          <Card title="Risk Dashboard">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className={`p-4 rounded-lg ${(riskStatus?.daily_pnl ?? 0) >= 0 ? 'bg-green-50' : 'bg-red-50'}`}>
                <p className="text-sm text-gray-600 mb-1">Daily P&L</p>
                <p className={`text-3xl font-bold ${(riskStatus?.daily_pnl ?? 0) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {(riskStatus?.daily_pnl ?? 0) >= 0 ? '+' : ''}${(riskStatus?.daily_pnl ?? 0).toFixed(2)}
                </p>
                <p className="text-sm text-gray-600 mt-1">{(riskStatus?.daily_return_pct ?? 0).toFixed(2)}% return</p>
              </div>
              <div className="bg-orange-50 p-4 rounded-lg">
                <p className="text-sm text-gray-600 mb-1">Max Drawdown</p>
                <p className="text-3xl font-bold text-orange-600">{(riskStatus?.max_drawdown_pct ?? 0).toFixed(2)}%</p>
              </div>
              <div className="bg-blue-50 p-4 rounded-lg">
                <p className="text-sm text-gray-600 mb-1">Active Alerts</p>
                <p className="text-3xl font-bold text-blue-600">{alerts.filter(a => !a.acknowledged).length}</p>
                <p className="text-sm text-gray-600 mt-1">{alerts.length} total</p>
              </div>
            </div>
          </Card>

          {/* Alerts Feed */}
          <Card title="Recent Alerts">
            {alerts.length === 0 ? <p className="text-gray-500 text-center py-8">No alerts to display</p> : (
              <div className="space-y-3">
                {alerts.slice(0, 10).map((alert) => (
                  <Alert key={alert.id} variant={getAlertVariant(alert.level)} title={alert.title}>
                    <div className="flex items-start justify-between">
                      <div className="flex-1"><p className="text-sm">{alert.message}</p><p className="text-xs text-gray-500 mt-1">{new Date(alert.timestamp).toLocaleString()}</p></div>
                      <Badge variant={getAlertVariant(alert.level)}>{alert.level}</Badge>
                    </div>
                  </Alert>
                ))}
              </div>
            )}
          </Card>
        </div>
      )}

      {/* --- TAB: SHADOW TRADING --- */}
      {activeTab === 'shadow' && (
        <div className="space-y-6">
          <Card title="Shadow Trading Logs (v2.0 Neural Link)">
            <div className="bg-gray-900 rounded-lg p-4 font-mono text-sm text-green-400 h-96 overflow-y-auto">
              {shadowLogs.map((log, i) => (
                <div key={i} className="mb-2 pb-2 border-b border-gray-800 last:border-0">
                  <div className="flex items-center gap-2">
                    <span className="text-gray-500">[{new Date(log.timestamp).toLocaleTimeString()}]</span>
                    <span className="font-bold text-yellow-500">{log.ticker}</span>
                    <span className={`font-bold ${log.intent.direction === 'BUY' ? 'text-green-500' : 'text-red-500'}`}>{log.intent.direction}</span>
                    <span className="text-gray-400">Score: {log.intent.score}</span>
                  </div>
                  <div className="pl-4 mt-1 text-xs text-gray-300">
                    Rationale: {log.intent.rationale.join(', ')}
                  </div>
                  <div className="pl-4 mt-1 flex items-center gap-2">
                    <span className="text-purple-400">Status: {log.status}</span>
                    {log.execution && (
                      <span className="text-blue-400">Exec: {log.execution.action === 2 ? 'BUY' : 'SELL'} @ ${log.execution.price}</span>
                    )}
                  </div>
                </div>
              ))}
              <div className="animate-pulse mt-4">_ Waiting for next neural signal...</div>
            </div>
          </Card>
        </div>
      )}

      {/* --- TAB: SYSTEM HEALTH --- */}
      {activeTab === 'system' && (
        <div className="space-y-6">
          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card>
              <div className="flex items-center justify-between">
                <div><p className="text-sm text-gray-600">Total Tickers</p><p className="text-2xl font-bold text-gray-900">{mockStats.total_tickers}</p></div>
                <Database className="text-blue-500" size={32} />
              </div>
            </Card>
            <Card>
              <div className="flex items-center justify-between">
                <div><p className="text-sm text-gray-600">Rows Stored</p><p className="text-2xl font-bold text-gray-900">{(mockStats.total_rows_stored / 1000).toFixed(1)}K</p></div>
                <TrendingDown className="text-green-500" size={32} />
              </div>
            </Card>
            <Card>
              <div className="flex items-center justify-between">
                <div><p className="text-sm text-gray-600">Cost Savings</p><p className="text-2xl font-bold text-green-600">{mockCostSavings.estimated_monthly_cost.savings_pct}%</p></div>
                <DollarSign className="text-green-500" size={32} />
              </div>
            </Card>
            <Card>
              <div className="flex items-center justify-between">
                <div><p className="text-sm text-gray-600">Speedup</p><p className="text-2xl font-bold text-purple-600">{mockCostSavings.performance.speedup_factor}x</p></div>
                <Zap className="text-purple-500" size={32} />
              </div>
            </Card>
          </div>

          {/* Performance & Storage */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card title="Monthly Cost Comparison">
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={costComparisonData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="cost" name="Cost (USD)" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <div className="mt-4 p-4 bg-green-50 rounded-lg text-sm text-green-900">
                💰 <strong>Savings:</strong> ${mockCostSavings.estimated_monthly_cost.savings_usd}/month ({mockCostSavings.estimated_monthly_cost.savings_pct}% reduction)
              </div>
            </Card>

            <Card title="Storage Usage by Location">
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={storageData} cx="50%" cy="50%" labelLine={false} label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`} outerRadius={80} fill="#8884d8" dataKey="value">
                      {storageData.map((_, index) => <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />)}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="mt-4 text-sm text-gray-600 text-center">
                Total: {mockStorage.total_size_gb.toFixed(2)} GB ({mockStorage.total_files} files)
              </div>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
};

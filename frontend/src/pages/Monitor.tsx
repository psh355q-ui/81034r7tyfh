/**
 * Monitor Page Example
 * Live Trading 모니터링 페이지
 */

import React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Power, Activity, AlertTriangle, CheckCircle, XCircle } from 'lucide-react';
import {
  getRiskStatus,
  activateKillSwitch,
  deactivateKillSwitch,
  getSystemInfo,
  getAlerts,
  type RiskStatus,
  type SystemInfo,
  type RiskAlert,
} from '../services/api';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { Alert } from '../components/common/Alert';

export const Monitor: React.FC = () => {
  const queryClient = useQueryClient();

  // Fetch risk status (5초마다 갱신)
  const {
    data: riskStatus,
    isLoading: riskLoading,
  } = useQuery({
    queryKey: ['risk', 'status'],
    queryFn: getRiskStatus,
    refetchInterval: 5000,
  });

  // Fetch system info
  const {
    data: systemInfo,
    isLoading: systemLoading,
  } = useQuery({
    queryKey: ['system', 'info'],
    queryFn: getSystemInfo,
  });

  // Fetch alerts
  const {
    data: alertsData,
    isLoading: alertsLoading,
  } = useQuery({
    queryKey: ['alerts'],
    queryFn: () => getAlerts(20),
    refetchInterval: 10000,
  });

  // Ensure alerts is always an array
  const alerts = Array.isArray(alertsData) ? alertsData : [];

  // Kill switch mutations
  const activateMutation = useMutation({
    mutationFn: activateKillSwitch,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['risk', 'status'] });
    },
  });

  const deactivateMutation = useMutation({
    mutationFn: deactivateKillSwitch,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['risk', 'status'] });
    },
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
    return (
      <div className="flex items-center justify-center h-screen">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Live Trading Monitor</h1>
        <p className="text-gray-600 mt-1">Real-time system monitoring and control</p>
      </div>

      {/* System Status */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Kill Switch Card */}
        <Card title="Kill Switch" className="bg-gradient-to-br from-red-50 to-orange-50">
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 mb-1">Trading Status</p>
                <p className={`text-2xl font-bold ${
                  riskStatus?.kill_switch_active ? 'text-red-600' : 'text-green-600'
                }`}>
                  {riskStatus?.kill_switch_active ? 'STOPPED' : 'ACTIVE'}
                </p>
              </div>
              <div className={`p-4 rounded-full ${
                riskStatus?.kill_switch_active ? 'bg-red-100' : 'bg-green-100'
              }`}>
                {riskStatus?.kill_switch_active ? (
                  <XCircle className="text-red-600" size={32} />
                ) : (
                  <CheckCircle className="text-green-600" size={32} />
                )}
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
              {riskStatus?.kill_switch_active
                ? 'All trading operations are paused. Click to resume.'
                : 'Click to immediately stop all trading operations.'}
            </p>
          </div>
        </Card>

        {/* System Info Card */}
        <Card title="System Information">
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-600">Version</span>
              <span className="font-semibold">{systemInfo?.version}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Environment</span>
              <Badge variant={systemInfo?.environment === 'production' ? 'danger' : 'info'}>
                {systemInfo?.environment}
              </Badge>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Uptime</span>
              <span className="font-semibold">
                {systemInfo?.uptime_seconds ? formatUptime(systemInfo.uptime_seconds) : 'N/A'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Start Time</span>
              <span className="text-sm">
                {systemInfo?.start_time
                  ? new Date(systemInfo.start_time).toLocaleString()
                  : 'N/A'}
              </span>
            </div>
          </div>

          {/* Component Health */}
          <div className="mt-4 pt-4 border-t border-gray-200">
            <h4 className="text-sm font-medium text-gray-700 mb-2">Components</h4>
            <div className="space-y-2">
              {systemInfo?.components && Object.entries(systemInfo.components).map(([name, status]) => (
                <div key={name} className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">{name}</span>
                  {status ? (
                    <Badge variant="success">
                      <CheckCircle size={12} className="inline mr-1" />
                      Healthy
                    </Badge>
                  ) : (
                    <Badge variant="danger">
                      <XCircle size={12} className="inline mr-1" />
                      Down
                    </Badge>
                  )}
                </div>
              ))}
            </div>
          </div>
        </Card>
      </div>

      {/* Risk Dashboard */}
      <Card title="Risk Dashboard">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Daily P&L */}
          <div className={`p-4 rounded-lg ${
            (riskStatus?.daily_pnl ?? 0) >= 0 ? 'bg-green-50' : 'bg-red-50'
          }`}>
            <p className="text-sm text-gray-600 mb-1">Daily P&L</p>
            <p className={`text-3xl font-bold ${
              (riskStatus?.daily_pnl ?? 0) >= 0 ? 'text-green-600' : 'text-red-600'
            }`}>
              {(riskStatus?.daily_pnl ?? 0) >= 0 ? '+' : ''}
              ${(riskStatus?.daily_pnl ?? 0).toFixed(2)}
            </p>
            <p className="text-sm text-gray-600 mt-1">
              {(riskStatus?.daily_return_pct ?? 0).toFixed(2)}% return
            </p>
          </div>

          {/* Max Drawdown */}
          <div className="bg-orange-50 p-4 rounded-lg">
            <p className="text-sm text-gray-600 mb-1">Max Drawdown</p>
            <p className="text-3xl font-bold text-orange-600">
              {(riskStatus?.max_drawdown_pct ?? 0).toFixed(2)}%
            </p>
          </div>

          {/* Active Alerts */}
          <div className="bg-blue-50 p-4 rounded-lg">
            <p className="text-sm text-gray-600 mb-1">Active Alerts</p>
            <p className="text-3xl font-bold text-blue-600">
              {alerts.filter(a => !a.acknowledged).length}
            </p>
            <p className="text-sm text-gray-600 mt-1">
              {alerts.length} total
            </p>
          </div>
        </div>

        {/* Position Concentration */}
        {riskStatus?.position_concentration && Object.keys(riskStatus.position_concentration).length > 0 && (
          <div className="mt-6">
            <h4 className="text-sm font-medium text-gray-700 mb-3">Position Concentration</h4>
            <div className="space-y-2">
              {Object.entries(riskStatus.position_concentration)
                .sort(([, a], [, b]) => b - a)
                .slice(0, 5)
                .map(([ticker, percentage]) => (
                  <div key={ticker} className="flex items-center gap-3">
                    <span className="text-sm font-medium w-16">{ticker}</span>
                    <div className="flex-1 bg-gray-200 rounded-full h-3">
                      <div
                        className="bg-blue-500 h-3 rounded-full"
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                    <span className="text-sm text-gray-600 w-12 text-right">
                      {(percentage ?? 0).toFixed(1)}%
                    </span>
                  </div>
                ))}
            </div>
          </div>
        )}
      </Card>

      {/* Alerts Feed */}
      <Card title="Recent Alerts">
        {alertsLoading ? (
          <LoadingSpinner />
        ) : alerts.length === 0 ? (
          <p className="text-gray-500 text-center py-8">No alerts to display</p>
        ) : (
          <div className="space-y-3">
            {alerts.slice(0, 10).map((alert) => (
              <Alert
                key={alert.id}
                variant={getAlertVariant(alert.level)}
                title={alert.title}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <p className="text-sm">{alert.message}</p>
                    <p className="text-xs text-gray-500 mt-1">
                      {new Date(alert.timestamp).toLocaleString()}
                    </p>
                  </div>
                  <Badge variant={getAlertVariant(alert.level)}>
                    {alert.level}
                  </Badge>
                </div>
              </Alert>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
};

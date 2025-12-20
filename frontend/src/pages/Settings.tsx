import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Settings as SettingsIcon, Info, Shield, Code } from 'lucide-react';
import { getSystemInfo } from '../services/api';
import { Card } from '../components/common/Card';
import { Badge } from '../components/common/Badge';
import { LoadingSpinner } from '../components/common/LoadingSpinner';

export const Settings: React.FC = () => {
  const {
    data: systemInfo,
    isLoading,
  } = useQuery({
    queryKey: ['system', 'info'],
    queryFn: getSystemInfo,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-600 mt-1">System configuration and information</p>
      </div>

      <Card title="System Information" className="border-l-4 border-l-blue-500">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-4">
            <div className="flex items-start gap-3">
              <Info className="text-blue-600 mt-1" size={20} />
              <div>
                <p className="text-sm text-gray-600">Version</p>
                <p className="text-lg font-semibold">{systemInfo?.version || 'N/A'}</p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <Code className="text-green-600 mt-1" size={20} />
              <div>
                <p className="text-sm text-gray-600">Environment</p>
                <Badge variant={systemInfo?.environment === 'production' ? 'danger' : 'info'}>
                  {systemInfo?.environment || 'N/A'}
                </Badge>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <SettingsIcon className="text-purple-600 mt-1" size={20} />
              <div>
                <p className="text-sm text-gray-600">Start Time</p>
                <p className="text-sm">
                  {systemInfo?.start_time
                    ? new Date(systemInfo.start_time).toLocaleString()
                    : 'N/A'}
                </p>
              </div>
            </div>
          </div>

          <div className="space-y-4">
            <div className="flex items-start gap-3">
              <Shield className="text-orange-600 mt-1" size={20} />
              <div>
                <p className="text-sm text-gray-600">Uptime</p>
                <p className="text-lg font-semibold">
                  {systemInfo?.uptime_seconds
                    ? `${Math.floor(systemInfo.uptime_seconds / 3600)}h ${Math.floor((systemInfo.uptime_seconds % 3600) / 60)}m`
                    : 'N/A'}
                </p>
              </div>
            </div>

            <div>
              <p className="text-sm text-gray-600 mb-2">Component Health</p>
              <div className="space-y-2">
                {systemInfo?.components && Object.entries(systemInfo.components).map(([name, status]) => (
                  <div key={name} className="flex items-center justify-between">
                    <span className="text-sm">{name}</span>
                    <Badge variant={status ? 'success' : 'danger'}>
                      {status ? 'Healthy' : 'Down'}
                    </Badge>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </Card>

      {systemInfo?.config && (
        <Card title="Trading Configuration" className="border-l-4 border-l-green-500">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {Object.entries(systemInfo.config).map(([key, value]) => (
              <div key={key} className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                <span className="text-sm font-medium text-gray-700">
                  {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                </span>
                <span className="text-sm font-semibold">
                  {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                </span>
              </div>
            ))}
          </div>
        </Card>
      )}

      <Card title="API Configuration" className="border-l-4 border-l-yellow-500">
        <div className="space-y-4">
          <div className="bg-yellow-50 p-4 rounded-lg">
            <p className="text-sm text-yellow-800">
              API configuration is managed through environment variables and config files.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 border border-gray-200 rounded-lg">
              <p className="text-sm text-gray-600 mb-1">API Base URL</p>
              <p className="text-sm font-mono bg-gray-50 p-2 rounded">
                http://localhost:8001
              </p>
            </div>

            <div className="p-4 border border-gray-200 rounded-lg">
              <p className="text-sm text-gray-600 mb-1">WebSocket Endpoint</p>
              <p className="text-sm font-mono bg-gray-50 p-2 rounded">
                ws://localhost:8001/ws
              </p>
            </div>
          </div>
        </div>
      </Card>

      <Card title="Advanced Settings" className="border-l-4 border-l-red-500">
        <div className="space-y-4">
          <div className="bg-red-50 p-4 rounded-lg">
            <p className="text-sm text-red-800 font-medium mb-2">⚠️ Warning</p>
            <p className="text-sm text-red-700">
              Advanced settings can significantly impact system behavior.
              Modify with caution and only if you understand the implications.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 border border-gray-200 rounded-lg opacity-50">
              <p className="text-sm font-medium mb-2">Risk Limits</p>
              <p className="text-xs text-gray-500">Feature coming soon</p>
            </div>

            <div className="p-4 border border-gray-200 rounded-lg opacity-50">
              <p className="text-sm font-medium mb-2">Notification Settings</p>
              <p className="text-xs text-gray-500">Feature coming soon</p>
            </div>

            <div className="p-4 border border-gray-200 rounded-lg opacity-50">
              <p className="text-sm font-medium mb-2">Data Retention</p>
              <p className="text-xs text-gray-500">Feature coming soon</p>
            </div>

            <div className="p-4 border border-gray-200 rounded-lg opacity-50">
              <p className="text-sm font-medium mb-2">API Rate Limits</p>
              <p className="text-xs text-gray-500">Feature coming soon</p>
            </div>
          </div>
        </div>
      </Card>

      <Card title="About">
        <div className="text-center space-y-4 py-6">
          <div className="flex justify-center">
            <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center">
              <SettingsIcon className="text-blue-600" size={32} />
            </div>
          </div>

          <div>
            <h3 className="text-xl font-bold text-gray-900">AI Trading System</h3>
            <p className="text-gray-600 mt-1">Intelligent Trading Platform</p>
          </div>

          <div className="text-sm text-gray-500">
            <p>Version {systemInfo?.version || '1.0.0'}</p>
            <p className="mt-1">© 2025 AI Trading System. All rights reserved.</p>
          </div>

          <div className="pt-4 border-t border-gray-200">
            <p className="text-xs text-gray-500">
              Built with React, TypeScript, Tailwind CSS, and FastAPI
            </p>
          </div>
        </div>
      </Card>
    </div>
  );
};

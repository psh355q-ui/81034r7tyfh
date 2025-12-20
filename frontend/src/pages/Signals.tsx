/**
 * Trading Signals Dashboard
 * 
 * Features:
 * - View active signals
 * - Approve/Reject signals
 * - Signal history
 * - Real-time updates
 * - Validator status monitoring
 * 
 * Author: AI Trading System
 * Date: 2025-11-15
 */

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  TrendingUp,
  TrendingDown,
  Minus,
  Check,
  X,
  Play,
  AlertTriangle,
  Activity,
  Target,
  Shield,
  Zap,
  BarChart2,
  History,
  Settings,
} from 'lucide-react';

// API Types
interface TradingSignal {
  id: number;
  ticker: string;
  action: string;
  position_size: number;
  confidence: number;
  execution_type: string;
  reason: string;
  urgency: string;
  created_at: string;
  news_title: string | null;
  affected_sectors: string[];
  auto_execute: boolean;
  status: string;
  approved_at: string | null;
  rejected_at: string | null;
  executed_at: string | null;
  rejection_reason: string | null;
}

interface ValidatorStatus {
  kill_switch_active: boolean;
  kill_switch_reason: string;
  daily_trades_count: number;
  daily_trade_limit: number;
  daily_pnl: number;
  daily_loss_limit: number;
  consecutive_losses: number;
  max_consecutive_losses: number;
  market_open: boolean;
  statistics: Record<string, number>;
}

// API Configuration
const API_BASE = '/api';
const API_KEY = import.meta.env.VITE_API_KEY || '';

const apiHeaders = {
  'Content-Type': 'application/json',
  'X-API-Key': API_KEY,
};

// API Functions
const fetchActiveSignals = async (): Promise<TradingSignal[]> => {
  const response = await fetch(`${API_BASE}/api/signals/active`, {
    headers: apiHeaders,
  });
  if (!response.ok) throw new Error('Failed to fetch active signals');
  return response.json();
};

const fetchSignalHistory = async (limit = 50): Promise<TradingSignal[]> => {
  const response = await fetch(`${API_BASE}/api/signals/history?limit=${limit}`, {
    headers: apiHeaders,
  });
  if (!response.ok) throw new Error('Failed to fetch signal history');
  return response.json();
};

const fetchValidatorStatus = async (): Promise<ValidatorStatus> => {
  const response = await fetch(`${API_BASE}/api/signals/validator/status`, {
    headers: apiHeaders,
  });
  if (!response.ok) throw new Error('Failed to fetch validator status');
  return response.json();
};

const approveSignal = async ({
  signalId,
  executeImmediately,
  adjustedSize,
}: {
  signalId: number;
  executeImmediately: boolean;
  adjustedSize?: number;
}): Promise<any> => {
  const response = await fetch(`${API_BASE}/api/signals/${signalId}/approve`, {
    method: 'PUT',
    headers: apiHeaders,
    body: JSON.stringify({
      execute_immediately: executeImmediately,
      adjusted_position_size: adjustedSize,
    }),
  });
  if (!response.ok) throw new Error('Failed to approve signal');
  return response.json();
};

const rejectSignal = async ({
  signalId,
  reason,
}: {
  signalId: number;
  reason: string;
}): Promise<any> => {
  const response = await fetch(
    `${API_BASE}/api/signals/${signalId}/reject?reason=${encodeURIComponent(reason)}`,
    {
      method: 'DELETE',
      headers: apiHeaders,
    }
  );
  if (!response.ok) throw new Error('Failed to reject signal');
  return response.json();
};

const resetKillSwitch = async (): Promise<any> => {
  const response = await fetch(`${API_BASE}/api/signals/validator/reset-kill-switch`, {
    method: 'POST',
    headers: apiHeaders,
  });
  if (!response.ok) throw new Error('Failed to reset kill switch');
  return response.json();
};

// Components
const StatusBadge: React.FC<{ status: string }> = ({ status }) => {
  const colors: Record<string, string> = {
    PENDING: 'bg-yellow-100 text-yellow-800 border-yellow-300',
    APPROVED: 'bg-green-100 text-green-800 border-green-300',
    REJECTED: 'bg-red-100 text-red-800 border-red-300',
    EXECUTED: 'bg-blue-100 text-blue-800 border-blue-300',
  };

  return (
    <span
      className={`px-2 py-1 rounded-full text-xs font-medium border ${colors[status] || 'bg-gray-100 text-gray-800'
        }`}
    >
      {status}
    </span>
  );
};

const ActionIcon: React.FC<{ action: string }> = ({ action }) => {
  if (action === 'BUY') {
    return <TrendingUp className="w-5 h-5 text-green-500" />;
  } else if (action === 'SELL') {
    return <TrendingDown className="w-5 h-5 text-red-500" />;
  }
  return <Minus className="w-5 h-5 text-gray-500" />;
};

const UrgencyBadge: React.FC<{ urgency: string }> = ({ urgency }) => {
  const colors: Record<string, string> = {
    IMMEDIATE: 'bg-red-500 text-white',
    HIGH: 'bg-orange-500 text-white',
    MEDIUM: 'bg-yellow-500 text-white',
    LOW: 'bg-gray-500 text-white',
  };

  return (
    <span className={`px-2 py-1 rounded text-xs font-bold ${colors[urgency] || 'bg-gray-500'}`}>
      {urgency}
    </span>
  );
};

const ConfidenceBar: React.FC<{ confidence: number }> = ({ confidence }) => {
  const percentage = confidence * 100;
  const color =
    percentage >= 80 ? 'bg-green-500' : percentage >= 60 ? 'bg-yellow-500' : 'bg-red-500';

  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 bg-gray-200 rounded-full h-2">
        <div className={`${color} h-2 rounded-full`} style={{ width: `${percentage}%` }} />
      </div>
      <span className="text-sm font-medium">{percentage.toFixed(0)}%</span>
    </div>
  );
};

const SignalCard: React.FC<{
  signal: TradingSignal;
  onApprove: (signalId: number, execute: boolean) => void;
  onReject: (signalId: number, reason: string) => void;
}> = ({ signal, onApprove, onReject }) => {
  const [showRejectModal, setShowRejectModal] = useState(false);
  const [rejectReason, setRejectReason] = useState('');

  const actionColor = signal.action === 'BUY' ? 'border-green-500' : 'border-red-500';
  const actionBg = signal.action === 'BUY' ? 'bg-green-50' : 'bg-red-50';

  return (
    <div className={`bg-white rounded-lg shadow-md p-4 border-l-4 ${actionColor}`}>
      <div className="flex justify-between items-start mb-3">
        <div className="flex items-center gap-3">
          <ActionIcon action={signal.action} />
          <div>
            <span className="text-2xl font-bold">${signal.ticker}</span>
            <span
              className={`ml-2 text-lg font-semibold ${signal.action === 'BUY' ? 'text-green-600' : 'text-red-600'
                }`}
            >
              {signal.action}
            </span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <UrgencyBadge urgency={signal.urgency} />
          {signal.auto_execute && (
            <span className="flex items-center gap-1 text-xs bg-purple-100 text-purple-800 px-2 py-1 rounded">
              <Zap className="w-3 h-3" />
              AUTO
            </span>
          )}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-3">
        <div>
          <p className="text-xs text-gray-500">Position Size</p>
          <p className="text-lg font-semibold">{(signal.position_size * 100).toFixed(1)}%</p>
        </div>
        <div>
          <p className="text-xs text-gray-500">Execution</p>
          <p className="text-sm font-medium">{signal.execution_type}</p>
        </div>
      </div>

      <div className="mb-3">
        <p className="text-xs text-gray-500 mb-1">Confidence</p>
        <ConfidenceBar confidence={signal.confidence} />
      </div>

      <div className="mb-3">
        <p className="text-xs text-gray-500">Reason</p>
        <p className="text-sm">{signal.reason}</p>
      </div>

      {signal.news_title && (
        <div className="mb-3">
          <p className="text-xs text-gray-500">Source</p>
          <p className="text-sm truncate">{signal.news_title}</p>
        </div>
      )}

      {signal.affected_sectors.length > 0 && (
        <div className="mb-4">
          <p className="text-xs text-gray-500">Sectors</p>
          <div className="flex gap-1 flex-wrap mt-1">
            {signal.affected_sectors.map((sector) => (
              <span
                key={sector}
                className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded"
              >
                {sector}
              </span>
            ))}
          </div>
        </div>
      )}

      <div className="flex gap-2">
        <button
          onClick={() => onApprove(signal.id, false)}
          className="flex-1 flex items-center justify-center gap-1 bg-green-500 text-white py-2 px-4 rounded-lg hover:bg-green-600 transition"
        >
          <Check className="w-4 h-4" />
          Approve
        </button>
        <button
          onClick={() => onApprove(signal.id, true)}
          className="flex items-center gap-1 bg-green-700 text-white py-2 px-4 rounded-lg hover:bg-green-800 transition"
        >
          <Play className="w-4 h-4" />
          Execute
        </button>
        <button
          onClick={() => setShowRejectModal(true)}
          className="flex items-center gap-1 bg-red-500 text-white py-2 px-3 rounded-lg hover:bg-red-600 transition"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      <div className="mt-3 text-xs text-gray-400">
        Created: {new Date(signal.created_at).toLocaleString()}
      </div>

      {/* Reject Modal */}
      {showRejectModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-96">
            <h3 className="text-lg font-bold mb-4">Reject Signal</h3>
            <textarea
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
              placeholder="Reason for rejection..."
              className="w-full border rounded-lg p-2 h-24 mb-4"
            />
            <div className="flex gap-2">
              <button
                onClick={() => {
                  onReject(signal.id, rejectReason || 'Manual rejection');
                  setShowRejectModal(false);
                  setRejectReason('');
                }}
                className="flex-1 bg-red-500 text-white py-2 rounded-lg hover:bg-red-600"
              >
                Reject
              </button>
              <button
                onClick={() => setShowRejectModal(false)}
                className="flex-1 border py-2 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

const ValidatorStatusCard: React.FC<{ status: ValidatorStatus }> = ({ status }) => {
  return (
    <div
      className={`bg-white rounded-lg shadow p-4 ${status.kill_switch_active ? 'border-2 border-red-500' : ''
        }`}
    >
      <div className="flex items-center gap-2 mb-3">
        <Shield className="w-5 h-5 text-blue-500" />
        <h3 className="font-semibold">Validator Status</h3>
      </div>

      {status.kill_switch_active && (
        <div className="bg-red-100 border border-red-300 rounded p-3 mb-3">
          <div className="flex items-center gap-2 text-red-700 font-bold">
            <AlertTriangle className="w-5 h-5" />
            KILL SWITCH ACTIVE
          </div>
          <p className="text-sm text-red-600 mt-1">{status.kill_switch_reason}</p>
        </div>
      )}

      <div className="space-y-2 text-sm">
        <div className="flex justify-between">
          <span>Market Status:</span>
          <span
            className={`font-medium ${status.market_open ? 'text-green-600' : 'text-red-600'}`}
          >
            {status.market_open ? 'OPEN' : 'CLOSED'}
          </span>
        </div>

        <div className="flex justify-between">
          <span>Daily Trades:</span>
          <span>
            {status.daily_trades_count} / {status.daily_trade_limit}
          </span>
        </div>

        <div className="flex justify-between">
          <span>Daily P&L:</span>
          <span
            className={`font-medium ${status.daily_pnl >= 0 ? 'text-green-600' : 'text-red-600'
              }`}
          >
            {status.daily_pnl >= 0 ? '+' : ''}
            {status.daily_pnl.toFixed(2)}%
          </span>
        </div>

        <div className="flex justify-between">
          <span>Consecutive Losses:</span>
          <span
            className={
              status.consecutive_losses >= status.max_consecutive_losses - 1
                ? 'text-red-600 font-bold'
                : ''
            }
          >
            {status.consecutive_losses} / {status.max_consecutive_losses}
          </span>
        </div>
      </div>

      {/* Progress bars */}
      <div className="mt-3">
        <p className="text-xs text-gray-500 mb-1">Daily Trade Usage</p>
        <div className="bg-gray-200 rounded-full h-2">
          <div
            className="bg-blue-500 h-2 rounded-full"
            style={{
              width: `${(status.daily_trades_count / status.daily_trade_limit) * 100}%`,
            }}
          />
        </div>
      </div>

      <div className="mt-2">
        <p className="text-xs text-gray-500 mb-1">Loss Limit Usage</p>
        <div className="bg-gray-200 rounded-full h-2">
          <div
            className={`h-2 rounded-full ${Math.abs(status.daily_pnl) >= status.daily_loss_limit * 0.8
                ? 'bg-red-500'
                : 'bg-green-500'
              }`}
            style={{
              width: `${Math.min(
                100,
                (Math.abs(status.daily_pnl) / status.daily_loss_limit) * 100
              )}%`,
            }}
          />
        </div>
      </div>
    </div>
  );
};

const SignalHistoryTable: React.FC<{ signals: TradingSignal[] }> = ({ signals }) => {
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500">Time</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500">Ticker</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500">Action</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500">Size</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500">Confidence</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500">Status</th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {signals.map((signal) => (
            <tr key={signal.id} className="hover:bg-gray-50">
              <td className="px-4 py-3 text-sm text-gray-500">
                {new Date(signal.created_at).toLocaleString()}
              </td>
              <td className="px-4 py-3 text-sm font-medium">${signal.ticker}</td>
              <td className="px-4 py-3">
                <div className="flex items-center gap-1">
                  <ActionIcon action={signal.action} />
                  <span className="text-sm">{signal.action}</span>
                </div>
              </td>
              <td className="px-4 py-3 text-sm">{(signal.position_size * 100).toFixed(1)}%</td>
              <td className="px-4 py-3 text-sm">{(signal.confidence * 100).toFixed(0)}%</td>
              <td className="px-4 py-3">
                <StatusBadge status={signal.status} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

// Main Component
export const Signals: React.FC = () => {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<'active' | 'history' | 'settings'>('active');

  // Queries
  const { data: activeSignals = [], isLoading: activeLoading } = useQuery({
    queryKey: ['signals', 'active'],
    queryFn: fetchActiveSignals,
    refetchInterval: 5000, // Refresh every 5 seconds
  });

  const { data: signalHistory = [] } = useQuery({
    queryKey: ['signals', 'history'],
    queryFn: () => fetchSignalHistory(100),
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  const { data: validatorStatus } = useQuery({
    queryKey: ['validator', 'status'],
    queryFn: fetchValidatorStatus,
    refetchInterval: 10000, // Refresh every 10 seconds
  });

  // Mutations
  const approveMutation = useMutation({
    mutationFn: approveSignal,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['signals'] });
    },
    onError: (error: Error) => {
      alert(`Failed to approve: ${error.message}`);
    },
  });

  const rejectMutation = useMutation({
    mutationFn: rejectSignal,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['signals'] });
    },
    onError: (error: Error) => {
      alert(`Failed to reject: ${error.message}`);
    },
  });

  const resetKillSwitchMutation = useMutation({
    mutationFn: resetKillSwitch,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['validator'] });
      alert('Kill switch has been reset');
    },
  });

  // Handlers
  const handleApprove = (signalId: number, executeImmediately: boolean) => {
    const confirmMessage = executeImmediately
      ? 'Execute this signal immediately?'
      : 'Approve this signal?';
    if (window.confirm(confirmMessage)) {
      approveMutation.mutate({ signalId, executeImmediately });
    }
  };

  const handleReject = (signalId: number, reason: string) => {
    rejectMutation.mutate({ signalId, reason });
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold flex items-center gap-2">
          <Target className="w-8 h-8 text-blue-500" />
          Trading Signals
        </h1>

        {validatorStatus?.kill_switch_active && (
          <button
            onClick={() => {
              if (window.confirm('Are you sure you want to reset the kill switch?')) {
                resetKillSwitchMutation.mutate();
              }
            }}
            className="bg-red-500 text-white px-4 py-2 rounded-lg hover:bg-red-600 flex items-center gap-2"
          >
            <AlertTriangle className="w-4 h-4" />
            Reset Kill Switch
          </button>
        )}
      </div>

      {/* Validator Status */}
      {validatorStatus && <ValidatorStatusCard status={validatorStatus} />}

      {/* Tabs */}
      <div className="flex gap-2 border-b">
        <button
          onClick={() => setActiveTab('active')}
          className={`px-4 py-2 font-medium flex items-center gap-2 ${activeTab === 'active'
              ? 'border-b-2 border-blue-500 text-blue-600'
              : 'text-gray-500 hover:text-gray-700'
            }`}
        >
          <Activity className="w-4 h-4" />
          Active Signals
          {activeSignals.length > 0 && (
            <span className="bg-red-500 text-white text-xs px-2 py-0.5 rounded-full">
              {activeSignals.length}
            </span>
          )}
        </button>

        <button
          onClick={() => setActiveTab('history')}
          className={`px-4 py-2 font-medium flex items-center gap-2 ${activeTab === 'history'
              ? 'border-b-2 border-blue-500 text-blue-600'
              : 'text-gray-500 hover:text-gray-700'
            }`}
        >
          <History className="w-4 h-4" />
          History
        </button>

        <button
          onClick={() => setActiveTab('settings')}
          className={`px-4 py-2 font-medium flex items-center gap-2 ${activeTab === 'settings'
              ? 'border-b-2 border-blue-500 text-blue-600'
              : 'text-gray-500 hover:text-gray-700'
            }`}
        >
          <Settings className="w-4 h-4" />
          Settings
        </button>
      </div>

      {/* Tab Content */}
      {activeTab === 'active' && (
        <div>
          {activeLoading ? (
            <div className="text-center py-8">Loading signals...</div>
          ) : activeSignals.length === 0 ? (
            <div className="text-center py-12 bg-gray-50 rounded-lg">
              <Activity className="w-12 h-12 text-gray-400 mx-auto mb-3" />
              <p className="text-gray-500">No active signals</p>
              <p className="text-sm text-gray-400">
                Signals will appear here when news generates trading opportunities
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {activeSignals.map((signal) => (
                <SignalCard
                  key={signal.id}
                  signal={signal}
                  onApprove={handleApprove}
                  onReject={handleReject}
                />
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === 'history' && (
        <div className="bg-white rounded-lg shadow">
          <div className="p-4 border-b">
            <h3 className="font-semibold flex items-center gap-2">
              <BarChart2 className="w-5 h-5" />
              Signal History
            </h3>
          </div>
          {signalHistory.length === 0 ? (
            <div className="p-8 text-center text-gray-500">No signal history yet</div>
          ) : (
            <SignalHistoryTable signals={signalHistory} />
          )}
        </div>
      )}

      {activeTab === 'settings' && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">Signal Settings</h3>
          <p className="text-gray-500">Settings panel coming soon...</p>
          {/* TODO: Add settings form */}
        </div>
      )}
    </div>
  );
};

export default Signals;

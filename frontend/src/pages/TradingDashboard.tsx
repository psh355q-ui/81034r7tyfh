/**
 * Trading Dashboard - Real-time Signal Stream
 *
 * Features:
 * - Live signal stream with WebSocket
 * - Filter by type, confidence, ticker
 * - Quick stats overview
 * - Click to view signal details
 */

/**
 * TradingDashboard.tsx - 트레이딩 대시보드
 * 
 * 📊 Data Sources:
 *   - API: GET /api/signals (트레이딩 시그널)
 *   - API: GET /api/orders (주문 내역)
 *   - API: POST /api/trade/execute (매매 실행)
 *   - State: signals, orders, selectedSignal
 * 
 * 🔗 Dependencies:
 *   - react: useState, useEffect
 *   - @tanstack/react-query: useQuery, useMutation
 *   - lucide-react: TrendingUp, Activity, AlertCircle
 * 
 * 📤 Components Used:
 *   - Card, LoadingSpinner, Button
 *   - ExecuteTradeModal: 매매 실행 모달
 *   - ClosePositionModal: 포지션 청산 모달
 * 
 * 🔄 Used By:
 *   - App.tsx (route: /trading)
 * 
 * 📝 Notes:
 *   - Phase 26: REAL MODE 실거래
 *   - KIS Broker 연동
 *   - 실시간 시그널 모니터링
 */

import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  TrendingUp,
  TrendingDown,
  Star,
  AlertTriangle,
  Filter,
  RefreshCw,
  Zap,
  Play
} from 'lucide-react';
import { ExecuteTradeModal } from '../components/Trading/ExecuteTradeModal';
import { notification } from 'antd';

// Types
interface Signal {
  id: number;
  ticker: string;
  action: string;
  signal_type: string;
  confidence: number;
  reasoning: string;
  created_at: string;
  alert_sent: boolean;
  news_title?: string;
  news_source?: string;
  analysis_theme?: string;
}

interface SignalStats {
  total_signals: number;
  signals_today: number;
  signals_this_week: number;
  primary_count: number;
  hidden_count: number;
  loser_count: number;
  avg_confidence: number;
  high_confidence_count: number;
  top_tickers: Array<{ ticker: string; count: number; avg_confidence: number }>;
}

// API URLs - 환경변수에서 읽거나 자동 감지
const API_BASE_URL = import.meta.env.VITE_API_URL ||
  (window.location.hostname === 'localhost' ? 'http://localhost:8001' : `http://${window.location.hostname}:8001`);

// For local debugging, prioritize strict IPv4 localhost
const WS_URL = window.location.hostname === 'localhost'
  ? 'ws://127.0.0.1:8001/api/signals/ws'
  : (import.meta.env.VITE_WS_URL || `ws://${window.location.hostname}:8001/api/signals/ws`);

export default function TradingDashboard() {
  const [signals, setSignals] = useState<Signal[]>([]);
  const [stats, setStats] = useState<SignalStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [connected, setConnected] = useState(false);

  // Filters
  const [filterType, setFilterType] = useState<string>('ALL');
  const [filterMinConfidence, setFilterMinConfidence] = useState<number>(0);
  const [searchTicker, setSearchTicker] = useState<string>('');

  // Execute Trade Modal
  const [selectedSignal, setSelectedSignal] = useState<Signal | null>(null);
  const [isExecuteModalOpen, setIsExecuteModalOpen] = useState(false);

  // ...

  // WebSocket with Auto-Reconnection
  useEffect(() => {
    let ws: WebSocket | null = null;
    let reconnectTimer: number;
    let reconnectAttempts = 0;
    const MAX_RECONNECT_ATTEMPTS = 10;

    const connect = () => {
      if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
        console.error('[WebSocket] Max reconnection attempts reached. Please refresh the page.');
        notification.error({
          message: 'WebSocket Connection Failed',
          description: 'Unable to connect to real-time signal stream. Please refresh the page.',
          placement: 'topRight',
          duration: 0, // Don't auto-close
        });
        return;
      }

      ws = new WebSocket(WS_URL);

      ws.onopen = () => {
        console.log('[WebSocket] Connected to signal stream');
        setConnected(true);
        reconnectAttempts = 0; // Reset counter on successful connection
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('[WebSocket] Message:', data);

        if (data.type === 'new_signal') {
          // Add new signal to top of list
          setSignals((prev) => [data.data, ...prev]);
          notification.info({
            message: 'New Signal Generated',
            description: `${data.data.ticker} ${data.data.action} (Confidence: ${(data.data.confidence * 100).toFixed(0)}%)`,
            placement: 'topRight',
            duration: 5,
          });
        } else if (data.type === 'order_filled') {
          const order = data.data;
          notification.success({
            message: 'Order Filled',
            description: `${order.side} ${order.quantity} ${order.ticker} @ $${order.avg_price}`,
            placement: 'topRight',
            duration: 8,
          });
        } else if (data.type === 'order_sent') {
          notification.info({
            message: 'Order Sent to Broker',
            description: `Sending order for ${data.data.ticker}...`,
            placement: 'topRight',
            duration: 3,
          });
        } else if (data.type === 'order_rejected' || data.type === 'order_failed') {
          notification.error({
            message: 'Order Failed',
            description: `Order for ${data.data.ticker} failed: ${data.data.reason || 'Unknown error'}`,
            placement: 'topRight',
            duration: 10,
          });
        }
      };

      ws.onerror = (error) => {
        console.warn('[WebSocket] Connection error, will retry...', error);
        setConnected(false);
      };

      ws.onclose = () => {
        console.log(`[WebSocket] Disconnected, reconnecting in 3s... (attempt ${reconnectAttempts + 1}/${MAX_RECONNECT_ATTEMPTS})`);
        setConnected(false);
        reconnectAttempts++;
        reconnectTimer = setTimeout(connect, 3000); // Reconnect after 3 seconds
      };
    };

    connect();

    return () => {
      if (ws) ws.close();
      clearTimeout(reconnectTimer);
    };
  }, []);

  // Fetch initial signals
  useEffect(() => {
    fetchSignals();
    fetchStats();
  }, []);

  const fetchSignals = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/signals?hours=168&limit=100`);
      const data = await response.json();
      setSignals(data);
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch signals:', error);
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/signals/stats/summary`);
      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  };

  const handleExecuteTrade = async (signalId: number, entryPrice: number, shares: number) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/signals/${signalId}/execute`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          entry_price: entryPrice,
          shares: shares
        })
      });

      if (!response.ok) {
        throw new Error('Failed to execute trade');
      }

      // Refresh signals to show updated entry_price
      await fetchSignals();
    } catch (error) {
      console.error('Execute trade error:', error);
      throw error;
    }
  };

  const openExecuteModal = (signal: Signal) => {
    setSelectedSignal(signal);
    setIsExecuteModalOpen(true);
  };

  const closeExecuteModal = () => {
    setSelectedSignal(null);
    setIsExecuteModalOpen(false);
  };

  // Filter signals
  const filteredSignals = signals.filter((signal) => {
    if (filterType !== 'ALL' && signal.signal_type !== filterType) return false;
    if (signal.confidence < filterMinConfidence) return false;
    if (searchTicker && !signal.ticker.toLowerCase().includes(searchTicker.toLowerCase())) return false;
    return true;
  });

  // Signal type badge
  const getSignalTypeBadge = (type: string) => {
    const badges = {
      PRIMARY: { bg: 'bg-blue-100', text: 'text-blue-800', icon: TrendingUp },
      HIDDEN: { bg: 'bg-purple-100', text: 'text-purple-800', icon: Star },
      LOSER: { bg: 'bg-red-100', text: 'text-red-800', icon: AlertTriangle }
    };

    const badge = badges[type as keyof typeof badges] || badges.PRIMARY;
    const Icon = badge.icon;

    return (
      <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm font-medium ${badge.bg} ${badge.text}`}>
        <Icon className="w-4 h-4" />
        {type}
      </span>
    );
  };

  // Action badge
  const getActionBadge = (action: string) => {
    const colors = {
      BUY: 'bg-green-100 text-green-800',
      SELL: 'bg-red-100 text-red-800',
      TRIM: 'bg-yellow-100 text-yellow-800',
      HOLD: 'bg-gray-100 text-gray-800'
    };

    return (
      <span className={`px-2 py-1 rounded text-sm font-semibold ${colors[action as keyof typeof colors] || 'bg-gray-100 text-gray-800'}`}>
        {action}
      </span>
    );
  };

  // Confidence bar
  const ConfidenceBar = ({ confidence }: { confidence: number }) => {
    // Fix: Handle both percentage (>1) and decimal (0-1) formats
    // Backend may send either 99.9 or 0.999 depending on the source
    const percentage = confidence > 1 ? confidence : confidence * 100;
    const color = percentage >= 85 ? 'bg-green-500' : percentage >= 70 ? 'bg-yellow-500' : 'bg-red-500';

    return (
      <div className="flex-1 items-center gap-2">
        <div className="flex-1 bg-gray-200 rounded-full h-2">
          <div className={`h-2 rounded-full ${color}`} style={{ width: `${Math.min(percentage, 100)}%` }}></div>
        </div>
        <span className="text-sm font-medium text-gray-700 w-12">{Math.min(percentage, 100).toFixed(0)}%</span>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="flex flex-col items-center gap-4">
          <RefreshCw className="w-12 h-12 animate-spin text-blue-500" />
          <p className="text-gray-600">Loading trading signals...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
              <Zap className="w-8 h-8 text-blue-500" />
              Trading Dashboard
            </h1>
            <p className="text-gray-600 mt-1">Real-time signal stream powered by Phase 14-16 AI system</p>
          </div>

          <div className="flex items-center gap-4">
            {/* Connection Status */}
            <div className="flex items-center gap-2">
              <div className={`w-3 h-3 rounded-full ${connected ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`}></div>
              <span className="text-sm text-gray-600">{connected ? 'Live' : 'Disconnected'}</span>
            </div>

            {/* Refresh Button */}
            <button
              onClick={() => { fetchSignals(); fetchStats(); }}
              className="flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition"
            >
              <RefreshCw className="w-4 h-4" />
              Refresh
            </button>
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
          {/* Total Signals */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-gray-600">Total Signals</h3>
              <TrendingUp className="w-5 h-5 text-blue-500" />
            </div>
            <p className="text-3xl font-bold text-gray-900">{stats.total_signals}</p>
            <p className="text-sm text-gray-500 mt-1">Last 7 days</p>
          </div>

          {/* Hidden Beneficiaries */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-gray-600">Hidden Beneficiaries</h3>
              <Star className="w-5 h-5 text-purple-500" />
            </div>
            <p className="text-3xl font-bold text-purple-600">{stats.hidden_count}</p>
            <p className="text-sm text-gray-500 mt-1">{stats.total_signals > 0 ? ((stats.hidden_count / stats.total_signals) * 100).toFixed(1) : '0.0'}% of total</p>
          </div>

          {/* Avg Confidence */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-gray-600">Avg Confidence</h3>
              <Zap className="w-5 h-5 text-green-500" />
            </div>
            <p className="text-3xl font-bold text-gray-900">{((stats.avg_confidence || 0) * 100).toFixed(1)}%</p>
            <p className="text-sm text-gray-500 mt-1">{stats.high_confidence_count} signals ≥85%</p>
          </div>

          {/* Today's Signals */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-gray-600">Today's Signals</h3>
              <AlertTriangle className="w-5 h-5 text-orange-500" />
            </div>
            <p className="text-3xl font-bold text-gray-900">{stats.signals_today}</p>
            <p className="text-sm text-gray-500 mt-1">New opportunities</p>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <div className="flex items-center gap-4 flex-wrap">
          <div className="flex items-center gap-2">
            <Filter className="w-5 h-5 text-gray-500" />
            <span className="text-sm font-medium text-gray-700">Filters:</span>
          </div>

          {/* Signal Type */}
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="ALL">All Types</option>
            <option value="PRIMARY">PRIMARY</option>
            <option value="HIDDEN">HIDDEN</option>
            <option value="LOSER">LOSER</option>
          </select>

          {/* Min Confidence */}
          <div className="flex items-center gap-2">
            <label className="text-sm text-gray-600">Min Confidence:</label>
            <select
              value={filterMinConfidence}
              onChange={(e) => setFilterMinConfidence(Number(e.target.value))}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="0">Any</option>
              <option value="0.7">≥70%</option>
              <option value="0.85">≥85%</option>
              <option value="0.9">≥90%</option>
            </select>
          </div>

          {/* Ticker Search */}
          <input
            type="text"
            placeholder="Search ticker..."
            value={searchTicker}
            onChange={(e) => setSearchTicker(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />

          {/* Results Count */}
          <span className="ml-auto text-sm text-gray-600">
            {filteredSignals.length} signal{filteredSignals.length !== 1 ? 's' : ''}
          </span>
        </div>
      </div>

      {/* Signals List */}
      <div className="space-y-4">
        {filteredSignals.length === 0 ? (
          <div className="bg-white rounded-lg shadow p-12 text-center">
            <AlertTriangle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600">No signals found matching your filters</p>
          </div>
        ) : (
          filteredSignals.map((signal) => (
            <div
              key={signal.id}
              className="bg-white rounded-lg shadow hover:shadow-lg transition p-6"
            >
              <div className="flex items-start justify-between">
                {/* Left: Signal Info */}
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-3">
                    {getSignalTypeBadge(signal.signal_type)}
                    <span className="text-2xl font-bold text-gray-900">{signal.ticker}</span>
                    {getActionBadge(signal.action)}
                    {signal.alert_sent && (
                      <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs font-medium">
                        Alert Sent
                      </span>
                    )}
                  </div>

                  {/* Theme */}
                  {signal.analysis_theme && (
                    <p className="text-sm font-medium text-gray-700 mb-2">
                      📊 {signal.analysis_theme}
                    </p>
                  )}

                  {/* Reasoning */}
                  <p className="text-gray-600 mb-3">{signal.reasoning}</p>

                  {/* News */}
                  {signal.news_title && (
                    <div className="flex items-center gap-2 text-sm text-gray-500">
                      <span className="font-medium">{signal.news_source}</span>
                      <span>•</span>
                      <span>{signal.news_title}</span>
                    </div>
                  )}

                  {/* Actions */}
                  <div className="flex items-center gap-2 mt-4">
                    <button
                      onClick={() => openExecuteModal(signal)}
                      className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors ${signal.action === 'BUY'
                        ? 'bg-green-500 hover:bg-green-600 text-white'
                        : 'bg-red-500 hover:bg-red-600 text-white'
                        }`}
                    >
                      <Play className="w-4 h-4" />
                      Execute {signal.action}
                    </button>
                    <Link
                      to={`/trading/signal/${signal.id}`}
                      className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                    >
                      View Details
                    </Link>
                  </div>
                </div>

                {/* Right: Confidence & Time */}
                <div className="ml-6 w-64">
                  <div className="mb-3">
                    <label className="text-xs text-gray-500 mb-1 block">Confidence</label>
                    <ConfidenceBar confidence={signal.confidence} />
                  </div>

                  <div className="text-sm text-gray-500">
                    <p>{new Date(signal.created_at).toLocaleDateString()}</p>
                    <p>{new Date(signal.created_at).toLocaleTimeString()}</p>
                  </div>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Execute Trade Modal */}
      <ExecuteTradeModal
        signal={selectedSignal}
        isOpen={isExecuteModalOpen}
        onClose={closeExecuteModal}
        onExecute={handleExecuteTrade}
      />
    </div>
  );
}

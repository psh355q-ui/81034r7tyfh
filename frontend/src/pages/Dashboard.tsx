/**
 * Dashboard Page
 *
 * Main dashboard showing portfolio overview, positions, and performance
 */

/**
 * Dashboard.tsx - 메인 대시보드 페이지
 * 
 * 📊 Data Sources:
 *   - API: GET /api/portfolio (포트폴리오 요약)
 *   - API: GET /api/signals (최근 트레이딩 시그널)
 *   - API: GET /api/performance (성과 지표)
 *   - State: portfolio, signals, loading
 * 
 * 🔗 Dependencies:
 *   - react: useState, useEffect
 *   - recharts: LineChart, BarChart, PieChart
 *   - lucide-react: 아이콘 (TrendingUp, DollarSign, etc.)
 * 
 * 📤 Components Used:
 *   - Card: 섹션별 카드 레이아웃
 *   - LoadingSpinner: 로딩 상태
 *   - PortfolioPerformanceChart: 성과 차트
 *   - SectorHeatmap: 섹터별 히트맵
 *   - SignalsList: 시그널 목록
 * 
 * 🔄 Used By:
 *   - App.tsx (route: /)
 * 
 * 📝 Notes:
 *   - 30초마다 자동 새로고침
 *   - 4개 주요 섹션: 성과/실시간/할당/리스크
 *   - 모바일 반응형 그리드 레이아웃
 */

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { TrendingUp, TrendingDown, DollarSign, Activity, PieChart, Zap, Layers, RefreshCw } from 'lucide-react';
import { getPortfolio } from '../services/api';
import { Card } from '../components/common/Card';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import {
  PortfolioPerformanceChart,
  RealTimePriceChart,
  SectorHeatmap,
  RiskMatrix
} from '../components/Analysis/AdvancedCharts';
import { InteractivePortfolio } from '../components/Portfolio/InteractivePortfolio';
import GlobalMacroPanel from '../components/GlobalMacroPanel';

type ChartTab = 'performance' | 'realtime' | 'sectors' | 'risk' | 'rebalance' | 'macro';

export const Dashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<ChartTab>('performance');
  const [selectedTicker, setSelectedTicker] = useState<string>('AAPL'); // Default ticker

  // Fetch portfolio data
  const {
    data: portfolio,
    isLoading: portfolioLoading,
    error: portfolioError,
  } = useQuery({
    queryKey: ['portfolio'],
    queryFn: getPortfolio,
    refetchInterval: 10000, // Refresh every 10 seconds
  });

  if (portfolioLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-screen gap-4">
        <LoadingSpinner size="lg" />
        <p className="text-gray-500 font-medium">Loading portfolio data...</p>
      </div>
    );
  }

  if (portfolioError) {
    return (
      <div className="p-6">
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          Error loading portfolio data. Please check if backend is running.
        </div>
      </div>
    );
  }

  const renderChart = () => {
    switch (activeTab) {
      case 'performance':
        return <PortfolioPerformanceChart />;
      case 'realtime':
        return (
          <div className="space-y-4">
            <div className="flex justify-end">
              <select
                value={selectedTicker}
                onChange={(e) => setSelectedTicker(e.target.value)}
                className="block w-32 rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-2 border"
              >
                {portfolio?.positions.map(p => (
                  <option key={p.ticker} value={p.ticker}>{p.ticker}</option>
                ))}
                {!portfolio?.positions.find(p => p.ticker === 'AAPL') && <option value="AAPL">AAPL</option>}
                {!portfolio?.positions.find(p => p.ticker === 'TSLA') && <option value="TSLA">TSLA</option>}
              </select>
            </div>
            <RealTimePriceChart ticker={selectedTicker} />
          </div>
        );
      case 'sectors':
        return <SectorHeatmap />;
      case 'risk':
        return <RiskMatrix />;
      case 'rebalance':
        return <InteractivePortfolio />;

      default:
        return <PortfolioPerformanceChart />;
    }
  };

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600 mt-1">Portfolio overview and performance</p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Total Value */}
        <Card className="hover:shadow-lg transition-shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Value</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">
                ${(portfolio?.total_value ?? 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </p>
              <p className={`text-sm mt-1 flex items-center ${(portfolio?.total_return_pct ?? 0) >= 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                {(portfolio?.total_return_pct ?? 0) >= 0 ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
                <span className="ml-1">
                  {(portfolio?.total_return_pct ?? 0) >= 0 ? '+' : ''}
                  {(portfolio?.total_return_pct ?? 0).toFixed(2)}%
                </span>
              </p>
            </div>
            <div className="p-3 bg-blue-100 rounded-full">
              <DollarSign className="text-blue-600" size={24} />
            </div>
          </div>
        </Card>

        {/* Daily P&L */}
        <Card className="hover:shadow-lg transition-shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Daily P&L</p>
              <p className={`text-2xl font-bold mt-1 ${(portfolio?.daily_pnl ?? 0) >= 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                {(portfolio?.daily_pnl ?? 0) >= 0 ? '+' : ''}
                ${(portfolio?.daily_pnl ?? 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </p>
              <p className="text-sm text-gray-600 mt-1">
                {(portfolio?.daily_return_pct ?? 0).toFixed(2)}% today
              </p>
            </div>
            <div className={`p-3 rounded-full ${(portfolio?.daily_pnl ?? 0) >= 0 ? 'bg-green-100' : 'bg-red-100'
              }`}>
              <Activity className={(portfolio?.daily_pnl ?? 0) >= 0 ? 'text-green-600' : 'text-red-600'} size={24} />
            </div>
          </div>
        </Card>

        {/* Positions */}
        <Card className="hover:shadow-lg transition-shadow">
          <div>
            <p className="text-sm font-medium text-gray-600">Positions</p>
            <p className="text-2xl font-bold text-gray-900 mt-1">
              {portfolio?.positions.length ?? 0}
            </p>
            <p className="text-sm text-gray-600 mt-1">
              Active positions
            </p>
          </div>
        </Card>

        {/* Cash */}
        <Card className="hover:shadow-lg transition-shadow">
          <div>
            <p className="text-sm font-medium text-gray-600">Available Cash</p>
            <p className="text-2xl font-bold text-gray-900 mt-1">
              ${(portfolio?.cash ?? 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </p>
            <p className="text-sm text-gray-600 mt-1">
              {((portfolio?.cash ?? 0) / (portfolio?.total_value ?? 1) * 100).toFixed(1)}% of portfolio
            </p>
          </div>
        </Card>
      </div>

      {/* Advanced Analytics Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-3">
          <Card>
            <div className="flex items-center justify-between mb-6 border-b pb-4">
              <h2 className="text-xl font-semibold text-gray-800">Portfolio Analytics</h2>
              <div className="flex space-x-2">
                <button
                  onClick={() => setActiveTab('performance')}
                  className={`px-4 py-2 rounded-md text-sm font-medium transition-colors flex items-center gap-2 ${activeTab === 'performance'
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-600 hover:bg-gray-100'
                    }`}
                >
                  <TrendingUp size={16} />
                  Performance
                </button>
                <button
                  onClick={() => setActiveTab('realtime')}
                  className={`px-4 py-2 rounded-md text-sm font-medium transition-colors flex items-center gap-2 ${activeTab === 'realtime'
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-600 hover:bg-gray-100'
                    }`}
                >
                  <Zap size={16} />
                  Real-time
                </button>
                <button
                  onClick={() => setActiveTab('sectors')}
                  className={`px-4 py-2 rounded-md text-sm font-medium transition-colors flex items-center gap-2 ${activeTab === 'sectors'
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-600 hover:bg-gray-100'
                    }`}
                >
                  <PieChart size={16} />
                  Allocation
                </button>
                <button
                  onClick={() => setActiveTab('risk')}
                  className={`px-4 py-2 rounded-md text-sm font-medium transition-colors flex items-center gap-2 ${activeTab === 'risk'
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-600 hover:bg-gray-100'
                    }`}
                >
                  <Layers size={16} />
                  Risk Analysis
                </button>
                <button
                  onClick={() => setActiveTab('rebalance')}
                  className={`px-4 py-2 rounded-md text-sm font-medium transition-colors flex items-center gap-2 ${activeTab === 'rebalance'
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-600 hover:bg-gray-100'
                    }`}
                >
                  Rebalance
                </button>
              </div>
            </div>

            <div className="min-h-[320px]">
              {renderChart()}
            </div>
          </Card>
        </div>
      </div >

      {/* Positions Table */}
      < Card >
        <h2 className="text-xl font-semibold mb-4">Current Positions</h2>
        {
          portfolio?.positions && portfolio.positions.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Ticker
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Shares
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Avg Price
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Current
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Value
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      P&L
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {portfolio.positions.map((position, index) => (
                    <tr key={`${position.ticker}-${index}`} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="font-semibold text-blue-600">{position.ticker}</span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {position.quantity}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        ${(position.entry_price || 0).toFixed(2)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        ${(position.current_price || 0).toFixed(2)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        ${(position.market_value || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className={`text-sm font-medium ${position.unrealized_pnl_pct >= 0 ? 'text-green-600' : 'text-red-600'
                          }`}>
                          {position.unrealized_pnl_pct >= 0 ? '+' : ''}
                          ${(position.unrealized_pnl || 0).toFixed(2)}
                          <span className="text-xs ml-1">
                            ({position.unrealized_pnl_pct >= 0 ? '+' : ''}{(position.unrealized_pnl_pct || 0).toFixed(2)}%)
                          </span>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              No positions yet. Start trading to see your portfolio here.
            </div>
          )
        }
      </Card >

      {/* Recent Trades */}
      {
        portfolio?.recent_trades && portfolio.recent_trades.length > 0 && (
          <Card>
            <h2 className="text-xl font-semibold mb-4">Recent Trades</h2>
            <div className="space-y-3">
              {portfolio.recent_trades.slice(0, 5).map((trade) => (
                <div key={trade.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center space-x-4">
                    <span className={`px-2 py-1 text-xs font-semibold rounded ${trade.action === 'BUY' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                      }`}>
                      {trade.action}
                    </span>
                    <span className="font-semibold text-gray-900">{trade.ticker}</span>
                    <span className="text-sm text-gray-600">
                      {trade.quantity} @ ${(trade.price || 0).toFixed(2)}
                    </span>
                  </div>
                  <div className="text-sm text-gray-600">
                    {new Date(trade.timestamp).toLocaleTimeString()}
                  </div>
                </div>
              ))}
            </div>
          </Card>
        )
      }

      {/* Global Macro Section */}
      <Card>
        <GlobalMacroPanel />
      </Card>
    </div >
  );
};

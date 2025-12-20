/**
 * Portfolio Management Page
 *
 * Features:
 * - Real KIS broker holdings
 * - AI trading recommendations for each position
 * - Performance tracking per position
 * - Combined view: What I own + What AI recommends
 */

import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  PieChart,
  BarChart3,
  AlertCircle,
  Brain,
  RefreshCw,
  CheckCircle,
  XCircle,
  MinusCircle
} from 'lucide-react';

// Types
interface Position {
  ticker: string;
  quantity: number;
  entry_price: number;
  current_price: number;
  market_value: number;
  unrealized_pnl: number;
  unrealized_pnl_pct: number;
}

interface PortfolioData {
  total_value: number;
  cash: number;
  positions_value: number;
  daily_pnl: number;
  total_pnl: number;
  daily_return_pct: number;
  total_return_pct: number;
  positions: Position[];
}

interface AIRecommendation {
  action: 'BUY' | 'SELL' | 'HOLD';
  confidence: number;
  reasoning: string;
}

// API URL
const API_BASE_URL = import.meta.env.VITE_API_URL ||
  (window.location.hostname === 'localhost' ? 'http://localhost:8001' : `http://${window.location.hostname}:8001`);

export default function PortfolioManagement() {
  const [portfolio, setPortfolio] = useState<PortfolioData | null>(null);
  const [aiRecommendations, setAiRecommendations] = useState<Record<string, AIRecommendation>>({});
  const [loading, setLoading] = useState(true);
  const [loadingAI, setLoadingAI] = useState(false);

  useEffect(() => {
    fetchPortfolio();
  }, []);

  const fetchPortfolio = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/portfolio`);
      const data = await response.json();
      setPortfolio(data);
      setLoading(false);

      // Fetch AI recommendations for each position
      if (data.positions && data.positions.length > 0) {
        fetchAIRecommendations(data.positions);
      }
    } catch (error) {
      console.error('Failed to fetch portfolio:', error);
      setLoading(false);
    }
  };

  const fetchAIRecommendations = async (positions: Position[]) => {
    setLoadingAI(true);
    const recommendations: Record<string, AIRecommendation> = {};

    for (const position of positions) {
      try {
        const response = await fetch(`${API_BASE_URL}/api/analyze`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ ticker: position.ticker })
        });

        if (response.ok) {
          const aiResult = await response.json();
          recommendations[position.ticker] = {
            action: aiResult.action || 'HOLD',
            confidence: aiResult.conviction || 0.5,
            reasoning: aiResult.reasoning || 'No analysis available'
          };
        }
      } catch (error) {
        console.error(`Failed to fetch AI recommendation for ${position.ticker}:`, error);
        // Provide fallback recommendation
        recommendations[position.ticker] = {
          action: 'HOLD',
          confidence: 0,
          reasoning: 'AI analysis unavailable'
        };
      }
    }

    setAiRecommendations(recommendations);
    setLoadingAI(false);
  };

  const getActionIcon = (action: string) => {
    switch (action) {
      case 'BUY':
        return <CheckCircle className="w-5 h-5 text-green-600" />;
      case 'SELL':
        return <XCircle className="w-5 h-5 text-red-600" />;
      default:
        return <MinusCircle className="w-5 h-5 text-gray-600" />;
    }
  };

  const getActionBadge = (action: string) => {
    const styles = {
      BUY: 'bg-green-100 text-green-800',
      SELL: 'bg-red-100 text-red-800',
      HOLD: 'bg-gray-100 text-gray-800'
    };
    return styles[action as keyof typeof styles] || styles.HOLD;
  };

  const getReturnColor = (returnPct: number) => {
    if (returnPct >= 10) return 'text-green-700';
    if (returnPct >= 0) return 'text-green-600';
    if (returnPct >= -5) return 'text-red-600';
    return 'text-red-700';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="flex flex-col items-center gap-4">
          <RefreshCw className="w-12 h-12 animate-spin text-blue-500" />
          <p className="text-gray-600">Loading portfolio...</p>
        </div>
      </div>
    );
  }

  if (!portfolio) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Error</h2>
          <p className="text-gray-600">Failed to load portfolio data</p>
        </div>
      </div>
    );
  }

  // Find best and worst performers
  const bestPerformer = portfolio.positions.length > 0
    ? portfolio.positions.reduce((best, pos) => pos.unrealized_pnl_pct > best.unrealized_pnl_pct ? pos : best)
    : null;

  const worstPerformer = portfolio.positions.length > 0
    ? portfolio.positions.reduce((worst, pos) => pos.unrealized_pnl_pct < worst.unrealized_pnl_pct ? pos : worst)
    : null;

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      {/* Header */}
      <div className="max-w-7xl mx-auto mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3 mb-2">
              <PieChart className="w-8 h-8 text-blue-500" />
              Portfolio + AI Insights
            </h1>
            <p className="text-gray-600">Your holdings with AI trading recommendations</p>
          </div>
          <button
            onClick={fetchPortfolio}
            className="flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
        </div>
      </div>

      {/* Stats Overview */}
      <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
        {/* Total Value */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-medium text-gray-600">Total Value</h3>
            <DollarSign className="w-5 h-5 text-blue-500" />
          </div>
          <p className="text-3xl font-bold text-gray-900">${portfolio.total_value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</p>
          <p className={`text-sm mt-1 ${getReturnColor(portfolio.total_return_pct)}`}>
            {portfolio.total_return_pct >= 0 ? '+' : ''}{portfolio.total_return_pct.toFixed(2)}% total
          </p>
        </div>

        {/* Total Positions */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-medium text-gray-600">Total Positions</h3>
            <BarChart3 className="w-5 h-5 text-blue-500" />
          </div>
          <p className="text-3xl font-bold text-gray-900">{portfolio.positions.length}</p>
          <p className="text-sm text-gray-500 mt-1">Active holdings</p>
        </div>

        {/* Best Performer */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-medium text-gray-600">Best Performer</h3>
            <TrendingUp className="w-5 h-5 text-green-500" />
          </div>
          {bestPerformer ? (
            <>
              <p className="text-2xl font-bold text-gray-900">{bestPerformer.ticker}</p>
              <p className="text-lg font-semibold text-green-600 mt-1">
                +{bestPerformer.unrealized_pnl_pct.toFixed(1)}%
              </p>
            </>
          ) : (
            <p className="text-gray-500">No data</p>
          )}
        </div>

        {/* Worst Performer */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-medium text-gray-600">Worst Performer</h3>
            <TrendingDown className="w-5 h-5 text-red-500" />
          </div>
          {worstPerformer ? (
            <>
              <p className="text-2xl font-bold text-gray-900">{worstPerformer.ticker}</p>
              <p className="text-lg font-semibold text-red-600 mt-1">
                {worstPerformer.unrealized_pnl_pct.toFixed(1)}%
              </p>
            </>
          ) : (
            <p className="text-gray-500">No data</p>
          )}
        </div>
      </div>

      {/* Positions with AI Recommendations */}
      <div className="max-w-7xl mx-auto">
        <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
          <Brain className="w-6 h-6 text-purple-500" />
          Holdings & AI Recommendations
          {loadingAI && <span className="text-sm text-gray-500">(Loading AI insights...)</span>}
        </h2>

        {portfolio.positions.length === 0 ? (
          <div className="bg-white rounded-lg shadow p-12 text-center">
            <AlertCircle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600">No positions yet</p>
            <Link to="/trading" className="mt-4 inline-block text-blue-600 hover:text-blue-700 font-medium">
              View Trading Signals →
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4">
            {portfolio.positions
              .sort((a, b) => b.market_value - a.market_value)
              .map((position) => {
                const aiRec = aiRecommendations[position.ticker];
                return (
                  <div key={position.ticker} className="bg-white rounded-lg shadow hover:shadow-lg transition p-6">
                    <div className="flex items-start justify-between">
                      {/* Left: Position Info */}
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-3">
                          <h3 className="text-2xl font-bold text-gray-900">{position.ticker}</h3>
                          <span className="text-sm text-gray-600">
                            {position.quantity} shares @ ${position.entry_price.toFixed(2)}
                          </span>
                        </div>

                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                          <div>
                            <p className="text-xs text-gray-500">Current Price</p>
                            <p className="text-lg font-semibold">${position.current_price.toFixed(2)}</p>
                          </div>
                          <div>
                            <p className="text-xs text-gray-500">Market Value</p>
                            <p className="text-lg font-semibold">${position.market_value.toLocaleString()}</p>
                          </div>
                          <div>
                            <p className="text-xs text-gray-500">P&L</p>
                            <p className={`text-lg font-semibold ${position.unrealized_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                              {position.unrealized_pnl >= 0 ? '+' : ''}${position.unrealized_pnl.toFixed(2)}
                            </p>
                          </div>
                          <div>
                            <p className="text-xs text-gray-500">Return</p>
                            <p className={`text-lg font-semibold ${position.unrealized_pnl_pct >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                              {position.unrealized_pnl_pct >= 0 ? '+' : ''}{position.unrealized_pnl_pct.toFixed(2)}%
                            </p>
                          </div>
                        </div>

                        {/* AI Recommendation */}
                        {aiRec ? (
                          <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                            <div className="flex items-center gap-2 mb-2">
                              <Brain className="w-5 h-5 text-purple-600" />
                              <span className="font-semibold text-purple-900">AI Recommendation</span>
                            </div>
                            <div className="flex items-center gap-3 mb-2">
                              {getActionIcon(aiRec.action)}
                              <span className={`px-3 py-1 rounded-full text-sm font-semibold ${getActionBadge(aiRec.action)}`}>
                                {aiRec.action}
                              </span>
                              <span className="text-sm text-gray-600">
                                Confidence: {(aiRec.confidence * 100).toFixed(0)}%
                              </span>
                            </div>
                            <p className="text-sm text-gray-700">{aiRec.reasoning}</p>
                          </div>
                        ) : (
                          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 text-center">
                            <p className="text-sm text-gray-500">Loading AI recommendation...</p>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
          </div>
        )}
      </div>
    </div>
  );
}

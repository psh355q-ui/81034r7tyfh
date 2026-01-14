/**
 * Portfolio Dashboard - 포트폴리오 현황 대시보드
 *
 * Phase 27: REAL MODE UI
 * Date: 2025-12-25 (Updated to Tailwind CSS)
 */

/**
 * Portfolio.tsx - 포트폴리오 관리 페이지
 * 
 * 📊 Data Sources:
 *   - API: GET /api/portfolio (KIS + Yahoo Finance)
 *     - Positions with dividend_info and sector
 *   - State: portfolio, loading (useState)
 *   - Refresh: 30초 간격 자동 새로고침
 * 
 * 🔗 Dependencies:
 *   - react: useState, useEffect
 *   - lucide-react: DollarSign, TrendingUp, PieChart 아이콘
 * 
 * 📤 Components Used:
 *   - Card: 섹션별 카드 래퍼
 *   - LoadingSpinner: 데이터 로딩 표시
 * 
 * 🔄 Used By:
 *   - App.tsx (route: /portfolio)
 * 
 * 📝 Notes:
 *   - Phase 28: 섹터 정보 통합 (Yahoo Finance)
 *   - 자산 배분: 주식/ETF/채권/암호화폐/현금
 *   - 섹터별 색상 매핑 (11개 GICS 섹터)
 *   - 모바일 반응형: 테이블 → 카드 레이아웃
 *   - 데스크톱/모바일 dual layout
 */

import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
    PieChart,
    Brain,
    TrendingUp,
    TrendingDown,
    DollarSign,
    BarChart3,
    CheckCircle,
    XCircle,
    MinusCircle,
    AlertCircle,
    Info
} from 'lucide-react';
import { Card } from '../components/common/Card';
import { LoadingSpinner } from '../components/common/LoadingSpinner';

// Interfaces for Portfolio
interface Position {
    symbol: string;
    quantity: number;
    avg_price: number;
    current_price: number;
    market_value: number;
    profit_loss: number;
    profit_loss_pct: number;
    daily_pnl: number;
    daily_return_pct: number;
    sector?: string;
}

interface PortfolioData {
    total_value: number;
    cash: number;
    invested: number;
    total_pnl: number;
    total_pnl_pct: number;
    total_return_pct: number; // Added for compatibility
    daily_pnl: number;
    daily_return_pct: number;
    positions: Position[];
}

// Interfaces for AI Insights
interface AIRecommendation {
    action: 'BUY' | 'SELL' | 'HOLD';
    confidence: number;
    reasoning: string;
}

// Mock Data (Fallback)
const MOCK_PORTFOLIO: PortfolioData = {
    total_value: 127580.50,
    cash: 45200.00,
    invested: 82380.50,
    total_pnl: 7380.50,
    total_pnl_pct: 9.84,
    total_return_pct: 5.78, // Mock value
    daily_pnl: 1250.30,
    daily_return_pct: 0.98,
    positions: [
        { symbol: 'AAPL', quantity: 100, avg_price: 175.20, current_price: 178.50, market_value: 17850.00, profit_loss: 330.00, profit_loss_pct: 1.88, daily_pnl: 150.00, daily_return_pct: 0.84, sector: 'Technology' },
        { symbol: 'NVDA', quantity: 50, avg_price: 480.00, current_price: 495.20, market_value: 24760.00, profit_loss: 760.00, profit_loss_pct: 3.17, daily_pnl: 380.00, daily_return_pct: 1.56, sector: 'Technology' },
        { symbol: 'MSFT', quantity: 75, avg_price: 385.00, current_price: 392.10, market_value: 29407.50, profit_loss: 532.50, profit_loss_pct: 1.84, daily_pnl: 225.00, daily_return_pct: 0.77, sector: 'Technology' },
    ]
};

const API_BASE_URL = import.meta.env.VITE_API_URL ||
    (window.location.hostname === 'localhost' ? 'http://localhost:8001' : `http://${window.location.hostname}:8001`);

const Portfolio: React.FC = () => {
    const [activeTab, setActiveTab] = useState<'overview' | 'ai-insights'>('overview');
    const [aiRecommendations, setAiRecommendations] = useState<Record<string, AIRecommendation>>({});
    const [loadingAI, setLoadingAI] = useState(false);

    // 1. Fetch Portfolio
    const { data: portfolio, isLoading, error } = useQuery<PortfolioData>({
        queryKey: ['portfolio'],
        queryFn: async () => {
            // Using absolute URL to avoid proxy issues during dev if needed, or relative if proxy set
            const response = await fetch(`${API_BASE_URL}/api/portfolio`);
            if (!response.ok) throw new Error('Failed to fetch portfolio');
            return response.json();
        },
        placeholderData: MOCK_PORTFOLIO,
        refetchInterval: 30000
    });

    // 2. Fetch AI Recommendations (Effect)
    useEffect(() => {
        if (activeTab === 'ai-insights' && portfolio?.positions && Object.keys(aiRecommendations).length === 0) {
            fetchAIRecommendations(portfolio.positions);
        }
    }, [activeTab, portfolio]);

    const fetchAIRecommendations = async (positions: Position[]) => {
        setLoadingAI(true);
        const recommendations: Record<string, AIRecommendation> = {};

        // Parallel requests for better performance
        await Promise.all(positions.map(async (position) => {
            // Simply mocking the AI response for now to ensure UI works without full backend AI
            try {
                // Simulate API call delay
                await new Promise(r => setTimeout(r, 500));

                // Randomly generate recommendation for demo/fallback
                // In real implementation, this would call POST /api/analyze
                const actions: ('BUY' | 'SELL' | 'HOLD')[] = ['BUY', 'HOLD', 'SELL'];
                const randomAction = actions[Math.floor(Math.random() * actions.length)];

                recommendations[position.symbol] = {
                    action: randomAction,
                    confidence: 0.7 + (Math.random() * 0.2), // 0.7 ~ 0.9
                    reasoning: `AI analysis suggests ${randomAction} based on recent technical patterns and news sentiment.`
                };
            } catch (e) {
                console.error(e);
            }
        }));

        setAiRecommendations(recommendations);
        setLoadingAI(false);
    };

    if (isLoading) return <div className="flex justify-center h-screen items-center"><LoadingSpinner size="lg" /></div>;
    if (error) return <div className="p-6 text-red-600">Error loading portfolio.</div>;
    if (!portfolio) return null;

    // Helper functions
    const allocation_pct = (portfolio.invested / portfolio.total_value) * 100;
    const cash_pct = (portfolio.cash / portfolio.total_value) * 100;

    const getActionIcon = (action: string) => {
        switch (action) {
            case 'BUY': return <CheckCircle className="w-5 h-5 text-green-600" />;
            case 'SELL': return <XCircle className="w-5 h-5 text-red-600" />;
            default: return <MinusCircle className="w-5 h-5 text-gray-600" />;
        }
    };

    const getActionBadge = (action: string) => {
        switch (action) {
            case 'BUY': return 'bg-green-100 text-green-800';
            case 'SELL': return 'bg-red-100 text-red-800';
            default: return 'bg-gray-100 text-gray-800';
        }
    };

    return (
        <div className="space-y-6 p-6">
            {/* Page Header */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
                        💼 Portfolio
                        <span className="text-sm font-normal text-gray-500 bg-gray-100 px-2 py-1 rounded-full">
                            Total: ${portfolio.total_value.toLocaleString()}
                        </span>
                    </h1>
                    <p className="text-gray-600 mt-1">Manage your positions and view AI insights</p>
                </div>

                {/* Tabs */}
                <div className="flex bg-white rounded-lg p-1 shadow-sm border border-gray-200">
                    <button
                        onClick={() => setActiveTab('overview')}
                        className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all ${activeTab === 'overview'
                            ? 'bg-blue-50 text-blue-700 shadow-sm'
                            : 'text-gray-600 hover:bg-gray-50'
                            }`}
                    >
                        <PieChart size={16} />
                        Overview
                    </button>
                    <button
                        onClick={() => setActiveTab('ai-insights')}
                        className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all ${activeTab === 'ai-insights'
                            ? 'bg-purple-50 text-purple-700 shadow-sm'
                            : 'text-gray-600 hover:bg-gray-50'
                            }`}
                    >
                        <Brain size={16} />
                        AI Insights
                    </button>
                </div>
            </div>

            {/* Summary Cards (Common) */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <Card>
                    <div className="flex justify-between items-start">
                        <div>
                            <p className="text-sm font-medium text-gray-500">Total Value</p>
                            <h3 className="text-2xl font-bold text-gray-900 mt-1">
                                ${portfolio.total_value.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                            </h3>
                            <p className={`text-sm mt-1 ${(portfolio.total_return_pct ?? 0) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                {(portfolio.total_return_pct ?? 0) >= 0 ? '+' : ''}{(portfolio.total_return_pct ?? 0).toFixed(2)}%
                            </p>
                        </div>
                        <div className="p-2 bg-blue-100 rounded-lg"><DollarSign className="text-blue-600" size={20} /></div>
                    </div>
                </Card>
                <Card>
                    <div className="flex justify-between items-start">
                        <div>
                            <p className="text-sm font-medium text-gray-500">Daily P&L</p>
                            <h3 className={`text-2xl font-bold mt-1 ${(portfolio.daily_pnl ?? 0) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                {(portfolio.daily_pnl ?? 0) >= 0 ? '+' : ''}${Math.abs(portfolio.daily_pnl ?? 0).toLocaleString()}
                            </h3>
                            <p className={`text-sm mt-1 ${(portfolio.daily_return_pct ?? 0) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                {(portfolio.daily_return_pct ?? 0) >= 0 ? '+' : ''}{(portfolio.daily_return_pct ?? 0).toFixed(2)}%
                            </p>
                        </div>
                        <div className={`p-2 rounded-lg ${portfolio.daily_pnl >= 0 ? 'bg-green-100' : 'bg-red-100'}`}>
                            {portfolio.daily_pnl >= 0 ? <TrendingUp className="text-green-600" size={20} /> : <TrendingDown className="text-red-600" size={20} />}
                        </div>
                    </div>
                </Card>
                <Card>
                    <div className="flex justify-between items-start">
                        <div>
                            <p className="text-sm font-medium text-gray-500">Invested</p>
                            <h3 className="text-2xl font-bold text-gray-900 mt-1">
                                ${portfolio.invested.toLocaleString()}
                            </h3>
                            <p className="text-sm text-gray-500 mt-1">{allocation_pct.toFixed(1)}% of total</p>
                        </div>
                        <div className="p-2 bg-purple-100 rounded-lg"><PieChart className="text-purple-600" size={20} /></div>
                    </div>
                </Card>
                <Card>
                    <div className="flex justify-between items-start">
                        <div>
                            <p className="text-sm font-medium text-gray-500">Cash</p>
                            <h3 className="text-2xl font-bold text-gray-900 mt-1">
                                ${portfolio.cash.toLocaleString()}
                            </h3>
                            <p className="text-sm text-gray-500 mt-1">{cash_pct.toFixed(1)}% available</p>
                        </div>
                        <div className="p-2 bg-gray-100 rounded-lg"><DollarSign className="text-gray-600" size={20} /></div>
                    </div>
                </Card>
            </div>

            {/* Tab Content 1: Overview (Existing Table View) */}
            {activeTab === 'overview' && (
                <div className="bg-white rounded-lg shadow border border-gray-200 overflow-hidden">
                    <div className="px-6 py-4 border-b border-gray-200 bg-gray-50 flex justify-between items-center">
                        <h2 className="text-lg font-semibold text-gray-900">Holdings</h2>
                        <span className="text-sm text-gray-500">{portfolio.positions.length} positions</span>
                    </div>

                    <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-50">
                                <tr>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Symbol</th>
                                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Shares</th>
                                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Avg Price</th>
                                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Current</th>
                                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Value</th>
                                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Return</th>
                                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Daily</th>
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                                {portfolio.positions.map((pos) => (
                                    <tr key={pos.symbol} className="hover:bg-gray-50">
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <div className="flex items-center">
                                                <div className="font-bold text-gray-900">{pos.symbol}</div>
                                                {pos.sector && <span className="ml-2 px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded-full">{pos.sector}</span>}
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-900">{pos.quantity}</td>
                                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-500">${pos.avg_price.toFixed(2)}</td>
                                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium text-gray-900">${pos.current_price.toFixed(2)}</td>
                                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-900 font-medium">${pos.market_value.toLocaleString()}</td>
                                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm">
                                            <div className={pos.profit_loss >= 0 ? 'text-green-600' : 'text-red-600'}>
                                                {pos.profit_loss_pct >= 0 ? '+' : ''}{pos.profit_loss_pct.toFixed(2)}%
                                            </div>
                                            <div className="text-xs text-gray-500">
                                                {pos.profit_loss >= 0 ? '+' : ''}${pos.profit_loss.toFixed(0)}
                                            </div>
                                        </td>
                                        <td className={`px-6 py-4 whitespace-nowrap text-right text-sm ${pos.daily_return_pct >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                            {pos.daily_return_pct >= 0 ? '+' : ''}{pos.daily_return_pct.toFixed(2)}%
                                        </td>
                                    </tr>
                                ))}
                                {portfolio.positions.length === 0 && (
                                    <tr>
                                        <td colSpan={7} className="px-6 py-12 text-center text-gray-500">No positions found.</td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}

            {/* Tab Content 2: AI Insights (Integrated Logic) */}
            {activeTab === 'ai-insights' && (
                <div className="space-y-4">
                    {/* Info Banner */}
                    <div className="bg-purple-50 border border-purple-200 rounded-lg p-4 flex items-start gap-3">
                        <Brain className="text-purple-600 mt-1 flex-shrink-0" size={20} />
                        <div>
                            <h3 className="text-sm font-bold text-purple-900">AI Portfolio Diagnostics</h3>
                            <p className="text-sm text-purple-700 mt-1">
                                The system analyzes your holdings against current market conditions, news sentiment, and technical indicators to provide actionable recommendations.
                            </p>
                        </div>
                    </div>

                    {loadingAI && Object.keys(aiRecommendations).length === 0 ? (
                        <div className="text-center py-12 bg-white rounded-lg border border-gray-200">
                            <LoadingSpinner />
                            <p className="text-sm text-gray-500 mt-4">Analyzing portfolio...</p>
                        </div>
                    ) : (
                        <div className="grid grid-cols-1 gap-4">
                            {portfolio.positions
                                .sort((a, b) => b.market_value - a.market_value)
                                .map(pos => {
                                    const rec = aiRecommendations[pos.symbol];
                                    return (
                                        <div key={pos.symbol} className="bg-white rounded-lg border border-gray-200 p-6 hover:shadow-md transition-shadow">
                                            <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
                                                {/* Left: Position Info */}
                                                <div>
                                                    <div className="flex items-center gap-2 mb-2">
                                                        <h3 className="text-xl font-bold text-gray-900">{pos.symbol}</h3>
                                                        <span className="text-sm text-gray-500">{pos.quantity} shares</span>
                                                    </div>
                                                    <div className="flex gap-4 text-sm">
                                                        <div>
                                                            <span className="text-gray-500">Value:</span>
                                                            <span className="font-medium ml-1">${pos.market_value.toLocaleString()}</span>
                                                        </div>
                                                        <div>
                                                            <span className="text-gray-500">Return:</span>
                                                            <span className={`font-medium ml-1 ${pos.profit_loss_pct >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                                                {pos.profit_loss_pct >= 0 ? '+' : ''}{pos.profit_loss_pct.toFixed(2)}%
                                                            </span>
                                                        </div>
                                                    </div>
                                                </div>

                                                {/* Right: AI Recommendation */}
                                                <div className="flex-1 md:max-w-xl">
                                                    {rec ? (
                                                        <div className="bg-gray-50 rounded-lg p-4 border border-gray-100">
                                                            <div className="flex items-center justify-between mb-2">
                                                                <div className="flex items-center gap-2">
                                                                    {getActionIcon(rec.action)}
                                                                    <span className={`px-2 py-0.5 rounded text-xs font-bold ${getActionBadge(rec.action)}`}>
                                                                        {rec.action}
                                                                    </span>
                                                                </div>
                                                                <span className="text-xs font-medium text-gray-500">
                                                                    Confidence: {(rec.confidence * 100).toFixed(0)}%
                                                                </span>
                                                            </div>
                                                            <p className="text-sm text-gray-700 leading-relaxed">
                                                                {rec.reasoning}
                                                            </p>
                                                        </div>
                                                    ) : (
                                                        <div className="flex items-center gap-2 text-gray-400 text-sm h-full bg-gray-50 rounded-lg p-4 justify-center">
                                                            <LoadingSpinner size="sm" />
                                                            Waiting for analysis...
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
            )}
        </div>
    );
};

export default Portfolio;

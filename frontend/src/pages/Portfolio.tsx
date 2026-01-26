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
import { StockChartWidget } from '../components/Portfolio/StockChartWidget';
import { PortfolioActionCard } from '../components/Portfolio/PortfolioActionCard';
import { AIDecision } from '../services/api';

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

interface AgentOpinion {
    action: 'BUY' | 'SELL' | 'HOLD';
    confidence: number;
    reasoning: string;
    weight?: number;
    latency_seconds?: number;
}

interface AgentAnalysis {
    trader_agent?: AgentOpinion;
    risk_agent?: AgentOpinion;
    analyst_agent?: AgentOpinion;
    pm_agent?: {
        action: 'BUY' | 'SELL' | 'HOLD';
        confidence: number;
        reasoning: string;
        hard_rules_passed: string[];
        hard_rules_violations: string[];
    };
    // NEW: Portfolio action guide
    portfolio_action_guide?: PortfolioActionGuide;
}

// NEW: Portfolio Action Guide interface
interface PortfolioActionGuide {
    action: 'SELL' | 'BUY_MORE' | 'HOLD' | 'DO_NOT_BUY';
    reason: string;
    strength: 'weak' | 'moderate' | 'strong';
    confidence: number;
    position_adjustment_pct: number;
    stop_loss_pct: number;
    take_profit_pct: number;
}

// Persona modes with dynamic weights
interface PersonaConfig {
    mode: string;
    description: string;
    weights: {
        trader_mvp: number;
        risk_mvp: number;
        analyst_mvp: number;
    };
}

const PERSONA_MODES: Record<string, PersonaConfig> = {
    dividend: {
        mode: 'dividend',
        description: '배당/안정 추구: Analyst(50%) > Risk(40%) > Trader(10%)',
        weights: { trader_mvp: 0.10, risk_mvp: 0.40, analyst_mvp: 0.50 }
    },
    long_term: {
        mode: 'long_term',
        description: '가치/성장 투자: Analyst(60%) > Risk(25%) > Trader(15%)',
        weights: { trader_mvp: 0.15, risk_mvp: 0.25, analyst_mvp: 0.60 }
    },
    trading: {
        mode: 'trading',
        description: '단기 트레이딩: Trader(35%) = Analyst(35%) > Risk(30%)',
        weights: { trader_mvp: 0.35, risk_mvp: 0.35, analyst_mvp: 0.30 }
    },
    aggressive: {
        mode: 'aggressive',
        description: '공격적 투자: Trader(50%) > Risk(30%) > Analyst(20%)',
        weights: { trader_mvp: 0.50, risk_mvp: 0.30, analyst_mvp: 0.20 }
    }
};

interface NewsArticle {
    id: number;
    title: string;
    url: string;
    published_at: string;
    sentiment?: string;
}

// Empty Portfolio Data (when API fails)
const EMPTY_PORTFOLIO: PortfolioData = {
    total_value: 0,
    cash: 0,
    invested: 0,
    total_pnl: 0,
    total_pnl_pct: 0,
    total_return_pct: 0,
    daily_pnl: 0,
    daily_return_pct: 0,
    positions: []
};

// Mock Data (only for development/testing - set USE_MOCK_DATA=true in .env to enable)
const MOCK_PORTFOLIO: PortfolioData = {
    total_value: 127580.50,
    cash: 45200.00,
    invested: 82380.50,
    total_pnl: 7380.50,
    total_pnl_pct: 9.84,
    total_return_pct: 5.78,
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

// Check if mock data should be used (for development/testing only)
const USE_MOCK_DATA = import.meta.env.VITE_USE_MOCK_DATA === 'true' || false;

const Portfolio: React.FC = () => {
    const [activeTab, setActiveTab] = useState<'overview' | 'ai-insights'>('overview');
    const [personaMode, setPersonaMode] = useState<string>('trading'); // New: persona mode state
    const [aiRecommendations, setAiRecommendations] = useState<Record<string, AIRecommendation>>({});
    const [agentAnalysis, setAgentAnalysis] = useState<Record<string, AgentAnalysis>>({});
    const [analysisLogs, setAnalysisLogs] = useState<Array<{
        ticker: string;
        timestamp: string;
        duration_seconds: number;
        agents_summary: {
            trader: string;
            risk: string;
            analyst: string;
            pm: string;
        };
        news_count: number;
        persona_mode?: string; // Add persona mode to logs
        weights?: { trader_mvp: number; risk_mvp: number; analyst_mvp: number }; // Add weights to logs
    }>>([]);
    const [loadingAI, setLoadingAI] = useState(false);
    const [currentAnalysisIndex, setCurrentAnalysisIndex] = useState(0); // For batch processing
    const [batchAnalysisInProgress, setBatchAnalysisInProgress] = useState(false);
    // Track loading state for each agent of each position
    const [agentLoadingStates, setAgentLoadingStates] = useState<Record<string, {
        trader: boolean;
        risk: boolean;
        analyst: boolean;
        pm: boolean;
    }>>({});

    // 1. Fetch Portfolio
    const { data: portfolio, isLoading, error } = useQuery<PortfolioData>({
        queryKey: ['portfolio'],
        queryFn: async () => {
            // Using absolute URL to avoid proxy issues during dev if needed, or relative if proxy set
            const response = await fetch(`${API_BASE_URL}/api/portfolio`);
            if (!response.ok) throw new Error('Failed to fetch portfolio');
            return response.json();
        },
        // Use mock data only when explicitly enabled for testing
        placeholderData: USE_MOCK_DATA ? MOCK_PORTFOLIO : EMPTY_PORTFOLIO,
        refetchInterval: 30000
    });

    // 2. Fetch AI Recommendations (Effect)
    useEffect(() => {
        if (activeTab === 'ai-insights' && portfolio?.positions && Object.keys(agentAnalysis).length === 0) {
            fetchAIRecommendations(portfolio.positions);
        }
    }, [activeTab, portfolio]);

    // Re-fetch when persona mode changes (only if we already have analysis)
    useEffect(() => {
        if (activeTab === 'ai-insights' && portfolio?.positions && Object.keys(agentAnalysis).length > 0) {
            // Clear existing analysis and fetch new with updated persona mode
            setAgentAnalysis({});
            setAiRecommendations({});
            setAnalysisLogs([]);
            fetchAIRecommendations(portfolio.positions);
        }
    }, [personaMode]);

    const fetchAIRecommendations = async (positions: Position[]) => {
        setLoadingAI(true);
        setBatchAnalysisInProgress(true);

        const recommendations: Record<string, AIRecommendation> = {};
        const analyses: Record<string, AgentAnalysis> = {};
        const logs: typeof analysisLogs = [];
        const loadingStates: typeof agentLoadingStates = {};

        // Initialize loading states for all positions
        positions.forEach(pos => {
            loadingStates[pos.symbol] = {
                trader: true,
                risk: true,
                analyst: true,
                pm: true
            };
        });
        setAgentLoadingStates(loadingStates);

        // Batch processing: Analyze positions one at a time with delays
        // For large portfolios (>10 positions), process in batches with 10-minute intervals
        const BATCH_SIZE = 10;
        const BATCH_DELAY_MS = 10 * 60 * 1000; // 10 minutes between batches

        for (let i = 0; i < positions.length; i++) {
            const position = positions[i];
            setCurrentAnalysisIndex(i);

            // Check if we need to delay between batches
            if (i > 0 && i % BATCH_SIZE === 0) {
                console.log(`Batch analysis: pausing for ${BATCH_DELAY_MS / 1000 / 60} minutes before next batch...`);
                await new Promise(resolve => setTimeout(resolve, BATCH_DELAY_MS));
            }

            try {
                // Call real AI analysis API (now returns all 3+1 agents)
                const startTime = new Date();
                const response = await fetch(`${API_BASE_URL}/api/analyze`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        ticker: position.symbol,
                        context: 'existing_position', // Explicitly set Context for Portfolio Page
                        persona_mode: personaMode     // Send current persona mode
                    })
                });

                if (response.ok) {
                    const data = await response.json();
                    const endTime = new Date();
                    const duration = (endTime.getTime() - startTime.getTime()) / 1000;

                    // Extract individual agent opinions
                    const agents = data.agents_analysis || {};
                    const pm_decision = data.final_decision || {};

                    // Initialize analysis object for this position
                    analyses[position.symbol] = {};

                    // Update each agent progressively (simulating sequential loading)
                    //Trader Agent
                    if (agents.trader_agent) {
                        analyses[position.symbol].trader_agent = {
                            action: agents.trader_agent?.action || 'HOLD',
                            confidence: agents.trader_agent?.confidence || 0.5,
                            reasoning: agents.trader_agent?.reasoning || '',
                            weight: agents.trader_agent?.weight || PERSONA_MODES[personaMode]?.weights.trader_mvp || 0.35,
                            latency_seconds: agents.trader_agent?.latency_seconds || 0
                        };
                        loadingStates[position.symbol].trader = false;
                        setAgentLoadingStates({ ...loadingStates });
                        setAgentAnalysis({ ...analyses });
                        await new Promise(resolve => setTimeout(resolve, 100)); // Small delay for visual effect
                    }

                    // Analyst Agent
                    if (agents.analyst_agent) {
                        analyses[position.symbol].analyst_agent = {
                            action: agents.analyst_agent?.action || 'HOLD',
                            confidence: agents.analyst_agent?.confidence || 0.5,
                            reasoning: agents.analyst_agent?.reasoning || '',
                            weight: agents.analyst_agent?.weight || PERSONA_MODES[personaMode]?.weights.analyst_mvp || 0.35,
                            latency_seconds: agents.analyst_agent?.latency_seconds || 0
                        };
                        loadingStates[position.symbol].analyst = false;
                        setAgentLoadingStates({ ...loadingStates });
                        setAgentAnalysis({ ...analyses });
                        await new Promise(resolve => setTimeout(resolve, 100)); // Small delay for visual effect
                    }

                    // Risk Agent (usually slowest)
                    if (agents.risk_agent) {
                        analyses[position.symbol].risk_agent = {
                            action: agents.risk_agent?.action || 'HOLD',
                            confidence: agents.risk_agent?.confidence || 0.5,
                            reasoning: agents.risk_agent?.reasoning || '',
                            weight: agents.risk_agent?.weight || PERSONA_MODES[personaMode]?.weights.risk_mvp || 0.30,
                            latency_seconds: agents.risk_agent?.latency_seconds || 0
                        };
                        loadingStates[position.symbol].risk = false;
                        setAgentLoadingStates({ ...loadingStates });
                        setAgentAnalysis({ ...analyses });
                        await new Promise(resolve => setTimeout(resolve, 100)); // Small delay for visual effect
                    }

                    // PM Agent (final)
                    if (agents.pm_agent) {
                        analyses[position.symbol].pm_agent = {
                            action: agents.pm_agent?.action || 'HOLD',
                            confidence: agents.pm_agent?.confidence || 0.5,
                            reasoning: agents.pm_agent?.reasoning || '',
                            hard_rules_passed: agents.pm_agent?.hard_rules_passed || [],
                            hard_rules_violations: agents.pm_agent?.hard_rules_violations || []
                        };
                        loadingStates[position.symbol].pm = false;
                        setAgentLoadingStates({ ...loadingStates });
                        setAgentAnalysis({ ...analyses });
                    }

                    // NEW: Parse portfolio action guide
                    if (data.portfolio_action) {
                        analyses[position.symbol].portfolio_action_guide = {
                            action: data.portfolio_action,
                            reason: data.action_reason || '',
                            strength: data.action_strength || 'moderate',
                            confidence: data.conviction || 0,
                            position_adjustment_pct: data.position_adjustment_pct || 0,
                            stop_loss_pct: 0,
                            take_profit_pct: 0
                        };
                        setAgentAnalysis({ ...analyses });
                    }

                    // Store final recommendation
                    const action = data.final_decision?.action?.toUpperCase() || 'HOLD';
                    const newRecommendation = {
                        action: action as 'BUY' | 'SELL' | 'HOLD',
                        confidence: data.final_decision?.confidence || 0.5,
                        reasoning: data.final_decision?.reasoning || `${action} based on War Room analysis of ${position.symbol}`
                    };

                    // Create analysis log entry with persona mode and weights
                    const newLog = {
                        ticker: position.symbol,
                        timestamp: data.analysis_timestamp || startTime.toISOString(),
                        duration_seconds: data.analysis_duration_seconds || duration,
                        agents_summary: {
                            trader: agents.trader_agent?.action || 'HOLD',
                            risk: agents.risk_agent?.action || 'HOLD',
                            analyst: agents.analyst_agent?.action || 'HOLD',
                            pm: agents.pm_agent?.action || 'HOLD'
                        },
                        news_count: data.news_summary?.total_articles || 0,
                        persona_mode: data.persona_mode || personaMode,
                        weights: data.weights || PERSONA_MODES[personaMode]?.weights
                    };

                    // Update state for this position
                    recommendations[position.symbol] = newRecommendation;
                    logs.push(newLog);

                    // Trigger re-render with current progress
                    setAiRecommendations({ ...recommendations });
                    setAnalysisLogs([...logs]);

                } else {
                    // Fallback if API fails
                    recommendations[position.symbol] = {
                        action: 'HOLD',
                        confidence: 0.5,
                        reasoning: 'AI analysis temporarily unavailable. Please try again later.'
                    };
                    setAiRecommendations({ ...recommendations });
                }
            } catch (e) {
                console.error(`Failed to fetch AI recommendation for ${position.symbol}:`, e);
                // Fallback on error
                recommendations[position.symbol] = {
                    action: 'HOLD',
                    confidence: 0.5,
                    reasoning: 'Unable to connect to AI service. Please check your connection.'
                };
                setAiRecommendations({ ...recommendations });
            }
        }

        setLoadingAI(false);
        setBatchAnalysisInProgress(false);
        setCurrentAnalysisIndex(0);
    };

    if (isLoading) return <div className="flex justify-center h-screen items-center"><LoadingSpinner size="lg" /></div>;
    if (error) return <div className="p-6 text-red-600">Error loading portfolio.</div>;
    if (!portfolio) return null;

    // Helper functions (with null safety)
    const allocation_pct = ((portfolio.invested ?? 0) / (portfolio.total_value || 1)) * 100;
    const cash_pct = ((portfolio.cash ?? 0) / (portfolio.total_value || 1)) * 100;

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

    const getAgentBadge = (action: string) => {
        switch (action) {
            case 'BUY': return 'bg-green-100 text-green-800';
            case 'SELL': return 'bg-red-100 text-red-800';
            default: return 'bg-gray-100 text-gray-800';
        }
    };

    const getAgentColor = (action: string) => {
        switch (action) {
            case 'BUY': return 'text-green-600';
            case 'SELL': return 'text-red-600';
            default: return 'text-gray-600';
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
                                ${(portfolio.invested ?? 0).toLocaleString()}
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
                                ${(portfolio.cash ?? 0).toLocaleString()}
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

            {/* Tab Content 2: AI Insights (War Room 3+1 Agents) */}
            {activeTab === 'ai-insights' && (
                <div className="space-y-6">
                    {/* Info Banner with Persona Mode Selector */}
                    <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                        <div className="flex items-start gap-3 mb-3">
                            <Brain className="text-purple-600 mt-1 flex-shrink-0" size={20} />
                            <div className="flex-1">
                                <div className="flex items-center justify-between">
                                    <h3 className="text-sm font-bold text-purple-900">War Room Analysis (3+1 Agents)</h3>
                                    <select
                                        value={personaMode}
                                        onChange={(e) => setPersonaMode(e.target.value)}
                                        className="text-xs px-2 py-1 rounded border border-purple-300 bg-white text-purple-900 font-medium cursor-pointer hover:bg-purple-100"
                                    >
                                        <option value="dividend">배당/안정</option>
                                        <option value="long_term">장기투자</option>
                                        <option value="trading">트레이딩</option>
                                        <option value="aggressive">공격적</option>
                                    </select>
                                </div>
                                <p className="text-sm text-purple-700 mt-2">
                                    {PERSONA_MODES[personaMode]?.description || 'Trader(35%), Risk(30%), Analyst(35%)'}
                                </p>
                            </div>
                        </div>
                        <div className="mt-2 pt-2 border-t border-purple-200">
                            <div className="flex items-center justify-between">
                                <div className="grid grid-cols-3 gap-2 text-xs">
                                    <div className="text-center">
                                        <span className="font-bold text-blue-900">📈 Trader</span>
                                        <span className="ml-1 text-blue-700">{((PERSONA_MODES[personaMode]?.weights.trader_mvp || 0.35) * 100).toFixed(0)}%</span>
                                    </div>
                                    <div className="text-center">
                                        <span className="font-bold text-yellow-900">⚠️ Risk</span>
                                        <span className="ml-1 text-yellow-700">{((PERSONA_MODES[personaMode]?.weights.risk_mvp || 0.30) * 100).toFixed(0)}%</span>
                                    </div>
                                    <div className="text-center">
                                        <span className="font-bold text-purple-900">📰 Analyst</span>
                                        <span className="ml-1 text-purple-700">{((PERSONA_MODES[personaMode]?.weights.analyst_mvp || 0.35) * 100).toFixed(0)}%</span>
                                    </div>
                                </div>
                                <div className="text-xs text-purple-700">
                                    ✅ KIS 잔고 확인 완료 ({portfolio.positions.length}종목)
                                </div>
                            </div>
                        </div>
                        {batchAnalysisInProgress && portfolio.positions.length > 10 && (
                            <div className="mt-3 pt-2 border-t border-purple-200">
                                <p className="text-xs text-purple-700">
                                    📊 Batch Analysis: {currentAnalysisIndex + 1}/{portfolio.positions.length} positions
                                    ({portfolio.positions.length > 10 ? `(Batch ${Math.floor(currentAnalysisIndex / 10) + 1} of ${Math.ceil(portfolio.positions.length / 10)})` : ''})
                                </p>
                            </div>
                        )}
                    </div>

                    {/* Analysis Logs */}
                    {analysisLogs.length > 0 && (
                        <div className="bg-white rounded-lg border border-gray-200 p-4">
                            <h4 className="text-sm font-semibold text-gray-900 mb-3">📊 Analysis Logs</h4>
                            <div className="space-y-2">
                                {analysisLogs.map((log, idx) => (
                                    <div key={idx} className="text-xs bg-gray-50 rounded p-2 border border-gray-100">
                                        <div className="flex justify-between items-center mb-1">
                                            <span className="font-medium text-gray-700">{log.ticker}</span>
                                            <span className="text-gray-400">{new Date(log.timestamp).toLocaleTimeString('ko-KR')}</span>
                                        </div>
                                        <div className="flex gap-4 text-xs">
                                            <span className="text-gray-500">{Number(log.duration_seconds).toFixed(1)}s</span>
                                            <span className="text-gray-500">📰 {log.news_count} news</span>
                                            <span className="text-gray-500">
                                                Trader: <span className={getAgentColor(log.agents_summary.trader)}>{log.agents_summary.trader}</span>
                                            </span>
                                            <span className="text-gray-500">
                                                PM: <span className={getAgentColor(log.agents_summary.pm)}>{log.agents_summary.pm}</span>
                                            </span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Always show positions list with real-time agent updates */}
                    <div className="space-y-6">
                        {portfolio.positions
                            .sort((a, b) => b.market_value - a.market_value)
                            .map(pos => {
                                const agents = agentAnalysis[pos.symbol];
                                const rec = aiRecommendations[pos.symbol];
                                const loadingStates = agentLoadingStates[pos.symbol] || {
                                    trader: true,
                                    risk: true,
                                    analyst: true,
                                    pm: true
                                };

                                // Check if any agent is still loading
                                const isLoadingAgent = loadingStates.trader || loadingStates.risk || loadingStates.analyst || loadingStates.pm;

                                return (
                                    <div key={pos.symbol} className="bg-white rounded-lg border border-gray-200 hover:shadow-md transition-shadow">
                                        {/* Header: Ticker + Final Decision */}
                                        <div className="px-6 py-4 bg-gray-50 border-b border-gray-200 flex justify-between items-center">
                                            <div>
                                                <div className="flex items-center gap-2">
                                                    <h3 className="text-xl font-bold text-gray-900">{pos.symbol}</h3>
                                                    <span className="px-2 py-0.5 rounded text-xs bg-blue-100 text-blue-700 font-medium">
                                                        보유중 {pos.quantity}주
                                                    </span>
                                                </div>
                                                <span className="text-sm text-gray-500">{pos.quantity} shares • ${pos.avg_price.toFixed(2)} avg</span>
                                            </div>
                                            <div className="flex items-center gap-2">
                                                {rec ? (
                                                    <>
                                                        {getActionIcon(rec.action)}
                                                        <span className={`px-2 py-0.5 rounded text-xs font-bold ${getActionBadge(rec.action)}`}>
                                                            {rec.action}
                                                        </span>
                                                        <span className="text-xs font-medium text-gray-500">
                                                            {(rec.confidence * 100).toFixed(0)}% PM Confidence
                                                        </span>
                                                    </>
                                                ) : (
                                                    <span className="text-xs text-gray-400">분석 중...</span>
                                                )}
                                            </div>
                                        </div>

                                        {/* Position Summary */}
                                        <div className="px-6 py-3 bg-white border-b border-gray-100">
                                            <div className="flex justify-between items-center text-sm">
                                                <div className="flex gap-4">
                                                    <span className="text-gray-500">현재가: <span className="font-medium text-gray-900">${pos.current_price.toFixed(2)}</span></span>
                                                    <span className="text-gray-500">평가액: <span className="font-medium text-gray-900">${pos.market_value.toLocaleString()}</span></span>
                                                </div>
                                                <div className="flex items-center gap-2">
                                                    <span className={`px-2 py-0.5 rounded ${pos.profit_loss_pct >= 0 ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'} text-xs font-medium`}>
                                                        {pos.profit_loss >= 0 ? '+' : ''}${pos.profit_loss.toFixed(2)} ({pos.profit_loss_pct >= 0 ? '+' : ''}{pos.profit_loss_pct.toFixed(2)}%)
                                                    </span>
                                                </div>
                                            </div>
                                        </div>

                                        {/* Portfolio Action Guide Card */}
                                        {agentAnalysis[pos.symbol]?.portfolio_action_guide && (
                                            <div className="px-6 pt-4">
                                                <PortfolioActionCard
                                                    decision={{
                                                        ticker: pos.symbol,
                                                        action: (agentAnalysis[pos.symbol]?.pm_agent?.action as any) || 'HOLD',
                                                        conviction: agentAnalysis[pos.symbol]?.pm_agent?.confidence || 0,
                                                        reasoning: agentAnalysis[pos.symbol]?.pm_agent?.reasoning || '',
                                                        position_size: 0,
                                                        risk_factors: [],
                                                        portfolio_action: agentAnalysis[pos.symbol]?.portfolio_action_guide?.action as any,
                                                        action_reason: agentAnalysis[pos.symbol]?.portfolio_action_guide?.reason,
                                                        action_strength: agentAnalysis[pos.symbol]?.portfolio_action_guide?.strength,
                                                        position_adjustment_pct: agentAnalysis[pos.symbol]?.portfolio_action_guide?.position_adjustment_pct
                                                    }}
                                                />
                                            </div>
                                        )}

                                        {/* Stock Chart */}
                                        <div className="px-6 py-4 border-b border-gray-100">
                                            <div className="flex items-center justify-between mb-2">
                                                <h4 className="text-sm font-semibold text-gray-700">📊 기술적 분석 차트</h4>
                                            </div>
                                            <StockChartWidget
                                                symbol={pos.symbol}
                                                timeframe="1h"
                                                height={250}
                                                showIndicators={true}
                                            />
                                        </div>

                                        {/* Agent Opinions */}
                                        <div className="px-6 py-4 space-y-4">
                                            {/* Trader Agent */}
                                            <div className="border-l-4 border-blue-500 pl-4">
                                                <div className="flex items-center gap-2 mb-2">
                                                    <span className="font-semibold text-sm text-blue-900">📈 Trader Agent ({((PERSONA_MODES[personaMode]?.weights.trader_mvp || 0.35) * 100).toFixed(0)}%)</span>
                                                    {loadingStates.trader && !agents?.trader_agent ? (
                                                        <span className="text-xs text-blue-600 animate-pulse">분석 중...</span>
                                                    ) : agents?.trader_agent?.latency_seconds ? (
                                                        <span className="text-xs text-gray-400">
                                                            {agents.trader_agent.latency_seconds.toFixed(1)}s latency
                                                        </span>
                                                    ) : null}
                                                </div>
                                                {agents?.trader_agent ? (
                                                    <div className="space-y-1">
                                                        <div className="flex items-center gap-2">
                                                            {getActionIcon(agents.trader_agent.action)}
                                                            <span className={`text-xs font-bold ${getAgentBadge(agents.trader_agent.action)}`}>
                                                                {agents.trader_agent.action}
                                                            </span>
                                                            <span className="text-xs text-gray-500">
                                                                {(agents.trader_agent.confidence * 100).toFixed(0)}% Confidence
                                                            </span>
                                                        </div>
                                                        <p className="text-xs text-gray-600 leading-relaxed whitespace-pre-wrap break-words max-w-none">
                                                            {agents.trader_agent.reasoning || 'No reasoning provided'}
                                                        </p>
                                                    </div>
                                                ) : (
                                                    <div className="flex items-center gap-2 py-2">
                                                        <LoadingSpinner size="sm" />
                                                        <span className="text-xs text-gray-500">Trader Agent 분석 중...</span>
                                                    </div>
                                                )}
                                            </div>

                                            {/* Risk Agent */}
                                            <div className="border-l-4 border-yellow-500 pl-4">
                                                <div className="flex items-center gap-2 mb-2">
                                                    <span className="font-semibold text-sm text-yellow-900">⚠️ Risk Agent ({((PERSONA_MODES[personaMode]?.weights.risk_mvp || 0.30) * 100).toFixed(0)}%)</span>
                                                    {loadingStates.risk && !agents?.risk_agent ? (
                                                        <span className="text-xs text-yellow-600 animate-pulse">분석 중...</span>
                                                    ) : agents?.risk_agent?.latency_seconds ? (
                                                        <span className="text-xs text-gray-400">
                                                            {agents.risk_agent.latency_seconds.toFixed(1)}s latency
                                                        </span>
                                                    ) : null}
                                                </div>
                                                {agents?.risk_agent ? (
                                                    <div className="space-y-1">
                                                        <div className="flex items-center gap-2">
                                                            {getActionIcon(agents.risk_agent.action)}
                                                            <span className={`text-xs font-bold ${getAgentBadge(agents.risk_agent.action)}`}>
                                                                {agents.risk_agent.action}
                                                            </span>
                                                            <span className="text-xs text-gray-500">
                                                                {(agents.risk_agent.confidence * 100).toFixed(0)}% Confidence
                                                            </span>
                                                        </div>
                                                        <p className="text-xs text-gray-600 leading-relaxed whitespace-pre-wrap break-words max-w-none">
                                                            {agents.risk_agent.reasoning || 'No reasoning provided'}
                                                        </p>
                                                    </div>
                                                ) : (
                                                    <div className="flex items-center gap-2 py-2">
                                                        <LoadingSpinner size="sm" />
                                                        <span className="text-xs text-gray-500">Risk Agent 분석 중...</span>
                                                    </div>
                                                )}
                                            </div>

                                            {/* Analyst Agent */}
                                            <div className="border-l-4 border-purple-500 pl-4">
                                                <div className="flex items-center gap-2 mb-2">
                                                    <span className="font-semibold text-sm text-purple-900">📰 Analyst Agent ({((PERSONA_MODES[personaMode]?.weights.analyst_mvp || 0.35) * 100).toFixed(0)}%)</span>
                                                    {loadingStates.analyst && !agents?.analyst_agent ? (
                                                        <span className="text-xs text-purple-600 animate-pulse">분석 중...</span>
                                                    ) : agents?.analyst_agent?.latency_seconds ? (
                                                        <span className="text-xs text-gray-400">
                                                            {agents.analyst_agent.latency_seconds.toFixed(1)}s latency
                                                        </span>
                                                    ) : null}
                                                </div>
                                                {agents?.analyst_agent ? (
                                                    <div className="space-y-1">
                                                        <div className="flex items-center gap-2">
                                                            {getActionIcon(agents.analyst_agent.action)}
                                                            <span className={`text-xs font-bold ${getAgentBadge(agents.analyst_agent.action)}`}>
                                                                {agents.analyst_agent.action}
                                                            </span>
                                                            <span className="text-xs text-gray-500">
                                                                {(agents.analyst_agent.confidence * 100).toFixed(0)}% Confidence
                                                            </span>
                                                        </div>
                                                        <p className="text-xs text-gray-600 leading-relaxed whitespace-pre-wrap break-words max-w-none">
                                                            {agents.analyst_agent.reasoning || 'No reasoning provided'}
                                                        </p>
                                                    </div>
                                                ) : (
                                                    <div className="flex items-center gap-2 py-2">
                                                        <LoadingSpinner size="sm" />
                                                        <span className="text-xs text-gray-500">Analyst Agent 분석 중...</span>
                                                    </div>
                                                )}
                                            </div>

                                            {/* PM Agent (Final) */}
                                            <div className="bg-gray-50 border-l-4 border-gray-300 pl-4 p-4">
                                                <div className="flex items-center gap-2 mb-2">
                                                    <span className="font-semibold text-sm text-gray-900">🏛️️ PM Agent (Final Decision)</span>
                                                    {loadingStates.pm && !agents?.pm_agent ? (
                                                        <span className="text-xs text-gray-600 animate-pulse">최종 결정 중...</span>
                                                    ) : null}
                                                </div>
                                                {agents?.pm_agent ? (
                                                    <div className="space-y-1">
                                                        <div className="flex items-center gap-2">
                                                            {getActionIcon(agents.pm_agent.action)}
                                                            <span className={`text-xs font-bold ${getActionBadge(agents.pm_agent.action)}`}>
                                                                {agents.pm_agent.action}
                                                            </span>
                                                            <span className="text-xs text-gray-500">
                                                                Hard Rules: {agents.pm_agent.hard_rules_passed.length} passed, {agents.pm_agent.hard_rules_violations.length} violated
                                                            </span>
                                                        </div>
                                                        <p className="text-xs text-gray-600 leading-relaxed whitespace-pre-wrap break-words max-w-none">
                                                            {agents.pm_agent.reasoning || 'No reasoning provided'}
                                                        </p>
                                                    </div>
                                                ) : (
                                                    <div className="flex items-center gap-2 py-2">
                                                        <LoadingSpinner size="sm" />
                                                        <span className="text-xs text-gray-500">PM Agent 최종 결정 중...</span>
                                                    </div>
                                                )}
                                            </div>

                                            {/* NEW: Portfolio Action Guide Card */}
                                            {agents?.portfolio_action_guide && (
                                                <div className={`mx-0 mt-4 p-4 rounded-lg border-2 ${agents.portfolio_action_guide.action === 'SELL' ? 'bg-red-50 border-red-200' :
                                                    agents.portfolio_action_guide.action === 'BUY_MORE' ? 'bg-green-50 border-green-200' :
                                                        agents.portfolio_action_guide.action === 'HOLD' ? 'bg-yellow-50 border-yellow-200' :
                                                            'bg-gray-50 border-gray-200'
                                                    }`}>
                                                    <div className="flex items-center justify-between">
                                                        <div className="flex items-center gap-2">
                                                            {agents.portfolio_action_guide.action === 'SELL' && <TrendingDown className="w-6 h-6 text-red-600" />}
                                                            {agents.portfolio_action_guide.action === 'BUY_MORE' && <TrendingUp className="w-6 h-6 text-green-600" />}
                                                            {agents.portfolio_action_guide.action === 'HOLD' && <MinusCircle className="w-6 h-6 text-yellow-600" />}
                                                            {agents.portfolio_action_guide.action === 'DO_NOT_BUY' && <AlertCircle className="w-6 h-6 text-gray-600" />}
                                                            <div>
                                                                <h4 className="font-bold text-sm">
                                                                    {agents.portfolio_action_guide.action === 'SELL' && '📉 매도 추천'}
                                                                    {agents.portfolio_action_guide.action === 'BUY_MORE' && '📈 추가 매수'}
                                                                    {agents.portfolio_action_guide.action === 'HOLD' && '⏸️ 보유 유지'}
                                                                    {agents.portfolio_action_guide.action === 'DO_NOT_BUY' && '⚠️ 관망 권장'}
                                                                </h4>
                                                                <p className="text-xs text-gray-600 mt-1">{agents.portfolio_action_guide.reason}</p>
                                                            </div>
                                                        </div>
                                                        <div className="text-right">
                                                            <span className={`text-xs px-2 py-1 rounded ${agents.portfolio_action_guide.strength === 'strong' ? 'bg-green-200' :
                                                                agents.portfolio_action_guide.strength === 'weak' ? 'bg-gray-200' :
                                                                    'bg-yellow-200'
                                                                }`}>
                                                                {agents.portfolio_action_guide.strength === 'strong' && '강한 신호'}
                                                                {agents.portfolio_action_guide.strength === 'moderate' && '보통 신호'}
                                                                {agents.portfolio_action_guide.strength === 'weak' && '약한 신호'}
                                                            </span>
                                                            <p className="text-xs text-gray-500 mt-1">
                                                                신뢰도 {(agents.portfolio_action_guide.confidence * 100).toFixed(0)}%
                                                            </p>
                                                        </div>
                                                    </div>
                                                    {agents.portfolio_action_guide.action !== 'DO_NOT_BUY' && (
                                                        <div className="mt-3 grid grid-cols-2 gap-2 text-xs border-t border-gray-200 pt-2">
                                                            <div>
                                                                <span className="text-gray-500">손절가</span>
                                                                <p className="font-medium text-red-600">{(agents.portfolio_action_guide.stop_loss_pct * 100).toFixed(1)}%</p>
                                                            </div>
                                                            <div>
                                                                <span className="text-gray-500">목표가</span>
                                                                <p className="font-medium text-green-600">{(agents.portfolio_action_guide.take_profit_pct * 100).toFixed(1)}%</p>
                                                            </div>
                                                        </div>
                                                    )}
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                );
                            })}
                    </div>
                </div>
            )}
        </div>
    );
};

export default Portfolio;

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

import React from 'react';
import { useQuery } from '@tanstack/react-query';

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
    sector?: string; // From Yahoo Finance via backend
}

interface PortfolioData {
    total_value: number;
    cash: number;
    invested: number;
    total_pnl: number;
    total_pnl_pct: number;
    daily_pnl: number;
    daily_return_pct: number;
    positions: Position[];
}

// Mock data for development
const MOCK_PORTFOLIO: PortfolioData = {
    total_value: 127580.50,
    cash: 45200.00,
    invested: 82380.50,
    total_pnl: 7380.50,
    total_pnl_pct: 9.84,
    daily_pnl: 1250.30,
    daily_return_pct: 0.98,
    positions: [
        {
            symbol: 'AAPL',
            quantity: 100,
            avg_price: 175.20,
            current_price: 178.50,
            market_value: 17850.00,
            profit_loss: 330.00,
            profit_loss_pct: 1.88,
            daily_pnl: 150.00,
            daily_return_pct: 0.84
        },
        {
            symbol: 'NVDA',
            quantity: 50,
            avg_price: 480.00,
            current_price: 495.20,
            market_value: 24760.00,
            profit_loss: 760.00,
            profit_loss_pct: 3.17,
            daily_pnl: 380.00,
            daily_return_pct: 1.56
        },
        {
            symbol: 'MSFT',
            quantity: 75,
            avg_price: 385.00,
            current_price: 392.10,
            market_value: 29407.50,
            profit_loss: 532.50,
            profit_loss_pct: 1.84,
            daily_pnl: 225.00,
            daily_return_pct: 0.77
        },
        {
            symbol: 'GOOGL',
            quantity: 80,
            avg_price: 138.50,
            current_price: 132.90,
            market_value: 10632.00,
            profit_loss: -448.00,
            profit_loss_pct: -4.04,
            daily_pnl: -160.00,
            daily_return_pct: -1.48
        }
    ]
};

const Portfolio: React.FC = () => {
    // Fetch portfolio from API
    const { data: portfolio, isLoading, error } = useQuery({
        queryKey: ['portfolio'],
        queryFn: async () => {
            const response = await fetch('/api/portfolio');
            if (!response.ok) {
                throw new Error(`Failed to fetch portfolio: ${response.statusText}`);
            }
            return response.json();
        },
        refetchInterval: 30000, // Refresh every 30 seconds
        // Fallback to mock data if API fails (development mode)
        placeholderData: MOCK_PORTFOLIO
    });

    if (isLoading) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <div className="text-center">
                    <div className="text-4xl mb-4">🔄</div>
                    <p className="text-gray-600">포트폴리오 로딩 중...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <div className="text-center">
                    <p className="text-lg text-red-600">⚠️ 포트폴리오를 불러올 수 없습니다</p>
                    <p className="text-sm text-gray-500 mt-2">{(error as Error).message}</p>
                </div>
            </div>
        );
    }

    const allocation_pct = (portfolio.invested / portfolio.total_value) * 100;
    const cash_pct = (portfolio.cash / portfolio.total_value) * 100;

    return (
        <div className="space-y-6 p-6">
            {/* Header */}
            <div>
                <h1 className="text-3xl font-bold text-gray-900">💼 포트폴리오</h1>
                <p className="text-gray-600 mt-1">Portfolio overview and performance</p>
            </div>

            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {/* Total Value */}
                <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm font-medium text-gray-600">총 자산</p>
                            <p className="text-2xl font-bold text-gray-900 mt-1">
                                ${portfolio.total_value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                            </p>
                            <p className={`text-sm mt-1 ${portfolio.daily_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                {portfolio.daily_pnl >= 0 ? '+' : ''}${portfolio.daily_pnl.toFixed(2)} ({portfolio.daily_return_pct >= 0 ? '+' : ''}{portfolio.daily_return_pct.toFixed(2)}%)
                                <span className="text-gray-500 ml-1">오늘</span>
                            </p>
                        </div>
                        <div className="p-3 bg-blue-100 rounded-full">
                            <span className="text-2xl">💰</span>
                        </div>
                    </div>
                </div>

                {/* Invested */}
                <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm font-medium text-gray-600">투자 금액</p>
                            <p className="text-2xl font-bold text-gray-900 mt-1">
                                ${(portfolio.invested || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                            </p>
                            <p className="text-sm text-gray-600 mt-1">
                                {allocation_pct.toFixed(1)}% 배분
                            </p>
                        </div>
                        <div className="p-3 bg-green-100 rounded-full">
                            <span className="text-2xl">📈</span>
                        </div>
                    </div>
                </div>

                {/* Cash */}
                <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm font-medium text-gray-600">현금</p>
                            <p className="text-2xl font-bold text-gray-900 mt-1">
                                ${portfolio.cash.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                            </p>
                            <p className="text-sm text-gray-600 mt-1">
                                {cash_pct.toFixed(1)}% 보유
                            </p>
                        </div>
                        <div className="p-3 bg-purple-100 rounded-full">
                            <span className="text-2xl">💵</span>
                        </div>
                    </div>
                </div>

                {/* Total P&L */}
                <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm font-medium text-gray-600">총 손익</p>
                            <p className={`text-2xl font-bold mt-1 ${(portfolio.total_pnl || 0) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                {(portfolio.total_pnl || 0) >= 0 ? '+' : ''}${(portfolio.total_pnl || 0).toFixed(2)}
                            </p>
                            <p className={`text-sm mt-1 ${(portfolio.total_pnl_pct || 0) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                {(portfolio.total_pnl_pct || 0) >= 0 ? '+' : ''}{(portfolio.total_pnl_pct || 0).toFixed(2)}%
                            </p>
                        </div>
                        <div className={`p-3 rounded-full ${(portfolio.total_pnl || 0) >= 0 ? 'bg-green-100' : 'bg-red-100'}`}>
                            <span className="text-2xl">{(portfolio.total_pnl || 0) >= 0 ? '🎯' : '📉'}</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Positions Table */}
            <div className="bg-white rounded-lg shadow-md p-6">
                <h2 className="text-xl font-bold text-gray-900 mb-4">📊 보유 종목 ({portfolio.positions.length})</h2>

                {portfolio.positions.length > 0 ? (
                    <>
                        {/* Mobile: Card Layout */}
                        <div className="md:hidden space-y-4">
                            {portfolio.positions.map((position: Position) => (
                                <div key={position.symbol} className="bg-gray-50 rounded-lg p-4 hover:shadow-md transition-shadow">
                                    {/* Header */}
                                    <div className="flex justify-between items-center mb-3">
                                        <div>
                                            <h3 className="text-lg font-bold text-gray-900">{position.symbol}</h3>
                                            <p className="text-sm text-gray-500">{position.quantity}주 보유</p>
                                        </div>
                                        <div className="text-right">
                                            <div className="text-lg font-mono font-semibold text-gray-900">${position.current_price.toFixed(2)}</div>
                                            <div className="text-xs text-gray-500">평균: ${position.avg_price.toFixed(2)}</div>
                                        </div>
                                    </div>

                                    {/* Grid Info */}
                                    <div className="grid grid-cols-2 gap-3">
                                        <div>
                                            <p className="text-xs text-gray-500 mb-1">평가액</p>
                                            <p className="text-sm font-mono font-semibold text-gray-900">${position.market_value.toLocaleString('en-US', { minimumFractionDigits: 2 })}</p>
                                        </div>
                                        <div>
                                            <p className="text-xs text-gray-500 mb-1">손익</p>
                                            <p className={`text-sm font-mono font-semibold ${position.profit_loss >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                                {position.profit_loss >= 0 ? '+' : ''}${position.profit_loss.toFixed(2)}
                                            </p>
                                        </div>
                                        <div>
                                            <p className="text-xs text-gray-500 mb-1">수익률</p>
                                            <p className={`text-sm font-mono font-semibold ${position.profit_loss_pct >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                                {position.profit_loss_pct >= 0 ? '+' : ''}{position.profit_loss_pct.toFixed(2)}%
                                            </p>
                                        </div>
                                        <div>
                                            <p className="text-xs text-gray-500 mb-1">일일 손익</p>
                                            <p className={`text-sm font-mono ${position.daily_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                                {position.daily_pnl >= 0 ? '+' : ''}${position.daily_pnl.toFixed(2)} ({position.daily_return_pct >= 0 ? '+' : ''}{position.daily_return_pct.toFixed(2)}%)
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>

                        {/* Desktop: Table Layout */}
                        <div className="hidden md:block overflow-x-auto">
                            <table className="w-full">
                                <thead>
                                    <tr className="border-b border-gray-200">
                                        <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">티커</th>
                                        <th className="text-right py-3 px-4 text-sm font-semibold text-gray-700">수량</th>
                                        <th className="text-right py-3 px-4 text-sm font-semibold text-gray-700">평균 단가</th>
                                        <th className="text-right py-3 px-4 text-sm font-semibold text-gray-700">현재가</th>
                                        <th className="text-right py-3 px-4 text-sm font-semibold text-gray-700">평가액</th>
                                        <th className="text-right py-3 px-4 text-sm font-semibold text-gray-700">손익</th>
                                        <th className="text-right py-3 px-4 text-sm font-semibold text-gray-700">수익률</th>
                                        <th className="text-right py-3 px-4 text-sm font-semibold text-gray-700">일일 손익</th>
                                        <th className="text-right py-3 px-4 text-sm font-semibold text-gray-700">일일 수익률</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {portfolio.positions.map((position: Position) => (
                                        <tr key={position.symbol} className="border-b border-gray-100 hover:bg-gray-50">
                                            <td className="py-3 px-4 font-semibold text-gray-900">{position.symbol}</td>
                                            <td className="text-right py-3 px-4 font-mono text-sm text-gray-700">{position.quantity}</td>
                                            <td className="text-right py-3 px-4 font-mono text-sm text-gray-700">${position.avg_price.toFixed(2)}</td>
                                            <td className="text-right py-3 px-4 font-mono text-sm text-gray-700">${position.current_price.toFixed(2)}</td>
                                            <td className="text-right py-3 px-4 font-mono text-sm text-gray-700">${position.market_value.toLocaleString('en-US', { minimumFractionDigits: 2 })}</td>
                                            <td className={`text-right py-3 px-4 font-mono text-sm font-semibold ${position.profit_loss >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                                {position.profit_loss >= 0 ? '+' : ''}${position.profit_loss.toFixed(2)}
                                            </td>
                                            <td className={`text-right py-3 px-4 font-mono text-sm font-semibold ${position.profit_loss_pct >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                                {position.profit_loss_pct >= 0 ? '+' : ''}{position.profit_loss_pct.toFixed(2)}%
                                            </td>
                                            <td className={`text-right py-3 px-4 font-mono text-sm ${position.daily_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                                {position.daily_pnl >= 0 ? '+' : ''}${position.daily_pnl.toFixed(2)}
                                            </td>
                                            <td className={`text-right py-3 px-4 font-mono text-sm ${position.daily_return_pct >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                                {position.daily_return_pct >= 0 ? '+' : ''}{position.daily_return_pct.toFixed(2)}%
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </>
                ) : (
                    <div className="text-center py-12">
                        <p className="text-gray-500 text-lg">보유 종목이 없습니다</p>
                        <p className="text-gray-400 text-sm mt-2">War Room에서 토론을 시작해보세요</p>
                    </div>
                )}
            </div>

            {/* Allocation Chart */}
            <div className="bg-white rounded-lg shadow-md p-6">
                <h2 className="text-xl font-bold text-gray-900 mb-6">📊 자산 배분</h2>

                {(() => {
                    const total = portfolio.total_value || 1;
                    const cash = portfolio.cash || (total - portfolio.positions.reduce((sum: number, p: any) => sum + p.market_value, 0));

                    // 자산 유형 분류 함수
                    const getAssetType = (symbol: string): string => {
                        const upperSymbol = symbol.toUpperCase();

                        // ETF 리스트 (주요 ETF들)
                        const etfs = ['SPY', 'QQQ', 'VOO', 'IVV', 'VTI', 'VEA', 'VWO', 'AGG', 'BND', 'TLT',
                            'IEF', 'SHY', 'LQD', 'HYG', 'JNK', 'GLD', 'SLV', 'USO', 'DIA', 'IWM',
                            'EEM', 'EFA', 'VNQ', 'XLF', 'XLE', 'XLK', 'XLV', 'XLI', 'XLP', 'XLY'];

                        // 채권 ETF (더 구체적)
                        const bonds = ['AGG', 'BND', 'TLT', 'IEF', 'SHY', 'LQD', 'HYG', 'JNK', 'MUB', 'TIP'];

                        // 암호화폐 관련
                        const crypto = ['BTC', 'ETH', 'COIN', 'MSTR', 'RIOT', 'MARA'];

                        if (bonds.includes(upperSymbol)) return 'bonds';
                        if (crypto.includes(upperSymbol)) return 'crypto';
                        if (etfs.includes(upperSymbol)) return 'etf';

                        // 기본은 주식
                        return 'stocks';
                    };

                    // 자산별 합계 계산
                    const assetAllocation: Record<string, number> = {
                        stocks: 0,
                        etf: 0,
                        bonds: 0,
                        crypto: 0,
                        cash: cash
                    };

                    portfolio.positions.forEach((position: Position) => {
                        const type = getAssetType(position.symbol);
                        assetAllocation[type] += position.market_value;
                    });

                    // 자산 유형 정의 (보유 중인 것만 필터링)
                    const assetTypes = [
                        { key: 'stocks', label: '주식', color: 'bg-blue-500', value: assetAllocation.stocks },
                        { key: 'etf', label: 'ETF', color: 'bg-purple-500', value: assetAllocation.etf },
                        { key: 'bonds', label: '채권', color: 'bg-green-500', value: assetAllocation.bonds },
                        { key: 'crypto', label: '암호화폐', color: 'bg-orange-500', value: assetAllocation.crypto },
                        { key: 'cash', label: '현금', color: 'bg-gray-400', value: assetAllocation.cash }
                    ].filter(asset => asset.value > 0); // 보유 중인 자산만

                    return (
                        <>
                            {/* Progress Bar */}
                            <div className="h-8 bg-gray-100 rounded-full overflow-hidden flex mb-6 shadow-inner">
                                {assetTypes.map((asset, idx) => {
                                    const percentage = (asset.value / total) * 100;
                                    return (
                                        <div
                                            key={asset.key}
                                            className={`${asset.color} flex items-center justify-center text-white font-semibold text-xs transition-all hover:opacity-80`}
                                            style={{ width: `${percentage}%` }}
                                            title={`${asset.label}: $${asset.value.toFixed(2)} (${percentage.toFixed(1)}%)`}
                                        >
                                            {percentage > 8 && `${percentage.toFixed(1)}%`}
                                        </div>
                                    );
                                })}
                            </div>

                            {/* Legend - Responsive Grid */}
                            <div className="grid grid-cols-2 md:grid-cols-3 lg:flex lg:flex-wrap gap-4">
                                {assetTypes.map(asset => {
                                    const percentage = (asset.value / total) * 100;
                                    return (
                                        <div key={asset.key} className="flex flex-col gap-2">
                                            <div className="flex items-center gap-3 bg-gray-50 rounded-lg p-3 hover:shadow-md transition-shadow">
                                                <div className={`w-5 h-5 ${asset.color} rounded shadow-sm`}></div>
                                                <div className="flex-1">
                                                    <div className="text-sm font-semibold text-gray-700">{asset.label}</div>
                                                    <div className="text-xs text-gray-500 font-mono">
                                                        ${asset.value.toFixed(2)} ({percentage.toFixed(1)}%)
                                                    </div>
                                                </div>
                                            </div>

                                            {/* Sector breakdown for stocks */}
                                            {asset.key === 'stocks' && (() => {
                                                // Get unique sectors from stock positions
                                                const stockPositions = portfolio.positions.filter((p: Position) => getAssetType(p.symbol) === 'stocks');
                                                const sectors = Array.from(new Set(stockPositions.map((p: Position) => p.sector).filter(Boolean))) as string[];

                                                if (sectors.length === 0) return null;

                                                const sectorColors: Record<string, string> = {
                                                    'Technology': 'bg-blue-500',
                                                    'Financial Services': 'bg-green-500',
                                                    'Healthcare': 'bg-red-500',
                                                    'Consumer Cyclical': 'bg-purple-500',
                                                    'Consumer Defensive': 'bg-yellow-500',
                                                    'Energy': 'bg-orange-500',
                                                    'Industrials': 'bg-gray-600',
                                                    'Communication Services': 'bg-pink-500',
                                                    'Utilities': 'bg-teal-500',
                                                    'Basic Materials': 'bg-indigo-500',
                                                    'Real Estate': 'bg-cyan-500',
                                                };

                                                const displaySectors = sectors.slice(0, 3);
                                                const moreCount = sectors.length - 3;

                                                return (
                                                    <div className="ml-8 text-xs text-gray-500">
                                                        <div className="font-semibold text-gray-600 mb-2">섹터 구분:</div>
                                                        <div className="flex flex-wrap gap-2">
                                                            {displaySectors.map((sector: string) => (
                                                                <div key={sector} className="flex items-center gap-1.5 bg-white px-2 py-1 rounded border border-gray-200">
                                                                    <div className={`w-3 h-3 ${sectorColors[sector] || 'bg-gray-400'} rounded`}></div>
                                                                    <span>{sector}</span>
                                                                </div>
                                                            ))}
                                                            {moreCount > 0 && (
                                                                <div className="text-gray-400 px-2 py-1">+ {moreCount} more</div>
                                                            )}
                                                        </div>
                                                    </div>
                                                );
                                            })()}
                                        </div>
                                    );
                                })}
                            </div>

                            {/* Total Summary */}
                            <div className="mt-6 pt-4 border-t border-gray-200 flex justify-between items-center">
                                <span className="text-sm font-medium text-gray-600">총 자산</span>
                                <span className="text-xl font-bold text-gray-900 font-mono">${total.toLocaleString('en-US', { minimumFractionDigits: 2 })}</span>
                            </div>
                        </>
                    );
                })()}
            </div>
        </div>
    );
};

export default Portfolio;

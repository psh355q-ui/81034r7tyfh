/**
 * Portfolio Dashboard - 포트폴리오 현황 대시보드
 *
 * Phase 27: REAL MODE UI
 * Date: 2025-12-25 (Updated to Tailwind CSS)
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
                            <p className={`text-2xl font-bold mt-1 ${portfolio.total_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                {portfolio.total_pnl >= 0 ? '+' : ''}${portfolio.total_pnl.toFixed(2)}
                            </p>
                            <p className={`text-sm mt-1 ${portfolio.total_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                {portfolio.total_pnl_pct >= 0 ? '+' : ''}{portfolio.total_pnl_pct.toFixed(2)}%
                            </p>
                        </div>
                        <div className={`p-3 rounded-full ${portfolio.total_pnl >= 0 ? 'bg-green-100' : 'bg-red-100'}`}>
                            <span className="text-2xl">{portfolio.total_pnl >= 0 ? '🎯' : '📉'}</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Positions Table */}
            <div className="bg-white rounded-lg shadow-md p-6">
                <h2 className="text-xl font-bold text-gray-900 mb-4">📊 보유 종목 ({portfolio.positions.length})</h2>

                {portfolio.positions.length > 0 ? (
                    <div className="overflow-x-auto">
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
                ) : (
                    <div className="text-center py-12">
                        <p className="text-gray-500 text-lg">보유 종목이 없습니다</p>
                        <p className="text-gray-400 text-sm mt-2">War Room에서 토론을 시작해보세요</p>
                    </div>
                )}
            </div>

            {/* Allocation Chart */}
            <div className="bg-white rounded-lg shadow-md p-6">
                <h2 className="text-xl font-bold text-gray-900 mb-4">📊 자산 배분</h2>

                <div className="space-y-4">
                    <div className="w-full h-12 bg-gray-200 rounded-lg overflow-hidden flex">
                        <div
                            className="bg-green-500 flex items-center justify-center text-white font-semibold text-sm"
                            style={{ width: `${allocation_pct}%` }}
                        >
                            {allocation_pct > 10 && `${allocation_pct.toFixed(1)}%`}
                        </div>
                        <div
                            className="bg-blue-500 flex items-center justify-center text-white font-semibold text-sm"
                            style={{ width: `${cash_pct}%` }}
                        >
                            {cash_pct > 10 && `${cash_pct.toFixed(1)}%`}
                        </div>
                    </div>

                    <div className="flex gap-6">
                        <div className="flex items-center gap-2">
                            <div className="w-4 h-4 bg-green-500 rounded"></div>
                            <span className="text-sm text-gray-700">투자 중 (${portfolio.invested.toLocaleString('en-US')})</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <div className="w-4 h-4 bg-blue-500 rounded"></div>
                            <span className="text-sm text-gray-700">현금 (${portfolio.cash.toLocaleString('en-US')})</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Portfolio;

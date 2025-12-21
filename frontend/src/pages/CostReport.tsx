/**
 * Cost Report Page
 * 
 * Monthly Grounding API cost analysis and visualization
 */

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { DollarSign, TrendingUp, AlertCircle, Calendar } from 'lucide-react';
import axios from 'axios';
import { Card } from '../components/common/Card';
import { LoadingSpinner } from '../components/common/LoadingSpinner';

interface CostReport {
    year: number;
    month: number;
    total_searches: number;
    total_cost_usd: number;
    emergency_searches: number;
    normal_searches: number;
    unique_tickers: number;
    by_ticker: Record<string, number>;
    daily_average: number;
    budget_used_pct: number;
    budget_remaining: number;
}

export const CostReport: React.FC = () => {
    const { data, isLoading } = useQuery<{ data: CostReport }>({
        queryKey: ['cost-report'],
        queryFn: () => axios.get('/api/emergency/grounding/report/monthly'),
        refetchInterval: 300000, // 5 minutes
    });

    const report = data?.data;

    if (isLoading) {
        return (
            <div className="flex justify-center items-center h-screen">
                <LoadingSpinner />
            </div>
        );
    }

    const getBudgetColor = (pct: number) => {
        if (pct >= 90) return 'text-red-600';
        if (pct >= 70) return 'text-yellow-600';
        return 'text-green-600';
    };

    return (
        <div className="space-y-6 p-6">
            {/* Header */}
            <div>
                <h1 className="text-3xl font-bold text-gray-900">💰 Grounding Cost Report</h1>
                <p className="text-gray-600 mt-1">
                    {report ? `${report.year}년 ${report.month}월` : 'Monthly cost analysis'}
                </p>
            </div>

            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <Card>
                    <div className="flex items-center gap-3">
                        <DollarSign className="text-blue-600" size={32} />
                        <div>
                            <p className="text-sm text-gray-600">Total Cost</p>
                            <p className="text-2xl font-bold">
                                ${report?.total_cost_usd?.toFixed(2) || '0.00'}
                            </p>
                        </div>
                    </div>
                </Card>

                <Card>
                    <div className="flex items-center gap-3">
                        <TrendingUp className="text-green-600" size={32} />
                        <div>
                            <p className="text-sm text-gray-600">Total Searches</p>
                            <p className="text-2xl font-bold">{report?.total_searches || 0}</p>
                            <p className="text-xs text-gray-500">
                                Avg: {report?.daily_average?.toFixed(1) || 0}/day
                            </p>
                        </div>
                    </div>
                </Card>

                <Card>
                    <div className="flex items-center gap-3">
                        <AlertCircle className="text-red-600" size={32} />
                        <div>
                            <p className="text-sm text-gray-600">Emergency Searches</p>
                            <p className="text-2xl font-bold">{report?.emergency_searches || 0}</p>
                            <p className="text-xs text-gray-500">
                                Normal: {report?.normal_searches || 0}
                            </p>
                        </div>
                    </div>
                </Card>

                <Card>
                    <div className="flex items-center gap-3">
                        <Calendar className="text-purple-600" size={32} />
                        <div>
                            <p className="text-sm text-gray-600">Budget Remaining</p>
                            <p className={`text-2xl font-bold ${getBudgetColor(report?.budget_used_pct || 0)}`}>
                                ${report?.budget_remaining?.toFixed(2) || '10.00'}
                            </p>
                            <p className="text-xs text-gray-500">
                                Used: {report?.budget_used_pct?.toFixed(0) || 0}%
                            </p>
                        </div>
                    </div>
                </Card>
            </div>

            {/* Budget Progress Bar */}
            <Card title="💳 Monthly Budget ($10.00)">
                <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                        <span>Used: ${report?.total_cost_usd?.toFixed(2) || '0.00'}</span>
                        <span>Remaining: ${report?.budget_remaining?.toFixed(2) || '10.00'}</span>
                    </div>
                    <div className="h-4 bg-gray-200 rounded-full overflow-hidden">
                        <div
                            className={`h-full transition-all ${(report?.budget_used_pct || 0) >= 90
                                ? 'bg-red-500'
                                : (report?.budget_used_pct || 0) >= 70
                                    ? 'bg-yellow-500'
                                    : 'bg-green-500'
                                }`}
                            style={{ width: `${Math.min(report?.budget_used_pct || 0, 100)}%` }}
                        />
                    </div>
                    <p className="text-xs text-gray-500 text-center">
                        {report?.budget_used_pct?.toFixed(1) || 0}% of budget used
                    </p>
                </div>
            </Card>

            {/* Top Tickers */}
            <Card title="📊 Top Searched Tickers">
                {report?.by_ticker && Object.keys(report.by_ticker).length > 0 ? (
                    <div className="space-y-3">
                        {Object.entries(report.by_ticker)
                            .sort((a, b) => b[1] - a[1])
                            .map(([ticker, count]) => (
                                <div key={ticker} className="flex items-center justify-between">
                                    <div className="flex items-center gap-3 flex-1">
                                        <span className="font-semibold text-lg w-16">{ticker}</span>
                                        <div className="flex-1 h-6 bg-gray-200 rounded-full overflow-hidden">
                                            <div
                                                className="h-full bg-blue-500"
                                                style={{
                                                    width: `${(count / (report.total_searches || 1)) * 100}%`,
                                                }}
                                            />
                                        </div>
                                    </div>
                                    <div className="text-right ml-4">
                                        <p className="font-semibold">{count}</p>
                                        <p className="text-xs text-gray-500">
                                            ${(count * 0.035).toFixed(2)}
                                        </p>
                                    </div>
                                </div>
                            ))}
                    </div>
                ) : (
                    <p className="text-center text-gray-600 py-8">
                        No searches recorded this month
                    </p>
                )}
            </Card>

            {/* Stats Summary */}
            <Card title="📈 Statistics">
                <div className="grid grid-cols-2 gap-4">
                    <div className="text-center p-4 bg-gray-50 rounded-lg">
                        <p className="text-sm text-gray-600">Unique Tickers</p>
                        <p className="text-3xl font-bold text-blue-600">
                            {report?.unique_tickers || 0}
                        </p>
                    </div>
                    <div className="text-center p-4 bg-gray-50 rounded-lg">
                        <p className="text-sm text-gray-600">Avg Cost/Search</p>
                        <p className="text-3xl font-bold text-green-600">$0.035</p>
                    </div>
                </div>
            </Card>

            {/* Warning if budget high */}
            {report && report.budget_used_pct >= 80 && (
                <div className="bg-yellow-50 border-l-4 border-yellow-500 p-4 rounded">
                    <div className="flex items-start gap-3">
                        <AlertCircle className="text-yellow-600" size={24} />
                        <div>
                            <p className="font-semibold text-yellow-800">Budget Warning</p>
                            <p className="text-sm text-yellow-700 mt-1">
                                You've used {report.budget_used_pct.toFixed(0)}% of your monthly budget.
                                Consider reducing non-emergency searches.
                            </p>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

/**
 * PartitionsCard - Account Partitioning Visualization
 * 
 * 📊 Data Sources:
 *   - API: /api/partitions/summary
 * 
 * 📤 Used By:
 *   - PersonaDashboard.tsx
 *   - Dashboard.tsx (optional)
 * 
 * 📝 Notes:
 *   - Shows Core/Income/Satellite wallet distribution
 *   - Pie chart visualization
 *   - Rebalance needed indicator
 */

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';
import { AlertTriangle, RefreshCw, Wallet } from 'lucide-react';
import { getPartitionsSummary, PartitionsSummary } from '../../services/personaApi';
import { Card } from '../common/Card';
import { LoadingSpinner } from '../common/LoadingSpinner';

const WALLET_COLORS = {
    core: '#3B82F6',      // blue
    income: '#10B981',    // green
    satellite: '#F59E0B', // amber
};

const WALLET_LABELS = {
    core: 'Core (장기)',
    income: 'Income (배당)',
    satellite: 'Satellite (공격)',
};

export const PartitionsCard: React.FC = () => {
    const { data, isLoading, error, refetch } = useQuery<PartitionsSummary>({
        queryKey: ['partitions-summary'],
        queryFn: getPartitionsSummary,
        refetchInterval: 30000, // 30 seconds
    });

    if (isLoading) {
        return (
            <Card className="h-[300px] flex items-center justify-center">
                <LoadingSpinner />
            </Card>
        );
    }

    if (error || !data) {
        return (
            <Card className="h-[300px] flex items-center justify-center">
                <div className="text-center text-gray-500">
                    <p>Failed to load partitions</p>
                    <button
                        onClick={() => refetch()}
                        className="mt-2 text-blue-500 hover:underline"
                    >
                        Retry
                    </button>
                </div>
            </Card>
        );
    }

    const chartData = [
        { name: WALLET_LABELS.core, value: data.wallets.core.value, pct: data.wallets.core.pct },
        { name: WALLET_LABELS.income, value: data.wallets.income.value, pct: data.wallets.income.pct },
        { name: WALLET_LABELS.satellite, value: data.wallets.satellite.value, pct: data.wallets.satellite.pct },
    ];

    return (
        <Card>
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                    <Wallet className="text-blue-500" size={20} />
                    <h3 className="font-semibold text-gray-800">가상 지갑</h3>
                </div>
                {data.rebalance_needed && (
                    <div className="flex items-center gap-1 text-amber-600 text-sm">
                        <AlertTriangle size={14} />
                        <span>리밸런싱 필요</span>
                    </div>
                )}
            </div>

            {/* Total Value */}
            <div className="text-center mb-4">
                <p className="text-sm text-gray-500">총 자산</p>
                <p className="text-2xl font-bold text-gray-900">
                    ${data.total_value.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                </p>
            </div>

            {/* Pie Chart */}
            <div className="h-[180px]">
                <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                        <Pie
                            data={chartData}
                            cx="50%"
                            cy="50%"
                            innerRadius={40}
                            outerRadius={70}
                            paddingAngle={2}
                            dataKey="value"
                        >
                            {chartData.map((entry, index) => (
                                <Cell
                                    key={`cell-${index}`}
                                    fill={Object.values(WALLET_COLORS)[index]}
                                />
                            ))}
                        </Pie>
                        <Tooltip
                            formatter={(value: number) => `$${value.toLocaleString()}`}
                        />
                        <Legend
                            formatter={(value, entry) => {
                                const item = chartData.find(d => d.name === value);
                                return `${value} (${((item?.pct || 0) * 100).toFixed(0)}%)`;
                            }}
                        />
                    </PieChart>
                </ResponsiveContainer>
            </div>

            {/* Wallet Details */}
            <div className="space-y-2 mt-4">
                {Object.entries(data.wallets).map(([key, wallet]) => (
                    <div
                        key={key}
                        className="flex items-center justify-between p-2 rounded-lg bg-gray-50"
                    >
                        <div className="flex items-center gap-2">
                            <div
                                className="w-3 h-3 rounded-full"
                                style={{ backgroundColor: WALLET_COLORS[key as keyof typeof WALLET_COLORS] }}
                            />
                            <span className="text-sm font-medium text-gray-700">
                                {WALLET_LABELS[key as keyof typeof WALLET_LABELS]}
                            </span>
                        </div>
                        <div className="text-right">
                            <span className="text-sm font-semibold text-gray-900">
                                ${wallet.value.toLocaleString()}
                            </span>
                            <span className={`text-xs ml-2 ${wallet.unrealized_pnl >= 0 ? 'text-green-600' : 'text-red-600'
                                }`}>
                                {wallet.unrealized_pnl >= 0 ? '+' : ''}
                                {wallet.unrealized_pnl_pct.toFixed(1)}%
                            </span>
                        </div>
                    </div>
                ))}
            </div>
        </Card>
    );
};

export default PartitionsCard;

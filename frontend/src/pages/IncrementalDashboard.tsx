/**
 * Incremental Update Dashboard Page
 * Phase 16 모니터링 및 비용 절감 시각화
 */

import React, { useState } from 'react';
import {
    TrendingDown,
    Database,
    Clock,
    DollarSign,
    Zap,
    Play,
    Square,
    RefreshCw,
    CheckCircle,
    XCircle,
} from 'lucide-react';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import {
    BarChart,
    Bar,
    PieChart,
    Pie,
    Cell,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
} from 'recharts';

// Types
interface IncrementalStats {
    total_tickers: number;
    total_rows_stored: number;
    last_update_date: string;
    avg_rows_per_ticker: number;
}

interface CostSavings {
    api_calls: {
        before_per_day: number;
        after_per_day: number;
        reduction_pct: number;
    };
    performance: {
        speedup_factor: number;
    };
    estimated_monthly_cost: {
        before_usd: number;
        after_usd: number;
        savings_usd: number;
        savings_pct: number;
    };
}

interface StorageUsage {
    total_size_gb: number;
    total_files: number;
    locations: Record<string, {
        size_mb: number;
        file_count: number;
        usage_pct: number;
    }>;
}

interface SchedulerStatus {
    is_running: boolean;
    schedule_time: string;
    last_update?: {
        successful: number;
        failed: number;
        duration_seconds: number;
    };
}

export const IncrementalDashboard: React.FC = () => {
    const [isLoading, setIsLoading] = useState(false);

    // Mock data (replace with actual API calls)
    const mockStats: IncrementalStats = {
        total_tickers: 100,
        total_rows_stored: 125800,
        last_update_date: '2025-11-23',
        avg_rows_per_ticker: 1258,
    };

    const mockCostSavings: CostSavings = {
        api_calls: {
            before_per_day: 182500,
            after_per_day: 100,
            reduction_pct: 99.95,
        },
        performance: {
            speedup_factor: 50,
        },
        estimated_monthly_cost: {
            before_usd: 10.55,
            after_usd: 1.51,
            savings_usd: 9.04,
            savings_pct: 86,
        },
    };

    const mockStorage: StorageUsage = {
        total_size_gb: 2.5,
        total_files: 1523,
        locations: {
            sec_filings: { size_mb: 450, file_count: 234, usage_pct: 18 },
            stock_prices: { size_mb: 1200, file_count: 856, usage_pct: 48 },
            ai_cache: { size_mb: 350, file_count: 189, usage_pct: 14 },
            news_archive: { size_mb: 300, file_count: 156, usage_pct: 12 },
            embeddings: { size_mb: 200, file_count: 88, usage_pct: 8 },
        },
    };

    const mockSchedulerStatus: SchedulerStatus = {
        is_running: true,
        schedule_time: '06:00',
        last_update: {
            successful: 95,
            failed: 0,
            duration_seconds: 45.2,
        },
    };

    // Chart data
    const costComparisonData = [
        {
            name: 'Before',
            cost: mockCostSavings.estimated_monthly_cost.before_usd,
            fill: '#ef4444',
        },
        {
            name: 'After',
            cost: mockCostSavings.estimated_monthly_cost.after_usd,
            fill: '#22c55e',
        },
    ];

    const storageData = Object.entries(mockStorage.locations).map(([name, data]) => ({
        name: name.replace(/_/g, ' '),
        value: data.size_mb,
        files: data.file_count,
    }));

    const COLORS = ['#3b82f6', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981'];

    const handleSchedulerAction = async (action: 'start' | 'stop' | 'run') => {
        setIsLoading(true);
        // TODO: API call
        console.log(`Scheduler action: ${action}`);
        setTimeout(() => setIsLoading(false), 1000);
    };

    return (
        <div className="space-y-6 p-6">
            {/* Header */}
            <div>
                <h1 className="text-3xl font-bold text-gray-900">Incremental Update Dashboard</h1>
                <p className="text-gray-600 mt-1">
                    Monitor cost savings and performance improvements
                </p>
            </div>

            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <Card>
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm text-gray-600">Total Tickers</p>
                            <p className="text-2xl font-bold text-gray-900">{mockStats.total_tickers}</p>
                        </div>
                        <Database className="text-blue-500" size={32} />
                    </div>
                </Card>

                <Card>
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm text-gray-600">Rows Stored</p>
                            <p className="text-2xl font-bold text-gray-900">
                                {(mockStats.total_rows_stored / 1000).toFixed(1)}K
                            </p>
                        </div>
                        <TrendingDown className="text-green-500" size={32} />
                    </div>
                </Card>

                <Card>
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm text-gray-600">Cost Savings</p>
                            <p className="text-2xl font-bold text-green-600">
                                {mockCostSavings.estimated_monthly_cost.savings_pct}%
                            </p>
                        </div>
                        <DollarSign className="text-green-500" size={32} />
                    </div>
                </Card>

                <Card>
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm text-gray-600">Speedup</p>
                            <p className="text-2xl font-bold text-purple-600">
                                {mockCostSavings.performance.speedup_factor}x
                            </p>
                        </div>
                        <Zap className="text-purple-500" size={32} />
                    </div>
                </Card>
            </div>

            {/* Cost Savings Chart */}
            <Card title="Monthly Cost Comparison">
                <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={costComparisonData}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="name" />
                            <YAxis />
                            <Tooltip />
                            <Legend />
                            <Bar dataKey="cost" name="Cost (USD)" />
                        </BarChart>
                    </ResponsiveContainer>
                </div>
                <div className="mt-4 p-4 bg-green-50 rounded-lg">
                    <p className="text-sm text-green-900">
                        💰 <strong>Savings:</strong> ${mockCostSavings.estimated_monthly_cost.savings_usd}/month
                        ({mockCostSavings.estimated_monthly_cost.savings_pct}% reduction)
                    </p>
                </div>
            </Card>

            {/* Storage Usage */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <Card title="Storage Usage by Location">
                    <div className="h-64">
                        <ResponsiveContainer width="100%" height="100%">
                            <PieChart>
                                <Pie
                                    data={storageData}
                                    cx="50%"
                                    cy="50%"
                                    labelLine={false}
                                    label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                                    outerRadius={80}
                                    fill="#8884d8"
                                    dataKey="value"
                                >
                                    {storageData.map((_, index) => (
                                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                    ))}
                                </Pie>
                                <Tooltip />
                            </PieChart>
                        </ResponsiveContainer>
                    </div>
                    <div className="mt-4">
                        <p className="text-sm text-gray-600">
                            Total: {mockStorage.total_size_gb.toFixed(2)} GB ({mockStorage.total_files} files)
                        </p>
                    </div>
                </Card>

                {/* Scheduler Control */}
                <Card title="Scheduler Status">
                    <div className="space-y-4">
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                                {mockSchedulerStatus.is_running ? (
                                    <CheckCircle className="text-green-500" size={20} />
                                ) : (
                                    <XCircle className="text-red-500" size={20} />
                                )}
                                <span className="font-medium">
                                    {mockSchedulerStatus.is_running ? 'Running' : 'Stopped'}
                                </span>
                            </div>
                            <Badge variant={mockSchedulerStatus.is_running ? 'success' : 'danger'}>
                                {mockSchedulerStatus.is_running ? 'Active' : 'Inactive'}
                            </Badge>
                        </div>

                        <div className="grid grid-cols-2 gap-4 text-sm">
                            <div>
                                <p className="text-gray-600">Schedule Time</p>
                                <p className="font-medium flex items-center gap-1">
                                    <Clock size={16} />
                                    {mockSchedulerStatus.schedule_time}
                                </p>
                            </div>
                            {mockSchedulerStatus.last_update && (
                                <>
                                    <div>
                                        <p className="text-gray-600">Last Update</p>
                                        <p className="font-medium text-green-600">
                                            {mockSchedulerStatus.last_update.successful} successful
                                        </p>
                                    </div>
                                    <div>
                                        <p className="text-gray-600">Duration</p>
                                        <p className="font-medium">
                                            {mockSchedulerStatus.last_update.duration_seconds.toFixed(1)}s
                                        </p>
                                    </div>
                                    <div>
                                        <p className="text-gray-600">Failed</p>
                                        <p className="font-medium text-red-600">
                                            {mockSchedulerStatus.last_update.failed}
                                        </p>
                                    </div>
                                </>
                            )}
                        </div>

                        <div className="flex gap-2 pt-4 border-t">
                            <Button
                                onClick={() => handleSchedulerAction('start')}
                                disabled={mockSchedulerStatus.is_running || isLoading}
                                className="flex items-center gap-2 flex-1"
                            >
                                <Play size={16} />
                                Start
                            </Button>
                            <Button
                                onClick={() => handleSchedulerAction('stop')}
                                disabled={!mockSchedulerStatus.is_running || isLoading}
                                className="flex items-center gap-2 flex-1"
                                variant="secondary"
                            >
                                <Square size={16} />
                                Stop
                            </Button>
                            <Button
                                onClick={() => handleSchedulerAction('run')}
                                disabled={isLoading}
                                className="flex items-center gap-2 flex-1"
                            >
                                <RefreshCw size={16} />
                                Run Now
                            </Button>
                        </div>
                    </div>
                </Card>
            </div>

            {/* Performance Metrics */}
            <Card title="Performance Improvements">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="p-4 bg-blue-50 rounded-lg">
                        <p className="text-sm text-blue-900 font-medium">API Call Reduction</p>
                        <p className="text-2xl font-bold text-blue-600">
                            {mockCostSavings.api_calls.reduction_pct.toFixed(2)}%
                        </p>
                        <p className="text-xs text-blue-700 mt-1">
                            {mockCostSavings.api_calls.before_per_day.toLocaleString()} → {mockCostSavings.api_calls.after_per_day} calls/day
                        </p>
                    </div>

                    <div className="p-4 bg-purple-50 rounded-lg">
                        <p className="text-sm text-purple-900 font-medium">Query Speedup</p>
                        <p className="text-2xl font-bold text-purple-600">
                            {mockCostSavings.performance.speedup_factor}x
                        </p>
                        <p className="text-xs text-purple-700 mt-1">
                            2-5 seconds → 0.1 seconds
                        </p>
                    </div>

                    <div className="p-4 bg-green-50 rounded-lg">
                        <p className="text-sm text-green-900 font-medium">Annual Savings</p>
                        <p className="text-2xl font-bold text-green-600">
                            ${(mockCostSavings.estimated_monthly_cost.savings_usd * 12).toFixed(2)}
                        </p>
                        <p className="text-xs text-green-700 mt-1">
                            ${mockCostSavings.estimated_monthly_cost.savings_usd}/month
                        </p>
                    </div>
                </div>
            </Card>
        </div>
    );
};

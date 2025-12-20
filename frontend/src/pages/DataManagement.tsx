/**
 * Data Management Page
 * 
 * 통합 데이터 관리 - News DB 스타일
 * - 주가 DB 현황 및 동기화
 * - 뉴스 DB 현황
 * - 섹터별 Top Movers
 */

import React, { useState, useEffect } from 'react';
import {
    Database, RefreshCw, TrendingUp, TrendingDown,
    ChevronDown, ChevronRight, Search, Download, Trash2,
    BarChart3, Newspaper, Activity
} from 'lucide-react';
import { Card } from '../components/common/Card';

// Types
interface SectorStats {
    total: number;
    synced: number;
    percent: number;
}

interface StockStats {
    total_rows: number;
    synced_stocks: number;
    total_sp500: number;
    coverage_percent: number;
    sectors: Record<string, SectorStats>;
}

interface TopMover {
    ticker: string;
    price: number;
    change_pct: number;
}

interface SectorMovers {
    gainers: TopMover[];
    losers: TopMover[];
}

type TabType = 'stocks' | 'news' | 'cache';

export const DataManagement: React.FC = () => {
    const [activeTab, setActiveTab] = useState<TabType>('stocks');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Stock data
    const [stockStats, setStockStats] = useState<StockStats | null>(null);
    const [topMovers, setTopMovers] = useState<Record<string, SectorMovers>>({});
    const [expandedSectors, setExpandedSectors] = useState<Set<string>>(new Set());

    // Sync state
    const [syncingSector, setSyncingSector] = useState<string | null>(null);

    // Load data
    const loadData = async () => {
        setLoading(true);
        setError(null);

        try {
            // Load stock stats
            const statsRes = await fetch('/api/stock-prices/stats');
            if (statsRes.ok) {
                const stats = await statsRes.json();
                setStockStats(stats);
            }

            // Load top movers
            const moversRes = await fetch('/api/stock-prices/sectors/top-movers');
            if (moversRes.ok) {
                const movers = await moversRes.json();
                setTopMovers(movers.sectors || {});
            }
        } catch (err) {
            console.error('Load error:', err);
            setError('데이터 로드 실패');
        } finally {
            setLoading(false);
        }
    };

    // Sync sector
    const syncSector = async (sector: string) => {
        setSyncingSector(sector);
        try {
            const res = await fetch('/api/stock-prices/sync', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ sector }),
            });
            if (res.ok) {
                await loadData();
            }
        } catch (err) {
            console.error('Sync error:', err);
        } finally {
            setSyncingSector(null);
        }
    };

    // Toggle sector expansion
    const toggleSector = (sector: string) => {
        const newExpanded = new Set(expandedSectors);
        if (newExpanded.has(sector)) {
            newExpanded.delete(sector);
        } else {
            newExpanded.add(sector);
        }
        setExpandedSectors(newExpanded);
    };

    useEffect(() => {
        loadData();
    }, []);

    return (
        <div className="p-6 space-y-6">
            {/* Header */}
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900">Data Management</h1>
                    <p className="text-gray-600 mt-1">주가, 뉴스, 캐시 데이터 통합 관리</p>
                </div>
                <button
                    onClick={loadData}
                    disabled={loading}
                    className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-white disabled:opacity-50"
                >
                    <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                    새로고침
                </button>
            </div>

            {error && (
                <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
                    {error}
                </div>
            )}

            {/* Tab Navigation */}
            <div className="flex border-b border-gray-200">
                {[
                    { key: 'stocks', icon: BarChart3, label: '주가 DB' },
                    { key: 'news', icon: Newspaper, label: '뉴스 DB' },
                    { key: 'cache', icon: Activity, label: '캐시' },
                ].map(({ key, icon: Icon, label }) => (
                    <button
                        key={key}
                        onClick={() => setActiveTab(key as TabType)}
                        className={`flex items-center gap-2 px-6 py-3 border-b-2 -mb-px transition-colors ${activeTab === key
                                ? 'border-blue-600 text-blue-600'
                                : 'border-transparent text-gray-600 hover:text-gray-900'
                            }`}
                    >
                        <Icon size={18} />
                        {label}
                    </button>
                ))}
            </div>

            {/* Stock DB Tab */}
            {activeTab === 'stocks' && (
                <div className="space-y-6">
                    {/* Overview Stats */}
                    {stockStats && (
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                            <Card className="bg-blue-50">
                                <div className="flex items-center gap-3">
                                    <Database className="w-8 h-8 text-blue-600" />
                                    <div>
                                        <p className="text-sm text-gray-600">Total Rows</p>
                                        <p className="text-xl font-bold text-gray-900">
                                            {stockStats.total_rows.toLocaleString()}
                                        </p>
                                    </div>
                                </div>
                            </Card>
                            <Card className="bg-green-50">
                                <div className="flex items-center gap-3">
                                    <TrendingUp className="w-8 h-8 text-green-600" />
                                    <div>
                                        <p className="text-sm text-gray-600">Synced Stocks</p>
                                        <p className="text-xl font-bold text-gray-900">
                                            {stockStats.synced_stocks} / {stockStats.total_sp500}
                                        </p>
                                    </div>
                                </div>
                            </Card>
                            <Card className="bg-purple-50">
                                <div className="flex items-center gap-3">
                                    <Activity className="w-8 h-8 text-purple-600" />
                                    <div>
                                        <p className="text-sm text-gray-600">Coverage</p>
                                        <p className="text-xl font-bold text-gray-900">
                                            {stockStats.coverage_percent}%
                                        </p>
                                    </div>
                                </div>
                            </Card>
                            <Card className="bg-orange-50">
                                <div className="flex items-center gap-3">
                                    <BarChart3 className="w-8 h-8 text-orange-600" />
                                    <div>
                                        <p className="text-sm text-gray-600">Sectors</p>
                                        <p className="text-xl font-bold text-gray-900">
                                            {Object.keys(stockStats.sectors).length}
                                        </p>
                                    </div>
                                </div>
                            </Card>
                        </div>
                    )}

                    {/* Sector List */}
                    <Card>
                        <h2 className="text-lg font-semibold mb-4">섹터별 현황</h2>
                        <div className="space-y-2">
                            {stockStats && Object.entries(stockStats.sectors).map(([sector, stats]) => (
                                <div key={sector} className="border rounded-lg overflow-hidden">
                                    <div
                                        className="flex items-center justify-between p-3 bg-gray-50 cursor-pointer hover:bg-gray-100"
                                        onClick={() => toggleSector(sector)}
                                    >
                                        <div className="flex items-center gap-3">
                                            {expandedSectors.has(sector) ? (
                                                <ChevronDown className="w-5 h-5 text-gray-500" />
                                            ) : (
                                                <ChevronRight className="w-5 h-5 text-gray-500" />
                                            )}
                                            <span className="font-medium">{sector}</span>
                                            <span className="text-sm text-gray-500">
                                                {stats.synced} / {stats.total} ({stats.percent}%)
                                            </span>
                                        </div>
                                        <div className="flex items-center gap-2">
                                            {/* Progress bar */}
                                            <div className="w-32 h-2 bg-gray-200 rounded-full overflow-hidden">
                                                <div
                                                    className="h-full bg-blue-600 rounded-full"
                                                    style={{ width: `${stats.percent}%` }}
                                                />
                                            </div>
                                            <button
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    syncSector(sector);
                                                }}
                                                disabled={syncingSector === sector}
                                                className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
                                            >
                                                {syncingSector === sector ? (
                                                    <RefreshCw className="w-4 h-4 animate-spin" />
                                                ) : (
                                                    'Sync'
                                                )}
                                            </button>
                                        </div>
                                    </div>

                                    {/* Expanded sector details */}
                                    {expandedSectors.has(sector) && topMovers[sector] && (
                                        <div className="p-4 border-t bg-white">
                                            <div className="grid grid-cols-2 gap-4">
                                                {/* Top Gainers */}
                                                <div>
                                                    <h4 className="text-sm font-medium text-green-600 mb-2">
                                                        🚀 Top 3 상승
                                                    </h4>
                                                    {topMovers[sector].gainers.map((stock) => (
                                                        <div
                                                            key={stock.ticker}
                                                            className="flex justify-between py-1 text-sm"
                                                        >
                                                            <span className="font-medium">{stock.ticker}</span>
                                                            <span className="text-green-600">+{stock.change_pct}%</span>
                                                        </div>
                                                    ))}
                                                    {topMovers[sector].gainers.length === 0 && (
                                                        <p className="text-gray-400 text-sm">데이터 없음</p>
                                                    )}
                                                </div>

                                                {/* Top Losers */}
                                                <div>
                                                    <h4 className="text-sm font-medium text-red-600 mb-2">
                                                        📉 Top 3 하락
                                                    </h4>
                                                    {topMovers[sector].losers.map((stock) => (
                                                        <div
                                                            key={stock.ticker}
                                                            className="flex justify-between py-1 text-sm"
                                                        >
                                                            <span className="font-medium">{stock.ticker}</span>
                                                            <span className="text-red-600">{stock.change_pct}%</span>
                                                        </div>
                                                    ))}
                                                    {topMovers[sector].losers.length === 0 && (
                                                        <p className="text-gray-400 text-sm">데이터 없음</p>
                                                    )}
                                                </div>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    </Card>
                </div>
            )}

            {/* News DB Tab */}
            {activeTab === 'news' && (
                <Card>
                    <div className="text-center py-12 text-gray-500">
                        <Newspaper className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                        <p>뉴스 DB 관리 기능 준비 중...</p>
                        <p className="text-sm mt-2">PostgreSQL 마이그레이션 후 활성화됩니다.</p>
                    </div>
                </Card>
            )}

            {/* Cache Tab */}
            {activeTab === 'cache' && (
                <Card>
                    <div className="text-center py-12 text-gray-500">
                        <Activity className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                        <p>캐시 관리 기능 준비 중...</p>
                        <p className="text-sm mt-2">Redis 설정 후 활성화됩니다.</p>
                    </div>
                </Card>
            )}
        </div>
    );
};

export default DataManagement;

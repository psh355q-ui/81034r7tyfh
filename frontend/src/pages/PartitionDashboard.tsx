import React, { useEffect, useState } from 'react';
import { partitionsApi, PartitionSummary, LeverageCheckResponse } from '../services/partitionsApi';

const PartitionDashboard: React.FC = () => {
    const [summary, setSummary] = useState<PartitionSummary | null>(null);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

    const [tickerCheck, setTickerCheck] = useState('');
    const [leverageCheckResult, setLeverageCheckResult] = useState<LeverageCheckResponse | null>(null);

    const fetchData = async () => {
        try {
            setLoading(true);
            const data = await partitionsApi.getSummary();
            setSummary(data);
            setError(null);
        } catch (err) {
            setError('Failed to load partition data');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 30000); // Refresh every 30s
        return () => clearInterval(interval);
    }, []);

    const handleCheckLeverage = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!tickerCheck) return;
        try {
            const res = await partitionsApi.checkLeverage(tickerCheck);
            setLeverageCheckResult(res);
        } catch (err) {
            console.error(err);
        }
    };

    if (loading && !summary) return <div className="p-8 text-white">Loading Partitions...</div>;
    if (error) return <div className="p-8 text-red-500">{error}</div>;

    const wallets = summary?.wallets;

    return (
        <div className="min-h-screen bg-gray-900 text-gray-100 p-6 space-y-6">
            <header className="flex justify-between items-center mb-8">
                <div>
                    <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-500">
                        Account Partitions
                    </h1>
                    <p className="text-gray-400 mt-2">Autonomous Portfolio Management System</p>
                </div>
                <div className="text-right">
                    <div className="text-2xl font-mono text-green-400">
                        ${summary?.total_equity.toLocaleString()}
                    </div>
                    <div className="text-sm text-gray-500">Total Equity</div>
                </div>
            </header>

            {/* Wallet Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {wallets && Object.values(wallets).map((wallet) => (
                    <div
                        key={wallet.wallet}
                        className={`p-6 rounded-xl border border-gray-700 bg-gray-800 relative overflow-hidden transition-all hover:border-gray-500
                            ${wallet.wallet === 'core' ? 'border-l-4 border-l-blue-500' : ''}
                            ${wallet.wallet === 'income' ? 'border-l-4 border-l-green-500' : ''}
                            ${wallet.wallet === 'satellite' ? 'border-l-4 border-l-purple-500' : ''}
                        `}
                    >
                        <div className="flex justify-between items-start mb-4">
                            <h2 className="text-xl font-bold uppercase tracking-wider">{wallet.wallet}</h2>
                            <span className="text-xs bg-gray-700 px-2 py-1 rounded">
                                Target: {wallet.target_pct * 100}%
                            </span>
                        </div>

                        <div className="space-y-4">
                            <div>
                                <div className="flex justify-between text-sm mb-1">
                                    <span className="text-gray-400">Current Allocation</span>
                                    <span className={wallet.deviation > 0.05 ? 'text-yellow-400' : 'text-blue-400'}>
                                        {(wallet.current_pct * 100).toFixed(1)}%
                                    </span>
                                </div>
                                <div className="w-full bg-gray-700 rounded-full h-2">
                                    <div
                                        className={`h-2 rounded-full ${wallet.wallet === 'core' ? 'bg-blue-500' :
                                                wallet.wallet === 'income' ? 'bg-green-500' : 'bg-purple-500'
                                            }`}
                                        style={{ width: `${Math.min(wallet.current_pct * 100, 100)}%` }}
                                    ></div>
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-4 text-sm">
                                <div>
                                    <span className="block text-gray-500">Value</span>
                                    <span className="font-mono text-lg">${wallet.current_value.toLocaleString()}</span>
                                </div>
                                <div>
                                    <span className="block text-gray-500">Cash</span>
                                    <span className="font-mono text-lg text-gray-300">${wallet.cash.toLocaleString()}</span>
                                </div>
                            </div>

                            {wallet.needs_rebalance && (
                                <div className="bg-yellow-900/30 text-yellow-500 text-xs p-2 rounded border border-yellow-800 mt-2 text-center">
                                    ⚠️ Rebalance Needed
                                </div>
                            )}
                        </div>
                    </div>
                ))}
            </div>

            {/* Leverage Guardian & Shadow Stats */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">

                {/* Leverage Checker */}
                <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
                    <h3 className="text-lg font-bold mb-4 flex items-center">
                        🛡️ Leverage Guardian Checker
                    </h3>
                    <form onSubmit={handleCheckLeverage} className="flex gap-4 mb-4">
                        <input
                            type="text"
                            value={tickerCheck}
                            onChange={(e) => setTickerCheck(e.target.value.toUpperCase())}
                            placeholder="Check Ticker (e.g. TQQQ)"
                            className="bg-gray-700 text-white px-4 py-2 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 flex-grow"
                        />
                        <button type="submit" className="bg-blue-600 hover:bg-blue-500 px-6 py-2 rounded font-medium">
                            Check
                        </button>
                    </form>

                    {leverageCheckResult && (
                        <div className={`p-4 rounded border ${leverageCheckResult.is_leveraged ? 'bg-purple-900/20 border-purple-500/50' : 'bg-green-900/20 border-green-500/50'
                            }`}>
                            <div className="flex items-center gap-2 mb-2">
                                <span className="font-bold text-lg">{leverageCheckResult.ticker}</span>
                                {leverageCheckResult.is_leveraged ?
                                    <span className="bg-purple-600 text-white text-xs px-2 py-0.5 rounded">LEVERAGED ({leverageCheckResult.leverage_ratio}x)</span> :
                                    <span className="bg-green-600 text-white text-xs px-2 py-0.5 rounded">SAFE</span>
                                }
                            </div>
                            <p className="text-sm text-gray-300 mb-2">
                                Allowed Wallets: <span className="text-white font-mono">{leverageCheckResult.allowed_wallets.join(', ')}</span>
                            </p>
                            <p className="text-xs text-gray-400">{leverageCheckResult.note}</p>
                        </div>
                    )}
                </div>

                {/* Shadow Trading Status */}
                <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
                    <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                        👻 Shadow Trading Status
                        <span className="flex h-2 w-2 relative">
                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                            <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                        </span>
                    </h3>

                    <div className="space-y-4">
                        <div className="flex justify-between items-center border-b border-gray-700 pb-2">
                            <span className="text-gray-400">Mode</span>
                            <span className="text-green-400 font-mono">AUTONOMOUS</span>
                        </div>
                        <div className="flex justify-between items-center border-b border-gray-700 pb-2">
                            <span className="text-gray-400">Price Source</span>
                            <span className="text-blue-400">KIS Real-time</span>
                        </div>
                        <div className="flex justify-between items-center">
                            <span className="text-gray-400">Last Action</span>
                            <span className="text-gray-500 italic">Monitoring news...</span>
                            {/* TODO: Connect to WebSocket logs */}
                        </div>
                    </div>
                </div>
            </div>

            {/* Disclaimer */}
            <div className="text-center text-xs text-gray-600 mt-12 pb-4">
                AI Trading System v2.0 • Shadow Mode Active • Not Investment Advice
            </div>
        </div>
    );
};

export default PartitionDashboard;

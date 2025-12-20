import React, { useState, useEffect } from 'react';
import { Play, TrendingUp, Users, BarChart2 } from 'lucide-react';

interface ConsensusConfig {
    start_date: string;
    end_date: string;
    top_n: number;
    voting_threshold: number;
    initial_capital: number;
}

interface ConsensusResult {
    id: string;
    config: ConsensusConfig;
    total_return: number;
    win_rate: number;
    total_trades: number;
    strong_consensus_count: number;
    created_at: string;
}

export const ConsensusBacktest: React.FC = () => {
    const [results, setResults] = useState<ConsensusResult[]>([]);
    const [loading, setLoading] = useState(false);
    const [config, setConfig] = useState<ConsensusConfig>({
        start_date: '2024-01-01',
        end_date: '2024-01-31',
        top_n: 10,
        voting_threshold: 0.7,
        initial_capital: 100000
    });

    const fetchResults = async () => {
        try {
            const res = await fetch('/backtest/consensus/list');
            if (res.ok) {
                const data = await res.json();
                setResults(data);
            }
        } catch (e) {
            console.error(e);
        }
    };

    useEffect(() => {
        fetchResults();
    }, []);

    const runBacktest = async () => {
        setLoading(true);
        try {
            const res = await fetch('/backtest/consensus', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(config)
            });
            if (res.ok) {
                await fetchResults();
            } else {
                alert('Backtest failed');
            }
        } catch (e) {
            alert('Error running backtest');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="space-y-6">
            {/* Config Panel */}
            <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                    <Users className="w-5 h-5 text-blue-500" />
                    Consensus Strategy Configuration
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
                    <div>
                        <label className="block text-sm text-gray-600 mb-1">Start Date</label>
                        <input type="date" value={config.start_date} onChange={e => setConfig({ ...config, start_date: e.target.value })} className="w-full border rounded p-2" />
                    </div>
                    <div>
                        <label className="block text-sm text-gray-600 mb-1">End Date</label>
                        <input type="date" value={config.end_date} onChange={e => setConfig({ ...config, end_date: e.target.value })} className="w-full border rounded p-2" />
                    </div>
                    <div>
                        <label className="block text-sm text-gray-600 mb-1">Top N Assets</label>
                        <input type="number" value={config.top_n} onChange={e => setConfig({ ...config, top_n: parseInt(e.target.value) })} className="w-full border rounded p-2" />
                    </div>
                    <div>
                        <label className="block text-sm text-gray-600 mb-1">Voting Threshold</label>
                        <input type="number" step="0.1" value={config.voting_threshold} onChange={e => setConfig({ ...config, voting_threshold: parseFloat(e.target.value) })} className="w-full border rounded p-2" />
                    </div>
                    <div className="flex items-end">
                        <button
                            onClick={runBacktest}
                            disabled={loading}
                            className="w-full bg-blue-600 text-white rounded p-2 hover:bg-blue-700 disabled:opacity-50 flex justify-center items-center gap-2"
                        >
                            {loading ? <div className="animate-spin w-4 h-4 border-2 border-white rounded-full border-t-transparent"></div> : <Play className="w-4 h-4" />}
                            Run Test
                        </button>
                    </div>
                </div>
            </div>

            {/* Results List */}
            <div className="bg-white rounded-lg shadow overflow-hidden">
                <div className="p-4 border-b">
                    <h3 className="text-lg font-semibold flex items-center gap-2">
                        <BarChart2 className="w-5 h-5 text-purple-500" />
                        Backtest Results
                    </h3>
                </div>
                <table className="w-full text-sm text-left">
                    <thead className="bg-gray-50 text-gray-600 uppercase">
                        <tr>
                            <th className="px-6 py-3">Date</th>
                            <th className="px-6 py-3">Period</th>
                            <th className="px-6 py-3">Return</th>
                            <th className="px-6 py-3">Win Rate</th>
                            <th className="px-6 py-3">Trades</th>
                            <th className="px-6 py-3">Consensus Str</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                        {results.length === 0 ? (
                            <tr><td colSpan={6} className="px-6 py-8 text-center text-gray-500">No results found</td></tr>
                        ) : (
                            results.map(r => (
                                <tr key={r.id} className="hover:bg-gray-50">
                                    <td className="px-6 py-4">{new Date(r.created_at).toLocaleString()}</td>
                                    <td className="px-6 py-4">{r.config.start_date} ~ {r.config.end_date}</td>
                                    <td className={`px-6 py-4 font-bold ${r.total_return >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                        {(r.total_return * 100).toFixed(2)}%
                                    </td>
                                    <td className="px-6 py-4">{(r.win_rate * 100).toFixed(1)}%</td>
                                    <td className="px-6 py-4">{r.total_trades}</td>
                                    <td className="px-6 py-4">{r.strong_consensus_count} signals</td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

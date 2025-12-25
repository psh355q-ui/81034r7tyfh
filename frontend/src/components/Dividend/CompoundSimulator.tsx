import React, { useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { TrendingUp } from 'lucide-react';

const CompoundSimulator: React.FC = () => {
    const [results, setResults] = useState<any[]>([]);
    const [loading, setLoading] = useState(false);
    const [formData, setFormData] = useState({
        initial: 100000,
        monthly: 1000,
        years: 10,
        cagr: 7,
        yield: 4,
        reinvest: true
    });

    const onSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        try {
            const response = await fetch('http://localhost:8001/api/dividend/simulate/drip', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    initial_usd: formData.initial,
                    monthly_contribution_usd: formData.monthly,
                    years: formData.years,
                    cagr: formData.cagr,
                    dividend_yield: formData.yield,
                    reinvest: formData.reinvest
                })
            });

            if (!response.ok) throw new Error('Failed to simulate');

            const data = await response.json();
            setResults(data.results || []);
        } catch (error: any) {
            console.error('Simulation failed:', error.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="space-y-6">
            <div>
                <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2 mb-2">
                    <TrendingUp size={20} className="text-green-600" />
                    DRIP 복리 시뮬레이터
                </h3>
                <p className="text-sm text-gray-600">배당 재투자 시 포트폴리오 성장 예측</p>
            </div>

            <div className="bg-white rounded-lg border border-gray-200 p-6">
                <form onSubmit={onSubmit} className="grid grid-cols-2 md:grid-cols-3 gap-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">초기 투자 (USD)</label>
                        <input
                            type="number"
                            value={formData.initial}
                            onChange={(e) => setFormData({ ...formData, initial: Number(e.target.value) })}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                            step="10000"
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">월 적립 (USD)</label>
                        <input
                            type="number"
                            value={formData.monthly}
                            onChange={(e) => setFormData({ ...formData, monthly: Number(e.target.value) })}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                            step="100"
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">기간 (년)</label>
                        <input
                            type="number"
                            value={formData.years}
                            onChange={(e) => setFormData({ ...formData, years: Number(e.target.value) })}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                            min="1"
                            max="30"
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">CAGR (%)</label>
                        <input
                            type="number"
                            value={formData.cagr}
                            onChange={(e) => setFormData({ ...formData, cagr: Number(e.target.value) })}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                            step="0.5"
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">배당률 (%)</label>
                        <input
                            type="number"
                            value={formData.yield}
                            onChange={(e) => setFormData({ ...formData, yield: Number(e.target.value) })}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                            step="0.5"
                        />
                    </div>
                    <div className="flex items-end">
                        <label className="flex items-center space-x-2">
                            <input
                                type="checkbox"
                                checked={formData.reinvest}
                                onChange={(e) => setFormData({ ...formData, reinvest: e.target.checked })}
                                className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                            />
                            <span className="text-sm font-medium text-gray-700">배당 재투자</span>
                        </label>
                    </div>
                    <div className="col-span-full">
                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 transition-colors"
                        >
                            {loading ? '시뮬레이션 중...' : '시뮬레이션'}
                        </button>
                    </div>
                </form>
            </div>

            {results.length > 0 && (
                <div className="bg-white rounded-lg border border-gray-200 p-6">
                    <ResponsiveContainer width="100%" height={400}>
                        <LineChart data={results}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                            <XAxis dataKey="year" stroke="#6b7280" />
                            <YAxis stroke="#6b7280" tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`} />
                            <Tooltip
                                contentStyle={{ backgroundColor: '#fff', border: '1px solid #e5e7eb', borderRadius: '6px' }}
                                formatter={(value: any) => `$${value.toLocaleString()}`}
                            />
                            <Legend />
                            <Line type="monotone" dataKey="portfolio_value_usd" stroke="#10b981" name="Portfolio Value" strokeWidth={2} />
                            <Line type="monotone" dataKey="cumulative_dividends_usd" stroke="#3b82f6" name="Cumulative Dividends" strokeWidth={2} />
                        </LineChart>
                    </ResponsiveContainer>
                </div>
            )}
        </div>
    );
};

export default CompoundSimulator;

import React, { useState, useEffect } from 'react';
import { Shield } from 'lucide-react';

const RiskScoreTable: React.FC = () => {
    const [tickers] = useState(['JNJ', 'PG', 'KO', 'T', 'O']);
    const [riskData, setRiskData] = useState<any[]>([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        fetchRiskScores();
    }, []);

    const fetchRiskScores = async () => {
        setLoading(true);
        try {
            const promises = tickers.map(ticker =>
                fetch(`http://localhost:8001/api/dividend/risk/${ticker}`)
                    .then(res => res.ok ? res.json() : null)
            );

            const results = await Promise.all(promises);
            setRiskData(results.filter(Boolean));
        } catch (error) {
            console.error('Risk fetch error:', error);
        } finally {
            setLoading(false);
        }
    };

    const getRiskColor = (score: number) => {
        if (score < 30) return 'text-green-600 bg-green-50';
        if (score < 60) return 'text-orange-600 bg-orange-50';
        return 'text-red-600 bg-red-50';
    };

    const getRiskLevel = (level: string) => {
        switch (level) {
            case 'Safe': return { color: 'text-green-700 bg-green-100', text: '안전' };
            case 'Warning': return { color: 'text-orange-700 bg-orange-100', text: '주의' };
            case 'Danger': return { color: 'text-red-700 bg-red-100', text: '위험' };
            default: return { color: 'text-gray-700 bg-gray-100', text: level };
        }
    };

    return (
        <div className="space-y-4">
            <div>
                <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2 mb-2">
                    <Shield size={20} className="text-blue-600" />
                    배당주 리스크 분석
                </h3>
                <p className="text-sm text-gray-600">배당 지속 가능성 평가 (0-100, 낮을수록 안전)</p>
            </div>

            <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Ticker
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Risk Score
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Level
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Payout Ratio
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Debt/Equity
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Sector
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Warnings
                                </th>
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                            {loading ? (
                                <tr>
                                    <td colSpan={7} className="px-6 py-4 text-center text-sm text-gray-500">
                                        Loading...
                                    </td>
                                </tr>
                            ) : riskData.length > 0 ? (
                                riskData.map((data, index) => {
                                    const levelInfo = getRiskLevel(data.risk_level);
                                    return (
                                        <tr key={index} className="hover:bg-gray-50">
                                            <td className="px-6 py-4 whitespace-nowrap">
                                                <span className="font-semibold text-blue-600">{data.ticker}</span>
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap">
                                                <span className={`px-2 py-1 text-xs font-semibold rounded ${getRiskColor(data.risk_score)}`}>
                                                    {data.risk_score}
                                                </span>
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap">
                                                <span className={`px-2 py-1 text-xs font-semibold rounded ${levelInfo.color}`}>
                                                    {levelInfo.text}
                                                </span>
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                                {data.metrics?.payout_ratio ? `${data.metrics.payout_ratio.toFixed(1)}%` : 'N/A'}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                                {data.metrics?.debt_to_equity ? data.metrics.debt_to_equity.toFixed(2) : 'N/A'}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap">
                                                <span className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded">
                                                    {data.sector || 'N/A'}
                                                </span>
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                                {data.warnings?.length || 0}
                                            </td>
                                        </tr>
                                    );
                                })
                            ) : (
                                <tr>
                                    <td colSpan={7} className="px-6 py-4 text-center text-sm text-gray-500">
                                        No data available
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

export default RiskScoreTable;

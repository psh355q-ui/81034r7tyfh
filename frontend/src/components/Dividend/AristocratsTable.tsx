import React, { useState, useEffect } from 'react';
import { Trophy } from 'lucide-react';

const AristocratsTable: React.FC = () => {
    const [aristocrats, setAristocrats] = useState<any[]>([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        fetchAristocrats();
    }, []);

    const fetchAristocrats = async () => {
        setLoading(true);
        try {
            const response = await fetch('http://localhost:8001/api/dividend/aristocrats');
            if (!response.ok) throw new Error('Failed to fetch aristocrats');

            const data = await response.json();
            setAristocrats(data.aristocrats || []);
        } catch (error: any) {
            console.error('Failed to fetch aristocrats:', error.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="space-y-4">
            <div>
                <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2 mb-2">
                    <Trophy size={20} className="text-yellow-600" />
                    배당 귀족주 (Dividend Aristocrats)
                </h3>
                <p className="text-sm text-gray-600">
                    25년 이상 연속 배당금을 증가시킨 우량 배당주 ({aristocrats.length}개)
                </p>
            </div>

            <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                            <tr>
                                <th className="px-3 md:px-6 py-2 md:py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Ticker
                                </th>
                                <th className="hidden md:table-cell px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Company
                                </th>
                                <th className="px-3 md:px-6 py-2 md:py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    연속증가
                                </th>
                                <th className="px-3 md:px-6 py-2 md:py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    배당률
                                </th>
                                <th className="hidden lg:table-cell px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Sector
                                </th>
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                            {loading ? (
                                <tr>
                                    <td colSpan={5} className="px-6 py-4 text-center text-sm text-gray-500">
                                        Loading...
                                    </td>
                                </tr>
                            ) : aristocrats.length > 0 ? (
                                aristocrats.map((stock, index) => (
                                    <tr key={index} className="hover:bg-gray-50">
                                        <td className="px-3 md:px-6 py-2 md:py-4 whitespace-nowrap">
                                            <span className="font-semibold text-blue-600 text-sm md:text-base">{stock.ticker}</span>
                                        </td>
                                        <td className="hidden md:table-cell px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                            {stock.company_name}
                                        </td>
                                        <td className="px-3 md:px-6 py-2 md:py-4 whitespace-nowrap">
                                            <span className="px-1.5 md:px-2 py-0.5 md:py-1 text-xs font-semibold bg-green-100 text-green-700 rounded">
                                                {stock.consecutive_years}년
                                            </span>
                                        </td>
                                        <td className="px-3 md:px-6 py-2 md:py-4 whitespace-nowrap text-sm text-gray-900">
                                            {stock.current_yield ? `${stock.current_yield.toFixed(2)}%` : 'N/A'}
                                        </td>
                                        <td className="hidden lg:table-cell px-6 py-4 whitespace-nowrap">
                                            <span className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded">
                                                {stock.sector}
                                            </span>
                                        </td>
                                    </tr>
                                ))
                            ) : (
                                <tr>
                                    <td colSpan={5} className="px-6 py-4 text-center text-sm text-gray-500">
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

export default AristocratsTable;

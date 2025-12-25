/**
 * AristocratsTable.tsx - 배당 귀족주 테이블
 * 
 * 📊 Data Sources:
 *   - API: GET /api/dividend/aristocrats
 *     - Returns: aristocrats[], last_updated, next_update, data_source
 *   - Yahoo Finance 분석 데이터 (DB 캐시)
 * 
 * 🔗 Dependencies:
 *   - react: useState, useEffect
 *   - lucide-react: Trophy 아이콘
 * 
 * 📤 Components Used:
 *   - None (leaf component)
 * 
 * 🔄 Used By:
 *   - pages/DividendDashboard.tsx (aristocrats tab)
 * 
 * 📝 Notes:
 *   - DB cached data (연 1회 갱신, 3월 1일 권장)
 *   - Shows last_updated date (기준일)
 *   - Removed '25년 이상' restriction - shows all dividend growers
 *   - Mobile responsive table
 */

import React, { useState, useEffect } from 'react';
import { Trophy, Calendar } from 'lucide-react';

interface AristocratData {
    ticker: string;
    company_name: string;
    sector: string;
    consecutive_years: number;
    current_yield: number;
    growth_rate: number;
}

interface AristocratsResponse {
    count: number;
    aristocrats: AristocratData[];
    last_updated?: string;  // ISO datetime
    next_update?: string;   // YYYY-MM-DD
    data_source?: string;   // "database" or "yahoo_finance"
}

const AristocratsTable: React.FC = () => {
    const [data, setData] = useState<AristocratsResponse | null>(null);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        fetchAristocrats();
    }, []);

    const fetchAristocrats = async () => {
        setLoading(true);
        try {
            const response = await fetch('http://localhost:8001/api/dividend/aristocrats');
            if (!response.ok) throw new Error('Failed to fetch aristocrats');

            const responseData = await response.json();
            setData(responseData);
        } catch (error: any) {
            console.error('Failed to fetch aristocrats:', error.message);
        } finally {
            setLoading(false);
        }
    };

    const formatDate = (isoString?: string) => {
        if (!isoString) return 'N/A';
        try {
            const date = new Date(isoString);
            return date.toLocaleDateString('ko-KR', {
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            });
        } catch {
            return 'N/A';
        }
    };

    const aristocrats = data?.aristocrats || [];

    return (
        <div className="space-y-4">
            <div>
                <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2 mb-2">
                    <Trophy size={20} className="text-yellow-600" />
                    배당 귀족주 (Dividend Aristocrats)
                </h3>
                <p className="text-sm text-gray-600">
                    연속 배당금을 증가시킨 우량 배당주 ({aristocrats.length}개)
                </p>

                {/* 기준일 표시 */}
                {data?.last_updated && (
                    <div className="flex items-center gap-2 mt-2 text-xs text-gray-500">
                        <Calendar size={14} />
                        <span>
                            기준일: {formatDate(data.last_updated)}
                            {data.next_update && (
                                <span className="ml-2 text-blue-600">
                                    (다음 갱신: {data.next_update})
                                </span>
                            )}
                        </span>
                    </div>
                )}
            </div>

            <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                            <tr>
                                <th className="px-3 md:px-6 py-2 md:py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    티커
                                </th>
                                <th className="hidden md:table-cell px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    회사명
                                </th>
                                <th className="px-3 md:px-6 py-2 md:py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    연속증가
                                </th>
                                <th className="px-3 md:px-6 py-2 md:py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    배당률
                                </th>
                                <th className="hidden lg:table-cell px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    섹터
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

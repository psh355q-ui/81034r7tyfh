import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { getMarketIndicators } from '../services/api';
import { Card } from './common/Card';
import { TrendingUp, TrendingDown } from 'lucide-react';

export const MarketIndicators: React.FC = () => {
    const { data, isLoading, isError } = useQuery({
        queryKey: ['marketIndicators'],
        queryFn: getMarketIndicators,
        refetchInterval: 30000, // 30초마다 갱신
    });

    if (isLoading) {
        return (
            <Card className="mb-6">
                <h2 className="text-lg font-bold text-gray-900 mb-4">📊 Major Market Indicators</h2>
                <div className="flex items-center justify-center py-8">
                    <div className="text-gray-500">Loading market data...</div>
                </div>
            </Card>
        );
    }

    if (isError || !data?.success) {
        return null; // Silent fail
    }

    const indicators = data.data;

    const IndicatorCard = ({
        indicator,
        isYield = false,
        isCurrency = false
    }: {
        indicator: any;
        isYield?: boolean;
        isCurrency?: boolean;
    }) => {
        const changeValue = isYield || isCurrency ? indicator.change_bp : indicator.change;
        const isPositive = changeValue > 0;

        let displayChange = '';
        if (isYield) {
            displayChange = `${changeValue > 0 ? '+' : ''}${changeValue.toFixed(1)}bp`;
        } else if (isCurrency) {
            // For currencies, show absolute change
            displayChange = `${indicator.change > 0 ? '+' : ''}${indicator.change.toFixed(2)}`;
        } else {
            displayChange = `${indicator.change_pct > 0 ? '+' : ''}${indicator.change_pct.toFixed(2)}%`;
        }

        return (
            <div className="flex flex-col p-4 bg-white rounded-lg shadow-sm border hover:shadow-md transition-shadow">
                <div className="text-xs text-gray-500 mb-1 font-medium">{indicator.name}</div>
                <div className="text-2xl font-bold text-gray-900 mb-1">
                    {isCurrency
                        ? indicator.price.toFixed(2)
                        : isYield
                            ? `${indicator.price.toFixed(2)}%`
                            : indicator.price.toLocaleString()}
                </div>
                <div className={`flex items-center text-sm font-semibold ${isPositive ? 'text-green-600' : 'text-red-600'
                    }`}>
                    {isPositive ? (
                        <TrendingUp size={16} className="mr-1" />
                    ) : (
                        <TrendingDown size={16} className="mr-1" />
                    )}
                    <span>{displayChange}</span>
                </div>
            </div>
        );
    };

    return (
        <Card className="mb-6 border-l-4 border-l-blue-500">
            <h2 className="text-lg font-bold text-gray-900 mb-4">📊 Major Market Indicators</h2>

            {/* Main Indicators Row */}
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-4">
                <IndicatorCard indicator={indicators.sp500} />
                <IndicatorCard indicator={indicators.nasdaq} />
                <IndicatorCard indicator={indicators.vix} />
                <IndicatorCard indicator={indicators.us10y} isYield />
                <IndicatorCard indicator={indicators.dxy} />
            </div>

            {/* Currency Exchange Rates Row */}
            <div className="pt-4 border-t border-gray-200">
                <h3 className="text-sm font-semibold text-gray-700 mb-3">💱 Currency Rates</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <IndicatorCard indicator={indicators.krw} isCurrency />
                    <IndicatorCard indicator={indicators.jpy} isCurrency />
                    <IndicatorCard indicator={indicators.eur} isCurrency />
                    <IndicatorCard indicator={indicators.cny} isCurrency />
                </div>
            </div>

            <div className="mt-3 text-xs text-gray-400 text-right">
                Last updated: {new Date(data.timestamp).toLocaleTimeString('ko-KR', {
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit'
                })}
            </div>
        </Card>
    );
};

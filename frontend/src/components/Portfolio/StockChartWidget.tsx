/**
 * StockChartWidget - 보유 주식 차트 위젯
 * 
 * Portfolio AI Insights 섹션에서 사용
 * 각 보유 주식의 1시간봉 캔들스틱 차트 표시
 * 
 * @author AI Trading System
 * @date 2026-01-18
 */

import React, { useState, useEffect } from 'react';
import CandlestickChart, { OHLCData, ChartIndicator } from '../common/CandlestickChart';

interface StockChartWidgetProps {
    symbol: string;
    timeframe?: '1h' | '4h' | '1d' | '1w';
    height?: number;
    showIndicators?: boolean;
}

interface ChartResponse {
    symbol: string;
    timeframe: string;
    data: OHLCData[];
    last_updated: string;
}

export const StockChartWidget: React.FC<StockChartWidgetProps> = ({
    symbol,
    timeframe = '1h',
    height = 300,
    showIndicators = true,
}) => {
    const [data, setData] = useState<OHLCData[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [selectedTimeframe, setSelectedTimeframe] = useState(timeframe);

    // Default indicators
    const indicators: ChartIndicator[] = showIndicators ? [
        { type: 'ma', period: 20, color: '#2196f3', visible: true },
        { type: 'ma', period: 50, color: '#ff9800', visible: true },
    ] : [];

    // Fetch chart data
    useEffect(() => {
        const fetchData = async () => {
            setLoading(true);
            setError(null);

            try {
                const response = await fetch(
                    `http://localhost:8001/api/chart/ohlc/${symbol}?timeframe=${selectedTimeframe}`
                );

                if (!response.ok) {
                    throw new Error(`Failed to fetch chart data: ${response.status}`);
                }

                const result: ChartResponse = await response.json();
                setData(result.data);
            } catch (err) {
                console.error('Chart fetch error:', err);
                setError(err instanceof Error ? err.message : 'Failed to load chart');
            } finally {
                setLoading(false);
            }
        };

        if (symbol) {
            fetchData();
        }
    }, [symbol, selectedTimeframe]);

    // Timeframe options
    const timeframeOptions = [
        { value: '1h', label: '1시간' },
        { value: '4h', label: '4시간' },
        { value: '1d', label: '일봉' },
        { value: '1w', label: '주봉' },
    ];

    if (loading) {
        return (
            <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                height: height,
                backgroundColor: '#1a1a2e',
                borderRadius: '8px',
                color: '#888',
            }}>
                <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: '24px', marginBottom: '8px' }}>📊</div>
                    <div>차트 로딩 중...</div>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                height: height,
                backgroundColor: '#1a1a2e',
                borderRadius: '8px',
                color: '#ef5350',
            }}>
                <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: '24px', marginBottom: '8px' }}>⚠️</div>
                    <div>{error}</div>
                </div>
            </div>
        );
    }

    return (
        <div style={{
            backgroundColor: '#1a1a2e',
            borderRadius: '8px',
            overflow: 'hidden',
        }}>
            {/* Timeframe Selector */}
            <div style={{
                display: 'flex',
                justifyContent: 'flex-end',
                padding: '8px 12px',
                backgroundColor: '#141428',
                borderBottom: '1px solid #2a2a4a',
                gap: '4px',
            }}>
                {timeframeOptions.map(option => (
                    <button
                        key={option.value}
                        onClick={() => setSelectedTimeframe(option.value as '1h' | '4h' | '1d' | '1w')}
                        style={{
                            padding: '4px 12px',
                            fontSize: '12px',
                            border: 'none',
                            borderRadius: '4px',
                            cursor: 'pointer',
                            backgroundColor: selectedTimeframe === option.value ? '#3b82f6' : '#2a2a4a',
                            color: selectedTimeframe === option.value ? '#fff' : '#888',
                            transition: 'all 0.2s',
                        }}
                    >
                        {option.label}
                    </button>
                ))}
            </div>

            {/* Chart */}
            <CandlestickChart
                data={data}
                symbol={symbol}
                timeframe={selectedTimeframe}
                indicators={indicators}
                height={height}
                showVolume={true}
                theme="dark"
            />
        </div>
    );
};

export default StockChartWidget;

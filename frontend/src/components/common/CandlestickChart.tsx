/**
 * CandlestickChart - TradingView Lightweight Charts v5 기반 캔들스틱 차트
 * 
 * Features:
 * - 1시간봉/일봉/주봉 지원
 * - MA(이동평균선) 오버레이
 * - 볼린저 밴드 오버레이
 * - 거래량 패널
 * - 반응형 크기 조절
 * 
 * @author AI Trading System
 * @date 2026-01-18
 */

import React, { useEffect, useRef, useState } from 'react';
import {
    createChart,
    IChartApi,
    ISeriesApi,
    CandlestickSeries,
    LineSeries,
    HistogramSeries,
    CandlestickData,
    LineData,
    HistogramData,
    ColorType,
    Time
} from 'lightweight-charts';

// ============================================================================
// Types
// ============================================================================

export interface OHLCData {
    time: string;  // ISO date string or 'YYYY-MM-DD'
    open: number;
    high: number;
    low: number;
    close: number;
    volume?: number;
}

export interface ChartIndicator {
    type: 'ma' | 'ema' | 'bollinger' | 'rsi' | 'macd';
    period?: number;
    color?: string;
    visible?: boolean;
}

export interface CandlestickChartProps {
    data: OHLCData[];
    symbol?: string;
    timeframe?: '1h' | '4h' | '1d' | '1w';
    indicators?: ChartIndicator[];
    height?: number;
    showVolume?: boolean;
    theme?: 'light' | 'dark';
    onCrosshairMove?: (price: number | null, time: string | null) => void;
}

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Normalize time string to unix timestamp if needed
 */
function normalizeTime(time: string | number): Time {
    if (typeof time === 'number') return time as Time;
    // If string contains time (e.g. '2026-01-08 09:30'), convert to unix timestamp
    if (time.includes(':')) {
        return (new Date(time).getTime() / 1000) as Time;
    }
    return time as Time;
}

/**
 * Calculate Simple Moving Average
 */
function calculateSMA(data: OHLCData[], period: number): LineData<Time>[] {
    const result: LineData<Time>[] = [];
    for (let i = period - 1; i < data.length; i++) {
        let sum = 0;
        for (let j = 0; j < period; j++) {
            sum += data[i - j].close;
        }
        result.push({
            time: normalizeTime(data[i].time),
            value: sum / period,
        });
    }
    return result;
}

/**
 * Calculate Exponential Moving Average
 */
function calculateEMA(data: OHLCData[], period: number): LineData<Time>[] {
    const result: LineData<Time>[] = [];
    const multiplier = 2 / (period + 1);

    // First EMA is SMA
    let ema = 0;
    for (let i = 0; i < period; i++) {
        ema += data[i].close;
    }
    ema /= period;
    result.push({ time: normalizeTime(data[period - 1].time), value: ema });

    // Calculate remaining EMAs
    for (let i = period; i < data.length; i++) {
        ema = (data[i].close - ema) * multiplier + ema;
        result.push({ time: normalizeTime(data[i].time), value: ema });
    }

    return result;
}

/**
 * Calculate Bollinger Bands
 */
function calculateBollingerBands(data: OHLCData[], period: number = 20, stdDev: number = 2): {
    upper: LineData<Time>[];
    middle: LineData<Time>[];
    lower: LineData<Time>[];
} {
    const upper: LineData<Time>[] = [];
    const middle: LineData<Time>[] = [];
    const lower: LineData<Time>[] = [];

    for (let i = period - 1; i < data.length; i++) {
        let sum = 0;
        for (let j = 0; j < period; j++) {
            sum += data[i - j].close;
        }
        const sma = sum / period;

        let variance = 0;
        for (let j = 0; j < period; j++) {
            variance += Math.pow(data[i - j].close - sma, 2);
        }
        const std = Math.sqrt(variance / period);

        middle.push({ time: normalizeTime(data[i].time), value: sma });
        upper.push({ time: normalizeTime(data[i].time), value: sma + stdDev * std });
        lower.push({ time: normalizeTime(data[i].time), value: sma - stdDev * std });
    }

    return { upper, middle, lower };
}

// ============================================================================
// Component
// ============================================================================

export const CandlestickChart: React.FC<CandlestickChartProps> = ({
    data,
    symbol = '',
    timeframe = '1h',
    indicators = [],
    height = 400,
    showVolume = true,
    theme = 'dark',
    onCrosshairMove,
}) => {
    const chartContainerRef = useRef<HTMLDivElement>(null);
    const chartRef = useRef<IChartApi | null>(null);
    const candleSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
    const volumeSeriesRef = useRef<ISeriesApi<'Histogram'> | null>(null);
    const indicatorSeriesRef = useRef<ISeriesApi<'Line'>[]>([]);

    const [currentPrice, setCurrentPrice] = useState<number | null>(null);
    const [priceChange, setPriceChange] = useState<{ value: number; percent: number } | null>(null);

    // Theme colors
    const colors = theme === 'dark' ? {
        background: '#1a1a2e',
        textColor: '#d1d4dc',
        gridColor: '#2a2a4a',
        upColor: '#26a69a',
        downColor: '#ef5350',
        borderUpColor: '#26a69a',
        borderDownColor: '#ef5350',
        wickUpColor: '#26a69a',
        wickDownColor: '#ef5350',
    } : {
        background: '#ffffff',
        textColor: '#191919',
        gridColor: '#e0e0e0',
        upColor: '#26a69a',
        downColor: '#ef5350',
        borderUpColor: '#26a69a',
        borderDownColor: '#ef5350',
        wickUpColor: '#26a69a',
        wickDownColor: '#ef5350',
    };

    // Initialize chart
    useEffect(() => {
        if (!chartContainerRef.current) return;

        // Create chart
        const chart = createChart(chartContainerRef.current, {
            width: chartContainerRef.current.clientWidth,
            height: height,
            layout: {
                background: { type: ColorType.Solid, color: colors.background },
                textColor: colors.textColor,
            },
            grid: {
                vertLines: { color: colors.gridColor },
                horzLines: { color: colors.gridColor },
            },
            crosshair: {
                mode: 1, // Normal mode
            },
            rightPriceScale: {
                borderColor: colors.gridColor,
            },
            timeScale: {
                borderColor: colors.gridColor,
                timeVisible: true,
                secondsVisible: false,
            },
        });

        chartRef.current = chart;

        // Create candlestick series (v5 API)
        const candleSeries = chart.addSeries(CandlestickSeries, {
            upColor: colors.upColor,
            downColor: colors.downColor,
            borderUpColor: colors.borderUpColor,
            borderDownColor: colors.borderDownColor,
            wickUpColor: colors.wickUpColor,
            wickDownColor: colors.wickDownColor,
        });
        candleSeriesRef.current = candleSeries;

        // Create volume series (v5 API)
        if (showVolume) {
            const volumeSeries = chart.addSeries(HistogramSeries, {
                color: '#26a69a',
                priceFormat: {
                    type: 'volume',
                },
                priceScaleId: '',
            });
            volumeSeries.priceScale().applyOptions({
                scaleMargins: {
                    top: 0.8,
                    bottom: 0,
                },
            });
            volumeSeriesRef.current = volumeSeries;
        }

        // Handle crosshair move
        chart.subscribeCrosshairMove((param) => {
            if (param.time && param.seriesData.size > 0) {
                const candleData = param.seriesData.get(candleSeries) as CandlestickData<Time>;
                if (candleData) {
                    setCurrentPrice(candleData.close);
                    onCrosshairMove?.(candleData.close, param.time as string);
                }
            } else {
                onCrosshairMove?.(null, null);
            }
        });

        // Handle resize
        const handleResize = () => {
            if (chartContainerRef.current) {
                chart.applyOptions({ width: chartContainerRef.current.clientWidth });
            }
        };
        window.addEventListener('resize', handleResize);

        return () => {
            window.removeEventListener('resize', handleResize);
            chart.remove();
        };
    }, [height, theme, showVolume]);

    // Update data
    useEffect(() => {
        if (!candleSeriesRef.current || data.length === 0) return;

        // Convert data to chart format
        const candleData: CandlestickData<Time>[] = data.map(d => ({
            time: normalizeTime(d.time),
            open: d.open,
            high: d.high,
            low: d.low,
            close: d.close,
        }));

        candleSeriesRef.current.setData(candleData);

        // Update volume
        if (volumeSeriesRef.current && showVolume) {
            const volumeData: HistogramData<Time>[] = data.map(d => ({
                time: normalizeTime(d.time),
                value: d.volume || 0,
                color: d.close >= d.open ? 'rgba(38, 166, 154, 0.5)' : 'rgba(239, 83, 80, 0.5)',
            }));
            volumeSeriesRef.current.setData(volumeData);
        }

        // Calculate price change
        if (data.length >= 2) {
            const latest = data[data.length - 1];
            const previous = data[data.length - 2];
            const change = latest.close - previous.close;
            const percent = (change / previous.close) * 100;
            setPriceChange({ value: change, percent });
            setCurrentPrice(latest.close);
        }

        // Fit content
        chartRef.current?.timeScale().fitContent();
    }, [data, showVolume]);

    // Update indicators
    useEffect(() => {
        if (!chartRef.current || data.length === 0) return;

        // Remove old indicator series
        indicatorSeriesRef.current.forEach(series => {
            try {
                if (series && chartRef.current) {
                    chartRef.current.removeSeries(series);
                }
            } catch (e) {
                console.warn("Failed to remove series:", e);
            }
        });
        indicatorSeriesRef.current = [];

        // Add new indicators
        indicators.forEach((indicator, index) => {
            if (!indicator.visible) return;

            const defaultColors = ['#2196f3', '#ff9800', '#9c27b0', '#4caf50', '#f44336'];
            const color = indicator.color || defaultColors[index % defaultColors.length];

            switch (indicator.type) {
                case 'ma': {
                    const maData = calculateSMA(data, indicator.period || 20);
                    const maSeries = chartRef.current!.addSeries(LineSeries, {
                        color,
                        lineWidth: 1,
                        title: `MA(${indicator.period || 20})`,
                    });
                    maSeries.setData(maData);
                    indicatorSeriesRef.current.push(maSeries);
                    break;
                }
                case 'ema': {
                    const emaData = calculateEMA(data, indicator.period || 20);
                    const emaSeries = chartRef.current!.addSeries(LineSeries, {
                        color,
                        lineWidth: 1,
                        title: `EMA(${indicator.period || 20})`,
                    });
                    emaSeries.setData(emaData);
                    indicatorSeriesRef.current.push(emaSeries);
                    break;
                }
                case 'bollinger': {
                    const bb = calculateBollingerBands(data, indicator.period || 20);

                    const upperSeries = chartRef.current!.addSeries(LineSeries, {
                        color: 'rgba(33, 150, 243, 0.5)',
                        lineWidth: 1,
                        title: 'BB Upper',
                    });
                    upperSeries.setData(bb.upper);
                    indicatorSeriesRef.current.push(upperSeries);

                    const middleSeries = chartRef.current!.addSeries(LineSeries, {
                        color: 'rgba(33, 150, 243, 0.8)',
                        lineWidth: 1,
                        title: 'BB Middle',
                    });
                    middleSeries.setData(bb.middle);
                    indicatorSeriesRef.current.push(middleSeries);

                    const lowerSeries = chartRef.current!.addSeries(LineSeries, {
                        color: 'rgba(33, 150, 243, 0.5)',
                        lineWidth: 1,
                        title: 'BB Lower',
                    });
                    lowerSeries.setData(bb.lower);
                    indicatorSeriesRef.current.push(lowerSeries);
                    break;
                }
            }
        });
    }, [data, indicators]);

    // Format timeframe label
    const timeframeLabels: Record<string, string> = {
        '1h': '1시간',
        '4h': '4시간',
        '1d': '일봉',
        '1w': '주봉',
    };

    return (
        <div className="candlestick-chart-container">
            {/* Header */}
            <div className="chart-header" style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '8px 12px',
                backgroundColor: theme === 'dark' ? '#1a1a2e' : '#f5f5f5',
                borderBottom: `1px solid ${theme === 'dark' ? '#2a2a4a' : '#e0e0e0'}`,
            }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    {symbol && (
                        <span style={{
                            fontWeight: 'bold',
                            fontSize: '16px',
                            color: theme === 'dark' ? '#fff' : '#000',
                        }}>
                            {symbol}
                        </span>
                    )}
                    <span style={{
                        fontSize: '12px',
                        color: theme === 'dark' ? '#888' : '#666',
                        padding: '2px 6px',
                        backgroundColor: theme === 'dark' ? '#2a2a4a' : '#e0e0e0',
                        borderRadius: '4px',
                    }}>
                        {timeframeLabels[timeframe] || timeframe}
                    </span>
                </div>

                {currentPrice !== null && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span style={{
                            fontWeight: 'bold',
                            fontSize: '16px',
                            color: theme === 'dark' ? '#fff' : '#000',
                        }}>
                            ${currentPrice.toFixed(2)}
                        </span>
                        {priceChange && (
                            <span style={{
                                fontSize: '14px',
                                color: priceChange.value >= 0 ? '#26a69a' : '#ef5350',
                            }}>
                                {priceChange.value >= 0 ? '+' : ''}{priceChange.value.toFixed(2)}
                                ({priceChange.percent >= 0 ? '+' : ''}{priceChange.percent.toFixed(2)}%)
                            </span>
                        )}
                    </div>
                )}
            </div>

            {/* Chart */}
            <div ref={chartContainerRef} style={{ width: '100%' }} />

            {/* Indicator Legend */}
            {indicators.length > 0 && (
                <div style={{
                    display: 'flex',
                    flexWrap: 'wrap',
                    gap: '8px',
                    padding: '8px 12px',
                    backgroundColor: theme === 'dark' ? '#1a1a2e' : '#f5f5f5',
                    borderTop: `1px solid ${theme === 'dark' ? '#2a2a4a' : '#e0e0e0'}`,
                    fontSize: '12px',
                }}>
                    {indicators.filter(i => i.visible).map((indicator, index) => {
                        const defaultColors = ['#2196f3', '#ff9800', '#9c27b0', '#4caf50', '#f44336'];
                        const color = indicator.color || defaultColors[index % defaultColors.length];
                        return (
                            <span key={index} style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                                <span style={{
                                    width: '12px',
                                    height: '2px',
                                    backgroundColor: color,
                                    display: 'inline-block',
                                }} />
                                <span style={{ color: theme === 'dark' ? '#888' : '#666' }}>
                                    {indicator.type.toUpperCase()}({indicator.period || 20})
                                </span>
                            </span>
                        );
                    })}
                </div>
            )}
        </div>
    );
};

export default CandlestickChart;

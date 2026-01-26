/**
 * Live Dashboard Page
 * 
 * 실시간 시장 데이터, 충돌 알림, 트레이딩 시그널을 통합한 라이브 대시보드
 * 
 * Features:
 * - Real-time market data via WebSocket
 * - Conflict alerts monitoring
 * - Live trading signals display
 * - Connection status indicators
 * - Auto-refresh and reconnect
 * 
 * Phase 4 - Real-time Execution
 */

import React, { useState } from 'react';
import { Row, Col, Card, Statistic, Tag } from 'antd';
import {
    DashboardOutlined,
    LineChartOutlined,
    WarningOutlined,
    SignalFilled,
    ReloadOutlined,
} from '@ant-design/icons';
import { RealTimeChart, ConflictAlert, LiveSignals } from '@/components/RealTimeChart';
import { useMarketDataWebSocket } from '@/hooks/useMarketDataWebSocket';
import { useConflictWebSocket } from '@/hooks/useMarketDataWebSocket';

const DEFAULT_WATCHLIST = ['NVDA', 'MSFT', 'AAPL', 'GOOGL', 'AMZN', 'TSLA', 'META'];

export const LiveDashboard: React.FC = () => {
    const [watchlist, setWatchlist] = useState<string[]>(DEFAULT_WATCHLIST);
    const { quotes, isConnected: marketConnected, reconnect: reconnectMarket } =
        useMarketDataWebSocket(watchlist);
    const { conflicts, isConnected: conflictConnected } = useConflictWebSocket();

    // Calculate summary statistics
    const totalSymbols = watchlist.length;
    const updatedSymbols = Object.keys(quotes).length;
    const activeConflicts = conflicts.length;

    // Calculate market movers
    const topGainers = Object.values(quotes)
        .filter(q => q.change !== null && q.change > 0)
        .sort((a, b) => (b.change ?? 0) - (a.change ?? 0))
        .slice(0, 3);

    const topLosers = Object.values(quotes)
        .filter(q => q.change !== null && q.change < 0)
        .sort((a, b) => (a.change ?? 0) - (b.change ?? 0))
        .slice(0, 3);

    return (
        <div className="live-dashboard" style={{ padding: '24px', backgroundColor: '#f0f2f5' }}>
            {/* Header */}
            <Card
                style={{ marginBottom: 24 }}
                bodyStyle={{ padding: '16px 24px' }}
            >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                        <DashboardOutlined style={{ fontSize: 28, color: '#1890ff' }} />
                        <h1 style={{ margin: 0, fontSize: 24, fontWeight: 'bold' }}>
                            Live Trading Dashboard
                        </h1>
                    </div>

                    <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
                        {/* Connection Status */}
                        <div style={{ display: 'flex', gap: 8 }}>
                            <Tag
                                icon={<LineChartOutlined />}
                                color={marketConnected ? 'success' : 'error'}
                            >
                                Market: {marketConnected ? 'Connected' : 'Disconnected'}
                            </Tag>
                            <Tag
                                icon={<WarningOutlined />}
                                color={conflictConnected ? 'success' : 'error'}
                            >
                                Conflicts: {conflictConnected ? 'Connected' : 'Disconnected'}
                            </Tag>
                        </div>

                        {/* Manual Reconnect Button */}
                        {(!marketConnected || !conflictConnected) && (
                            <button
                                onClick={() => {
                                    if (!marketConnected) reconnectMarket();
                                }}
                                style={{
                                    padding: '4px 12px',
                                    border: '1px solid #d9d9d9',
                                    borderRadius: 4,
                                    cursor: 'pointer',
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: 4,
                                    backgroundColor: 'white',
                                }}
                            >
                                <ReloadOutlined />
                                Reconnect
                            </button>
                        )}

                        <span style={{ fontSize: 12, color: '#8c8c8c' }}>
                            Last update: {new Date().toLocaleTimeString('ko-KR')}
                        </span>
                    </div>
                </div>
            </Card>

            {/* Summary Statistics */}
            <Row gutter={16} style={{ marginBottom: 24 }}>
                <Col xs={24} sm={12} md={6}>
                    <Card>
                        <Statistic
                            title="Watchlist Symbols"
                            value={totalSymbols}
                            suffix={`/ ${updatedSymbols} updated`}
                            valueStyle={{ color: '#1890ff' }}
                        />
                    </Card>
                </Col>

                <Col xs={24} sm={12} md={6}>
                    <Card>
                        <Statistic
                            title="Active Conflicts"
                            value={activeConflicts}
                            valueStyle={{ color: activeConflicts > 0 ? '#ff4d4f' : '#52c41a' }}
                            prefix={activeConflicts > 0 ? <WarningOutlined /> : null}
                        />
                    </Card>
                </Col>

                <Col xs={24} sm={12} md={6}>
                    <Card>
                        <Statistic
                            title="Top Gainer"
                            value={topGainers[0]?.symbol ?? 'N/A'}
                            suffix={topGainers[0]?.change ? `+${topGainers[0].change.toFixed(2)}%` : ''}
                            valueStyle={{ color: '#52c41a' }}
                        />
                    </Card>
                </Col>

                <Col xs={24} sm={12} md={6}>
                    <Card>
                        <Statistic
                            title="Top Loser"
                            value={topLosers[0]?.symbol ?? 'N/A'}
                            suffix={topLosers[0]?.change ? `${topLosers[0].change.toFixed(2)}%` : ''}
                            valueStyle={{ color: '#ff4d4f' }}
                        />
                    </Card>
                </Col>
            </Row>

            {/* Main Content */}
            <Row gutter={[16, 16]}>
                {/* Left Column - Market Data (70%) */}
                <Col xs={24} lg={16}>
                    <RealTimeChart
                        symbols={watchlist}
                        title="Real-time Market Data"
                    />
                </Col>

                {/* Right Column - Alerts & Signals (30%) */}
                <Col xs={24} lg={8}>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                        {/* Conflict Alerts */}
                        <ConflictAlert maxAlerts={5} />

                        {/* Live Signals */}
                        <LiveSignals />
                    </div>
                </Col>
            </Row>

            {/* Additional Info */}
            <Card
                style={{ marginTop: 24 }}
                title="Market Movers"
                size="small"
            >
                <Row gutter={16}>
                    <Col xs={24} md={12}>
                        <h4 style={{ color: '#52c41a', marginBottom: 12 }}>📈 Top Gainers</h4>
                        {topGainers.length === 0 ? (
                            <p style={{ color: '#8c8c8c' }}>No gainers yet</p>
                        ) : (
                            <ul style={{ listStyle: 'none', padding: 0 }}>
                                {topGainers.map(quote => (
                                    <li
                                        key={quote.symbol}
                                        style={{
                                            marginBottom: 8,
                                            padding: 8,
                                            backgroundColor: 'rgba(82, 196, 26, 0.05)',
                                            borderRadius: 4
                                        }}
                                    >
                                        <strong>{quote.symbol}</strong>: $
                                        {quote.price?.toFixed(2) ?? 'N/A'}
                                        <span style={{ color: '#52c41a', marginLeft: 8 }}>
                                            +{quote.change?.toFixed(2) ?? 0}%
                                        </span>
                                    </li>
                                ))}
                            </ul>
                        )}
                    </Col>

                    <Col xs={24} md={12}>
                        <h4 style={{ color: '#ff4d4f', marginBottom: 12 }}>📉 Top Losers</h4>
                        {topLosers.length === 0 ? (
                            <p style={{ color: '#8c8c8c' }}>No losers yet</p>
                        ) : (
                            <ul style={{ listStyle: 'none', padding: 0 }}>
                                {topLosers.map(quote => (
                                    <li
                                        key={quote.symbol}
                                        style={{
                                            marginBottom: 8,
                                            padding: 8,
                                            backgroundColor: 'rgba(255, 77, 79, 0.05)',
                                            borderRadius: 4
                                        }}
                                    >
                                        <strong>{quote.symbol}</strong>: $
                                        {quote.price?.toFixed(2) ?? 'N/A'}
                                        <span style={{ color: '#ff4d4f', marginLeft: 8 }}>
                                            {quote.change?.toFixed(2) ?? 0}%
                                        </span>
                                    </li>
                                ))}
                            </ul>
                        )}
                    </Col>
                </Row>
            </Card>
        </div>
    );
};

export default LiveDashboard;

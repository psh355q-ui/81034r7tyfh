import React, { useState, useEffect } from 'react';
import './FLEWidget.css';

interface FLEData {
    fle: number;
    peak_fle: number;
    drawdown: number;
    drawdown_pct: number;
    total_position_value: number;
    estimated_fees: number;
    estimated_tax: number;
    cash_balance: number;
    alert_level: string;
    safety_message: string;
}

interface FLEWidgetProps {
    userId: string;
}

const FLEWidget: React.FC<FLEWidgetProps> = ({ userId }) => {
    const [fleData, setFleData] = useState<FLEData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        fetchFLE();
        // Auto-refresh every 5 minutes
        const interval = setInterval(fetchFLE, 5 * 60 * 1000);
        return () => clearInterval(interval);
    }, [userId]);

    const fetchFLE = async () => {
        try {
            setLoading(true);

            // API Base URL
            const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8001';

            // TODO: Get actual portfolio data from API
            const mockPortfolio = {
                user_id: userId,
                positions: [
                    { ticker: 'AAPL', quantity: 100, current_price: 180, cost_basis: 150 },
                    { ticker: 'NVDA', quantity: 50, current_price: 560, cost_basis: 450 }
                ],
                cash: 10000
            };

            const response = await fetch(`${API_BASE}/api/portfolio/fle`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(mockPortfolio)
            });

            if (!response.ok) {
                throw new Error('Failed to fetch FLE');
            }

            const data = await response.json();
            setFleData(data);
            setError(null);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Unknown error');
        } finally {
            setLoading(false);
        }
    };

    const getAlertColor = (level: string): string => {
        switch (level) {
            case 'SAFE': return '#10b981'; // green
            case 'MILD': return '#f59e0b'; // amber
            case 'WARNING': return '#f97316'; // orange
            case 'CRITICAL': return '#ef4444'; // red
            default: return '#6b7280'; // gray
        }
    };

    const getAlertIcon = (level: string): string => {
        switch (level) {
            case 'SAFE': return '✅';
            case 'MILD': return 'ℹ️';
            case 'WARNING': return '⚠️';
            case 'CRITICAL': return '🛑';
            default: return '📊';
        }
    };

    const formatCurrency = (value: number): string => {
        return new Intl.NumberFormat('ko-KR', {
            style: 'currency',
            currency: 'KRW',
            maximumFractionDigits: 0
        }).format(value);
    };

    if (loading && !fleData) {
        return (
            <div className="fle-widget loading">
                <div className="loading-spinner">FLE 계산 중...</div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="fle-widget error">
                <div className="error-message">❌ {error}</div>
            </div>
        );
    }

    if (!fleData) {
        return null;
    }

    const alertColor = getAlertColor(fleData.alert_level);
    const alertIcon = getAlertIcon(fleData.alert_level);

    return (
        <div className="fle-widget" style={{ borderLeftColor: alertColor }}>
            <div className="widget-header">
                <h3>💰 FLE (지금 팔면)</h3>
                <button className="refresh-btn" onClick={fetchFLE} disabled={loading}>
                    {loading ? '⏳' : '🔄'}
                </button>
            </div>

            <div className="fle-content">
                <div className="fle-main">
                    <div className="fle-amount">{formatCurrency(fleData.fle)}</div>
                    <div className="fle-subtitle">전량 청산 시 실수령액</div>
                </div>

                <div className="fle-middle">
                    <div className="fle-metrics">
                        <div className="metric">
                            <span className="metric-label">최고점</span>
                            <span className="metric-value">{formatCurrency(fleData.peak_fle)}</span>
                        </div>
                        <div className="metric">
                            <span className="metric-label">Drawdown</span>
                            <span className="metric-value negative">
                                {formatCurrency(fleData.drawdown)} ({(fleData.drawdown_pct * 100).toFixed(1)}%)
                            </span>
                        </div>
                    </div>

                    <div className="fle-breakdown">
                        <div className="breakdown-item">
                            <span>포지션 가치</span>
                            <span>{formatCurrency(fleData.total_position_value)}</span>
                        </div>
                        <div className="breakdown-item">
                            <span>현금</span>
                            <span>{formatCurrency(fleData.cash_balance)}</span>
                        </div>
                        <div className="breakdown-item negative">
                            <span>예상 수수료</span>
                            <span>-{formatCurrency(fleData.estimated_fees)}</span>
                        </div>
                        <div className="breakdown-item negative">
                            <span>예상 세금</span>
                            <span>-{formatCurrency(fleData.estimated_tax)}</span>
                        </div>
                    </div>
                </div>

                <div
                    className="alert-status"
                    style={{ backgroundColor: alertColor }}
                >
                    <span className="alert-icon">{alertIcon}</span>
                    <span className="alert-text">{fleData.safety_message}</span>
                </div>
            </div>
        </div>
    );
};

export default FLEWidget;

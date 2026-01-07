/**
 * Orders Page - 주문 히스토리 관리
 *
 * Phase 27: REAL MODE UI
 * Date: 2025-12-23
 */

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import './Orders.css';

interface Order {
    id: number;
    ticker: string;
    action: 'BUY' | 'SELL';
    quantity: number;
    price: number;
    order_type: string;
    status: 'PENDING' | 'FILLED' | 'CANCELLED' | 'REJECTED';
    broker: string;
    order_id: string;
    signal_id: number | null;
    created_at: string;
    updated_at?: string;
    filled_at?: string;
}

// Mock data for development
const MOCK_ORDERS: Order[] = [
    {
        id: 1,
        ticker: 'AAPL',
        action: 'BUY',
        quantity: 10,
        price: 178.50,
        order_type: 'MARKET',
        status: 'FILLED',
        broker: 'KIS',
        order_id: 'KIS20251223001',
        signal_id: 14,
        created_at: '2025-12-23T12:37:38Z',
        filled_at: '2025-12-23T12:37:45Z'
    },
    {
        id: 2,
        ticker: 'NVDA',
        action: 'BUY',
        quantity: 5,
        price: 495.20,
        order_type: 'MARKET',
        status: 'PENDING',
        broker: 'KIS',
        order_id: 'KIS20251223002',
        signal_id: 15,
        created_at: '2025-12-23T14:22:10Z'
    },
    {
        id: 3,
        ticker: 'TSLA',
        action: 'SELL',
        quantity: 3,
        price: 252.80,
        order_type: 'MARKET',
        status: 'CANCELLED',
        broker: 'KIS',
        order_id: 'KIS20251223003',
        signal_id: null,
        created_at: '2025-12-23T15:10:22Z',
        updated_at: '2025-12-23T15:11:00Z'
    }
];

type StatusFilter = 'ALL' | 'PENDING' | 'FILLED' | 'CANCELLED';

const Orders: React.FC = () => {
    const [statusFilter, setStatusFilter] = useState<StatusFilter>('ALL');
    const [searchTicker, setSearchTicker] = useState('');

    // Fetch orders from API
    const { data: orders = [], isLoading, error } = useQuery<Order[]>({
        queryKey: ['orders', statusFilter, searchTicker],
        queryFn: async (): Promise<Order[]> => {
            const params = new URLSearchParams();
            if (statusFilter !== 'ALL') {
                params.append('status', statusFilter);
            }
            if (searchTicker) {
                params.append('ticker', searchTicker);
            }
            params.append('limit', '50');

            const response = await fetch(`/api/orders?${params.toString()}`);
            if (!response.ok) {
                throw new Error(`Failed to fetch orders: ${response.statusText}`);
            }
            return response.json();
        },
        refetchInterval: 10000 // Refresh every 10 seconds
    });

    // Filter orders
    const filteredOrders = orders.filter(order => {
        const matchesStatus = statusFilter === 'ALL' || order.status === statusFilter;
        const matchesTicker = searchTicker === '' ||
            order.ticker.toUpperCase().includes(searchTicker.toUpperCase());

        return matchesStatus && matchesTicker;
    });

    // Statistics
    const stats = {
        total: orders.length,
        pending: orders.filter(o => o.status === 'PENDING').length,
        filled: orders.filter(o => o.status === 'FILLED').length,
        cancelled: orders.filter(o => o.status === 'CANCELLED' || o.status === 'REJECTED').length,
    };

    // Status badge color
    const getStatusColor = (status: string) => {
        switch (status) {
            case 'FILLED': return '#4CAF50';
            case 'PENDING': return '#FF9800';
            case 'CANCELLED': return '#9E9E9E';
            case 'REJECTED': return '#F44336';
            default: return '#9E9E9E';
        }
    };

    // Action badge color
    const getActionColor = (action: string) => {
        return action === 'BUY' ? '#2196F3' : '#F44336';
    };

    if (isLoading) {
        return (
            <div className="orders-page">
                <div className="loading-state">
                    <div className="spinner">🔄</div>
                    <p>주문 히스토리 로딩 중...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="orders-page">
                <div className="error-state">
                    <p>⚠️ 주문 히스토리를 불러올 수 없습니다</p>
                    <p style={{ fontSize: '14px', opacity: 0.7 }}>{(error as Error).message}</p>
                </div>
            </div>
        );
    }

    return (
        <div className="orders-page">
            {/* Header */}
            <div className="page-header">
                <h1>📋 주문 히스토리</h1>
                <div className="header-stats">
                    <div className="stat-card">
                        <span className="stat-label">전체</span>
                        <span className="stat-value">{stats.total}</span>
                    </div>
                    <div className="stat-card">
                        <span className="stat-label">체결</span>
                        <span className="stat-value" style={{ color: '#4CAF50' }}>{stats.filled}</span>
                    </div>
                    <div className="stat-card">
                        <span className="stat-label">대기</span>
                        <span className="stat-value" style={{ color: '#FF9800' }}>{stats.pending}</span>
                    </div>
                    <div className="stat-card">
                        <span className="stat-label">취소</span>
                        <span className="stat-value" style={{ color: '#9E9E9E' }}>{stats.cancelled}</span>
                    </div>
                </div>
            </div>

            {/* Filters */}
            <div className="filters">
                <div className="search-box">
                    <input
                        type="text"
                        value={searchTicker}
                        onChange={(e) => setSearchTicker(e.target.value)}
                        placeholder="🔍 티커 검색..."
                        className="search-input"
                    />
                </div>
                <div className="status-filters">
                    {(['ALL', 'PENDING', 'FILLED', 'CANCELLED'] as StatusFilter[]).map(status => (
                        <button
                            key={status}
                            className={`filter-btn ${statusFilter === status ? 'active' : ''}`}
                            onClick={() => setStatusFilter(status)}
                        >
                            {status === 'ALL' ? '전체' :
                             status === 'PENDING' ? '대기중' :
                             status === 'FILLED' ? '체결' : '취소'}
                        </button>
                    ))}
                </div>
            </div>

            {/* Orders Table */}
            <div className="orders-table-container">
                {filteredOrders.length > 0 ? (
                    <table className="orders-table">
                        <thead>
                            <tr>
                                <th>주문 ID</th>
                                <th>티커</th>
                                <th>액션</th>
                                <th>수량</th>
                                <th>가격</th>
                                <th>총액</th>
                                <th>상태</th>
                                <th>브로커</th>
                                <th>시그널</th>
                                <th>생성 시각</th>
                                <th>체결 시각</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filteredOrders.map(order => (
                                <tr key={order.id}>
                                    <td className="mono">{order.order_id}</td>
                                    <td className="ticker">{order.ticker}</td>
                                    <td>
                                        <span
                                            className="action-badge"
                                            style={{ backgroundColor: getActionColor(order.action) }}
                                        >
                                            {order.action}
                                        </span>
                                    </td>
                                    <td>{order.quantity}</td>
                                    <td className="mono">${order.price.toFixed(2)}</td>
                                    <td className="mono">${(order.quantity * order.price).toFixed(2)}</td>
                                    <td>
                                        <span
                                            className="status-badge"
                                            style={{ backgroundColor: getStatusColor(order.status) }}
                                        >
                                            {order.status}
                                        </span>
                                    </td>
                                    <td>{order.broker}</td>
                                    <td>{order.signal_id || '-'}</td>
                                    <td className="mono">{new Date(order.created_at).toLocaleString('ko-KR')}</td>
                                    <td className="mono">
                                        {order.filled_at ? new Date(order.filled_at).toLocaleString('ko-KR') : '-'}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                ) : (
                    <div className="empty-state">
                        <p>검색 결과가 없습니다</p>
                        <p className="hint">다른 필터를 선택해보세요</p>
                    </div>
                )}
            </div>
        </div>
    );
};

export default Orders;

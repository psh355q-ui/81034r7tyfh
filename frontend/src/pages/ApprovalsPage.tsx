import React, { useState, useEffect } from 'react';
import './ApprovalsPage.css';

interface ApprovalRequest {
    request_id: string;
    ticker: string;
    action: string;
    quantity?: number;
    target_price?: number;
    ai_reasoning: string;
    consensus_confidence: number;
    priority_score: number;
    approval_level: string;
    status: string;
    requested_at: string;
}

const ApprovalsPage: React.FC = () => {
    const [pendingRequests, setPendingRequests] = useState<ApprovalRequest[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        fetchPendingApprovals();
    }, []);

    const fetchPendingApprovals = async () => {
        try {
            setLoading(true);
            const response = await fetch('/api/approvals/pending');

            if (!response.ok) {
                throw new Error('Failed to fetch approvals');
            }

            const data = await response.json();
            setPendingRequests(data);
            setError(null);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Unknown error');
        } finally {
            setLoading(false);
        }
    };

    const handleApprove = async (requestId: string) => {
        try {
            const response = await fetch(`/api/approvals/${requestId}/approve`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    approved_by: 'user@example.com', // TODO: Get from auth
                    notes: ''
                })
            });

            if (!response.ok) {
                throw new Error('Failed to approve');
            }

            // Refresh list
            fetchPendingApprovals();
        } catch (err) {
            alert('승인 실패: ' + (err instanceof Error ? err.message : 'Unknown error'));
        }
    };

    const handleReject = async (requestId: string) => {
        const reason = prompt('거부 사유를 입력하세요:');
        if (!reason) return;

        try {
            const response = await fetch(`/api/approvals/${requestId}/reject`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    rejected_by: 'user@example.com', // TODO: Get from auth
                    reason
                })
            });

            if (!response.ok) {
                throw new Error('Failed to reject');
            }

            // Refresh list
            fetchPendingApprovals();
        } catch (err) {
            alert('거부 실패: ' + (err instanceof Error ? err.message : 'Unknown error'));
        }
    };

    const getPriorityColor = (score: number): string => {
        if (score > 0.7) return '#ef4444'; // High priority - red
        if (score > 0.4) return '#f59e0b'; // Medium priority - amber
        return '#10b981'; // Low priority - green
    };

    const getApprovalLevelBadge = (level: string): string => {
        switch (level) {
            case 'HARD_APPROVAL': return '🔴 명시적 승인 필수';
            case 'SOFT_APPROVAL': return '🟡 24시간 후 자동승인';
            case 'PHILOSOPHY': return '🟣 철학 변경';
            default: return '⚪ 정보만';
        }
    };

    if (loading) {
        return (
            <div className="approvals-page">
                <div className="loading">승인 요청을 불러오는 중...</div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="approvals-page">
                <div className="error">❌ 오류: {error}</div>
            </div>
        );
    }

    return (
        <div className="approvals-page">
            <div className="page-header">
                <h1>🔐 승인 대기열</h1>
                <p className="subtitle">AI 제안에 대한 최종 결정권은 당신에게 있습니다</p>
                <div className="stats">
                    <span className="stat-item">
                        대기 중: <strong>{pendingRequests.length}</strong>
                    </span>
                </div>
            </div>

            {pendingRequests.length === 0 ? (
                <div className="empty-state">
                    <div className="empty-icon">✅</div>
                    <h3>모든 승인 처리 완료</h3>
                    <p>현재 대기 중인 승인 요청이 없습니다.</p>
                </div>
            ) : (
                <div className="approvals-list">
                    {pendingRequests.map((request) => (
                        <div key={request.request_id} className="approval-card">
                            <div className="card-header">
                                <div className="ticker-section">
                                    <span className="ticker">{request.ticker}</span>
                                    <span className={`action action-${request.action.toLowerCase()}`}>
                                        {request.action}
                                    </span>
                                    {request.quantity && (
                                        <span className="quantity">{request.quantity}주</span>
                                    )}
                                </div>
                                <div
                                    className="priority-badge"
                                    style={{ backgroundColor: getPriorityColor(request.priority_score) }}
                                >
                                    우선순위: {(request.priority_score * 100).toFixed(0)}
                                </div>
                            </div>

                            <div className="card-body">
                                <div className="info-row">
                                    <span className="label">승인 레벨:</span>
                                    <span className="value">{getApprovalLevelBadge(request.approval_level)}</span>
                                </div>

                                <div className="info-row">
                                    <span className="label">AI 합의도:</span>
                                    <span className="value">{(request.consensus_confidence * 100).toFixed(0)}%</span>
                                </div>

                                {request.target_price && (
                                    <div className="info-row">
                                        <span className="label">목표가:</span>
                                        <span className="value">${request.target_price.toFixed(2)}</span>
                                    </div>
                                )}

                                <div className="reasoning-section">
                                    <div className="label">AI 분석 근거:</div>
                                    <div className="reasoning-text">{request.ai_reasoning}</div>
                                </div>

                                <div className="timestamp">
                                    요청 시간: {new Date(request.requested_at).toLocaleString('ko-KR')}
                                </div>
                            </div>

                            <div className="card-footer">
                                <button
                                    className="btn btn-approve"
                                    onClick={() => handleApprove(request.request_id)}
                                >
                                    ✅ 승인
                                </button>
                                <button
                                    className="btn btn-reject"
                                    onClick={() => handleReject(request.request_id)}
                                >
                                    ❌ 거부
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default ApprovalsPage;

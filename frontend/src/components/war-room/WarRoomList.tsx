/**
 * War Room List - 여러 티커의 토론 목록
 */

import React, { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { DebateSession } from '../../data/mockDebateSessions';
import { warRoomApi } from '../../services/warRoomApi';
import WarRoomCard from './WarRoomCard';
import { TickerAutocompleteInput } from '../common/TickerAutocompleteInput';
import './WarRoomList.css';

type StatusFilter = 'all' | 'active' | 'completed' | 'pending';

const WarRoomList: React.FC = () => {
    // State for new debate
    const [newDebateTicker, setNewDebateTicker] = useState('');
    const [isRunningDebate, setIsRunningDebate] = useState(false);
    const [debateError, setDebateError] = useState<string | null>(null);

    // Fetch real War Room sessions from API
    const { data: apiSessions, isLoading, error, refetch } = useQuery({
        queryKey: ['war-room-sessions'],
        queryFn: () => warRoomApi.getSessions({ limit: 20 }),
        refetchInterval: 10000, // Refetch every 10 seconds for real-time updates
    });

    // Transform API response to match DebateSession interface
    const sessions: DebateSession[] = useMemo(() => {
        if (!apiSessions) return [];

        return apiSessions.map(session => {
            // Convert votes/votes_detail to messages format
            const messages: any[] = [];
            
            // Prefer 'votes' (dict) from backend, fallback to 'votes_detail' (list)
            // Note: backend returns 'votes' key, but interface might verify 'agent_votes'. check both.
            let votesDict: Record<string, any> = (session as any).votes || session.agent_votes || {};
            const votesDetail = session.votes_detail || [];

            // Helper: Convert list to dict if needed
            if (Object.keys(votesDict).length === 0 && Array.isArray(votesDetail) && votesDetail.length > 0) {
                 votesDetail.forEach((v: any) => {
                     if(v.agent) votesDict[v.agent] = v;
                 });
            }

            // Include ALL 8 agents
            const agentOrder = [
                'risk', 'macro', 'institutional', 'trader', 
                'news', 'analyst', 'chip_war', 'dividend_risk'
            ];

            agentOrder.forEach((agent) => {
                const vote = votesDict[agent] || votesDetail.find((v: any) => v.agent === agent);

                if (vote) {
                    // Risk Agent uses 'recommendation' instead of 'action'
                    const action = vote.action || vote.recommendation || 'hold';

                    messages.push({
                        id: `msg-${session.id}-${agent}`,
                        agent: agent,
                        action: action,
                        confidence: vote.confidence,
                        reasoning: vote.reasoning || `${agent} agent vote: ${action}`,
                        timestamp: new Date(session.created_at + 'Z'),  // Force UTC interpretation
                        isDecision: false
                    });
                }
            });

            // Add PM decision
            const actionLabels: { [key: string]: string } = {
                'buy': '매수',
                'sell': '매도',
                'hold': '보류',
                'reject': '거부',
                'approve': '승인',
                'BUY': '매수',
                'SELL': '매도',
                'HOLD': '보류',
                'REJECT': '거부',
                'APPROVE': '승인'
            };

            // Use PM decision details if available
            const pmDecision = (session as any).pm_decision;
            const finalAction = pmDecision?.final_decision || session.consensus_action;
            const finalConfidence = pmDecision?.confidence ?? session.consensus_confidence;
            const pmReasoning = pmDecision?.reasoning || '';

            const actionLabel = actionLabels[finalAction] || finalAction;

            // Create detailed PM reasoning
            let pmMessage = `PM 최종 결정: ${actionLabel} (${(finalConfidence * 100).toFixed(0)}% 신뢰도)`;
            if (pmReasoning) {
                pmMessage = pmReasoning;
            }

            messages.push({
                id: `msg-${session.id}-pm`,
                agent: 'pm',
                action: finalAction,
                confidence: finalConfidence,
                reasoning: pmMessage,
                timestamp: new Date(session.created_at + 'Z'),  // Force UTC interpretation
                isDecision: true
            });

            return {
                id: session.id.toString(),
                ticker: session.ticker,
                status: 'completed', // All sessions with votes are completed
                startedAt: new Date(session.created_at + 'Z'),  // Force UTC interpretation
                completedAt: new Date(session.created_at + 'Z'),
                messages: messages,
                consensus: session.consensus_confidence,
                finalDecision: {
                    action: session.consensus_action,
                    confidence: session.consensus_confidence
                },
                constitutionalResult: {
                    isValid: session.constitutional_valid,
                    violations: session.constitutional_valid ? [] : ['제3조 위반: 인간 승인이 필요합니다'],
                    violatedArticles: session.constitutional_valid ? [] : ['제3조: 인간 최종 결정권']
                }
            };
        });
    }, [apiSessions]);
    const [searchTicker, setSearchTicker] = useState('');
    const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');
    const [expandedCardId, setExpandedCardId] = useState<string | null>(null);

    // 필터링 및 정렬된 세션 (최신순)
    const filteredSessions = useMemo(() => {
        return sessions
            .filter(session => {
                // 티커 검색
                const matchesTicker = searchTicker === '' ||
                    session.ticker.toUpperCase().includes(searchTicker.toUpperCase());

                // 상태 필터
                const matchesStatus = statusFilter === 'all' ||
                    session.status === statusFilter;

                return matchesTicker && matchesStatus;
            })
            .sort((a, b) => {
                // 최신순 정렬 (created_at 기준 내림차순)
                return b.startedAt.getTime() - a.startedAt.getTime();
            });
    }, [sessions, searchTicker, statusFilter]);

    // 통계
    const stats = useMemo(() => {
        return {
            total: sessions.length,
            active: sessions.filter(s => s.status === 'active').length,
            completed: sessions.filter(s => s.status === 'completed').length,
            pending: sessions.filter(s => s.status === 'pending').length
        };
    }, [sessions]);

    // 카드 토글
    const handleCardToggle = (cardId: string) => {
        setExpandedCardId(prev => prev === cardId ? null : cardId);
    };

    // 빈 공간 클릭 시 카드 닫기
    const handleBackdropClick = () => {
        setExpandedCardId(null);
    };

    // 새로운 토론 시작
    const handleRunDebate = async () => {
        if (!newDebateTicker.trim()) {
            setDebateError('티커를 입력해주세요');
            return;
        }

        setIsRunningDebate(true);
        setDebateError(null);

        try {
            const result = await warRoomApi.runDebate(newDebateTicker.toUpperCase());
            console.log('Debate result:', result);

            // 성공: 세션 목록 갱신
            await refetch();

            // 입력 초기화
            setNewDebateTicker('');

            // 알림 (latency 정보 포함)
            const latencyInfo = result.latency_ms
                ? `\n⏱️ 응답 시간: ${(result.latency_ms / 1000).toFixed(1)}초`
                : '';
            alert(`✅ ${result.ticker} War Room 토론 완료!\n결과: ${result.consensus.action} (${(result.consensus.confidence * 100).toFixed(0)}%)${latencyInfo}`);

        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : 'Unknown error';
            setDebateError(errorMessage);
            console.error('Debate error:', err);
        } finally {
            setIsRunningDebate(false);
        }
    };

    // Loading state
    if (isLoading) {
        return (
            <div className="war-room-list">
                <div className="loading-state" style={{ textAlign: 'center', padding: '40px' }}>
                    <div className="spinner">🔄</div>
                    <p>War Room 세션 불러오는 중...</p>
                </div>
            </div>
        );
    }

    // Error state
    if (error) {
        return (
            <div className="war-room-list">
                <div className="error-state" style={{ textAlign: 'center', padding: '40px', color: '#F44336' }}>
                    <p>⚠️ War Room 세션을 불러올 수 없습니다</p>
                    <p style={{ fontSize: '14px', opacity: 0.7 }}>{(error as Error).message}</p>
                </div>
            </div>
        );
    }

    return (
        <div className="war-room-list">
            {/* 새로운 토론 시작 섹션 */}
            <div className="new-debate-section" style={{
                marginBottom: '24px',
                padding: '20px',
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                borderRadius: '12px',
                color: 'white'
            }}>
                <h3 style={{ margin: '0 0 16px 0', fontSize: '18px', fontWeight: 'bold' }}>
                    🚀 새로운 토론 시작
                </h3>
                <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-start' }}>
                    <input
                        type="text"
                        value={newDebateTicker}
                        onChange={(e) => setNewDebateTicker(e.target.value.toUpperCase())}
                        onKeyPress={(e) => e.key === 'Enter' && handleRunDebate()}
                        placeholder="티커 입력 (예: AAPL, TSLA)"
                        disabled={isRunningDebate}
                        style={{
                            flex: 1,
                            padding: '12px 16px',
                            fontSize: '16px',
                            border: '2px solid rgba(255,255,255,0.3)',
                            borderRadius: '8px',
                            background: 'rgba(255,255,255,0.15)',
                            color: 'white',
                            fontWeight: 'bold'
                        }}
                    />
                    <button
                        onClick={handleRunDebate}
                        disabled={isRunningDebate || !newDebateTicker.trim()}
                        style={{
                            padding: '12px 24px',
                            fontSize: '16px',
                            fontWeight: 'bold',
                            border: 'none',
                            borderRadius: '8px',
                            background: isRunningDebate ? '#999' : 'white',
                            color: '#667eea',
                            cursor: isRunningDebate ? 'not-allowed' : 'pointer',
                            transition: 'all 0.2s',
                            opacity: !newDebateTicker.trim() ? 0.5 : 1
                        }}
                    >
                        {isRunningDebate ? '🔄 실행중...' : '🎭 토론 시작'}
                    </button>
                </div>
                {debateError && (
                    <div style={{
                        marginTop: '12px',
                        padding: '8px 12px',
                        background: 'rgba(244, 67, 54, 0.2)',
                        borderRadius: '6px',
                        fontSize: '14px'
                    }}>
                        ⚠️ {debateError}
                    </div>
                )}
            </div>

            {/* 검색 & 필터 */}
            <div className="list-controls">
                <div className="search-section">
                    <TickerAutocompleteInput
                        label=""
                        value={searchTicker}
                        onChange={setSearchTicker}
                        placeholder="🔍 티커 검색... (예: NVDA, AAPL)"
                    />
                </div>

                <div className="filter-section">
                    <button
                        className={`filter-btn ${statusFilter === 'all' ? 'active' : ''}`}
                        onClick={() => setStatusFilter('all')}
                    >
                        전체 ({stats.total})
                    </button>
                    <button
                        className={`filter-btn ${statusFilter === 'active' ? 'active' : ''}`}
                        onClick={() => setStatusFilter('active')}
                    >
                        🔄 진행중 ({stats.active})
                    </button>
                    <button
                        className={`filter-btn ${statusFilter === 'completed' ? 'active' : ''}`}
                        onClick={() => setStatusFilter('completed')}
                    >
                        ✅ 완료 ({stats.completed})
                    </button>
                    <button
                        className={`filter-btn ${statusFilter === 'pending' ? 'active' : ''}`}
                        onClick={() => setStatusFilter('pending')}
                    >
                        ⏳ 대기중 ({stats.pending})
                    </button>
                </div>
            </div>

            {/* 결과 표시 */}
            <div className="results-info">
                {filteredSessions.length}개의 토론 세션
            </div>

            {/* 세션 카드 목록 */}
            <div className="sessions-container" onClick={handleBackdropClick}>
                {filteredSessions.length > 0 ? (
                    filteredSessions.map(session => (
                        <WarRoomCard
                            key={session.id}
                            session={session}
                            isExpanded={expandedCardId === session.id}
                            onToggle={() => handleCardToggle(session.id)}
                        />
                    ))
                ) : (
                    <div className="empty-result">
                        <p>검색 결과가 없습니다</p>
                        <p className="hint">다른 티커를 검색해보세요</p>
                    </div>
                )}
            </div>
        </div>
    );
};

export default WarRoomList;

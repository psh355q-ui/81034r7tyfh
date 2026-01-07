/**
 * War Room List - 여러 티커의 토론 목록
 * 
 * Dashboard 스타일과 동일하게 Tailwind CSS 적용
 */

import React, { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Search, Filter, Plus, Loader2, AlertCircle } from 'lucide-react';
import { DebateSession as MockDebateSession } from '../../data/mockDebateSessions';
import { warRoomApi, DebateSession as ApiDebateSession } from '../../services/warRoomApi';
import WarRoomCard from './WarRoomCard';
import { Card } from '../common/Card';
import { LoadingSpinner } from '../common/LoadingSpinner';

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
        refetchInterval: 10000,
    });

    // Transform API response to match MockDebateSession interface
    const sessions: MockDebateSession[] = useMemo(() => {
        if (!apiSessions) return [];

        return apiSessions.map(session => {
            const messages: any[] = [];

            let votesDict: Record<string, any> = (session as any).votes || session.agent_votes || {};
            const votesDetail = session.votes_detail || [];

            if (Object.keys(votesDict).length === 0 && Array.isArray(votesDetail) && votesDetail.length > 0) {
                votesDetail.forEach((v: any) => {
                    if (v.agent) votesDict[v.agent] = v;
                });
            }

            const agentOrder = [
                'risk', 'macro', 'institutional', 'trader',
                'news', 'analyst', 'chip_war', 'dividend_risk'
            ];

            agentOrder.forEach((agent) => {
                const vote = votesDict[agent] || votesDetail.find((v: any) => v.agent === agent);

                if (vote) {
                    const action = vote.action || vote.recommendation || 'hold';

                    messages.push({
                        id: `msg-${session.id}-${agent}`,
                        agent: agent,
                        action: action,
                        confidence: vote.confidence,
                        reasoning: vote.reasoning || `${agent} agent vote: ${action}`,
                        timestamp: new Date(session.created_at + 'Z'),
                        isDecision: false
                    });
                }
            });

            const actionLabels: { [key: string]: string } = {
                'buy': '매수', 'sell': '매도', 'hold': '보류',
                'reject': '거부', 'approve': '승인',
                'BUY': '매수', 'SELL': '매도', 'HOLD': '보류',
                'REJECT': '거부', 'APPROVE': '승인'
            };

            const pmDecision = (session as any).pm_decision;
            const finalAction = pmDecision?.final_decision || session.consensus_action;
            const finalConfidence = pmDecision?.confidence ?? session.consensus_confidence;
            const pmReasoning = pmDecision?.reasoning || '';

            const actionLabel = actionLabels[finalAction] || finalAction;

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
                timestamp: new Date(session.created_at + 'Z'),
                isDecision: true
            });

            return {
                id: session.id.toString(),
                ticker: session.ticker,
                status: 'completed',
                startedAt: new Date(session.created_at + 'Z'),
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
                const matchesTicker = searchTicker === '' ||
                    session.ticker.toUpperCase().includes(searchTicker.toUpperCase());
                const matchesStatus = statusFilter === 'all' ||
                    session.status === statusFilter;
                return matchesTicker && matchesStatus;
            })
            .sort((a, b) => b.startedAt.getTime() - a.startedAt.getTime());
    }, [sessions, searchTicker, statusFilter]);

    // 통계
    const stats = useMemo(() => ({
        total: sessions.length,
        active: sessions.filter(s => s.status === 'active').length,
        completed: sessions.filter(s => s.status === 'completed').length,
        pending: sessions.filter(s => s.status === 'pending').length
    }), [sessions]);

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
            await refetch();
            setNewDebateTicker('');

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
            <div className="flex flex-col items-center justify-center h-64 gap-4">
                <LoadingSpinner size="lg" />
                <p className="text-gray-500 font-medium">War Room 세션 불러오는 중...</p>
            </div>
        );
    }

    // Error state
    if (error) {
        return (
            <div className="p-6">
                <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded flex items-center gap-2">
                    <AlertCircle size={20} />
                    <div>
                        <p className="font-medium">War Room 세션을 불러올 수 없습니다</p>
                        <p className="text-sm opacity-70">{(error as Error).message}</p>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* 새로운 토론 시작 섹션 */}
            <Card className="bg-gradient-to-r from-blue-500 to-purple-600 text-white">
                <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                    <Plus size={20} />
                    새로운 토론 시작
                </h3>
                <div className="flex gap-3 items-start">
                    <input
                        type="text"
                        value={newDebateTicker}
                        onChange={(e) => setNewDebateTicker(e.target.value.toUpperCase())}
                        onKeyPress={(e) => e.key === 'Enter' && handleRunDebate()}
                        placeholder="티커 입력 (예: AAPL, TSLA)"
                        disabled={isRunningDebate}
                        className="flex-1 px-4 py-3 text-gray-900 rounded-lg border-0 focus:ring-2 focus:ring-white font-medium"
                    />
                    <button
                        onClick={handleRunDebate}
                        disabled={isRunningDebate || !newDebateTicker.trim()}
                        className={`px-6 py-3 rounded-lg font-bold transition-all flex items-center gap-2
                            ${isRunningDebate || !newDebateTicker.trim()
                                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                                : 'bg-white text-blue-600 hover:bg-gray-100 shadow-lg hover:shadow-xl'
                            }`}
                    >
                        {isRunningDebate ? (
                            <>
                                <Loader2 className="animate-spin" size={18} />
                                실행중...
                            </>
                        ) : (
                            <>🎭 토론 시작</>
                        )}
                    </button>
                </div>
                {debateError && (
                    <div className="mt-3 px-3 py-2 bg-red-500/20 rounded-lg text-sm flex items-center gap-2">
                        <AlertCircle size={16} />
                        {debateError}
                    </div>
                )}
            </Card>

            {/* 검색 & 필터 */}
            <Card>
                <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
                    {/* 검색 */}
                    <div className="relative flex-1 w-full sm:max-w-xs">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                        <input
                            type="text"
                            value={searchTicker}
                            onChange={(e) => setSearchTicker(e.target.value)}
                            placeholder="티커 검색..."
                            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        />
                    </div>

                    {/* 필터 버튼 */}
                    <div className="flex gap-2 flex-wrap">
                        {[
                            { value: 'all', label: `전체 (${stats.total})` },
                            { value: 'active', label: `🔄 진행중 (${stats.active})` },
                            { value: 'completed', label: `✅ 완료 (${stats.completed})` },
                            { value: 'pending', label: `⏳ 대기중 (${stats.pending})` },
                        ].map(filter => (
                            <button
                                key={filter.value}
                                onClick={() => setStatusFilter(filter.value as StatusFilter)}
                                className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors
                                    ${statusFilter === filter.value
                                        ? 'bg-blue-100 text-blue-700'
                                        : 'text-gray-600 hover:bg-gray-100'
                                    }`}
                            >
                                {filter.label}
                            </button>
                        ))}
                    </div>
                </div>
            </Card>

            {/* 결과 표시 */}
            <div className="text-sm text-gray-500 px-1">
                {filteredSessions.length}개의 토론 세션
            </div>

            {/* 세션 카드 목록 */}
            <div className="space-y-4" onClick={handleBackdropClick}>
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
                    <Card>
                        <div className="text-center py-8 text-gray-500">
                            <p className="text-lg">검색 결과가 없습니다</p>
                            <p className="text-sm mt-1">다른 티커를 검색해보세요</p>
                        </div>
                    </Card>
                )}
            </div>
        </div>
    );
};

export default WarRoomList;

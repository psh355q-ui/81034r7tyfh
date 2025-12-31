/**
 * War Room Card - 개별 티커 토론 카드 (아코디언)
 */

import React, { useState } from 'react';
import { DebateSession } from '../../data/mockDebateSessions';
import WarRoom from './WarRoom';
import './WarRoomCard.css';

interface WarRoomCardProps {
    session: DebateSession;
    isExpanded: boolean;
    onToggle: () => void;
}

const WarRoomCard: React.FC<WarRoomCardProps> = ({ session, isExpanded, onToggle }) => {

    const getStatusBadge = () => {
        switch (session.status) {
            case 'active':
                return { text: '진행중', color: '#4CAF50', icon: '🔄' };
            case 'completed':
                return { text: '완료', color: '#2196F3', icon: '✅' };
            case 'pending':
                return { text: '대기중', color: '#FF9800', icon: '⏳' };
        }
    };

    const statusBadge = getStatusBadge();

    const getFinalDecisionBadge = () => {
        if (!session.finalDecision) return null;

        const colors = {
            BUY: '#4CAF50',
            SELL: '#F44336',
            HOLD: '#FF9800'
        };

        return (
            <span
                className="final-decision-badge"
                style={{ backgroundColor: colors[session.finalDecision.action] }}
            >
                {session.finalDecision.action} ({(session.finalDecision.confidence * 100).toFixed(0)}%)
            </span>
        );
    };

    return (
        <div className={`war-room-card ${session.status}`}>
            {/* 카드 헤더 (접혀있을 때 보이는 부분) */}
            <div
                className="card-header"
                onClick={(e) => {
                    e.stopPropagation(); // 부모로 이벤트 전파 방지
                    onToggle();
                }}
            >
                <div className="header-left">
                    <span className="ticker-symbol">{session.ticker}</span>
                    <span
                        className="status-badge"
                        style={{ backgroundColor: statusBadge.color }}
                    >
                        {statusBadge.icon} {statusBadge.text}
                    </span>
                </div>

                <div className="header-right">
                    {session.messages.length > 0 && (
                        <>
                            <span className="debate-progress">
                                AI 토론 {session.messages.filter(m => !m.isDecision).length}/3
                            </span>
                            {session.consensus > 0 && (
                                <span className="consensus-indicator">
                                    합의: {(session.consensus * 100).toFixed(0)}%
                                </span>
                            )}
                            {getFinalDecisionBadge()}
                        </>
                    )}
                    <span className="expand-icon">
                        {isExpanded ? '▼' : '▶'}
                    </span>
                </div>
            </div>

            {/* 카드 본문 (펼쳐졌을 때) */}
            {isExpanded && (
                <div className="card-body">
                    {session.messages.length > 0 ? (
                        <WarRoom
                            debateId={session.id}
                            initialMessages={session.messages}
                            initialConsensus={session.consensus}
                            initialConstitutionalResult={session.constitutionalResult}
                            autoPlay={false}
                            showHeader={false}
                        />
                    ) : (
                        <div className="empty-debate">
                            <p>토론이 아직 시작되지 않았습니다</p>
                            <p className="start-time">
                                시작 예정: {session.startedAt.toLocaleString('ko-KR')}
                            </p>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default WarRoomCard;

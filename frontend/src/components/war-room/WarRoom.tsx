/**
 * War Room - AI 토론 실시간 시각화 (MVP 3+1 System)
 *
 * MVP 3+1 AI Agents의 토론 과정을 카카오톡 스타일로 표시
 *
 * Features:
 * - 실시간 토론 흐름
 * - Agent별 캐릭터 아이콘 (Trader 35%, Risk 35%, Analyst 30%, PM +1)
 * - 찬성/반대 시각화
 * - Hard Rules 검증 결과
 * - Position Sizing 자동 계산
 *
 * 작성일: 2025-12-15
 * 업데이트: 2025-12-31 - MVP Consolidation
 */

import React, { useState, useEffect, useRef } from 'react';
import './WarRoom.css';
import { CONSTITUTION_ARTICLES, getArticleByNumber } from '../../constants/constitution';

// Agent 정의 - MVP 3+1 System + Extended Agents
const AGENTS = {
    trader: {
        name: 'Trader MVP',
        icon: '🧑‍💻',
        color: '#4CAF50',
        role: '공격수 (35%)',
        weight: 0.35,
        focus: 'Attack - Opportunities'
    },
    risk: {
        name: 'Risk MVP',
        icon: '👮',
        color: '#F44336',
        role: '수비수 (35%)',
        weight: 0.35,
        focus: 'Defense + Position Sizing'
    },
    analyst: {
        name: 'Analyst MVP',
        icon: '🕵️',
        color: '#2196F3',
        role: '분석가 (30%)',
        weight: 0.30,
        focus: 'News + Macro + Institutional + ChipWar'
    },
    pm: {
        name: 'PM MVP',
        icon: '🤵',
        color: '#607D8B',
        role: '결정자 (+1)',
        weight: 'final',
        focus: 'Hard Rules + Silence Policy'
    },
    // Extended Agents (Legacy Support)
    macro: {
        name: 'Macro Analyst',
        icon: '🌍',
        color: '#9C27B0',
        role: '매크로 분석',
        weight: 0.25,
        focus: 'Global Macro Trends'
    },
    institutional: {
        name: 'Institutional',
        icon: '🏛️',
        color: '#795548',
        role: '기관 동향',
        weight: 0.20,
        focus: 'Institutional Flow Analysis'
    }
};

interface DebateMessage {
    id: string;
    agent: keyof typeof AGENTS;
    action: 'BUY' | 'SELL' | 'HOLD';
    confidence: number;
    reasoning: string;
    timestamp: Date;
    isDecision?: boolean;
}

interface ConstitutionalResult {
    isValid: boolean;
    violations: string[];
    violatedArticles: string[];
}

interface WarRoomProps {
    debateId?: string;
    autoPlay?: boolean;
    initialMessages?: DebateMessage[];
    initialConsensus?: number;
    initialConstitutionalResult?: ConstitutionalResult | null;
    showHeader?: boolean;
}

const WarRoom: React.FC<WarRoomProps> = ({
    debateId,
    autoPlay = false,
    initialMessages = [],
    initialConsensus = 0,
    initialConstitutionalResult = null,
    showHeader = true
}) => {
    const [messages, setMessages] = useState<DebateMessage[]>(initialMessages);
    const [constitutionalResult, setConstitutionalResult] = useState<ConstitutionalResult | null>(initialConstitutionalResult);
    const [isDebating, setIsDebating] = useState(false);
    const [consensus, setConsensus] = useState<number>(initialConsensus);
    const [showConstitution, setShowConstitution] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    // 자동 스크롤
    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    // 샘플 토론 시뮬레이션 - MVP 3+1 System
    const simulateDebate = async () => {
        setIsDebating(true);
        setMessages([]);
        setConstitutionalResult(null);

        const debateFlow: Omit<DebateMessage, 'id' | 'timestamp'>[] = [
            {
                agent: 'trader',
                action: 'BUY',
                confidence: 0.85,
                reasoning: '[공격수 35%] 강한 수급 신호! NVDA AI 칩 수요 급증. Opportunity Score: 8.5/10'
            },
            {
                agent: 'risk',
                action: 'BUY',
                confidence: 0.75,
                reasoning: '[수비수 35%] Risk Level: MEDIUM. Position Size: $25,000 (5%). Stop Loss: 3%'
            },
            {
                agent: 'analyst',
                action: 'BUY',
                confidence: 0.80,
                reasoning: '[분석가 30%] 종합 Info Score: 7.5/10. 뉴스 긍정, 매크로 양호, 기관 매수 증가. Red Flags: 없음'
            },
            {
                agent: 'pm',
                action: 'BUY',
                confidence: 0.80,
                reasoning: '[PM +1] 합의 도출: 3/3 agents BUY. Hard Rules PASSED. Can Execute: TRUE',
                isDecision: true
            }
        ];

        // 메시지 순차 표시
        for (const msg of debateFlow) {
            await new Promise(resolve => setTimeout(resolve, 1000));

            const newMessage: DebateMessage = {
                ...msg,
                id: Math.random().toString(36),
                timestamp: new Date()
            };

            setMessages(prev => [...prev, newMessage]);

            // 합의 수준 업데이트 (3 voting agents)
            if (msg.agent !== 'pm') {
                const buyVotes = debateFlow
                    .slice(0, debateFlow.indexOf(msg) + 1)
                    .filter(m => m.action === 'BUY' && m.agent !== 'pm').length;
                const totalVotes = 3; // MVP: Trader, Risk, Analyst
                setConsensus(buyVotes / totalVotes);
            }
        }

        // Constitutional 검증
        await new Promise(resolve => setTimeout(resolve, 1500));
        setConstitutionalResult({
            isValid: false,
            violations: ['제3조 위반: 인간 승인이 필요합니다'],
            violatedArticles: ['제3조: 인간 최종 결정권']
        });

        setIsDebating(false);
    };

    // 액션 배지 색상
    const getActionColor = (action: string) => {
        const actionUpper = action?.toUpperCase() || '';
        switch (actionUpper) {
            case 'BUY': return '#4CAF50';          // 녹색 - 긍정
            case 'SELL': return '#F44336';         // 빨강 - 매도
            case 'HOLD': return '#9E9E9E';         // 회색 - 보류
            case 'PASS': return '#9E9E9E';         // 회색 - 패스
            case 'REDUCE_SIZE': return '#E65100';  // 진한 주황 - 축소 (부정적)
            case 'REJECT': return '#D32F2F';       // 진한 빨강 - 거부
            case 'APPROVE': return '#4CAF50';      // 녹색 - 승인
            default: return '#757575';
        }
    };

    const getActionLabel = (action: string) => {
        const actionUpper = action?.toUpperCase() || '';
        const labels: { [key: string]: string } = {
            'BUY': '매수',
            'SELL': '매도',
            'HOLD': '보류',
            'PASS': '패스',
            'REDUCE_SIZE': '축소',
            'REJECT': '거부',
            'APPROVE': '승인'
        };
        return labels[actionUpper] || action;
    };

    return (
        <>
            <div className="war-room">
                {/* 헤더 */}
                {showHeader && (
                    <div className="war-room-header">
                        <h2>🎭 War Room</h2>
                        <p className="subtitle">AI Investment Committee 토론 회의록</p>

                        {/* 합의 레벨 */}
                        {messages.length > 0 && (
                            <div className="consensus-meter">
                                <div className="consensus-label">
                                    합의 수준: {(consensus * 100).toFixed(0)}%
                                </div>
                                <div className="consensus-bar">
                                    <div
                                        className="consensus-fill"
                                        style={{ width: `${consensus * 100}%` }}
                                    />
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {/* 토론 영역 */}
                <div className="debate-messages">
                    {messages.length === 0 ? (
                        <div className="empty-state">
                            <p>토론이 시작되지 않았습니다</p>
                            <button
                                className="btn-start-debate"
                                onClick={simulateDebate}
                                disabled={isDebating}
                            >
                                {isDebating ? '토론 중...' : '샘플 토론 시작'}
                            </button>
                        </div>
                    ) : (
                        <>
                            {messages.map((msg) => {
                                // Fallback to trader if agent not found
                                const agent = AGENTS[msg.agent] || {
                                    name: msg.agent,
                                    icon: '🤖',
                                    color: '#9E9E9E',
                                    role: 'Unknown'
                                };

                                return (
                                    <div
                                        key={msg.id}
                                        className={`message ${msg.isDecision ? 'decision' : ''}`}
                                        style={{ borderLeftColor: agent.color }}
                                    >
                                        {/* Agent 정보 */}
                                        <div className="message-header">
                                            <span className="agent-icon">{agent.icon}</span>
                                            <span className="agent-name" style={{ color: agent.color }}>
                                                {agent.name}
                                            </span>
                                            <span className="agent-role">({agent.role})</span>

                                            {/* 액션 배지 */}
                                            <span
                                                className="action-badge"
                                                style={{ backgroundColor: getActionColor(msg.action) }}
                                            >
                                                {getActionLabel(msg.action)}
                                            </span>

                                            {/* 신뢰도 */}
                                            <span className="confidence">
                                                {(msg.confidence * 100).toFixed(0)}%
                                            </span>
                                        </div>

                                        {/* 메시지 내용 */}
                                        <div className="message-content">
                                            <p>{msg.reasoning}</p>
                                        </div>

                                        {/* 타임스탬프 */}
                                        <div className="message-time">
                                            {msg.timestamp.toLocaleTimeString('ko-KR')}
                                        </div>
                                    </div>
                                );
                            })}

                            {/* Constitutional 검증 결과 */}
                            {constitutionalResult && (
                                <div className={`constitutional-result ${constitutionalResult.isValid ? 'pass' : 'fail'}`}>
                                    <div className="result-header">
                                        <span className="result-icon">
                                            {constitutionalResult.isValid ? '✅' : '❌'}
                                        </span>
                                        <span className="result-title">
                                            헌법 검증: {constitutionalResult.isValid ? 'PASS' : 'FAIL'}
                                        </span>
                                    </div>

                                    {!constitutionalResult.isValid && (
                                        <div className="result-details">
                                            <div className="violations">
                                                <strong>위반 사항:</strong>
                                                <ul>
                                                    {constitutionalResult.violations.map((v, i) => (
                                                        <li key={i}>{v}</li>
                                                    ))}
                                                </ul>
                                            </div>
                                            <div className="articles">
                                                <strong>위반 조항 상세:</strong>
                                                <div className="article-cards">
                                                    {constitutionalResult.violatedArticles.map((articleStr, i) => {
                                                        const articleNum = articleStr.match(/제\d+조/)?.[0];
                                                        const article = articleNum ? getArticleByNumber(articleNum) : null;

                                                        return article ? (
                                                            <div
                                                                key={i}
                                                                className="article-card"
                                                                style={{ borderLeftColor: article.color }}
                                                            >
                                                                <div className="article-header">
                                                                    <span className="article-icon">{article.icon}</span>
                                                                    <span className="article-number">{article.number}</span>
                                                                    <span className="article-title">{article.title}</span>
                                                                </div>
                                                                <div className="article-description">
                                                                    {article.description}
                                                                </div>
                                                            </div>
                                                        ) : (
                                                            <li key={i}>{articleStr}</li>
                                                        );
                                                    })}
                                                </div>
                                                <button
                                                    className="view-constitution-btn"
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        setShowConstitution(!showConstitution);
                                                    }}
                                                >
                                                    {showConstitution ? '❌ 헌법 닫기' : '📜 헌법 전문 보기'}
                                                </button>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            )}

                            <div ref={messagesEndRef} />
                        </>
                    )}
                </div>

                {/* 푸터 - 통계 */}
                {messages.length > 0 && (
                    <div className="war-room-footer">
                        <div className="stat">
                            <span className="stat-label">Agents</span>
                            <span className="stat-value">{messages.filter(m => !m.isDecision).length}/3 (+1 PM)</span>
                        </div>
                        <div className="stat">
                            <span className="stat-label">BUY</span>
                            <span className="stat-value" style={{ color: '#4CAF50' }}>
                                {messages.filter(m => m.action === 'BUY' && !m.isDecision).length}
                            </span>
                        </div>
                        <div className="stat">
                            <span className="stat-label">SELL</span>
                            <span className="stat-value" style={{ color: '#F44336' }}>
                                {messages.filter(m => m.action === 'SELL' && !m.isDecision).length}
                            </span>
                        </div>
                        <div className="stat">
                            <span className="stat-label">HOLD</span>
                            <span className="stat-value" style={{ color: '#FF9800' }}>
                                {messages.filter(m => m.action === 'HOLD' && !m.isDecision).length}
                            </span>
                        </div>
                    </div>
                )}
            </div>

            {/* 헌법 전문 모달 */}
            {
                showConstitution && (
                    <div className="constitution-modal" onClick={() => setShowConstitution(false)}>
                        <div className="constitution-content" onClick={(e) => e.stopPropagation()}>
                            <div className="modal-header">
                                <h2>🏛️ Constitutional AI Trading System</h2>
                                <p className="modal-subtitle">헌법 5대 조항</p>
                                <button className="close-btn" onClick={() => setShowConstitution(false)}>✕</button>
                            </div>

                            <div className="modal-body">
                                {Object.entries(CONSTITUTION_ARTICLES).map(([key, article]) => (
                                    <div
                                        key={key}
                                        className="constitution-article"
                                        style={{ borderLeftColor: article.color }}
                                    >
                                        <div className="article-header">
                                            <span className="article-icon">{article.icon}</span>
                                            <div>
                                                <h3>{article.number}: {article.title}</h3>
                                                <p>{article.description}</p>
                                            </div>
                                        </div>
                                    </div>
                                ))}

                                <div className="constitution-footer">
                                    <p>💎 "수익률이 아닌 안전을 판매하는 AI 투자 위원회"</p>
                                </div>
                            </div>
                        </div>
                    </div>
                )
            }
        </>
    );
};

export default WarRoom;

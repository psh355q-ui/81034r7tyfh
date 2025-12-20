/**
 * LogicTraceViewer - AI 추론 과정 뷰어
 * 
 * Phase F5: 프론트엔드 시각화
 * 
 * 기능:
 * - Step별 추론 과정 표시
 * - 3-AI 토론 요약
 * - 타임라인/아코디언 스타일
 */

import React, { useState } from 'react';

// 타입 정의
interface ReasoningStep {
    id: string;
    stepNumber: number;
    title: string;
    description: string;
    inputs: string[];
    output: string;
    confidence: number;
    timestamp: string;
}

interface AIVote {
    agent: string;
    vote: 'BUY' | 'SELL' | 'HOLD' | 'ABSTAIN';
    confidence: number;
    reasoning: string;
    role?: string;
}

interface DebateSummary {
    ticker: string;
    topic: string;
    votes: AIVote[];
    finalDecision: string;
    consensusStrength: number;
    dissenting: string[];
    timestamp: string;
}

interface LogicTrace {
    id: string;
    ticker: string;
    signal: string;
    steps: ReasoningStep[];
    debate?: DebateSummary;
    totalTime: number;
    confidence: number;
}

// AI 에이전트 정보
const AI_AGENTS: Record<string, { name: string; color: string; icon: string }> = {
    claude: { name: 'Claude', color: '#D97706', icon: '🟠' },
    chatgpt: { name: 'ChatGPT', color: '#10B981', icon: '🟢' },
    gemini: { name: 'Gemini', color: '#3B82F6', icon: '🔵' },
};

// 투표 색상
const VOTE_COLORS: Record<string, string> = {
    BUY: '#10B981',
    SELL: '#EF4444',
    HOLD: '#6B7280',
    ABSTAIN: '#9CA3AF',
};

// 추론 단계 컴포넌트
const StepCard: React.FC<{ step: ReasoningStep; isExpanded: boolean; onToggle: () => void }> = ({
    step,
    isExpanded,
    onToggle
}) => {
    return (
        <div className={`step-card ${isExpanded ? 'expanded' : ''}`}>
            <div className="step-header" onClick={onToggle}>
                <div className="step-number">{step.stepNumber}</div>
                <div className="step-info">
                    <h4 className="step-title">{step.title}</h4>
                    <span className="step-confidence">
                        신뢰도: {(step.confidence * 100).toFixed(0)}%
                    </span>
                </div>
                <span className="expand-icon">{isExpanded ? '▼' : '▶'}</span>
            </div>

            {isExpanded && (
                <div className="step-content">
                    <p className="step-description">{step.description}</p>

                    <div className="step-inputs">
                        <span className="input-label">입력:</span>
                        {step.inputs.map((input, idx) => (
                            <span key={idx} className="input-tag">{input}</span>
                        ))}
                    </div>

                    <div className="step-output">
                        <span className="output-label">출력:</span>
                        <span className="output-text">{step.output}</span>
                    </div>
                </div>
            )}
        </div>
    );
};

// AI 투표 카드 컴포넌트
const VoteCard: React.FC<{ vote: AIVote }> = ({ vote }) => {
    const agent = AI_AGENTS[vote.agent] || { name: vote.agent, color: '#6B7280', icon: '⚪' };
    const voteColor = VOTE_COLORS[vote.vote] || '#6B7280';

    return (
        <div className="vote-card" style={{ borderColor: agent.color }}>
            <div className="vote-header">
                <span className="agent-icon">{agent.icon}</span>
                <span className="agent-name">{agent.name}</span>
                {vote.role && <span className="agent-role">{vote.role}</span>}
            </div>

            <div className="vote-decision" style={{ color: voteColor }}>
                {vote.vote}
            </div>

            <div className="vote-confidence">
                <div className="confidence-bar">
                    <div
                        className="confidence-fill"
                        style={{ width: `${vote.confidence * 100}%`, backgroundColor: voteColor }}
                    />
                </div>
                <span>{(vote.confidence * 100).toFixed(0)}%</span>
            </div>

            <p className="vote-reasoning">{vote.reasoning}</p>
        </div>
    );
};

// 토론 요약 컴포넌트
const DebatePanel: React.FC<{ debate: DebateSummary }> = ({ debate }) => {
    const consensusColor = debate.consensusStrength >= 0.8 ? '#10B981' :
        debate.consensusStrength >= 0.6 ? '#F59E0B' : '#EF4444';

    return (
        <div className="debate-panel">
            <div className="debate-header">
                <h4>🗣️ AI 토론</h4>
                <span className="debate-topic">{debate.topic}</span>
            </div>

            <div className="votes-grid">
                {debate.votes.map((vote, idx) => (
                    <VoteCard key={idx} vote={vote} />
                ))}
            </div>

            <div className="debate-result">
                <div className="final-decision">
                    <span className="result-label">최종 결정:</span>
                    <span className="result-value" style={{ color: VOTE_COLORS[debate.finalDecision] }}>
                        {debate.finalDecision}
                    </span>
                </div>

                <div className="consensus-meter">
                    <span className="result-label">합의 강도:</span>
                    <div className="meter-bar">
                        <div
                            className="meter-fill"
                            style={{
                                width: `${debate.consensusStrength * 100}%`,
                                backgroundColor: consensusColor
                            }}
                        />
                    </div>
                    <span style={{ color: consensusColor }}>
                        {(debate.consensusStrength * 100).toFixed(0)}%
                    </span>
                </div>

                {debate.dissenting.length > 0 && (
                    <div className="dissenting">
                        <span className="result-label">반대 의견:</span>
                        <span>{debate.dissenting.join(', ')}</span>
                    </div>
                )}
            </div>
        </div>
    );
};

// 메인 컴포넌트
const LogicTraceViewer: React.FC<{ trace?: LogicTrace }> = ({ trace: propTrace }) => {
    const [expandedSteps, setExpandedSteps] = useState<Set<string>>(new Set());
    const [showDebate, setShowDebate] = useState(true);

    // 샘플 데이터
    const trace: LogicTrace = propTrace || {
        id: 'trace_001',
        ticker: 'NVDA',
        signal: 'BUY',
        totalTime: 2340,
        confidence: 0.87,
        steps: [
            {
                id: 's1',
                stepNumber: 1,
                title: '시장 데이터 수집',
                description: 'Yahoo Finance, SEC EDGAR에서 최신 데이터 수집',
                inputs: ['NVDA ticker', 'Last 30 days'],
                output: 'Price: $142.50, Vol: 45M, P/E: 65',
                confidence: 0.95,
                timestamp: new Date().toISOString()
            },
            {
                id: 's2',
                stepNumber: 2,
                title: '뉴스 분석',
                description: 'AI 반도체 수요 관련 뉴스 25건 분석',
                inputs: ['News API', 'Keyword: AI chip'],
                output: 'Positive sentiment 82%, HBM demand surge',
                confidence: 0.88,
                timestamp: new Date().toISOString()
            },
            {
                id: 's3',
                stepNumber: 3,
                title: '글로벌 매크로 분석',
                description: 'US 금리, 반도체 수출 규제, AI 투자 동향',
                inputs: ['FRED API', 'Country Risk'],
                output: 'Favorable macro, US risk moderate',
                confidence: 0.75,
                timestamp: new Date().toISOString()
            },
            {
                id: 's4',
                stepNumber: 4,
                title: 'AI 앙상블 투표',
                description: '3개 AI 모델의 종합 판단',
                inputs: ['Claude', 'ChatGPT', 'Gemini'],
                output: 'BUY (2/3), Consensus: 87%',
                confidence: 0.87,
                timestamp: new Date().toISOString()
            }
        ],
        debate: {
            ticker: 'NVDA',
            topic: 'BUY 결정',
            votes: [
                { agent: 'claude', vote: 'BUY', confidence: 0.85, reasoning: 'AI chip demand remains strong. HBM4 supply contract secured.', role: '리스크 컨트롤러' },
                { agent: 'chatgpt', vote: 'HOLD', confidence: 0.72, reasoning: 'Valuation concerns at P/E 65. Wait for pullback.', role: '섹터 스페셜리스트' },
                { agent: 'gemini', vote: 'BUY', confidence: 0.88, reasoning: 'Macro favorable. AI capex cycle just beginning.', role: '매크로 전략가' },
            ],
            finalDecision: 'BUY',
            consensusStrength: 0.87,
            dissenting: ['chatgpt'],
            timestamp: new Date().toISOString()
        }
    };

    const toggleStep = (stepId: string) => {
        const newExpanded = new Set(expandedSteps);
        if (newExpanded.has(stepId)) {
            newExpanded.delete(stepId);
        } else {
            newExpanded.add(stepId);
        }
        setExpandedSteps(newExpanded);
    };

    const expandAll = () => {
        setExpandedSteps(new Set(trace.steps.map(s => s.id)));
    };

    const collapseAll = () => {
        setExpandedSteps(new Set());
    };

    return (
        <div className="logic-trace-viewer">
            <style>{`
        .logic-trace-viewer {
          padding: 24px;
          background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
          min-height: 100vh;
          color: #e0e0e0;
        }
        
        .trace-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 24px;
        }
        
        .trace-title {
          display: flex;
          align-items: center;
          gap: 12px;
        }
        
        .trace-title h2 {
          font-size: 24px;
          font-weight: 700;
          color: #fff;
        }
        
        .signal-badge {
          padding: 6px 16px;
          border-radius: 20px;
          font-weight: 600;
          font-size: 14px;
        }
        
        .trace-meta {
          display: flex;
          gap: 16px;
          color: #a0aec0;
          font-size: 14px;
        }
        
        .controls {
          display: flex;
          gap: 8px;
        }
        
        .control-btn {
          background: rgba(255, 255, 255, 0.1);
          border: none;
          color: #e0e0e0;
          padding: 8px 16px;
          border-radius: 8px;
          cursor: pointer;
          transition: background 0.2s;
        }
        
        .control-btn:hover {
          background: rgba(255, 255, 255, 0.2);
        }
        
        .section-title {
          font-size: 18px;
          font-weight: 600;
          margin: 24px 0 16px;
          color: #a0aec0;
        }
        
        .timeline {
          position: relative;
          padding-left: 32px;
        }
        
        .timeline::before {
          content: '';
          position: absolute;
          left: 16px;
          top: 0;
          bottom: 0;
          width: 2px;
          background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
        }
        
        .step-card {
          background: rgba(255, 255, 255, 0.05);
          border-radius: 12px;
          margin-bottom: 12px;
          overflow: hidden;
          transition: all 0.2s;
        }
        
        .step-card:hover {
          background: rgba(255, 255, 255, 0.08);
        }
        
        .step-header {
          display: flex;
          align-items: center;
          padding: 16px;
          cursor: pointer;
        }
        
        .step-number {
          width: 32px;
          height: 32px;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-weight: 600;
          margin-right: 16px;
        }
        
        .step-info {
          flex: 1;
        }
        
        .step-title {
          margin: 0;
          font-size: 16px;
          color: #fff;
        }
        
        .step-confidence {
          font-size: 12px;
          color: #a0aec0;
        }
        
        .expand-icon {
          color: #6B7280;
        }
        
        .step-content {
          padding: 0 16px 16px 64px;
          border-top: 1px solid rgba(255, 255, 255, 0.05);
        }
        
        .step-description {
          margin: 12px 0;
          color: #a0aec0;
        }
        
        .step-inputs, .step-output {
          display: flex;
          align-items: center;
          gap: 8px;
          margin: 8px 0;
          flex-wrap: wrap;
        }
        
        .input-label, .output-label {
          font-size: 12px;
          color: #6B7280;
          min-width: 40px;
        }
        
        .input-tag {
          background: rgba(102, 126, 234, 0.2);
          padding: 4px 10px;
          border-radius: 4px;
          font-size: 12px;
        }
        
        .output-text {
          font-size: 14px;
          color: #10B981;
        }
        
        /* Debate Panel */
        .debate-panel {
          background: rgba(255, 255, 255, 0.05);
          border-radius: 12px;
          padding: 20px;
          margin-top: 24px;
        }
        
        .debate-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 20px;
        }
        
        .debate-header h4 {
          margin: 0;
          font-size: 18px;
          color: #fff;
        }
        
        .debate-topic {
          background: rgba(102, 126, 234, 0.3);
          padding: 4px 12px;
          border-radius: 12px;
          font-size: 13px;
        }
        
        .votes-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 16px;
          margin-bottom: 20px;
        }
        
        .vote-card {
          background: rgba(255, 255, 255, 0.03);
          border-radius: 10px;
          padding: 16px;
          border-left: 3px solid;
        }
        
        .vote-header {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 12px;
        }
        
        .agent-icon { font-size: 18px; }
        .agent-name {
          font-weight: 600;
          flex: 1;
        }
        
        .agent-role {
          font-size: 10px;
          background: rgba(255, 255, 255, 0.1);
          padding: 2px 6px;
          border-radius: 4px;
          color: #a0aec0;
        }
        
        .vote-decision {
          font-size: 24px;
          font-weight: 700;
          margin-bottom: 8px;
        }
        
        .vote-confidence {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 12px;
        }
        
        .confidence-bar {
          flex: 1;
          height: 6px;
          background: rgba(255, 255, 255, 0.1);
          border-radius: 3px;
          overflow: hidden;
        }
        
        .confidence-fill {
          height: 100%;
          border-radius: 3px;
        }
        
        .vote-reasoning {
          font-size: 13px;
          color: #a0aec0;
          line-height: 1.5;
          margin: 0;
        }
        
        .debate-result {
          display: flex;
          gap: 24px;
          align-items: center;
          padding-top: 16px;
          border-top: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .final-decision, .consensus-meter, .dissenting {
          display: flex;
          align-items: center;
          gap: 8px;
        }
        
        .result-label {
          font-size: 13px;
          color: #6B7280;
        }
        
        .result-value {
          font-size: 18px;
          font-weight: 700;
        }
        
        .meter-bar {
          width: 100px;
          height: 8px;
          background: rgba(255, 255, 255, 0.1);
          border-radius: 4px;
          overflow: hidden;
        }
        
        .meter-fill {
          height: 100%;
          border-radius: 4px;
        }
        
        @media (max-width: 768px) {
          .votes-grid {
            grid-template-columns: 1fr;
          }
          .debate-result {
            flex-direction: column;
            align-items: flex-start;
          }
        }
      `}</style>

            <div className="trace-header">
                <div className="trace-title">
                    <h2>🔍 {trace.ticker} 분석 추적</h2>
                    <span
                        className="signal-badge"
                        style={{
                            backgroundColor: VOTE_COLORS[trace.signal] || '#6B7280',
                            color: '#fff'
                        }}
                    >
                        {trace.signal}
                    </span>
                </div>
                <div className="trace-meta">
                    <span>⏱️ {trace.totalTime}ms</span>
                    <span>🎯 {(trace.confidence * 100).toFixed(0)}%</span>
                </div>
            </div>

            <div className="controls">
                <button className="control-btn" onClick={expandAll}>전체 펼치기</button>
                <button className="control-btn" onClick={collapseAll}>전체 접기</button>
                <button
                    className="control-btn"
                    onClick={() => setShowDebate(!showDebate)}
                >
                    {showDebate ? '토론 숨기기' : '토론 보기'}
                </button>
            </div>

            <h3 className="section-title">📋 추론 단계</h3>
            <div className="timeline">
                {trace.steps.map(step => (
                    <StepCard
                        key={step.id}
                        step={step}
                        isExpanded={expandedSteps.has(step.id)}
                        onToggle={() => toggleStep(step.id)}
                    />
                ))}
            </div>

            {showDebate && trace.debate && (
                <DebatePanel debate={trace.debate} />
            )}
        </div>
    );
};

export default LogicTraceViewer;

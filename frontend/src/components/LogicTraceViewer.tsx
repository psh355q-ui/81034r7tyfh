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

// 추론 단계 컴포넌트 (Restyled for Light Theme)
const StepCard: React.FC<{ step: ReasoningStep; isExpanded: boolean; onToggle: () => void }> = ({
  step,
  isExpanded,
  onToggle
}) => {
  return (
    <div className={`bg-white border rounded-lg transition-all duration-200 ${isExpanded ? 'border-blue-300 shadow-md ring-1 ring-blue-100' : 'border-gray-200 hover:border-gray-300'}`}>
      <div className="flex items-center p-4 cursor-pointer" onClick={onToggle}>
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center font-bold mr-4 -ml-10 z-10 border-4 border-white shadow-sm">
          {step.stepNumber}
        </div>
        <div className="flex-1">
          <h4 className="font-semibold text-gray-900">{step.title}</h4>
        </div>
        <div className="text-sm text-gray-500 mr-4">
          Confidence: {(step.confidence * 100).toFixed(0)}%
        </div>
        <span className="text-gray-400">{isExpanded ? '▼' : '▶'}</span>
      </div>

      {isExpanded && (
        <div className="px-4 pb-4 pl-12">
          <p className="text-gray-600 mb-3">{step.description}</p>

          <div className="flex flex-wrap gap-2 mb-2 items-center">
            <span className="text-xs font-semibold text-gray-500 uppercase w-12">Input</span>
            {step.inputs.map((input, idx) => (
              <span key={idx} className="bg-gray-100 text-gray-600 px-2 py-1 rounded text-xs border border-gray-200">
                {input}
              </span>
            ))}
          </div>

          <div className="flex gap-2 items-center">
            <span className="text-xs font-semibold text-gray-500 uppercase w-12">Output</span>
            <span className="text-sm text-green-700 font-medium bg-green-50 px-2 py-1 rounded border border-green-100">
              {step.output}
            </span>
          </div>
        </div>
      )}
    </div>
  );
};

// AI 투표 카드 컴포넌트 (Restyled)
const VoteCard: React.FC<{ vote: AIVote }> = ({ vote }) => {
  const agent = AI_AGENTS[vote.agent] || { name: vote.agent, color: '#6B7280', icon: '⚪' };
  const voteColor = VOTE_COLORS[vote.vote] || '#6B7280';

  return (
    <div className="bg-white border rounded-lg p-4 shadow-sm relative overflow-hidden">
      <div className="absolute top-0 left-0 w-1 h-full" style={{ backgroundColor: agent.color }} />

      <div className="flex items-center gap-2 mb-3">
        <span className="text-xl">{agent.icon}</span>
        <div className="flex-1">
          <div className="font-bold text-gray-900 leading-tight">{agent.name}</div>
          {vote.role && <div className="text-xs text-gray-500">{vote.role}</div>}
        </div>
      </div>

      <div className="text-2xl font-bold mb-2" style={{ color: voteColor }}>
        {vote.vote}
      </div>

      <div className="flex items-center gap-2 mb-3">
        <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
          <div className="h-full rounded-full" style={{ width: `${vote.confidence * 100}%`, backgroundColor: voteColor }} />
        </div>
        <span className="text-xs font-medium text-gray-500">{(vote.confidence * 100).toFixed(0)}%</span>
      </div>

      <p className="text-sm text-gray-600 bg-gray-50 p-2 rounded border border-gray-100 min-h-[60px]">
        "{vote.reasoning}"
      </p>
    </div>
  );
};

// 토론 요약 컴포넌트 (Restyled)
const DebatePanel: React.FC<{ debate: DebateSummary }> = ({ debate }) => {
  const consensusColor = debate.consensusStrength >= 0.8 ? '#10B981' :
    debate.consensusStrength >= 0.6 ? '#F59E0B' : '#EF4444';

  return (
    <div className="bg-gray-50 rounded-xl p-6 border border-gray-200">
      <div className="flex justify-between items-center mb-6">
        <h4 className="text-lg font-bold text-gray-800 flex items-center gap-2">
          🗣️ AI Debate: <span className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-base font-normal">{debate.topic}</span>
        </h4>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        {debate.votes.map((vote, idx) => (
          <VoteCard key={idx} vote={vote} />
        ))}
      </div>

      <div className="flex flex-col md:flex-row gap-6 p-4 bg-white rounded-lg border border-gray-200 shadow-sm">
        <div className="flex items-center gap-3">
          <span className="text-sm font-semibold text-gray-500 uppercase">Final Decision</span>
          <span className="text-xl font-bold" style={{ color: VOTE_COLORS[debate.finalDecision] }}>{debate.finalDecision}</span>
        </div>

        <div className="flex items-center gap-3 flex-1">
          <span className="text-sm font-semibold text-gray-500 uppercase">Consensus Strength</span>
          <div className="flex-1 h-3 bg-gray-100 rounded-full overflow-hidden max-w-[200px]">
            <div className="h-full rounded-full" style={{ width: `${debate.consensusStrength * 100}%`, backgroundColor: consensusColor }} />
          </div>
          <span className="font-bold" style={{ color: consensusColor }}>{(debate.consensusStrength * 100).toFixed(0)}%</span>
        </div>

        {debate.dissenting.length > 0 && (
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold text-gray-500 uppercase">Dissenting</span>
            <div className="flex gap-1">
              {debate.dissenting.map(agent => (
                <span key={agent} className="px-2 py-0.5 bg-red-100 text-red-600 rounded text-xs font-semibold">
                  {AI_AGENTS[agent]?.name || agent}
                </span>
              ))}
            </div>
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

  // 샘플 데이터 (If prop not provided)
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
        title: 'Market Data Collection',
        description: 'Fetched latest price and volume data from Yahoo Finance & SEC EDGAR',
        inputs: ['NVDA ticker', 'Last 30 days'],
        output: 'Price: $142.50, Vol: 45M, P/E: 65',
        confidence: 0.95,
        timestamp: new Date().toISOString()
      },
      {
        id: 's2',
        stepNumber: 2,
        title: 'News Analysis',
        description: 'Analyzed 25 news articles related to AI demand',
        inputs: ['News API', 'Keyword: AI chip'],
        output: 'Positive sentiment 82%, HBM demand surge',
        confidence: 0.88,
        timestamp: new Date().toISOString()
      },
      {
        id: 's3',
        stepNumber: 3,
        title: 'Global Macro Context',
        description: 'Assessed US interest rates and semiconductor export controls',
        inputs: ['FRED API', 'Country Risk'],
        output: 'Favorable macro, US risk moderate',
        confidence: 0.75,
        timestamp: new Date().toISOString()
      },
      {
        id: 's4',
        stepNumber: 4,
        title: 'AI Ensemble Voting',
        description: 'Consensus decision from 3 AI models',
        inputs: ['Claude', 'ChatGPT', 'Gemini'],
        output: 'BUY (2/3), Consensus: 87%',
        confidence: 0.87,
        timestamp: new Date().toISOString()
      }
    ],
    debate: {
      ticker: 'NVDA',
      topic: 'BUY Decision',
      votes: [
        { agent: 'claude', vote: 'BUY', confidence: 0.85, reasoning: 'AI chip demand remains strong. HBM4 supply contract secured.', role: 'Risk Controller' },
        { agent: 'chatgpt', vote: 'HOLD', confidence: 0.72, reasoning: 'Valuation concerns at P/E 65. Wait for pullback.', role: 'Sector Specialist' },
        { agent: 'gemini', vote: 'BUY', confidence: 0.88, reasoning: 'Macro favorable. AI capex cycle just beginning.', role: 'Macro Strategist' },
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
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex justify-between items-center mb-6">
        <div className="flex items-center gap-3">
          <h2 className="text-xl font-bold text-gray-900">🔍 Analysis Trace: {trace.ticker}</h2>
          <span
            className="px-3 py-1 rounded-full text-sm font-bold text-white shadow-sm"
            style={{
              backgroundColor: VOTE_COLORS[trace.signal] || '#6B7280',
            }}
          >
            {trace.signal}
          </span>
        </div>
        <div className="flex items-center gap-4 text-sm text-gray-500">
          <span>⏱️ {trace.totalTime}ms</span>
          <span>🎯 {(trace.confidence * 100).toFixed(0)}% Confidence</span>
        </div>
      </div>

      <div className="flex gap-2 mb-6">
        <button
          onClick={expandAll}
          className="px-3 py-1.5 bg-gray-100 text-gray-700 rounded hover:bg-gray-200 text-sm font-medium transition-colors"
        >
          Expand All
        </button>
        <button
          onClick={collapseAll}
          className="px-3 py-1.5 bg-gray-100 text-gray-700 rounded hover:bg-gray-200 text-sm font-medium transition-colors"
        >
          Collapse All
        </button>
        <button
          onClick={() => setShowDebate(!showDebate)}
          className="px-3 py-1.5 bg-blue-50 text-blue-600 rounded hover:bg-blue-100 text-sm font-medium transition-colors"
        >
          {showDebate ? 'Hide Debate' : 'Show Debate'}
        </button>
      </div>

      <h3 className="text-lg font-semibold text-gray-800 mb-4 border-b pb-2">📋 Reasoning Steps</h3>
      <div className="space-y-4 relative pl-8 before:absolute before:left-4 before:top-4 before:bottom-4 before:w-0.5 before:bg-gray-200">
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
        <div className="mt-8 pt-6 border-t border-gray-200">
          <DebatePanel debate={trace.debate} />
        </div>
      )}
    </div>
  );
};



export default LogicTraceViewer;

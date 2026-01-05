/**
 * JourneyTimeline - Investment Decision History & Coaching
 * 
 * 📊 Data Sources:
 *   - API: /api/journey/history
 *   - API: /api/journey/quality-score
 * 
 * 📤 Used By:
 *   - PersonaDashboard.tsx
 * 
 * 📝 Notes:
 *   - Shows past investment decisions
 *   - Displays quality score (fear response, greed response, etc.)
 *   - Provides AI coaching insights
 */

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import {
    History,
    TrendingUp,
    TrendingDown,
    Brain,
    AlertCircle,
    CheckCircle,
    Clock
} from 'lucide-react';
import { getJourneyHistory, getQualityScore, JourneyHistory, QualityScore } from '../../services/personaApi';
import { Card } from '../common/Card';
import { LoadingSpinner } from '../common/LoadingSpinner';

const DECISION_TYPE_COLORS: Record<string, { bg: string; text: string; icon: React.ReactNode }> = {
    buy: { bg: 'bg-green-100', text: 'text-green-700', icon: <TrendingUp size={14} /> },
    sell: { bg: 'bg-red-100', text: 'text-red-700', icon: <TrendingDown size={14} /> },
    hold: { bg: 'bg-gray-100', text: 'text-gray-700', icon: <Clock size={14} /> },
    panic_sell: { bg: 'bg-red-200', text: 'text-red-800', icon: <AlertCircle size={14} /> },
    fomo_buy: { bg: 'bg-amber-100', text: 'text-amber-700', icon: <AlertCircle size={14} /> },
};

const MARKET_CONDITION_LABELS: Record<string, string> = {
    fear: '공포 구간',
    greed: '탐욕 구간',
    neutral: '중립',
    high_vol: '고변동성',
    trending_up: '상승 추세',
    trending_down: '하락 추세',
};

export const JourneyTimeline: React.FC = () => {
    const { data: history, isLoading: historyLoading } = useQuery<JourneyHistory>({
        queryKey: ['journey-history'],
        queryFn: () => getJourneyHistory(10),
        refetchInterval: 60000,
    });

    const { data: quality } = useQuery<QualityScore>({
        queryKey: ['quality-score'],
        queryFn: getQualityScore,
        refetchInterval: 60000,
    });

    if (historyLoading) {
        return (
            <Card className="h-[400px] flex items-center justify-center">
                <LoadingSpinner />
            </Card>
        );
    }

    return (
        <Card>
            <div className="flex items-center gap-2 mb-4">
                <History className="text-purple-500" size={20} />
                <h3 className="font-semibold text-gray-800">투자 여정</h3>
            </div>

            {/* Quality Scores */}
            {quality && (
                <div className="grid grid-cols-2 gap-3 mb-6">
                    <ScoreCard
                        label="공포 대응"
                        score={quality.scores.fear_response}
                        color="blue"
                    />
                    <ScoreCard
                        label="탐욕 대응"
                        score={quality.scores.greed_response}
                        color="amber"
                    />
                    <ScoreCard
                        label="일관성"
                        score={quality.scores.consistency}
                        color="green"
                    />
                    <ScoreCard
                        label="규율"
                        score={quality.scores.discipline}
                        color="purple"
                    />
                </div>
            )}

            {/* Insights */}
            {quality?.insights && quality.insights.length > 0 && (
                <div className="mb-4 p-3 bg-purple-50 rounded-lg">
                    <div className="flex items-center gap-2 mb-2">
                        <Brain className="text-purple-600" size={16} />
                        <span className="text-sm font-medium text-purple-700">AI 인사이트</span>
                    </div>
                    <ul className="space-y-1">
                        {quality.insights.map((insight, idx) => (
                            <li key={idx} className="text-sm text-purple-600 flex items-start gap-1">
                                <span className="mt-0.5">💡</span>
                                {insight}
                            </li>
                        ))}
                    </ul>
                </div>
            )}

            {/* Decision Timeline */}
            <div className="space-y-3 max-h-[300px] overflow-y-auto">
                {history?.decisions && history.decisions.length > 0 ? (
                    history.decisions.map((decision) => {
                        const style = DECISION_TYPE_COLORS[decision.decision_type] ||
                            DECISION_TYPE_COLORS.hold;

                        return (
                            <div
                                key={decision.decision_id}
                                className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg"
                            >
                                <div className={`p-1.5 rounded-full ${style.bg}`}>
                                    {style.icon}
                                </div>
                                <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-2 flex-wrap">
                                        <span className="font-semibold text-gray-900">
                                            {decision.ticker}
                                        </span>
                                        <span className={`px-2 py-0.5 text-xs rounded-full ${style.bg} ${style.text}`}>
                                            {decision.decision_type.toUpperCase()}
                                        </span>
                                        <span className="text-xs text-gray-500">
                                            {MARKET_CONDITION_LABELS[decision.market_condition] || decision.market_condition}
                                        </span>
                                    </div>
                                    <p className="text-sm text-gray-600 mt-1 truncate">
                                        {decision.quantity}주 @ ${decision.entry_price.toFixed(2)}
                                    </p>
                                    {decision.outcome_30d !== null && (
                                        <p className={`text-xs mt-1 ${decision.outcome_30d >= 0 ? 'text-green-600' : 'text-red-600'
                                            }`}>
                                            30일 후: {decision.outcome_30d >= 0 ? '+' : ''}{decision.outcome_30d.toFixed(1)}%
                                        </p>
                                    )}
                                    <p className="text-xs text-gray-400 mt-1">
                                        {new Date(decision.decision_date).toLocaleDateString()}
                                    </p>
                                </div>
                                {decision.followed_ai && (
                                    <CheckCircle className="text-green-500 flex-shrink-0" size={16} />
                                )}
                            </div>
                        );
                    })
                ) : (
                    <div className="text-center py-8 text-gray-500">
                        아직 기록된 결정이 없습니다.
                    </div>
                )}
            </div>
        </Card>
    );
};

interface ScoreCardProps {
    label: string;
    score: number;
    color: 'blue' | 'amber' | 'green' | 'purple';
}

const ScoreCard: React.FC<ScoreCardProps> = ({ label, score, color }) => {
    const colorClasses = {
        blue: 'bg-blue-50 text-blue-700',
        amber: 'bg-amber-50 text-amber-700',
        green: 'bg-green-50 text-green-700',
        purple: 'bg-purple-50 text-purple-700',
    };

    return (
        <div className={`p-3 rounded-lg ${colorClasses[color]}`}>
            <p className="text-xs opacity-75">{label}</p>
            <p className="text-xl font-bold">{score.toFixed(0)}</p>
        </div>
    );
};

export default JourneyTimeline;

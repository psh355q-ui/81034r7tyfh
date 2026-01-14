import React from 'react';
import { Card } from '../common/Card';
import { Badge } from '../common/Badge';

interface FusionFactor {
    category: string;
    score: number; // -1.0 to 1.0 or 0 to 100
    weight: number;
    description?: string;
}

interface FusionScorecardProps {
    totalScore: number; // 0 to 100
    factors: FusionFactor[];
    confidence: number;
}

export const FusionScorecard: React.FC<FusionScorecardProps> = ({ totalScore, factors, confidence }) => {

    const getScoreColor = (score: number) => {
        if (score >= 70) return 'text-green-500';
        if (score >= 40) return 'text-yellow-500';
        return 'text-red-500';
    };

    const getBarColor = (score: number) => {
        if (score >= 70) return 'bg-green-500';
        if (score >= 40) return 'bg-yellow-500';
        return 'bg-red-500';
    };

    return (
        <Card title="Fusion Engine Scorecard (v2.0)">
            <div className="flex items-center justify-between mb-6">
                <div className="text-center">
                    <p className="text-sm text-gray-500 mb-1">Total Fusion Score</p>
                    <div className={`text-4xl font-bold ${getScoreColor(totalScore)}`}>
                        {totalScore.toFixed(0)}
                    </div>
                </div>
                <div className="text-center">
                    <p className="text-sm text-gray-500 mb-1">AI Confidence</p>
                    <Badge variant={confidence > 0.8 ? 'success' : confidence > 0.5 ? 'warning' : 'danger'}>
                        {(confidence * 100).toFixed(0)}%
                    </Badge>
                </div>
            </div>

            <div className="space-y-4">
                {factors.map((factor, idx) => (
                    <div key={idx}>
                        <div className="flex justify-between text-sm mb-1">
                            <span className="font-medium text-gray-700">{factor.category}</span>
                            <span className="text-gray-500">{factor.score.toFixed(0)}/100</span>
                        </div>
                        <div className="h-2.5 w-full bg-gray-200 rounded-full h-2">
                            <div
                                className={`h-2.5 rounded-full ${getBarColor(factor.score)}`}
                                style={{ width: `${factor.score}%` }}
                            ></div>
                        </div>
                        {factor.description && (
                            <p className="text-xs text-gray-400 mt-1">{factor.description}</p>
                        )}
                    </div>
                ))}
            </div>

            <div className="mt-6 pt-4 border-t border-gray-100">
                <p className="text-xs text-gray-400 text-center">
                    Powered by Multi-Modal Fusion Engine (RL + GNN + Sentiment)
                </p>
            </div>
        </Card>
    );
};

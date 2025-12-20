/**
 * News Badges Component
 * 
 * Displays visual indicators for news analysis results:
 * - Sentiment badge (color-coded)
 * - Urgency indicator (emoji)
 * - Actionable star
 */

import React from 'react';

interface NewsBadgesProps {
    sentiment?: string | null;
    urgency?: string | null;
    actionable?: boolean;
}

export const NewsBadges: React.FC<NewsBadgesProps> = ({ sentiment, urgency, actionable }) => {
    if (!sentiment && !urgency && !actionable) return null;

    return (
        <div className="flex items-center space-x-1 flex-wrap gap-1">
            {/* Sentiment Badge */}
            {sentiment && (
                <span className={`px-2 py-0.5 text-xs font-medium rounded ${sentiment.toLowerCase() === 'positive' ? 'bg-green-100 text-green-700' :
                        sentiment.toLowerCase() === 'negative' ? 'bg-red-100 text-red-700' :
                            sentiment.toLowerCase() === 'mixed' ? 'bg-yellow-100 text-yellow-700' :
                                'bg-gray-100 text-gray-700'
                    }`}>
                    {sentiment}
                </span>
            )}

            {/* Urgency Indicator */}
            {urgency && (
                <span title={`Urgency: ${urgency}`} className="text-sm">
                    {urgency.toLowerCase() === 'high' || urgency.toLowerCase() === 'critical' ? '🔴' :
                        urgency.toLowerCase() === 'medium' ? '🟡' :
                            '🟢'}
                </span>
            )}

            {/* Actionable Star */}
            {actionable && (
                <span title="Actionable" className="text-sm">⭐</span>
            )}
        </div>
    );
};

import React from 'react';
import { AIDecision } from '../../services/api';
import {
    TrendingUp,
    TrendingDown,
    MinusCircle,
    XCircle,
    Activity,
    AlertCircle
} from 'lucide-react';

interface PortfolioActionCardProps {
    decision: AIDecision;
}

const getStyles = (actionType: string | undefined) => {
    switch (actionType) {
        case 'buy':
            return {
                bg: 'bg-green-50',
                border: 'border-green-200',
                text: 'text-green-800',
                badgeBg: 'bg-green-100'
            };
        case 'buy_more':
            return {
                bg: 'bg-emerald-50',
                border: 'border-emerald-200',
                text: 'text-emerald-800',
                badgeBg: 'bg-emerald-100'
            };
        case 'sell':
            return {
                bg: 'bg-red-50',
                border: 'border-red-200',
                text: 'text-red-800',
                badgeBg: 'bg-red-100'
            };
        case 'reduce_size':
            return {
                bg: 'bg-rose-50',
                border: 'border-rose-200',
                text: 'text-rose-800',
                badgeBg: 'bg-rose-100'
            };
        case 'do_not_buy':
            return {
                bg: 'bg-orange-50',
                border: 'border-orange-200',
                text: 'text-orange-800',
                badgeBg: 'bg-orange-100'
            };
        default:
            return {
                bg: 'bg-gray-50',
                border: 'border-gray-200',
                text: 'text-gray-800',
                badgeBg: 'bg-gray-100'
            };
    }
};

const getStrengthColor = (strength: string | undefined) => {
    switch (strength) {
        case 'strong': return 'text-green-600 border-green-200 bg-green-50';
        case 'moderate': return 'text-yellow-600 border-yellow-200 bg-yellow-50';
        case 'weak': return 'text-gray-500 border-gray-200 bg-gray-50';
        default: return 'text-gray-500 border-gray-200 bg-gray-50';
    }
};

const formatAction = (action?: string) => {
    switch (action) {
        case 'buy_more': return '추가 매수 (Buy More)';
        case 'sell': return '전량 매도 (Sell)';
        case 'reduce_size': return '비중 축소 (Reduce)';
        case 'hold': return '관망/홀딩 (Hold)';
        case 'buy': return '신규 매수 (Buy)';
        case 'do_not_buy': return '매수 보류 (Wait)';
        default: return action?.toUpperCase() || 'UNKNOWN';
    }
};

const getIcon = (action?: string) => {
    switch (action) {
        case 'buy':
        case 'buy_more': return <TrendingUp size={20} />;
        case 'sell':
        case 'reduce_size': return <TrendingDown size={20} />;
        case 'do_not_buy': return <XCircle size={20} />;
        default: return <MinusCircle size={20} />;
    }
};

export const PortfolioActionCard: React.FC<PortfolioActionCardProps> = ({ decision }) => {
    const { portfolio_action, action_reason, action_strength, position_adjustment_pct } = decision;

    // If no specific portfolio action, don't show or render default
    if (!portfolio_action) return null;

    const styles = getStyles(portfolio_action);

    return (
        <div className={`rounded-xl p-6 border mb-6 flex flex-col gap-4 ${styles.bg} ${styles.border}`}>
            <div className="flex justify-between items-center">
                <div className="flex items-center gap-3">
                    <div className={`px-4 py-2 rounded-lg text-lg font-bold uppercase flex items-center gap-2 ${styles.badgeBg} ${styles.text}`}>
                        {getIcon(portfolio_action)}
                        {formatAction(portfolio_action)}
                    </div>
                    {action_strength && (
                        <span className={`text-xs px-3 py-1 rounded-full border font-medium uppercase ${getStrengthColor(action_strength)}`}>
                            강도: {action_strength}
                        </span>
                    )}
                </div>

                {position_adjustment_pct !== undefined && position_adjustment_pct !== 0 && (
                    <div className="text-sm text-gray-500 flex items-center gap-2">
                        <Activity size={16} />
                        제안: {position_adjustment_pct > 0 ? '+' : ''}{Math.round(position_adjustment_pct * 100)}% 비중 조절
                    </div>
                )}
            </div>

            <p className="text-gray-700 text-lg leading-relaxed font-medium m-0">
                {action_reason || decision.reasoning}
            </p>
        </div>
    );
};

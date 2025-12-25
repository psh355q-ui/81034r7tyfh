import React from 'react';
import { DollarSign, Calendar, TrendingUp, Shield } from 'lucide-react';

interface DividendSummaryCardsProps {
    portfolioIncome: any;
}

const DividendSummaryCards: React.FC<DividendSummaryCardsProps> = ({ portfolioIncome }) => {
    const cards = [
        {
            title: '연간 배당 수입 (세후)',
            value: portfolioIncome?.annual_net_krw || 0,
            prefix: '₩',
            suffix: '',
            icon: <DollarSign className="text-green-600" size={24} />
        },
        {
            title: '월평균 배당금',
            value: portfolioIncome?.monthly_avg_krw || 0,
            prefix: '₩',
            suffix: '/월',
            icon: <Calendar className="text-cyan-600" size={24} />
        },
        {
            title: 'YOC (Yield on Cost)',
            value: portfolioIncome?.yoc || 0,
            prefix: '',
            suffix: '%',
            icon: <TrendingUp className="text-orange-600" size={24} />
        },
        {
            title: '실효 세율',
            value: portfolioIncome?.effective_tax_rate || 0,
            prefix: '',
            suffix: '%',
            icon: <Shield className="text-pink-600" size={24} />
        }
    ];

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {cards.map((card, index) => (
                <div
                    key={index}
                    className="bg-white rounded-lg shadow-md border border-gray-200 p-6 hover:shadow-lg transition-shadow"
                >
                    <div className="flex items-center justify-between">
                        <div className="flex-1">
                            <p className="text-sm font-medium text-gray-600 mb-2">{card.title}</p>
                            <p className="text-2xl font-bold text-gray-900">
                                {card.prefix}{card.value.toLocaleString()}{card.suffix}
                            </p>
                        </div>
                        <div className="p-3 bg-gray-50 rounded-full">{card.icon}</div>
                    </div>
                </div>
            ))}
        </div>
    );
};

export default DividendSummaryCards;

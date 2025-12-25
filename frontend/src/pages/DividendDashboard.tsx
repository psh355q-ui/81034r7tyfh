import React, { useState, useEffect } from 'react';
import { DollarSign, Calendar, TrendingUp, Shield, PlusCircle, Trophy } from 'lucide-react';
import { Card } from '../components/common/Card';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import DividendSummaryCards from '../components/Dividend/DividendSummaryCards';
import DividendCalendar from '../components/Dividend/DividendCalendar';
import CompoundSimulator from '../components/Dividend/CompoundSimulator';
import RiskScoreTable from '../components/Dividend/RiskScoreTable';
import CashInjectionSlider from '../components/Dividend/CashInjectionSlider';
import AristocratsTable from '../components/Dividend/AristocratsTable';

type TabType = 'calendar' | 'drip' | 'risk' | 'injection' | 'aristocrats';

const DividendDashboard: React.FC = () => {
    const [activeTab, setActiveTab] = useState<TabType>('calendar');
    const [loading, setLoading] = useState(false);
    const [portfolioIncome, setPortfolioIncome] = useState<any>(null);

    // 포트폴리오 배당 수입 조회
    const fetchPortfolioIncome = async () => {
        setLoading(true);
        try {
            // 예시 포지션 (실제로는 KIS API에서 가져와야 함)
            const positions = [
                { ticker: 'JNJ', shares: 100, avg_price: 150 },
                { ticker: 'PG', shares: 50, avg_price: 145 },
                { ticker: 'KO', shares: 150, avg_price: 60 }
            ];

            const response = await fetch('http://localhost:8001/api/dividend/portfolio', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(positions)
            });

            if (!response.ok) throw new Error('Failed to fetch portfolio income');

            const data = await response.json();
            setPortfolioIncome(data);
        } catch (error: any) {
            console.error('Failed to fetch portfolio income:', error.message);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchPortfolioIncome();
    }, []);

    const renderTabContent = () => {
        switch (activeTab) {
            case 'calendar':
                return <DividendCalendar />;
            case 'drip':
                return <CompoundSimulator />;
            case 'risk':
                return <RiskScoreTable />;
            case 'injection':
                return <CashInjectionSlider portfolioIncome={portfolioIncome} />;
            case 'aristocrats':
                return <AristocratsTable />;
            default:
                return <DividendCalendar />;
        }
    };

    return (
        <div className="space-y-6 p-6">
            {/* Header */}
            <div>
                <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
                    <DollarSign className="text-green-600" size={32} />
                    배당 인텔리전스
                </h1>
                <p className="text-gray-600 mt-1">미국 배당주 포트폴리오 분석 및 시뮬레이션</p>
            </div>

            {/* Summary Cards */}
            {loading ? (
                <div className="flex justify-center items-center py-12">
                    <LoadingSpinner size="lg" />
                </div>
            ) : (
                <DividendSummaryCards portfolioIncome={portfolioIncome} />
            )}

            {/* Tabs and Content */}
            <div className="space-y-6">
                <Card>
                    <div className="flex items-center justify-between mb-6 border-b pb-4">
                        <h2 className="text-xl font-semibold text-gray-800">배당 분석 도구</h2>
                        <div className="flex space-x-2">
                            <button
                                onClick={() => setActiveTab('calendar')}
                                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors flex items-center gap-2 ${activeTab === 'calendar'
                                        ? 'bg-blue-100 text-blue-700'
                                        : 'text-gray-600 hover:bg-gray-100'
                                    }`}
                            >
                                <Calendar size={16} />
                                배당 캘린더
                            </button>
                            <button
                                onClick={() => setActiveTab('drip')}
                                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors flex items-center gap-2 ${activeTab === 'drip'
                                        ? 'bg-blue-100 text-blue-700'
                                        : 'text-gray-600 hover:bg-gray-100'
                                    }`}
                            >
                                <TrendingUp size={16} />
                                복리 시뮬레이션
                            </button>
                            <button
                                onClick={() => setActiveTab('risk')}
                                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors flex items-center gap-2 ${activeTab === 'risk'
                                        ? 'bg-blue-100 text-blue-700'
                                        : 'text-gray-600 hover:bg-gray-100'
                                    }`}
                            >
                                <Shield size={16} />
                                리스크 분석
                            </button>
                            <button
                                onClick={() => setActiveTab('injection')}
                                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors flex items-center gap-2 ${activeTab === 'injection'
                                        ? 'bg-blue-100 text-blue-700'
                                        : 'text-gray-600 hover:bg-gray-100'
                                    }`}
                            >
                                <PlusCircle size={16} />
                                예수금 추가
                            </button>
                            <button
                                onClick={() => setActiveTab('aristocrats')}
                                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors flex items-center gap-2 ${activeTab === 'aristocrats'
                                        ? 'bg-blue-100 text-blue-700'
                                        : 'text-gray-600 hover:bg-gray-100'
                                    }`}
                            >
                                <Trophy size={16} />
                                배당 귀족주
                            </button>
                        </div>
                    </div>

                    <div className="min-h-[400px]">
                        {renderTabContent()}
                    </div>
                </Card>
            </div>
        </div>
    );
};

export default DividendDashboard;

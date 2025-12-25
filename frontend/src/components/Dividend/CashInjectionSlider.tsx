import React, { useState } from 'react';
import { PlusCircle, ArrowUp } from 'lucide-react';

interface CashInjectionSliderProps {
    portfolioIncome: any;
}

const CashInjectionSlider: React.FC<CashInjectionSliderProps> = ({ portfolioIncome }) => {
    const [injectionAmount, setInjectionAmount] = useState(10000);
    const [simulationResult, setSimulationResult] = useState<any>(null);
    const [loading, setLoading] = useState(false);

    const handleSimulate = async () => {
        setLoading(true);
        try {
            const positions = [
                { ticker: 'JNJ', shares: 100, avg_price: 150 },
                { ticker: 'PG', shares: 50, avg_price: 145 },
                { ticker: 'KO', shares: 150, avg_price: 60 }
            ];

            const response = await fetch('http://localhost:8001/api/dividend/simulate/injection', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    inject_amount_usd: injectionAmount,
                    positions: positions
                })
            });

            if (!response.ok) throw new Error('Failed to simulate injection');

            const data = await response.json();
            setSimulationResult(data);
        } catch (error: any) {
            console.error('Simulation failed:', error.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="space-y-6">
            <div>
                <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2 mb-2">
                    <PlusCircle size={20} className="text-green-600" />
                    예수금 추가 시뮬레이션
                </h3>
                <p className="text-sm text-gray-600">추가 투자 시 배당 수입 변화 예측</p>
            </div>

            <div className="bg-white rounded-lg border border-gray-200 p-6 space-y-4">
                <div>
                    <div className="flex justify-between items-center mb-2">
                        <label className="text-sm font-medium text-gray-700">추가 투자 금액</label>
                        <span className="text-lg font-bold text-green-600">${injectionAmount.toLocaleString()}</span>
                    </div>
                    <input
                        type="range"
                        min="1000"
                        max="100000"
                        step="1000"
                        value={injectionAmount}
                        onChange={(e) => setInjectionAmount(Number(e.target.value))}
                        className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                    />
                    <div className="flex justify-between text-xs text-gray-500 mt-1">
                        <span>$1K</span>
                        <span>$25K</span>
                        <span>$50K</span>
                        <span>$75K</span>
                        <span>$100K</span>
                    </div>
                </div>

                <button
                    onClick={handleSimulate}
                    disabled={loading}
                    className="w-full px-4 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 transition-colors flex items-center justify-center gap-2"
                >
                    <ArrowUp size={20} />
                    {loading ? '시뮬레이션 중...' : '시뮬레이션 실행'}
                </button>
            </div>

            {simulationResult && (
                <div className="bg-white rounded-lg border border-gray-200 p-6">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="text-center">
                            <p className="text-sm text-gray-600 mb-1">현재 연간 배당</p>
                            <p className="text-2xl font-bold text-gray-900">
                                ₩{(simulationResult.before?.annual_net_krw || 0).toLocaleString()}
                            </p>
                        </div>
                        <div className="text-center">
                            <p className="text-sm text-gray-600 mb-1">추가 후 연간 배당</p>
                            <p className="text-2xl font-bold text-green-600">
                                ₩{(simulationResult.after?.annual_net_krw || 0).toLocaleString()}
                            </p>
                        </div>
                        <div className="text-center">
                            <p className="text-sm text-gray-600 mb-1">증가량</p>
                            <p className="text-2xl font-bold text-blue-600">
                                ₩+{(simulationResult.increase?.annual_krw || 0).toLocaleString()}
                            </p>
                            <p className="text-sm text-gray-500">
                                (+{simulationResult.increase?.percentage || 0}%)
                            </p>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default CashInjectionSlider;

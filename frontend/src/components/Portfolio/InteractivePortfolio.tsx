import React, { useState, useRef, useEffect } from 'react';
import { GripVertical, ArrowRight, RefreshCw } from 'lucide-react';
import { Card } from '../common/Card';

interface PortfolioItem {
    id: string;
    ticker: string;
    currentWeight: number;
    targetWeight: number;
}

const MOCK_ITEMS: PortfolioItem[] = [
    { id: '1', ticker: 'AAPL', currentWeight: 45, targetWeight: 45 },
    { id: '2', ticker: 'MSFT', currentWeight: 25, targetWeight: 25 },
    { id: '3', ticker: 'GOOGL', currentWeight: 15, targetWeight: 15 },
    { id: '4', ticker: 'TSLA', currentWeight: 10, targetWeight: 10 },
    { id: '5', ticker: 'NVDA', currentWeight: 5, targetWeight: 5 },
];

export const InteractivePortfolio: React.FC = () => {
    const [items, setItems] = useState<PortfolioItem[]>([]);
    const [draggedItem, setDraggedItem] = useState<PortfolioItem | null>(null);
    const [isRebalancing, setIsRebalancing] = useState(false);
    const [loading, setLoading] = useState(true);

    // 실제 포트폴리오 데이터 가져오기
    useEffect(() => {
        const fetchPortfolio = async () => {
            try {
                const response = await fetch('/api/portfolio');
                const portfolio = await response.json();

                if (portfolio.positions && portfolio.positions.length > 0) {
                    const totalValue = portfolio.total_value || 1;
                    const portfolioItems = portfolio.positions.map((pos: any, idx: number) => ({
                        id: String(idx + 1),
                        ticker: pos.ticker,
                        currentWeight: Math.round((pos.market_value / totalValue) * 100),
                        targetWeight: Math.round((pos.market_value / totalValue) * 100)
                    }));

                    setItems(portfolioItems);
                }
            } catch (error) {
                console.error('Failed to fetch portfolio for rebalance:', error);
            }
        };

        fetchPortfolio();
    }, []);

    const handleDragStart = (e: React.DragEvent<HTMLDivElement>, item: PortfolioItem) => {
        setDraggedItem(item);
        e.dataTransfer.effectAllowed = 'move';
        // Invisible drag image or custom styling could be added here
    };

    const handleDragOver = (e: React.DragEvent<HTMLDivElement>, index: number) => {
        e.preventDefault();
        if (!draggedItem) return;

        const draggedIndex = items.findIndex(i => i.id === draggedItem.id);
        if (draggedIndex === index) return;

        const newItems = [...items];
        newItems.splice(draggedIndex, 1);
        newItems.splice(index, 0, draggedItem);
        setItems(newItems);
    };

    const handleDragEnd = () => {
        setDraggedItem(null);
    };

    const handleWeightChange = (id: string, newWeight: number) => {
        setItems(items.map(item =>
            item.id === id ? { ...item, targetWeight: newWeight } : item
        ));
    };

    const handleRebalance = () => {
        setIsRebalancing(true);
        setTimeout(() => {
            setIsRebalancing(false);
            alert('Rebalancing orders generated based on new priorities and weights!');
        }, 1500);
    };

    return (
        <Card title="Portfolio Rebalancing (Drag to Prioritize)">
            <div className="space-y-4">
                <div className="flex justify-between text-sm text-gray-500 px-4">
                    <span>Asset</span>
                    <div className="flex gap-8">
                        <span>Current %</span>
                        <span>Target %</span>
                    </div>
                </div>

                <div className="space-y-2">
                    {items.map((item, index) => (
                        <div
                            key={item.id}
                            draggable
                            onDragStart={(e) => handleDragStart(e, item)}
                            onDragOver={(e) => handleDragOver(e, index)}
                            onDragEnd={handleDragEnd}
                            className={`flex items-center justify-between p-3 bg-white border rounded-lg shadow-sm cursor-move transition-all ${draggedItem?.id === item.id ? 'opacity-50 border-blue-400' : 'border-gray-200 hover:border-blue-300'
                                }`}
                        >
                            <div className="flex items-center gap-3">
                                <GripVertical className="text-gray-400" size={20} />
                                <span className="font-bold text-gray-800">{item.ticker}</span>
                                <span className="text-xs bg-blue-100 text-blue-800 px-2 py-0.5 rounded-full">
                                    Priority {index + 1}
                                </span>
                            </div>

                            <div className="flex items-center gap-6">
                                <div className="w-16 text-right font-medium text-gray-600">
                                    {item.currentWeight}%
                                </div>
                                <div className="flex items-center gap-2">
                                    <ArrowRight size={16} className="text-gray-400" />
                                    <input
                                        type="number"
                                        min="0"
                                        max="100"
                                        value={item.targetWeight}
                                        onChange={(e) => handleWeightChange(item.id, parseInt(e.target.value) || 0)}
                                        className="w-16 p-1 text-right border rounded focus:ring-2 focus:ring-blue-500 outline-none"
                                    />
                                    <span className="text-gray-500">%</span>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>

                <div className="pt-4 border-t mt-4 flex justify-between items-center">
                    <div className="text-sm text-gray-500">
                        Total Target: <span className={`font-bold ${items.reduce((sum, item) => sum + item.targetWeight, 0) === 100 ? 'text-green-600' : 'text-red-600'
                            }`}>
                            {items.reduce((sum, item) => sum + item.targetWeight, 0)}%
                        </span>
                    </div>
                    <button
                        onClick={handleRebalance}
                        disabled={isRebalancing}
                        className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
                    >
                        <RefreshCw size={18} className={isRebalancing ? 'animate-spin' : ''} />
                        {isRebalancing ? 'Simulating...' : 'Simulate Rebalance'}
                    </button>
                </div>
            </div>
        </Card>
    );
};

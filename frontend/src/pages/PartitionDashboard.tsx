import React, { useEffect, useState } from 'react';
import { partitionsApi, PartitionSummary, LeverageCheckResponse, Order } from '../services/partitionsApi';

const PartitionDashboard: React.FC = () => {
    const [summary, setSummary] = useState<PartitionSummary | null>(null);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

    const [tickerCheck, setTickerCheck] = useState('');
    const [leverageCheckResult, setLeverageCheckResult] = useState<LeverageCheckResponse | null>(null);
    const [orders, setOrders] = useState<Order[]>([]);
    const [ordersLoading, setOrdersLoading] = useState<boolean>(true);

    const fetchData = async () => {
        try {
            setLoading(true);
            const data = await partitionsApi.getSummary();
            setSummary(data);
            setError(null);
        } catch (err) {
            setError('Failed to load partition data');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const fetchOrders = async () => {
        try {
            setOrdersLoading(true);
            const data = await partitionsApi.getOrders(10);
            setOrders(data);
        } catch (err) {
            console.error('Failed to fetch orders:', err);
        } finally {
            setOrdersLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
        fetchOrders();
        const interval = setInterval(() => {
            fetchData();
            fetchOrders();
        }, 30000); // Refresh every 30s
        return () => clearInterval(interval);
    }, []);

    const handleCheckLeverage = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!tickerCheck) return;
        try {
            const res = await partitionsApi.checkLeverage(tickerCheck);
            setLeverageCheckResult(res);
        } catch (err) {
            console.error(err);
        }
    };

    if (loading && !summary) return <div className="p-8 text-white">Loading Partitions...</div>;
    if (error) return <div className="p-8 text-red-500">{error}</div>;

    const wallets = summary?.wallets;

    return (
        <div className="min-h-screen bg-gray-900 text-gray-100 p-6 space-y-6">
            <header className="flex justify-between items-center mb-8">
                <div>
                    <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-500">
                        계좌 파티션
                    </h1>
                    <p className="text-gray-400 mt-2">자율 포트폴리오 관리 시스템</p>
                </div>
                <div className="text-right">
                    <div className="text-2xl font-mono text-green-400">
                        ${summary?.total_equity?.toLocaleString() ?? '0'}
                    </div>
                    <div className="text-sm text-gray-500">총 자산</div>
                </div>
            </header>

            {/* Wallet Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {wallets && Object.values(wallets).map((wallet) => (
                    <div
                        key={wallet.wallet}
                        className={`p-6 rounded-xl border border-gray-700 bg-gray-800 relative overflow-hidden transition-all hover:border-gray-500
                            ${wallet.wallet === 'core' ? 'border-l-4 border-l-blue-500' : ''}
                            ${wallet.wallet === 'income' ? 'border-l-4 border-l-green-500' : ''}
                            ${wallet.wallet === 'satellite' ? 'border-l-4 border-l-purple-500' : ''}
                        `}
                    >
                        <div className="flex justify-between items-start mb-4">
                            <h2 className="text-xl font-bold uppercase tracking-wider">{wallet.wallet}</h2>
                            <span className="text-xs bg-gray-700 px-2 py-1 rounded">
                                목표 비중: {wallet.target_pct * 100}%
                            </span>
                        </div>

                        <div className="space-y-4">
                            <div>
                                <div className="flex justify-between text-sm mb-1">
                                    <span className="text-gray-400">현재 비중</span>
                                    <span className={wallet.deviation > 0.05 ? 'text-yellow-400' : 'text-blue-400'}>
                                        {(wallet.current_pct * 100).toFixed(1)}%
                                    </span>
                                </div>
                                <div className="w-full bg-gray-700 rounded-full h-2">
                                    <div
                                        className={`h-2 rounded-full ${wallet.wallet === 'core' ? 'bg-blue-500' :
                                            wallet.wallet === 'income' ? 'bg-green-500' : 'bg-purple-500'
                                            }`}
                                        style={{ width: `${Math.min(wallet.current_pct * 100, 100)}%` }}
                                    ></div>
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-4 text-sm">
                                <div>
                                    <span className="block text-gray-500">평가액</span>
                                    <span className="font-mono text-lg">${wallet.current_value?.toLocaleString() ?? '0'}</span>
                                </div>
                                <div>
                                    <span className="block text-gray-500">예수금</span>
                                    <span className="font-mono text-lg text-gray-300">${wallet.cash?.toLocaleString() ?? '0'}</span>
                                </div>
                            </div>

                            {wallet.needs_rebalance && (
                                <div className="bg-yellow-900/30 text-yellow-500 text-xs p-2 rounded border border-yellow-800 mt-2 text-center">
                                    ⚠️ 리밸런싱 필요
                                </div>
                            )}
                        </div>
                    </div>
                ))}
            </div>

            {/* Leverage Guardian & Shadow Stats */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">

                {/* Leverage Checker */}
                <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
                    <h3 className="text-lg font-bold mb-4 flex items-center">
                        🛡️ 레버리지 가디언 진단
                    </h3>
                    <form onSubmit={handleCheckLeverage} className="flex gap-4 mb-4">
                        <input
                            type="text"
                            value={tickerCheck}
                            onChange={(e) => setTickerCheck(e.target.value.toUpperCase())}
                            placeholder="티커 조회 (예: TQQQ)"
                            className="bg-gray-700 text-white px-4 py-2 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 flex-grow"
                        />
                        <button type="submit" className="bg-blue-600 hover:bg-blue-500 px-6 py-2 rounded font-medium">
                            진단
                        </button>
                    </form>

                    {leverageCheckResult && (
                        <div className={`p-4 rounded border ${leverageCheckResult.is_leveraged ? 'bg-purple-900/20 border-purple-500/50' : 'bg-green-900/20 border-green-500/50'
                            }`}>
                            <div className="flex items-center gap-2 mb-2">
                                <span className="font-bold text-lg">{leverageCheckResult.ticker}</span>
                                {leverageCheckResult.is_leveraged ?
                                    <span className="bg-purple-600 text-white text-xs px-2 py-0.5 rounded">LEVERAGED ({leverageCheckResult.leverage_ratio}x)</span> :
                                    <span className="bg-green-600 text-white text-xs px-2 py-0.5 rounded">SAFE</span>
                                }
                            </div>
                            <p className="text-sm text-gray-300 mb-2">
                                허용 지갑: <span className="text-white font-mono">{leverageCheckResult.allowed_wallets.join(', ')}</span>
                            </p>
                            <p className="text-xs text-gray-400">{leverageCheckResult.note}</p>
                        </div>
                    )}
                </div>

                {/* Shadow Trading Status */}
                <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
                    <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                        👻 섀도우 트레이딩 상태
                        <span className="flex h-2 w-2 relative">
                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                            <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                        </span>
                    </h3>

                    <div className="space-y-3">
                        <div className="flex justify-between items-center border-b border-gray-700 pb-2">
                            <span className="text-gray-400">모드</span>
                            <span className="text-green-400 font-mono">AUTONOMOUS</span>
                        </div>
                        <div className="flex justify-between items-center border-b border-gray-700 pb-2">
                            <span className="text-gray-400">시세 연동</span>
                            <span className="text-blue-400">KIS Real-time</span>
                        </div>
                        <div className="flex justify-between items-center border-b border-gray-700 pb-2">
                            <span className="text-gray-400">총 매매 수</span>
                            <span className="text-white font-mono">{orders.length}</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Shadow Trade Log */}
            <div className="bg-gray-800 rounded-xl p-6 border border-gray-700 mt-6">
                <div className="flex justify-between items-center mb-4">
                    <h3 className="text-lg font-bold flex items-center gap-2">
                        📋 섀도우 매매 로그
                    </h3>
                    <button
                        onClick={fetchOrders}
                        className="text-sm text-blue-400 hover:text-blue-300 transition-colors"
                    >
                        새로고침
                    </button>
                </div>

                {ordersLoading && orders.length === 0 ? (
                    <div className="text-center text-gray-500 py-8">매매 기록 로딩 중...</div>
                ) : orders.length === 0 ? (
                    <div className="text-center text-gray-500 py-8">
                        <div className="text-4xl mb-2">🔍</div>
                        <p>아직 매매 기록이 없습니다</p>
                        <p className="text-sm mt-1">AI가 트레이딩 신호를 포착하기 위해 뉴스를 모니터링 중입니다...</p>
                    </div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                            <thead>
                                <tr className="text-gray-400 text-left border-b border-gray-700">
                                    <th className="pb-3 font-medium">시간</th>
                                    <th className="pb-3 font-medium">티커</th>
                                    <th className="pb-3 font-medium">매매</th>
                                    <th className="pb-3 font-medium text-right">수량</th>
                                    <th className="pb-3 font-medium text-right">가격</th>
                                    <th className="pb-3 font-medium text-center">상태</th>
                                </tr>
                            </thead>
                            <tbody>
                                {orders.map((order) => (
                                    <tr key={order.id} className="border-b border-gray-700/50 hover:bg-gray-700/30 transition-colors">
                                        <td className="py-3 text-gray-400 text-xs">
                                            {new Date(order.created_at).toLocaleString('ko-KR', {
                                                month: 'short',
                                                day: 'numeric',
                                                hour: '2-digit',
                                                minute: '2-digit'
                                            })}
                                        </td>
                                        <td className="py-3">
                                            <span className="font-mono font-medium text-white">{order.ticker}</span>
                                        </td>
                                        <td className="py-3">
                                            <span className={`px-2 py-0.5 rounded text-xs font-medium ${order.action === 'BUY'
                                                    ? 'bg-green-900/50 text-green-400 border border-green-700'
                                                    : 'bg-red-900/50 text-red-400 border border-red-700'
                                                }`}>
                                                {order.action}
                                            </span>
                                        </td>
                                        <td className="py-3 text-right font-mono text-gray-300">
                                            {order.quantity.toLocaleString()}
                                        </td>
                                        <td className="py-3 text-right font-mono text-gray-300">
                                            ${order.price.toFixed(2)}
                                        </td>
                                        <td className="py-3 text-center">
                                            <span className={`px-2 py-0.5 rounded text-xs ${order.status === 'FILLED'
                                                    ? 'bg-blue-900/50 text-blue-400'
                                                    : order.status === 'PENDING'
                                                        ? 'bg-yellow-900/50 text-yellow-400'
                                                        : 'bg-gray-700 text-gray-400'
                                                }`}>
                                                {order.status}
                                            </span>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>

            {/* Disclaimer */}
            <div className="text-center text-xs text-gray-600 mt-12 pb-4">
                AI 트레이딩 시스템 v2.0 • 섀도우 모드 활성 • 투자 권유 아님
            </div>
        </div>
    );
};

export default PartitionDashboard;

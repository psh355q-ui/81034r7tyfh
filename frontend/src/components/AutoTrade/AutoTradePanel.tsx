import React, { useState, useEffect } from 'react';
import { Play, Pause, AlertOctagon, ShieldCheck, Activity, RotateCcw } from 'lucide-react';

interface AutoTradeStatus {
    status: 'running' | 'stopped';
    kill_switch_triggered: boolean;
    kill_switch_reason: string | null;
    config: {
        is_virtual: boolean;
        dry_run: boolean;
        max_daily_loss_pct: number;
    };
    stats: {
        daily_trades: number;
        daily_pnl: number;
        current_positions: number;
    };
}

export const AutoTradePanel: React.FC = () => {
    const [status, setStatus] = useState<AutoTradeStatus | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchStatus = async () => {
        try {
            const response = await fetch('/api/auto-trade/status');
            if (response.ok) {
                const data = await response.json();
                setStatus(data);
                setError(null);
            } else {
                setError('Failed to fetch status');
            }
        } catch (err) {
            setError('Connection error');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchStatus();
        const interval = setInterval(fetchStatus, 5000); // 5초마다 상태 갱신
        return () => clearInterval(interval);
    }, []);

    const handleAction = async (action: 'start' | 'stop' | 'kill-switch/reset') => {
        try {
            setLoading(true);
            const method = action === 'start' || action === 'stop' || action === 'kill-switch/reset' ? 'POST' : 'GET';
            // start/stop take parameters? start takes mode.

            let url = `/api/auto-trade/${action}`;
            let body = {};

            if (action === 'start') {
                body = { mode: 'conservative' }; // Default mode
            }

            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json'
                },
                body: Object.keys(body).length > 0 ? JSON.stringify(body) : undefined
            });

            if (response.ok) {
                await fetchStatus();
            } else {
                const err = await response.json();
                alert(`Action failed: ${err.detail}`);
            }
        } catch (err) {
            alert('Network error during action');
        } finally {
            setLoading(false);
        }
    };

    if (loading && !status) return <div className="p-4 bg-gray-800 rounded-lg animate-pulse h-32"></div>;
    if (!status) return null;

    const isRunning = status.status === 'running';
    const isKillSwitch = status.kill_switch_triggered;

    return (
        <div className="bg-gray-900 rounded-xl p-6 mb-6 text-white border border-gray-800 shadow-xl">
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <div className={`p-3 rounded-lg ${isRunning ? 'bg-green-500/20 text-green-400' : 'bg-gray-700/50 text-gray-400'}`}>
                        <Activity className="w-6 h-6" />
                    </div>
                    <div>
                        <h2 className="text-xl font-bold flex items-center gap-2">
                            Auto Trading Engine
                            {status.config.dry_run && <span className="text-xs bg-blue-500/20 text-blue-300 px-2 py-1 rounded">DRY RUN</span>}
                        </h2>
                        <div className="flex items-center gap-2 text-sm text-gray-400 mt-1">
                            <span className={`w-2 h-2 rounded-full ${isRunning ? 'bg-green-500 animate-pulse' : 'bg-gray-500'}`}></span>
                            {isRunning ? 'System Active' : 'System Stopped'}
                        </div>
                    </div>
                </div>

                {/* Stats */}
                <div className="flex items-center gap-8">
                    <div className="text-right">
                        <p className="text-sm text-gray-400">Daily P&L</p>
                        <p className={`font-mono font-bold text-lg ${status.stats.daily_pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                            {status.stats.daily_pnl >= 0 ? '+' : ''}{status.stats.daily_pnl.toLocaleString()} USD
                        </p>
                    </div>
                    <div className="text-right">
                        <p className="text-sm text-gray-400">Trades / Pos</p>
                        <p className="font-mono font-bold text-lg">
                            {status.stats.daily_trades} / {status.stats.current_positions}
                        </p>
                    </div>
                </div>

                {/* Controls */}
                <div className="flex gap-3">
                    {isKillSwitch ? (
                        <button
                            onClick={() => handleAction('kill-switch/reset')}
                            className="flex items-center gap-2 px-6 py-3 bg-red-600 hover:bg-red-700 rounded-lg font-bold transition-all animate-pulse"
                        >
                            <RotateCcw className="w-5 h-5" />
                            RESET KILL SWITCH
                        </button>
                    ) : (
                        <>
                            {!isRunning ? (
                                <button
                                    onClick={() => handleAction('start')}
                                    className="flex items-center gap-2 px-6 py-3 bg-green-600 hover:bg-green-700 rounded-lg font-bold transition-all shadow-lg shadow-green-900/20"
                                >
                                    <Play className="w-5 h-5" />
                                    START ENGINE
                                </button>
                            ) : (
                                <button
                                    onClick={() => handleAction('stop')}
                                    className="flex items-center gap-2 px-6 py-3 bg-red-500/20 text-red-500 hover:bg-red-500/30 rounded-lg font-bold transition-all border border-red-500/50"
                                >
                                    <Pause className="w-5 h-5" />
                                    STOP ENGINE
                                </button>
                            )}
                        </>
                    )}
                </div>
            </div>

            {/* Kill Switch Warning */}
            {isKillSwitch && (
                <div className="mt-4 bg-red-900/50 border border-red-500 rounded-lg p-3 flex items-center gap-3 text-red-200">
                    <AlertOctagon className="w-5 h-5 text-red-500" />
                    <span className="font-bold">KILL SWITCH TRIGGERED:</span> {status.kill_switch_reason}
                </div>
            )}
        </div>
    );
};

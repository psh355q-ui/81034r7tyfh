/**
 * Global Analysis Progress Display
 * 
 * Shows analysis progress across ALL pages:
 * - Minimized: Bottom-right corner popup (always visible)
 * - Maximized: Full modal (only on Analysis Lab page)
 */

import React from 'react';
import { Brain, CheckCircle, XCircle, Clock, AlertCircle, Minimize2, Maximize2, X, StopCircle } from 'lucide-react';
import { useAnalysis } from '../../contexts/AnalysisContext';
import { useLocation } from 'react-router-dom';

export const GlobalAnalysisProgress: React.FC = () => {
    const { isAnalyzing, progress, isMinimized, setMinimized, stopAnalysis, currentPage } = useAnalysis();
    const location = useLocation();

    const prevPathRef = React.useRef(location.pathname);

    // Auto-maximize when returning to News page (only on navigation, not on manual minimize)
    React.useEffect(() => {
        const prevPath = prevPathRef.current;
        const currentPath = location.pathname;

        // Only auto-maximize if we actually navigated TO /news from another page
        if (currentPath === '/news' && prevPath !== '/news' && isMinimized && isAnalyzing) {
            console.log(`📈 Auto-maximizing on News page (navigated from ${prevPath})`);
            setMinimized(false);
        }

        // Update previous path
        prevPathRef.current = currentPath;
    }, [location.pathname, isAnalyzing]); // Removed isMinimized and setMinimized from deps

    if (!isAnalyzing) return null;

    const { status, progress_percent, current_index, total_articles, current_article, completed, skipped, errors, message } = progress;

    const isOnNewsPage = location.pathname === '/news';

    // Show full modal only on News page when not minimized
    const showFullModal = isOnNewsPage && !isMinimized;

    // Minimized corner popup (visible on ALL pages)
    if (!showFullModal) {
        return (
            <div className="fixed bottom-6 right-6 z-50">
                <div className="bg-white rounded-lg shadow-2xl p-4 w-80 border-2 border-purple-500">
                    <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center space-x-2">
                            <Brain className={`text-purple-600 ${status === 'running' ? 'animate-pulse' : ''}`} size={20} />
                            <span className="font-bold text-gray-900">AI 분석 중...</span>
                        </div>
                        <div className="flex items-center space-x-1">
                            {isOnNewsPage && (
                                <button
                                    onClick={() => setMinimized(false)}
                                    className="p-1 hover:bg-gray-100 rounded transition-colors"
                                    title="확대"
                                >
                                    <Maximize2 size={16} className="text-gray-600" />
                                </button>
                            )}
                            <button
                                onClick={stopAnalysis}
                                className="p-1 hover:bg-red-100 rounded transition-colors"
                                title="중단"
                            >
                                <StopCircle size={16} className="text-red-600" />
                            </button>
                            {status !== 'running' && (
                                <button
                                    onClick={stopAnalysis}
                                    className="p-1 hover:bg-gray-100 rounded transition-colors"
                                    title="닫기"
                                >
                                    <X size={16} className="text-gray-600" />
                                </button>
                            )}
                        </div>
                    </div>

                    <div className="mb-2">
                        <div className="flex items-center justify-between mb-1">
                            <span className="text-sm font-medium text-gray-700">
                                {current_index} / {total_articles}
                            </span>
                            <span className="text-sm font-medium text-gray-700">
                                {progress_percent.toFixed(0)}%
                            </span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                            <div
                                className={`h-full transition-all duration-500 ${status === 'error' ? 'bg-red-600' :
                                    status === 'completed' ? 'bg-green-600' :
                                        'bg-purple-600'
                                    }`}
                                style={{ width: `${progress_percent}%` }}
                            />
                        </div>
                    </div>

                    <div className="flex items-center justify-between text-xs">
                        <span className="text-green-600">✓ {completed}</span>
                        <span className="text-yellow-600">⊘ {skipped}</span>
                        <span className="text-red-600">✗ {errors}</span>
                    </div>

                    {message && (
                        <div className="mt-2 text-xs text-gray-600 truncate">
                            {message}
                        </div>
                    )}
                </div>
            </div>
        );
    }

    // Full modal view (only on Analysis Lab page)
    return (
        <div className="fixed inset-0 z-40 pointer-events-none">
            {/* Semi-transparent backdrop */}
            <div className="absolute inset-0 bg-black bg-opacity-30 pointer-events-none" />

            {/* Modal content - only this part blocks clicks */}
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                <div className="bg-white rounded-lg shadow-2xl p-6 w-full max-w-2xl pointer-events-auto">
                    {/* Header */}
                    <div className="flex items-center justify-between mb-6">
                        <div className="flex items-center space-x-3">
                            <Brain className={`text-purple-600 ${status === 'running' ? 'animate-pulse' : ''}`} size={28} />
                            <div>
                                <h2 className="text-xl font-bold text-gray-900">AI 뉴스 분석 진행 중</h2>
                                <p className="text-sm text-gray-600">Gemini 2.5 Flash 분석 중...</p>
                            </div>
                        </div>
                        <div className="flex items-center space-x-2">
                            <button
                                onClick={() => setMinimized(true)}
                                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                                title="최소화"
                            >
                                <Minimize2 size={20} className="text-gray-600" />
                            </button>
                            <button
                                onClick={stopAnalysis}
                                className="p-2 hover:bg-red-100 rounded-lg transition-colors flex items-center space-x-1"
                                title="분석 중단"
                            >
                                <StopCircle size={20} className="text-red-600" />
                                <span className="text-sm text-red-600 font-medium">중단</span>
                            </button>
                            {status === 'completed' && (
                                <CheckCircle className="text-green-600" size={24} />
                            )}
                        </div>
                    </div>

                    {/* Progress Bar */}
                    <div className="mb-6">
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-sm font-medium text-gray-700">
                                {current_index} / {total_articles} 기사
                            </span>
                            <span className="text-sm font-medium text-gray-700">
                                {progress_percent.toFixed(1)}%
                            </span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
                            <div
                                className={`h-full transition-all duration-500 ${status === 'error' ? 'bg-red-600' :
                                    status === 'completed' ? 'bg-green-600' :
                                        'bg-purple-600'
                                    }`}
                                style={{ width: `${progress_percent}%` }}
                            />
                        </div>
                    </div>

                    {/* Current Article */}
                    {current_article && status === 'running' && (
                        <div className="mb-4 p-3 bg-purple-50 border border-purple-200 rounded-lg">
                            <div className="flex items-start space-x-2">
                                <Clock className="text-purple-600 flex-shrink-0 mt-1" size={16} />
                                <div className="flex-1 min-w-0">
                                    <p className="text-xs text-purple-700 font-medium mb-1">분석 중:</p>
                                    <p className="text-sm text-gray-800 line-clamp-2">{current_article}</p>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Statistics */}
                    <div className="grid grid-cols-3 gap-4 mb-6">
                        <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                            <div className="flex items-center space-x-2">
                                <CheckCircle className="text-green-600" size={20} />
                                <div>
                                    <p className="text-xs text-green-700">완료</p>
                                    <p className="text-lg font-bold text-green-800">{completed}</p>
                                </div>
                            </div>
                        </div>

                        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                            <div className="flex items-center space-x-2">
                                <AlertCircle className="text-yellow-600" size={20} />
                                <div>
                                    <p className="text-xs text-yellow-700">스킵</p>
                                    <p className="text-lg font-bold text-yellow-800">{skipped}</p>
                                </div>
                            </div>
                        </div>

                        <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                            <div className="flex items-center space-x-2">
                                <XCircle className="text-red-600" size={20} />
                                <div>
                                    <p className="text-xs text-red-700">에러</p>
                                    <p className="text-lg font-bold text-red-800">{errors}</p>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Status Message */}
                    {message && (
                        <div className={`p-3 rounded-lg mb-4 ${status === 'error' ? 'bg-red-50 border border-red-200' :
                            status === 'completed' ? 'bg-green-50 border border-green-200' :
                                'bg-blue-50 border border-blue-200'
                            }`}>
                            <p className={`text-sm ${status === 'error' ? 'text-red-800' :
                                status === 'completed' ? 'text-green-800' :
                                    'text-blue-800'
                                }`}>
                                {message}
                            </p>
                        </div>
                    )}

                    {/* Info */}
                    <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                        <p className="text-xs text-purple-800 mb-2">
                            💡 <strong>백그라운드 처리:</strong> "최소화" 버튼을 눌러 작은 팝업으로 전환할 수 있습니다.
                        </p>
                        <p className="text-xs text-purple-700">
                            분석은 서버에서 계속 진행되며, 다른 페이지로 이동해도 우측 하단에서 진행 상황을 확인할 수 있습니다.
                        </p>
                    </div>

                    {/* Close Button */}
                    {status !== 'running' && (
                        <div className="mt-4 flex justify-end">
                            <button
                                onClick={stopAnalysis}
                                className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
                            >
                                닫기
                            </button>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

/**
 * News Analysis Lab - Batch Processing Test Page
 * 
 * Uses global AnalysisContext for persistent progress across pages
 */

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Brain, Zap, BarChart2, CheckCircle } from 'lucide-react';
import { useAnalysis } from '../contexts/AnalysisContext';
import { getNewsStats } from '../services/newsService';

export const NewsAnalysisLab: React.FC = () => {
    const [analysisCount, setAnalysisCount] = useState(50);
    const { startAnalysis, isAnalyzing } = useAnalysis();

    const { data: stats, refetch: refetchStats } = useQuery({
        queryKey: ['news-stats'],
        queryFn: getNewsStats,
        refetchInterval: 60000,
    });

    const handleStartAnalysis = () => {
        startAnalysis(analysisCount);
    };

    return (
        <div className="p-6 space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                    <Brain className="text-purple-600" size={32} />
                    <div>
                        <h1 className="text-2xl font-bold text-gray-900">AI 분석 테스트</h1>
                        <p className="text-sm text-gray-600">
                            배치 분석 진행 상황을 실시간으로 확인하세요
                        </p>
                    </div>
                </div>
            </div>

            {/* Stats Overview */}
            {stats && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="bg-white rounded-lg shadow p-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-gray-600">전체 기사</p>
                                <p className="text-3xl font-bold mt-2">{stats.total_articles}</p>
                            </div>
                            <BarChart2 className="text-blue-500" size={40} />
                        </div>
                    </div>

                    <div className="bg-white rounded-lg shadow p-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-gray-600">분석 완료</p>
                                <p className="text-3xl font-bold mt-2 text-green-600">{stats.analyzed_articles}</p>
                                <p className="text-xs text-gray-500 mt-1">
                                    미분석: {stats.unanalyzed_articles}
                                </p>
                            </div>
                            <CheckCircle className="text-green-500" size={40} />
                        </div>
                    </div>

                    <div className="bg-white rounded-lg shadow p-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-gray-600">Gemini 사용량</p>
                                <p className="text-xl font-bold mt-2">
                                    {stats.gemini_usage.requests_used}/1500
                                </p>
                                <p className="text-xs text-gray-500 mt-1">{stats.gemini_usage.cost}</p>
                            </div>
                            <Zap className="text-yellow-500" size={40} />
                        </div>
                    </div>
                </div>
            )}

            {/* Control Panel */}
            <div className="bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg shadow-lg p-8">
                <h2 className="text-xl font-bold text-gray-900 mb-6">배치 분석 실행</h2>

                {/* Count Selector */}
                <div className="mb-6">
                    <label className="block text-sm font-medium text-gray-700 mb-3">
                        분석할 기사 수: <span className="text-purple-600 font-bold">{analysisCount}개</span>
                    </label>
                    <input
                        type="range"
                        min="10"
                        max="100"
                        step="10"
                        value={analysisCount}
                        onChange={(e) => setAnalysisCount(parseInt(e.target.value))}
                        className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-purple-600"
                        disabled={isAnalyzing}
                    />
                    <div className="flex justify-between text-xs text-gray-500 mt-1">
                        <span>10개</span>
                        <span>50개</span>
                        <span>100개</span>
                    </div>
                </div>

                {/* Start Button */}
                <button
                    onClick={handleStartAnalysis}
                    disabled={stats?.unanalyzed_articles === 0 || isAnalyzing}
                    className={`
            w-full flex items-center justify-center space-x-3 px-6 py-4 rounded-lg 
            font-semibold text-lg transition-all transform hover:scale-105
            ${stats?.unanalyzed_articles === 0 || isAnalyzing
                            ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                            : 'bg-gradient-to-r from-purple-600 to-blue-600 text-white hover:from-purple-700 hover:to-blue-700 shadow-lg'
                        }
          `}
                >
                    <Brain size={24} />
                    <span>
                        {isAnalyzing ? 'AI 분석 진행 중...' : `AI 분석 시작 (${analysisCount}개)`}
                    </span>
                </button>

                {stats?.unanalyzed_articles === 0 && (
                    <p className="text-center text-sm text-gray-500 mt-3">
                        ⚠️ 분석할 기사가 없습니다. RSS 크롤링을 먼저 실행해주세요.
                    </p>
                )}

                {isAnalyzing && (
                    <p className="text-center text-sm text-purple-600 mt-3 font-medium">
                        📊 분석이 진행 중입니다. 우측 하단 팝업 또는 전체 모달에서 확인하세요.
                    </p>
                )}
            </div>
        </div>
    );
};

export default NewsAnalysisLab;

/**
 * Analysis Configuration Modal
 * 
 * Popup to configure and start AI batch analysis from any page
 * Uses global AnalysisContext to trigger analysis
 */

import React, { useState } from 'react';
import { Brain, X, Zap } from 'lucide-react';
import { useAnalysis } from '../../contexts/AnalysisContext';

interface AnalysisConfigModalProps {
    isOpen: boolean;
    onClose: () => void;
}

export const AnalysisConfigModal: React.FC<AnalysisConfigModalProps> = ({ isOpen, onClose }) => {
    const [analysisCount, setAnalysisCount] = useState(50);
    const { startAnalysis, isAnalyzing } = useAnalysis();

    if (!isOpen) return null;

    const handleStartAnalysis = () => {
        startAnalysis(analysisCount);
        onClose(); // Close config modal, GlobalAnalysisProgress will take over
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
            <div className="bg-white rounded-lg shadow-2xl p-6 w-full max-w-md">
                {/* Header */}
                <div className="flex items-center justify-between mb-6">
                    <div className="flex items-center space-x-3">
                        <Brain className="text-purple-600" size={28} />
                        <div>
                            <h2 className="text-xl font-bold text-gray-900">AI 배치 분석</h2>
                            <p className="text-sm text-gray-600">Gemini 2.5 Flash</p>
                        </div>
                    </div>
                    <button
                        onClick={onClose}
                        className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                    >
                        <X size={20} className="text-gray-600" />
                    </button>
                </div>

                {/* Count Selector */}
                <div className="mb-6">
                    <label className="block text-sm font-medium text-gray-700 mb-3">
                        분석할 기사 수: <span className="text-purple-600 font-bold text-lg">{analysisCount}개</span>
                    </label>
                    <input
                        type="range"
                        min="10"
                        max="100"
                        step="10"
                        value={analysisCount}
                        onChange={(e) => setAnalysisCount(parseInt(e.target.value))}
                        className="w-full h-3 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-purple-600"
                        disabled={isAnalyzing}
                    />
                    <div className="flex justify-between text-xs text-gray-500 mt-2">
                        <span>10개</span>
                        <span>50개</span>
                        <span>100개</span>
                    </div>
                </div>

                {/* Info Box */}
                <div className="bg-purple-50 border border-purple-200 rounded-lg p-4 mb-6">
                    <div className="flex items-start space-x-2">
                        <Zap className="text-purple-600 flex-shrink-0 mt-0.5" size={18} />
                        <div>
                            <p className="text-xs text-purple-800 font-medium mb-1">실시간 진행 상황</p>
                            <p className="text-xs text-purple-700">
                                분석이 시작되면 우측 하단에 진행 상황이 표시됩니다.
                                다른 페이지로 이동해도 백그라운드에서 계속 진행됩니다.
                            </p>
                        </div>
                    </div>
                </div>

                {/* Buttons */}
                <div className="flex space-x-3">
                    <button
                        onClick={onClose}
                        className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                    >
                        취소
                    </button>
                    <button
                        onClick={handleStartAnalysis}
                        disabled={isAnalyzing}
                        className={`flex-1 flex items-center justify-center space-x-2 px-4 py-2 rounded-lg font-semibold transition-all ${isAnalyzing
                                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                                : 'bg-gradient-to-r from-purple-600 to-blue-600 text-white hover:from-purple-700 hover:to-blue-700'
                            }`}
                    >
                        <Brain size={18} />
                        <span>{isAnalyzing ? '분석 진행 중...' : `AI 분석 시작 (${analysisCount}개)`}</span>
                    </button>
                </div>

                {isAnalyzing && (
                    <p className="text-center text-xs text-purple-600 mt-3">
                        이미 분석이 진행 중입니다. 우측 하단을 확인하세요.
                    </p>
                )}
            </div>
        </div>
    );
};

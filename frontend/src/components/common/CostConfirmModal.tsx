/**
 * Cost Confirmation Modal
 * 
 * 비용이 발생하는 API 호출 전에 사용자에게 확인을 요청하는 모달
 * 
 * 사용 예:
 * <CostConfirmModal
 *   isOpen={showModal}
 *   onConfirm={() => executeExpensiveAPI()}
 *   onCancel={() => setShowModal(false)}
 *   action="AI 분석"
 *   estimatedCost={0.015}
 *   budgetStatus={budgetData}
 * />
 */

import React from 'react';
import { AlertTriangle, DollarSign, TrendingUp, X } from 'lucide-react';
import { Button } from './Button';

export interface BudgetStatus {
    status: 'OK' | 'WARNING' | 'CRITICAL';
    daily: {
        cost: number;
        limit: number;
        percentage: number;
    };
    monthly: {
        cost: number;
        limit: number;
        percentage: number;
    };
}

interface CostConfirmModalProps {
    isOpen: boolean;
    onConfirm: () => void;
    onCancel: () => void;
    action: string;  // 예: "AI 분석", "뉴스 조회"
    estimatedCost: number;  // 예상 비용 (USD)
    budgetStatus?: BudgetStatus | null;
    isLoading?: boolean;
    apiType?: 'ai' | 'news' | 'data';  // API 유형
    remainingFreeQuota?: number;  // 남은 무료 쿼터 (뉴스 API용)
}

export const CostConfirmModal: React.FC<CostConfirmModalProps> = ({
    isOpen,
    onConfirm,
    onCancel,
    action,
    estimatedCost,
    budgetStatus,
    isLoading = false,
    apiType = 'ai',
    remainingFreeQuota,
}) => {
    if (!isOpen) return null;

    const isOverBudget = budgetStatus?.status === 'CRITICAL';
    const isWarning = budgetStatus?.status === 'WARNING';
    const hasFreeQuota = remainingFreeQuota !== undefined && remainingFreeQuota > 0;

    const getStatusColor = () => {
        if (isOverBudget) return 'text-red-600';
        if (isWarning) return 'text-yellow-600';
        return 'text-green-600';
    };

    const getStatusBg = () => {
        if (isOverBudget) return 'bg-red-50 border-red-200';
        if (isWarning) return 'bg-yellow-50 border-yellow-200';
        return 'bg-green-50 border-green-200';
    };

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-lg shadow-xl max-w-md w-full">
                {/* Header */}
                <div className="flex items-center justify-between p-4 border-b">
                    <div className="flex items-center gap-2">
                        {isOverBudget ? (
                            <AlertTriangle className="text-red-500" size={24} />
                        ) : (
                            <DollarSign className="text-blue-500" size={24} />
                        )}
                        <h3 className="text-lg font-semibold">비용 확인</h3>
                    </div>
                    <button
                        onClick={onCancel}
                        className="text-gray-400 hover:text-gray-600"
                    >
                        <X size={20} />
                    </button>
                </div>

                {/* Content */}
                <div className="p-4 space-y-4">
                    {/* Action Description */}
                    <div className="text-center">
                        <p className="text-gray-600">
                            <strong>{action}</strong>을(를) 실행하시겠습니까?
                        </p>
                    </div>

                    {/* Estimated Cost */}
                    <div className={`p-4 rounded-lg border ${getStatusBg()}`}>
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-sm text-gray-600">예상 비용</span>
                            <span className="text-xl font-bold text-gray-900">
                                ${estimatedCost.toFixed(4)}
                            </span>
                        </div>

                        {/* Free Quota Info (for News API) */}
                        {hasFreeQuota && (
                            <div className="text-sm text-green-600 mt-2">
                                ✅ 무료 쿼터 사용 (남은 횟수: {remainingFreeQuota})
                            </div>
                        )}
                    </div>

                    {/* Budget Status */}
                    {budgetStatus && (
                        <div className="space-y-2">
                            <h4 className="text-sm font-medium text-gray-700">현재 예산 사용량</h4>

                            {/* Daily Budget */}
                            <div className="flex items-center justify-between text-sm">
                                <span className="text-gray-600">일일</span>
                                <span className={getStatusColor()}>
                                    ${budgetStatus.daily.cost.toFixed(2)} / ${budgetStatus.daily.limit.toFixed(2)}
                                    <span className="ml-2">
                                        ({budgetStatus.daily.percentage.toFixed(1)}%)
                                    </span>
                                </span>
                            </div>
                            <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                                <div
                                    className={`h-full ${budgetStatus.daily.percentage > 100
                                            ? 'bg-red-500'
                                            : budgetStatus.daily.percentage > 80
                                                ? 'bg-yellow-500'
                                                : 'bg-green-500'
                                        }`}
                                    style={{ width: `${Math.min(budgetStatus.daily.percentage, 100)}%` }}
                                />
                            </div>

                            {/* Monthly Budget */}
                            <div className="flex items-center justify-between text-sm mt-2">
                                <span className="text-gray-600">월간</span>
                                <span className={getStatusColor()}>
                                    ${budgetStatus.monthly.cost.toFixed(2)} / ${budgetStatus.monthly.limit.toFixed(2)}
                                    <span className="ml-2">
                                        ({budgetStatus.monthly.percentage.toFixed(1)}%)
                                    </span>
                                </span>
                            </div>
                            <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                                <div
                                    className={`h-full ${budgetStatus.monthly.percentage > 100
                                            ? 'bg-red-500'
                                            : budgetStatus.monthly.percentage > 80
                                                ? 'bg-yellow-500'
                                                : 'bg-green-500'
                                        }`}
                                    style={{ width: `${Math.min(budgetStatus.monthly.percentage, 100)}%` }}
                                />
                            </div>
                        </div>
                    )}

                    {/* Warning Message */}
                    {isOverBudget && (
                        <div className="p-3 bg-red-100 border border-red-300 rounded-lg text-sm text-red-700">
                            ⚠️ <strong>주의:</strong> 일일/월간 예산을 초과했습니다.
                            계속 진행하면 추가 비용이 발생합니다.
                        </div>
                    )}

                    {isWarning && !isOverBudget && (
                        <div className="p-3 bg-yellow-100 border border-yellow-300 rounded-lg text-sm text-yellow-700">
                            ⚠️ 예산의 80% 이상을 사용했습니다.
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="flex gap-3 p-4 border-t bg-gray-50 rounded-b-lg">
                    <Button
                        onClick={onCancel}
                        variant="secondary"
                        className="flex-1"
                        disabled={isLoading}
                    >
                        취소
                    </Button>
                    <Button
                        onClick={onConfirm}
                        className={`flex-1 ${isOverBudget ? 'bg-red-600 hover:bg-red-700' : ''}`}
                        disabled={isLoading}
                    >
                        {isLoading ? '처리 중...' : isOverBudget ? '그래도 진행' : '확인'}
                    </Button>
                </div>
            </div>
        </div>
    );
};

/**
 * useCostCheck Hook
 * 
 * 비용이 발생하는 API 호출 전에 예산을 확인하는 훅
 * 
 * 사용 예:
 * const { checkBudget, budgetStatus, showConfirmModal, ... } = useCostCheck();
 * 
 * const handleAnalyze = async () => {
 *   const canProceed = await checkBudget({
 *     action: 'AI 분석',
 *     estimatedCost: 0.015,
 *     skipConfirmIfUnderBudget: false // 예산 내여도 항상 확인
 *   });
 *   
 *   if (canProceed) {
 *     await executeAnalysis();
 *   }
 * };
 */

import { useState, useCallback } from 'react';
import axios from 'axios';
import { BudgetStatus } from '../components/common/CostConfirmModal';

const API_BASE = '/api';

interface CostCheckOptions {
    action: string;
    estimatedCost: number;
    skipConfirmIfUnderBudget?: boolean;  // 예산 내면 확인 없이 진행
    apiType?: 'ai' | 'news' | 'data';
}

interface UseCostCheckReturn {
    // State
    budgetStatus: BudgetStatus | null;
    isLoading: boolean;
    error: string | null;

    // Modal State
    showConfirmModal: boolean;
    pendingAction: string;
    pendingEstimatedCost: number;
    pendingApiType: 'ai' | 'news' | 'data';

    // Actions
    checkBudget: (options: CostCheckOptions) => Promise<boolean>;
    confirmAndProceed: () => void;
    cancelAction: () => void;
    refreshBudgetStatus: () => Promise<void>;

    // News API specific
    remainingNewsQuota: number | null;
}

// 뉴스 API 일일 무료 쿼터 (설정 가능)
const NEWS_API_DAILY_FREE_QUOTA = 100;

export const useCostCheck = (): UseCostCheckReturn => {
    const [budgetStatus, setBudgetStatus] = useState<BudgetStatus | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Modal state
    const [showConfirmModal, setShowConfirmModal] = useState(false);
    const [pendingAction, setPendingAction] = useState('');
    const [pendingEstimatedCost, setPendingEstimatedCost] = useState(0);
    const [pendingApiType, setPendingApiType] = useState<'ai' | 'news' | 'data'>('ai');
    const [resolvePromise, setResolvePromise] = useState<((value: boolean) => void) | null>(null);

    // News API quota tracking
    const [remainingNewsQuota, setRemainingNewsQuota] = useState<number | null>(null);
    const [newsApiCallsToday, setNewsApiCallsToday] = useState(0);

    // Fetch budget status from backend
    const refreshBudgetStatus = useCallback(async () => {
        try {
            const response = await axios.get(`${API_BASE}/cost/budget/check`);
            if (response.data) {
                setBudgetStatus(response.data);
            }
            setError(null);
        } catch (err: any) {
            console.error('Failed to fetch budget status:', err);
            // Fallback for demo/dev if API fails
            setBudgetStatus({
                status: 'OK',
                daily: { cost: 0, limit: 1.0, percentage: 0 },
                monthly: { cost: 0, limit: 10.0, percentage: 0 }
            });
        }
    }, []);

    // Get news API usage from localStorage (simple client-side tracking)
    const getNewsApiUsageToday = useCallback(() => {
        const today = new Date().toISOString().split('T')[0];
        const stored = localStorage.getItem('news_api_usage');

        if (stored) {
            const data = JSON.parse(stored);
            if (data.date === today) {
                return data.count;
            }
        }
        return 0;
    }, []);

    // Increment news API usage
    const incrementNewsApiUsage = useCallback(() => {
        const today = new Date().toISOString().split('T')[0];
        const current = getNewsApiUsageToday();
        localStorage.setItem('news_api_usage', JSON.stringify({
            date: today,
            count: current + 1,
        }));
        setNewsApiCallsToday(current + 1);
        setRemainingNewsQuota(Math.max(0, NEWS_API_DAILY_FREE_QUOTA - current - 1));
    }, [getNewsApiUsageToday]);

    // Main check budget function
    const checkBudget = useCallback(async (options: CostCheckOptions): Promise<boolean> => {
        const { action, estimatedCost, skipConfirmIfUnderBudget = false, apiType = 'ai' } = options;

        setIsLoading(true);
        setError(null);

        try {
            // Fetch current budget status
            await refreshBudgetStatus();

            // For news API, check free quota
            if (apiType === 'news') {
                const usedToday = getNewsApiUsageToday();
                const remaining = NEWS_API_DAILY_FREE_QUOTA - usedToday;
                setNewsApiCallsToday(usedToday);
                setRemainingNewsQuota(remaining);

                // If we have free quota and skipConfirmIfUnderBudget, proceed
                if (remaining > 0 && skipConfirmIfUnderBudget) {
                    incrementNewsApiUsage();
                    return true;
                }
            }

            // If under budget and skip confirm is enabled, proceed immediately
            if (skipConfirmIfUnderBudget && budgetStatus?.status === 'OK') {
                if (apiType === 'news') {
                    incrementNewsApiUsage();
                }
                return true;
            }

            // Show confirmation modal
            setPendingAction(action);
            setPendingEstimatedCost(estimatedCost);
            setPendingApiType(apiType);
            setShowConfirmModal(true);

            // Return a promise that resolves when user confirms/cancels
            return new Promise((resolve) => {
                setResolvePromise(() => resolve);
            });

        } catch (err) {
            setError('예산 확인에 실패했습니다.');
            console.error('Budget check failed:', err);
            return false;
        } finally {
            setIsLoading(false);
        }
    }, [budgetStatus, refreshBudgetStatus, getNewsApiUsageToday, incrementNewsApiUsage]);

    // Confirm action in modal
    const confirmAndProceed = useCallback(() => {
        if (pendingApiType === 'news') {
            incrementNewsApiUsage();
        }
        setShowConfirmModal(false);
        if (resolvePromise) {
            resolvePromise(true);
            setResolvePromise(null);
        }
    }, [pendingApiType, incrementNewsApiUsage, resolvePromise]);

    // Cancel action in modal
    const cancelAction = useCallback(() => {
        setShowConfirmModal(false);
        if (resolvePromise) {
            resolvePromise(false);
            setResolvePromise(null);
        }
    }, [resolvePromise]);

    return {
        budgetStatus,
        isLoading,
        error,
        showConfirmModal,
        pendingAction,
        pendingEstimatedCost,
        pendingApiType,
        checkBudget,
        confirmAndProceed,
        cancelAction,
        refreshBudgetStatus,
        remainingNewsQuota,
    };
};

// Estimated costs for different operations
export const ESTIMATED_COSTS = {
    // AI Analysis
    AI_ANALYSIS_CLAUDE_SONNET: 0.015,  // ~2000 tokens
    AI_ANALYSIS_CLAUDE_HAIKU: 0.002,
    AI_ANALYSIS_GEMINI: 0.0004,

    // Deep Reasoning (longer context)
    DEEP_REASONING: 0.03,

    // News Analysis
    NEWS_FETCH: 0,  // Free within quota
    NEWS_AI_ANALYSIS: 0.02,

    // Embeddings
    EMBEDDING_GENERATION: 0.00001,

    // Reports
    REPORT_GENERATION: 0.01,
};

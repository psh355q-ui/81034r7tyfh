/**
 * Persona API Service
 * 
 * 📊 Data Sources:
 *   - Backend: /api/persona/* endpoints
 *   - Backend: /api/partitions/* endpoints
 *   - Backend: /api/journey/* endpoints
 *   - Backend: /api/thesis/* endpoints
 * 
 * 📤 Used By:
 *   - PersonaContext.tsx
 *   - ModeSwitcher.tsx
 *   - PartitionsCard.tsx
 *   - JourneyTimeline.tsx
 */

import axios from 'axios';

const API_BASE_URL = '/api';

const apiClient = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// ============================================================================
// Types
// ============================================================================

export type PersonaMode = 'dividend' | 'long_term' | 'trading' | 'aggressive';

export interface PersonaModeInfo {
    mode: PersonaMode;
    description: string;
    weights: {
        trader_mvp: number;
        risk_mvp: number;
        analyst_mvp: number;
    };
    features: Record<string, boolean>;
    leverage_allowed: boolean;
}

export interface SwitchModeResponse {
    success: boolean;
    previous_mode: string;
    current_mode: string;
    weights: Record<string, number>;
    message: string;
}

export interface WalletSummary {
    value: number;
    pct: number;
    target_pct: number;
    deviation: number;
    positions_count: number;
    unrealized_pnl: number;
    unrealized_pnl_pct: number;
    needs_rebalance: boolean;
}

export interface PartitionsSummary {
    total_value: number;
    wallets: {
        core: WalletSummary;
        income: WalletSummary;
        satellite: WalletSummary;
    };
    rebalance_needed: boolean;
}

export interface JourneyDecision {
    decision_id: string;
    ticker: string;
    decision_type: string;
    market_condition: string;
    entry_price: number;
    quantity: number;
    decision_date: string;
    reasoning: string;
    outcome_30d: number | null;
    outcome_90d: number | null;
    followed_ai: boolean;
}

export interface JourneyHistory {
    user_id: string;
    decisions: JourneyDecision[];
    statistics: {
        total_decisions: number;
        by_type: Record<string, number>;
        by_condition: Record<string, number>;
        ai_followed_rate: number;
    };
}

export interface QualityScore {
    scores: {
        fear_response: number;
        greed_response: number;
        consistency: number;
        discipline: number;
        overall: number;
    };
    insights: string[];
}

export interface CoachingAdvice {
    message: string;
    based_on_decisions: string[];
    confidence: number;
    historical_success_rate: number | null;
}

// ============================================================================
// Persona API
// ============================================================================

export const getPersonaModes = async (): Promise<PersonaModeInfo[]> => {
    const response = await apiClient.get('/persona/modes');
    return response.data;
};

export const getCurrentMode = async (): Promise<PersonaModeInfo & { leverage_cap: number }> => {
    const response = await apiClient.get('/persona/current');
    return response.data;
};

export const switchPersonaMode = async (mode: string): Promise<SwitchModeResponse> => {
    const response = await apiClient.post('/persona/switch', { mode });
    return response.data;
};

export const checkLeverageProduct = async (ticker: string): Promise<{
    ticker: string;
    is_leveraged: boolean;
    category: string;
    max_allowed_value?: number;
    warning?: string;
}> => {
    const response = await apiClient.get(`/persona/leverage-check/${ticker}`);
    return response.data;
};

// ============================================================================
// Partitions API
// ============================================================================

export const getPartitionsSummary = async (): Promise<PartitionsSummary> => {
    const response = await apiClient.get('/partitions/summary');
    return response.data;
};

export const getWalletDetail = async (wallet: string) => {
    const response = await apiClient.get(`/partitions/wallet/${wallet}`);
    return response.data;
};

export const allocateToWallet = async (
    wallet: string,
    ticker: string,
    quantity: number,
    price: number
) => {
    const response = await apiClient.post('/partitions/allocate', {
        wallet,
        ticker,
        quantity,
        price,
    });
    return response.data;
};

export const getRebalanceRecommendations = async () => {
    const response = await apiClient.get('/partitions/rebalance');
    return response.data;
};

// ============================================================================
// Journey Memory API
// ============================================================================

export const getJourneyHistory = async (limit: number = 20): Promise<JourneyHistory> => {
    const response = await apiClient.get(`/journey/history?limit=${limit}`);
    return response.data;
};

export const recordDecision = async (decision: {
    ticker: string;
    decision_type: string;
    market_condition: string;
    entry_price: number;
    quantity: number;
    reasoning: string;
    followed_ai?: boolean;
}) => {
    const response = await apiClient.post('/journey/record', decision);
    return response.data;
};

export const getCoaching = async (
    ticker: string,
    current_market_condition: string,
    current_action?: string
): Promise<CoachingAdvice> => {
    const response = await apiClient.post('/journey/coaching', {
        ticker,
        current_market_condition,
        current_action,
    });
    return response.data;
};

export const getQualityScore = async (): Promise<QualityScore> => {
    const response = await apiClient.get('/journey/quality-score');
    return response.data;
};

// ============================================================================
// Thesis API
// ============================================================================

export const checkThesis = async (
    ticker: string,
    thesis_type: string,
    fundamental_data: Record<string, unknown>
) => {
    const response = await apiClient.post('/thesis/check', {
        ticker,
        thesis_type,
        fundamental_data,
    });
    return response.data;
};

export const getThesisThresholds = async () => {
    const response = await apiClient.get('/thesis/thresholds');
    return response.data;
};

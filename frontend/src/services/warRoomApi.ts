/**
 * War Room API Service - MVP Version
 *
 * Type-safe API client for MVP War Room (3+1 Agent System)
 *
 * Created: 2025-12-21
 * Updated: 2025-12-31 - MVP Consolidation
 * Phase: MVP (3+1 Agent System)
 *
 * MVP Benefits:
 * - Cost: 67% reduction (9 agents → 4 agents)
 * - Speed: 67% faster
 * - API: /api/war-room-mvp/*
 */

const API_BASE_URL = '/api/war-room-mvp';

// ============================================================================
// TypeScript Interfaces
// ============================================================================

export interface WarRoomVote {
    agent: string;
    action: 'BUY' | 'SELL' | 'HOLD';
    confidence: number;
    reasoning: string;
}

export interface WarRoomConsensus {
    action: 'BUY' | 'SELL' | 'HOLD';
    confidence: number;
    summary: string;
}

export interface WarRoomDebateResponse {
    session_id: number;
    ticker: string;
    votes: WarRoomVote[];
    consensus: WarRoomConsensus;
    constitutional_valid: boolean;
    signal_id: number | null;
    timestamp: string;
    latency_ms?: number;  // API 호출 소요 시간 (milliseconds)
}

export interface DebateSession {
    id: number;
    ticker: string;
    consensus_action: 'BUY' | 'SELL' | 'HOLD';
    consensus_confidence: number;
    constitutional_valid: boolean;
    agent_votes: Record<string, any>;
    signal_generated: boolean;
    created_at: string;
}

export interface WarRoomHealthResponse {
    status: string;
    war_room_active: boolean;
    shadow_trading_active: boolean;
    timestamp: string;
    version: string;
}

// ============================================================================
// API Client
// ============================================================================

export const warRoomApi = {
    /**
     * Run War Room debate for a ticker
     * POST /api/war-room-mvp/deliberate
     */
    runDebate: async (ticker: string): Promise<WarRoomDebateResponse> => {
        const startTime = performance.now();  // 호출 시작 시간

        const response = await fetch(`${API_BASE_URL}/deliberate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                symbol: ticker
                // market_data와 portfolio_state는 백엔드에서 자동으로 가져옴
            }),
        });

        if (!response.ok) {
            throw new Error(`War Room debate failed: ${response.statusText}`);
        }

        const data = await response.json();
        const endTime = performance.now();  // 호출 종료 시간
        const latency_ms = Math.round(endTime - startTime);  // 소요 시간 (ms)

        // Convert MVP response to legacy format for compatibility
        return {
            session_id: 0,
            ticker: data.symbol || ticker,
            votes: [],
            consensus: {
                action: data.recommended_action?.toUpperCase() || 'HOLD',
                confidence: data.confidence || 0,
                summary: data.conversation_summary || ''
            },
            constitutional_valid: data.can_execute || false,
            signal_id: null,
            timestamp: data.timestamp || new Date().toISOString(),
            latency_ms: latency_ms  // API 호출 시간 추가
        };
    },

    /**
     * Get War Room debate session history
     * GET /api/war-room-mvp/history
     */
    getSessions: async (params: { limit?: number } = {}): Promise<DebateSession[]> => {
        const queryParams = new URLSearchParams();
        if (params.limit) {
            queryParams.append('limit', params.limit.toString());
        }

        const url = `${API_BASE_URL}/history${queryParams.toString() ? `?${queryParams}` : ''}`;
        const response = await fetch(url);

        if (!response.ok) {
            throw new Error(`Failed to fetch War Room sessions: ${response.statusText}`);
        }

        const data = await response.json();
        const decisions = data.decisions || [];

        // Convert MVP decisions to legacy format
        return decisions.map((decision: any, index: number) => ({
            id: index,
            ticker: decision.symbol || '',
            consensus_action: decision.final_decision?.toUpperCase() || 'HOLD',
            consensus_confidence: decision.confidence || 0,
            constitutional_valid: decision.can_execute || false,
            agent_votes: decision.agent_opinions || {},
            pm_decision: decision.pm_decision || null,  // PM 결정 상세 정보 추가
            signal_generated: decision.can_execute || false,
            created_at: decision.timestamp || new Date().toISOString()
        }));
    },

    /**
     * Get War Room health status
     * GET /api/war-room-mvp/health
     */
    getHealth: async (): Promise<WarRoomHealthResponse> => {
        const response = await fetch(`${API_BASE_URL}/health`);

        if (!response.ok) {
            throw new Error(`Failed to fetch War Room health: ${response.statusText}`);
        }

        return response.json();
    },
};

export default warRoomApi;

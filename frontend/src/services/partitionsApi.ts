/**
 * Partitions API Service
 * 
 * Manages Account Partitions (Core/Income/Satellite) and Shadow Trading.
 * 
 * Created: 2026-01-05
 * Phase: 6.2 Frontend Integration
 */

const API_BASE_URL = '/api/partitions';

// ===================================
// Interfaces
// ===================================

export interface WalletSummary {
    wallet: string; // core, income, satellite
    current_value: number;
    current_pct: number;
    target_pct: number;
    deviation: number;
    cash: number;
    positions_count: number;
    unrealized_pnl: number;
    unrealized_pnl_pct: number;
    needs_rebalance: boolean;
}

export interface PartitionSummary {
    total_equity: number;
    wallets: {
        core: WalletSummary;
        income: WalletSummary;
        satellite: WalletSummary;
    };
    cash_total: number;
}

export interface PartitionPosition {
    ticker: string;
    quantity: number;
    avg_price: number;
    current_price: number;
    market_value: number;
    unrealized_pnl: number;
    unrealized_pnl_pct: number;
    allocation_pct: number;
}

export interface WalletDetail extends WalletSummary {
    description: string;
    allowed_leverage: boolean;
    positions: PartitionPosition[];
}

export interface LeverageCheckResponse {
    ticker: string;
    is_leveraged: boolean;
    leverage_ratio: number;
    allowed_wallets: string[];
    note: string;
}

export interface AllocateRequest {
    wallet: string;
    ticker: string;
    quantity: number;
    price: number;
    user_id?: string;
}

// ===================================
// API Client
// ===================================

export const partitionsApi = {
    /**
     * Get summary of all partitions (Core/Income/Satellite)
     */
    getSummary: async (): Promise<PartitionSummary> => {
        const response = await fetch(`${API_BASE_URL}/summary`);
        if (!response.ok) throw new Error('Failed to fetch partition summary');
        return response.json();
    },

    /**
     * Get detailed info for a specific wallet
     */
    getWalletDetail: async (wallet: string): Promise<WalletDetail> => {
        const response = await fetch(`${API_BASE_URL}/wallet/${wallet}`);
        if (!response.ok) throw new Error(`Failed to fetch wallet detail for ${wallet}`);
        return response.json();
    },

    /**
     * Check if a ticker is a leveraged product
     */
    checkLeverage: async (ticker: string): Promise<LeverageCheckResponse> => {
        const response = await fetch(`${API_BASE_URL}/leverage/${ticker}`);
        if (!response.ok) throw new Error(`Failed to check leverage for ${ticker}`);
        return response.json();
    },

    /**
     * Allocate position to a wallet (Buy)
     */
    allocate: async (data: AllocateRequest) => {
        const response = await fetch(`${API_BASE_URL}/allocate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Allocation failed');
        }
        return response.json();
    },

    /**
     * Sell position from a wallet
     */
    sell: async (data: AllocateRequest) => {
        const response = await fetch(`${API_BASE_URL}/sell`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Sell failed');
        }
        return response.json();
    },


    /**
     * Get rebalancing recommendations
     */
    getRebalance: async () => {
        const response = await fetch(`${API_BASE_URL}/rebalance`);
        if (!response.ok) throw new Error('Failed to fetch rebalance info');
        return response.json();
    },

    /**
     * Get shadow trade orders
     */
    getOrders: async (limit: number = 20) => {
        const response = await fetch(`/api/orders?limit=${limit}`);
        if (!response.ok) throw new Error('Failed to fetch orders');
        return response.json();
    }
};

export interface Order {
    id: number;
    ticker: string;
    action: string;
    quantity: number;
    price: number;
    order_type: string;
    status: string;
    broker: string;
    order_id: string;
    signal_id?: number;
    created_at: string;
    updated_at?: string;
    filled_at?: string;
}

export default partitionsApi;

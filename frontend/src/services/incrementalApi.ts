/**
 * Incremental Update System API Service
 * Phase 16: Cost Savings & Performance Monitoring
 */

import axios from 'axios';

const API_BASE_URL = '/api/incremental';

export interface IncrementalStats {
    total_tickers: number;
    total_rows_stored: number;
    last_update_date: string;
    last_price_date: string;
    avg_rows_per_ticker: number;
    scheduler_last_run?: {
        start_time: string;
        end_time: string;
        duration_seconds: number;
        successful: number;
        failed: number;
        total_new_rows: number;
    };
}

export interface StorageUsage {
    total_size_gb: number;
    total_files: number;
    locations: Record<string, {
        path: string;
        size_mb: number;
        file_count: number;
        usage_pct: number;
    }>;
}

export interface CostSavings {
    api_calls: {
        before_per_day: number;
        after_per_day: number;
        saved_per_day: number;
        reduction_pct: number;
    };
    performance: {
        speedup_factor: number;
        time_saved_seconds: number;
    };
    estimated_monthly_cost: {
        before_usd: number;
        after_usd: number;
        savings_usd: number;
        savings_pct: number;
    };
}

export interface SchedulerStatus {
    is_running: boolean;
    schedule_time: string;
    last_update?: {
        successful: number;
        failed: number;
        duration_seconds: number;
    };
    max_retries: number;
    retry_delay_seconds: number;
}

export const incrementalApi = {
    /**
     * Get overall statistics
     */
    getStats: async (): Promise<IncrementalStats> => {
        const response = await axios.get(`${API_BASE_URL}/stats`);
        return response.data;
    },

    /**
     * Get storage usage statistics
     */
    getStorage: async (): Promise<StorageUsage> => {
        const response = await axios.get(`${API_BASE_URL}/storage`);
        return response.data;
    },

    /**
     * Get cost savings analysis
     */
    getCostSavings: async (tickers: number = 100): Promise<CostSavings> => {
        const response = await axios.get(`${API_BASE_URL}/cost-savings`, {
            params: { tickers }
        });
        return response.data;
    },

    /**
     * Get scheduler status
     */
    getSchedulerStatus: async (): Promise<SchedulerStatus> => {
        const response = await axios.get(`${API_BASE_URL}/scheduler-status`);
        return response.data;
    },

    /**
     * Start the scheduler
     */
    startScheduler: async (): Promise<{ status: string; message: string }> => {
        const response = await axios.post(`${API_BASE_URL}/scheduler/start`);
        return response.data;
    },

    /**
     * Stop the scheduler
     */
    stopScheduler: async (): Promise<{ status: string; message: string }> => {
        const response = await axios.post(`${API_BASE_URL}/scheduler/stop`);
        return response.data;
    },

    /**
     * Run manual update immediately
     */
    runNow: async (): Promise<{ status: string; stats: any }> => {
        const response = await axios.post(`${API_BASE_URL}/scheduler/run-now`);
        return response.data;
    }
};

/**
 * Advanced Analytics API Service
 *
 * @author AI Trading System Team
 * @date 2025-11-26
 */

import api from './api';

export interface AttributionData {
  strategy_attribution?: Record<string, any>;
  sector_attribution?: Record<string, any>;
  ai_source_attribution?: Record<string, any>;
  position_attribution?: any[];
  time_attribution?: any;
}

export interface RiskMetrics {
  var_metrics?: any;
  drawdown_metrics?: any;
  concentration_metrics?: any;
  correlation_analysis?: any;
  stress_test_scenarios?: any;
}

export interface TradeInsights {
  win_loss_patterns?: any;
  execution_quality?: any;
  hold_duration_analysis?: any;
  confidence_impact?: any;
}

/**
 * Performance Attribution
 */
export const getPerformanceAttribution = async (
  startDate: string,
  endDate: string,
  dimension: string = 'all'
): Promise<AttributionData> => {
  const response = await api.get('/reports/advanced/performance-attribution', {
    params: { start_date: startDate, end_date: endDate, dimension },
  });
  return response.data;
};

/**
 * Risk Analytics
 */
export const getRiskMetrics = async (
  startDate: string,
  endDate: string,
  metric: string = 'all'
): Promise<RiskMetrics> => {
  const response = await api.get('/reports/advanced/risk-metrics', {
    params: { start_date: startDate, end_date: endDate, metric },
  });
  return response.data;
};

/**
 * Trade Analytics
 */
export const getTradeInsights = async (
  startDate: string,
  endDate: string,
  analysis: string = 'all'
): Promise<TradeInsights> => {
  const response = await api.get('/reports/advanced/trade-insights', {
    params: { start_date: startDate, end_date: endDate, analysis },
  });
  return response.data;
};

/**
 * Query Keys for React Query
 */
export const analyticsKeys = {
  all: ['analytics'] as const,
  performance: (startDate: string, endDate: string, dimension: string) =>
    [...analyticsKeys.all, 'performance', startDate, endDate, dimension] as const,
  risk: (startDate: string, endDate: string, metric: string) =>
    [...analyticsKeys.all, 'risk', startDate, endDate, metric] as const,
  trade: (startDate: string, endDate: string, analysis: string) =>
    [...analyticsKeys.all, 'trade', startDate, endDate, analysis] as const,
};

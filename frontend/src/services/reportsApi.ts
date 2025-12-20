/**
 * Reports API Service
 *
 * Handles all report-related API calls:
 * - Daily/Weekly/Monthly reports
 * - Performance analytics
 * - PDF/CSV exports
 * - Time series data
 *
 * @author AI Trading System Team
 * @date 2025-11-25
 */

import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001';

// =============================================================================
// Types
// =============================================================================

export interface DailyReportSummary {
  date: string;
  portfolio_value: number;
  daily_pnl: number;
  daily_return_pct: number;
  trades_count: number;
  win_rate: number | null;
}

export interface ExecutiveSummary {
  portfolio_value: number;
  daily_pnl: number;
  daily_return_pct: number;
  total_return_pct: number;
  win_rate: number | null;
  sharpe_ratio: number | null;
  positions_count: number;
  trades_count: number;
  ai_cost_usd: number;
  highlights: string[];
  risk_alerts: string[];
}

export interface TradingActivity {
  total_trades: number;
  buy_trades: number;
  sell_trades: number;
  total_volume_usd: number;
  avg_position_size_usd: number | null;
  win_count: number;
  loss_count: number;
  win_rate: number | null;
  avg_win_pct: number | null;
  avg_loss_pct: number | null;
  avg_slippage_bps: number | null;
  avg_execution_time_ms: number | null;
  top_trades: TableData | null;
}

export interface PortfolioOverview {
  total_value: number;
  cash: number;
  invested_value: number;
  positions_count: number;
  sector_allocation: Record<string, number>;
  strategy_allocation: Record<string, number>;
  top_positions: TableData | null;
  largest_position_pct: number | null;
  cash_pct: number | null;
}

export interface AIPerformance {
  signals_generated: number;
  signal_avg_confidence: number | null;
  signal_accuracy: number | null;
  ai_cost_usd: number;
  ai_tokens_used: number;
  cost_per_signal: number | null;
  source_comparison: ChartData | null;
  rag_impact_summary: string | null;
}

export interface RiskMetrics {
  sharpe_ratio: number | null;
  sortino_ratio: number | null;
  max_drawdown_pct: number | null;
  volatility_30d: number | null;
  var_95: number | null;
  circuit_breaker_triggers: number;
  kill_switch_active: boolean;
  alerts_triggered: number;
  drawdown_chart: ChartData | null;
}

export interface ChartData {
  chart_type: 'line' | 'bar' | 'pie' | 'area';
  title: string;
  x_labels: string[];
  datasets: {
    label: string;
    data: number[];
    color?: string;
    backgroundColor?: string | string[];
    fill?: boolean;
  }[];
  y_axis_label?: string;
  x_axis_label?: string;
}

export interface TableData {
  title: string;
  headers: string[];
  rows: (string | number)[][];
  footer?: string[];
}

export interface DailyReport {
  report_id: string;
  report_type: 'daily';
  report_date: string;
  generated_at: string;
  executive_summary: ExecutiveSummary | null;
  trading_activity: TradingActivity | null;
  portfolio_overview: PortfolioOverview | null;
  ai_performance: AIPerformance | null;
  risk_metrics: RiskMetrics | null;
  performance_chart: ChartData | null;
  pnl_chart: ChartData | null;
  notes: string | null;
}

export interface WeeklyReport {
  report_id: string;
  year: number;
  week_number: number;
  week_start_date: string;
  week_end_date: string;
  portfolio_value_start: number;
  portfolio_value_end: number;
  weekly_pnl: number;
  weekly_return_pct: number | null;
  total_trades: number;
  win_rate: number | null;
}

export interface MonthlyReport {
  report_id: string;
  year: number;
  month: number;
  portfolio_value_start: number;
  portfolio_value_end: number;
  monthly_pnl: number;
  monthly_return_pct: number | null;
  total_trades: number;
  trading_days: number;
  win_rate: number | null;
  sharpe_ratio: number | null;
  total_ai_cost_usd: number | null;
}

export interface PerformanceSummary {
  period: {
    start_date: string;
    end_date: string;
    days: number;
  };
  current: {
    portfolio_value: number;
    positions_count: number;
  };
  performance: {
    total_pnl: number;
    total_trades: number;
    total_volume_usd: number;
    win_rate: number | null;
    avg_daily_pnl: number;
  };
  risk: {
    sharpe_ratio: number | null;
    max_drawdown_pct: number | null;
    volatility_30d: number | null;
  };
  ai: {
    total_cost_usd: number;
    total_signals: number;
    avg_accuracy: number | null;
  };
}

export interface TimeSeriesData {
  metric: string;
  start_date: string;
  end_date: string;
  data_points: number;
  dates: string[];
  values: (number | null)[];
}

// =============================================================================
// API Functions
// =============================================================================

/**
 * Get daily report
 */
export const getDailyReport = async (
  targetDate?: string,
  format: 'json' | 'pdf' = 'json'
): Promise<DailyReport | Blob> => {
  const params = new URLSearchParams();
  if (targetDate) params.append('target_date', targetDate);
  if (format) params.append('format', format);

  const response = await axios.get(
    `${API_BASE_URL}/reports/daily?${params.toString()}`,
    format === 'pdf' ? { responseType: 'blob' } : {}
  );

  return response.data;
};

/**
 * Get daily report summaries for date range
 */
export const getDailySummaries = async (
  startDate: string,
  endDate: string
): Promise<DailyReportSummary[]> => {
  const response = await axios.get(`${API_BASE_URL}/reports/daily/summary`, {
    params: { start_date: startDate, end_date: endDate },
  });

  return response.data;
};

/**
 * Get weekly report
 */
export const getWeeklyReport = async (
  year: number,
  week: number,
  format: 'json' | 'pdf' = 'json'
): Promise<WeeklyReport | Blob> => {
  const response = await axios.get(`${API_BASE_URL}/reports/weekly`, {
    params: { year, week, format },
    responseType: format === 'pdf' ? 'blob' : 'json',
  });

  return response.data;
};

/**
 * List weekly reports
 */
export const listWeeklyReports = async (
  year?: number,
  limit: number = 20
): Promise<WeeklyReport[]> => {
  const response = await axios.get(`${API_BASE_URL}/reports/weekly/list`, {
    params: { year, limit },
  });

  return response.data;
};

/**
 * Get monthly report
 */
export const getMonthlyReport = async (
  year: number,
  month: number,
  format: 'json' | 'pdf' = 'json'
): Promise<MonthlyReport | Blob> => {
  const response = await axios.get(`${API_BASE_URL}/reports/monthly`, {
    params: { year, month, format },
    responseType: format === 'pdf' ? 'blob' : 'json',
  });

  return response.data;
};

/**
 * List monthly reports
 */
export const listMonthlyReports = async (
  year?: number
): Promise<MonthlyReport[]> => {
  const response = await axios.get(`${API_BASE_URL}/reports/monthly/list`, {
    params: { year },
  });

  return response.data;
};

/**
 * Get performance summary
 */
export const getPerformanceSummary = async (
  lookbackDays: number = 30
): Promise<PerformanceSummary> => {
  const response = await axios.get(
    `${API_BASE_URL}/reports/analytics/performance-summary`,
    {
      params: { lookback_days: lookbackDays },
    }
  );

  return response.data;
};

/**
 * Get time series data for charting
 */
export const getTimeSeriesData = async (
  metric: string,
  startDate: string,
  endDate: string
): Promise<TimeSeriesData> => {
  const response = await axios.get(
    `${API_BASE_URL}/reports/analytics/time-series`,
    {
      params: {
        metric,
        start_date: startDate,
        end_date: endDate,
      },
    }
  );

  return response.data;
};

/**
 * Export to CSV
 */
export const exportToCSV = async (
  startDate: string,
  endDate: string
): Promise<Blob> => {
  const response = await axios.post(
    `${API_BASE_URL}/reports/export/csv`,
    null,
    {
      params: { start_date: startDate, end_date: endDate },
      responseType: 'blob',
    }
  );

  return response.data;
};

/**
 * Download file helper
 */
export const downloadFile = (blob: Blob, filename: string) => {
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
};

/**
 * Download daily report as PDF
 */
export const downloadDailyReportPDF = async (targetDate?: string) => {
  const blob = await getDailyReport(targetDate, 'pdf') as Blob;
  const filename = `daily_report_${targetDate || 'latest'}.pdf`;
  downloadFile(blob, filename);
};

/**
 * Download CSV export
 */
export const downloadCSV = async (startDate: string, endDate: string) => {
  const blob = await exportToCSV(startDate, endDate);
  const filename = `analytics_${startDate}_${endDate}.csv`;
  downloadFile(blob, filename);
};

// =============================================================================
// React Query Hooks
// =============================================================================

/**
 * Query keys for React Query
 */
export const reportsKeys = {
  all: ['reports'] as const,
  daily: (date?: string) => [...reportsKeys.all, 'daily', date] as const,
  dailySummaries: (startDate: string, endDate: string) =>
    [...reportsKeys.all, 'daily-summaries', startDate, endDate] as const,
  weekly: (year: number, week: number) =>
    [...reportsKeys.all, 'weekly', year, week] as const,
  weeklyList: (year?: number) =>
    [...reportsKeys.all, 'weekly-list', year] as const,
  monthly: (year: number, month: number) =>
    [...reportsKeys.all, 'monthly', year, month] as const,
  monthlyList: (year?: number) =>
    [...reportsKeys.all, 'monthly-list', year] as const,
  performanceSummary: (lookbackDays: number) =>
    [...reportsKeys.all, 'performance-summary', lookbackDays] as const,
  timeSeries: (metric: string, startDate: string, endDate: string) =>
    [...reportsKeys.all, 'time-series', metric, startDate, endDate] as const,
};

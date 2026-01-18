import axios from 'axios';

// Use relative path to go through Nginx reverse proxy
// This avoids CORS issues and works in all environments
const API_BASE_URL = '/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Types
export interface Position {
  ticker: string;
  quantity: number;
  entry_price: number;
  current_price: number;
  market_value: number;
  unrealized_pnl: number;
  unrealized_pnl_pct: number;
}

export interface Trade {
  id: string;
  ticker: string;
  action: 'BUY' | 'SELL';
  quantity: number;
  price: number;
  timestamp: string;
  reason: string;
}

export interface Portfolio {
  total_value: number;
  cash: number;
  positions_value: number;
  daily_pnl: number;
  total_pnl: number;
  daily_return_pct: number;
  total_return_pct: number;
  positions: Position[];
  recent_trades: Trade[];
}

export interface AIDecision {
  ticker: string;
  action: 'BUY' | 'SELL' | 'HOLD';
  conviction: number;
  reasoning: string;
  target_price?: number;
  stop_loss?: number;
  position_size: number;
  risk_factors: string[];
  timestamp?: string;

  // Context-Aware Portfolio Action Fields
  portfolio_action?: 'buy' | 'sell' | 'hold' | 'buy_more' | 'do_not_buy';
  action_reason?: string;
  action_strength?: 'weak' | 'moderate' | 'strong';
  position_adjustment_pct?: number;
}

export interface RiskStatus {
  kill_switch_active: boolean;
  daily_pnl: number;
  daily_return_pct: number;
  max_drawdown_pct: number;
  position_concentration: Record<string, number>;
  alerts: RiskAlert[];
}

export interface RiskAlert {
  id: string;
  level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  title: string;
  message: string;
  timestamp: string;
  acknowledged: boolean;
}

export interface SystemInfo {
  version: string;
  environment: string;
  uptime_seconds: number;
  start_time: string;
  components: Record<string, boolean>;
  config?: Record<string, unknown>;
}

// API Functions
export const getPortfolio = async (): Promise<Portfolio> => {
  const response = await apiClient.get('/portfolio');
  const data = response.data;

  // Map backend response format to frontend interface
  return {
    total_value: data.total_value || 0,
    cash: data.cash || 0,
    positions_value: data.invested || 0, // backend: invested -> frontend: positions_value
    daily_pnl: data.daily_pnl || 0,
    total_pnl: data.total_pnl || 0,
    daily_return_pct: data.daily_return_pct || 0,
    total_return_pct: data.total_pnl_pct || 0, // backend: total_pnl_pct -> frontend: total_return_pct
    positions: (data.positions || []).map((pos: any) => ({
      // Preserve backend field names for compatibility  with DividendDashboard
      symbol: pos.symbol || '',
      ticker: pos.symbol || '', // Also provide ticker for backward compatibility
      quantity: pos.quantity || 0,
      avg_price: pos.avg_price || 0,
      entry_price: pos.avg_price || 0, // Also provide entry_price for backward compatibility
      current_price: pos.current_price || 0,
      market_value: pos.market_value || 0,
      profit_loss: pos.profit_loss || 0,
      unrealized_pnl: pos.profit_loss || 0, // Also provide unrealized_pnl for backward compatibility
      profit_loss_pct: pos.profit_loss_pct || 0,
      unrealized_pnl_pct: pos.profit_loss_pct || 0, // Also provide unrealized_pnl_pct for backward compatibility
      daily_pnl: pos.daily_pnl || 0,
      daily_return_pct: pos.daily_return_pct || 0,
      // Dividend information
      annual_dividend: pos.annual_dividend || 0,
      dividend_yield: pos.dividend_yield || 0,
      dividend_frequency: pos.dividend_frequency || '',
      next_dividend_date: pos.next_dividend_date || '',
    })),
    recent_trades: data.recent_trades || [],
  };
};

export const getDailyPortfolio = async (): Promise<Portfolio> => {
  return getPortfolio();
};

export const analyzeTicker = async (ticker: string): Promise<AIDecision> => {
  const response = await apiClient.post('/analyze', { ticker });
  return response.data;
};

export const analyzeBatch = async (tickers: string[]): Promise<AIDecision[]> => {
  const response = await apiClient.post('/analyze/batch', { tickers });
  return response.data;
};

export const getRiskStatus = async (): Promise<RiskStatus> => {
  const response = await apiClient.get('/risk/status');
  return response.data;
};

export const activateKillSwitch = async (): Promise<{ status: string }> => {
  const response = await apiClient.post('/risk/kill-switch/activate');
  return response.data;
};

export const deactivateKillSwitch = async (): Promise<{ status: string }> => {
  const response = await apiClient.post('/risk/kill-switch/deactivate');
  return response.data;
};

export const getAlerts = async (limit: number = 10): Promise<RiskAlert[]> => {
  const response = await apiClient.get(`/alerts?limit=${limit}`);
  const recent = response.data?.recent;
  return Array.isArray(recent) ? recent : [];
};

export const getSystemInfo = async (): Promise<SystemInfo> => {
  const response = await apiClient.get('/system/info');
  return response.data;
};

export const getLatestBriefing = async (): Promise<{ content: string; date: string }> => {
  const response = await apiClient.get('/briefing/latest');
  return response.data;
};

export const generateBriefing = async (): Promise<void> => {
  await apiClient.post('/briefing/generate');
};

export interface FeedbackData {
  target_type: string;
  target_id: string;
  feedback_type: 'like' | 'dislike';
  comment?: string;
}

export const sendFeedback = async (data: FeedbackData): Promise<{ id: number }> => {
  const response = await apiClient.post('/feedback/', data);
  return response.data;
};

export const getFeedbackList = async (limit: number = 20): Promise<any[]> => {
  const response = await apiClient.get(`/feedback/?limit=${limit}`);
  return response.data;
};

// --- Shadow Trading & GNN API (v2.0) ---

export interface ShadowLog {
  timestamp: string;
  ticker: string;
  intent: { direction: 'BUY' | 'SELL' | 'HOLD'; score: number; rationale: string[] };
  status: 'SHADOW_FILLED' | 'SKIPPED';
  execution?: { action: number; price: number };
}

export interface GNNNode {
  id: string;
  group: string;
  value?: number;
}

export interface GNNLink {
  source: string;
  target: string;
  value: number;
}

export interface GNNGraphData {
  nodes: GNNNode[];
  links: GNNLink[];
}

export const getShadowLogs = async (): Promise<ShadowLog[]> => {
  const response = await apiClient.get('/shadow/logs');
  return response.data;
};

export const getGNNGraph = async (): Promise<GNNGraphData> => {
  const response = await apiClient.get('/shadow/graph');
  return response.data;
};

// --- Real Data API (Phase 8) ---

export interface RealTimeQuote {
  ticker: string;
  price: number;
  change: number;
  change_pct: number;
  volume: number;
  timestamp: string;
}

export interface SectorPerformance {
  name: string;
  ticker: string;
  change_pct: number;
  price: number;
}

export const getRealTimeQuotes = async (tickers: string): Promise<{ success: boolean; data: RealTimeQuote[] }> => {
  const response = await apiClient.get(`/stock-prices/quotes?tickers=${tickers}`);
  return response.data;
};

export const getSectorPerformance = async (): Promise<{ success: boolean; data: SectorPerformance[] }> => {
  const response = await apiClient.get('/stock-prices/sectors/performance');
  return response.data;
};

export const getGlobalMarketMap = async (): Promise<any> => {
  const response = await apiClient.get('/global-macro/market-map');
  return response.data;
};

export const getCountryRisks = async (): Promise<any> => {
  const response = await apiClient.get('/global-macro/country-risks');
  return response.data;
};

export default apiClient;

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
  return response.data;
};

export const getDailyPortfolio = async (): Promise<Portfolio> => {
  const response = await apiClient.get('/portfolio');
  return response.data;
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

export default apiClient;

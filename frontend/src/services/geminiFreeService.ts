/**
 * Gemini Free API Service
 * 
 * 무료 티어: 1,500회/일
 * 비용: $0
 */

import axios from 'axios';

const API_BASE_URL = '/api';

// ============================================================================
// Types
// ============================================================================

export interface ChatMessage {
  role: 'user' | 'model';
  content: string;
}

export interface GeminiRequest {
  message: string;
  history?: ChatMessage[];
  max_tokens?: number;
  temperature?: number;
}

export interface TokenUsage {
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
}

export interface DailyUsage {
  requests_today: number;
  remaining: number;
  total_tokens_today: number;
}

export interface GeminiResponse {
  response: string;
  token_usage: TokenUsage;
  response_time_ms: number;
  request_id: string;
  daily_usage: DailyUsage;
}

export interface UsageStats {
  date: string;
  requests: {
    used: number;
    remaining: number;
    limit: number;
  };
  tokens: {
    input: number;
    output: number;
    total: number;
  };
  last_request: string | null;
  cost: string;
}

export interface NewsAnalysis {
  analysis: {
    sentiment: 'positive' | 'negative' | 'neutral';
    sentiment_score: number;
    key_points: string[];
    risk_factors: string[];
    market_impact: string;
    recommendation: string;
  } | { raw_response: string };
  request_id: string;
  tokens_used: number;
  remaining_requests: number;
  cost: string;
}

// ============================================================================
// API Functions
// ============================================================================

/**
 * Gemini와 대화 (무료)
 */
export const sendGeminiMessage = async (request: GeminiRequest): Promise<GeminiResponse> => {
  const response = await axios.post<GeminiResponse>(
    `${API_BASE_URL}/api/gemini-free/chat`,
    {
      message: request.message,
      history: request.history || [],
      max_tokens: request.max_tokens || 1000,
      temperature: request.temperature || 0.7,
    }
  );
  return response.data;
};

/**
 * 오늘의 사용량 조회
 */
export const getGeminiUsage = async (): Promise<UsageStats> => {
  const response = await axios.get<UsageStats>(`${API_BASE_URL}/api/gemini-free/usage`);
  return response.data;
};

/**
 * 채팅 히스토리 조회
 */
export const getGeminiHistory = async (limit: number = 20) => {
  const response = await axios.get(`${API_BASE_URL}/api/gemini-free/history`, {
    params: { limit }
  });
  return response.data;
};

/**
 * API 상태 확인
 */
export const getGeminiStatus = async () => {
  const response = await axios.get(`${API_BASE_URL}/api/gemini-free/status`);
  return response.data;
};

/**
 * 뉴스 자동 분석 (Trading System용)
 */
export const analyzeNewsWithGemini = async (
  newsContent: string,
  ticker?: string
): Promise<NewsAnalysis> => {
  const response = await axios.post<NewsAnalysis>(
    `${API_BASE_URL}/api/gemini-free/analyze-news`,
    null,
    {
      params: {
        news_content: newsContent,
        ticker: ticker || ''
      }
    }
  );
  return response.data;
};

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * 남은 요청 수 표시
 */
export const formatRemainingRequests = (remaining: number): string => {
  if (remaining > 1000) {
    return `${(remaining / 1000).toFixed(1)}K`;
  }
  return remaining.toString();
};

/**
 * 사용률 퍼센트
 */
export const getUsagePercentage = (used: number, limit: number = 1500): number => {
  return Math.round((used / limit) * 100);
};

/**
 * 사용률에 따른 색상
 */
export const getUsageColor = (percentage: number): string => {
  if (percentage < 50) return 'text-green-600';
  if (percentage < 80) return 'text-yellow-600';
  return 'text-red-600';
};

/**
 * 사용률에 따른 배경색
 */
export const getUsageBgColor = (percentage: number): string => {
  if (percentage < 50) return 'bg-green-500';
  if (percentage < 80) return 'bg-yellow-500';
  return 'bg-red-500';
};

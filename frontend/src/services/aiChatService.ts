/**
 * AI Chat API Service
 * 
 * Features:
 * - Claude/Gemini API 호출
 * - 토큰 사용량 추적
 * - 비용 계산
 * - 히스토리 관리
 */

import axios from 'axios';

const API_BASE_URL = '/api';

// ============================================================================
// Types
// ============================================================================

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface ChatRequest {
  model: 'claude' | 'claude-haiku' | 'claude-sonnet' | 'gemini' | 'gemini-flash' | 'gemini-pro';
  message: string;
  history?: ChatMessage[];
  max_tokens?: number;
  temperature?: number;
  show_raw_request?: boolean;
}

export interface TokenUsage {
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
}

export interface CostEstimate {
  input_cost: number;
  output_cost: number;
  total_cost: number;
  currency: string;
}

export interface ChatResponse {
  response: string;
  model_used: string;
  token_usage: TokenUsage;
  cost_estimate: CostEstimate;
  response_time_ms: number;
  raw_request?: Record<string, unknown>;
  raw_response?: Record<string, unknown>;
  chat_id: string;
}

export interface ChatHistorySummary {
  chat_id: string;
  model: string;
  message_count: number;
  total_tokens: number;
  total_cost: number;
  updated_at: string;
}

export interface ChatHistoryDetail {
  chat_id: string;
  model: string;
  messages: ChatMessage[];
  total_tokens: number;
  total_cost: number;
  created_at: string;
  updated_at: string;
}

export interface ModelPricing {
  input_per_1m: number;
  output_per_1m: number;
  display_name: string;
}

export interface ModelInfo {
  id: string;
  name: string;
  description: string;
  pricing: ModelPricing;
}

export interface AvailableModels {
  claude: ModelInfo[];
  gemini: ModelInfo[];
}

// ============================================================================
// API Functions
// ============================================================================

/**
 * AI와 대화
 */
export const sendChatMessage = async (request: ChatRequest): Promise<ChatResponse> => {
  const response = await axios.post<ChatResponse>(
    `${API_BASE_URL}/api/ai-chat/chat`,
    {
      model: request.model,
      message: request.message,
      history: request.history || [],
      max_tokens: request.max_tokens || 1000,
      temperature: request.temperature || 0.7,
      show_raw_request: request.show_raw_request || false,
    }
  );
  return response.data;
};

/**
 * 채팅 히스토리 목록 조회
 */
export const getChatHistoryList = async (limit: number = 20): Promise<ChatHistorySummary[]> => {
  const response = await axios.get<ChatHistorySummary[]>(
    `${API_BASE_URL}/api/ai-chat/history`,
    { params: { limit } }
  );
  return response.data;
};

/**
 * 특정 채팅 히스토리 조회
 */
export const getChatHistoryDetail = async (chatId: string): Promise<ChatHistoryDetail> => {
  const response = await axios.get<ChatHistoryDetail>(
    `${API_BASE_URL}/api/ai-chat/history/${chatId}`
  );
  return response.data;
};

/**
 * 모델별 가격표 조회
 */
export const getModelPricing = async (): Promise<Record<string, ModelPricing>> => {
  const response = await axios.get<Record<string, ModelPricing>>(
    `${API_BASE_URL}/api/ai-chat/pricing`
  );
  return response.data;
};

/**
 * 사용 가능한 모델 목록
 */
export const getAvailableModels = async (): Promise<AvailableModels> => {
  const response = await axios.get<AvailableModels>(
    `${API_BASE_URL}/api/ai-chat/models`
  );
  return response.data;
};

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * 비용을 읽기 좋은 형식으로 변환
 */
export const formatCost = (cost: number): string => {
  if (cost === 0) return '$0.00';
  if (cost < 0.000001) return '< $0.000001';
  if (cost < 0.01) return `$${cost.toFixed(6)}`;
  return `$${cost.toFixed(4)}`;
};

/**
 * 토큰 수를 읽기 좋은 형식으로 변환
 */
export const formatTokens = (tokens: number): string => {
  if (tokens < 1000) return tokens.toString();
  if (tokens < 1000000) return `${(tokens / 1000).toFixed(1)}K`;
  return `${(tokens / 1000000).toFixed(2)}M`;
};

/**
 * 응답 시간을 읽기 좋은 형식으로 변환
 */
export const formatResponseTime = (ms: number): string => {
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(2)}s`;
};

/**
 * 누적 세션 통계 계산
 */
export const calculateSessionStats = (
  messages: ChatMessage[],
  responses: ChatResponse[]
) => {
  let totalInputTokens = 0;
  let totalOutputTokens = 0;
  let totalCost = 0;
  let totalResponseTime = 0;

  for (const response of responses) {
    totalInputTokens += response.token_usage.input_tokens;
    totalOutputTokens += response.token_usage.output_tokens;
    totalCost += response.cost_estimate.total_cost;
    totalResponseTime += response.response_time_ms;
  }

  return {
    messageCount: messages.length,
    totalInputTokens,
    totalOutputTokens,
    totalTokens: totalInputTokens + totalOutputTokens,
    totalCost,
    averageResponseTime: responses.length > 0 ? totalResponseTime / responses.length : 0,
  };
};

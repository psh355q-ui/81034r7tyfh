/**
 * AI Review API Service
 *
 * Backend API 연동을 위한 서비스 레이어
 */

import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// ============================================================================
// Types
// ============================================================================

export interface AIReviewSummary {
  analysis_id: string;
  ticker: string;
  timestamp: string;
  action: 'BUY' | 'SELL' | 'HOLD';
  conviction: number;
  reasoning_preview: string;
  has_changes: boolean;
  model_name: string;
}

export interface AIReviewListResponse {
  total_count: number;
  today_count: number;
  avg_conviction: number;
  changed_count: number;
  reviews: AIReviewSummary[];
}

export interface AnalysisResult {
  action: 'BUY' | 'SELL' | 'HOLD';
  conviction: number;
  reasoning: string;
  target_price?: number;
  stop_loss?: number;
  position_size: number;
  risk_factors: string[];
}

export interface DetailedReasoning {
  technical_analysis: string;
  fundamental_analysis: string;
  sentiment_analysis: string;
  risk_assessment: string;
}

export interface ModelInfo {
  model_name: string;
  tokens_used: number;
  response_time_ms: number;
  cost_usd?: number;
}

export interface DiffFromPrevious {
  has_changes: boolean;
  conviction_change: number;
  action_changed: boolean;
  reasoning_diff: string;
}

export interface AIReviewDetail {
  analysis_id: string;
  ticker: string;
  timestamp: string;
  analysis: AnalysisResult;
  detailed_reasoning: DetailedReasoning;
  model_info: ModelInfo;
  diff_from_previous?: DiffFromPrevious;
}

export interface TradingTerm {
  term: string;
  term_kr: string;
  definition: string;
  example: string;
  category: string;
  related_terms: string[];
}

export interface TradingTermsResponse {
  terms: TradingTerm[];
  categories: string[];
  total_count: number;
}

export interface AIReviewStatistics {
  total: number;
  by_action: Record<string, number>;
  by_ticker: Record<string, number>;
  avg_conviction: number;
  changed_rate: number;
}

// ============================================================================
// AI Review API Functions
// ============================================================================

/**
 * Get list of AI reviews with summary statistics
 */
export async function getAIReviews(params?: {
  limit?: number;
  offset?: number;
}): Promise<AIReviewListResponse> {
  const response = await api.get('/ai-reviews', { params });
  return response.data;
}

/**
 * Get detailed AI review by ID
 */
export async function getAIReviewDetail(analysisId: string): Promise<AIReviewDetail> {
  const response = await api.get(`/api/ai-reviews/${analysisId}`);
  return response.data;
}

/**
 * Get analysis history for a specific ticker
 */
export async function getTickerHistory(
  ticker: string,
  limit: number = 10
): Promise<{ ticker: string; count: number; history: AIReviewDetail[] }> {
  const response = await api.get(`/api/ai-reviews/ticker/${ticker}/history`, {
    params: { limit },
  });
  return response.data;
}

/**
 * Get latest analysis for a specific ticker
 */
export async function getLatestForTicker(ticker: string): Promise<AIReviewDetail> {
  const response = await api.get(`/api/ai-reviews/ticker/${ticker}/latest`);
  return response.data;
}

/**
 * Search AI reviews with filters
 */
export async function searchAIReviews(params: {
  ticker?: string;
  action?: string;
  min_conviction?: number;
  has_changes_only?: boolean;
  days_back?: number;
  limit?: number;
}): Promise<{ count: number; reviews: AIReviewSummary[] }> {
  const response = await api.get('/ai-reviews/search', { params });
  return response.data;
}

/**
 * Get AI review statistics
 */
export async function getAIReviewStatistics(): Promise<AIReviewStatistics> {
  const response = await api.get('/ai-reviews/statistics');
  return response.data;
}

/**
 * Create a new AI review record
 */
export async function createAIReview(data: {
  ticker: string;
  analysis: AnalysisResult;
  detailed_reasoning: DetailedReasoning;
  model_info: ModelInfo;
}): Promise<{ success: boolean; analysis_id: string; message: string }> {
  const response = await api.post('/ai-reviews', data);
  return response.data;
}

/**
 * Delete an AI review record
 */
export async function deleteAIReview(
  analysisId: string
): Promise<{ success: boolean; message: string }> {
  const response = await api.delete(`/api/ai-reviews/${analysisId}`);
  return response.data;
}

// ============================================================================
// Trading Terms API Functions
// ============================================================================

/**
 * Get all trading terms
 */
export async function getTradingTerms(): Promise<TradingTermsResponse> {
  const response = await api.get('/ai-reviews/terms/all');
  return response.data;
}

/**
 * Search trading terms
 */
export async function searchTradingTerms(
  query: string,
  category?: string
): Promise<{ query: string; category?: string; count: number; terms: TradingTerm[] }> {
  const response = await api.get('/ai-reviews/terms/search', {
    params: { query, category },
  });
  return response.data;
}

/**
 * Get all term categories
 */
export async function getTermCategories(): Promise<{
  categories: string[];
  count: number;
}> {
  const response = await api.get('/ai-reviews/terms/categories');
  return response.data;
}

// ============================================================================
// Export Default API Instance
// ============================================================================

export default api;

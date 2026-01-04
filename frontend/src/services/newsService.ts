/**
 * News Aggregation API Service
 * 
 * Features:
 * - RSS 크롤링 트리거
 * - 뉴스 조회 (필터링)
 * - AI 분석 조회
 * - 티커별 뉴스
 */

import axios from 'axios';

const API_BASE_URL = '/api';

// ============================================================================
// Types
// ============================================================================

export interface NewsArticle {
  id: number;
  url: string;
  title: string;
  source: string;
  feed_source: string;
  published_at: string | null;
  content_summary: string | null;
  keywords: string[];
  crawled_at: string;
  has_analysis: boolean;
  sentiment?: string | null;
  urgency?: string | null;
  actionable?: boolean;
  related_tickers?: string[];
}

export interface NewsAnalysis {
  sentiment_overall: 'positive' | 'negative' | 'neutral' | 'mixed';
  sentiment_score: number;
  sentiment_confidence: number;
  urgency: 'low' | 'medium' | 'high' | 'critical';
  market_impact_short: 'bullish' | 'bearish' | 'neutral' | 'uncertain';
  market_impact_long: 'bullish' | 'bearish' | 'neutral' | 'uncertain';
  impact_magnitude: number;
  affected_sectors: string[];
  key_facts: string[];
  key_warnings: string[];
  trading_actionable: boolean;
  risk_category: string;
  recommendation: string;
  red_flags: string[];
  analyzed_at: string;
  tokens_used: number;
}

export interface NewsDetail {
  id: number;
  url: string;
  title: string;
  source: string;
  published_at: string | null;
  content_text: string | null;
  content_summary: string | null;
  keywords: string[];
  authors: string[];
  analysis: NewsAnalysis | null;
  related_tickers: {
    ticker: string;
    relevance: number;
    sentiment: number;
  }[];
}

export interface CrawlResult {
  total_articles: number;
  feeds_processed: number;
  articles_new: number;
  articles_skipped: number;
  content_extracted: number;
  errors: { feed: string; error: string }[];
  timestamp: string;
}

export interface AnalyzeResult {
  analyzed: number;
  skipped: number;
  errors: number;
  remaining_requests: number;
  details: {
    title: string;
    sentiment?: string;
    score?: number;
    actionable?: boolean;
    error?: string;
  }[];
}

export interface NewsStats {
  total_articles: number;
  analyzed_articles: number;
  unanalyzed_articles: number;
  sentiment_distribution: {
    positive: number;
    negative: number;
    neutral: number;
    mixed: number;
  };
  actionable_count: number;
  gemini_usage: {
    date: string;
    requests_used: number;
    requests_remaining: number;
    total_tokens: number;
    cost: string;
  };
}

export interface RSSFeed {
  id: number;
  name: string;
  url: string;
  category: string;
  enabled: boolean;
  last_fetched: string | null;
  total_articles: number;
  error_count: number;
}

export interface TickerNews {
  article_id: number;
  title: string;
  source: string;
  published_at: string | null;
  relevance: number;
  sentiment: number;
  analysis: {
    overall_sentiment: string;
    impact: string;
    actionable: boolean;
  } | null;
}

// ============================================================================
// API Functions
// ============================================================================

/**
 * RSS 피드 크롤링 트리거
 */
export const crawlRSSFeeds = async (extractContent: boolean = true): Promise<CrawlResult> => {
  const response = await axios.post<CrawlResult>(
    `${API_BASE_URL}/news/crawl`,
    null,
    { params: { extract_content: extractContent } }
  );
  return response.data;
};

/**
 * 특정 티커 뉴스 크롤링
 */
export const crawlTickerNews = async (ticker: string) => {
  const response = await axios.post(`${API_BASE_URL}/news/crawl/ticker/${ticker}`);
  return response.data;
};

/**
 * 미분석 기사 AI 분석
 */
export const analyzeUnanalyzedArticles = async (maxCount: number = 10): Promise<AnalyzeResult> => {
  const response = await axios.post<AnalyzeResult>(
    `${API_BASE_URL}/news/analyze`,
    null,
    { params: { max_count: maxCount } }
  );
  return response.data;
};

/**
 * 단일 기사 분석
 */
export const analyzeSingleArticle = async (articleId: number) => {
  const response = await axios.post(`${API_BASE_URL}/news/analyze/${articleId}`);
  return response.data;
};

/**
 * 뉴스 기사 목록 조회
 */
export const getNewsArticles = async (params: {
  limit?: number;
  hours?: number;
  source?: string;
  sentiment?: 'positive' | 'negative' | 'neutral' | 'mixed';
  actionable_only?: boolean;
}): Promise<NewsArticle[]> => {
  const response = await axios.get<NewsArticle[]>(
    `${API_BASE_URL}/news/articles`,
    { params }
  );
  return response.data;
};

/**
 * 뉴스 상세 조회 (분석 포함)
 */
export const getNewsDetail = async (articleId: number): Promise<NewsDetail> => {
  const response = await axios.get<NewsDetail>(
    `${API_BASE_URL}/news/articles/${articleId}`
  );
  return response.data;
};

/**
 * 티커별 뉴스 조회
 */
export const getTickerNews = async (ticker: string, limit: number = 20): Promise<{
  ticker: string;
  count: number;
  articles: TickerNews[];
}> => {
  const response = await axios.get(
    `${API_BASE_URL}/news/ticker/${ticker}`,
    { params: { limit } }
  );
  return response.data;
};

/**
 * 높은 영향도 뉴스 조회
 */
export const getHighImpactNews = async (minMagnitude: number = 0.6) => {
  const response = await axios.get(`${API_BASE_URL}/news/high-impact`, {
    params: { min_magnitude: minMagnitude }
  });
  return response.data;
};

/**
 * 경고 뉴스 조회
 */
export const getWarningNews = async () => {
  const response = await axios.get(`${API_BASE_URL}/news/warnings`);
  return response.data;
};

/**
 * 뉴스 통계 조회
 */
export const getNewsStats = async (): Promise<NewsStats> => {
  const response = await axios.get<NewsStats>(`${API_BASE_URL}/news/stats`);
  return response.data;
};

/**
 * RSS 피드 목록 조회
 */
export const getRSSFeeds = async (): Promise<RSSFeed[]> => {
  const response = await axios.get<RSSFeed[]>(`${API_BASE_URL}/news/feeds`);
  return response.data;
};

/**
 * RSS 피드 추가
 */
export const addRSSFeed = async (name: string, url: string, category: string = 'global') => {
  const response = await axios.post(`${API_BASE_URL}/news/feeds`, null, {
    params: { name, url, category }
  });
  return response.data;
};

/**
 * RSS 피드 토글
 */
export const toggleRSSFeed = async (feedId: number) => {
  const response = await axios.put(`${API_BASE_URL}/news/feeds/${feedId}/toggle`);
  return response.data;
};

/**
 * Gemini Real-Time Search (Premium Feature)
 */
export const searchTickerRealtime = async (ticker: string, maxArticles: number = 5) => {
  const response = await axios.get(`${API_BASE_URL}/news/gemini/search/ticker/${ticker}`, {
    params: { max_articles: maxArticles }
  });
  return response.data;
};

export const searchNewsRealtime = async (query: string, maxArticles: number = 5) => {
  const response = await axios.get(`${API_BASE_URL}/news/gemini/search`, {
    params: { query, max_articles: maxArticles }
  });
  return response.data;
};

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * 감정 점수를 색상으로 변환
 */
export const getSentimentColor = (sentiment: string): string => {
  switch (sentiment) {
    case 'positive':
      return 'text-green-600';
    case 'negative':
      return 'text-red-600';
    case 'neutral':
      return 'text-gray-600';
    case 'mixed':
      return 'text-yellow-600';
    default:
      return 'text-gray-600';
  }
};

/**
 * 감정 점수를 배경색으로 변환
 */
export const getSentimentBgColor = (sentiment: string): string => {
  switch (sentiment) {
    case 'positive':
      return 'bg-green-100';
    case 'negative':
      return 'bg-red-100';
    case 'neutral':
      return 'bg-gray-100';
    case 'mixed':
      return 'bg-yellow-100';
    default:
      return 'bg-gray-100';
  }
};

/**
 * 긴급도를 색상으로 변환
 */
export const getUrgencyColor = (urgency: string): string => {
  switch (urgency) {
    case 'critical':
      return 'text-red-700 bg-red-100';
    case 'high':
      return 'text-orange-700 bg-orange-100';
    case 'medium':
      return 'text-yellow-700 bg-yellow-100';
    case 'low':
      return 'text-green-700 bg-green-100';
    default:
      return 'text-gray-700 bg-gray-100';
  }
};

/**
 * 영향도를 퍼센트로 변환
 */
export const formatMagnitude = (magnitude: number): string => {
  return `${Math.round(magnitude * 100)}%`;
};

/**
 * 시간 차이 계산
 */
export const getTimeAgo = (dateString: string): string => {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffMins < 60) {
    return `${diffMins}분 전`;
  } else if (diffHours < 24) {
    return `${diffHours}시간 전`;
  } else {
    return `${diffDays}일 전`;
  }
};

/**
 * 정확한 날짜/시간 포맷팅
 * 예: "2026-01-02 11:30"
 */
export const formatDateTime = (dateString: string): string => {
  const date = new Date(dateString);
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');

  return `${year}-${month}-${day} ${hours}:${minutes}`;
};

/**
 * 한국어 날짜 포맷팅
 * 예: "2026년 1월 2일 오전 11:30"
 */
export const formatDateTimeKorean = (dateString: string): string => {
  const date = new Date(dateString);
  const year = date.getFullYear();
  const month = date.getMonth() + 1;
  const day = date.getDate();
  const hours = date.getHours();
  const minutes = String(date.getMinutes()).padStart(2, '0');
  const ampm = hours < 12 ? '오전' : '오후';
  const displayHours = hours % 12 || 12;

  return `${year}년 ${month}월 ${day}일 ${ampm} ${displayHours}:${minutes}`;
};

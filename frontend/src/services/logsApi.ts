/**
 * Logs API Service
 * 로그 조회 API 서비스
 */

import axios from 'axios';

const API_BASE_URL = '/api/logs';

export interface LogEntry {
  timestamp: string;
  level: string;
  category: string;
  message: string;
  details?: Record<string, any>;
  user?: string;
  request_id?: string;
}

export interface LogsResponse {
  total_count: number;
  logs: LogEntry[];
  limit: number;
  offset: number;
}

export interface LogStatistics {
  total_logs: number;
  by_level: Record<string, number>;
  by_category: Record<string, number>;
  errors_count: number;
  warnings_count: number;
}

export interface LogFilters {
  limit?: number;
  offset?: number;
  level?: string;
  category?: string;
  days?: number;
  search?: string;
}

/**
 * 로그 목록 조회
 */
export const getLogs = async (filters: LogFilters = {}): Promise<LogsResponse> => {
  const params = new URLSearchParams();

  if (filters.limit) params.append('limit', filters.limit.toString());
  if (filters.offset) params.append('offset', filters.offset.toString());
  if (filters.level) params.append('level', filters.level);
  if (filters.category) params.append('category', filters.category);
  if (filters.days) params.append('days', filters.days.toString());
  if (filters.search) params.append('search', filters.search);

  const response = await axios.get<LogsResponse>(`${API_BASE_URL}?${params.toString()}`);
  return response.data;
};

/**
 * 로그 통계 조회
 */
export const getLogStatistics = async (days: number = 7): Promise<LogStatistics> => {
  const response = await axios.get<LogStatistics>(`${API_BASE_URL}/statistics?days=${days}`);
  return response.data;
};

/**
 * 사용 가능한 로그 레벨 목록
 */
export const getLogLevels = async (): Promise<string[]> => {
  const response = await axios.get<{ levels: string[] }>(`${API_BASE_URL}/levels`);
  return response.data.levels;
};

/**
 * 사용 가능한 로그 카테고리 목록
 */
export const getLogCategories = async (): Promise<string[]> => {
  const response = await axios.get<{ categories: string[] }>(`${API_BASE_URL}/categories`);
  return response.data.categories;
};

/**
 * 오래된 로그 파일 삭제
 */
export const cleanupOldLogs = async (days: number = 30): Promise<{ deleted_count: number; message: string }> => {
  const response = await axios.post<{ deleted_count: number; message: string }>(
    `${API_BASE_URL}/cleanup?days=${days}`
  );
  return response.data;
};

/**
 * React Query Hook for Position Ownerships
 *
 * Phase 5, T5.4: Position Ownership Table
 */

import { useQuery } from '@tanstack/react-query';
import type { OwnershipListResponse } from '../types/strategy';

const API_BASE = 'http://localhost:8001/api';

interface FetchOwnershipsParams {
  page?: number;
  pageSize?: number;
  ticker?: string;
  strategyId?: string;
}

/**
 * Fetch position ownerships with pagination
 */
async function fetchOwnerships({
  page = 1,
  pageSize = 20,
  ticker,
  strategyId
}: FetchOwnershipsParams): Promise<OwnershipListResponse> {
  const params = new URLSearchParams();
  params.append('page', page.toString());
  params.append('page_size', pageSize.toString());

  if (ticker) {
    params.append('ticker', ticker);
  }

  if (strategyId) {
    params.append('strategy_id', strategyId);
  }

  const response = await fetch(`${API_BASE}/ownership?${params}`);

  if (!response.ok) {
    throw new Error('Failed to fetch ownerships');
  }

  return response.json();
}

/**
 * Hook to fetch position ownerships with React Query
 */
export function useOwnerships(params: FetchOwnershipsParams = {}) {
  return useQuery({
    queryKey: ['ownerships', params],
    queryFn: () => fetchOwnerships(params),
    refetchInterval: 30000, // Refetch every 30 seconds
    staleTime: 10000 // Data is fresh for 10 seconds
  });
}

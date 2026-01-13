/**
 * React Query Hook for Strategies
 *
 * Phase 5, T5.3: Strategy Dashboard UI
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type { Strategy } from '../types/strategy';

const API_BASE = 'http://localhost:8001/api';

/**
 * Fetch all strategies
 */
async function fetchStrategies(activeOnly: boolean = false): Promise<Strategy[]> {
  const params = new URLSearchParams();
  if (activeOnly) {
    params.append('active_only', 'true');
  }

  const response = await fetch(`${API_BASE}/strategies?${params}`);
  if (!response.ok) {
    throw new Error('Failed to fetch strategies');
  }

  return response.json();
}

/**
 * Activate a strategy
 */
async function activateStrategy(strategyId: string): Promise<Strategy> {
  const response = await fetch(`${API_BASE}/strategies/${strategyId}/activate`, {
    method: 'POST'
  });

  if (!response.ok) {
    throw new Error('Failed to activate strategy');
  }

  return response.json();
}

/**
 * Deactivate a strategy
 */
async function deactivateStrategy(strategyId: string): Promise<Strategy> {
  const response = await fetch(`${API_BASE}/strategies/${strategyId}/deactivate`, {
    method: 'POST'
  });

  if (!response.ok) {
    throw new Error('Failed to deactivate strategy');
  }

  return response.json();
}

/**
 * Hook to fetch strategies with React Query
 */
export function useStrategies(activeOnly: boolean = false) {
  return useQuery({
    queryKey: ['strategies', activeOnly],
    queryFn: () => fetchStrategies(activeOnly),
    refetchInterval: 30000, // Refetch every 30 seconds
    staleTime: 10000 // Data is fresh for 10 seconds
  });
}

/**
 * Hook to toggle strategy activation
 */
export function useToggleStrategy() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ strategyId, activate }: { strategyId: string; activate: boolean }) => {
      return activate
        ? activateStrategy(strategyId)
        : deactivateStrategy(strategyId);
    },
    onSuccess: () => {
      // Invalidate strategies query to refetch
      queryClient.invalidateQueries({ queryKey: ['strategies'] });
    }
  });
}

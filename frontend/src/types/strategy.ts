/**
 * Multi-Strategy Orchestration Types
 *
 * Phase 5, T5.3: Strategy Dashboard UI
 *
 * Type definitions for Strategy and Ownership entities
 */

export type PersonaType = 'trading' | 'long_term' | 'dividend' | 'aggressive';

export type TimeHorizon = 'short' | 'medium' | 'long';

export type OwnershipType = 'primary' | 'shared';

export interface Strategy {
  id: string;
  name: string;
  display_name: string;
  persona_type: PersonaType;
  priority: number;
  time_horizon: TimeHorizon;
  is_active: boolean;
  config_metadata: Record<string, any> | null;
  created_at: string;
  updated_at: string;
}

export interface PositionOwnership {
  id: string;
  ticker: string;
  strategy_id: string;
  position_id: string | null;
  ownership_type: OwnershipType;
  locked_until: string | null;
  reasoning: string | null;
  created_at: string;
  strategy?: Strategy;
}

export interface OwnershipListResponse {
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  items: PositionOwnership[];
}

// Persona Icon Mapping
export const PERSONA_ICONS: Record<PersonaType, string> = {
  long_term: '📈',
  dividend: '💰',
  trading: '⚡',
  aggressive: '🔥'
};

// Persona Display Names
export const PERSONA_NAMES: Record<PersonaType, string> = {
  long_term: '장기 투자',
  dividend: '배당 투자',
  trading: '단기 트레이딩',
  aggressive: '공격적 투자'
};

// Time Horizon Display Names
export const TIME_HORIZON_NAMES: Record<TimeHorizon, string> = {
  short: '단기',
  medium: '중기',
  long: '장기'
};

// Priority Color Mapping
export function getPriorityColor(priority: number): string {
  if (priority > 80) return 'text-green-600 bg-green-50';
  if (priority >= 50) return 'text-yellow-600 bg-yellow-50';
  return 'text-orange-600 bg-orange-50';
}

// Strategy Color Mapping (for badges)
export const STRATEGY_COLORS: Record<PersonaType, string> = {
  long_term: 'bg-blue-100 text-blue-800',
  dividend: 'bg-purple-100 text-purple-800',
  trading: 'bg-amber-100 text-amber-800',
  aggressive: 'bg-red-100 text-red-800'
};

// Conflict Types (Phase 5, T5.5)
export interface OrderConflict {
  id: string;
  ticker: string;
  strategy_id: string;
  conflicting_strategy_id: string;
  conflict_type: 'position_conflict' | 'priority_conflict' | 'ownership_locked';
  resolution: 'blocked' | 'override' | 'pending';
  reason: string;
  created_at: string;
  strategy?: Strategy;
  conflicting_strategy?: Strategy;
}

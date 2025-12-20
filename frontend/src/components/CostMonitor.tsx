/**
 * Real-time Cost Monitor Widget
 *
 * Compact widget for displaying current cost status in sidebar/header
 */

import React, { useState, useEffect } from 'react';

interface BudgetStatus {
  status: 'OK' | 'WARNING' | 'CRITICAL';
  daily: {
    cost: number;
    limit: number;
    percentage: number;
  };
  monthly: {
    cost: number;
    limit: number;
    percentage: number;
  };
}

const CostMonitor: React.FC = () => {
  const [budget, setBudget] = useState<BudgetStatus | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchBudgetStatus = async () => {
    try {
      const response = await fetch('/api/cost/budget/check');
      if (response.ok) {
        const data = await response.json();
        setBudget(data);
      }
    } catch (error) {
      console.error('Failed to fetch budget status:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBudgetStatus();
    const interval = setInterval(fetchBudgetStatus, 30000); // 30 seconds
    return () => clearInterval(interval);
  }, []);

  if (loading || !budget) {
    return (
      <div className="text-sm text-gray-500">
        Loading cost...
      </div>
    );
  }

  const statusColor =
    budget.status === 'OK'
      ? 'text-green-600'
      : budget.status === 'WARNING'
      ? 'text-yellow-600'
      : 'text-red-600';

  const statusBg =
    budget.status === 'OK'
      ? 'bg-green-100'
      : budget.status === 'WARNING'
      ? 'bg-yellow-100'
      : 'bg-red-100';

  const statusIcon =
    budget.status === 'OK'
      ? '✓'
      : budget.status === 'WARNING'
      ? '⚠'
      : '✗';

  return (
    <div className={`rounded-lg p-3 ${statusBg}`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <span className={`text-lg font-semibold ${statusColor}`}>
            {statusIcon}
          </span>
          <span className="text-sm font-medium text-gray-700">Cost Monitor</span>
        </div>
        <span className={`text-xs font-semibold ${statusColor}`}>
          {budget.status}
        </span>
      </div>

      <div className="mt-2 space-y-1">
        {/* Daily */}
        <div className="flex items-center justify-between text-xs">
          <span className="text-gray-600">Today:</span>
          <span className={`font-semibold ${statusColor}`}>
            ${budget.daily.cost.toFixed(4)} / ${budget.daily.limit.toFixed(2)}
          </span>
        </div>

        {/* Daily Progress Bar */}
        <div className="w-full bg-gray-300 rounded-full h-1.5">
          <div
            className={`h-1.5 rounded-full transition-all ${
              budget.status === 'OK'
                ? 'bg-green-600'
                : budget.status === 'WARNING'
                ? 'bg-yellow-600'
                : 'bg-red-600'
            }`}
            style={{
              width: `${Math.min(budget.daily.percentage, 100)}%`,
            }}
          />
        </div>

        {/* Monthly */}
        <div className="flex items-center justify-between text-xs">
          <span className="text-gray-600">This Month:</span>
          <span className={`font-semibold ${statusColor}`}>
            ${budget.monthly.cost.toFixed(2)} / ${budget.monthly.limit.toFixed(2)}
          </span>
        </div>

        {/* Monthly Progress Bar */}
        <div className="w-full bg-gray-300 rounded-full h-1.5">
          <div
            className={`h-1.5 rounded-full transition-all ${
              budget.status === 'OK'
                ? 'bg-green-600'
                : budget.status === 'WARNING'
                ? 'bg-yellow-600'
                : 'bg-red-600'
            }`}
            style={{
              width: `${Math.min(budget.monthly.percentage, 100)}%`,
            }}
          />
        </div>
      </div>

      <div className="mt-2 text-xs text-gray-500 text-center">
        Updated every 30s
      </div>
    </div>
  );
};

export default CostMonitor;

/**
 * Advanced Analytics Page - Advanced performance, risk, and trade analytics
 *
 * Features:
 * - Performance Attribution (Strategy, Sector, AI Source, Position, Time)
 * - Risk Analytics (VaR, Drawdown, Concentration, Correlation, Stress Testing)
 * - Trade Analytics (Win/Loss Patterns, Execution Quality, Hold Duration, Confidence Impact)
 *
 * @author AI Trading System Team
 * @date 2025-11-26
 */

import React, { useState } from 'react';
import dayjs from 'dayjs';
import {
  TrendingUp,
  AlertTriangle,
  BarChart3,
  Activity,
  PieChart,
  Clock,
} from 'lucide-react';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import PerformanceAttribution from '../components/Analytics/PerformanceAttribution';
import RiskAnalytics from '../components/Analytics/RiskAnalytics';
import TradeAnalytics from '../components/Analytics/TradeAnalytics';

type TabType = 'performance' | 'risk' | 'trade';

const AdvancedAnalytics: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabType>('performance');
  const [startDate, setStartDate] = useState<string>(
    dayjs().subtract(30, 'day').format('YYYY-MM-DD')
  );
  const [endDate, setEndDate] = useState<string>(dayjs().format('YYYY-MM-DD'));

  const tabs = [
    { id: 'performance' as TabType, label: 'Performance Attribution', icon: TrendingUp },
    { id: 'risk' as TabType, label: 'Risk Analytics', icon: AlertTriangle },
    { id: 'trade' as TabType, label: 'Trade Analytics', icon: BarChart3 },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Advanced Analytics</h1>
          <p className="mt-1 text-sm text-gray-500">
            Deep dive into performance attribution, risk metrics, and trade patterns
          </p>
        </div>
      </div>

      {/* Date Range Selector */}
      <Card>
        <div className="flex flex-wrap items-end gap-4">
          <div className="flex-1 min-w-[200px]">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Start Date
            </label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <div className="flex-1 min-w-[200px]">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              End Date
            </label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <div className="flex gap-2">
            <Button
              variant="secondary"
              onClick={() => {
                setStartDate(dayjs().subtract(7, 'day').format('YYYY-MM-DD'));
                setEndDate(dayjs().format('YYYY-MM-DD'));
              }}
            >
              Last 7 Days
            </Button>
            <Button
              variant="secondary"
              onClick={() => {
                setStartDate(dayjs().subtract(30, 'day').format('YYYY-MM-DD'));
                setEndDate(dayjs().format('YYYY-MM-DD'));
              }}
            >
              Last 30 Days
            </Button>
            <Button
              variant="secondary"
              onClick={() => {
                setStartDate(dayjs().subtract(90, 'day').format('YYYY-MM-DD'));
                setEndDate(dayjs().format('YYYY-MM-DD'));
              }}
            >
              Last 90 Days
            </Button>
          </div>
        </div>
      </Card>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8" aria-label="Tabs">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`
                  group inline-flex items-center py-4 px-1 border-b-2 font-medium text-sm
                  ${isActive
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }
                `}
              >
                <Icon
                  className={`
                    -ml-0.5 mr-2 h-5 w-5
                    ${isActive ? 'text-blue-500' : 'text-gray-400 group-hover:text-gray-500'}
                  `}
                />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="mt-6">
        {activeTab === 'performance' && (
          <PerformanceAttribution startDate={startDate} endDate={endDate} />
        )}
        {activeTab === 'risk' && <RiskAnalytics startDate={startDate} endDate={endDate} />}
        {activeTab === 'trade' && <TradeAnalytics startDate={startDate} endDate={endDate} />}
      </div>
    </div>
  );
};

export default AdvancedAnalytics;

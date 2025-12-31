/**
 * Multi-Asset Dashboard
 *
 * Phase 30: Multi-Asset Support
 * Date: 2025-12-30
 *
 * 📊 Data Sources:
 *   - API: GET /api/assets - List of all assets with filtering
 *   - API: GET /api/assets/stats/overview - Asset statistics
 *   - API: GET /api/assets/risk/distribution - Risk distribution
 *
 * 🔗 Dependencies:
 *   - react: useState
 *   - @tanstack/react-query: useQuery
 *   - recharts: BarChart, PieChart
 *   - lucide-react: Icons
 *
 * 📤 Features:
 *   - 27 assets across 6 asset classes
 *   - Asset class filtering (STOCK, BOND, CRYPTO, COMMODITY, ETF, REIT)
 *   - Risk level visualization
 *   - S&P500 correlation display
 *   - 60-second auto-refresh
 *
 * 🔄 Used By:
 *   - App.tsx (route: /multi-asset)
 */

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card } from '../components/common/Card';
import { Badge } from '../components/common/Badge';
import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import {
  Coins,
  TrendingUp,
  Shield,
  AlertTriangle,
  DollarSign,
  Activity
} from 'lucide-react';

// ============================================================================
// Types
// ============================================================================

/** Asset model from API */
interface Asset {
  id: number;
  symbol: string;
  asset_class: string;
  name: string;
  exchange: string;
  currency: string;
  sector: string | null;
  bond_type: string | null;
  crypto_type: string | null;
  commodity_type: string | null;
  risk_level: string;
  correlation_to_sp500: number | null;
  is_active: boolean;
  created_at: string;
}

/** Asset statistics from API */
interface AssetStats {
  total_assets: number;
  by_asset_class: Record<string, number>;
  by_risk_level: Record<string, number>;
  avg_correlation_to_sp500: Record<string, number>;
}

/** Risk distribution from API */
interface RiskDistribution {
  risk_levels: string[];
  distribution: Record<string, {
    count: number;
    assets: Array<{
      symbol: string;
      name: string;
      asset_class: string;
      correlation_to_sp500: number | null;
    }>;
  }>;
}

// ============================================================================
// API Functions
// ============================================================================

/** Fetch assets with optional filtering */
const fetchAssets = async (assetClass?: string): Promise<{ assets: Asset[] }> => {
  const params = new URLSearchParams();
  if (assetClass) params.append('asset_class', assetClass);

  const response = await fetch(`/api/assets?${params.toString()}`);
  if (!response.ok) throw new Error('Failed to fetch assets');
  return response.json();
};

/** Fetch asset statistics */
const fetchAssetStats = async (): Promise<AssetStats> => {
  const response = await fetch('/api/assets/stats/overview');
  if (!response.ok) throw new Error('Failed to fetch asset stats');
  return response.json();
};

/** Fetch risk distribution */
const fetchRiskDistribution = async (): Promise<RiskDistribution> => {
  const response = await fetch('/api/assets/risk/distribution');
  if (!response.ok) throw new Error('Failed to fetch risk distribution');
  return response.json();
};

// ============================================================================
// Component
// ============================================================================

export const MultiAssetDashboard: React.FC = () => {
  // ========================================================================
  // State Management
  // ========================================================================

  /** Selected asset class filter */
  const [selectedClass, setSelectedClass] = useState<string | undefined>(undefined);

  // ========================================================================
  // Data Fetching
  // ========================================================================

  /** Fetch assets with 60-second refresh */
  const { data: assetsData } = useQuery({
    queryKey: ['assets', selectedClass],
    queryFn: () => fetchAssets(selectedClass),
    refetchInterval: 60000
  });

  /** Fetch statistics with 60-second refresh */
  const { data: stats } = useQuery({
    queryKey: ['assetStats'],
    queryFn: fetchAssetStats,
    refetchInterval: 60000
  });

  /** Fetch risk distribution with 60-second refresh */
  const { data: riskDist } = useQuery({
    queryKey: ['riskDistribution'],
    queryFn: fetchRiskDistribution,
    refetchInterval: 60000
  });

  // ========================================================================
  // Chart Data Preparation
  // ========================================================================

  /** Asset Class Bar Chart Data */
  const assetClassData = stats ? Object.entries(stats.by_asset_class).map(([name, value]) => ({
    name,
    count: value,
    avgCorr: stats.avg_correlation_to_sp500[name] || 0
  })) : [];

  /** Risk Level Pie Chart Data */
  const riskLevelData = stats ? Object.entries(stats.by_risk_level).map(([name, value]) => ({
    name,
    value
  })) : [];

  /** Asset class color mapping */
  const ASSET_CLASS_COLORS: Record<string, string> = {
    STOCK: '#3b82f6',
    BOND: '#10b981',
    CRYPTO: '#f59e0b',
    COMMODITY: '#8b5cf6',
    ETF: '#06b6d4',
    REIT: '#ec4899'
  };

  /** Risk level color mapping */
  const RISK_COLORS: Record<string, string> = {
    VERY_LOW: '#10b981',
    LOW: '#3b82f6',
    MEDIUM: '#f59e0b',
    HIGH: '#ef4444',
    VERY_HIGH: '#dc2626'
  };

  // ========================================================================
  // Render Helper Functions
  // ========================================================================

  /** Get Badge variant for risk level */
  const getRiskBadgeVariant = (risk: string): 'default' | 'success' | 'danger' | 'warning' | 'info' => {
    const variants: Record<string, 'default' | 'success' | 'danger' | 'warning' | 'info'> = {
      VERY_LOW: 'success',
      LOW: 'info',
      MEDIUM: 'warning',
      HIGH: 'danger',
      VERY_HIGH: 'danger'
    };
    return variants[risk] || 'default';
  };

  /** Get icon for asset class */
  const getAssetIcon = (assetClass: string) => {
    const icons: Record<string, React.ReactNode> = {
      STOCK: <TrendingUp className="h-5 w-5" />,
      BOND: <Shield className="h-5 w-5" />,
      CRYPTO: <Coins className="h-5 w-5" />,
      COMMODITY: <Activity className="h-5 w-5" />,
      ETF: <DollarSign className="h-5 w-5" />,
      REIT: <AlertTriangle className="h-5 w-5" />
    };
    return icons[assetClass] || <DollarSign className="h-5 w-5" />;
  };

  // ========================================================================
  // Render
  // ========================================================================

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Multi-Asset Dashboard</h1>
        <p className="text-gray-600 mt-2">
          Phase 30: Multi-Asset Support - Manage stocks, bonds, crypto, commodities, ETFs, and REITs
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <div className="space-y-2">
            <p className="text-sm font-medium text-gray-600">Total Assets</p>
            <div className="text-3xl font-bold">{stats?.total_assets || 0}</div>
            <p className="text-xs text-gray-500 mt-2">Across 6 asset classes</p>
          </div>
        </Card>

        <Card>
          <div className="space-y-2">
            <p className="text-sm font-medium text-gray-600">Asset Classes</p>
            <div className="text-3xl font-bold">
              {stats ? Object.keys(stats.by_asset_class).length : 0}
            </div>
            <p className="text-xs text-gray-500 mt-2">STOCK, BOND, CRYPTO, etc.</p>
          </div>
        </Card>

        <Card>
          <div className="space-y-2">
            <p className="text-sm font-medium text-gray-600">High Risk Assets</p>
            <div className="text-3xl font-bold text-red-500">
              {(stats?.by_risk_level?.HIGH || 0) + (stats?.by_risk_level?.VERY_HIGH || 0)}
            </div>
            <p className="text-xs text-gray-500 mt-2">Require careful monitoring</p>
          </div>
        </Card>

        <Card>
          <div className="space-y-2">
            <p className="text-sm font-medium text-gray-600">Low Risk Assets</p>
            <div className="text-3xl font-bold text-green-500">
              {(stats?.by_risk_level?.VERY_LOW || 0) + (stats?.by_risk_level?.LOW || 0)}
            </div>
            <p className="text-xs text-gray-500 mt-2">Safe haven assets</p>
          </div>
        </Card>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Asset Class Distribution */}
        <Card title="Asset Class Distribution">
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={assetClassData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="count" fill="#3b82f6" name="Count" />
            </BarChart>
          </ResponsiveContainer>
        </Card>

        {/* Risk Level Distribution */}
        <Card title="Risk Level Distribution">
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={riskLevelData}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                outerRadius={100}
                label
              >
                {riskLevelData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={RISK_COLORS[entry.name] || '#3b82f6'} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </Card>
      </div>

      {/* Assets Table */}
      <Card title="Assets by Class">
        {/* Tab Buttons */}
        <div className="flex flex-wrap gap-2 mb-4 pb-4 border-b">
          <button
            onClick={() => setSelectedClass(undefined)}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              selectedClass === undefined
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            All
          </button>
          <button
            onClick={() => setSelectedClass('STOCK')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              selectedClass === 'STOCK'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Stocks
          </button>
          <button
            onClick={() => setSelectedClass('BOND')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              selectedClass === 'BOND'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Bonds
          </button>
          <button
            onClick={() => setSelectedClass('CRYPTO')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              selectedClass === 'CRYPTO'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Crypto
          </button>
          <button
            onClick={() => setSelectedClass('COMMODITY')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              selectedClass === 'COMMODITY'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Commodities
          </button>
          <button
            onClick={() => setSelectedClass('ETF')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              selectedClass === 'ETF'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            ETFs
          </button>
          <button
            onClick={() => setSelectedClass('REIT')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              selectedClass === 'REIT'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            REITs
          </button>
        </div>

        {/* Table */}
        <div className="rounded-md border overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-gray-50">
                <th className="h-12 px-4 text-left align-middle font-medium">Symbol</th>
                <th className="h-12 px-4 text-left align-middle font-medium">Name</th>
                <th className="h-12 px-4 text-left align-middle font-medium">Class</th>
                <th className="h-12 px-4 text-left align-middle font-medium">Risk</th>
                <th className="h-12 px-4 text-left align-middle font-medium">Corr (S&P500)</th>
                <th className="h-12 px-4 text-left align-middle font-medium">Exchange</th>
              </tr>
            </thead>
            <tbody>
              {assetsData?.assets.map((asset) => (
                <tr key={asset.id} className="border-b">
                  <td className="p-4 align-middle font-mono font-bold">{asset.symbol}</td>
                  <td className="p-4 align-middle">{asset.name}</td>
                  <td className="p-4 align-middle">
                    <div className="flex items-center gap-2">
                      {getAssetIcon(asset.asset_class)}
                      <span>{asset.asset_class}</span>
                    </div>
                  </td>
                  <td className="p-4 align-middle">
                    <Badge variant={getRiskBadgeVariant(asset.risk_level)}>
                      {asset.risk_level}
                    </Badge>
                  </td>
                  <td className="p-4 align-middle">
                    {asset.correlation_to_sp500 !== null ? (
                      <span className={asset.correlation_to_sp500 > 0.7 ? 'text-blue-600' : asset.correlation_to_sp500 < 0 ? 'text-red-600' : ''}>
                        {asset.correlation_to_sp500.toFixed(2)}
                      </span>
                    ) : (
                      <span className="text-gray-400">N/A</span>
                    )}
                  </td>
                  <td className="p-4 align-middle text-gray-600">{asset.exchange || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>

          {(!assetsData?.assets || assetsData.assets.length === 0) && (
            <div className="p-8 text-center text-gray-500">
              No assets found
            </div>
          )}
        </div>
      </Card>

      {/* Risk Distribution Detail */}
      {riskDist && (
        <Card title="Risk Level Breakdown">
          <div className="space-y-4">
            {riskDist.risk_levels.map((level) => {
              const data = riskDist.distribution[level];
              if (data.count === 0) return null;

              return (
                <div key={level} className="border rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-semibold flex items-center gap-2">
                      <Badge variant={getRiskBadgeVariant(level)}>{level}</Badge>
                      <span className="text-gray-600 text-sm">({data.count} assets)</span>
                    </h3>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
                    {data.assets.map((asset) => (
                      <div key={asset.symbol} className="text-sm flex items-center justify-between bg-gray-50 rounded px-3 py-2">
                        <span className="font-mono font-medium">{asset.symbol}</span>
                        <span className="text-gray-500 text-xs">{asset.asset_class}</span>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </Card>
      )}
    </div>
  );
};

export default MultiAssetDashboard;

/**
 * Portfolio Optimization Page
 *
 * Phase 31: Portfolio Optimization
 * Date: 2025-12-30
 *
 * Modern Portfolio Theory (MPT) visualization dashboard:
 * - Maximum Sharpe Ratio optimization
 * - Minimum Variance portfolio
 * - Efficient Frontier calculation
 * - Monte Carlo simulation
 * - Risk Parity allocation
 *
 * Features:
 * - Interactive asset selection (multi-select)
 * - Real-time optimization calculations
 * - Recharts visualization (Scatter, Line, Pie charts)
 * - Downloadable optimization results
 */

import React, { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import {
  ScatterChart,
  Scatter,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Label
} from 'recharts';
import {
  TrendingUp,
  Shield,
  Target,
  BarChart3,
  PieChart as PieChartIcon,
  AlertCircle,
  Download
} from 'lucide-react';

// ============================================================================
// Types
// ============================================================================

/** Request payload for optimization API */
interface OptimizeRequest {
  symbols: string[];
  period: string;
  risk_free_rate: number;
}

/** Optimization result from API */
interface OptimizationResult {
  optimization_type: string;
  weights: Record<string, number>;
  expected_return: number;
  volatility: number;
  sharpe_ratio: number;
}

/** Efficient Frontier point */
interface FrontierPoint {
  return: number;
  volatility: number;
  sharpe_ratio: number;
}

/** Monte Carlo simulation result */
interface MonteCarloResult {
  simulations: Array<{
    return: number;
    volatility: number;
    sharpe_ratio: number;
    weights: Record<string, number>;
  }>;
  best_sharpe_portfolio: {
    return: number;
    volatility: number;
    sharpe_ratio: number;
  };
}

// ============================================================================
// Constants
// ============================================================================

/** Popular asset symbols for quick selection */
const POPULAR_ASSETS = [
  { symbol: 'AAPL', name: 'Apple Inc.', class: 'STOCK' },
  { symbol: 'MSFT', name: 'Microsoft', class: 'STOCK' },
  { symbol: 'GOOGL', name: 'Alphabet', class: 'STOCK' },
  { symbol: 'TSLA', name: 'Tesla', class: 'STOCK' },
  { symbol: 'NVDA', name: 'NVIDIA', class: 'STOCK' },
  { symbol: 'TLT', name: '20Y Treasury Bond ETF', class: 'BOND' },
  { symbol: 'IEF', name: '7-10Y Treasury Bond ETF', class: 'BOND' },
  { symbol: 'GLD', name: 'Gold ETF', class: 'COMMODITY' },
  { symbol: 'SLV', name: 'Silver ETF', class: 'COMMODITY' },
  { symbol: 'BTC-USD', name: 'Bitcoin', class: 'CRYPTO' },
  { symbol: 'ETH-USD', name: 'Ethereum', class: 'CRYPTO' },
  { symbol: 'SPY', name: 'S&P 500 ETF', class: 'ETF' },
  { symbol: 'QQQ', name: 'Nasdaq-100 ETF', class: 'ETF' },
  { symbol: 'VNQ', name: 'Real Estate ETF', class: 'REIT' }
];

/** Chart colors */
const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4'];

// ============================================================================
// API Functions
// ============================================================================

/** Optimize for maximum Sharpe ratio */
const optimizeSharpe = async (request: OptimizeRequest): Promise<OptimizationResult> => {
  const response = await fetch('/api/portfolio/optimize/sharpe', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request)
  });
  if (!response.ok) throw new Error('Sharpe optimization failed');
  return response.json();
};

/** Optimize for minimum variance */
const optimizeMinVariance = async (request: OptimizeRequest): Promise<OptimizationResult> => {
  const response = await fetch('/api/portfolio/optimize/min-variance', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request)
  });
  if (!response.ok) throw new Error('Min variance optimization failed');
  return response.json();
};

/** Calculate efficient frontier */
const calculateEfficientFrontier = async (request: OptimizeRequest & { num_points: number }) => {
  const response = await fetch('/api/portfolio/efficient-frontier', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request)
  });
  if (!response.ok) throw new Error('Efficient frontier calculation failed');
  return response.json();
};

/** Run Monte Carlo simulation */
const runMonteCarlo = async (request: OptimizeRequest & { num_simulations: number }): Promise<MonteCarloResult> => {
  const response = await fetch('/api/portfolio/monte-carlo', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request)
  });
  if (!response.ok) throw new Error('Monte Carlo simulation failed');
  return response.json();
};

/** Calculate risk parity allocation */
const calculateRiskParity = async (request: OptimizeRequest): Promise<OptimizationResult> => {
  const response = await fetch('/api/portfolio/risk-parity', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request)
  });
  if (!response.ok) throw new Error('Risk parity calculation failed');
  return response.json();
};

// ============================================================================
// Component
// ============================================================================

export const PortfolioOptimizationPage: React.FC = () => {
  // ========================================================================
  // State Management
  // ========================================================================

  /** Selected asset symbols for optimization */
  const [selectedSymbols, setSelectedSymbols] = useState<string[]>(['AAPL', 'MSFT', 'GOOGL', 'TLT', 'GLD']);

  /** Historical data period */
  const [period, setPeriod] = useState<string>('1y');

  /** Risk-free rate for Sharpe ratio calculation */
  const [riskFreeRate, setRiskFreeRate] = useState<number>(0.02);

  /** Number of Monte Carlo simulations */
  const [numSimulations, setNumSimulations] = useState<number>(5000);

  /** Active result tab */
  const [activeTab, setActiveTab] = useState<'sharpe' | 'min-var' | 'frontier' | 'monte-carlo' | 'risk-parity'>('sharpe');

  // ========================================================================
  // API Mutations
  // ========================================================================

  const sharpeMutation = useMutation({
    mutationFn: optimizeSharpe
  });

  const minVarianceMutation = useMutation({
    mutationFn: optimizeMinVariance
  });

  const frontierMutation = useMutation({
    mutationFn: calculateEfficientFrontier
  });

  const monteCarloMutation = useMutation({
    mutationFn: runMonteCarlo
  });

  const riskParityMutation = useMutation({
    mutationFn: calculateRiskParity
  });

  // ========================================================================
  // Event Handlers
  // ========================================================================

  /** Toggle asset selection */
  const toggleAsset = (symbol: string) => {
    if (selectedSymbols.includes(symbol)) {
      setSelectedSymbols(selectedSymbols.filter(s => s !== symbol));
    } else {
      setSelectedSymbols([...selectedSymbols, symbol]);
    }
  };

  /** Run optimization based on type */
  const runOptimization = (type: 'sharpe' | 'min-variance' | 'frontier' | 'monte-carlo' | 'risk-parity') => {
    if (selectedSymbols.length < 2) {
      alert('Please select at least 2 assets');
      return;
    }

    const request: OptimizeRequest = {
      symbols: selectedSymbols,
      period,
      risk_free_rate: riskFreeRate
    };

    switch (type) {
      case 'sharpe':
        sharpeMutation.mutate(request);
        setActiveTab('sharpe');
        break;
      case 'min-variance':
        minVarianceMutation.mutate(request);
        setActiveTab('min-var');
        break;
      case 'frontier':
        frontierMutation.mutate({ ...request, num_points: 50 });
        setActiveTab('frontier');
        break;
      case 'monte-carlo':
        monteCarloMutation.mutate({ ...request, num_simulations: numSimulations });
        setActiveTab('monte-carlo');
        break;
      case 'risk-parity':
        riskParityMutation.mutate(request);
        setActiveTab('risk-parity');
        break;
    }
  };

  /** Download results as JSON */
  const downloadResults = (data: any, filename: string) => {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  };

  // ========================================================================
  // Render Helper Functions
  // ========================================================================

  /** Render portfolio weights as pie chart */
  const renderWeightsPieChart = (weights: Record<string, number>) => {
    const data = Object.entries(weights).map(([symbol, weight]) => ({
      name: symbol,
      value: weight * 100 // Convert to percentage
    }));

    return (
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={data}
            dataKey="value"
            nameKey="name"
            cx="50%"
            cy="50%"
            outerRadius={100}
            label={(entry) => `${entry.name}: ${entry.value.toFixed(1)}%`}
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip formatter={(value: number) => `${value.toFixed(2)}%`} />
        </PieChart>
      </ResponsiveContainer>
    );
  };

  /** Render optimization result card */
  const renderResultCard = (
    title: string,
    icon: React.ReactNode,
    mutation: any,
    onDownload?: () => void
  ) => {
    const data = mutation.data;

    return (
      <Card title={title}>
        {data && (
          <div className="flex items-center gap-2 mb-4">
            <Badge variant="info">
              Return: {(data.expected_return * 100).toFixed(1)}%
            </Badge>
            <Badge variant="info">
              Vol: {(data.volatility * 100).toFixed(1)}%
            </Badge>
            <Badge variant="success">
              Sharpe: {data.sharpe_ratio.toFixed(2)}
            </Badge>
            {onDownload && (
              <button
                onClick={onDownload}
                className="ml-auto p-2 hover:bg-gray-100 rounded transition-colors"
              >
                <Download className="h-4 w-4" />
              </button>
            )}
          </div>
        )}
        {mutation.isPending && <p className="text-gray-600">Calculating...</p>}
        {mutation.isError && (
          <div className="flex items-center gap-2 text-red-500">
            <AlertCircle className="h-4 w-4" />
            <span>Error: {mutation.error?.message}</span>
          </div>
        )}
        {data && data.weights && renderWeightsPieChart(data.weights)}
      </Card>
    );
  };

  // ========================================================================
  // Render Tab Content
  // ========================================================================

  const renderTabContent = () => {
    switch (activeTab) {
      case 'sharpe':
        return renderResultCard(
          'Maximum Sharpe Ratio Portfolio',
          <TrendingUp className="h-5 w-5" />,
          sharpeMutation,
          () => downloadResults(sharpeMutation.data, 'max-sharpe.json')
        );

      case 'min-var':
        return renderResultCard(
          'Minimum Variance Portfolio',
          <Shield className="h-5 w-5" />,
          minVarianceMutation,
          () => downloadResults(minVarianceMutation.data, 'min-variance.json')
        );

      case 'frontier':
        return (
          <Card title="Efficient Frontier">
            {frontierMutation.data && (
              <button
                onClick={() => downloadResults(frontierMutation.data, 'efficient-frontier.json')}
                className="mb-4 flex items-center gap-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded transition-colors"
              >
                <Download className="h-4 w-4" />
                Download
              </button>
            )}
            {frontierMutation.isPending && <p>Calculating efficient frontier...</p>}
            {frontierMutation.isError && <p className="text-red-500">Error: {frontierMutation.error?.message}</p>}
            {frontierMutation.data && frontierMutation.data.frontier && (
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={frontierMutation.data.frontier}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="volatility" tickFormatter={(v) => `${(v * 100).toFixed(1)}%`}>
                    <Label value="Volatility (Risk)" position="insideBottom" offset={-5} />
                  </XAxis>
                  <YAxis tickFormatter={(v) => `${(v * 100).toFixed(1)}%`}>
                    <Label value="Expected Return" angle={-90} position="insideLeft" />
                  </YAxis>
                  <Tooltip
                    formatter={(value: number, name: string) => {
                      if (name === 'return' || name === 'volatility') return `${(value * 100).toFixed(2)}%`;
                      return value.toFixed(2);
                    }}
                  />
                  <Legend />
                  <Line type="monotone" dataKey="return" stroke="#3b82f6" name="Return" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            )}
          </Card>
        );

      case 'monte-carlo':
        return (
          <Card title="Monte Carlo Simulation">
            {monteCarloMutation.data && (
              <button
                onClick={() => downloadResults(monteCarloMutation.data, 'monte-carlo.json')}
                className="mb-4 flex items-center gap-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded transition-colors"
              >
                <Download className="h-4 w-4" />
                Download
              </button>
            )}
            {monteCarloMutation.isPending && <p>Running {numSimulations.toLocaleString()} simulations...</p>}
            {monteCarloMutation.isError && <p className="text-red-500">Error: {monteCarloMutation.error?.message}</p>}
            {monteCarloMutation.data && monteCarloMutation.data.simulations && (
              <ResponsiveContainer width="100%" height={400}>
                <ScatterChart>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="volatility" tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}>
                    <Label value="Volatility (Risk)" position="insideBottom" offset={-5} />
                  </XAxis>
                  <YAxis dataKey="return" tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}>
                    <Label value="Expected Return" angle={-90} position="insideLeft" />
                  </YAxis>
                  <Tooltip
                    formatter={(value: number) => `${(value * 100).toFixed(2)}%`}
                    cursor={{ strokeDasharray: '3 3' }}
                  />
                  <Legend />
                  <Scatter
                    name="Portfolios"
                    data={monteCarloMutation.data.simulations}
                    fill="#3b82f6"
                    fillOpacity={0.3}
                  />
                </ScatterChart>
              </ResponsiveContainer>
            )}
          </Card>
        );

      case 'risk-parity':
        return renderResultCard(
          'Risk Parity Allocation',
          <PieChartIcon className="h-5 w-5" />,
          riskParityMutation,
          () => downloadResults(riskParityMutation.data, 'risk-parity.json')
        );

      default:
        return null;
    }
  };

  // ========================================================================
  // Render
  // ========================================================================

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Portfolio Optimization</h1>
        <p className="text-gray-600 mt-2">
          Phase 31: Modern Portfolio Theory (MPT) - Efficient Frontier, Sharpe Ratio, Monte Carlo
        </p>
      </div>

      {/* Asset Selection */}
      <Card title="Asset Selection">
        <p className="text-sm text-gray-600 mb-4">
          Select 2-20 assets for portfolio optimization. Selected: {selectedSymbols.length}
        </p>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-7 gap-2">
          {POPULAR_ASSETS.map((asset) => (
            <button
              key={asset.symbol}
              onClick={() => toggleAsset(asset.symbol)}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                selectedSymbols.includes(asset.symbol)
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              <span className="font-mono font-bold">{asset.symbol}</span>
            </button>
          ))}
        </div>

        {/* Parameters */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
          <div>
            <label className="text-sm font-medium">Period</label>
            <select
              className="w-full mt-1 rounded-md border px-3 py-2"
              value={period}
              onChange={(e) => setPeriod(e.target.value)}
            >
              <option value="6mo">6 Months</option>
              <option value="1y">1 Year</option>
              <option value="2y">2 Years</option>
              <option value="5y">5 Years</option>
            </select>
          </div>

          <div>
            <label className="text-sm font-medium">Risk-Free Rate</label>
            <input
              type="number"
              className="w-full mt-1 rounded-md border px-3 py-2"
              value={riskFreeRate}
              onChange={(e) => setRiskFreeRate(parseFloat(e.target.value))}
              min="0"
              max="0.1"
              step="0.001"
            />
          </div>

          <div>
            <label className="text-sm font-medium">Monte Carlo Simulations</label>
            <input
              type="number"
              className="w-full mt-1 rounded-md border px-3 py-2"
              value={numSimulations}
              onChange={(e) => setNumSimulations(parseInt(e.target.value))}
              min="1000"
              max="50000"
              step="1000"
            />
          </div>
        </div>
      </Card>

      {/* Optimization Controls */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <Button
          onClick={() => runOptimization('sharpe')}
          disabled={sharpeMutation.isPending}
          variant="primary"
        >
          <div className="flex items-center gap-2">
            <TrendingUp className="h-4 w-4" />
            Max Sharpe
          </div>
        </Button>
        <Button
          onClick={() => runOptimization('min-variance')}
          disabled={minVarianceMutation.isPending}
          variant="primary"
        >
          <div className="flex items-center gap-2">
            <Shield className="h-4 w-4" />
            Min Variance
          </div>
        </Button>
        <Button
          onClick={() => runOptimization('frontier')}
          disabled={frontierMutation.isPending}
          variant="primary"
        >
          <div className="flex items-center gap-2">
            <BarChart3 className="h-4 w-4" />
            Frontier
          </div>
        </Button>
        <Button
          onClick={() => runOptimization('monte-carlo')}
          disabled={monteCarloMutation.isPending}
          variant="primary"
        >
          <div className="flex items-center gap-2">
            <Target className="h-4 w-4" />
            Monte Carlo
          </div>
        </Button>
        <Button
          onClick={() => runOptimization('risk-parity')}
          disabled={riskParityMutation.isPending}
          variant="primary"
        >
          <div className="flex items-center gap-2">
            <PieChartIcon className="h-4 w-4" />
            Risk Parity
          </div>
        </Button>
      </div>

      {/* Results Tabs */}
      <div>
        <div className="flex flex-wrap gap-2 mb-4 pb-4 border-b">
          <button
            onClick={() => setActiveTab('sharpe')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              activeTab === 'sharpe'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Max Sharpe
          </button>
          <button
            onClick={() => setActiveTab('min-var')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              activeTab === 'min-var'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Min Variance
          </button>
          <button
            onClick={() => setActiveTab('frontier')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              activeTab === 'frontier'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Efficient Frontier
          </button>
          <button
            onClick={() => setActiveTab('monte-carlo')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              activeTab === 'monte-carlo'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Monte Carlo
          </button>
          <button
            onClick={() => setActiveTab('risk-parity')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              activeTab === 'risk-parity'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Risk Parity
          </button>
        </div>

        {renderTabContent()}
      </div>
    </div>
  );
};

export default PortfolioOptimizationPage;

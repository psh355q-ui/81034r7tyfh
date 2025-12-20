/**
 * Analysis Page Example
 * AI 종목 분석 페이지
 */

import React, { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { Search, TrendingUp, TrendingDown, Minus, AlertTriangle } from 'lucide-react';
import { analyzeTicker, analyzeBatch, type AIDecision } from '../services/api';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Input } from '../components/common/Input';
import { Badge } from '../components/common/Badge';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { Alert } from '../components/common/Alert';
import { TickerAutocompleteInput } from '../components/common/TickerAutocompleteInput';

export const Analysis: React.FC = () => {
  const [ticker, setTicker] = useState('');
  const [batchTickers, setBatchTickers] = useState('');
  const [analysisResult, setAnalysisResult] = useState<AIDecision | null>(null);

  // Single ticker analysis mutation
  const analyzeMutation = useMutation({
    mutationFn: (ticker: string) => analyzeTicker(ticker),
    onSuccess: (data) => {
      setAnalysisResult(data);
    },
  });

  // Batch analysis mutation
  const batchMutation = useMutation({
    mutationFn: (tickers: string[]) => analyzeBatch(tickers),
  });

  const handleAnalyze = async () => {
    if (!ticker.trim()) return;
    analyzeMutation.mutate(ticker.toUpperCase());
  };

  const handleBatchAnalyze = async () => {
    if (!batchTickers.trim()) return;
    const tickers = batchTickers
      .split(',')
      .map(t => t.trim().toUpperCase())
      .filter(t => t.length > 0);

    if (tickers.length === 0) return;
    batchMutation.mutate(tickers);
  };

  const getActionColor = (action: string) => {
    switch (action) {
      case 'BUY': return 'success';
      case 'SELL': return 'danger';
      case 'HOLD': return 'default';
      default: return 'default';
    }
  };

  const getActionIcon = (action: string) => {
    switch (action) {
      case 'BUY': return <TrendingUp size={20} />;
      case 'SELL': return <TrendingDown size={20} />;
      case 'HOLD': return <Minus size={20} />;
      default: return null;
    }
  };

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">AI Analysis</h1>
        <p className="text-gray-600 mt-1">Get AI-powered trading recommendations</p>
      </div>

      {/* Single Ticker Analysis */}
      <Card title="Single Ticker Analysis">
        <div className="space-y-4">
          <div className="flex gap-4">
            <div className="flex-1">
              <TickerAutocompleteInput
                label="Ticker Symbol"
                value={ticker}
                onChange={setTicker}
                onSubmit={handleAnalyze}
                placeholder="Enter ticker (e.g., AAPL)"
              />
            </div>
            <div className="flex items-end">
              <Button
                onClick={handleAnalyze}
                disabled={analyzeMutation.isPending || !ticker.trim()}
                className="flex items-center gap-2"
              >
                {analyzeMutation.isPending ? (
                  <>
                    <LoadingSpinner size="sm" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <Search size={16} />
                    Analyze
                  </>
                )}
              </Button>
            </div>
          </div>

          {analyzeMutation.isError && (
            <Alert variant="error">
              Failed to analyze ticker. Please try again.
            </Alert>
          )}
        </div>
      </Card>

      {/* Analysis Result */}
      {analysisResult && (
        <Card title={`Analysis Result: ${analysisResult.ticker}`}>
          <div className="space-y-6">
            {/* Action & Conviction */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Badge variant={getActionColor(analysisResult.action)} className="text-lg px-4 py-2">
                  <span className="flex items-center gap-2">
                    {getActionIcon(analysisResult.action)}
                    {analysisResult.action}
                  </span>
                </Badge>
                <div>
                  <p className="text-sm text-gray-600">Conviction</p>
                  <p className="text-2xl font-bold">
                    {(analysisResult.conviction * 100).toFixed(0)}%
                  </p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-sm text-gray-600">Position Size</p>
                <p className="text-xl font-semibold">{analysisResult.position_size}%</p>
              </div>
            </div>

            {/* Conviction Bar */}
            <div>
              <div className="h-3 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className={`h-full ${analysisResult.conviction >= 0.8
                    ? 'bg-green-500'
                    : analysisResult.conviction >= 0.6
                      ? 'bg-yellow-500'
                      : 'bg-red-500'
                    }`}
                  style={{ width: `${analysisResult.conviction * 100}%` }}
                />
              </div>
            </div>

            {/* Reasoning */}
            <div>
              <h3 className="text-sm font-medium text-gray-700 mb-2">AI Reasoning</h3>
              <p className="text-gray-900 bg-gray-50 p-4 rounded-lg">
                {analysisResult.reasoning}
              </p>
            </div>

            {/* Price Targets */}
            <div className="grid grid-cols-2 gap-4">
              {analysisResult.target_price && (
                <div className="bg-green-50 p-4 rounded-lg">
                  <p className="text-sm text-green-700 font-medium">Target Price</p>
                  <p className="text-2xl font-bold text-green-900">
                    ${analysisResult.target_price.toFixed(2)}
                  </p>
                </div>
              )}
              {analysisResult.stop_loss && (
                <div className="bg-red-50 p-4 rounded-lg">
                  <p className="text-sm text-red-700 font-medium">Stop Loss</p>
                  <p className="text-2xl font-bold text-red-900">
                    ${analysisResult.stop_loss.toFixed(2)}
                  </p>
                </div>
              )}
            </div>

            {/* Risk Factors */}
            {analysisResult.risk_factors.length > 0 && (
              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
                  <AlertTriangle size={16} className="text-yellow-600" />
                  Risk Factors
                </h3>
                <div className="flex flex-wrap gap-2">
                  {analysisResult.risk_factors.map((factor, idx) => (
                    <Badge key={idx} variant="warning">
                      {factor.replace(/_/g, ' ')}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {/* Timestamp */}
            {analysisResult.timestamp && (
              <p className="text-xs text-gray-500">
                Analyzed at: {new Date(analysisResult.timestamp).toLocaleString()}
              </p>
            )}
          </div>
        </Card>
      )}

      {/* Batch Analysis */}
      <Card title="Batch Analysis">
        <div className="space-y-4">
          <TickerAutocompleteInput
            label="Multiple Tickers"
            value={batchTickers}
            onChange={setBatchTickers}
            onSubmit={handleBatchAnalyze}
            placeholder="Enter tickers separated by commas (e.g., AAPL, GOOGL, MSFT)"
            multi={true}
          />
          <Button
            onClick={handleBatchAnalyze}
            disabled={batchMutation.isPending || !batchTickers.trim()}
            variant="secondary"
          >
            {batchMutation.isPending ? 'Analyzing...' : 'Analyze Batch'}
          </Button>

          {batchMutation.isError && (
            <Alert variant="error">
              Failed to analyze batch. Please try again.
            </Alert>
          )}

          {batchMutation.isSuccess && batchMutation.data && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-4">
              {batchMutation.data.map((result) => (
                <div
                  key={result.ticker}
                  className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                >
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-semibold text-lg">{result.ticker}</h4>
                    <Badge variant={getActionColor(result.action)}>
                      {result.action}
                    </Badge>
                  </div>
                  <p className="text-sm text-gray-600 mb-2">
                    Conviction: {(result.conviction * 100).toFixed(0)}%
                  </p>
                  <div className="h-2 bg-gray-200 rounded-full">
                    <div
                      className="h-full bg-blue-500 rounded-full"
                      style={{ width: `${result.conviction * 100}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </Card>
    </div>
  );
};

/**
 * Analysis Page Example
 * AI 종목 분석 페이지
 */

import React, { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { Search, TrendingUp, TrendingDown, Minus, AlertTriangle, Radio } from 'lucide-react';
import { analyzeTicker, analyzeBatch, type AIDecision } from '../services/api';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Input } from '../components/common/Input';
import { Badge } from '../components/common/Badge';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { Alert } from '../components/common/Alert';
import { TickerAutocompleteInput } from '../components/common/TickerAutocompleteInput';
import { useEmergencyStatus, useGroundingUsage } from '../hooks/useEmergencyStatus';
import axios from 'axios';
import { GNNGraph } from '../components/Analysis/GNNGraph';

export const Analysis: React.FC = () => {
  const [ticker, setTicker] = useState('');
  const [batchTickers, setBatchTickers] = useState('');
  const [analysisResult, setAnalysisResult] = useState<AIDecision | null>(null);
  const [showGroundingWarning, setShowGroundingWarning] = useState(false);
  const [groundingNews, setGroundingNews] = useState<any>(null);
  const [historyFilter, setHistoryFilter] = useState('');
  const [selectedHistory, setSelectedHistory] = useState<any>(null);

  // Emergency status polling
  const {
    isEmergency,
    severity,
    triggers,
    recommended,
    searchesToday,
    dailyLimit,
    message: emergencyMessage,
    vix,
    portfolioData
  } = useEmergencyStatus();

  const { usage } = useGroundingUsage();

  // Analysis history query
  const { data: history, isLoading: historyLoading } = useQuery({
    queryKey: ['analysis-history', historyFilter],
    queryFn: () => axios.get('/api/analysis/history', {
      params: {
        ticker: historyFilter || undefined,
        limit: 20
      }
    }),
    refetchInterval: 120000, // Refresh every 2 minutes
  });

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

  // Grounding search mutation
  const groundingMutation = useMutation({
    mutationFn: async (ticker: string) => {
      const response = await axios.get(`/api/news/gemini/search/ticker/${ticker}?max_articles=5`);
      return response.data;
    },
    onSuccess: (data) => {
      setGroundingNews(data);
    },
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

  const handleEmergencySearch = () => {
    setShowGroundingWarning(true);
  };

  const confirmGroundingSearch = async () => {
    if (!ticker.trim()) return;
    setShowGroundingWarning(false);

    const result = await groundingMutation.mutateAsync(ticker.toUpperCase());

    // Track the search
    await axios.post('/api/emergency/grounding/track', {
      ticker: ticker.toUpperCase(),
      results_count: result?.articles?.length || 0,
      emergency_trigger: isEmergency ? triggers[0] : null
    });
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

      {/* Emergency Banner */}
      {isEmergency && (
        <Alert variant="error" className="animate-pulse">
          <div className="flex items-start gap-3">
            <AlertTriangle className="text-red-600" size={24} />
            <div className="flex-1">
              <strong className="text-lg">🚨 Emergency Mode Active</strong>
              <p className="text-sm mt-1">{emergencyMessage}</p>
              <div className="mt-2 flex gap-4 text-xs">
                {vix && <span>VIX: {vix.toFixed(1)}</span>}
                {portfolioData && (
                  <>
                    <span>Daily P&L: {portfolioData.daily_loss_pct.toFixed(2)}%</span>
                    <span>Drawdown: {portfolioData.total_drawdown_pct.toFixed(2)}%</span>
                  </>
                )}
              </div>
            </div>
          </div>
        </Alert>
      )}

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
              <Button
                onClick={handleEmergencySearch}
                disabled={!ticker.trim() || searchesToday >= dailyLimit}
                className={`flex items-center gap-2 ${recommended
                  ? 'bg-red-600 hover:bg-red-700 animate-pulse ring-2 ring-red-400'
                  : 'bg-red-600 hover:bg-red-700'
                  }`}
              >
                <Radio size={16} className={recommended ? 'animate-spin' : ''} />
                🔴 Emergency News
                {recommended && <span className="ml-1 text-xs">⭐ RECOMMENDED</span>}
                <span className="text-xs opacity-75">({searchesToday}/{dailyLimit})</span>
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

      {/* GNN Graph Visualization (v2.0 Injection) */}
      {(ticker || analysisResult) && (
        <div className="animate-fade-in-up">
          <GNNGraph ticker={analysisResult?.ticker || ticker} />
        </div>
      )}

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
                    {((analysisResult.conviction ?? 0) * 100).toFixed(0)}%
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
                  className={`h-full ${(analysisResult.conviction ?? 0) >= 0.8
                    ? 'bg-green-500'
                    : (analysisResult.conviction ?? 0) >= 0.6
                      ? 'bg-yellow-500'
                      : 'bg-red-500'
                    }`}
                  style={{ width: `${(analysisResult.conviction ?? 0) * 100}%` }}
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
            {analysisResult.risk_factors?.length > 0 && (
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
                    Conviction: {((result.conviction ?? 0) * 100).toFixed(0)}%
                  </p>
                  <div className="h-2 bg-gray-200 rounded-full">
                    <div
                      className="h-full bg-blue-500 rounded-full"
                      style={{ width: `${(result.conviction ?? 0) * 100}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </Card>

      {/* Emergency Grounding Warning Modal */}
      {showGroundingWarning && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4" onClick={() => setShowGroundingWarning(false)}>
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-md p-6" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-start gap-3 mb-4">
              <AlertTriangle className="text-red-600" size={24} />
              <div>
                <h3 className="text-lg font-bold text-gray-900">🚨 Emergency Real-Time Search</h3>
                <p className="text-sm text-gray-600 mt-1">This feature uses Gemini Grounding API</p>
              </div>
            </div>

            <Alert variant="warning" className="mb-4">
              <strong>Cost Warning:</strong> $0.035 per search
            </Alert>

            <div className="space-y-2 text-sm text-gray-700 mb-4">
              <p><strong>Use this only for:</strong></p>
              <ul className="list-disc list-inside space-y-1 ml-2">
                <li>Breaking news (war, crisis)</li>
                <li>Market crashes</li>
                <li>Emergency events</li>
                <li>Real-time situation updates</li>
              </ul>
            </div>

            <div className="flex gap-3">
              <Button
                onClick={() => setShowGroundingWarning(false)}
                variant="secondary"
                className="flex-1"
              >
                Cancel
              </Button>
              <Button
                onClick={confirmGroundingSearch}
                className="flex-1 bg-red-600 hover:bg-red-700"
              >
                Search Now ($0.035)
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Grounding News Results */}
      {groundingNews && (
        <Card title="🔴 Emergency Real-Time News">
          <div className="space-y-4">
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-sm text-red-800">
                <strong>Ticker:</strong> {groundingNews.ticker} | <strong>Cost:</strong> {groundingNews.cost_info.current_cost}
              </p>
            </div>

            {groundingNews.articles && groundingNews.articles.length > 0 ? (
              <div className="space-y-3">
                {groundingNews.articles.map((article: any, idx: number) => (
                  <div key={idx} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                    <h4 className="font-semibold text-gray-900 mb-2">{article.title}</h4>
                    <p className="text-sm text-gray-600 mb-2">{article.summary}</p>
                    {article.url && (
                      <a
                        href={article.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm text-blue-600 hover:underline"
                      >
                        Read more →
                      </a>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-600">No breaking news found</p>
            )}
          </div>
        </Card>
      )}

      {/* Analysis History */}
      <Card title="📊 Recent Analysis History">
        <div className="space-y-4">
          {/* Ticker Filter */}
          <div className="flex gap-4">
            <Input
              label="Filter by Ticker"
              value={historyFilter}
              onChange={(value) => setHistoryFilter(value.toUpperCase())}
              placeholder="e.g., AAPL (leave empty for all)"
              className="flex-1"
            />
            {historyFilter && (
              <Button
                variant="secondary"
                onClick={() => setHistoryFilter('')}
                className="self-end"
              >
                Clear
              </Button>
            )}
          </div>

          {/* History Grid */}
          {historyLoading ? (
            <div className="flex justify-center p-8">
              <LoadingSpinner />
            </div>
          ) : history && Array.isArray(history.data) && history.data.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {history.data.map((item: any) => (
                <div
                  key={item.id}
                  onClick={() => setSelectedHistory(item)}
                  className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
                >
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-semibold text-lg">{item.ticker}</h4>
                    <Badge variant={getActionColor(item.action)}>
                      {item.action}
                    </Badge>
                  </div>
                  <div className="space-y-1 text-sm text-gray-600">
                    <p>Conviction: {((item.conviction ?? 0) * 100).toFixed(0)}%</p>
                    <p>Position: {item.position_size}%</p>
                    <p className="text-xs text-gray-400">
                      {new Date(item.timestamp).toLocaleString()}
                    </p>
                  </div>
                  <div className="h-2 bg-gray-200 rounded-full mt-2">
                    <div
                      className="h-full bg-blue-500 rounded-full"
                      style={{ width: `${(item.conviction ?? 0) * 100}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-center text-gray-600 py-8">
              {historyFilter
                ? `No analysis found for ${historyFilter}`
                : 'No analysis history yet'}
            </p>
          )}
        </div>
      </Card>

      {/* History Detail Modal */}
      {selectedHistory && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
          onClick={() => setSelectedHistory(null)}
        >
          <div
            className="bg-white rounded-xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="p-6 space-y-4">
              <div className="flex items-start justify-between">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">{selectedHistory.ticker}</h2>
                  <p className="text-sm text-gray-500">
                    {new Date(selectedHistory.timestamp).toLocaleString()}
                  </p>
                </div>
                <button
                  onClick={() => setSelectedHistory(null)}
                  className="text-gray-500 hover:text-gray-700"
                >
                  ✕
                </button>
              </div>

              <div className="flex items-center gap-4">
                <Badge variant={getActionColor(selectedHistory.action)} className="text-lg px-4 py-2">
                  {selectedHistory.action}
                </Badge>
                <div>
                  <p className="text-sm text-gray-600">Conviction</p>
                  <p className="text-xl font-bold">{((selectedHistory.conviction ?? 0) * 100).toFixed(0)}%</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Position Size</p>
                  <p className="text-xl font-semibold">{selectedHistory.position_size}%</p>
                </div>
              </div>

              <div>
                <h3 className="font-semibold mb-2">AI Reasoning</h3>
                <p className="text-gray-700 bg-gray-50 p-4 rounded-lg whitespace-pre-wrap">
                  {selectedHistory.reasoning}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

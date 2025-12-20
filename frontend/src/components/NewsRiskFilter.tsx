/**
 * News Risk Filter Component - Phase 14.5
 *
 * Advanced news filtering using 4-way ensemble approach.
 * Eliminates noise and identifies true risk signals.
 */

import React, { useState, useEffect } from 'react';
import {
  AlertTriangle,
  Filter,
  TrendingUp,
  TrendingDown,
  Zap,
  PieChart,
  RefreshCw,
  Check,
  X,
  Info
} from 'lucide-react';

// ============================================================================
// Types
// ============================================================================

interface NewsRiskScore {
  news_id?: number;
  ticker: string;
  title: string;
  publish_date: string;
  cluster_risk: number;
  sector_risk: number;
  crash_pattern_risk: number;
  sentiment_trend_risk: number;
  final_risk_score: number;
  risk_level: 'CRITICAL' | 'HIGH' | 'NORMAL' | 'LOW';
  cluster_id?: number;
  sentiment_change?: number;
}

interface RiskCluster {
  cluster_id: number;
  cluster_name: string;
  crash_count: number;
  avg_price_drop: number;
  keywords: string[];
  example_news: string[];
}

interface SectorVector {
  sector_name: string;
  vector_dimension: number;
  news_count: number;
}

// ============================================================================
// Main Component
// ============================================================================

const NewsRiskFilter: React.FC = () => {
  const [mode, setMode] = useState<'analyze' | 'batch' | 'clusters' | 'sectors'>('analyze');

  // Single analysis
  const [ticker, setTicker] = useState('AAPL');
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [analysisResult, setAnalysisResult] = useState<NewsRiskScore | null>(null);

  // Batch filtering
  const [batchNews, setBatchNews] = useState<string>('');
  const [minRiskScore, setMinRiskScore] = useState(0.5);
  const [batchResults, setBatchResults] = useState<any>(null);

  // Risk clusters
  const [clusters, setClusters] = useState<RiskCluster[]>([]);

  // Sector vectors
  const [sectors, setSectors] = useState<SectorVector[]>([]);

  // UI state
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // ============================================================================
  // API Calls
  // ============================================================================

  const analyzeNews = async () => {
    if (!title.trim() || !content.trim()) {
      setError('Please enter both title and content');
      return;
    }

    setLoading(true);
    setError(null);
    setAnalysisResult(null);

    try {
      const response = await fetch('/api/news/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ticker: ticker.toUpperCase(),
          title,
          content,
        })
      });

      if (!response.ok) {
        throw new Error(`Analysis failed: ${response.statusText}`);
      }

      const data: NewsRiskScore = await response.json();
      setAnalysisResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis failed');
    } finally {
      setLoading(false);
    }
  };

  const filterBatch = async () => {
    if (!batchNews.trim()) {
      setError('Please enter news items (JSON array)');
      return;
    }

    setLoading(true);
    setError(null);
    setBatchResults(null);

    try {
      const newsItems = JSON.parse(batchNews);

      const response = await fetch('/api/news/filter-batch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          news_items: newsItems,
          min_risk_score: minRiskScore
        })
      });

      if (!response.ok) {
        throw new Error(`Batch filtering failed: ${response.statusText}`);
      }

      const data = await response.json();
      setBatchResults(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Batch filtering failed');
    } finally {
      setLoading(false);
    }
  };

  const loadClusters = async (rebuild: boolean = false) => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`/api/news/risk-clusters?rebuild=${rebuild}&n_clusters=5`);

      if (!response.ok) {
        throw new Error(`Failed to load clusters: ${response.statusText}`);
      }

      const data = await response.json();
      setClusters(data.clusters);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load clusters');
    } finally {
      setLoading(false);
    }
  };

  const loadSectors = async (rebuild: boolean = false) => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`/api/news/sector-vectors?rebuild=${rebuild}`);

      if (!response.ok) {
        throw new Error(`Failed to load sectors: ${response.statusText}`);
      }

      const data = await response.json();
      setSectors(data.sectors);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load sectors');
    } finally {
      setLoading(false);
    }
  };

  // Load clusters/sectors on mount
  useEffect(() => {
    if (mode === 'clusters' && clusters.length === 0) {
      loadClusters();
    } else if (mode === 'sectors' && sectors.length === 0) {
      loadSectors();
    }
  }, [mode]);

  // ============================================================================
  // Render Helpers
  // ============================================================================

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'CRITICAL': return 'text-red-600 bg-red-50 border-red-200';
      case 'HIGH': return 'text-orange-600 bg-orange-50 border-orange-200';
      case 'NORMAL': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'LOW': return 'text-green-600 bg-green-50 border-green-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const renderModeSelector = () => (
    <div className="flex gap-2 mb-6">
      <button
        onClick={() => setMode('analyze')}
        className={`flex items-center gap-2 px-4 py-2 rounded transition ${
          mode === 'analyze'
            ? 'bg-blue-600 text-white'
            : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
        }`}
      >
        <Zap className="w-4 h-4" />
        Analyze Single
      </button>
      <button
        onClick={() => setMode('batch')}
        className={`flex items-center gap-2 px-4 py-2 rounded transition ${
          mode === 'batch'
            ? 'bg-purple-600 text-white'
            : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
        }`}
      >
        <Filter className="w-4 h-4" />
        Batch Filter
      </button>
      <button
        onClick={() => setMode('clusters')}
        className={`flex items-center gap-2 px-4 py-2 rounded transition ${
          mode === 'clusters'
            ? 'bg-red-600 text-white'
            : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
        }`}
      >
        <PieChart className="w-4 h-4" />
        Risk Clusters
      </button>
      <button
        onClick={() => setMode('sectors')}
        className={`flex items-center gap-2 px-4 py-2 rounded transition ${
          mode === 'sectors'
            ? 'bg-green-600 text-white'
            : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
        }`}
      >
        <TrendingUp className="w-4 h-4" />
        Sector Vectors
      </button>
    </div>
  );

  const renderAnalyzeMode = () => (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Ticker
        </label>
        <input
          type="text"
          value={ticker}
          onChange={(e) => setTicker(e.target.value.toUpperCase())}
          placeholder="AAPL"
          className="w-full px-4 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          News Title
        </label>
        <input
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Apple supplier faces production delays"
          className="w-full px-4 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          News Content
        </label>
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder="Apple's main supplier announced production delays due to supply chain issues..."
          rows={6}
          className="w-full px-4 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <button
        onClick={analyzeNews}
        disabled={loading}
        className="w-full bg-blue-600 text-white px-6 py-3 rounded font-medium hover:bg-blue-700 disabled:bg-gray-400 transition flex items-center justify-center gap-2"
      >
        {loading ? (
          <>
            <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent" />
            Analyzing...
          </>
        ) : (
          <>
            <Zap className="w-5 h-5" />
            Analyze Risk
          </>
        )}
      </button>

      {/* Analysis Result */}
      {analysisResult && (
        <div className="mt-6 border border-gray-200 rounded-lg p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold">Risk Analysis Result</h3>
            <div className={`px-4 py-2 rounded font-semibold border ${getRiskColor(analysisResult.risk_level)}`}>
              {analysisResult.risk_level}
            </div>
          </div>

          {/* Overall Score */}
          <div className="bg-gray-50 rounded p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700">Final Risk Score</span>
              <span className="text-2xl font-bold text-gray-900">
                {(analysisResult.final_risk_score * 100).toFixed(1)}%
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3">
              <div
                className={`h-3 rounded-full transition-all ${
                  analysisResult.final_risk_score >= 0.7 ? 'bg-red-600' :
                  analysisResult.final_risk_score >= 0.5 ? 'bg-orange-500' :
                  analysisResult.final_risk_score >= 0.3 ? 'bg-yellow-500' :
                  'bg-green-500'
                }`}
                style={{ width: `${analysisResult.final_risk_score * 100}%` }}
              />
            </div>
          </div>

          {/* Component Scores */}
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-purple-50 rounded p-3">
              <div className="text-xs text-purple-600 font-medium mb-1">Cluster Risk</div>
              <div className="text-lg font-bold text-purple-900">
                {(analysisResult.cluster_risk * 100).toFixed(1)}%
              </div>
              <div className="text-xs text-purple-600 mt-1">30% weight</div>
            </div>

            <div className="bg-blue-50 rounded p-3">
              <div className="text-xs text-blue-600 font-medium mb-1">Sector Risk</div>
              <div className="text-lg font-bold text-blue-900">
                {(analysisResult.sector_risk * 100).toFixed(1)}%
              </div>
              <div className="text-xs text-blue-600 mt-1">20% weight</div>
            </div>

            <div className="bg-red-50 rounded p-3">
              <div className="text-xs text-red-600 font-medium mb-1">Crash Pattern</div>
              <div className="text-lg font-bold text-red-900">
                {(analysisResult.crash_pattern_risk * 100).toFixed(1)}%
              </div>
              <div className="text-xs text-red-600 mt-1">30% weight</div>
            </div>

            <div className="bg-orange-50 rounded p-3">
              <div className="text-xs text-orange-600 font-medium mb-1">Sentiment Trend</div>
              <div className="text-lg font-bold text-orange-900">
                {(analysisResult.sentiment_trend_risk * 100).toFixed(1)}%
              </div>
              <div className="text-xs text-orange-600 mt-1">20% weight</div>
            </div>
          </div>

          {/* Metadata */}
          {analysisResult.sentiment_change && (
            <div className="bg-yellow-50 border border-yellow-200 rounded p-3 flex items-start gap-2">
              <Info className="w-5 h-5 text-yellow-600 mt-0.5" />
              <div className="text-sm text-yellow-800">
                <span className="font-medium">Sentiment Change:</span>{' '}
                {(analysisResult.sentiment_change * 100).toFixed(1)}% deviation from 30-day average
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );

  const renderBatchMode = () => (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          News Items (JSON Array)
        </label>
        <textarea
          value={batchNews}
          onChange={(e) => setBatchNews(e.target.value)}
          placeholder={`[\n  {"ticker": "AAPL", "title": "...", "content": "...", "publish_date": "2023-11-23T10:00:00"},\n  {"ticker": "MSFT", "title": "...", "content": "..."}\n]`}
          rows={10}
          className="w-full px-4 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-purple-500 font-mono text-sm"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Minimum Risk Score: {(minRiskScore * 100).toFixed(0)}%
        </label>
        <input
          type="range"
          value={minRiskScore}
          onChange={(e) => setMinRiskScore(parseFloat(e.target.value))}
          min={0}
          max={1}
          step={0.05}
          className="w-full"
        />
      </div>

      <button
        onClick={filterBatch}
        disabled={loading}
        className="w-full bg-purple-600 text-white px-6 py-3 rounded font-medium hover:bg-purple-700 disabled:bg-gray-400 transition flex items-center justify-center gap-2"
      >
        {loading ? (
          <>
            <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent" />
            Filtering...
          </>
        ) : (
          <>
            <Filter className="w-5 h-5" />
            Filter Batch
          </>
        )}
      </button>

      {/* Batch Results */}
      {batchResults && (
        <div className="mt-6 space-y-4">
          {/* Statistics */}
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-blue-50 rounded-lg p-4">
              <div className="text-sm text-blue-600 font-medium mb-1">Total Input</div>
              <div className="text-2xl font-bold text-blue-900">{batchResults.total_input}</div>
            </div>

            <div className="bg-green-50 rounded-lg p-4">
              <div className="text-sm text-green-600 font-medium mb-1">Filtered Output</div>
              <div className="text-2xl font-bold text-green-900">{batchResults.filtered_output}</div>
            </div>

            <div className="bg-purple-50 rounded-lg p-4">
              <div className="text-sm text-purple-600 font-medium mb-1">Pass Rate</div>
              <div className="text-2xl font-bold text-purple-900">
                {batchResults.pass_rate_pct.toFixed(1)}%
              </div>
            </div>
          </div>

          {/* Risk Distribution */}
          <div className="bg-gray-50 rounded-lg p-4">
            <h4 className="font-semibold mb-3">Risk Distribution</h4>
            <div className="grid grid-cols-4 gap-2">
              <div className="text-center">
                <div className="text-2xl font-bold text-red-600">
                  {batchResults.risk_distribution.CRITICAL}
                </div>
                <div className="text-xs text-gray-600">CRITICAL</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-orange-600">
                  {batchResults.risk_distribution.HIGH}
                </div>
                <div className="text-xs text-gray-600">HIGH</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-yellow-600">
                  {batchResults.risk_distribution.NORMAL}
                </div>
                <div className="text-xs text-gray-600">NORMAL</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">
                  {batchResults.risk_distribution.LOW}
                </div>
                <div className="text-xs text-gray-600">LOW</div>
              </div>
            </div>
          </div>

          {/* Filtered News List */}
          <div>
            <h4 className="font-semibold mb-3">Filtered News ({batchResults.filtered_output})</h4>
            <div className="space-y-2">
              {batchResults.filtered_news.map((news: NewsRiskScore, index: number) => (
                <div key={index} className={`border rounded-lg p-3 ${getRiskColor(news.risk_level)}`}>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="font-medium text-gray-900">{news.ticker} - {news.title}</div>
                      <div className="text-sm text-gray-600 mt-1">{news.publish_date}</div>
                    </div>
                    <div className="text-right">
                      <div className="font-bold">{news.risk_level}</div>
                      <div className="text-sm">{(news.final_risk_score * 100).toFixed(0)}%</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );

  const renderClustersMode = () => (
    <div className="space-y-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">Risk Clusters</h3>
        <button
          onClick={() => loadClusters(true)}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 disabled:bg-gray-400"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Rebuild
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {clusters.map((cluster) => (
          <div key={cluster.cluster_id} className="border border-gray-200 rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <div className="font-semibold text-gray-900">{cluster.cluster_name}</div>
              <div className="bg-red-100 text-red-800 px-2 py-1 rounded text-sm">
                {cluster.crash_count} crashes
              </div>
            </div>

            <div className="space-y-2 text-sm">
              <div>
                <span className="text-gray-600">Avg Drop:</span>{' '}
                <span className="font-medium text-red-600">
                  {(cluster.avg_price_drop * 100).toFixed(1)}%
                </span>
              </div>

              <div>
                <span className="text-gray-600">Keywords:</span>{' '}
                <div className="flex flex-wrap gap-1 mt-1">
                  {cluster.keywords.map((keyword, i) => (
                    <span key={i} className="bg-gray-100 text-gray-700 px-2 py-0.5 rounded text-xs">
                      {keyword}
                    </span>
                  ))}
                </div>
              </div>

              <div>
                <span className="text-gray-600">Example News:</span>
                <ul className="mt-1 space-y-1">
                  {cluster.example_news.slice(0, 2).map((news, i) => (
                    <li key={i} className="text-xs text-gray-700 italic">"{news.substring(0, 60)}..."</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        ))}
      </div>

      {clusters.length === 0 && !loading && (
        <div className="text-center text-gray-500 py-12">
          <PieChart className="w-16 h-16 mx-auto mb-4 text-gray-400" />
          <p>No risk clusters loaded. Click "Rebuild" to learn patterns.</p>
        </div>
      )}
    </div>
  );

  const renderSectorsMode = () => (
    <div className="space-y-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">Sector Risk Vectors</h3>
        <button
          onClick={() => loadSectors(true)}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:bg-gray-400"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Rebuild
        </button>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        {sectors.map((sector, index) => (
          <div key={index} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition">
            <div className="font-semibold text-gray-900 mb-2">{sector.sector_name}</div>
            <div className="space-y-1 text-sm text-gray-600">
              <div>Dimension: {sector.vector_dimension}</div>
              <div>News Count: {sector.news_count}</div>
            </div>
          </div>
        ))}
      </div>

      {sectors.length === 0 && !loading && (
        <div className="text-center text-gray-500 py-12">
          <TrendingUp className="w-16 h-16 mx-auto mb-4 text-gray-400" />
          <p>No sector vectors loaded. Click "Rebuild" to create profiles.</p>
        </div>
      )}
    </div>
  );

  // ============================================================================
  // Main Render
  // ============================================================================

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2 flex items-center gap-2">
          <AlertTriangle className="w-8 h-8 text-red-600" />
          News Risk Filter
        </h1>
        <p className="text-gray-600">
          4-way ensemble for eliminating noise and identifying true risk signals
        </p>
      </div>

      {/* Mode Selector */}
      {renderModeSelector()}

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 flex items-center gap-2">
          <X className="w-5 h-5 text-red-600" />
          <span className="text-red-800">{error}</span>
        </div>
      )}

      {/* Content */}
      <div className="bg-white rounded-lg shadow p-6">
        {mode === 'analyze' && renderAnalyzeMode()}
        {mode === 'batch' && renderBatchMode()}
        {mode === 'clusters' && renderClustersMode()}
        {mode === 'sectors' && renderSectorsMode()}
      </div>

      {/* Info Panel */}
      <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h4 className="font-semibold text-blue-900 mb-2 flex items-center gap-2">
          <Info className="w-4 h-4" />
          How It Works
        </h4>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>• <strong>Cluster Risk (30%):</strong> Proximity to historical crash patterns</li>
          <li>• <strong>Sector Risk (20%):</strong> Sector-specific risk profile matching</li>
          <li>• <strong>Crash Pattern (30%):</strong> Company-specific historical crash signatures</li>
          <li>• <strong>Sentiment Trend (20%):</strong> Deviation from 30-day sentiment average</li>
        </ul>
      </div>
    </div>
  );
};

export default NewsRiskFilter;

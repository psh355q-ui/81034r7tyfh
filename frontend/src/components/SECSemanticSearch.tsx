/**
 * SEC Semantic Search Component - Phase 13.5
 *
 * Advanced semantic search interface for SEC filings.
 * Provides natural language search with multiple search modes.
 */

import React, { useState } from 'react';
import {
  Search,
  AlertTriangle,
  TrendingUp,
  Building2,
  FileText,
  Clock,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Sparkles
} from 'lucide-react';

// ============================================================================
// Types
// ============================================================================

interface SearchResult {
  score: number;
  ticker: string;
  filing_type: string;
  filing_date: string;
  content: string;
  metadata?: {
    risk_severity?: number;
    risk_keyword_count?: number;
  };
}

interface SearchResponse {
  query: string;
  ticker: string;
  results: SearchResult[];
  total_results: number;
  search_time_ms: number;
}

interface TrendPoint {
  year: number;
  quarter?: number;
  filing_date: string;
  relevance_score: number;
  summary: string;
  key_excerpts: string[];
}

interface TrendResponse {
  ticker: string;
  query: string;
  period: string;
  trend_points: TrendPoint[];
  overall_trend: string;
  insights: string[];
}

interface SimilarCompany {
  ticker: string;
  similarity_score: number;
  common_themes: string[];
}

// ============================================================================
// Main Component
// ============================================================================

const SECSemanticSearch: React.FC = () => {
  const [searchMode, setSearchMode] = useState<'semantic' | 'risk' | 'trend' | 'similar'>('semantic');
  const [ticker, setTicker] = useState('AAPL');
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<SearchResponse | null>(null);
  const [trendResults, setTrendResults] = useState<TrendResponse | null>(null);
  const [similarCompanies, setSimilarCompanies] = useState<SimilarCompany[]>([]);
  const [expandedResults, setExpandedResults] = useState<Set<number>>(new Set());
  const [error, setError] = useState<string | null>(null);

  // Search parameters
  const [topK, setTopK] = useState(5);
  const [startYear, setStartYear] = useState(2020);
  const [endYear, setEndYear] = useState(2023);
  const [riskCategories, setRiskCategories] = useState<string[]>([]);

  const riskCategoryOptions = [
    'regulatory',
    'operational',
    'market',
    'legal',
    'financial',
    'technology',
    'reputational'
  ];

  // ============================================================================
  // API Calls
  // ============================================================================

  const handleSemanticSearch = async () => {
    if (!query.trim()) {
      setError('Please enter a search query');
      return;
    }

    setLoading(true);
    setError(null);
    setResults(null);

    try {
      const response = await fetch('/api/sec/semantic-search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ticker: ticker.toUpperCase(),
          query: query,
          top_k: topK
        })
      });

      if (!response.ok) {
        throw new Error(`Search failed: ${response.statusText}`);
      }

      const data: SearchResponse = await response.json();
      setResults(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed');
    } finally {
      setLoading(false);
    }
  };

  const handleRiskSearch = async () => {
    setLoading(true);
    setError(null);
    setResults(null);

    try {
      const response = await fetch('/api/sec/risk-search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ticker: ticker.toUpperCase(),
          risk_categories: riskCategories.length > 0 ? riskCategories : undefined,
          top_k: topK,
          severity_threshold: 0.3
        })
      });

      if (!response.ok) {
        throw new Error(`Risk search failed: ${response.statusText}`);
      }

      const data: SearchResponse = await response.json();
      setResults(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Risk search failed');
    } finally {
      setLoading(false);
    }
  };

  const handleTrendSearch = async () => {
    if (!query.trim()) {
      setError('Please enter a topic to track');
      return;
    }

    setLoading(true);
    setError(null);
    setTrendResults(null);

    try {
      const response = await fetch('/api/sec/trend-search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ticker: ticker.toUpperCase(),
          query: query,
          start_year: startYear,
          end_year: endYear,
          filing_type: '10-K'
        })
      });

      if (!response.ok) {
        throw new Error(`Trend search failed: ${response.statusText}`);
      }

      const data: TrendResponse = await response.json();
      setTrendResults(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Trend search failed');
    } finally {
      setLoading(false);
    }
  };

  const handleSimilarCompanies = async () => {
    setLoading(true);
    setError(null);
    setSimilarCompanies([]);

    try {
      const response = await fetch(
        `/api/sec/similar-companies/${ticker.toUpperCase()}?top_k=${topK}`
      );

      if (!response.ok) {
        throw new Error(`Similar companies search failed: ${response.statusText}`);
      }

      const data = await response.json();
      setSimilarCompanies(data.similar_companies);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Similar companies search failed');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    switch (searchMode) {
      case 'semantic':
        handleSemanticSearch();
        break;
      case 'risk':
        handleRiskSearch();
        break;
      case 'trend':
        handleTrendSearch();
        break;
      case 'similar':
        handleSimilarCompanies();
        break;
    }
  };

  const toggleExpand = (index: number) => {
    const newExpanded = new Set(expandedResults);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedResults(newExpanded);
  };

  const toggleRiskCategory = (category: string) => {
    setRiskCategories(prev =>
      prev.includes(category)
        ? prev.filter(c => c !== category)
        : [...prev, category]
    );
  };

  // ============================================================================
  // Render Helpers
  // ============================================================================

  const renderSearchModeSelector = () => (
    <div className="flex gap-2 mb-4">
      <button
        onClick={() => setSearchMode('semantic')}
        className={`flex items-center gap-2 px-4 py-2 rounded transition ${
          searchMode === 'semantic'
            ? 'bg-blue-600 text-white'
            : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
        }`}
      >
        <Sparkles className="w-4 h-4" />
        Semantic Search
      </button>
      <button
        onClick={() => setSearchMode('risk')}
        className={`flex items-center gap-2 px-4 py-2 rounded transition ${
          searchMode === 'risk'
            ? 'bg-red-600 text-white'
            : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
        }`}
      >
        <AlertTriangle className="w-4 h-4" />
        Risk Search
      </button>
      <button
        onClick={() => setSearchMode('trend')}
        className={`flex items-center gap-2 px-4 py-2 rounded transition ${
          searchMode === 'trend'
            ? 'bg-green-600 text-white'
            : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
        }`}
      >
        <TrendingUp className="w-4 h-4" />
        Trend Analysis
      </button>
      <button
        onClick={() => setSearchMode('similar')}
        className={`flex items-center gap-2 px-4 py-2 rounded transition ${
          searchMode === 'similar'
            ? 'bg-purple-600 text-white'
            : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
        }`}
      >
        <Building2 className="w-4 h-4" />
        Similar Companies
      </button>
    </div>
  );

  const renderSearchInputs = () => (
    <div className="space-y-4 mb-6">
      {/* Ticker */}
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

      {/* Query (for semantic, risk, trend) */}
      {searchMode !== 'similar' && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            {searchMode === 'semantic' ? 'Search Query' :
             searchMode === 'risk' ? 'Risk Query (optional)' :
             'Topic to Track'}
          </label>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={
              searchMode === 'semantic' ? 'What are the supply chain risks?' :
              searchMode === 'risk' ? 'Leave empty for all risks' :
              'artificial intelligence'
            }
            className="w-full px-4 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
          />
        </div>
      )}

      {/* Risk categories */}
      {searchMode === 'risk' && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Risk Categories (optional)
          </label>
          <div className="flex flex-wrap gap-2">
            {riskCategoryOptions.map(category => (
              <button
                key={category}
                onClick={() => toggleRiskCategory(category)}
                className={`px-3 py-1 rounded text-sm transition ${
                  riskCategories.includes(category)
                    ? 'bg-red-600 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                {category}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Year range for trend */}
      {searchMode === 'trend' && (
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Start Year
            </label>
            <input
              type="number"
              value={startYear}
              onChange={(e) => setStartYear(parseInt(e.target.value))}
              min={2010}
              max={2024}
              className="w-full px-4 py-2 border border-gray-300 rounded"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              End Year
            </label>
            <input
              type="number"
              value={endYear}
              onChange={(e) => setEndYear(parseInt(e.target.value))}
              min={2010}
              max={2024}
              className="w-full px-4 py-2 border border-gray-300 rounded"
            />
          </div>
        </div>
      )}

      {/* Top K */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Number of Results: {topK}
        </label>
        <input
          type="range"
          value={topK}
          onChange={(e) => setTopK(parseInt(e.target.value))}
          min={1}
          max={20}
          className="w-full"
        />
      </div>

      {/* Search button */}
      <button
        onClick={handleSearch}
        disabled={loading}
        className="w-full bg-blue-600 text-white px-6 py-3 rounded font-medium hover:bg-blue-700 disabled:bg-gray-400 transition flex items-center justify-center gap-2"
      >
        {loading ? (
          <>
            <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent" />
            Searching...
          </>
        ) : (
          <>
            <Search className="w-5 h-5" />
            Search
          </>
        )}
      </button>
    </div>
  );

  const renderResults = () => {
    if (!results || results.results.length === 0) return null;

    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">
            {results.total_results} Results for "{results.query}"
          </h3>
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <Clock className="w-4 h-4" />
            {results.search_time_ms.toFixed(0)}ms
          </div>
        </div>

        {results.results.map((result, index) => (
          <div
            key={index}
            className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition"
          >
            {/* Header */}
            <div className="flex items-start justify-between mb-2">
              <div className="flex items-center gap-3">
                <FileText className="w-5 h-5 text-blue-600" />
                <div>
                  <div className="font-semibold text-gray-900">
                    {result.ticker} - {result.filing_type}
                  </div>
                  <div className="text-sm text-gray-600">
                    Filed: {result.filing_date}
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-3">
                {result.metadata?.risk_severity && (
                  <div className="flex items-center gap-1">
                    <AlertTriangle className="w-4 h-4 text-red-600" />
                    <span className="text-sm font-medium text-red-600">
                      Risk: {(result.metadata.risk_severity * 100).toFixed(0)}%
                    </span>
                  </div>
                )}
                <div className="bg-green-100 text-green-800 px-2 py-1 rounded text-sm font-medium">
                  {(result.score * 100).toFixed(1)}% match
                </div>
              </div>
            </div>

            {/* Content preview */}
            <div className="text-gray-700 mb-2">
              {expandedResults.has(index) ? (
                <div className="whitespace-pre-wrap">{result.content}</div>
              ) : (
                <div className="line-clamp-3">{result.content}</div>
              )}
            </div>

            {/* Expand/collapse */}
            <button
              onClick={() => toggleExpand(index)}
              className="flex items-center gap-1 text-sm text-blue-600 hover:text-blue-800"
            >
              {expandedResults.has(index) ? (
                <>
                  <ChevronUp className="w-4 h-4" />
                  Show less
                </>
              ) : (
                <>
                  <ChevronDown className="w-4 h-4" />
                  Show more
                </>
              )}
            </button>
          </div>
        ))}
      </div>
    );
  };

  const renderTrendResults = () => {
    if (!trendResults) return null;

    const getTrendColor = (trend: string) => {
      switch (trend) {
        case 'increasing': return 'text-green-600';
        case 'decreasing': return 'text-red-600';
        default: return 'text-gray-600';
      }
    };

    return (
      <div className="space-y-6">
        <div>
          <h3 className="text-lg font-semibold mb-2">
            Trend: {trendResults.query} ({trendResults.period})
          </h3>
          <div className={`text-lg font-medium ${getTrendColor(trendResults.overall_trend)}`}>
            Overall Trend: {trendResults.overall_trend.toUpperCase()}
          </div>
        </div>

        {/* Insights */}
        {trendResults.insights.length > 0 && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h4 className="font-semibold mb-2">Insights</h4>
            <ul className="list-disc list-inside space-y-1">
              {trendResults.insights.map((insight, i) => (
                <li key={i} className="text-gray-700">{insight}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Timeline */}
        <div className="space-y-4">
          {trendResults.trend_points.map((point, index) => (
            <div key={index} className="border-l-4 border-blue-600 pl-4 py-2">
              <div className="flex items-center justify-between mb-1">
                <div className="font-semibold text-gray-900">
                  {point.year} {point.quarter && `Q${point.quarter}`}
                </div>
                <div className="text-sm text-gray-600">
                  Score: {(point.relevance_score * 100).toFixed(1)}%
                </div>
              </div>
              <div className="text-sm text-gray-700 mb-2">{point.summary}</div>
              {point.key_excerpts.map((excerpt, i) => (
                <div key={i} className="text-xs text-gray-600 italic mt-1">
                  "{excerpt}"
                </div>
              ))}
            </div>
          ))}
        </div>
      </div>
    );
  };

  const renderSimilarCompanies = () => {
    if (similarCompanies.length === 0) return null;

    return (
      <div className="space-y-4">
        <h3 className="text-lg font-semibold mb-4">
          Companies Similar to {ticker}
        </h3>

        {similarCompanies.map((company, index) => (
          <div
            key={index}
            className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Building2 className="w-6 h-6 text-purple-600" />
                <div>
                  <div className="font-semibold text-gray-900 text-lg">
                    {company.ticker}
                  </div>
                  <div className="text-sm text-gray-600">
                    {company.common_themes.join(', ')}
                  </div>
                </div>
              </div>
              <div className="bg-purple-100 text-purple-800 px-3 py-1 rounded font-medium">
                {(company.similarity_score * 100).toFixed(1)}% similar
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  };

  // ============================================================================
  // Main Render
  // ============================================================================

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2 flex items-center gap-2">
          <Sparkles className="w-8 h-8 text-blue-600" />
          SEC Semantic Search
        </h1>
        <p className="text-gray-600">
          AI-powered search for SEC filings using natural language
        </p>
      </div>

      {/* Search mode selector */}
      {renderSearchModeSelector()}

      {/* Search inputs */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        {renderSearchInputs()}
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 text-red-600" />
          <span className="text-red-800">{error}</span>
        </div>
      )}

      {/* Results */}
      <div className="bg-white rounded-lg shadow p-6">
        {searchMode === 'trend' && renderTrendResults()}
        {searchMode === 'similar' && renderSimilarCompanies()}
        {(searchMode === 'semantic' || searchMode === 'risk') && renderResults()}

        {!loading && !results && !trendResults && similarCompanies.length === 0 && (
          <div className="text-center text-gray-500 py-12">
            <Search className="w-16 h-16 mx-auto mb-4 text-gray-400" />
            <p>Enter your search criteria and click Search</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default SECSemanticSearch;

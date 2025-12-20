/**
 * Signal Detail Page
 *
 * Shows comprehensive information about a single trading signal:
 * - Full signal details
 * - Complete news article
 * - Deep Reasoning analysis (3-step CoT)
 * - Related signals from same analysis
 * - Bull/Bear cases
 */

import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  ArrowLeft,
  ExternalLink,
  TrendingUp,
  TrendingDown,
  Star,
  AlertTriangle,
  Brain,
  Newspaper,
  LinkIcon,
  Calendar,
  Zap
} from 'lucide-react';

// Types
interface Signal {
  id: number;
  ticker: string;
  action: string;
  signal_type: string;
  confidence: number;
  reasoning: string;
  generated_at: string;
  alert_sent: boolean;
  entry_price?: number;
  exit_price?: number;
  actual_return_pct?: number;
}

interface SignalDetail {
  signal: Signal;
  news_article: {
    id: number;
    title: string;
    content: string;
    url: string;
    source: string;
    published_date: string;
    crawled_at: string;
  };
  analysis: {
    id: number;
    theme: string;
    bull_case: string;
    bear_case: string;
    step1_direct_impact: string;
    step2_secondary_impact: string;
    step3_conclusion: string;
    model_name: string;
    analysis_duration_seconds: number;
    analyzed_at: string;
  };
  related_signals: Signal[];
}

// API URL - 환경변수에서 읽거나 자동 감지
const API_BASE_URL = import.meta.env.VITE_API_URL ||
  (window.location.hostname === 'localhost' ? 'http://localhost:8001' : `http://${window.location.hostname}:8001`);

export default function SignalDetail() {
  const { id } = useParams<{ id: string }>();
  const [data, setData] = useState<SignalDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchSignalDetail();
  }, [id]);

  const fetchSignalDetail = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/signals/${id}`);
      if (!response.ok) {
        throw new Error('Signal not found');
      }
      const data = await response.json();
      setData(data);
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch signal detail:', error);
      setError('Failed to load signal details');
      setLoading(false);
    }
  };

  const getSignalTypeColor = (type: string) => {
    const colors = {
      PRIMARY: 'text-blue-600 bg-blue-100',
      HIDDEN: 'text-purple-600 bg-purple-100',
      LOSER: 'text-red-600 bg-red-100'
    };
    return colors[type as keyof typeof colors] || 'text-gray-600 bg-gray-100';
  };

  const getActionColor = (action: string) => {
    const colors = {
      BUY: 'text-green-700 bg-green-100',
      SELL: 'text-red-700 bg-red-100',
      TRIM: 'text-yellow-700 bg-yellow-100',
      HOLD: 'text-gray-700 bg-gray-100'
    };
    return colors[action as keyof typeof colors] || 'text-gray-700 bg-gray-100';
  };

  const getSignalIcon = (type: string) => {
    const icons = {
      PRIMARY: TrendingUp,
      HIDDEN: Star,
      LOSER: AlertTriangle
    };
    return icons[type as keyof typeof icons] || TrendingUp;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
          <p className="text-gray-600">Loading signal details...</p>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <AlertTriangle className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Error</h2>
          <p className="text-gray-600 mb-4">{error || 'Signal not found'}</p>
          <Link to="/trading" className="text-blue-600 hover:text-blue-700 font-medium">
            ← Back to Dashboard
          </Link>
        </div>
      </div>
    );
  }

  const { signal, news_article, analysis, related_signals } = data;
  const SignalIcon = getSignalIcon(signal.signal_type);

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      {/* Header */}
      <div className="max-w-6xl mx-auto mb-6">
        <Link
          to="/trading"
          className="inline-flex items-center gap-2 text-blue-600 hover:text-blue-700 mb-4"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Dashboard
        </Link>

        <div className="bg-white rounded-lg shadow-lg p-8">
          {/* Signal Header */}
          <div className="flex items-start justify-between mb-6">
            <div className="flex items-center gap-4">
              <div className={`p-4 rounded-full ${getSignalTypeColor(signal.signal_type)}`}>
                <SignalIcon className="w-8 h-8" />
              </div>

              <div>
                <div className="flex items-center gap-3 mb-2">
                  <h1 className="text-4xl font-bold text-gray-900">{signal.ticker}</h1>
                  <span className={`px-4 py-2 rounded-lg font-semibold ${getActionColor(signal.action)}`}>
                    {signal.action}
                  </span>
                  <span className={`px-4 py-2 rounded-lg font-semibold ${getSignalTypeColor(signal.signal_type)}`}>
                    {signal.signal_type}
                  </span>
                </div>

                <p className="text-gray-600">
                  Generated on {new Date(signal.generated_at).toLocaleString()}
                </p>
              </div>
            </div>

            {/* Confidence */}
            <div className="text-right">
              <div className="text-sm text-gray-500 mb-1">Confidence</div>
              <div className="text-4xl font-bold text-green-600">
                {(signal.confidence * 100).toFixed(0)}%
              </div>
              {signal.alert_sent && (
                <div className="mt-2 text-sm text-blue-600 font-medium">
                  ✓ Alert Sent
                </div>
              )}
            </div>
          </div>

          {/* Signal Reasoning */}
          <div className="bg-gray-50 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-3">Signal Reasoning</h3>
            <p className="text-gray-700 leading-relaxed">{signal.reasoning}</p>
          </div>
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: News & Analysis */}
        <div className="lg:col-span-2 space-y-6">
          {/* News Article */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <div className="flex items-center gap-2 mb-4">
              <Newspaper className="w-5 h-5 text-blue-600" />
              <h2 className="text-xl font-bold text-gray-900">News Article</h2>
            </div>

            <div className="space-y-4">
              <div>
                <h3 className="text-2xl font-bold text-gray-900 mb-2">
                  {news_article.title}
                </h3>

                <div className="flex items-center gap-4 text-sm text-gray-500">
                  <span className="font-medium">{news_article.source}</span>
                  <span>•</span>
                  <span>{new Date(news_article.published_date).toLocaleDateString()}</span>
                  <span>•</span>
                  <a
                    href={news_article.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1 text-blue-600 hover:text-blue-700"
                  >
                    Read original <ExternalLink className="w-3 h-3" />
                  </a>
                </div>
              </div>

              <div className="prose max-w-none">
                <p className="text-gray-700 leading-relaxed whitespace-pre-wrap">
                  {news_article.content}
                </p>
              </div>
            </div>
          </div>

          {/* Deep Reasoning Analysis */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <div className="flex items-center gap-2 mb-4">
              <Brain className="w-5 h-5 text-purple-600" />
              <h2 className="text-xl font-bold text-gray-900">Deep Reasoning Analysis</h2>
              <span className="ml-auto text-sm text-gray-500">
                {analysis.model_name} • {analysis.analysis_duration_seconds.toFixed(2)}s
              </span>
            </div>

            {/* Theme */}
            <div className="mb-6 p-4 bg-purple-50 rounded-lg">
              <h3 className="text-sm font-medium text-purple-900 mb-1">Theme</h3>
              <p className="text-purple-800 font-semibold">{analysis.theme}</p>
            </div>

            {/* 3-Step Chain-of-Thought */}
            <div className="space-y-4 mb-6">
              <h3 className="text-lg font-semibold text-gray-900">Chain-of-Thought Reasoning</h3>

              {/* Step 1 */}
              <div className="border-l-4 border-blue-500 pl-4">
                <div className="text-sm font-medium text-blue-600 mb-1">Step 1: Direct Impact</div>
                <p className="text-gray-700">{analysis.step1_direct_impact}</p>
              </div>

              {/* Step 2 */}
              <div className="border-l-4 border-purple-500 pl-4">
                <div className="text-sm font-medium text-purple-600 mb-1">Step 2: Secondary Impact</div>
                <p className="text-gray-700">{analysis.step2_secondary_impact}</p>
              </div>

              {/* Step 3 */}
              <div className="border-l-4 border-green-500 pl-4">
                <div className="text-sm font-medium text-green-600 mb-1">Step 3: Conclusion</div>
                <p className="text-gray-700">{analysis.step3_conclusion}</p>
              </div>
            </div>

            {/* Bull/Bear Cases */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Bull Case */}
              <div className="bg-green-50 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <TrendingUp className="w-5 h-5 text-green-600" />
                  <h4 className="font-semibold text-green-900">Bull Case</h4>
                </div>
                <p className="text-green-800 text-sm">{analysis.bull_case}</p>
              </div>

              {/* Bear Case */}
              <div className="bg-red-50 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <TrendingDown className="w-5 h-5 text-red-600" />
                  <h4 className="font-semibold text-red-900">Bear Case</h4>
                </div>
                <p className="text-red-800 text-sm">{analysis.bear_case}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Related Signals */}
        <div className="space-y-6">
          {/* Performance (if available) */}
          {signal.actual_return_pct !== null && signal.actual_return_pct !== undefined && (
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Performance</h3>

              <div className="space-y-3">
                <div>
                  <div className="text-sm text-gray-500">Entry Price</div>
                  <div className="text-2xl font-bold text-gray-900">
                    ${signal.entry_price?.toFixed(2)}
                  </div>
                </div>

                {signal.exit_price && (
                  <div>
                    <div className="text-sm text-gray-500">Exit Price</div>
                    <div className="text-2xl font-bold text-gray-900">
                      ${signal.exit_price.toFixed(2)}
                    </div>
                  </div>
                )}

                <div>
                  <div className="text-sm text-gray-500">Return</div>
                  <div className={`text-3xl font-bold ${signal.actual_return_pct >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {signal.actual_return_pct >= 0 ? '+' : ''}{signal.actual_return_pct.toFixed(1)}%
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Related Signals */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <div className="flex items-center gap-2 mb-4">
              <LinkIcon className="w-5 h-5 text-gray-600" />
              <h3 className="text-lg font-semibold text-gray-900">Related Signals</h3>
            </div>

            {related_signals.length === 0 ? (
              <p className="text-gray-500 text-sm">No related signals from this analysis</p>
            ) : (
              <div className="space-y-3">
                {related_signals.map((relatedSignal) => {
                  const RelatedIcon = getSignalIcon(relatedSignal.signal_type);
                  return (
                    <Link
                      key={relatedSignal.id}
                      to={`/trading/signal/${relatedSignal.id}`}
                      className="block p-4 border border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition"
                    >
                      <div className="flex items-center gap-3 mb-2">
                        <RelatedIcon className="w-4 h-4 text-gray-600" />
                        <span className="font-bold text-gray-900">{relatedSignal.ticker}</span>
                        <span className={`px-2 py-1 rounded text-xs font-semibold ${getActionColor(relatedSignal.action)}`}>
                          {relatedSignal.action}
                        </span>
                      </div>

                      <div className="flex items-center gap-2 text-sm">
                        <span className={`px-2 py-1 rounded ${getSignalTypeColor(relatedSignal.signal_type)}`}>
                          {relatedSignal.signal_type}
                        </span>
                        <span className="text-gray-600">
                          {(relatedSignal.confidence * 100).toFixed(0)}%
                        </span>
                      </div>
                    </Link>
                  );
                })}
              </div>
            )}
          </div>

          {/* Metadata */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Metadata</h3>

            <div className="space-y-3 text-sm">
              <div>
                <div className="text-gray-500">Signal ID</div>
                <div className="font-mono text-gray-900">#{signal.id}</div>
              </div>

              <div>
                <div className="text-gray-500">Analysis ID</div>
                <div className="font-mono text-gray-900">#{analysis.id}</div>
              </div>

              <div>
                <div className="text-gray-500">Generated At</div>
                <div className="text-gray-900">
                  {new Date(signal.generated_at).toLocaleString()}
                </div>
              </div>

              <div>
                <div className="text-gray-500">Analyzed At</div>
                <div className="text-gray-900">
                  {new Date(analysis.analyzed_at).toLocaleString()}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

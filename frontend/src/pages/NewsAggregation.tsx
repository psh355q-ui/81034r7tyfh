/**
 * News Aggregation Tab
 * 
 * Features:
 * - RSS 크롤링 트리거
 * - AI 분석 트리거
 * - 뉴스 목록 (필터링)
 * - 분석 결과 표시
 * - 통계 대시보드
 */

import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Newspaper,
  RefreshCw,
  Brain,
  Filter,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Minus,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  Zap,
  BarChart2,
  Clock,
} from 'lucide-react';
import {
  getNewsArticles,
  getNewsStats,
  crawlRSSFeeds,
  analyzeUnanalyzedArticles,
  getNewsDetail,
  NewsArticle,
  NewsStats,
  NewsDetail,
  getSentimentColor,
  getSentimentBgColor,
  getUrgencyColor,
  formatMagnitude,
  getTimeAgo,
} from '../services/newsService';
import { RssCrawlProgress } from '../components/News/RssCrawlProgress';

export const NewsAggregation: React.FC = () => {
  const queryClient = useQueryClient();

  // State
  const [selectedArticle, setSelectedArticle] = useState<NewsDetail | null>(null);
  const [filters, setFilters] = useState({
    sentiment: '' as '' | 'positive' | 'negative' | 'neutral' | 'mixed',
    actionable_only: false,
    hours: 24,
  });
  const [showFilters, setShowFilters] = useState(false);
  const [crawlCount, setCrawlCount] = useState(0);
  const [showCrawlProgress, setShowCrawlProgress] = useState(false);

  // Queries
  const { data: articles, isLoading: articlesLoading, refetch: refetchArticles } = useQuery({
    queryKey: ['news-articles', filters],
    queryFn: () => getNewsArticles({
      limit: 50,
      hours: filters.hours,
      sentiment: filters.sentiment || undefined,
      actionable_only: filters.actionable_only,
    }),
    refetchInterval: 60000, // 1분마다 새로고침
  });

  const { data: stats, refetch: refetchStats } = useQuery({
    queryKey: ['news-stats'],
    queryFn: getNewsStats,
    refetchInterval: 60000,
  });

  // Crawl button handler
  const handleCrawl = () => {
    setShowCrawlProgress(true);
  };

  const handleCrawlComplete = () => {
    setShowCrawlProgress(false);
    refetchArticles();
    refetchStats();
  };

  // Mutations (keeping for backward compatibility)
  const crawlMutation = useMutation({
    mutationFn: () => crawlRSSFeeds(true),
    onSuccess: (result) => {
      setCrawlCount(result.articles_new);
      refetchArticles();
      refetchStats();
    },
  });

  const analyzeMutation = useMutation({
    mutationFn: (count: number) => analyzeUnanalyzedArticles(count),
    onSuccess: () => {
      refetchArticles();
      refetchStats();
    },
  });

  // Article detail query
  const handleArticleClick = async (articleId: number) => {
    try {
      const detail = await getNewsDetail(articleId);
      setSelectedArticle(detail);
    } catch (err) {
      console.error('Failed to load article detail:', err);
    }
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <Newspaper className="text-blue-600" size={28} />
          <div>
            <h1 className="text-2xl font-bold text-gray-900">뉴스 수집 및 분석</h1>
            <p className="text-sm text-gray-600">RSS 크롤링 + Gemini 무료 AI 분석</p>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center space-x-3">
          <button
            onClick={handleCrawl}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <RefreshCw size={16} />
            <span>RSS 크롤링</span>
          </button>

          <button
            onClick={() => analyzeMutation.mutate(10)}
            disabled={analyzeMutation.isPending || (stats?.unanalyzed_articles === 0)}
            className="flex items-center space-x-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50"
          >
            <Brain size={16} className={analyzeMutation.isPending ? 'animate-pulse' : ''} />
            <span>{analyzeMutation.isPending ? '분석 중...' : 'AI 분석 (10개)'}</span>
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <StatCard
            title="전체 기사"
            value={stats.total_articles}
            icon={<Newspaper className="text-blue-500" />}
          />
          <StatCard
            title="분석 완료"
            value={stats.analyzed_articles}
            subtitle={`미분석: ${stats.unanalyzed_articles}`}
            icon={<Brain className="text-purple-500" />}
          />
          <StatCard
            title="행동 가능"
            value={stats.actionable_count}
            icon={<TrendingUp className="text-green-500" />}
          />
          <StatCard
            title="Gemini 사용량"
            value={`${stats.gemini_usage.requests_used}/1500`}
            subtitle={stats.gemini_usage.cost}
            icon={<Zap className="text-yellow-500" />}
          />
        </div>
      )}

      {/* Sentiment Distribution */}
      {stats && (
        <div className="bg-white rounded-lg shadow p-4">
          <h3 className="font-semibold mb-3">감정 분포</h3>
          <div className="flex items-center space-x-4">
            <div className="flex-1">
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm text-green-600">긍정</span>
                <span className="text-sm font-medium">{stats.sentiment_distribution.positive}</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-green-500 h-2 rounded-full"
                  style={{
                    width: `${(stats.sentiment_distribution.positive / stats.analyzed_articles) * 100}%`
                  }}
                />
              </div>
            </div>
            <div className="flex-1">
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm text-gray-600">중립</span>
                <span className="text-sm font-medium">{stats.sentiment_distribution.neutral}</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-gray-500 h-2 rounded-full"
                  style={{
                    width: `${(stats.sentiment_distribution.neutral / stats.analyzed_articles) * 100}%`
                  }}
                />
              </div>
            </div>
            <div className="flex-1">
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm text-red-600">부정</span>
                <span className="text-sm font-medium">{stats.sentiment_distribution.negative}</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-red-500 h-2 rounded-full"
                  style={{
                    width: `${(stats.sentiment_distribution.negative / stats.analyzed_articles) * 100}%`
                  }}
                />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="bg-white rounded-lg shadow">
        <button
          onClick={() => setShowFilters(!showFilters)}
          className="w-full flex items-center justify-between p-4 hover:bg-gray-50"
        >
          <div className="flex items-center space-x-2">
            <Filter size={18} className="text-gray-600" />
            <span className="font-medium">필터</span>
          </div>
          {showFilters ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
        </button>

        {showFilters && (
          <div className="p-4 border-t border-gray-200 space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">감정</label>
                <select
                  value={filters.sentiment}
                  onChange={e => setFilters(prev => ({ ...prev, sentiment: e.target.value as any }))}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                >
                  <option value="">전체</option>
                  <option value="positive">긍정</option>
                  <option value="negative">부정</option>
                  <option value="neutral">중립</option>
                  <option value="mixed">혼합</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">기간</label>
                <select
                  value={filters.hours}
                  onChange={e => setFilters(prev => ({ ...prev, hours: parseInt(e.target.value) }))}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                >
                  <option value={6}>최근 6시간</option>
                  <option value={12}>최근 12시간</option>
                  <option value={24}>최근 24시간</option>
                  <option value={48}>최근 48시간</option>
                  <option value={168}>최근 1주일</option>
                </select>
              </div>

              <div className="flex items-end">
                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={filters.actionable_only}
                    onChange={e => setFilters(prev => ({ ...prev, actionable_only: e.target.checked }))}
                    className="rounded"
                  />
                  <span className="text-sm font-medium text-gray-700">행동 가능한 것만</span>
                </label>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Articles List */}
      <div className="bg-white rounded-lg shadow">
        <div className="p-4 border-b border-gray-200">
          <h3 className="font-semibold">뉴스 기사 ({articles?.length || 0}개)</h3>
        </div>

        <div className="divide-y divide-gray-200">
          {articlesLoading ? (
            <div className="p-8 text-center">
              <RefreshCw size={24} className="animate-spin mx-auto text-gray-400" />
              <p className="mt-2 text-gray-600">로딩 중...</p>
            </div>
          ) : articles?.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              <Newspaper size={48} className="mx-auto mb-4 text-gray-300" />
              <p>뉴스가 없습니다. RSS 크롤링을 실행해주세요.</p>
            </div>
          ) : (
            articles?.map(article => (
              <NewsArticleItem
                key={article.id}
                article={article}
                onClick={() => handleArticleClick(article.id)}
                isSelected={selectedArticle?.id === article.id}
              />
            ))
          )}
        </div>
      </div>

      {/* RSS Crawl Progress Modal */}
      <RssCrawlProgress
        isOpen={showCrawlProgress}
        onClose={handleCrawlComplete}
      />

      {/* Article Detail Modal */}
      {selectedArticle && (
        <NewsDetailModal
          article={selectedArticle}
          onClose={() => setSelectedArticle(null)}
        />
      )}

      {/* Crawl Result Toast */}
      {crawlMutation.isSuccess && crawlCount > 0 && (
        <div className="fixed bottom-6 right-6 bg-green-600 text-white px-6 py-3 rounded-lg shadow-lg animate-fade-in">
          ✅ {crawlCount}개의 새 기사를 수집했습니다!
        </div>
      )}

      {/* Analyze Result Toast */}
      {analyzeMutation.isSuccess && (
        <div className="fixed bottom-6 right-6 bg-purple-600 text-white px-6 py-3 rounded-lg shadow-lg animate-fade-in">
          🧠 {analyzeMutation.data?.analyzed}개의 기사를 분석했습니다!
        </div>
      )}
    </div>
  );
};

// ============================================================================
// Sub-components
// ============================================================================

interface StatCardProps {
  title: string;
  value: number | string;
  subtitle?: string;
  icon: React.ReactNode;
}

const StatCard: React.FC<StatCardProps> = ({ title, value, subtitle, icon }) => (
  <div className="bg-white rounded-lg shadow p-4">
    <div className="flex items-center justify-between">
      <div>
        <p className="text-sm text-gray-600">{title}</p>
        <p className="text-2xl font-bold mt-1">{value}</p>
        {subtitle && <p className="text-xs text-gray-500 mt-1">{subtitle}</p>}
      </div>
      <div className="p-3 bg-gray-50 rounded-lg">{icon}</div>
    </div>
  </div>
);

interface NewsArticleItemProps {
  article: NewsArticle;
  onClick: () => void;
  isSelected: boolean;
}

const NewsArticleItem: React.FC<NewsArticleItemProps> = ({ article, onClick, isSelected }) => (
  <div
    onClick={onClick}
    className={`p-4 hover:bg-gray-50 cursor-pointer transition-colors ${
      isSelected ? 'bg-blue-50' : ''
    }`}
  >
    <div className="flex items-start justify-between">
      <div className="flex-1">
        <h4 className="font-medium text-gray-900 line-clamp-2">{article.title}</h4>
        <div className="flex items-center space-x-3 mt-2 text-sm text-gray-500">
          <span>{article.source}</span>
          <span>•</span>
          <span>{article.published_at ? getTimeAgo(article.published_at) : '날짜 없음'}</span>
        </div>
        {article.keywords.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-2">
            {article.keywords.slice(0, 5).map((kw, i) => (
              <span key={i} className="px-2 py-0.5 text-xs bg-gray-100 text-gray-600 rounded">
                {kw}
              </span>
            ))}
          </div>
        )}
      </div>
      <div className="ml-4 flex flex-col items-end space-y-2">
        {article.has_analysis ? (
          <span className="px-2 py-1 text-xs bg-purple-100 text-purple-700 rounded">
            분석됨
          </span>
        ) : (
          <span className="px-2 py-1 text-xs bg-gray-100 text-gray-500 rounded">
            미분석
          </span>
        )}
        <ExternalLink size={14} className="text-gray-400" />
      </div>
    </div>
  </div>
);

interface NewsDetailModalProps {
  article: NewsDetail;
  onClose: () => void;
}

const NewsDetailModal: React.FC<NewsDetailModalProps> = ({ article, onClose }) => (
  <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
    <div className="bg-white rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 flex items-center justify-between">
        <h2 className="text-lg font-bold line-clamp-1">{article.title}</h2>
        <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
          ✕
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Meta */}
        <div className="flex items-center space-x-4 text-sm text-gray-600">
          <span>{article.source}</span>
          <span>•</span>
          <span>{article.published_at ? new Date(article.published_at).toLocaleString('ko-KR') : '날짜 없음'}</span>
          {article.authors.length > 0 && (
            <>
              <span>•</span>
              <span>저자: {article.authors.join(', ')}</span>
            </>
          )}
        </div>

        {/* Analysis (if available) */}
        {article.analysis && (
          <div className="bg-purple-50 border border-purple-200 rounded-lg p-4 space-y-4">
            <h3 className="font-semibold text-purple-900 flex items-center space-x-2">
              <Brain size={18} />
              <span>AI 분석 결과</span>
            </h3>

            {/* Sentiment */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-xs text-gray-600">감정</p>
                <p className={`font-semibold ${getSentimentColor(article.analysis.sentiment_overall)}`}>
                  {article.analysis.sentiment_overall.toUpperCase()}
                </p>
                <p className="text-sm text-gray-600">
                  점수: {article.analysis.sentiment_score.toFixed(2)}
                </p>
              </div>
              <div>
                <p className="text-xs text-gray-600">긴급도</p>
                <span className={`px-2 py-1 text-xs rounded ${getUrgencyColor(article.analysis.urgency)}`}>
                  {article.analysis.urgency.toUpperCase()}
                </span>
              </div>
              <div>
                <p className="text-xs text-gray-600">단기 영향</p>
                <p className="font-semibold">
                  {article.analysis.market_impact_short === 'bullish' && <TrendingUp className="text-green-600 inline" size={16} />}
                  {article.analysis.market_impact_short === 'bearish' && <TrendingDown className="text-red-600 inline" size={16} />}
                  {article.analysis.market_impact_short === 'neutral' && <Minus className="text-gray-600 inline" size={16} />}
                  {' '}{article.analysis.market_impact_short}
                </p>
              </div>
              <div>
                <p className="text-xs text-gray-600">영향도</p>
                <p className="font-semibold">{formatMagnitude(article.analysis.impact_magnitude)}</p>
              </div>
            </div>

            {/* Key Facts */}
            {article.analysis.key_facts.length > 0 && (
              <div>
                <p className="text-sm font-medium text-gray-700 mb-1">주요 사실</p>
                <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
                  {article.analysis.key_facts.map((fact, i) => (
                    <li key={i}>{fact}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Warnings */}
            {article.analysis.key_warnings.length > 0 && (
              <div className="bg-yellow-50 p-3 rounded">
                <p className="text-sm font-medium text-yellow-800 mb-1 flex items-center space-x-1">
                  <AlertTriangle size={14} />
                  <span>경고</span>
                </p>
                <ul className="list-disc list-inside text-sm text-yellow-700 space-y-1">
                  {article.analysis.key_warnings.map((warning, i) => (
                    <li key={i}>{warning}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Red Flags */}
            {article.analysis.red_flags.length > 0 && (
              <div className="bg-red-50 p-3 rounded">
                <p className="text-sm font-medium text-red-800 mb-1">🚩 Red Flags</p>
                <ul className="list-disc list-inside text-sm text-red-700 space-y-1">
                  {article.analysis.red_flags.map((flag, i) => (
                    <li key={i}>{flag}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Recommendation */}
            {article.analysis.recommendation && (
              <div className="bg-blue-50 p-3 rounded">
                <p className="text-sm font-medium text-blue-800 mb-1">💡 추천 행동</p>
                <p className="text-sm text-blue-700">{article.analysis.recommendation}</p>
              </div>
            )}

            {/* Actionable Badge */}
            {article.analysis.trading_actionable && (
              <div className="bg-green-100 border border-green-300 p-3 rounded">
                <p className="font-semibold text-green-800">✅ 행동 가능한 정보</p>
                <p className="text-sm text-green-700">
                  리스크 카테고리: {article.analysis.risk_category}
                </p>
              </div>
            )}

            {/* Tokens Used */}
            <div className="text-xs text-gray-500 flex items-center space-x-2">
              <Zap size={12} />
              <span>토큰 사용: {article.analysis.tokens_used} (비용: $0.00)</span>
              <Clock size={12} />
              <span>분석 시간: {new Date(article.analysis.analyzed_at).toLocaleString('ko-KR')}</span>
            </div>
          </div>
        )}

        {/* Related Tickers */}
        {article.related_tickers.length > 0 && (
          <div>
            <h3 className="font-semibold mb-2">관련 티커</h3>
            <div className="flex flex-wrap gap-2">
              {article.related_tickers.map((rel, i) => (
                <span
                  key={i}
                  className={`px-3 py-1 rounded-full text-sm font-medium ${
                    rel.sentiment > 0.2
                      ? 'bg-green-100 text-green-700'
                      : rel.sentiment < -0.2
                      ? 'bg-red-100 text-red-700'
                      : 'bg-gray-100 text-gray-700'
                  }`}
                >
                  {rel.ticker} ({(rel.relevance * 100).toFixed(0)}%)
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Content */}
        <div>
          <h3 className="font-semibold mb-2">본문</h3>
          <div className="bg-gray-50 p-4 rounded text-sm text-gray-700 whitespace-pre-wrap max-h-80 overflow-y-auto">
            {article.content_text || article.content_summary || '본문 없음'}
          </div>
        </div>

        {/* Link */}
        <a
          href={article.url}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center space-x-2 text-blue-600 hover:underline"
        >
          <ExternalLink size={16} />
          <span>원문 보기</span>
        </a>
      </div>
    </div>
  </div>
);

export default NewsAggregation;

/**
 * News Aggregation Page
 * 
 * Features:
 * - RSS Crawling
 * - AI Analysis with AnalysisConfigModal
 * - News List Display
 * - Statistics Dashboard
 */

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Newspaper,
  RefreshCw,
  Brain,
  Filter,
  TrendingUp,
  ChevronDown,
  ChevronUp,
  Zap,
  ExternalLink,
} from 'lucide-react';
import {
  getNewsArticles,
  getNewsStats,
  crawlRSSFeeds,
  getNewsDetail,
  NewsArticle,
  NewsStats,
  getTimeAgo,
  formatDateTimeKorean,
} from '../services/newsService';
import { RssCrawlProgress } from '../components/News/RssCrawlProgress';
import { AnalysisConfigModal } from '../components/News/AnalysisConfigModal';

export const NewsAggregation: React.FC = () => {
  const queryClient = useQueryClient();

  // State
  const [filters, setFilters] = useState({
    sentiment: '',
    actionable_only: false,
    hours: 24,
  });
  const [showFilters, setShowFilters] = useState(false);
  const [crawlCount, setCrawlCount] = useState(0);
  const [showCrawlProgress, setShowCrawlProgress] = useState(false);
  const [showAnalysisConfig, setShowAnalysisConfig] = useState(false);
  const [selectedArticle, setSelectedArticle] = useState<any>(null);

  // Queries
  const { data: articles, isLoading: articlesLoading } = useQuery({
    queryKey: ['news-articles', filters],
    queryFn: () => getNewsArticles({
      limit: 50,
      hours: filters.hours,
      sentiment: (filters.sentiment || undefined) as 'positive' | 'negative' | 'neutral' | 'mixed' | undefined,
      actionable_only: filters.actionable_only,
    }),
    refetchInterval: 60000,
  });

  const { data: stats } = useQuery({
    queryKey: ['news-stats'],
    queryFn: getNewsStats,
    refetchInterval: 60000,
  });

  // Mutations
  // Removed crawlMutation since RssCrawlProgress handles the crawling via SSE stream

  const handleCrawl = () => {
    // Directly open the progress modal which triggers the stream
    setShowCrawlProgress(true);
  };

  const handleCrawlComplete = () => {
    setShowCrawlProgress(false);
    // Refresh data after crawl completes
    queryClient.invalidateQueries({ queryKey: ['news-articles'] });
    queryClient.invalidateQueries({ queryKey: ['news-stats'] });
  };

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
            <p className="text-sm text-gray-600">RSS 크롤링 + Gemini AI 분석</p>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center space-x-3">
          <button
            onClick={handleCrawl}
            disabled={showCrawlProgress}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            <RefreshCw size={16} className={showCrawlProgress ? 'animate-spin' : ''} />
            <span>{showCrawlProgress ? '크롤링 중...' : 'RSS 크롤링'}</span>
          </button>

          <button
            onClick={() => setShowAnalysisConfig(true)}
            disabled={!stats || stats.unanalyzed_articles === 0}
            className="flex items-center space-x-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 transition-colors"
          >
            <Brain size={16} />
            <span>AI 분석 ({stats?.unanalyzed_articles || 0}개)</span>
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
                  onChange={e => setFilters(prev => ({ ...prev, sentiment: e.target.value }))}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                >
                  <option value="">전체</option>
                  <option value="positive">긍정</option>
                  <option value="negative">부정</option>
                  <option value="neutral">중립</option>
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
          ) : articles && articles.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              <Newspaper size={48} className="mx-auto mb-4 text-gray-300" />
              <p>뉴스가 없습니다. RSS 크롤링을 실행해주세요.</p>
            </div>
          ) : (
            articles?.map(article => (
              <ArticleItem key={article.id} article={article} onClick={() => handleArticleClick(article.id)} />
            ))
          )}
        </div>
      </div>

      {/* Modals */}
      <RssCrawlProgress
        isOpen={showCrawlProgress}
        onClose={handleCrawlComplete}
      />

      {showAnalysisConfig && (
        <AnalysisConfigModal
          isOpen={showAnalysisConfig}
          onClose={() => setShowAnalysisConfig(false)}
        />
      )}

      {/* Article Detail Modal */}
      {selectedArticle && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4" onClick={() => setSelectedArticle(null)}>
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
            <div className="p-6 space-y-4">
              <div className="flex items-start justify-between">
                <h2 className="text-xl font-bold text-gray-900 flex-1">{selectedArticle.title}</h2>
                <button onClick={() => setSelectedArticle(null)} className="text-gray-500 hover:text-gray-700 ml-4">✕</button>
              </div>

              {selectedArticle.analysis && (
                <div className="bg-purple-50 border border-purple-200 rounded-lg p-4 space-y-3">
                  <h3 className="font-semibold text-purple-900 flex items-center space-x-2">
                    <Brain size={18} />
                    <span>AI 분석 결과</span>
                  </h3>
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div>
                      <p className="text-gray-600">감정</p>
                      <p className="font-semibold">{selectedArticle.analysis.sentiment_overall}</p>
                    </div>
                    <div>
                      <p className="text-gray-600">긴급도</p>
                      <p className="font-semibold">{selectedArticle.analysis.urgency}</p>
                    </div>
                    <div>
                      <p className="text-gray-600">시장 영향</p>
                      <p className="font-semibold">{selectedArticle.analysis.market_impact_short}</p>
                    </div>
                    <div>
                      <p className="text-gray-600">행동 가능</p>
                      <p className="font-semibold">{selectedArticle.analysis.trading_actionable ? '✅ Yes' : '❌ No'}</p>
                    </div>
                  </div>
                </div>
              )}

              {/* Related Tickers */}
              {selectedArticle.related_tickers && selectedArticle.related_tickers.length > 0 && (
                <div>
                  <h3 className="font-semibold mb-2">관련 티커</h3>
                  <div className="flex flex-wrap gap-2">
                    {selectedArticle.related_tickers.map((rel: any, i: number) => (
                      <span
                        key={i}
                        className="px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-700"
                      >
                        ${rel.ticker}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              <div>
                <h3 className="font-semibold mb-2">본문</h3>
                <p className="text-gray-700 text-sm whitespace-pre-wrap">
                  {selectedArticle.content_text || selectedArticle.content_summary || '본문 없음'}
                </p>
              </div>

              {selectedArticle.url && (
                <a href={selectedArticle.url} target="_blank" rel="noopener noreferrer" className="flex items-center space-x-2 text-blue-600 hover:underline">
                  <ExternalLink size={16} />
                  <span>원문 보기</span>
                </a>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Success Toast - Show when recent articles found */}
      {!showCrawlProgress && crawlCount > 0 && (
        <div className="fixed bottom-6 right-6 bg-green-600 text-white px-6 py-3 rounded-lg shadow-lg animate-fade-in">
          ✅ {crawlCount}개의 기사가 처리되었습니다.
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

interface ArticleItemProps {
  article: NewsArticle;
  onClick: () => void;
}

const ArticleItem: React.FC<ArticleItemProps> = ({ article, onClick }) => (
  <div className="p-4 hover:bg-gray-50 transition-colors cursor-pointer" onClick={onClick}>
    <div className="flex items-start justify-between">
      <div className="flex-1">
        <h4 className="font-medium text-gray-900 line-clamp-2">{article.title}</h4>
        <div className="flex items-center space-x-3 mt-2 text-sm text-gray-500">
          <span>{article.source}</span>
          <span>•</span>
          {article.published_at ? (
            <span
              title={formatDateTimeKorean(article.published_at)}
              className="cursor-help"
            >
              {getTimeAgo(article.published_at)} ({formatDateTimeKorean(article.published_at)})
            </span>
          ) : (
            <span>날짜 없음</span>
          )}
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
        {article.url && (
          <a
            href={article.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-600 hover:underline"
            onClick={(e) => e.stopPropagation()}
          >
            <ExternalLink size={14} />
          </a>
        )}
      </div>
    </div>
  </div>
);

export default NewsAggregation;

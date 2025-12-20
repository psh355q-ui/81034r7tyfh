/**
 * AI Review Tab - Main Page
 *
 * 실시간 AI 분석 검토 및 히스토리 관리
 */

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  FileText,
  Clock,
  TrendingUp,
  AlertCircle,
  RefreshCw,
  Search,
  Filter,
} from 'lucide-react';
import {
  getAIReviews,
  getAIReviewDetail,
  searchAIReviews,
} from '../services/aiReviewApi';
import { AIReviewList } from '../components/AIReview/AIReviewList';
import { AIReviewDetail } from '../components/AIReview/AIReviewDetail';
import { TradingTermsDictionary } from '../components/AIReview/TradingTermsDictionary';

// Card Component (inline for simplicity)
const Card: React.FC<{
  children: React.ReactNode;
  className?: string;
}> = ({ children, className = '' }) => (
  <div className={`bg-white rounded-lg shadow-sm border border-gray-200 p-6 ${className}`}>
    {children}
  </div>
);

// Loading Spinner Component
const LoadingSpinner: React.FC<{ size?: 'sm' | 'md' | 'lg' }> = ({ size = 'md' }) => {
  const sizeClass = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
  }[size];

  return (
    <div className={`animate-spin rounded-full border-b-2 border-blue-600 ${sizeClass}`} />
  );
};

export const AIReviewPage: React.FC = () => {
  const [selectedReviewId, setSelectedReviewId] = useState<string | null>(null);
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState({
    ticker: '',
    action: '',
    minConviction: 0,
    hasChangesOnly: false,
  });

  // Fetch AI reviews list
  const {
    data: reviews,
    isLoading: reviewsLoading,
    error: reviewsError,
    refetch: refetchReviews,
  } = useQuery({
    queryKey: ['ai-reviews'],
    queryFn: () => getAIReviews({ limit: 50 }),
    refetchInterval: 15000, // Refresh every 15 seconds
  });

  // Fetch filtered reviews when filters are applied
  const {
    data: filteredReviewsData,
    isLoading: filteredLoading,
  } = useQuery({
    queryKey: ['ai-reviews-filtered', filters],
    queryFn: () =>
      searchAIReviews({
        ticker: filters.ticker || undefined,
        action: filters.action || undefined,
        min_conviction: filters.minConviction > 0 ? filters.minConviction / 100 : undefined,
        has_changes_only: filters.hasChangesOnly,
        limit: 50,
      }),
    enabled:
      !!filters.ticker ||
      !!filters.action ||
      filters.minConviction > 0 ||
      filters.hasChangesOnly,
  });

  // Fetch detailed review when selected
  const { data: detailedReview, isLoading: detailLoading } = useQuery({
    queryKey: ['ai-review-detail', selectedReviewId],
    queryFn: () => getAIReviewDetail(selectedReviewId!),
    enabled: !!selectedReviewId,
  });

  // Determine which reviews to display
  const displayReviews =
    filteredReviewsData?.reviews ??
    reviews?.reviews ??
    [];
  const isFiltering =
    !!filters.ticker ||
    !!filters.action ||
    filters.minConviction > 0 ||
    filters.hasChangesOnly;

  if (reviewsLoading && !isFiltering) {
    return (
      <div className="flex items-center justify-center h-screen">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (reviewsError) {
    return (
      <div className="p-6">
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          Error loading AI reviews. Please check if backend is running.
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6 bg-gray-50 min-h-screen">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">AI 실시간 검토</h1>
          <p className="text-gray-600 mt-1">
            AI가 분석한 내용을 실시간으로 확인하고 과거 내역과 비교하세요
          </p>
        </div>
        <button
          onClick={() => refetchReviews()}
          className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <RefreshCw size={18} />
          <span>새로고침</span>
        </button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card className="hover:shadow-lg transition-shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">총 분석 수</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">
                {reviews?.total_count ?? 0}
              </p>
            </div>
            <div className="p-3 bg-blue-100 rounded-full">
              <FileText className="text-blue-600" size={24} />
            </div>
          </div>
        </Card>

        <Card className="hover:shadow-lg transition-shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">오늘 분석</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">
                {reviews?.today_count ?? 0}
              </p>
            </div>
            <div className="p-3 bg-green-100 rounded-full">
              <Clock className="text-green-600" size={24} />
            </div>
          </div>
        </Card>

        <Card className="hover:shadow-lg transition-shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">평균 확신도</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">
                {((reviews?.avg_conviction ?? 0) * 100).toFixed(0)}%
              </p>
            </div>
            <div className="p-3 bg-purple-100 rounded-full">
              <TrendingUp className="text-purple-600" size={24} />
            </div>
          </div>
        </Card>

        <Card className="hover:shadow-lg transition-shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">변경 감지</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">
                {reviews?.changed_count ?? 0}
              </p>
            </div>
            <div className="p-3 bg-yellow-100 rounded-full">
              <AlertCircle className="text-yellow-600" size={24} />
            </div>
          </div>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">필터</h2>
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="flex items-center space-x-2 text-blue-600 hover:text-blue-800"
          >
            <Filter size={18} />
            <span>{showFilters ? '숨기기' : '표시'}</span>
          </button>
        </div>

        {showFilters && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                티커
              </label>
              <input
                type="text"
                value={filters.ticker}
                onChange={(e) =>
                  setFilters((prev) => ({ ...prev, ticker: e.target.value.toUpperCase() }))
                }
                placeholder="예: AAPL"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                액션
              </label>
              <select
                value={filters.action}
                onChange={(e) => setFilters((prev) => ({ ...prev, action: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="">전체</option>
                <option value="BUY">매수</option>
                <option value="SELL">매도</option>
                <option value="HOLD">관망</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                최소 확신도: {filters.minConviction}%
              </label>
              <input
                type="range"
                min="0"
                max="100"
                value={filters.minConviction}
                onChange={(e) =>
                  setFilters((prev) => ({
                    ...prev,
                    minConviction: parseInt(e.target.value),
                  }))
                }
                className="w-full"
              />
            </div>

            <div className="flex items-center">
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={filters.hasChangesOnly}
                  onChange={(e) =>
                    setFilters((prev) => ({ ...prev, hasChangesOnly: e.target.checked }))
                  }
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="text-sm font-medium text-gray-700">변경사항만</span>
              </label>
            </div>
          </div>
        )}

        {isFiltering && (
          <div className="mt-4 flex items-center justify-between">
            <span className="text-sm text-gray-600">
              {filteredLoading
                ? '검색 중...'
                : `${filteredReviewsData?.count ?? 0}개 결과`}
            </span>
            <button
              onClick={() =>
                setFilters({
                  ticker: '',
                  action: '',
                  minConviction: 0,
                  hasChangesOnly: false,
                })
              }
              className="text-sm text-red-600 hover:text-red-800"
            >
              필터 초기화
            </button>
          </div>
        )}
      </Card>

      {/* Main Content - Two Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column - Reviews List */}
        <Card>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold">실시간 검토 목록</h2>
            <span className="text-sm text-gray-500">
              {displayReviews.length}개 항목
            </span>
          </div>
          <AIReviewList
            reviews={displayReviews}
            selectedId={selectedReviewId}
            onSelect={setSelectedReviewId}
          />
        </Card>

        {/* Right Column - Detail Panel */}
        <Card>
          <h2 className="text-xl font-semibold mb-4">상세 분석</h2>
          {selectedReviewId ? (
            detailLoading ? (
              <div className="flex items-center justify-center py-12">
                <LoadingSpinner />
              </div>
            ) : (
              <AIReviewDetail review={detailedReview} />
            )
          ) : (
            <div className="flex items-center justify-center py-12 text-gray-500">
              <div className="text-center">
                <Search size={48} className="mx-auto mb-4 text-gray-300" />
                <p>좌측에서 분석 내역을 선택하세요</p>
              </div>
            </div>
          )}
        </Card>
      </div>

      {/* Trading Terms Dictionary */}
      <Card>
        <h2 className="text-xl font-semibold mb-4">매매 용어 사전</h2>
        <TradingTermsDictionary />
      </Card>
    </div>
  );
};

export default AIReviewPage;

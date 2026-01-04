/**
 * AI Review List Component
 *
 * AI 분석 목록을 카드 형태로 표시
 */

import React from 'react';
import { TrendingUp, TrendingDown, Minus, AlertCircle } from 'lucide-react';
import dayjs from 'dayjs';
import { AIReviewSummary } from '../../services/aiReviewApi';

interface AIReviewListProps {
  reviews: AIReviewSummary[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}

export const AIReviewList: React.FC<AIReviewListProps> = ({
  reviews,
  selectedId,
  onSelect,
}) => {
  if (reviews.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        분석 내역이 없습니다. AI 분석을 실행해보세요.
      </div>
    );
  }

  return (
    <div className="space-y-3 max-h-[600px] overflow-y-auto pr-2">
      {reviews.map((review) => (
        <div
          key={review.analysis_id}
          onClick={() => onSelect(review.analysis_id)}
          className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${selectedId === review.analysis_id
              ? 'border-blue-500 bg-blue-50'
              : 'border-gray-200 hover:border-blue-300 hover:bg-gray-50'
            }`}
        >
          {/* Header */}
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-2">
              <span className="text-lg font-bold text-blue-600">
                {review.ticker}
              </span>
              {review.has_changes && (
                <span className="px-2 py-0.5 text-xs font-semibold rounded bg-yellow-100 text-yellow-700">
                  변경됨
                </span>
              )}
            </div>
            <span className="text-xs text-gray-500">
              {dayjs(review.timestamp).fromNow()}
            </span>
          </div>

          {/* Action Badge */}
          <div className="flex items-center space-x-2 mb-2">
            {review.action === 'BUY' && (
              <span className="px-3 py-1 text-sm font-semibold rounded bg-green-100 text-green-700 flex items-center">
                <TrendingUp size={16} className="mr-1" />
                매수
              </span>
            )}
            {review.action === 'SELL' && (
              <span className="px-3 py-1 text-sm font-semibold rounded bg-red-100 text-red-700 flex items-center">
                <TrendingDown size={16} className="mr-1" />
                매도
              </span>
            )}
            {review.action === 'HOLD' && (
              <span className="px-3 py-1 text-sm font-semibold rounded bg-gray-100 text-gray-700 flex items-center">
                <Minus size={16} className="mr-1" />
                관망
              </span>
            )}

            {/* Conviction Bar */}
            <div className="flex-1">
              <div className="flex items-center space-x-2">
                <span className="text-xs text-gray-600">확신도:</span>
                <div className="flex-1 bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full transition-all ${review.conviction >= 0.7
                        ? 'bg-green-500'
                        : review.conviction >= 0.5
                          ? 'bg-yellow-500'
                          : 'bg-red-500'
                      }`}
                    style={{ width: `${review.conviction * 100}%` }}
                  />
                </div>
                <span className="text-xs font-semibold text-gray-700 min-w-[40px] text-right">
                  {(review.conviction * 100).toFixed(0)}%
                </span>
              </div>
            </div>
          </div>

          {/* Reasoning Preview */}
          <p className="text-sm text-gray-700 line-clamp-2 mb-2">
            {review.reasoning_preview}
          </p>

          {/* Footer */}
          <div className="flex items-center justify-between text-xs text-gray-500">
            <span className="flex items-center">
              <AlertCircle size={12} className="mr-1" />
              {review.model_name}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
};

/**
 * AI Review Detail Component
 *
 * 선택된 AI 분석의 상세 내용 표시 및 과거 비교
 */

import React, { useState } from 'react';
import { ChevronDown, ChevronUp, AlertTriangle, Target, DollarSign } from 'lucide-react';
import { AIReviewDetail as AIReviewDetailType } from '../../services/aiReviewApi';

interface AIReviewDetailProps {
  review?: AIReviewDetailType;
}

export const AIReviewDetail: React.FC<AIReviewDetailProps> = ({ review }) => {
  const [expandedSections, setExpandedSections] = useState<Set<string>>(
    new Set(['technical', 'fundamental'])
  );

  if (!review) {
    return (
      <div className="text-center py-8 text-gray-500">
        분석 내역을 불러오는 중...
      </div>
    );
  }

  const toggleSection = (section: string) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(section)) {
      newExpanded.delete(section);
    } else {
      newExpanded.add(section);
    }
    setExpandedSections(newExpanded);
  };

  return (
    <div className="space-y-4 max-h-[600px] overflow-y-auto pr-2">
      {/* Header Info */}
      <div className="p-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-2xl font-bold text-gray-900">{review.ticker}</h3>
          <span className="text-sm text-gray-600">
            {new Date(review.timestamp).toLocaleString('ko-KR')}
          </span>
        </div>

        <div className="flex items-center space-x-4">
          <span
            className={`px-4 py-2 text-sm font-bold rounded ${
              review.analysis.action === 'BUY'
                ? 'bg-green-500 text-white'
                : review.analysis.action === 'SELL'
                ? 'bg-red-500 text-white'
                : 'bg-gray-500 text-white'
            }`}
          >
            {review.analysis.action === 'BUY'
              ? '매수 추천'
              : review.analysis.action === 'SELL'
              ? '매도 추천'
              : '관망 추천'}
          </span>

          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-700">확신도:</span>
            <span className="text-lg font-bold text-gray-900">
              {(review.analysis.conviction * 100).toFixed(0)}%
            </span>
          </div>
        </div>
      </div>

      {/* Changes from Previous */}
      {review.diff_from_previous?.has_changes && (
        <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
          <div className="flex items-center space-x-2 mb-2">
            <AlertTriangle className="text-yellow-600" size={20} />
            <h4 className="font-semibold text-yellow-900">이전 분석 대비 변경 사항</h4>
          </div>

          {review.diff_from_previous.action_changed && (
            <p className="text-sm text-yellow-800 mb-2">
              ⚠️ 투자 의견이 변경되었습니다.
            </p>
          )}

          {review.diff_from_previous.conviction_change !== 0 && (
            <p className="text-sm text-yellow-800 mb-2">
              확신도 변화:{' '}
              <span
                className={
                  review.diff_from_previous.conviction_change > 0
                    ? 'text-green-700 font-semibold'
                    : 'text-red-700 font-semibold'
                }
              >
                {review.diff_from_previous.conviction_change > 0 ? '+' : ''}
                {(review.diff_from_previous.conviction_change * 100).toFixed(1)}%p
              </span>
            </p>
          )}

          <p className="text-sm text-gray-700 whitespace-pre-wrap">
            {review.diff_from_previous.reasoning_diff}
          </p>
        </div>
      )}

      {/* Main Reasoning */}
      <div className="p-4 bg-white border border-gray-200 rounded-lg">
        <h4 className="font-semibold text-gray-900 mb-2">분석 요약</h4>
        <p className="text-sm text-gray-700 whitespace-pre-wrap">
          {review.analysis.reasoning}
        </p>
      </div>

      {/* Price Targets */}
      {(review.analysis.target_price || review.analysis.stop_loss) && (
        <div className="grid grid-cols-2 gap-4">
          {review.analysis.target_price && (
            <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
              <div className="flex items-center space-x-2 mb-1">
                <Target size={16} className="text-green-700" />
                <p className="text-xs text-green-700 font-medium">목표가</p>
              </div>
              <p className="text-2xl font-bold text-green-900">
                ${review.analysis.target_price.toFixed(2)}
              </p>
            </div>
          )}

          {review.analysis.stop_loss && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
              <div className="flex items-center space-x-2 mb-1">
                <DollarSign size={16} className="text-red-700" />
                <p className="text-xs text-red-700 font-medium">손절가</p>
              </div>
              <p className="text-2xl font-bold text-red-900">
                ${review.analysis.stop_loss.toFixed(2)}
              </p>
            </div>
          )}
        </div>
      )}

      {/* Position Size */}
      <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <p className="text-sm text-blue-700 mb-1">권장 포지션 크기</p>
        <p className="text-xl font-bold text-blue-900">
          {(review.analysis.position_size * 100).toFixed(1)}% of portfolio
        </p>
      </div>

      {/* Risk Factors */}
      {review.analysis.risk_factors.length > 0 && (
        <div className="p-4 bg-orange-50 border border-orange-200 rounded-lg">
          <h4 className="font-semibold text-orange-900 mb-2 flex items-center">
            <AlertTriangle className="mr-2" size={18} />
            리스크 요인
          </h4>
          <ul className="list-disc list-inside space-y-1">
            {review.analysis.risk_factors.map((risk, index) => (
              <li key={index} className="text-sm text-orange-800">
                {risk}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Detailed Reasoning Sections */}
      <div className="space-y-2">
        {/* Technical Analysis */}
        <CollapsibleSection
          title="기술적 분석"
          isExpanded={expandedSections.has('technical')}
          onToggle={() => toggleSection('technical')}
        >
          <p className="text-sm text-gray-700 whitespace-pre-wrap">
            {review.detailed_reasoning.technical_analysis || '데이터 없음'}
          </p>
        </CollapsibleSection>

        {/* Fundamental Analysis */}
        <CollapsibleSection
          title="펀더멘털 분석"
          isExpanded={expandedSections.has('fundamental')}
          onToggle={() => toggleSection('fundamental')}
        >
          <p className="text-sm text-gray-700 whitespace-pre-wrap">
            {review.detailed_reasoning.fundamental_analysis || '데이터 없음'}
          </p>
        </CollapsibleSection>

        {/* Sentiment Analysis */}
        <CollapsibleSection
          title="시장 심리 분석"
          isExpanded={expandedSections.has('sentiment')}
          onToggle={() => toggleSection('sentiment')}
        >
          <p className="text-sm text-gray-700 whitespace-pre-wrap">
            {review.detailed_reasoning.sentiment_analysis || '데이터 없음'}
          </p>
        </CollapsibleSection>

        {/* Risk Assessment */}
        <CollapsibleSection
          title="리스크 평가"
          isExpanded={expandedSections.has('risk')}
          onToggle={() => toggleSection('risk')}
        >
          <p className="text-sm text-gray-700 whitespace-pre-wrap">
            {review.detailed_reasoning.risk_assessment || '데이터 없음'}
          </p>
        </CollapsibleSection>
      </div>

      {/* Model Info Footer */}
      <div className="p-3 bg-gray-50 border border-gray-200 rounded text-xs text-gray-600">
        <div className="flex items-center justify-between">
          <span>모델: {review.model_info.model_name}</span>
          <span>토큰: {review.model_info.tokens_used.toLocaleString()}</span>
          <span>응답 시간: {review.model_info.response_time_ms}ms</span>
        </div>
        {review.model_info.cost_usd !== undefined && review.model_info.cost_usd > 0 && (
          <div className="mt-1 text-center">
            <span className="text-green-600 font-medium">
              비용: ${review.model_info.cost_usd.toFixed(5)}
            </span>
          </div>
        )}
      </div>
    </div>
  );
};

// Collapsible Section Component
interface CollapsibleSectionProps {
  title: string;
  isExpanded: boolean;
  onToggle: () => void;
  children: React.ReactNode;
}

const CollapsibleSection: React.FC<CollapsibleSectionProps> = ({
  title,
  isExpanded,
  onToggle,
  children,
}) => {
  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between p-3 bg-gray-50 hover:bg-gray-100 transition-colors"
      >
        <span className="font-semibold text-gray-900">{title}</span>
        {isExpanded ? (
          <ChevronUp className="text-gray-600" size={20} />
        ) : (
          <ChevronDown className="text-gray-600" size={20} />
        )}
      </button>

      {isExpanded && <div className="p-4 bg-white">{children}</div>}
    </div>
  );
};

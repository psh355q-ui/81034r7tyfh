/**
 * Trading Terms Dictionary Component
 *
 * MASTER_GUIDE.md 기반 매매 용어 사전
 */

import React, { useState } from 'react';
import { Search, Book, ChevronRight, RefreshCw } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { getTradingTerms, TradingTerm } from '../../services/aiReviewApi';

export const TradingTermsDictionary: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [selectedTerm, setSelectedTerm] = useState<TradingTerm | null>(null);

  // Fetch trading terms from backend (parsed from MASTER_GUIDE.md)
  const { data: termsData, isLoading, error, refetch } = useQuery({
    queryKey: ['trading-terms'],
    queryFn: getTradingTerms,
    staleTime: 1000 * 60 * 60, // Cache for 1 hour
  });

  if (isLoading) {
    return (
      <div className="text-center py-8 text-gray-500">
        <RefreshCw className="animate-spin inline-block mr-2" size={20} />
        용어 사전을 불러오는 중...
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-8">
        <p className="text-red-500 mb-4">용어 사전 로드 실패</p>
        <button
          onClick={() => refetch()}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          재시도
        </button>
      </div>
    );
  }

  const terms = termsData?.terms ?? [];
  const categories = termsData?.categories ?? [];

  // Filter terms based on search and category
  const filteredTerms = terms.filter((term: TradingTerm) => {
    const matchesSearch =
      !searchQuery ||
      term.term.toLowerCase().includes(searchQuery.toLowerCase()) ||
      term.term_kr.includes(searchQuery) ||
      term.definition.includes(searchQuery);

    const matchesCategory = !selectedCategory || term.category === selectedCategory;

    return matchesSearch && matchesCategory;
  });

  return (
    <div className="space-y-4">
      {/* Search Bar */}
      <div className="relative">
        <Search
          className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400"
          size={20}
        />
        <input
          type="text"
          placeholder="용어 검색 (예: Position Sizing, 포지션 크기, Stop Loss)"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>

      {/* Category Filter */}
      <div className="flex flex-wrap gap-2">
        <button
          onClick={() => setSelectedCategory(null)}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            selectedCategory === null
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          전체 ({terms.length})
        </button>
        {categories.map((category: string) => {
          const count = terms.filter((t: TradingTerm) => t.category === category).length;
          return (
            <button
              key={category}
              onClick={() => setSelectedCategory(category)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                selectedCategory === category
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {category} ({count})
            </button>
          );
        })}
      </div>

      {/* Terms Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Terms List */}
        <div className="space-y-2 max-h-[400px] overflow-y-auto pr-2">
          {filteredTerms.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              검색 결과가 없습니다.
            </div>
          ) : (
            filteredTerms.map((term: TradingTerm) => (
              <button
                key={term.term}
                onClick={() => setSelectedTerm(term)}
                className={`w-full p-4 rounded-lg border text-left transition-all ${
                  selectedTerm?.term === term.term
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-blue-300 hover:bg-gray-50'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-semibold text-gray-900">{term.term_kr}</h4>
                    <p className="text-sm text-gray-600">{term.term}</p>
                  </div>
                  <ChevronRight
                    className={`text-gray-400 ${
                      selectedTerm?.term === term.term ? 'text-blue-600' : ''
                    }`}
                    size={20}
                  />
                </div>
                <p className="text-sm text-gray-700 mt-2 line-clamp-2">
                  {term.definition}
                </p>
              </button>
            ))
          )}
        </div>

        {/* Term Detail */}
        <div className="p-6 bg-gray-50 rounded-lg min-h-[400px]">
          {selectedTerm ? (
            <div className="space-y-4">
              <div>
                <div className="flex items-center space-x-2 mb-2">
                  <Book className="text-blue-600" size={24} />
                  <h3 className="text-2xl font-bold text-gray-900">
                    {selectedTerm.term_kr}
                  </h3>
                </div>
                <p className="text-sm text-gray-600 mb-1">{selectedTerm.term}</p>
                <span className="inline-block px-3 py-1 text-xs font-semibold rounded bg-blue-100 text-blue-700">
                  {selectedTerm.category}
                </span>
              </div>

              <div>
                <h4 className="font-semibold text-gray-900 mb-2">정의</h4>
                <p className="text-sm text-gray-700 whitespace-pre-wrap">
                  {selectedTerm.definition}
                </p>
              </div>

              {selectedTerm.example && (
                <div className="p-4 bg-white rounded-lg border border-gray-200">
                  <h4 className="font-semibold text-gray-900 mb-2">예시</h4>
                  <p className="text-sm text-gray-700 whitespace-pre-wrap italic">
                    {selectedTerm.example}
                  </p>
                </div>
              )}

              {selectedTerm.related_terms.length > 0 && (
                <div>
                  <h4 className="font-semibold text-gray-900 mb-2">연관 용어</h4>
                  <div className="flex flex-wrap gap-2">
                    {selectedTerm.related_terms.map((relatedTermName) => {
                      const related = terms.find(
                        (t: TradingTerm) => t.term === relatedTermName
                      );
                      return (
                        <button
                          key={relatedTermName}
                          onClick={() => related && setSelectedTerm(related)}
                          className="px-3 py-1 text-sm rounded bg-white border border-gray-300 hover:border-blue-500 hover:bg-blue-50 transition-colors"
                        >
                          {related?.term_kr ?? relatedTermName}
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-full text-gray-500">
              <Book size={48} className="mb-4 text-gray-300" />
              <p>좌측에서 용어를 선택하세요</p>
            </div>
          )}
        </div>
      </div>

      {/* Footer Stats */}
      <div className="text-center text-sm text-gray-500">
        총 <span className="font-semibold">{terms.length}</span>개 용어 |{' '}
        <span className="font-semibold">{categories.length}</span>개 카테고리
      </div>
    </div>
  );
};

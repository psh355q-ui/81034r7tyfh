/**
 * Logs Page
 * 시스템 로그 및 실행 이력 조회 페이지
 */

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Search, Filter, Download, RefreshCw, AlertCircle, Info, AlertTriangle, XCircle } from 'lucide-react';
import { getLogs, getLogStatistics, getLogLevels, getLogCategories, type LogFilters } from '../services/logsApi';
import { Card } from '../components/common/Card';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { Button } from '../components/common/Button';

export const Logs: React.FC = () => {
  const [filters, setFilters] = useState<LogFilters>({
    limit: 100,
    offset: 0,
    days: 7,
  });

  const [searchTerm, setSearchTerm] = useState('');

  // Fetch logs
  const {
    data: logsData,
    isLoading: logsLoading,
    refetch: refetchLogs,
  } = useQuery({
    queryKey: ['logs', filters],
    queryFn: () => getLogs(filters),
    refetchInterval: 10000, // 10초마다 자동 새로고침
  });

  // Fetch statistics
  const {
    data: stats,
    isLoading: statsLoading,
  } = useQuery({
    queryKey: ['log-statistics', filters.days],
    queryFn: () => getLogStatistics(filters.days || 7),
    refetchInterval: 30000, // 30초마다 자동 새로고침
  });

  // Fetch levels and categories
  const { data: levels = [] } = useQuery({
    queryKey: ['log-levels'],
    queryFn: getLogLevels,
  });

  const { data: categories = [] } = useQuery({
    queryKey: ['log-categories'],
    queryFn: getLogCategories,
  });

  const handleSearch = () => {
    setFilters(prev => ({ ...prev, search: searchTerm, offset: 0 }));
  };

  const handleFilterChange = (key: keyof LogFilters, value: any) => {
    setFilters(prev => ({ ...prev, [key]: value, offset: 0 }));
  };

  const handleClearFilters = () => {
    setFilters({ limit: 100, offset: 0, days: 7 });
    setSearchTerm('');
  };

  const handleExport = () => {
    if (!logsData?.logs) return;

    const csv = [
      ['Timestamp', 'Level', 'Category', 'Message'].join(','),
      ...logsData.logs.map(log => [
        log.timestamp,
        log.level,
        log.category,
        `"${log.message.replace(/"/g, '""')}"`,
      ].join(',')),
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `logs_${new Date().toISOString()}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'DEBUG': return 'text-gray-600 bg-gray-100';
      case 'INFO': return 'text-blue-600 bg-blue-100';
      case 'WARNING': return 'text-yellow-600 bg-yellow-100';
      case 'ERROR': return 'text-red-600 bg-red-100';
      case 'CRITICAL': return 'text-red-700 bg-red-200';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getLevelIcon = (level: string) => {
    switch (level) {
      case 'DEBUG': return <Info size={16} />;
      case 'INFO': return <Info size={16} />;
      case 'WARNING': return <AlertTriangle size={16} />;
      case 'ERROR': return <AlertCircle size={16} />;
      case 'CRITICAL': return <XCircle size={16} />;
      default: return <Info size={16} />;
    }
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString('ko-KR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  if (logsLoading || statsLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">System Logs</h1>
          <p className="text-gray-600 mt-1">실행 이력 및 시스템 로그</p>
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" size="sm" onClick={() => refetchLogs()}>
            <RefreshCw size={16} className="mr-1" />
            새로고침
          </Button>
          <Button variant="secondary" size="sm" onClick={handleExport}>
            <Download size={16} className="mr-1" />
            CSV 내보내기
          </Button>
        </div>
      </div>

      {/* Statistics Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <Card>
            <div className="text-center">
              <p className="text-sm text-gray-600 mb-1">총 로그 수</p>
              <p className="text-3xl font-bold text-gray-900">{stats.total_logs.toLocaleString()}</p>
            </div>
          </Card>

          <Card>
            <div className="text-center">
              <p className="text-sm text-gray-600 mb-1">에러</p>
              <p className="text-3xl font-bold text-red-600">{stats.errors_count.toLocaleString()}</p>
            </div>
          </Card>

          <Card>
            <div className="text-center">
              <p className="text-sm text-gray-600 mb-1">경고</p>
              <p className="text-3xl font-bold text-yellow-600">{stats.warnings_count.toLocaleString()}</p>
            </div>
          </Card>

          <Card>
            <div className="text-center">
              <p className="text-sm text-gray-600 mb-1">기간</p>
              <p className="text-3xl font-bold text-blue-600">{filters.days}일</p>
            </div>
          </Card>
        </div>
      )}

      {/* Filters */}
      <Card>
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <Filter size={20} className="text-gray-600" />
            <h3 className="text-lg font-semibold">필터</h3>
            <Button variant="secondary" size="sm" onClick={handleClearFilters} className="ml-auto">
              초기화
            </Button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Search */}
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">검색</label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                  placeholder="메시지 검색..."
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <Button onClick={handleSearch}>
                  <Search size={16} />
                </Button>
              </div>
            </div>

            {/* Level */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">레벨</label>
              <select
                value={filters.level || ''}
                onChange={(e) => handleFilterChange('level', e.target.value || undefined)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">전체</option>
                {levels.map(level => (
                  <option key={level} value={level}>{level}</option>
                ))}
              </select>
            </div>

            {/* Category */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">카테고리</label>
              <select
                value={filters.category || ''}
                onChange={(e) => handleFilterChange('category', e.target.value || undefined)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">전체</option>
                {categories.map(category => (
                  <option key={category} value={category}>{category}</option>
                ))}
              </select>
            </div>

            {/* Days */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">기간 (일)</label>
              <select
                value={filters.days || 7}
                onChange={(e) => handleFilterChange('days', Number(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value={1}>1일</option>
                <option value={3}>3일</option>
                <option value={7}>7일</option>
                <option value={14}>14일</option>
                <option value={30}>30일</option>
              </select>
            </div>

            {/* Limit */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">표시 개수</label>
              <select
                value={filters.limit || 100}
                onChange={(e) => handleFilterChange('limit', Number(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value={50}>50개</option>
                <option value={100}>100개</option>
                <option value={200}>200개</option>
                <option value={500}>500개</option>
              </select>
            </div>
          </div>
        </div>
      </Card>

      {/* Logs Table */}
      <Card>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold">
              로그 ({logsData?.total_count.toLocaleString() || 0}개)
            </h3>
          </div>

          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    시간
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    레벨
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    카테고리
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    메시지
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {logsData?.logs.map((log, index) => (
                  <tr key={index} className="hover:bg-gray-50">
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                      {formatTimestamp(log.timestamp)}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${getLevelColor(log.level)}`}>
                        {getLevelIcon(log.level)}
                        {log.level}
                      </span>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">
                      {log.category}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900">
                      <div className="max-w-2xl">
                        {log.message}
                        {log.details && (
                          <details className="mt-1">
                            <summary className="text-xs text-blue-600 cursor-pointer hover:underline">
                              상세 정보
                            </summary>
                            <pre className="mt-2 text-xs bg-gray-50 p-2 rounded overflow-x-auto">
                              {JSON.stringify(log.details, null, 2)}
                            </pre>
                          </details>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {(!logsData?.logs || logsData.logs.length === 0) && (
              <div className="text-center py-12 text-gray-500">
                로그가 없습니다.
              </div>
            )}
          </div>

          {/* Pagination */}
          {logsData && logsData.total_count > (filters.limit || 100) && (
            <div className="flex items-center justify-between pt-4 border-t">
              <Button
                variant="secondary"
                size="sm"
                disabled={(filters.offset || 0) === 0}
                onClick={() => handleFilterChange('offset', Math.max(0, (filters.offset || 0) - (filters.limit || 100)))}
              >
                이전
              </Button>
              <span className="text-sm text-gray-600">
                {(filters.offset || 0) + 1} - {Math.min((filters.offset || 0) + (filters.limit || 100), logsData.total_count)} / {logsData.total_count}
              </span>
              <Button
                variant="secondary"
                size="sm"
                disabled={(filters.offset || 0) + (filters.limit || 100) >= logsData.total_count}
                onClick={() => handleFilterChange('offset', (filters.offset || 0) + (filters.limit || 100))}
              >
                다음
              </Button>
            </div>
          )}
        </div>
      </Card>
    </div>
  );
};

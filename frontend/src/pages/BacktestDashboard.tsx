import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

// API 클라이언트
const API_BASE = '/api/backtest';

const fetchResults = async () => {
  const response = await fetch(`${API_BASE}/results`);
  if (!response.ok) throw new Error('Failed to fetch results');
  return response.json();
};

const fetchResult = async (id: string) => {
  const response = await fetch(`${API_BASE}/results/${id}`);
  if (!response.ok) throw new Error('Failed to fetch result');
  return response.json();
};

const runBacktest = async (config: any) => {
  const response = await fetch(`${API_BASE}/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config)
  });
  if (!response.ok) throw new Error('Failed to run backtest');
  return response.json();
};

const optimizeParams = async (request: any) => {
  const response = await fetch(`${API_BASE}/optimize`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request)
  });
  if (!response.ok) throw new Error('Failed to optimize');
  return response.json();
};

// 타입 정의
interface BacktestConfig {
  start_date: string;
  end_date: string;
  initial_capital: number;
  commission_rate: number;
  slippage_bps: number;
  max_holding_days: number;
  stop_loss_pct: number;
  take_profit_pct: number;
  base_position_size: number;
  max_position_size: number;
  min_sentiment_threshold: number;
  min_relevance_score: number;
  min_confidence: number;
  max_daily_trades: number;
  daily_loss_limit_pct: number;
}

interface BacktestResultSummary {
  id: string;
  name: string;
  status: string;
  created_at: string;
  total_return_pct?: number;
  sharpe_ratio?: number;
  max_drawdown_pct?: number;
  win_rate?: number;
  total_trades?: number;
}

// 메인 컴포넌트
export const BacktestDashboard: React.FC = () => {
  const queryClient = useQueryClient();
  const [selectedResult, setSelectedResult] = useState<string | null>(null);
  const [showNewBacktest, setShowNewBacktest] = useState(false);
  const [showOptimization, setShowOptimization] = useState(false);

  // 결과 목록 조회
  const { data: results, isLoading } = useQuery({
    queryKey: ['backtest-results'],
    queryFn: fetchResults,
    refetchInterval: 5000 // 5초마다 갱신
  });

  // 상세 결과 조회
  const { data: detailResult } = useQuery({
    queryKey: ['backtest-detail', selectedResult],
    queryFn: () => selectedResult ? fetchResult(selectedResult) : null,
    enabled: !!selectedResult
  });

  // 백테스트 실행 뮤테이션
  const runMutation = useMutation({
    mutationFn: runBacktest,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['backtest-results'] });
      setShowNewBacktest(false);
    }
  });

  return (
    <div className="min-h-screen bg-gray-100 p-6">
      <div className="max-w-7xl mx-auto">
        {/* 헤더 */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                📊 Signal Backtest Dashboard
              </h1>
              <p className="text-gray-600 mt-1">
                Phase 10: 뉴스 기반 거래 시그널 성과 검증
              </p>
            </div>
            <div className="flex space-x-3">
              <button
                onClick={() => setShowOptimization(true)}
                className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition"
              >
                🔧 파라미터 최적화
              </button>
              <button
                onClick={() => setShowNewBacktest(true)}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
              >
                ➕ 새 백테스트
              </button>
            </div>
          </div>
        </div>

        {/* 결과 목록 */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* 왼쪽: 백테스트 목록 */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow-sm p-4">
              <h2 className="text-lg font-semibold mb-4">백테스트 결과</h2>
              
              {isLoading ? (
                <div className="text-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                  <p className="text-gray-600 mt-2">로딩 중...</p>
                </div>
              ) : results?.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  백테스트 결과가 없습니다
                </div>
              ) : (
                <div className="space-y-3">
                  {results?.map((result: BacktestResultSummary) => (
                    <div
                      key={result.id}
                      onClick={() => setSelectedResult(result.id)}
                      className={`p-3 rounded-lg border cursor-pointer transition ${
                        selectedResult === result.id
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      <div className="flex justify-between items-start">
                        <div>
                          <h3 className="font-medium text-gray-900">{result.name}</h3>
                          <p className="text-xs text-gray-500">
                            {new Date(result.created_at).toLocaleString()}
                          </p>
                        </div>
                        <StatusBadge status={result.status} />
                      </div>
                      
                      {result.status === 'COMPLETED' && (
                        <div className="mt-2 grid grid-cols-2 gap-2 text-sm">
                          <div>
                            <span className="text-gray-600">수익률:</span>
                            <span className={`ml-1 font-medium ${
                              (result.total_return_pct || 0) >= 0 ? 'text-green-600' : 'text-red-600'
                            }`}>
                              {result.total_return_pct?.toFixed(2)}%
                            </span>
                          </div>
                          <div>
                            <span className="text-gray-600">샤프:</span>
                            <span className="ml-1 font-medium">
                              {result.sharpe_ratio?.toFixed(2)}
                            </span>
                          </div>
                          <div>
                            <span className="text-gray-600">승률:</span>
                            <span className="ml-1 font-medium">
                              {((result.win_rate || 0) * 100).toFixed(1)}%
                            </span>
                          </div>
                          <div>
                            <span className="text-gray-600">거래:</span>
                            <span className="ml-1 font-medium">
                              {result.total_trades}회
                            </span>
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* 오른쪽: 상세 결과 */}
          <div className="lg:col-span-2">
            {detailResult ? (
              <ResultDetail result={detailResult} />
            ) : (
              <div className="bg-white rounded-lg shadow-sm p-8 text-center">
                <div className="text-gray-400 text-5xl mb-4">📈</div>
                <p className="text-gray-600">
                  왼쪽에서 백테스트 결과를 선택하세요
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 새 백테스트 모달 */}
      {showNewBacktest && (
        <NewBacktestModal
          onClose={() => setShowNewBacktest(false)}
          onSubmit={(config) => runMutation.mutate(config)}
          isLoading={runMutation.isPending}
        />
      )}

      {/* 최적화 모달 */}
      {showOptimization && (
        <OptimizationModal onClose={() => setShowOptimization(false)} />
      )}
    </div>
  );
};

// 상태 배지
const StatusBadge: React.FC<{ status: string }> = ({ status }) => {
  const styles: Record<string, string> = {
    PENDING: 'bg-yellow-100 text-yellow-800',
    RUNNING: 'bg-blue-100 text-blue-800',
    COMPLETED: 'bg-green-100 text-green-800',
    FAILED: 'bg-red-100 text-red-800'
  };

  return (
    <span className={`px-2 py-1 rounded-full text-xs font-medium ${styles[status] || 'bg-gray-100'}`}>
      {status}
    </span>
  );
};

// 상세 결과 컴포넌트
const ResultDetail: React.FC<{ result: any }> = ({ result }) => {
  if (result.status === 'RUNNING' || result.status === 'PENDING') {
    return (
      <div className="bg-white rounded-lg shadow-sm p-8 text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
        <p className="text-gray-600 mt-4">백테스트 실행 중...</p>
        <p className="text-sm text-gray-500 mt-2">
          시작: {result.created_at ? new Date(result.created_at).toLocaleString() : 'N/A'}
        </p>
      </div>
    );
  }

  if (result.status === 'FAILED') {
    return (
      <div className="bg-white rounded-lg shadow-sm p-8">
        <div className="text-red-500 text-5xl text-center mb-4">❌</div>
        <h3 className="text-lg font-semibold text-red-600 text-center">백테스트 실패</h3>
        <p className="text-gray-600 text-center mt-2">{result.error}</p>
      </div>
    );
  }

  const data = result.result;

  return (
    <div className="space-y-4">
      {/* 주요 지표 카드 */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard
          title="총 수익률"
          value={`${data.total_return_pct.toFixed(2)}%`}
          color={data.total_return_pct >= 0 ? 'green' : 'red'}
          icon="💰"
        />
        <MetricCard
          title="샤프 비율"
          value={data.sharpe_ratio.toFixed(2)}
          color={data.sharpe_ratio >= 1 ? 'green' : data.sharpe_ratio >= 0.5 ? 'yellow' : 'red'}
          icon="📊"
        />
        <MetricCard
          title="최대 낙폭"
          value={`${data.max_drawdown_pct.toFixed(2)}%`}
          color={data.max_drawdown_pct >= -10 ? 'green' : data.max_drawdown_pct >= -20 ? 'yellow' : 'red'}
          icon="📉"
        />
        <MetricCard
          title="승률"
          value={`${(data.win_rate * 100).toFixed(1)}%`}
          color={data.win_rate >= 0.6 ? 'green' : data.win_rate >= 0.5 ? 'yellow' : 'red'}
          icon="🎯"
        />
      </div>

      {/* 거래 통계 */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h3 className="text-lg font-semibold mb-4">📊 거래 통계</h3>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          <StatItem label="총 거래 수" value={data.total_trades} />
          <StatItem label="성공 거래" value={data.winning_trades} />
          <StatItem label="실패 거래" value={data.losing_trades} />
          <StatItem label="평균 수익" value={`${data.avg_win_pct.toFixed(2)}%`} />
          <StatItem label="평균 손실" value={`${data.avg_loss_pct.toFixed(2)}%`} />
          <StatItem label="수익 팩터" value={data.profit_factor.toFixed(2)} />
        </div>
      </div>

      {/* 시그널 통계 */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h3 className="text-lg font-semibold mb-4">🔔 시그널 통계</h3>
        <div className="grid grid-cols-3 gap-4">
          <StatItem label="총 시그널" value={data.total_signals} />
          <StatItem label="실행됨" value={data.executed_signals} />
          <StatItem label="거부됨" value={data.rejected_signals} />
        </div>
        <div className="mt-4">
          <div className="h-4 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-green-500"
              style={{
                width: `${data.total_signals > 0 ? (data.executed_signals / data.total_signals) * 100 : 0}%`
              }}
            />
          </div>
          <p className="text-sm text-gray-600 mt-1">
            실행률: {data.total_signals > 0 ? ((data.executed_signals / data.total_signals) * 100).toFixed(1) : 0}%
          </p>
        </div>
      </div>

      {/* 일별 성과 */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h3 className="text-lg font-semibold mb-4">📅 일별 성과</h3>
        <div className="grid grid-cols-3 gap-4">
          <StatItem 
            label="최고의 날" 
            value={`${data.best_day_pct.toFixed(2)}%`}
            valueColor="text-green-600"
          />
          <StatItem 
            label="최악의 날" 
            value={`${data.worst_day_pct.toFixed(2)}%`}
            valueColor="text-red-600"
          />
          <StatItem 
            label="평균 일일 수익" 
            value={`${data.avg_daily_return_pct.toFixed(4)}%`}
          />
        </div>
      </div>

      {/* 개별 거래 목록 */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h3 className="text-lg font-semibold mb-4">💼 거래 내역</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b">
                <th className="text-left py-2">티커</th>
                <th className="text-left py-2">액션</th>
                <th className="text-right py-2">진입가</th>
                <th className="text-right py-2">청산가</th>
                <th className="text-right py-2">손익</th>
                <th className="text-right py-2">수익률</th>
              </tr>
            </thead>
            <tbody>
              {data.trades.slice(0, 10).map((trade: any, index: number) => (
                <tr key={index} className="border-b last:border-0">
                  <td className="py-2 font-medium">{trade.ticker}</td>
                  <td className="py-2">
                    <span className={trade.action === 'BUY' ? 'text-green-600' : 'text-red-600'}>
                      {trade.action}
                    </span>
                  </td>
                  <td className="py-2 text-right">${trade.entry_price.toFixed(2)}</td>
                  <td className="py-2 text-right">${trade.exit_price?.toFixed(2) || '-'}</td>
                  <td className={`py-2 text-right ${trade.pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    ${trade.pnl.toFixed(2)}
                  </td>
                  <td className={`py-2 text-right ${trade.pnl_pct >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {trade.pnl_pct.toFixed(2)}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {data.trades.length > 10 && (
            <p className="text-sm text-gray-500 mt-2">
              ... 외 {data.trades.length - 10}건의 거래
            </p>
          )}
        </div>
      </div>

      {/* 사용된 파라미터 */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h3 className="text-lg font-semibold mb-4">⚙️ 사용된 파라미터</h3>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm">
          {Object.entries(data.parameters).map(([key, value]) => (
            <div key={key} className="flex justify-between">
              <span className="text-gray-600">{key}:</span>
              <span className="font-medium">{String(value)}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

// 지표 카드
const MetricCard: React.FC<{
  title: string;
  value: string;
  color: 'green' | 'red' | 'yellow';
  icon: string;
}> = ({ title, value, color, icon }) => {
  const colorStyles = {
    green: 'bg-green-50 border-green-200 text-green-700',
    red: 'bg-red-50 border-red-200 text-red-700',
    yellow: 'bg-yellow-50 border-yellow-200 text-yellow-700'
  };

  return (
    <div className={`bg-white rounded-lg shadow-sm p-4 border ${colorStyles[color]}`}>
      <div className="text-2xl mb-2">{icon}</div>
      <div className="text-sm text-gray-600">{title}</div>
      <div className="text-xl font-bold">{value}</div>
    </div>
  );
};

// 통계 아이템
const StatItem: React.FC<{
  label: string;
  value: string | number;
  valueColor?: string;
}> = ({ label, value, valueColor = 'text-gray-900' }) => (
  <div>
    <div className="text-sm text-gray-600">{label}</div>
    <div className={`text-lg font-semibold ${valueColor}`}>{value}</div>
  </div>
);

// 새 백테스트 모달
const NewBacktestModal: React.FC<{
  onClose: () => void;
  onSubmit: (config: any) => void;
  isLoading: boolean;
}> = ({ onClose, onSubmit, isLoading }) => {
  const [name, setName] = useState('Backtest ' + new Date().toLocaleDateString());
  const [description, setDescription] = useState('');
  const [config, setConfig] = useState<BacktestConfig>({
    start_date: '2024-01-01',
    end_date: '2024-01-30',
    initial_capital: 100000,
    commission_rate: 0.00015,
    slippage_bps: 1.0,
    max_holding_days: 5,
    stop_loss_pct: 2.0,
    take_profit_pct: 5.0,
    base_position_size: 0.05,
    max_position_size: 0.10,
    min_sentiment_threshold: 0.7,
    min_relevance_score: 70,
    min_confidence: 0.7,
    max_daily_trades: 10,
    daily_loss_limit_pct: 2.0
  });

  const handleSubmit = () => {
    onSubmit({
      config,
      name,
      description,
      use_real_data: false // 샘플 데이터 사용
    });
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto m-4">
        <div className="p-6 border-b">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-semibold">➕ 새 백테스트 실행</h2>
            <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
              ✕
            </button>
          </div>
        </div>

        <div className="p-6 space-y-6">
          {/* 기본 정보 */}
          <div>
            <h3 className="font-medium mb-3">기본 정보</h3>
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">이름</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">설명</label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                  rows={2}
                />
              </div>
            </div>
          </div>

          {/* 기간 & 자본금 */}
          <div>
            <h3 className="font-medium mb-3">기간 & 자본금</h3>
            <div className="grid grid-cols-3 gap-3">
              <div>
                <label className="block text-sm text-gray-600 mb-1">시작일</label>
                <input
                  type="date"
                  value={config.start_date}
                  onChange={(e) => setConfig({ ...config, start_date: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-600 mb-1">종료일</label>
                <input
                  type="date"
                  value={config.end_date}
                  onChange={(e) => setConfig({ ...config, end_date: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-600 mb-1">초기 자본금</label>
                <input
                  type="number"
                  value={config.initial_capital}
                  onChange={(e) => setConfig({ ...config, initial_capital: parseFloat(e.target.value) })}
                  className="w-full px-3 py-2 border rounded-lg"
                />
              </div>
            </div>
          </div>

          {/* 거래 비용 */}
          <div>
            <h3 className="font-medium mb-3">거래 비용</h3>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm text-gray-600 mb-1">수수료율 (%)</label>
                <input
                  type="number"
                  step="0.001"
                  value={config.commission_rate * 100}
                  onChange={(e) => setConfig({ ...config, commission_rate: parseFloat(e.target.value) / 100 })}
                  className="w-full px-3 py-2 border rounded-lg"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-600 mb-1">슬리피지 (bps)</label>
                <input
                  type="number"
                  step="0.1"
                  value={config.slippage_bps}
                  onChange={(e) => setConfig({ ...config, slippage_bps: parseFloat(e.target.value) })}
                  className="w-full px-3 py-2 border rounded-lg"
                />
              </div>
            </div>
          </div>

          {/* 포지션 관리 */}
          <div>
            <h3 className="font-medium mb-3">포지션 관리</h3>
            <div className="grid grid-cols-3 gap-3">
              <div>
                <label className="block text-sm text-gray-600 mb-1">최대 보유일</label>
                <input
                  type="number"
                  value={config.max_holding_days}
                  onChange={(e) => setConfig({ ...config, max_holding_days: parseInt(e.target.value) })}
                  className="w-full px-3 py-2 border rounded-lg"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-600 mb-1">손절 (%)</label>
                <input
                  type="number"
                  step="0.5"
                  value={config.stop_loss_pct}
                  onChange={(e) => setConfig({ ...config, stop_loss_pct: parseFloat(e.target.value) })}
                  className="w-full px-3 py-2 border rounded-lg"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-600 mb-1">익절 (%)</label>
                <input
                  type="number"
                  step="0.5"
                  value={config.take_profit_pct}
                  onChange={(e) => setConfig({ ...config, take_profit_pct: parseFloat(e.target.value) })}
                  className="w-full px-3 py-2 border rounded-lg"
                />
              </div>
            </div>
          </div>

          {/* 시그널 파라미터 */}
          <div>
            <h3 className="font-medium mb-3">시그널 파라미터</h3>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm text-gray-600 mb-1">최소 신뢰도</label>
                <input
                  type="number"
                  step="0.05"
                  min="0"
                  max="1"
                  value={config.min_confidence}
                  onChange={(e) => setConfig({ ...config, min_confidence: parseFloat(e.target.value) })}
                  className="w-full px-3 py-2 border rounded-lg"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-600 mb-1">최소 감정 임계값</label>
                <input
                  type="number"
                  step="0.05"
                  min="0"
                  max="1"
                  value={config.min_sentiment_threshold}
                  onChange={(e) => setConfig({ ...config, min_sentiment_threshold: parseFloat(e.target.value) })}
                  className="w-full px-3 py-2 border rounded-lg"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-600 mb-1">기본 포지션 크기</label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  max="1"
                  value={config.base_position_size}
                  onChange={(e) => setConfig({ ...config, base_position_size: parseFloat(e.target.value) })}
                  className="w-full px-3 py-2 border rounded-lg"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-600 mb-1">최대 포지션 크기</label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  max="1"
                  value={config.max_position_size}
                  onChange={(e) => setConfig({ ...config, max_position_size: parseFloat(e.target.value) })}
                  className="w-full px-3 py-2 border rounded-lg"
                />
              </div>
            </div>
          </div>
        </div>

        <div className="p-6 border-t bg-gray-50 flex justify-end space-x-3">
          <button
            onClick={onClose}
            className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-100"
            disabled={isLoading}
          >
            취소
          </button>
          <button
            onClick={handleSubmit}
            disabled={isLoading}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {isLoading ? '실행 중...' : '백테스트 실행'}
          </button>
        </div>
      </div>
    </div>
  );
};

// 최적화 모달
const OptimizationModal: React.FC<{ onClose: () => void }> = ({ onClose }) => {
  const [isRunning, setIsRunning] = useState(false);
  const [result, setResult] = useState<any>(null);

  const handleOptimize = async () => {
    setIsRunning(true);
    try {
      const response = await optimizeParams({
        base_config: {
          start_date: '2024-01-01',
          end_date: '2024-01-30',
          initial_capital: 100000,
          commission_rate: 0.00015,
          slippage_bps: 1.0,
          max_holding_days: 5,
          stop_loss_pct: 2.0,
          take_profit_pct: 5.0,
          base_position_size: 0.05,
          max_position_size: 0.10,
          min_sentiment_threshold: 0.7,
          min_relevance_score: 70,
          min_confidence: 0.7,
          max_daily_trades: 10,
          daily_loss_limit_pct: 2.0
        },
        param_ranges: {
          min_sentiment_threshold: [0.6, 0.7, 0.8],
          stop_loss_pct: [1.5, 2.0, 2.5],
          take_profit_pct: [3.0, 5.0, 7.0]
        },
        optimization_metric: 'sharpe_ratio'
      });
      setResult(response);
    } catch (error) {
      console.error('Optimization failed:', error);
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-3xl w-full max-h-[90vh] overflow-y-auto m-4">
        <div className="p-6 border-b">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-semibold">🔧 파라미터 최적화</h2>
            <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
              ✕
            </button>
          </div>
        </div>

        <div className="p-6">
          {!result ? (
            <div className="text-center">
              <p className="text-gray-600 mb-4">
                Grid Search 방식으로 최적의 파라미터 조합을 찾습니다.
              </p>
              <div className="bg-gray-50 rounded-lg p-4 mb-6">
                <h4 className="font-medium mb-2">테스트할 파라미터:</h4>
                <ul className="text-sm text-gray-600 space-y-1">
                  <li>• 최소 감정 임계값: 0.6, 0.7, 0.8</li>
                  <li>• 손절 퍼센트: 1.5%, 2.0%, 2.5%</li>
                  <li>• 익절 퍼센트: 3.0%, 5.0%, 7.0%</li>
                  <li className="font-medium mt-2">총 27개 조합 테스트</li>
                </ul>
              </div>
              <button
                onClick={handleOptimize}
                disabled={isRunning}
                className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50"
              >
                {isRunning ? (
                  <span className="flex items-center">
                    <span className="animate-spin mr-2">⚙️</span>
                    최적화 실행 중...
                  </span>
                ) : (
                  '최적화 시작'
                )}
              </button>
            </div>
          ) : (
            <div className="space-y-6">
              {/* 최적 파라미터 */}
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <h3 className="font-semibold text-green-700 mb-3">🏆 최적 파라미터</h3>
                <div className="grid grid-cols-2 gap-3">
                  {Object.entries(result.best_params).map(([key, value]) => (
                    <div key={key} className="flex justify-between">
                      <span className="text-gray-600">{key}:</span>
                      <span className="font-medium">{String(value)}</span>
                    </div>
                  ))}
                </div>
                <div className="mt-3 pt-3 border-t border-green-200">
                  <span className="text-gray-600">최적 {result.optimization_metric}:</span>
                  <span className="ml-2 font-bold text-green-700">
                    {result.best_score.toFixed(4)}
                  </span>
                </div>
              </div>

              {/* 전체 결과 테이블 */}
              <div>
                <h3 className="font-semibold mb-3">📊 전체 결과 ({result.total_combinations}개 조합)</h3>
                <div className="overflow-x-auto max-h-60">
                  <table className="w-full text-sm">
                    <thead className="bg-gray-50 sticky top-0">
                      <tr>
                        <th className="text-left py-2 px-2">감정 임계값</th>
                        <th className="text-left py-2 px-2">손절%</th>
                        <th className="text-left py-2 px-2">익절%</th>
                        <th className="text-right py-2 px-2">샤프</th>
                        <th className="text-right py-2 px-2">수익률%</th>
                        <th className="text-right py-2 px-2">승률</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.all_results
                        .sort((a: any, b: any) => b.sharpe_ratio - a.sharpe_ratio)
                        .map((r: any, i: number) => (
                          <tr key={i} className={i === 0 ? 'bg-green-50' : ''}>
                            <td className="py-1 px-2">{r.params.min_sentiment_threshold}</td>
                            <td className="py-1 px-2">{r.params.stop_loss_pct}</td>
                            <td className="py-1 px-2">{r.params.take_profit_pct}</td>
                            <td className="py-1 px-2 text-right font-medium">
                              {r.sharpe_ratio.toFixed(3)}
                            </td>
                            <td className="py-1 px-2 text-right">
                              {r.total_return_pct.toFixed(2)}%
                            </td>
                            <td className="py-1 px-2 text-right">
                              {(r.win_rate * 100).toFixed(1)}%
                            </td>
                          </tr>
                        ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="p-6 border-t bg-gray-50 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-100"
          >
            닫기
          </button>
        </div>
      </div>
    </div>
  );
};

export default BacktestDashboard;

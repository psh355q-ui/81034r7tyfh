/**
 * GlobalMacroPanel - 글로벌 매크로 대시보드 컴포넌트
 * 
 * Phase F5: 프론트엔드 시각화
 * 
 * 기능:
 * - 국가별 리스크 점수 대시보드
 * - 나비효과 전파 시각화
 * - 실시간 매크로 알림
 */

import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getGlobalMarketMap, getCountryRisks } from '../services/api';

// 타입 정의
interface CountryRisk {
  country: string;
  countryName: string;
  score: number;
  level: 'low' | 'moderate' | 'elevated' | 'high';
  trend: 'improving' | 'stable' | 'declining';
  factors: string[];
}

interface MacroEvent {
  id: string;
  source: string;
  description: string;
  shock: number;
  timestamp: string;
  affectedAssets: string[];
}

interface ImpactPath {
  path: string[];
  impact: number;
  reason: string;
}

// 국가 정보
const COUNTRIES: Record<string, { name: string; flag: string }> = {
  US: { name: '미국', flag: '🇺🇸' },
  JP: { name: '일본', flag: '🇯🇵' },
  CN: { name: '중국', flag: '🇨🇳' },
  EU: { name: '유럽', flag: '🇪🇺' },
  KR: { name: '한국', flag: '🇰🇷' },
};

// 리스크 레벨 색상
const RISK_COLORS: Record<string, string> = {
  low: '#10B981',      // 녹색
  moderate: '#F59E0B',  // 노란색
  elevated: '#F97316',  // 주황색
  high: '#EF4444',     // 빨간색
};

// 리스크 게이지 컴포넌트 (Restyled)
const RiskGauge: React.FC<{ score: number; level: string }> = ({ score, level }) => {
  const color = RISK_COLORS[level] || '#6B7280';
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
        <div className="h-full rounded-full transition-all duration-500" style={{ width: `${score}%`, backgroundColor: color }} />
      </div>
      <span className="text-sm font-bold w-8 text-right text-gray-700">{score.toFixed(0)}</span>
    </div>
  );
};

// 국가 카드 컴포넌트 (Restyled)
const CountryCard: React.FC<{ risk: CountryRisk }> = ({ risk }) => {
  const country = COUNTRIES[risk.country] || { name: risk.country, flag: '🌍' };
  const trendIcon = { improving: '📈', stable: '➡️', declining: '📉' }[risk.trend];

  // Border color based on risk
  const borderClass = {
    low: 'border-l-green-500',
    moderate: 'border-l-yellow-500',
    elevated: 'border-l-orange-500',
    high: 'border-l-red-500'
  }[risk.level] || 'border-l-gray-400';

  return (
    <div className={`bg-gray-50 rounded-lg p-3 border-l-4 ${borderClass} hover:bg-gray-100 transition-colors`}>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="text-xl">{country.flag}</span>
          <span className="font-semibold text-gray-800">{country.name}</span>
        </div>
        <span className="text-sm">{trendIcon}</span>
      </div>
      <RiskGauge score={risk.score} level={risk.level} />
      <div className="flex flex-wrap gap-1 mt-2">
        {risk.factors.slice(0, 2).map((factor, idx) => (
          <span key={idx} className="text-[10px] px-2 py-0.5 bg-white border border-gray-200 rounded text-gray-500">
            {factor}
          </span>
        ))}
      </div>
    </div>
  );
};

// 이벤트 카드 컴포넌트 (Restyled)
const EventCard: React.FC<{ event: MacroEvent }> = ({ event }) => {
  const eventDate = new Date(event.timestamp);
  const dateStr = eventDate.toLocaleDateString('ko-KR', { month: '2-digit', day: '2-digit' }).replace(/\./g, '').replace(/\s/g, '');
  const timeStr = eventDate.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit', hour12: false });

  return (
    <div className="p-3 bg-gray-50 rounded-lg border border-gray-100 hover:shadow-sm transition-shadow">
      <div className="flex justify-between items-start mb-1">
        <span className="text-xs font-bold text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded">{event.source}</span>
        <span className="text-xs text-gray-400">{dateStr} {timeStr}</span>
      </div>
      <p className="text-sm text-gray-800 font-medium mb-2">{event.description}</p>
      <div className="flex justify-between items-center text-xs">
        <span className={`${event.shock > 0 ? 'text-green-600' : 'text-red-600'} font-bold`}>
          {event.shock > 0 ? '📈' : '📉'} Impact: {(event.shock * 100).toFixed(1)}%
        </span>
        <span className="text-gray-500">{event.affectedAssets.length} assets affected</span>
      </div>
    </div>
  );
};

// 영향 경로 시각화 컴포넌트 (Restyled)
const ImpactPathView: React.FC<{ paths: ImpactPath[] }> = ({ paths }) => {
  return (
    <div className="space-y-2">
      {paths.map((path, idx) => (
        <div key={idx} className="flex items-center justify-between p-2 bg-gray-50 rounded border border-gray-100 text-sm">
          <div className="flex flex-wrap items-center gap-1">
            {path.path.map((node, i) => (
              <React.Fragment key={i}>
                <span className="px-2 py-0.5 bg-white border border-gray-200 rounded text-xs text-gray-600">{node}</span>
                {i < path.path.length - 1 && <span className="text-gray-400 text-xs">→</span>}
              </React.Fragment>
            ))}
          </div>
          <span className={`font-bold ml-2 ${path.impact > 0 ? 'text-green-600' : 'text-red-600'}`}>
            {path.impact > 0 ? '+' : ''}{(path.impact * 100).toFixed(1)}%
          </span>
        </div>
      ))}
    </div>
  );
};

// 메인 컴포넌트
const GlobalMacroPanel: React.FC = () => {
  const [loading, setLoading] = useState(true);

  // Fetch Real Data
  const { data: marketMapData, isLoading: mapLoading } = useQuery({
    queryKey: ['globalMarketMap'],
    queryFn: getGlobalMarketMap,
    refetchInterval: 30000,
  });

  const { data: riskData, isLoading: riskLoading } = useQuery({
    queryKey: ['countryRisks'],
    queryFn: getCountryRisks,
    refetchInterval: 60000,
  });

  const isLoading = mapLoading || riskLoading;

  if (isLoading) {
    return <div className="flex justify-center p-12"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div></div>;
  }

  // Transform Backend Data to Frontend Interfaces
  const countryRisks: CountryRisk[] = riskData?.risks?.map((r: any) => ({
    country: r.country,
    countryName: COUNTRIES[r.country]?.name || r.country,
    score: r.score,
    level: r.score > 75 ? 'high' : r.score > 60 ? 'elevated' : r.score > 40 ? 'moderate' : 'low',
    trend: r.trend || 'stable',
    factors: Object.keys(r.components || {}).slice(0, 3) // Use component keys as factors
  })) || [];

  // Transform Graph Data to Events & Paths (Approximation for MVP)
  // Since backend does not return distinct "Events" list yet, we synthesize from high-change nodes
  const nodes = marketMapData?.nodes || [];
  const significantMoves = nodes.filter((n: any) => Math.abs(n.change_pct || 0) > 0.01); // > 1% change

  const recentEvents: MacroEvent[] = significantMoves.map((n: any, idx: number) => ({
    id: `evt-${idx}`,
    source: n.id,
    description: `${n.label} ${n.change_pct > 0 ? 'Surge' : 'Drop'} detected`,
    shock: n.change_pct || 0,
    timestamp: new Date().toISOString(),
    affectedAssets: [] // Would need impact trace from backend
  })).slice(0, 5) || [];

  // Fallback if no significant moves (Display placeholder or static top nodes)
  if (recentEvents.length === 0 && nodes.length > 0) {
    // Just show top nodes by absolute chg
    const sorted = [...nodes].sort((a: any, b: any) => Math.abs(b.change_pct || 0) - Math.abs(a.change_pct || 0));
    sorted.slice(0, 3).forEach((n: any, idx: number) => {
      recentEvents.push({
        id: `evt-static-${idx}`,
        source: n.id,
        description: `${n.label} Market Update`,
        shock: n.change_pct || 0,
        timestamp: new Date().toISOString(),
        affectedAssets: []
      });
    });
  }

  const impactPaths: ImpactPath[] = []; // Graph API doesn't return paths directly unless analyze-event is called

  // 평균 글로벌 리스크
  const avgRisk = riskData?.average_score || 50;

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-gray-900">🌍 글로벌 매크로 대시보드</h2>
          <p className="text-xs text-gray-500 mt-1">
            업데이트: {new Date().toLocaleString('ko-KR')} (실시간 데이터 연동)
          </p>
        </div>
        <div className="bg-gradient-to-r from-blue-500 to-indigo-600 text-white px-4 py-2 rounded-lg font-semibold shadow-sm">
          글로벌 평균 리스크: {avgRisk.toFixed(0)} / 100
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Country Risk Section */}
        <div className="bg-white rounded-lg shadow p-6 border border-gray-100">
          <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
            🏳️ 국가별 리스크 모니터
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {countryRisks.length > 0 ? countryRisks.map(risk => (
              <CountryCard key={risk.country} risk={risk} />
            )) : (
              <div className="col-span-2 text-center text-gray-400 py-4">No Data Available</div>
            )}
          </div>
        </div>

        {/* Events & Impact Section */}
        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow p-6 border border-gray-100">
            <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
              ⚡ 최근 시장 변동 (Top Movers)
            </h3>
            <div className="space-y-3">
              {recentEvents.length > 0 ? recentEvents.map(event => (
                <EventCard key={event.id} event={event} />
              )) : (<div className="text-center text-gray-400">No Significant Events</div>)}
            </div>
          </div>

          {/* Impact Path View - Optional/Placeholder for now as direct trace not implemented in GET /market-map */}
          {impactPaths.length > 0 && (
            <div className="bg-white rounded-lg shadow p-6 border border-gray-100">
              <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
                📊 충격 전파 경로 (나비효과)
              </h3>
              <ImpactPathView paths={impactPaths} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
};



export default GlobalMacroPanel;

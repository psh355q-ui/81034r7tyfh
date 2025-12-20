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

// 리스크 게이지 컴포넌트
const RiskGauge: React.FC<{ score: number; level: string }> = ({ score, level }) => {
    const color = RISK_COLORS[level] || '#6B7280';

    return (
        <div className="risk-gauge">
            <div className="gauge-background">
                <div
                    className="gauge-fill"
                    style={{
                        width: `${score}%`,
                        backgroundColor: color
                    }}
                />
            </div>
            <span className="gauge-value">{score.toFixed(0)}</span>
        </div>
    );
};

// 국가 카드 컴포넌트
const CountryCard: React.FC<{ risk: CountryRisk }> = ({ risk }) => {
    const country = COUNTRIES[risk.country] || { name: risk.country, flag: '🌍' };
    const trendIcon = {
        improving: '📈',
        stable: '➡️',
        declining: '📉'
    }[risk.trend];

    return (
        <div className={`country-card risk-${risk.level}`}>
            <div className="card-header">
                <span className="country-flag">{country.flag}</span>
                <span className="country-name">{country.name}</span>
                <span className="trend-icon">{trendIcon}</span>
            </div>

            <RiskGauge score={risk.score} level={risk.level} />

            <div className="risk-factors">
                {risk.factors.slice(0, 2).map((factor, idx) => (
                    <span key={idx} className="factor-tag">{factor}</span>
                ))}
            </div>
        </div>
    );
};

// 이벤트 카드 컴포넌트
const EventCard: React.FC<{ event: MacroEvent }> = ({ event }) => {
    const shockColor = event.shock > 0 ? '#10B981' : '#EF4444';
    const shockIcon = event.shock > 0 ? '📈' : '📉';

    return (
        <div className="event-card">
            <div className="event-header">
                <span className="event-source">{event.source}</span>
                <span className="event-time">
                    {new Date(event.timestamp).toLocaleTimeString('ko-KR')}
                </span>
            </div>
            <p className="event-description">{event.description}</p>
            <div className="event-impact">
                <span style={{ color: shockColor }}>
                    {shockIcon} {(event.shock * 100).toFixed(1)}%
                </span>
                <span className="affected-count">
                    {event.affectedAssets.length}개 자산 영향
                </span>
            </div>
        </div>
    );
};

// 영향 경로 시각화 컴포넌트
const ImpactPathView: React.FC<{ paths: ImpactPath[] }> = ({ paths }) => {
    return (
        <div className="impact-paths">
            <h4>📊 영향 전파 경로</h4>
            {paths.slice(0, 5).map((path, idx) => (
                <div key={idx} className="path-item">
                    <div className="path-nodes">
                        {path.path.map((node, nodeIdx) => (
                            <React.Fragment key={nodeIdx}>
                                <span className="path-node">{node}</span>
                                {nodeIdx < path.path.length - 1 && (
                                    <span className="path-arrow">→</span>
                                )}
                            </React.Fragment>
                        ))}
                    </div>
                    <div className="path-impact" style={{
                        color: path.impact > 0 ? '#10B981' : '#EF4444'
                    }}>
                        {path.impact > 0 ? '+' : ''}{(path.impact * 100).toFixed(1)}%
                    </div>
                </div>
            ))}
        </div>
    );
};

// 메인 컴포넌트
const GlobalMacroPanel: React.FC = () => {
    const [countryRisks, setCountryRisks] = useState<CountryRisk[]>([]);
    const [recentEvents, setRecentEvents] = useState<MacroEvent[]>([]);
    const [impactPaths, setImpactPaths] = useState<ImpactPath[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedEvent, setSelectedEvent] = useState<MacroEvent | null>(null);

    // 샘플 데이터 로드
    useEffect(() => {
        // 실제로는 API에서 가져옴
        const sampleRisks: CountryRisk[] = [
            { country: 'US', countryName: '미국', score: 55, level: 'moderate', trend: 'stable', factors: ['High rates (5.25%)', 'Inverted yield curve'] },
            { country: 'JP', countryName: '일본', score: 62, level: 'elevated', trend: 'declining', factors: ['Currency weak (85)', 'BOJ policy shift'] },
            { country: 'CN', countryName: '중국', score: 68, level: 'elevated', trend: 'declining', factors: ['Deflation risk (0.1%)', 'Property crisis'] },
            { country: 'EU', countryName: '유럽', score: 48, level: 'moderate', trend: 'stable', factors: ['Manufacturing weak', 'Energy transition'] },
            { country: 'KR', countryName: '한국', score: 42, level: 'moderate', trend: 'improving', factors: ['Semiconductor recovery', 'Currency stable'] },
        ];

        const sampleEvents: MacroEvent[] = [
            { id: '1', source: 'BOJ_RATE', description: 'BOJ unexpectedly raises rates by 25bps', shock: -0.3, timestamp: new Date().toISOString(), affectedAssets: ['NDX', 'KOSPI', 'NIKKEI'] },
            { id: '2', source: 'CRUDE_OIL', description: 'Oil price surges on OPEC+ cuts', shock: 0.15, timestamp: new Date(Date.now() - 3600000).toISOString(), affectedAssets: ['XLE', 'XOM', 'AIRLINE_SECTOR'] },
        ];

        const samplePaths: ImpactPath[] = [
            { path: ['JPY_STRENGTH', 'US_TECH_LIQUIDITY', 'NDX'], impact: -0.24, reason: 'Yen carry trade unwind' },
            { path: ['JPY_STRENGTH', 'GLOBAL_RISK_APPETITE', 'KOSPI'], impact: -0.15, reason: 'Risk-off sentiment' },
            { path: ['CRUDE_OIL', 'ENERGY_SECTOR'], impact: 0.27, reason: 'Revenue increase' },
            { path: ['CRUDE_OIL', 'AIRLINE_SECTOR'], impact: -0.24, reason: 'Fuel cost surge' },
        ];

        setCountryRisks(sampleRisks);
        setRecentEvents(sampleEvents);
        setImpactPaths(samplePaths);
        setLoading(false);
    }, []);

    if (loading) {
        return <div className="loading-spinner">로딩 중...</div>;
    }

    // 평균 글로벌 리스크
    const avgRisk = countryRisks.reduce((sum, r) => sum + r.score, 0) / countryRisks.length;

    return (
        <div className="global-macro-panel">
            <style>{`
        .global-macro-panel {
          padding: 24px;
          background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
          min-height: 100vh;
          color: #e0e0e0;
        }
        
        .panel-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 24px;
        }
        
        .panel-title {
          font-size: 24px;
          font-weight: 700;
          color: #fff;
        }
        
        .global-risk-badge {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          padding: 12px 24px;
          border-radius: 12px;
          font-weight: 600;
        }
        
        .section-title {
          font-size: 18px;
          font-weight: 600;
          margin: 24px 0 16px;
          color: #a0aec0;
        }
        
        .country-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 16px;
          margin-bottom: 24px;
        }
        
        .country-card {
          background: rgba(255, 255, 255, 0.05);
          border-radius: 12px;
          padding: 16px;
          border-left: 4px solid #6B7280;
        }
        
        .country-card.risk-low { border-left-color: #10B981; }
        .country-card.risk-moderate { border-left-color: #F59E0B; }
        .country-card.risk-elevated { border-left-color: #F97316; }
        .country-card.risk-high { border-left-color: #EF4444; }
        
        .card-header {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 12px;
        }
        
        .country-flag { font-size: 24px; }
        .country-name { flex: 1; font-weight: 600; }
        .trend-icon { font-size: 16px; }
        
        .risk-gauge {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 12px;
        }
        
        .gauge-background {
          flex: 1;
          height: 8px;
          background: rgba(255, 255, 255, 0.1);
          border-radius: 4px;
          overflow: hidden;
        }
        
        .gauge-fill {
          height: 100%;
          border-radius: 4px;
          transition: width 0.5s ease;
        }
        
        .gauge-value {
          font-weight: 600;
          min-width: 30px;
          text-align: right;
        }
        
        .risk-factors {
          display: flex;
          flex-wrap: wrap;
          gap: 4px;
        }
        
        .factor-tag {
          font-size: 11px;
          background: rgba(255, 255, 255, 0.1);
          padding: 2px 8px;
          border-radius: 4px;
          color: #a0aec0;
        }
        
        .events-section {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 24px;
        }
        
        .event-list {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }
        
        .event-card {
          background: rgba(255, 255, 255, 0.05);
          border-radius: 12px;
          padding: 16px;
          cursor: pointer;
          transition: transform 0.2s;
        }
        
        .event-card:hover {
          transform: translateX(4px);
          background: rgba(255, 255, 255, 0.08);
        }
        
        .event-header {
          display: flex;
          justify-content: space-between;
          margin-bottom: 8px;
        }
        
        .event-source {
          font-weight: 600;
          color: #667eea;
        }
        
        .event-time {
          font-size: 12px;
          color: #6B7280;
        }
        
        .event-description {
          font-size: 14px;
          margin-bottom: 8px;
        }
        
        .event-impact {
          display: flex;
          justify-content: space-between;
          font-size: 13px;
        }
        
        .affected-count {
          color: #6B7280;
        }
        
        .impact-paths {
          background: rgba(255, 255, 255, 0.05);
          border-radius: 12px;
          padding: 16px;
        }
        
        .impact-paths h4 {
          margin-bottom: 16px;
          color: #fff;
        }
        
        .path-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 8px 0;
          border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }
        
        .path-nodes {
          display: flex;
          align-items: center;
          gap: 4px;
          flex-wrap: wrap;
        }
        
        .path-node {
          background: rgba(102, 126, 234, 0.2);
          padding: 4px 8px;
          border-radius: 4px;
          font-size: 12px;
        }
        
        .path-arrow {
          color: #6B7280;
        }
        
        .path-impact {
          font-weight: 600;
          min-width: 60px;
          text-align: right;
        }
        
        .loading-spinner {
          display: flex;
          justify-content: center;
          align-items: center;
          height: 200px;
          color: #6B7280;
        }
      `}</style>

            <div className="panel-header">
                <h1 className="panel-title">🌍 글로벌 매크로 대시보드</h1>
                <div className="global-risk-badge">
                    평균 리스크: {avgRisk.toFixed(0)}점
                </div>
            </div>

            <h3 className="section-title">🏳️ 국가별 리스크</h3>
            <div className="country-grid">
                {countryRisks.map(risk => (
                    <CountryCard key={risk.country} risk={risk} />
                ))}
            </div>

            <h3 className="section-title">⚡ 최근 이벤트 & 영향</h3>
            <div className="events-section">
                <div className="event-list">
                    {recentEvents.map(event => (
                        <EventCard
                            key={event.id}
                            event={event}
                        />
                    ))}
                </div>
                <ImpactPathView paths={impactPaths} />
            </div>
        </div>
    );
};

export default GlobalMacroPanel;

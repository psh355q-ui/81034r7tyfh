/**
 * Mock Debate Sessions
 * 
 * 5개 티커의 샘플 AI 토론 데이터
 */

export interface DebateMessage {
    id: string;
    agent: 'trader' | 'risk' | 'analyst' | 'macro' | 'institutional' | 'pm';
    action: 'BUY' | 'SELL' | 'HOLD';
    confidence: number;
    reasoning: string;
    timestamp: Date;
    isDecision?: boolean;
}

export interface ConstitutionalResult {
    isValid: boolean;
    violations: string[];
    violatedArticles: string[];
}

export interface DebateSession {
    id: string;
    ticker: string;
    status: 'active' | 'completed' | 'pending';
    startedAt: Date;
    completedAt?: Date;

    messages: DebateMessage[];
    consensus: number;
    finalDecision?: {
        action: 'BUY' | 'SELL' | 'HOLD';
        confidence: number;
    };
    constitutionalResult?: ConstitutionalResult;
}

// Mock 토론 세션 데이터
export const MOCK_DEBATE_SESSIONS: DebateSession[] = [
    // NVDA - 진행중
    {
        id: 'debate-nvda-001',
        ticker: 'NVDA',
        status: 'active',
        startedAt: new Date('2025-12-17T00:30:00'),
        messages: [
            {
                id: 'msg-1',
                agent: 'trader',
                action: 'BUY',
                confidence: 0.92,
                reasoning: 'AI 칩 수요 폭발! Jensen Huang의 GTC 발표 후 기관 매수세 급증. Options Flow도 강한 콜 매수 신호',
                timestamp: new Date('2025-12-17T00:30:10')
            },
            {
                id: 'msg-2',
                agent: 'risk',
                action: 'HOLD',
                confidence: 0.68,
                reasoning: 'VIX 19.5로 상승세. 반도체 섹터 밸류에이션 역사적 고점 근접. 단기 과열 신호 감지',
                timestamp: new Date('2025-12-17T00:30:25')
            },
            {
                id: 'msg-3',
                agent: 'analyst',
                action: 'BUY',
                confidence: 0.85,
                reasoning: 'P/E 35배는 성장률 대비 합리적. 데이터센터 매출 YoY +200%. GPU 점유율 85% 유지',
                timestamp: new Date('2025-12-17T00:30:40')
            },
            {
                id: 'msg-4',
                agent: 'macro',
                action: 'BUY',
                confidence: 0.78,
                reasoning: 'Fed 금리 인하 시그널 → RISK_ON 체제. 달러 약세로 IT 섹터 수혜. 중국 경기부양책 긍정적',
                timestamp: new Date('2025-12-17T00:30:55')
            }
        ],
        consensus: 0.75,
        finalDecision: undefined
    },

    // TSLA - 완료 (SELL)
    {
        id: 'debate-tsla-002',
        ticker: 'TSLA',
        status: 'completed',
        startedAt: new Date('2025-12-16T15:20:00'),
        completedAt: new Date('2025-12-16T15:25:30'),
        messages: [
            {
                id: 'msg-t1',
                agent: 'trader',
                action: 'SELL',
                confidence: 0.75,
                reasoning: 'RSI 72 과매수 구간. 5일 연속 상승 후 피로도. Elon의 CEO 교체 루머로 변동성 급증',
                timestamp: new Date('2025-12-16T15:20:10')
            },
            {
                id: 'msg-t2',
                agent: 'risk',
                action: 'SELL',
                confidence: 0.88,
                reasoning: 'Put/Call Ratio 1.8 → 하방 베팅 증가. Delivery 숫자 컨센서스 미달 우려. 중국 경쟁 심화',
                timestamp: new Date('2025-12-16T15:20:25')
            },
            {
                id: 'msg-t3',
                agent: 'analyst',
                action: 'HOLD',
                confidence: 0.60,
                reasoning: 'Cybertruck 생산 램프업은 긍정적. 하지만 마진 압박과 가격 인하 정책이 수익성 훼손',
                timestamp: new Date('2025-12-16T15:20:40')
            },
            {
                id: 'msg-t4',
                agent: 'macro',
                action: 'SELL',
                confidence: 0.70,
                reasoning: 'EV 보조금 축소 리스크. 유가 하락으로 EV 매력도 감소. 자동차 섹터 전반 약세',
                timestamp: new Date('2025-12-16T15:20:55')
            },
            {
                id: 'msg-t5',
                agent: 'institutional',
                action: 'SELL',
                confidence: 0.82,
                reasoning: 'SEC 13F: ARK 매도 (-3.5%), Vanguard 비중 축소. 기관 투자자 이탈 가속화',
                timestamp: new Date('2025-12-16T15:21:10')
            },
            {
                id: 'msg-t6',
                agent: 'pm',
                action: 'SELL',
                confidence: 0.75,
                reasoning: '최종 합의: 4/5 agents SELL 투표. 단기 조정 전망',
                timestamp: new Date('2025-12-16T15:21:25'),
                isDecision: true
            }
        ],
        consensus: 0.80,
        finalDecision: {
            action: 'SELL',
            confidence: 0.75
        },
        constitutionalResult: {
            isValid: false,
            violations: ['제3조 위반: 인간 승인이 필요합니다'],
            violatedArticles: ['제3조: 인간 최종 결정권']
        }
    },

    // AAPL - 완료 (BUY)
    {
        id: 'debate-aapl-003',
        ticker: 'AAPL',
        status: 'completed',
        startedAt: new Date('2025-12-16T10:00:00'),
        completedAt: new Date('2025-12-16T10:05:45'),
        messages: [
            {
                id: 'msg-a1',
                agent: 'trader',
                action: 'BUY',
                confidence: 0.82,
                reasoning: 'iPhone 16 수요 예상 초과. 중국 시장 회복세. 서비스 매출 성장 지속',
                timestamp: new Date('2025-12-16T10:00:10')
            },
            {
                id: 'msg-a2',
                agent: 'risk',
                action: 'BUY',
                confidence: 0.75,
                reasoning: 'Beta 0.8로 방어적. 캐시 플로우 안정적. 배당 + 자사주 매입으로 주주 환원',
                timestamp: new Date('2025-12-16T10:00:25')
            },
            {
                id: 'msg-a3',
                agent: 'analyst',
                action: 'BUY',
                confidence: 0.88,
                reasoning: 'P/E 28배 합리적. Vision Pro 성장 잠재력. AI 칩 자체 개발로 마진 개선',
                timestamp: new Date('2025-12-16T10:00:40')
            },
            {
                id: 'msg-a4',
                agent: 'macro',
                action: 'BUY',
                confidence: 0.70,
                reasoning: 'Safe Haven 자산으로 재평가. 불확실성 시기 방어주 선호. 달러 약세 수혜',
                timestamp: new Date('2025-12-16T10:00:55')
            },
            {
                id: 'msg-a5',
                agent: 'institutional',
                action: 'BUY',
                confidence: 0.85,
                reasoning: 'Berkshire Hathaway 홀딩 유지. 워렌 버핏의 신뢰. FAANG 중 가장 안정적',
                timestamp: new Date('2025-12-16T10:01:10')
            },
            {
                id: 'msg-a6',
                agent: 'pm',
                action: 'BUY',
                confidence: 0.80,
                reasoning: '만장일치 BUY 합의 (5/5). 장기 보유 추천',
                timestamp: new Date('2025-12-16T10:01:25'),
                isDecision: true
            }
        ],
        consensus: 1.0,
        finalDecision: {
            action: 'BUY',
            confidence: 0.80
        },
        constitutionalResult: {
            isValid: false,
            violations: ['제3조 위반: 인간 승인이 필요합니다'],
            violatedArticles: ['제3조: 인간 최종 결정권']
        }
    },

    // MSFT - 대기중
    {
        id: 'debate-msft-004',
        ticker: 'MSFT',
        status: 'pending',
        startedAt: new Date('2025-12-17T01:00:00'),
        messages: [],
        consensus: 0
    },

    // GOOGL - 대기중
    {
        id: 'debate-googl-005',
        ticker: 'GOOGL',
        status: 'pending',
        startedAt: new Date('2025-12-17T01:15:00'),
        messages: [],
        consensus: 0
    }
];

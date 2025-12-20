/**
 * CEO Analysis Page
 * CEO 발언 분석 및 시각화 페이지 (Phase 15)
 */

import React, { useState } from 'react';
import {
    MessageSquare,
    TrendingUp,
    TrendingDown,
    Minus,
    AlertTriangle,
    Search,
    Calendar,
    BarChart3,
} from 'lucide-react';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Input } from '../components/common/Input';
import { Badge } from '../components/common/Badge';

// Types
interface CEOQuote {
    text: string;
    quote_type: string;
    source: string;
    fiscal_period?: string;
    sentiment?: number;
    published_at: string;
}

interface ToneShift {
    direction: 'MORE_OPTIMISTIC' | 'SIMILAR' | 'MORE_PESSIMISTIC';
    magnitude: number;
    signal: string;
    is_significant: boolean;
    key_changes: string[];
}

interface SimilarStatement {
    date: string;
    statement: string;
    similarity: number;
    outcome?: string;
    source: string;
}

export const CEOAnalysis: React.FC = () => {
    const [ticker, setTicker] = useState('');
    const [selectedQuote, setSelectedQuote] = useState<CEOQuote | null>(null);

    // Mock data for demonstration
    const mockQuotes: CEOQuote[] = [
        {
            text: "We believe that our AI strategy will drive significant growth in the coming quarters.",
            quote_type: "forward_looking",
            source: "sec_filing",
            fiscal_period: "2024-Q3",
            sentiment: 0.75,
            published_at: "2024-11-01T00:00:00Z"
        },
        {
            text: "Our strategy focuses on expanding our data center business and AI capabilities.",
            quote_type: "strategy",
            source: "sec_filing",
            fiscal_period: "2024-Q3",
            sentiment: 0.65,
            published_at: "2024-11-01T00:00:00Z"
        },
        {
            text: "We face challenges in the competitive landscape and supply chain disruptions.",
            quote_type: "risk_mention",
            source: "sec_filing",
            fiscal_period: "2024-Q3",
            sentiment: -0.3,
            published_at: "2024-11-01T00:00:00Z"
        },
    ];

    const mockToneShift: ToneShift = {
        direction: "MORE_OPTIMISTIC",
        magnitude: 0.45,
        signal: "POSITIVE",
        is_significant: true,
        key_changes: [
            "Confidence: MEDIUM → HIGH",
            "New opportunities: AI expansion, Data center growth"
        ]
    };

    const mockSimilarStatements: SimilarStatement[] = [
        {
            date: "2023-Q2",
            statement: "We expect strong AI demand to continue driving our growth.",
            similarity: 0.92,
            outcome: "Stock +18% in 3M",
            source: "sec_filing"
        },
        {
            date: "2022-Q4",
            statement: "Our AI strategy positions us well for future growth opportunities.",
            similarity: 0.85,
            outcome: "Stock +12% in 3M",
            source: "sec_filing"
        },
    ];

    const getQuoteTypeColor = (type: string) => {
        switch (type) {
            case 'forward_looking': return 'info';
            case 'strategy': return 'success';
            case 'risk_mention': return 'warning';
            case 'opportunity': return 'success';
            default: return 'default';
        }
    };

    const getQuoteTypeIcon = (type: string) => {
        switch (type) {
            case 'forward_looking': return <TrendingUp size={16} />;
            case 'strategy': return <BarChart3 size={16} />;
            case 'risk_mention': return <AlertTriangle size={16} />;
            case 'opportunity': return <TrendingUp size={16} />;
            default: return <MessageSquare size={16} />;
        }
    };

    const getToneShiftIcon = (direction: string) => {
        switch (direction) {
            case 'MORE_OPTIMISTIC': return <TrendingUp className="text-green-500" size={24} />;
            case 'MORE_PESSIMISTIC': return <TrendingDown className="text-red-500" size={24} />;
            default: return <Minus className="text-gray-500" size={24} />;
        }
    };

    const getSentimentColor = (sentiment: number) => {
        if (sentiment >= 0.5) return 'bg-green-500';
        if (sentiment >= 0) return 'bg-yellow-500';
        return 'bg-red-500';
    };

    return (
        <div className="space-y-6 p-6">
            {/* Header */}
            <div>
                <h1 className="text-3xl font-bold text-gray-900">CEO Speech Analysis</h1>
                <p className="text-gray-600 mt-1">
                    Analyze CEO statements from SEC filings and news
                </p>
            </div>

            {/* Search */}
            <Card title="Search CEO Analysis">
                <div className="flex gap-4">
                    <div className="flex-1">
                        <Input
                            label="Ticker Symbol"
                            value={ticker}
                            onChange={setTicker}
                            placeholder="Enter ticker (e.g., NVDA)"
                        />
                    </div>
                    <div className="flex items-end">
                        <Button
                            onClick={() => console.log('Searching for:', ticker)}
                            disabled={!ticker.trim()}
                            className="flex items-center gap-2"
                        >
                            <Search size={16} />
                            Search
                        </Button>
                    </div>
                </div>
            </Card>

            {/* Tone Shift Analysis */}
            <Card title="Tone Shift Analysis">
                <div className="space-y-4">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                            {getToneShiftIcon(mockToneShift.direction)}
                            <div>
                                <h3 className="text-lg font-semibold">
                                    {mockToneShift.direction.replace(/_/g, ' ')}
                                </h3>
                                <p className="text-sm text-gray-600">
                                    Magnitude: {(mockToneShift.magnitude * 100).toFixed(0)}%
                                </p>
                            </div>
                        </div>
                        <Badge variant={mockToneShift.signal === 'POSITIVE' ? 'success' : 'warning'}>
                            {mockToneShift.signal}
                        </Badge>
                    </div>

                    <div>
                        <div className="h-3 bg-gray-200 rounded-full overflow-hidden">
                            <div
                                className={`h-full ${mockToneShift.direction === 'MORE_OPTIMISTIC'
                                        ? 'bg-green-500'
                                        : mockToneShift.direction === 'MORE_PESSIMISTIC'
                                            ? 'bg-red-500'
                                            : 'bg-gray-500'
                                    }`}
                                style={{ width: `${mockToneShift.magnitude * 100}%` }}
                            />
                        </div>
                        {mockToneShift.is_significant && (
                            <p className="text-xs text-gray-600 mt-1">
                                ⚠️ Significant change detected
                            </p>
                        )}
                    </div>

                    {mockToneShift.key_changes.length > 0 && (
                        <div>
                            <h4 className="text-sm font-medium text-gray-700 mb-2">Key Changes:</h4>
                            <ul className="space-y-1">
                                {mockToneShift.key_changes.map((change, idx) => (
                                    <li key={idx} className="text-sm text-gray-600 flex items-start gap-2">
                                        <span className="text-blue-500 mt-1">•</span>
                                        {change}
                                    </li>
                                ))}
                            </ul>
                        </div>
                    )}
                </div>
            </Card>

            {/* CEO Quotes */}
            <Card title="CEO Quotes">
                <div className="space-y-3">
                    {mockQuotes.map((quote, idx) => (
                        <div
                            key={idx}
                            className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
                            onClick={() => setSelectedQuote(quote)}
                        >
                            <div className="flex items-start justify-between mb-2">
                                <div className="flex items-center gap-2">
                                    {getQuoteTypeIcon(quote.quote_type)}
                                    <Badge variant={getQuoteTypeColor(quote.quote_type)}>
                                        {quote.quote_type.replace(/_/g, ' ')}
                                    </Badge>
                                    <Badge variant="default">
                                        {quote.source === 'sec_filing' ? 'SEC' : 'News'}
                                    </Badge>
                                </div>
                                {quote.fiscal_period && (
                                    <div className="flex items-center gap-1 text-xs text-gray-500">
                                        <Calendar size={12} />
                                        {quote.fiscal_period}
                                    </div>
                                )}
                            </div>

                            <p className="text-gray-900 mb-2">"{quote.text}"</p>

                            {quote.sentiment !== undefined && (
                                <div className="flex items-center gap-2">
                                    <span className="text-xs text-gray-600 w-20">Sentiment:</span>
                                    <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                                        <div
                                            className={`h-full ${getSentimentColor(quote.sentiment)}`}
                                            style={{
                                                width: `${Math.abs(quote.sentiment) * 100}%`,
                                                marginLeft: quote.sentiment < 0 ? '0' : '50%',
                                            }}
                                        />
                                    </div>
                                    <span className="text-xs font-medium w-12 text-right">
                                        {(quote.sentiment * 100).toFixed(0)}%
                                    </span>
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            </Card>

            {/* Similar Historical Statements */}
            <Card title="Similar Historical Statements">
                <div className="space-y-3">
                    {mockSimilarStatements.map((statement, idx) => (
                        <div
                            key={idx}
                            className="border border-gray-200 rounded-lg p-4 bg-gray-50"
                        >
                            <div className="flex items-center justify-between mb-2">
                                <div className="flex items-center gap-2">
                                    <Badge variant="info">
                                        {statement.date}
                                    </Badge>
                                    <span className="text-xs text-gray-600">
                                        Similarity: {(statement.similarity * 100).toFixed(0)}%
                                    </span>
                                </div>
                                {statement.outcome && (
                                    <Badge variant={statement.outcome.includes('+') ? 'success' : 'danger'}>
                                        {statement.outcome}
                                    </Badge>
                                )}
                            </div>

                            <p className="text-sm text-gray-700">"{statement.statement}"</p>

                            <div className="mt-2">
                                <div className="h-1.5 bg-gray-300 rounded-full overflow-hidden">
                                    <div
                                        className="h-full bg-blue-500"
                                        style={{ width: `${statement.similarity * 100}%` }}
                                    />
                                </div>
                            </div>
                        </div>
                    ))}
                </div>

                <div className="mt-4 p-3 bg-blue-50 rounded-lg">
                    <p className="text-sm text-blue-900">
                        💡 <strong>Pattern Insight:</strong> Similar optimistic statements in the past
                        led to positive stock performance within 3 months.
                    </p>
                </div>
            </Card>

            {/* Quote Detail Modal */}
            {selectedQuote && (
                <div
                    className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
                    onClick={() => setSelectedQuote(null)}
                >
                    <div
                        className="bg-white rounded-lg p-6 max-w-2xl w-full"
                        onClick={(e) => e.stopPropagation()}
                    >
                        <h3 className="text-xl font-bold mb-4">Quote Details</h3>
                        <div className="space-y-4">
                            <div>
                                <p className="text-sm text-gray-600 mb-1">Quote:</p>
                                <p className="text-gray-900">"{selectedQuote.text}"</p>
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <p className="text-sm text-gray-600">Type:</p>
                                    <Badge variant={getQuoteTypeColor(selectedQuote.quote_type)}>
                                        {selectedQuote.quote_type.replace(/_/g, ' ')}
                                    </Badge>
                                </div>
                                <div>
                                    <p className="text-sm text-gray-600">Source:</p>
                                    <Badge variant="default">{selectedQuote.source}</Badge>
                                </div>
                                {selectedQuote.fiscal_period && (
                                    <div>
                                        <p className="text-sm text-gray-600">Period:</p>
                                        <p className="font-medium">{selectedQuote.fiscal_period}</p>
                                    </div>
                                )}
                                {selectedQuote.sentiment !== undefined && (
                                    <div>
                                        <p className="text-sm text-gray-600">Sentiment:</p>
                                        <p className="font-medium">
                                            {(selectedQuote.sentiment * 100).toFixed(0)}%
                                        </p>
                                    </div>
                                )}
                            </div>
                        </div>
                        <div className="mt-6 flex justify-end">
                            <Button onClick={() => setSelectedQuote(null)}>Close</Button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

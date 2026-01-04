/**
 * Data Backfill Page
 *
 * Historical Data Seeding UI
 * - News backfill (multi-source crawling + NLP processing)
 * - Stock price backfill (yfinance OHLCV data)
 * - Real-time progress monitoring
 * - Job management (list, detail, cancel)
 */

import React, { useState, useEffect } from 'react';
import {
    Database, RefreshCw, Calendar, Download, X,
    TrendingUp, Clock, CheckCircle, XCircle,
    PlayCircle, Pause, Trash2, ChevronRight, AlertCircle
} from 'lucide-react';
import { Card } from '../components/common/Card';

// Types
interface BackfillJob {
    job_id: string;
    job_type: 'news_backfill' | 'price_backfill';
    status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
    progress: {
        total_articles?: number;
        crawled_articles?: number;
        processed_articles?: number;
        saved_articles?: number;
        failed_articles?: number;
        total_tickers?: number;
        processed_tickers?: number;
        total_data_points?: number;
        saved_data_points?: number;
        failed_tickers?: number;
    };
    created_at: string;
    started_at?: string;
    completed_at?: string;
    error_message?: string;
    params?: {
        start_date?: string;
        end_date?: string;
        keywords?: string[];
        tickers?: string[];
        interval?: string;
    };
}

type TabType = 'news' | 'prices' | 'jobs' | 'explore';

export const DataBackfill: React.FC = () => {
    const [activeTab, setActiveTab] = useState<TabType>('jobs');
    const [jobs, setJobs] = useState<BackfillJob[]>([]);
    const [selectedJob, setSelectedJob] = useState<BackfillJob | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // News backfill form
    const [newsStartDate, setNewsStartDate] = useState('2024-01-01');
    const [newsEndDate, setNewsEndDate] = useState('2024-12-31');
    const [keywords, setKeywords] = useState('AI, tech, finance');
    const [newsTickers, setNewsTickers] = useState('AAPL, MSFT, GOOGL, TSLA, NVDA');

    // Data Explorer State
    const [explorerData, setExplorerData] = useState<any[]>([]);
    const [explorerLoading, setExplorerLoading] = useState(false);
    const [explorerFilters, setExplorerFilters] = useState({
        start_date: '2024-01-01',
        end_date: new Date().toISOString().split('T')[0],
        ticker: ''
    });

    const searchData = async () => {
        setExplorerLoading(true);
        try {
            const params = new URLSearchParams();
            if (explorerFilters.start_date) params.append('start_date', explorerFilters.start_date);
            if (explorerFilters.end_date) params.append('end_date', explorerFilters.end_date);
            if (explorerFilters.ticker) params.append('ticker', explorerFilters.ticker.toUpperCase());

            const res = await fetch(`/api/backfill/data/news?${params.toString()}`);
            if (res.ok) {
                const data = await res.json();
                setExplorerData(data.articles || []);
            }
        } catch (e) {
            console.error(e);
        } finally {
            setExplorerLoading(false);
        }
    };

    // Price backfill form
    const [priceStartDate, setPriceStartDate] = useState('2024-01-01');
    const [priceEndDate, setPriceEndDate] = useState('2024-12-31');
    const [priceTickers, setPriceTickers] = useState('AAPL, MSFT, GOOGL, TSLA, NVDA');
    const [interval, setInterval] = useState('1d');

    // Load jobs (silent = true for background polling)
    const loadJobs = async (silent = false) => {
        if (!silent) {
            setLoading(true);
            setError(null);
        }

        try {
            const res = await fetch('/api/backfill/jobs');
            if (res.ok) {
                const data = await res.json();
                setJobs(data.jobs || []);
            } else if (!silent) {
                setError('작업 목록 로드 실패');
            }
        } catch (err) {
            if (!silent) {
                console.error('Load jobs error:', err);
                setError('작업 목록 로드 중 오류 발생');
            }
            // Silently fail for polling requests
        } finally {
            if (!silent) {
                setLoading(false);
            }
        }
    };

    // Load job detail
    const loadJobDetail = async (jobId: string) => {
        try {
            const res = await fetch(`/api/backfill/status/${jobId}`);
            if (res.ok) {
                const job = await res.json();
                setSelectedJob(job);

                // Update in list
                setJobs(prev => prev.map(j =>
                    j.job_id === jobId ? job : j
                ));
            }
        } catch (err) {
            console.error('Load job detail error:', err);
        }
    };

    // Start news backfill
    const startNewsBackfill = async () => {
        setLoading(true);
        setError(null);

        try {
            const res = await fetch('/api/backfill/news', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    start_date: newsStartDate,
                    end_date: newsEndDate,
                    keywords: keywords.split(',').map(k => k.trim()).filter(k => k),
                    tickers: newsTickers.split(',').map(t => t.trim()).filter(t => t),
                }),
            });

            if (res.ok) {
                const data = await res.json();
                alert(`뉴스 백필 작업이 시작되었습니다!\nJob ID: ${data.job_id}`);
                await loadJobs();
                setActiveTab('jobs');
            } else {
                const errorData = await res.json();
                setError(errorData.detail || '뉴스 백필 시작 실패');
            }
        } catch (err) {
            console.error('Start news backfill error:', err);
            setError('뉴스 백필 시작 중 오류 발생');
        } finally {
            setLoading(false);
        }
    };

    // Start price backfill
    const startPriceBackfill = async () => {
        setLoading(true);
        setError(null);

        // Client-side validation for Yahoo Finance limitations
        const startDate = new Date(priceStartDate);
        const endDate = new Date(priceEndDate);
        const daysDiff = Math.floor((endDate.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24));

        if (interval === '1m' && daysDiff > 7) {
            alert(
                '❌ Yahoo Finance 제한사항\n\n' +
                '1분(1m) 간격 데이터는 최근 7일까지만 제공됩니다.\n\n' +
                '해결 방법:\n' +
                '1. 조회 기간을 7일 이내로 줄이거나\n' +
                '2. 간격을 1시간(1h) 또는 1일(1d)로 변경하세요.'
            );
            setLoading(false);
            return;
        }

        if (interval === '1h' && daysDiff > 730) {
            alert(
                '❌ Yahoo Finance 제한사항\n\n' +
                '1시간(1h) 간격 데이터는 최근 730일(2년)까지만 제공됩니다.\n\n' +
                '해결 방법:\n' +
                '1. 조회 기간을 730일 이내로 줄이거나\n' +
                '2. 간격을 1일(1d)로 변경하세요.\n\n' +
                `현재 기간: ${daysDiff}일`
            );
            setLoading(false);
            return;
        }

        try {
            const res = await fetch('/api/backfill/prices', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    tickers: priceTickers.split(',').map(t => t.trim()).filter(t => t),
                    start_date: priceStartDate,
                    end_date: priceEndDate,
                    interval: interval,
                }),
            });

            if (res.ok) {
                const data = await res.json();
                alert(`✅ 주가 백필 작업이 시작되었습니다!\n\nJob ID: ${data.job_id}\n간격: ${interval}\n기간: ${daysDiff}일`);
                await loadJobs();
                setActiveTab('jobs');
            } else {
                const errorData = await res.json();
                const errorMsg = errorData.detail || '주가 백필 시작 실패';
                // Show as alert popup
                alert(`❌ 주가 백필 실패\n\n${errorMsg}`);
                setError(errorMsg);
            }
        } catch (err) {
            console.error('Start price backfill error:', err);
            const errorMsg = '주가 백필 시작 중 오류 발생';
            alert(`❌ 오류\n\n${errorMsg}`);
            setError(errorMsg);
        } finally {
            setLoading(false);
        }
    };

    // Cancel job
    const cancelJob = async (jobId: string) => {
        if (!confirm('작업을 취소하시겠습니까?')) return;

        try {
            const res = await fetch(`/api/backfill/jobs/${jobId}`, {
                method: 'DELETE',
            });

            if (res.ok) {
                alert('작업이 취소되었습니다.');
                await loadJobs();
            }
        } catch (err) {
            console.error('Cancel job error:', err);
            alert('작업 취소 중 오류 발생');
        }
    };

    // Ref to track selected job ID to avoid stale closures in polling
    const selectedJobIdRef = React.useRef<string | null>(null);
    useEffect(() => {
        selectedJobIdRef.current = selectedJob?.job_id || null;
    }, [selectedJob]);

    // Robust Polling Logic using recursive setTimeout
    useEffect(() => {
        let timeoutId: any; // Use any to avoid NodeJS vs Window timeout type issues
        let isMounted = true;

        const poll = async () => {
            if (!isMounted) return;

            // 1. Load jobs list silently
            try {
                const res = await fetch('/api/backfill/jobs');
                if (res.ok) {
                    const data = await res.json();
                    const currentJobs: BackfillJob[] = data.jobs || [];

                    // Only update state if mounted
                    if (isMounted) {
                        setJobs(currentJobs);
                    }

                    // 2. Load detail if selected job is running
                    const currentSelectedId = selectedJobIdRef.current;
                    const selectedJobIsRunning = currentJobs.find(j =>
                        j.job_id === currentSelectedId &&
                        (j.status === 'running' || j.status === 'pending')
                    );

                    if (currentSelectedId && selectedJobIsRunning && isMounted) {
                        try {
                            const detailRes = await fetch(`/api/backfill/status/${currentSelectedId}`);
                            if (detailRes.ok) {
                                const jobDetail = await detailRes.json();
                                if (isMounted) {
                                    setSelectedJob(jobDetail);
                                }
                            }
                        } catch (err) {
                            console.error('Detail polling error:', err);
                        }
                    }

                    // 3. Decide whether to continue polling
                    // We poll more frequently if jobs are running, less frequently if idle
                    const hasRunning = currentJobs.some(j => j.status === 'running' || j.status === 'pending');
                    const nextInterval = hasRunning ? 3000 : 10000; // 3s if running, 10s if idle

                    if (isMounted) {
                        timeoutId = setTimeout(poll, nextInterval);
                    }
                } else {
                    // If fetch fails, retry slower
                    if (isMounted) timeoutId = setTimeout(poll, 15000);
                }
            } catch (err) {
                console.error('Polling error:', err);
                // Retry on error
                if (isMounted) timeoutId = setTimeout(poll, 15000);
            }
        };

        // Initial call
        poll();

        return () => {
            isMounted = false;
            clearTimeout(timeoutId);
        };
    }, []); // Empty dependency array -> Ensure single polling loop lifespan


    // Initial load
    useEffect(() => {
        loadJobs();
    }, []);

    // Status icon
    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'pending':
                return <Clock className="w-5 h-5 text-gray-400" />;
            case 'running':
                return <RefreshCw className="w-5 h-5 text-blue-500 animate-spin" />;
            case 'completed':
                return <CheckCircle className="w-5 h-5 text-green-500" />;
            case 'failed':
                return <XCircle className="w-5 h-5 text-red-500" />;
            case 'cancelled':
                return <X className="w-5 h-5 text-gray-500" />;
            default:
                return <Clock className="w-5 h-5 text-gray-400" />;
        }
    };

    // Progress percentage
    const getProgressPercentage = (job: BackfillJob): number => {
        if (job.job_type === 'news_backfill') {
            const { total_articles, saved_articles } = job.progress;
            if (!total_articles) return 0;
            return Math.round((saved_articles || 0) / total_articles * 100);
        } else {
            const { total_tickers, processed_tickers } = job.progress;
            if (!total_tickers) return 0;
            return Math.round((processed_tickers || 0) / total_tickers * 100);
        }
    };

    return (
        <div className="p-6 max-w-7xl mx-auto">
            {/* Header */}
            <div className="mb-6">
                <h1 className="text-3xl font-bold mb-2 flex items-center gap-3">
                    <Database className="w-8 h-8 text-blue-500" />
                    Historical Data Backfill
                </h1>
                <p className="text-gray-600">
                    과거 데이터 수집 - 뉴스 크롤링 + NLP 처리, 주가 OHLCV 데이터
                </p>
            </div>

            {/* Error Alert */}
            {error && (
                <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
                    <AlertCircle className="w-5 h-5 text-red-500 mt-0.5" />
                    <div>
                        <div className="font-semibold text-red-800">오류 발생</div>
                        <div className="text-red-600 text-sm">{error}</div>
                    </div>
                    <button
                        onClick={() => setError(null)}
                        className="ml-auto text-red-500 hover:text-red-700"
                    >
                        <X className="w-5 h-5" />
                    </button>
                </div>
            )}

            {/* Tabs */}
            <div className="flex gap-2 mb-6 border-b">
                <button
                    onClick={() => setActiveTab('news')}
                    className={`px-4 py-2 font-medium transition-colors ${activeTab === 'news'
                        ? 'border-b-2 border-blue-500 text-blue-600'
                        : 'text-gray-600 hover:text-gray-900'
                        }`}
                >
                    <div className="flex items-center gap-2">
                        <Download className="w-4 h-4" />
                        뉴스 백필
                    </div>
                </button>
                <button
                    onClick={() => setActiveTab('prices')}
                    className={`px-4 py-2 font-medium transition-colors ${activeTab === 'prices'
                        ? 'border-b-2 border-blue-500 text-blue-600'
                        : 'text-gray-600 hover:text-gray-900'
                        }`}
                >
                    <div className="flex items-center gap-2">
                        <TrendingUp className="w-4 h-4" />
                        주가 백필
                    </div>
                </button>
                <button
                    onClick={() => setActiveTab('jobs')}
                    className={`px-4 py-2 font-medium transition-colors ${activeTab === 'jobs'
                        ? 'border-b-2 border-blue-500 text-blue-600'
                        : 'text-gray-600 hover:text-gray-900'
                        }`}
                >
                    <div className="flex items-center gap-2">
                        <Clock className="w-4 h-4" />
                        작업 목록 ({jobs.length})
                    </div>
                </button>
                <button
                    onClick={() => setActiveTab('explore')}
                    className={`px-4 py-2 font-medium transition-colors ${activeTab === 'explore'
                        ? 'border-b-2 border-purple-500 text-purple-600'
                        : 'text-gray-600 hover:text-gray-900'
                        }`}
                >
                    <div className="flex items-center gap-2">
                        <Database className="w-4 h-4" />
                        Data Explorer
                    </div>
                </button>
            </div>

            {/* Tab Content */}
            {activeTab === 'news' && (
                <Card className="p-6">
                    <h2 className="text-xl font-bold mb-4">뉴스 데이터 백필</h2>
                    <p className="text-gray-600 mb-6">
                        NewsAPI, Google News, Reuters, Yahoo Finance, Bloomberg에서 뉴스를 수집하고
                        Sentiment Analysis + Embedding 처리를 진행합니다.
                    </p>

                    <div className="space-y-4">
                        {/* Date Range */}
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium mb-2">
                                    <Calendar className="w-4 h-4 inline mr-1" />
                                    시작 날짜
                                </label>
                                <input
                                    type="date"
                                    value={newsStartDate}
                                    onChange={(e) => setNewsStartDate(e.target.value)}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium mb-2">
                                    <Calendar className="w-4 h-4 inline mr-1" />
                                    종료 날짜
                                </label>
                                <input
                                    type="date"
                                    value={newsEndDate}
                                    onChange={(e) => setNewsEndDate(e.target.value)}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                                />
                            </div>
                        </div>

                        {/* Keywords */}
                        <div>
                            <label className="block text-sm font-medium mb-2">
                                키워드 (쉼표로 구분)
                            </label>
                            <input
                                type="text"
                                value={keywords}
                                onChange={(e) => setKeywords(e.target.value)}
                                placeholder="AI, tech, finance"
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                            />
                        </div>

                        {/* Tickers */}
                        <div>
                            <label className="block text-sm font-medium mb-2">
                                Tickers (쉼표로 구분)
                            </label>
                            <input
                                type="text"
                                value={newsTickers}
                                onChange={(e) => setNewsTickers(e.target.value)}
                                placeholder="AAPL, MSFT, GOOGL"
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                            />
                        </div>

                        {/* Info Box */}
                        <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                            <div className="font-semibold text-blue-800 mb-2">예상 소요 시간</div>
                            <div className="text-sm text-blue-700 space-y-1">
                                <div>• 크롤링: ~30분 (rate limit)</div>
                                <div>• NLP 처리: ~5시간 (Gemini + OpenAI)</div>
                                <div>• DB 저장: ~1.5초 ⚡</div>
                                <div>• 예상 비용: ~$0.73 (1년 데이터 기준)</div>
                            </div>
                        </div>

                        {/* Submit Button */}
                        <button
                            onClick={startNewsBackfill}
                            disabled={loading}
                            className="w-full bg-blue-500 text-white px-6 py-3 rounded-lg hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center justify-center gap-2 font-semibold"
                        >
                            {loading ? (
                                <>
                                    <RefreshCw className="w-5 h-5 animate-spin" />
                                    시작 중...
                                </>
                            ) : (
                                <>
                                    <PlayCircle className="w-5 h-5" />
                                    뉴스 백필 시작
                                </>
                            )}
                        </button>
                    </div>
                </Card>
            )}

            {activeTab === 'prices' && (
                <Card className="p-6">
                    <h2 className="text-xl font-bold mb-4">주가 데이터 백필</h2>
                    <p className="text-gray-600 mb-6">
                        yfinance를 사용하여 OHLCV 주가 데이터를 수집합니다 (무료).
                    </p>

                    <div className="space-y-4">
                        {/* Date Range */}
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium mb-2">
                                    <Calendar className="w-4 h-4 inline mr-1" />
                                    시작 날짜
                                </label>
                                <input
                                    type="date"
                                    value={priceStartDate}
                                    onChange={(e) => setPriceStartDate(e.target.value)}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium mb-2">
                                    <Calendar className="w-4 h-4 inline mr-1" />
                                    종료 날짜
                                </label>
                                <input
                                    type="date"
                                    value={priceEndDate}
                                    onChange={(e) => setPriceEndDate(e.target.value)}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                                />
                            </div>
                        </div>

                        {/* Tickers */}
                        <div>
                            <label className="block text-sm font-medium mb-2">
                                Tickers (쉼표로 구분)
                            </label>
                            <input
                                type="text"
                                value={priceTickers}
                                onChange={(e) => setPriceTickers(e.target.value)}
                                placeholder="AAPL, MSFT, GOOGL, TSLA, NVDA"
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                            />
                        </div>

                        {/* Interval */}
                        <div>
                            <label className="block text-sm font-medium mb-2">
                                데이터 간격
                            </label>
                            <select
                                value={interval}
                                onChange={(e) => setInterval(e.target.value)}
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                            >
                                <option value="1d">1일 (Daily) - 제한 없음</option>
                                <option value="1h">1시간 (Hourly) - 최근 2년</option>
                                <option value="1m">1분 (Minute) - 최근 7일</option>
                            </select>
                        </div>

                        {/* Yahoo Finance Limitations Warning */}
                        <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                            <div className="flex items-start gap-2">
                                <AlertCircle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
                                <div>
                                    <div className="font-semibold text-yellow-800 mb-2">⚠️ Yahoo Finance 제한사항</div>
                                    <div className="text-sm text-yellow-700 space-y-1">
                                        <div>• <strong>1분(1m)</strong>: 최근 7일까지만 조회 가능</div>
                                        <div>• <strong>1시간(1h)</strong>: 최근 730일(2년)까지만 조회 가능</div>
                                        <div>• <strong>1일(1d)</strong>: 과거 모든 데이터 조회 가능 ✅</div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Info Box */}
                        <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                            <div className="font-semibold text-green-800 mb-2">예상 소요 시간</div>
                            <div className="text-sm text-green-700 space-y-1">
                                <div>• yfinance 수집: ~5분 (100 tickers)</div>
                                <div>• DB 저장: ~12초 ⚡</div>
                                <div>• 비용: $0 (무료)</div>
                            </div>
                        </div>

                        {/* Submit Button */}
                        <button
                            onClick={startPriceBackfill}
                            disabled={loading}
                            className="w-full bg-green-500 text-white px-6 py-3 rounded-lg hover:bg-green-600 disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center justify-center gap-2 font-semibold"
                        >
                            {loading ? (
                                <>
                                    <RefreshCw className="w-5 h-5 animate-spin" />
                                    시작 중...
                                </>
                            ) : (
                                <>
                                    <PlayCircle className="w-5 h-5" />
                                    주가 백필 시작
                                </>
                            )}
                        </button>
                    </div>
                </Card>
            )}

            {activeTab === 'jobs' && (
                <div className="space-y-4">
                    {/* Refresh Button */}
                    <div className="flex justify-end">
                        <button
                            onClick={() => loadJobs(false)}
                            disabled={loading}
                            className="px-3 py-1 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-md flex items-center text-sm disabled:opacity-50 transition-colors"
                        >
                            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                            Refresh Jobs
                        </button>
                    </div>

                    {/* Jobs List */}
                    {jobs.length === 0 ? (
                        <Card className="p-12 text-center">
                            <Clock className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                            <p className="text-gray-600">진행 중인 작업이 없습니다.</p>
                        </Card>
                    ) : (
                        <div className="space-y-3">
                            {jobs.map((job) => (
                                <Card
                                    key={job.job_id}
                                    className={`p-4 cursor-pointer hover:shadow-lg transition-shadow ${selectedJob?.job_id === job.job_id ? 'ring-2 ring-blue-500' : ''
                                        }`}
                                    onClick={() => loadJobDetail(job.job_id)}
                                >
                                    <div className="flex items-start gap-4">
                                        {/* Status Icon */}
                                        <div className="mt-1">
                                            {getStatusIcon(job.status)}
                                        </div>

                                        {/* Job Info */}
                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-center gap-2 mb-2">
                                                <span className="font-semibold">
                                                    {job.job_type === 'news_backfill' ? '뉴스 백필' : '주가 백필'}
                                                </span>
                                                <span className={`px-2 py-0.5 rounded text-xs font-medium ${job.status === 'completed' ? 'bg-green-100 text-green-800' :
                                                    job.status === 'running' ? 'bg-blue-100 text-blue-800' :
                                                        job.status === 'failed' ? 'bg-red-100 text-red-800' :
                                                            job.status === 'cancelled' ? 'bg-gray-100 text-gray-800' :
                                                                'bg-gray-100 text-gray-800'
                                                    }`}>
                                                    {job.status.toUpperCase()}
                                                </span>
                                            </div>

                                            <div className="text-sm text-gray-600 mb-2">
                                                Job ID: {job.job_id.substring(0, 8)}...
                                            </div>

                                            {/* Progress Bar */}
                                            {(job.status === 'running' || job.status === 'completed') && (
                                                <div className="mb-2">
                                                    <div className="flex items-center justify-between text-xs mb-1">
                                                        <span>진행률</span>
                                                        <span>{getProgressPercentage(job)}%</span>
                                                    </div>
                                                    <div className="w-full bg-gray-200 rounded-full h-2">
                                                        <div
                                                            className={`h-2 rounded-full transition-all ${job.status === 'completed' ? 'bg-green-500' : 'bg-blue-500'
                                                                }`}
                                                            style={{ width: `${getProgressPercentage(job)}%` }}
                                                        />
                                                    </div>
                                                </div>
                                            )}

                                            {/* Progress Details */}
                                            <div className="text-xs text-gray-500 space-y-1">
                                                {job.job_type === 'news_backfill' ? (
                                                    <>
                                                        <div className="flex justify-between">
                                                            <span>저장:</span>
                                                            <span className="font-medium text-green-600">{job.progress.saved_articles || 0}</span>
                                                        </div>
                                                        <div className="flex justify-between">
                                                            <span>실패:</span>
                                                            <span className="font-medium text-red-600">{job.progress.failed_articles || 0}</span>
                                                        </div>
                                                    </>
                                                ) : (
                                                    <>
                                                        <div className="flex justify-between">
                                                            <span>저장:</span>
                                                            <span className="font-medium text-green-600">{job.progress.saved_data_points || 0}</span>
                                                        </div>
                                                        <div className="flex justify-between">
                                                            <span>실패:</span>
                                                            <span className="font-medium text-red-600">{job.progress.failed_tickers || 0}</span>
                                                        </div>
                                                    </>
                                                )}
                                            </div>

                                            {/* Current Activity */}
                                            {job.status === 'running' && (
                                                <div className="mt-2 pt-2 border-t text-xs text-blue-600 flex items-center gap-1">
                                                    <RefreshCw className="w-3 h-3 animate-spin" />
                                                    <span>
                                                        {job.job_type === 'news_backfill'
                                                            ? `뉴스 크롤링 및 NLP 처리 중...`
                                                            : `${job.params?.tickers?.join(', ')} 주가 수집 중...`
                                                        }
                                                    </span>
                                                </div>
                                            )}

                                            {/* Created At */}
                                            <div className="text-xs text-gray-400 mt-2">
                                                생성: {new Date(job.created_at).toLocaleString('ko-KR')}
                                            </div>
                                        </div>

                                        {/* Actions */}
                                        <div className="flex gap-2">
                                            {(job.status === 'pending' || job.status === 'running') && (
                                                <button
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        cancelJob(job.job_id);
                                                    }}
                                                    className="p-2 text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                                                    title="작업 취소"
                                                >
                                                    <X className="w-4 h-4" />
                                                </button>
                                            )}
                                            <ChevronRight className="w-5 h-5 text-gray-400" />
                                        </div>
                                    </div>

                                    {/* Error Message */}
                                    {job.error_message && (
                                        <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded text-sm text-red-700">
                                            <strong>오류:</strong> {job.error_message}
                                        </div>
                                    )}
                                </Card>
                            ))}
                        </div>
                    )}
                </div>
            )}
            {/* Content: Data Explorer */}
            {activeTab === 'explore' && (
                <div className="space-y-6">
                    {/* Filters */}
                    <Card className="p-4" title="Search Backfilled Data">
                        <div className="flex flex-wrap gap-4 items-end">
                            <div>
                                <label className="block text-sm text-gray-500 mb-1">Start Date</label>
                                <input
                                    type="date"
                                    value={explorerFilters.start_date}
                                    onChange={(e) => setExplorerFilters({ ...explorerFilters, start_date: e.target.value })}
                                    className="bg-gray-100 border border-gray-300 rounded px-3 py-2 text-gray-800"
                                />
                            </div>
                            <div>
                                <label className="block text-sm text-gray-500 mb-1">End Date</label>
                                <input
                                    type="date"
                                    value={explorerFilters.end_date}
                                    onChange={(e) => setExplorerFilters({ ...explorerFilters, end_date: e.target.value })}
                                    className="bg-gray-100 border border-gray-300 rounded px-3 py-2 text-gray-800"
                                />
                            </div>
                            <div>
                                <label className="block text-sm text-gray-500 mb-1">Ticker (Optional)</label>
                                <input
                                    type="text"
                                    placeholder="e.g. AAPL"
                                    value={explorerFilters.ticker}
                                    onChange={(e) => setExplorerFilters({ ...explorerFilters, ticker: e.target.value })}
                                    className="bg-gray-100 border border-gray-300 rounded px-3 py-2 text-gray-800 w-32"
                                />
                            </div>
                            <button
                                onClick={searchData}
                                className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg flex items-center gap-2"
                            >
                                <Database className="w-4 h-4" />
                                Search Data
                            </button>
                        </div>
                    </Card>

                    {/* Results */}
                    {explorerLoading ? (
                        <div className="text-center py-20 text-gray-500">
                            <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-2 text-purple-500" />
                            Loading Data...
                        </div>
                    ) : (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                            {explorerData.length === 0 ? (
                                <div className="col-span-full text-center py-20 text-gray-500 bg-gray-100 rounded-lg border border-dashed border-gray-300">
                                    No data found. Try adjusting filters or running a backfill job.
                                </div>
                            ) : (
                                explorerData.map((article) => (
                                    <Card key={article.id} className="hover:shadow-md transition-shadow">
                                        <div className="flex justify-between items-start mb-2">
                                            <span className="text-xs text-blue-600 bg-blue-100 px-2 py-1 rounded">
                                                {article.source || 'Unknown Source'}
                                            </span>
                                            <span className="text-xs text-gray-500">
                                                {article.published_date?.split('T')[0]}
                                            </span>
                                        </div>
                                        <h3 className="text-sm font-semibold text-gray-800 mb-2 line-clamp-2" title={article.title}>
                                            {article.title}
                                        </h3>
                                        <div className="flex flex-wrap gap-2 mt-2">
                                            {article.sentiment_label && (
                                                <span className={`text-xs px-2 py-0.5 rounded ${article.sentiment_label === 'positive' ? 'bg-green-100 text-green-700' :
                                                        article.sentiment_label === 'negative' ? 'bg-red-100 text-red-700' :
                                                            'bg-gray-100 text-gray-600'
                                                    }`}>
                                                    {article.sentiment_label} ({article.sentiment_score?.toFixed(2)})
                                                </span>
                                            )}
                                            {article.tickers && article.tickers.map((t: string) => (
                                                <span key={t} className="text-xs bg-gray-200 px-2 py-0.5 rounded text-gray-600">
                                                    {t}
                                                </span>
                                            ))}
                                        </div>
                                    </Card>
                                ))
                            )}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default DataBackfill;

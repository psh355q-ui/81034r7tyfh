/**
 * Global Analysis Context
 * 
 * Manages AI news analysis state globally across all pages
 * - Persists minimized popup across navigation
 * - Prevents duplicate EventSource connections
 * - Maintains single analysis session
 */

import React, { createContext, useContext, useState, useRef, useEffect, ReactNode } from 'react';

interface AnalysisProgress {
    status: 'idle' | 'running' | 'completed' | 'error';
    current_index: number;
    total_articles: number;
    progress_percent: number;
    current_article?: string;
    completed: number;
    skipped: number;
    errors: number;
    message?: string;
}

interface AnalysisContextType {
    isAnalyzing: boolean;
    progress: AnalysisProgress;
    isMinimized: boolean;
    currentPage: string;
    startAnalysis: (maxCount: number) => void;
    stopAnalysis: () => void;
    setMinimized: (minimized: boolean) => void;
    setCurrentPage: (page: string) => void;
}

const AnalysisContext = createContext<AnalysisContextType | undefined>(undefined);

export const useAnalysis = () => {
    const context = useContext(AnalysisContext);
    if (!context) {
        throw new Error('useAnalysis must be used within AnalysisProvider');
    }
    return context;
};

interface AnalysisProviderProps {
    children: ReactNode;
}

export const AnalysisProvider: React.FC<AnalysisProviderProps> = ({ children }) => {
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [isMinimized, setIsMinimized] = useState(false);
    const [currentPage, setCurrentPage] = useState('/');
    const [progress, setProgress] = useState<AnalysisProgress>({
        status: 'idle',
        current_index: 0,
        total_articles: 0,
        progress_percent: 0,
        completed: 0,
        skipped: 0,
        errors: 0,
    });

    const eventSourceRef = useRef<EventSource | null>(null);
    const analysisIdRef = useRef<string | null>(null);

    // Request notification permission on mount
    useEffect(() => {
        if ('Notification' in window && Notification.permission === 'default') {
            console.log('📢 Requesting notification permission...');
            Notification.requestPermission().then(permission => {
                console.log(`📢 Notification permission: ${permission}`);
            });
        }
    }, []);

    const startAnalysis = (maxCount: number) => {
        // Prevent duplicate analysis
        if (eventSourceRef.current) {
            console.warn('⚠️ Analysis already running, ignoring duplicate request');
            return;
        }

        // Generate unique analysis ID
        const analysisId = `analysis_${Date.now()}`;
        analysisIdRef.current = analysisId;

        console.log(`🚀 Starting analysis ${analysisId} with max_count=${maxCount}`);

        // Initialize progress
        setProgress({
            status: 'running',
            current_index: 0,
            total_articles: maxCount,
            progress_percent: 0,
            completed: 0,
            skipped: 0,
            errors: 0,
        });
        setIsAnalyzing(true);

        // Create EventSource
        const es = new EventSource(`/api/news/analyze-stream?max_count=${maxCount}`);
        eventSourceRef.current = es;

        es.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                console.log(`📊 Progress update (${analysisId}):`, data.current_index, '/', data.total_articles);
                setProgress(data);

                // Auto-complete
                if (data.status === 'completed') {
                    console.log(`✅ Analysis ${analysisId} completed`);

                    // Show browser notification
                    if ('Notification' in window && Notification.permission === 'granted') {
                        new Notification('🧠 AI 뉴스 분석 완료!', {
                            body: `✅ ${data.completed}개 완료 | ⊘ ${data.skipped}개 스킵 | ❌ ${data.errors}개 실패`,
                            icon: '/favicon.ico',
                            tag: 'analysis-complete',
                            requireInteraction: false
                        });
                    }

                    es.close();
                    eventSourceRef.current = null;

                    setTimeout(() => {
                        setIsAnalyzing(false);
                        setIsMinimized(false);
                    }, 3000);
                }
            } catch (error) {
                console.error('❌ Failed to parse progress data:', error);
            }
        };

        es.onerror = (error) => {
            console.error(`❌ SSE error for ${analysisId}:`, error);

            // Only set error if not completed
            if (progress.status !== 'completed') {
                setProgress(prev => ({
                    ...prev,
                    status: 'error',
                    message: 'Connection error occurred',
                }));
            }

            es.close();
            eventSourceRef.current = null;
            setIsAnalyzing(false);
        };
    };

    const stopAnalysis = () => {
        console.log('⛔ Stopping analysis manually');
        if (eventSourceRef.current) {
            eventSourceRef.current.close();
            eventSourceRef.current = null;
        }
        setIsAnalyzing(false);
        setIsMinimized(false);
        setProgress({
            status: 'idle',
            current_index: 0,
            total_articles: 0,
            progress_percent: 0,
            completed: 0,
            skipped: 0,
            errors: 0,
        });
    };

    const setMinimized = (minimized: boolean) => {
        console.log(`🔽 Setting minimized: ${minimized}`);
        setIsMinimized(minimized);
    };

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            if (eventSourceRef.current) {
                console.log('🧹 Cleaning up EventSource on unmount');
                eventSourceRef.current.close();
            }
        };
    }, []);

    return (
        <AnalysisContext.Provider
            value={{
                isAnalyzing,
                progress,
                isMinimized,
                currentPage,
                startAnalysis,
                stopAnalysis,
                setMinimized,
                setCurrentPage,
            }}
        >
            {children}
        </AnalysisContext.Provider>
    );
};

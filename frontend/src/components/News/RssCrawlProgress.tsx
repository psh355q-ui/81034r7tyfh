/**
 * RSS Crawl Progress Modal
 * RSS 크롤링 진행 상황을 실시간으로 표시하는 모달
 */

import React, { useEffect, useState } from 'react';
import { X, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';

interface CrawlProgress {
  status: 'running' | 'completed' | 'error';
  current_feed: string;
  current_index: number;
  total_feeds: number;
  progress_percent: number;
  articles_found: number;
  errors: Array<{
    feed: string;
    error: string;
    suggestion?: string;
    diagnosis?: string;
    likely_cause?: string;
    alternative_urls?: string[];
  }>;
  message: string;
}

interface RssCrawlProgressProps {
  isOpen: boolean;
  onClose: () => void;
}

export const RssCrawlProgress: React.FC<RssCrawlProgressProps> = ({ isOpen, onClose }) => {
  const [progress, setProgress] = useState<CrawlProgress>({
    status: 'running',
    current_feed: '',
    current_index: 0,
    total_feeds: 0,
    progress_percent: 0,
    articles_found: 0,
    errors: [],
    message: 'Starting RSS crawl...',
  });

  const [eventSource, setEventSource] = useState<EventSource | null>(null);

  useEffect(() => {
    if (!isOpen) return;

    // Prevent multiple EventSource connections
    const es = new EventSource('/api/news/crawl/stream?extract_content=true');
    let isCompleted = false; // Track completion locally

    es.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setProgress(data);

        // Auto-close on completion
        if (data.status === 'completed') {
          isCompleted = true; // Mark as completed
          // Close EventSource FIRST to prevent error event
          es.close();

          // Then trigger UI close after delay
          setTimeout(() => {
            onClose();
          }, 3000);
        }
      } catch (error) {
        console.error('Failed to parse progress data:', error);
      }
    };

    es.onerror = (error) => {
      // Ignore errors if stream closed after completion (normal behavior)
      if (isCompleted) {
        es.close();
        return;
      }

      console.error('SSE error:', error);
      setProgress(prev => ({
        ...prev,
        status: 'error',
        message: 'Connection error occurred',
      }));
      es.close();
    };

    setEventSource(es);

    return () => {
      es.close();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen]); // Remove onClose from deps to prevent multiple EventSource connections


  const handleClose = () => {
    if (eventSource) {
      eventSource.close();
    }
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl mx-4 max-h-[80vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <h2 className="text-xl font-semibold text-gray-900">
            RSS Crawling Progress
          </h2>
          {progress.status !== 'running' && (
            <button
              onClick={handleClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <X size={24} />
            </button>
          )}
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Status Icon & Message */}
          <div className="flex items-center space-x-3">
            {progress.status === 'running' && (
              <Loader2 size={24} className="text-blue-600 animate-spin" />
            )}
            {progress.status === 'completed' && (
              <CheckCircle size={24} className="text-green-600" />
            )}
            {progress.status === 'error' && (
              <AlertCircle size={24} className="text-red-600" />
            )}
            <p className="text-lg font-medium text-gray-900">{progress.message}</p>
          </div>

          {/* Progress Bar */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm text-gray-600">
              <span>
                {progress.current_index} / {progress.total_feeds} feeds processed
              </span>
              <span className="font-semibold">{progress.progress_percent.toFixed(0)}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
              <div
                className={`h-3 rounded-full transition-all duration-300 ${progress.status === 'completed'
                  ? 'bg-green-600'
                  : progress.status === 'error'
                    ? 'bg-red-600'
                    : 'bg-blue-600'
                  }`}
                style={{ width: `${progress.progress_percent}%` }}
              />
            </div>
          </div>

          {/* Current Feed */}
          {progress.current_feed && progress.status === 'running' && (
            <div className="bg-blue-50 p-4 rounded-lg">
              <p className="text-sm text-gray-600 mb-1">Currently processing:</p>
              <p className="text-sm font-medium text-gray-900 truncate">
                {progress.current_feed}
              </p>
            </div>
          )}

          {/* Statistics */}
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-green-50 p-4 rounded-lg">
              <p className="text-sm text-gray-600">Articles Found</p>
              <p className="text-2xl font-bold text-green-600">{progress.articles_found}</p>
            </div>
            <div className="bg-orange-50 p-4 rounded-lg">
              <p className="text-sm text-gray-600">Errors</p>
              <p className="text-2xl font-bold text-orange-600">{progress.errors?.length || 0}</p>
            </div>
          </div>

          {/* Errors List */}
          {progress.errors && progress.errors.length > 0 && (
            <div className="space-y-3 max-h-96 overflow-y-auto">
              <h3 className="text-sm font-semibold text-gray-900">Errors Detected:</h3>
              {progress.errors.map((error, index) => (
                <div key={index} className="bg-red-50 border border-red-200 rounded-lg p-3 space-y-2">
                  <div className="flex items-start space-x-2">
                    <AlertCircle size={16} className="text-red-600 mt-0.5 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {error.feed}
                      </p>
                      <p className="text-xs text-red-700 mt-1">{error.error}</p>

                      {/* Gemini AI Diagnosis */}
                      {error.suggestion && (
                        <div className="mt-3 bg-white border border-blue-200 rounded-lg p-3 space-y-2">
                          <div className="flex items-center space-x-2">
                            <div className="w-5 h-5 bg-gradient-to-r from-blue-500 to-purple-500 rounded flex items-center justify-center">
                              <span className="text-white text-xs font-bold">AI</span>
                            </div>
                            <p className="text-xs font-semibold text-gray-900">Gemini AI Diagnosis</p>
                          </div>

                          {error.diagnosis && (
                            <div className="pl-7">
                              <p className="text-xs text-gray-700 font-medium">Diagnosis:</p>
                              <p className="text-xs text-gray-600 mt-0.5">{error.diagnosis}</p>
                            </div>
                          )}

                          {error.likely_cause && (
                            <div className="pl-7">
                              <p className="text-xs text-gray-700 font-medium">Likely Cause:</p>
                              <span className="inline-block mt-0.5 px-2 py-0.5 bg-orange-100 text-orange-700 text-xs rounded">
                                {error.likely_cause}
                              </span>
                            </div>
                          )}

                          <div className="pl-7">
                            <p className="text-xs text-gray-700 font-medium">Suggested Fix:</p>
                            <p className="text-xs text-blue-600 mt-0.5 font-medium">{error.suggestion}</p>
                          </div>

                          {error.alternative_urls && error.alternative_urls.length > 0 && (
                            <div className="pl-7">
                              <p className="text-xs text-gray-700 font-medium">Alternative URLs:</p>
                              <ul className="mt-1 space-y-1">
                                {error.alternative_urls.map((url, urlIndex) => (
                                  <li key={urlIndex} className="text-xs">
                                    <a
                                      href={url}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="text-blue-600 hover:text-blue-800 hover:underline break-all"
                                    >
                                      {url}
                                    </a>
                                  </li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Completion Message */}
          {progress.status === 'completed' && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <div className="flex items-center space-x-2">
                <CheckCircle size={20} className="text-green-600" />
                <p className="text-sm font-medium text-green-900">
                  Crawling completed successfully! This window will close automatically.
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        {progress.status !== 'running' && (
          <div className="flex items-center justify-end p-6 border-t bg-gray-50">
            <button
              onClick={handleClose}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Close
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

/**
 * Gemini Free Chat Popup
 * 
 * 무료 티어: 1,500회/일
 * 비용: $0
 * 토큰 모니터링 + 일일 사용량 추적
 */

import React, { useState, useRef, useEffect } from 'react';
import {
  MessageSquare,
  X,
  Send,
  Zap,
  Clock,
  BarChart2,
  AlertCircle,
  CheckCircle,
  RefreshCw,
} from 'lucide-react';
import {
  sendGeminiMessage,
  getGeminiUsage,
  ChatMessage,
  GeminiResponse,
  UsageStats,
  formatRemainingRequests,
  getUsagePercentage,
  getUsageColor,
  getUsageBgColor,
} from '../../services/geminiFreeService';

interface GeminiFreePopupProps {
  isOpen: boolean;
  onClose: () => void;
}

export const GeminiFreePopup: React.FC<GeminiFreePopupProps> = ({ isOpen, onClose }) => {
  // State
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [latestResponse, setLatestResponse] = useState<GeminiResponse | null>(null);
  const [usageStats, setUsageStats] = useState<UsageStats | null>(null);

  // Refs
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Focus input on open
  useEffect(() => {
    if (isOpen) {
      inputRef.current?.focus();
      fetchUsage();
    }
  }, [isOpen]);

  // Fetch usage stats
  const fetchUsage = async () => {
    try {
      const stats = await getGeminiUsage();
      setUsageStats(stats);
    } catch (err) {
      console.error('Failed to fetch usage:', err);
    }
  };

  // Send message
  const handleSendMessage = async () => {
    if (!inputText.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      role: 'user',
      content: inputText.trim(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputText('');
    setIsLoading(true);
    setError(null);

    try {
      const response = await sendGeminiMessage({
        message: userMessage.content,
        history: messages,
        max_tokens: 1000,
        temperature: 0.7,
      });

      const assistantMessage: ChatMessage = {
        role: 'model',
        content: response.response,
      };

      setMessages(prev => [...prev, assistantMessage]);
      setLatestResponse(response);
      setUsageStats(prev => prev ? {
        ...prev,
        requests: {
          ...prev.requests,
          used: response.daily_usage.requests_today,
          remaining: response.daily_usage.remaining,
        },
        tokens: {
          ...prev.tokens,
          total: response.daily_usage.total_tokens_today,
        }
      } : null);
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Unknown error';
      setError(errorMessage);
      setMessages(prev => prev.slice(0, -1));
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleClearChat = () => {
    setMessages([]);
    setLatestResponse(null);
    setError(null);
  };

  if (!isOpen) return null;

  const usagePercentage = usageStats ? getUsagePercentage(usageStats.requests.used) : 0;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-3xl h-[80vh] flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-gray-200 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-t-xl">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-white/20 rounded-lg">
                <Zap className="text-white" size={20} />
              </div>
              <div>
                <h2 className="text-lg font-bold text-white">Gemini 무료 Chat</h2>
                <p className="text-xs text-white/80">1,500회/일 무료 • 비용 $0</p>
              </div>
            </div>
            
            <button
              onClick={onClose}
              className="text-white hover:bg-white/20 p-2 rounded-lg"
            >
              <X size={20} />
            </button>
          </div>

          {/* Usage Bar */}
          {usageStats && (
            <div className="mt-3">
              <div className="flex items-center justify-between text-xs text-white/90 mb-1">
                <span>오늘 사용량</span>
                <span>
                  {usageStats.requests.used} / {usageStats.requests.limit} 요청
                  ({formatRemainingRequests(usageStats.requests.remaining)} 남음)
                </span>
              </div>
              <div className="w-full bg-white/30 rounded-full h-2">
                <div
                  className={`h-2 rounded-full transition-all ${getUsageBgColor(usagePercentage)}`}
                  style={{ width: `${usagePercentage}%` }}
                />
              </div>
            </div>
          )}
        </div>

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
          {messages.length === 0 && (
            <div className="text-center text-gray-500 py-12">
              <Zap size={48} className="mx-auto mb-4 text-blue-300" />
              <p className="font-medium">Gemini에게 질문하세요</p>
              <p className="text-sm mt-2">무료 티어: 하루 1,500회</p>
              <p className="text-xs mt-1 text-green-600">💰 비용: $0</p>
            </div>
          )}

          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[75%] rounded-lg p-3 shadow-sm ${
                  msg.role === 'user'
                    ? 'bg-blue-500 text-white'
                    : 'bg-white text-gray-900 border border-gray-200'
                }`}
              >
                <div className="whitespace-pre-wrap text-sm">{msg.content}</div>
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-white rounded-lg p-3 shadow-sm border border-gray-200">
                <div className="flex items-center space-x-2">
                  <RefreshCw size={16} className="text-blue-500 animate-spin" />
                  <span className="text-sm text-gray-600">생성 중...</span>
                </div>
              </div>
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 p-3 rounded-lg flex items-start space-x-2">
              <AlertCircle size={18} className="flex-shrink-0 mt-0.5" />
              <div className="text-sm">{error}</div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Latest Response Stats */}
        {latestResponse && (
          <div className="border-t border-gray-200 bg-white p-3">
            <div className="flex items-center justify-between text-sm">
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-1 text-gray-600">
                  <Zap size={14} />
                  <span>
                    {latestResponse.token_usage.input_tokens} →{' '}
                    {latestResponse.token_usage.output_tokens}
                  </span>
                </div>
                <div className="flex items-center space-x-1 text-gray-600">
                  <Clock size={14} />
                  <span>{latestResponse.response_time_ms}ms</span>
                </div>
              </div>
              <div className="flex items-center space-x-1 text-green-600 font-medium">
                <CheckCircle size={14} />
                <span>$0.00</span>
              </div>
            </div>
          </div>
        )}

        {/* Input Area */}
        <div className="p-4 border-t border-gray-200 bg-white rounded-b-xl">
          <div className="flex items-center space-x-2 mb-2">
            <button
              onClick={handleClearChat}
              className="px-3 py-1 text-xs text-gray-600 hover:bg-gray-100 rounded"
            >
              대화 초기화
            </button>
            <button
              onClick={fetchUsage}
              className="px-3 py-1 text-xs text-gray-600 hover:bg-gray-100 rounded flex items-center space-x-1"
            >
              <RefreshCw size={12} />
              <span>사용량 새로고침</span>
            </button>
          </div>

          <div className="flex items-end space-x-2">
            <div className="flex-1">
              <textarea
                ref={inputRef}
                value={inputText}
                onChange={e => setInputText(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="메시지 입력... (Shift+Enter로 줄바꿈)"
                className="w-full border border-gray-300 rounded-lg px-4 py-2 resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                rows={2}
                disabled={isLoading || (usageStats?.requests.remaining === 0)}
              />
            </div>
            <button
              onClick={handleSendMessage}
              disabled={!inputText.trim() || isLoading || (usageStats?.requests.remaining === 0)}
              className={`p-3 rounded-lg transition-colors ${
                inputText.trim() && !isLoading && (usageStats?.requests.remaining ?? 1) > 0
                  ? 'bg-blue-500 text-white hover:bg-blue-600'
                  : 'bg-gray-200 text-gray-400 cursor-not-allowed'
              }`}
            >
              <Send size={18} />
            </button>
          </div>

          {usageStats?.requests.remaining === 0 && (
            <div className="mt-2 text-xs text-red-600 flex items-center space-x-1">
              <AlertCircle size={12} />
              <span>일일 무료 한도 초과! 내일 다시 사용 가능합니다.</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default GeminiFreePopup;

/**
 * AI Chat Popup Component
 * 
 * Features:
 * - 모델 선택 (Claude / Gemini)
 * - 실시간 토큰 사용량 모니터링
 * - 예상 비용 계산 및 표시
 * - API 요청/응답 원문 확인
 * - 세션 누적 통계
 */

import React, { useState, useRef, useEffect } from 'react';
import {
  MessageSquare,
  X,
  Send,
  ChevronDown,
  ChevronUp,
  DollarSign,
  Clock,
  Code,
  Copy,
  Check,
  Zap,
  Cpu,
  BarChart2,
} from 'lucide-react';
import {
  sendChatMessage,
  ChatMessage,
  ChatResponse,
  formatCost,
  formatTokens,
  formatResponseTime,
  calculateSessionStats,
} from '../../services/aiChatService';

// ============================================================================
// Types
// ============================================================================

interface AIChatPopupProps {
  isOpen: boolean;
  onClose: () => void;
}

interface ModelOption {
  id: string;
  name: string;
  description: string;
  provider: 'claude' | 'gemini';
  inputCost: number;
  outputCost: number;
}

// ============================================================================
// Constants
// ============================================================================

const MODELS: ModelOption[] = [
  {
    id: 'gemini-flash',
    name: 'Gemini 1.5 Flash',
    description: '최저가 (무료 티어)',
    provider: 'gemini',
    inputCost: 0.075,
    outputCost: 0.30,
  },
  {
    id: 'claude-haiku',
    name: 'Claude Haiku 4.5',
    description: '빠르고 저렴',
    provider: 'claude',
    inputCost: 1.00,
    outputCost: 5.00,
  },
  {
    id: 'gemini-pro',
    name: 'Gemini 1.5 Pro',
    description: '긴 컨텍스트',
    provider: 'gemini',
    inputCost: 1.25,
    outputCost: 5.00,
  },
  {
    id: 'claude-sonnet',
    name: 'Claude Sonnet 4',
    description: '고성능 분석',
    provider: 'claude',
    inputCost: 3.00,
    outputCost: 15.00,
  },
];

// ============================================================================
// Main Component
// ============================================================================

export const AIChatPopup: React.FC<AIChatPopupProps> = ({ isOpen, onClose }) => {
  // State
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [responses, setResponses] = useState<ChatResponse[]>([]);
  const [inputText, setInputText] = useState('');
  const [selectedModel, setSelectedModel] = useState<ModelOption>(MODELS[0]);
  const [isLoading, setIsLoading] = useState(false);
  const [showModelSelector, setShowModelSelector] = useState(false);
  const [showAPIDetails, setShowAPIDetails] = useState(false);
  const [showRawRequest, setShowRawRequest] = useState(false);
  const [latestResponse, setLatestResponse] = useState<ChatResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copiedField, setCopiedField] = useState<string | null>(null);

  // Refs
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Focus input on open
  useEffect(() => {
    if (isOpen) {
      inputRef.current?.focus();
    }
  }, [isOpen]);

  // Calculate session stats
  const sessionStats = calculateSessionStats(messages, responses);

  // ============================================================================
  // Handlers
  // ============================================================================

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
      const response = await sendChatMessage({
        model: selectedModel.id as any,
        message: userMessage.content,
        history: messages,
        max_tokens: 1000,
        temperature: 0.7,
        show_raw_request: showRawRequest,
      });

      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: response.response,
      };

      setMessages(prev => [...prev, assistantMessage]);
      setResponses(prev => [...prev, response]);
      setLatestResponse(response);
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Unknown error';
      setError(`오류: ${errorMessage}`);
      // Remove the user message on error
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

  const handleCopy = async (text: string, field: string) => {
    await navigator.clipboard.writeText(text);
    setCopiedField(field);
    setTimeout(() => setCopiedField(null), 2000);
  };

  const handleClearChat = () => {
    setMessages([]);
    setResponses([]);
    setLatestResponse(null);
    setError(null);
  };

  // ============================================================================
  // Render
  // ============================================================================

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-4xl h-[80vh] flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-gray-200 flex items-center justify-between bg-gradient-to-r from-blue-600 to-purple-600 rounded-t-xl">
          <div className="flex items-center space-x-3">
            <MessageSquare className="text-white" size={24} />
            <h2 className="text-lg font-bold text-white">AI Chat</h2>
          </div>
          
          <div className="flex items-center space-x-4">
            {/* Session Stats */}
            <div className="flex items-center space-x-3 text-white text-sm">
              <div className="flex items-center space-x-1">
                <Zap size={14} />
                <span>{formatTokens(sessionStats.totalTokens)}</span>
              </div>
              <div className="flex items-center space-x-1">
                <DollarSign size={14} />
                <span>{formatCost(sessionStats.totalCost)}</span>
              </div>
            </div>
            
            <button
              onClick={onClose}
              className="text-white hover:bg-white/20 p-1 rounded"
            >
              <X size={20} />
            </button>
          </div>
        </div>

        {/* Model Selector */}
        <div className="p-3 border-b border-gray-200 bg-gray-50">
          <div className="flex items-center justify-between">
            <div className="relative">
              <button
                onClick={() => setShowModelSelector(!showModelSelector)}
                className="flex items-center space-x-2 px-3 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                <Cpu size={16} className="text-gray-600" />
                <span className="font-medium">{selectedModel.name}</span>
                <ChevronDown size={16} className="text-gray-400" />
              </button>

              {showModelSelector && (
                <div className="absolute top-full left-0 mt-1 w-80 bg-white border border-gray-200 rounded-lg shadow-xl z-10">
                  {MODELS.map(model => (
                    <button
                      key={model.id}
                      onClick={() => {
                        setSelectedModel(model);
                        setShowModelSelector(false);
                      }}
                      className={`w-full text-left p-3 hover:bg-gray-50 first:rounded-t-lg last:rounded-b-lg ${
                        model.id === selectedModel.id ? 'bg-blue-50' : ''
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="font-medium text-gray-900">{model.name}</div>
                          <div className="text-xs text-gray-500">{model.description}</div>
                        </div>
                        <div className="text-right text-xs">
                          <div className="text-gray-600">
                            In: ${model.inputCost}/M
                          </div>
                          <div className="text-gray-600">
                            Out: ${model.outputCost}/M
                          </div>
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>

            <div className="flex items-center space-x-2">
              <label className="flex items-center space-x-2 text-sm">
                <input
                  type="checkbox"
                  checked={showRawRequest}
                  onChange={e => setShowRawRequest(e.target.checked)}
                  className="rounded"
                />
                <span>API 원문 표시</span>
              </label>
              
              <button
                onClick={handleClearChat}
                className="px-3 py-1 text-sm text-red-600 hover:bg-red-50 rounded"
              >
                대화 초기화
              </button>
            </div>
          </div>
        </div>

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 && (
            <div className="text-center text-gray-500 py-8">
              <MessageSquare size={48} className="mx-auto mb-4 text-gray-300" />
              <p>AI에게 질문을 입력하세요</p>
              <p className="text-sm mt-2">
                모델: <strong>{selectedModel.name}</strong>
              </p>
            </div>
          )}

          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[70%] rounded-lg p-3 ${
                  msg.role === 'user'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-900'
                }`}
              >
                <div className="whitespace-pre-wrap">{msg.content}</div>
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-gray-100 rounded-lg p-3">
                <div className="flex items-center space-x-2">
                  <div className="animate-pulse flex space-x-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-100" />
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-200" />
                  </div>
                  <span className="text-sm text-gray-600">응답 생성 중...</span>
                </div>
              </div>
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 p-3 rounded-lg">
              {error}
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Token Usage Display (Latest Response) */}
        {latestResponse && (
          <div className="border-t border-gray-200 bg-gray-50 p-3">
            <div className="flex items-center justify-between">
              <button
                onClick={() => setShowAPIDetails(!showAPIDetails)}
                className="flex items-center space-x-2 text-sm font-medium text-gray-700 hover:text-blue-600"
              >
                <BarChart2 size={16} />
                <span>최근 응답 상세</span>
                {showAPIDetails ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
              </button>

              <div className="flex items-center space-x-4 text-sm">
                <div className="flex items-center space-x-1 text-gray-600">
                  <Zap size={14} />
                  <span>
                    {latestResponse.token_usage.input_tokens} →{' '}
                    {latestResponse.token_usage.output_tokens}
                  </span>
                </div>
                <div className="flex items-center space-x-1 text-green-600 font-medium">
                  <DollarSign size={14} />
                  <span>{formatCost(latestResponse.cost_estimate.total_cost)}</span>
                </div>
                <div className="flex items-center space-x-1 text-gray-600">
                  <Clock size={14} />
                  <span>{formatResponseTime(latestResponse.response_time_ms)}</span>
                </div>
              </div>
            </div>

            {showAPIDetails && (
              <div className="mt-3 space-y-3">
                {/* Token Breakdown */}
                <div className="bg-white p-3 rounded border border-gray-200">
                  <h4 className="font-medium text-sm mb-2">토큰 사용량</h4>
                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div>
                      <div className="text-gray-500">입력 토큰</div>
                      <div className="font-mono font-medium">
                        {latestResponse.token_usage.input_tokens.toLocaleString()}
                      </div>
                      <div className="text-xs text-gray-400">
                        {formatCost(latestResponse.cost_estimate.input_cost)}
                      </div>
                    </div>
                    <div>
                      <div className="text-gray-500">출력 토큰</div>
                      <div className="font-mono font-medium">
                        {latestResponse.token_usage.output_tokens.toLocaleString()}
                      </div>
                      <div className="text-xs text-gray-400">
                        {formatCost(latestResponse.cost_estimate.output_cost)}
                      </div>
                    </div>
                    <div>
                      <div className="text-gray-500">총 비용</div>
                      <div className="font-mono font-medium text-green-600">
                        {formatCost(latestResponse.cost_estimate.total_cost)}
                      </div>
                      <div className="text-xs text-gray-400">
                        {latestResponse.cost_estimate.currency}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Raw Request/Response (if enabled) */}
                {showRawRequest && latestResponse.raw_request && (
                  <div className="space-y-2">
                    <div className="bg-white p-3 rounded border border-gray-200">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-medium text-sm flex items-center space-x-2">
                          <Code size={14} />
                          <span>API 요청 원문</span>
                        </h4>
                        <button
                          onClick={() =>
                            handleCopy(
                              JSON.stringify(latestResponse.raw_request, null, 2),
                              'request'
                            )
                          }
                          className="flex items-center space-x-1 text-xs text-blue-600 hover:text-blue-800"
                        >
                          {copiedField === 'request' ? (
                            <Check size={12} />
                          ) : (
                            <Copy size={12} />
                          )}
                          <span>{copiedField === 'request' ? '복사됨' : '복사'}</span>
                        </button>
                      </div>
                      <pre className="text-xs bg-gray-50 p-2 rounded overflow-x-auto max-h-40">
                        {JSON.stringify(latestResponse.raw_request, null, 2)}
                      </pre>
                    </div>

                    <div className="bg-white p-3 rounded border border-gray-200">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-medium text-sm flex items-center space-x-2">
                          <Code size={14} />
                          <span>API 응답 원문</span>
                        </h4>
                        <button
                          onClick={() =>
                            handleCopy(
                              JSON.stringify(latestResponse.raw_response, null, 2),
                              'response'
                            )
                          }
                          className="flex items-center space-x-1 text-xs text-blue-600 hover:text-blue-800"
                        >
                          {copiedField === 'response' ? (
                            <Check size={12} />
                          ) : (
                            <Copy size={12} />
                          )}
                          <span>{copiedField === 'response' ? '복사됨' : '복사'}</span>
                        </button>
                      </div>
                      <pre className="text-xs bg-gray-50 p-2 rounded overflow-x-auto max-h-40">
                        {JSON.stringify(latestResponse.raw_response, null, 2)}
                      </pre>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Input Area */}
        <div className="p-4 border-t border-gray-200">
          <div className="flex items-end space-x-2">
            <div className="flex-1">
              <textarea
                ref={inputRef}
                value={inputText}
                onChange={e => setInputText(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="메시지를 입력하세요... (Shift+Enter로 줄바꿈)"
                className="w-full border border-gray-300 rounded-lg px-4 py-2 resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                rows={3}
                disabled={isLoading}
              />
            </div>
            <button
              onClick={handleSendMessage}
              disabled={!inputText.trim() || isLoading}
              className={`p-3 rounded-lg transition-colors ${
                inputText.trim() && !isLoading
                  ? 'bg-blue-600 text-white hover:bg-blue-700'
                  : 'bg-gray-200 text-gray-400 cursor-not-allowed'
              }`}
            >
              <Send size={20} />
            </button>
          </div>
          
          {/* Estimated cost for next message */}
          {inputText.trim() && (
            <div className="mt-2 text-xs text-gray-500">
              예상 비용: ~{formatCost((inputText.length / 4 / 1000000) * selectedModel.inputCost)} (입력만)
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AIChatPopup;

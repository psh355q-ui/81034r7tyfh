import React, { useState } from 'react';
import { Brain, TrendingUp, TrendingDown, Network, Search, Lightbulb, AlertTriangle } from 'lucide-react';
import axios from 'axios';
import LogicTraceViewer from '../components/LogicTraceViewer';

interface ReasoningResult {
  success: boolean;
  theme: string;
  primary_beneficiary?: {
    ticker: string;
    action: string;
    confidence: number;
    reasoning: string;
  };
  hidden_beneficiary?: {
    ticker: string;
    action: string;
    confidence: number;
    reasoning: string;
  };
  loser?: {
    ticker: string;
    action: string;
    confidence: number;
    reasoning: string;
  };
  bull_case: string;
  bear_case: string;
  reasoning_trace: string[];
  model_used: string;
  analyzed_at: string;
  processing_time_ms: number;
}

interface KnowledgeRelation {
  subject: string;
  relation: string;
  object: string;
  confidence: number;
  evidence?: string;
}

type TabType = 'analysis' | 'trace' | 'knowledge' | 'history';

interface HistoryItem {
  id: number;
  news_text: string;
  theme: string;
  primary_beneficiary_ticker?: string;
  primary_beneficiary_action?: string;
  primary_beneficiary_confidence?: number;
  primary_beneficiary_reasoning?: string;
  hidden_beneficiary_ticker?: string;
  hidden_beneficiary_action?: string;
  hidden_beneficiary_confidence?: number;
  hidden_beneficiary_reasoning?: string;
  loser_ticker?: string;
  loser_action?: string;
  loser_confidence?: number;
  loser_reasoning?: string;
  bull_case: string;
  bear_case: string;
  reasoning_trace: any[];
  model_used: string;
  processing_time_ms: number;
  created_at: string;
}

const DeepReasoning: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabType>('analysis');
  const [newsText, setNewsText] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ReasoningResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [knowledgeEntity, setKnowledgeEntity] = useState('');
  const [knowledgeRelations, setKnowledgeRelations] = useState<KnowledgeRelation[]>([]);
  const [expandedSteps, setExpandedSteps] = useState<Set<number>>(new Set());
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [historyTotal, setHistoryTotal] = useState(0);
  const [historyLoading, setHistoryLoading] = useState(false);

  // Load history from DB
  const loadHistory = async () => {
    setHistoryLoading(true);
    try {
      const response = await axios.get('/api/reasoning/history', {
        params: { limit: 50, offset: 0 }
      });
      setHistory(response.data.items || []);
      setHistoryTotal(response.data.total || 0);
    } catch (err: any) {
      console.error('Failed to load history:', err);
    } finally {
      setHistoryLoading(false);
    }
  };

  // Load history when History tab is activated
  React.useEffect(() => {
    if (activeTab === 'history') {
      loadHistory();
    }
  }, [activeTab]);

  // Load from history item
  const loadFromHistory = (item: HistoryItem) => {
    setNewsText(item.news_text);

    // Convert history item to ReasoningResult format
    const resultData: ReasoningResult = {
      success: true,
      theme: item.theme,
      primary_beneficiary: item.primary_beneficiary_ticker ? {
        ticker: item.primary_beneficiary_ticker,
        action: item.primary_beneficiary_action || '',
        confidence: item.primary_beneficiary_confidence || 0,
        reasoning: item.primary_beneficiary_reasoning || ''
      } : undefined,
      hidden_beneficiary: item.hidden_beneficiary_ticker ? {
        ticker: item.hidden_beneficiary_ticker,
        action: item.hidden_beneficiary_action || '',
        confidence: item.hidden_beneficiary_confidence || 0,
        reasoning: item.hidden_beneficiary_reasoning || ''
      } : undefined,
      loser: item.loser_ticker ? {
        ticker: item.loser_ticker,
        action: item.loser_action || '',
        confidence: item.loser_confidence || 0,
        reasoning: item.loser_reasoning || ''
      } : undefined,
      bull_case: item.bull_case,
      bear_case: item.bear_case,
      reasoning_trace: item.reasoning_trace.map(t => typeof t === 'string' ? t : JSON.stringify(t)),
      model_used: item.model_used,
      analyzed_at: item.created_at,
      processing_time_ms: item.processing_time_ms
    };

    setResult(resultData);
    setActiveTab('analysis');
  };

  // Delete history item
  const deleteHistoryItem = async (id: number) => {
    if (!confirm('Are you sure you want to delete this analysis?')) {
      return;
    }

    try {
      await axios.delete(`/api/reasoning/history/${id}`);
      // Reload history after deletion
      await loadHistory();
    } catch (err: any) {
      console.error('Failed to delete history item:', err);
      alert('Failed to delete analysis');
    }
  };

  const analyzeNews = async () => {
    if (!newsText.trim()) {
      setError('Please enter news text to analyze');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await axios.post('/api/reasoning/analyze', {
        news_text: newsText,
        enable_verification: true,
      });
      setResult(response.data);
      setActiveTab('analysis'); // Show results tab after analysis
      // Note: Analysis is automatically saved to DB by backend
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to analyze news');
    } finally {
      setLoading(false);
    }
  };

  const searchKnowledge = async () => {
    if (!knowledgeEntity.trim()) return;

    try {
      const response = await axios.get(`/api/reasoning/knowledge/${knowledgeEntity}`);
      setKnowledgeRelations(response.data.relationships || []);
    } catch (err: any) {
      console.error('Failed to fetch knowledge:', err);
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600';
    if (confidence >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getActionIcon = (action: string) => {
    if (action === 'BUY') return <TrendingUp className="w-5 h-5 text-green-600" />;
    if (action === 'SELL' || action === 'TRIM') return <TrendingDown className="w-5 h-5 text-red-600" />;
    return <AlertTriangle className="w-5 h-5 text-yellow-600" />;
  };

  const toggleStep = (stepIndex: number) => {
    const newExpanded = new Set(expandedSteps);
    if (newExpanded.has(stepIndex)) {
      newExpanded.delete(stepIndex);
    } else {
      newExpanded.add(stepIndex);
    }
    setExpandedSteps(newExpanded);
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <Brain className="w-8 h-8 text-purple-600" />
            Deep Reasoning Analysis
          </h1>
          <p className="text-gray-600 mt-1">3-Step Chain-of-Thought reasoning with Hidden Beneficiary detection</p>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="flex gap-2 border-b border-gray-200">
        <button
          onClick={() => setActiveTab('analysis')}
          className={`px-6 py-3 font-semibold transition-colors ${activeTab === 'analysis'
            ? 'text-purple-600 border-b-2 border-purple-600'
            : 'text-gray-500 hover:text-gray-700'
            }`}
        >
          <Brain className="inline w-4 h-4 mr-2" />
          Analysis Results
        </button>
        <button
          onClick={() => setActiveTab('trace')}
          className={`px-6 py-3 font-semibold transition-colors ${activeTab === 'trace'
            ? 'text-purple-600 border-b-2 border-purple-600'
            : 'text-gray-500 hover:text-gray-700'
            }`}
          disabled={!result}
        >
          <Network className="inline w-4 h-4 mr-2" />
          Reasoning Trace
        </button>
        <button
          onClick={() => setActiveTab('knowledge')}
          className={`px-6 py-3 font-semibold transition-colors ${activeTab === 'knowledge'
            ? 'text-purple-600 border-b-2 border-purple-600'
            : 'text-gray-500 hover:text-gray-700'
            }`}
        >
          <Search className="inline w-4 h-4 mr-2" />
          Knowledge Graph
        </button>
        <button
          onClick={() => setActiveTab('history')}
          className={`px-6 py-3 font-semibold transition-colors ${activeTab === 'history'
            ? 'text-purple-600 border-b-2 border-purple-600'
            : 'text-gray-500 hover:text-gray-700'
            }`}
        >
          <svg className="inline w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          History ({historyTotal})
        </button>
      </div>

      {/* Tab Content */}
      {activeTab === 'analysis' && (
        <>
          {/* News Input Section */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
              <Search className="w-5 h-5" />
              News Analysis
            </h2>
            <textarea
              className="w-full h-32 p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              placeholder="Enter news text to analyze (e.g., 'Google announced TPU v6 with 2x efficiency improvement')"
              value={newsText}
              onChange={(e) => setNewsText(e.target.value)}
            />
            <div className="mt-4 flex gap-3">
              <button
                onClick={analyzeNews}
                disabled={loading}
                className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {loading ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    Analyzing...
                  </>
                ) : (
                  <>
                    <Brain className="w-4 h-4" />
                    Analyze with Deep Reasoning
                  </>
                )}
              </button>
              <button
                onClick={() => {
                  setNewsText('tpu npu gpu 간 현재 최대 쟁점을 확인하고 그 정보를 바탕으로 googl 주식 전망에 대해 분석하자');
                }}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Load Example
              </button>
            </div>

            {error && (
              <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
                {error}
              </div>
            )}
          </div>

          {/* Results Section */}
          {result && (
            <div className="space-y-6">
              {/* Theme */}
              <div className="bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold mb-2 flex items-center gap-2">
                  <Lightbulb className="w-5 h-5 text-purple-600" />
                  Investment Theme
                </h3>
                <p className="text-xl font-bold text-purple-900">{result.theme}</p>
              </div>

              {/* Beneficiaries Grid */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Primary Beneficiary */}
                {result.primary_beneficiary && (
                  <div className="bg-white rounded-lg shadow p-6 border-l-4 border-blue-500">
                    <h3 className="text-sm font-semibold text-gray-600 mb-3">Primary Beneficiary</h3>
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        {getActionIcon(result.primary_beneficiary.action)}
                        <span className="text-2xl font-bold">{result.primary_beneficiary.ticker}</span>
                      </div>
                      <span className={`text-sm font-semibold ${getConfidenceColor(result.primary_beneficiary.confidence)}`}>
                        {(result.primary_beneficiary.confidence * 100).toFixed(0)}%
                      </span>
                    </div>
                    <div className="text-sm bg-gray-50 p-3 rounded">
                      <span className="font-semibold">Action:</span> {result.primary_beneficiary.action}
                    </div>
                    <p className="text-sm text-gray-600 mt-3">{result.primary_beneficiary.reasoning}</p>
                  </div>
                )}

                {/* Hidden Beneficiary */}
                {result.hidden_beneficiary && (
                  <div className="bg-white rounded-lg shadow p-6 border-l-4 border-green-500">
                    <h3 className="text-sm font-semibold text-gray-600 mb-3 flex items-center gap-2">
                      <Network className="w-4 h-4" />
                      Hidden Beneficiary
                    </h3>
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        {getActionIcon(result.hidden_beneficiary.action)}
                        <span className="text-2xl font-bold">{result.hidden_beneficiary.ticker}</span>
                      </div>
                      <span className={`text-sm font-semibold ${getConfidenceColor(result.hidden_beneficiary.confidence)}`}>
                        {(result.hidden_beneficiary.confidence * 100).toFixed(0)}%
                      </span>
                    </div>
                    <div className="text-sm bg-green-50 p-3 rounded">
                      <span className="font-semibold">Action:</span> {result.hidden_beneficiary.action}
                    </div>
                    <p className="text-sm text-gray-600 mt-3">{result.hidden_beneficiary.reasoning}</p>
                  </div>
                )}

                {/* Loser */}
                {result.loser && (
                  <div className="bg-white rounded-lg shadow p-6 border-l-4 border-red-500">
                    <h3 className="text-sm font-semibold text-gray-600 mb-3">Potential Loser</h3>
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        {getActionIcon(result.loser.action)}
                        <span className="text-2xl font-bold">{result.loser.ticker}</span>
                      </div>
                      <span className={`text-sm font-semibold ${getConfidenceColor(result.loser.confidence)}`}>
                        {(result.loser.confidence * 100).toFixed(0)}%
                      </span>
                    </div>
                    <div className="text-sm bg-red-50 p-3 rounded">
                      <span className="font-semibold">Action:</span> {result.loser.action}
                    </div>
                    <p className="text-sm text-gray-600 mt-3">{result.loser.reasoning}</p>
                  </div>
                )}
              </div>

              {/* Bull/Bear Cases */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-white rounded-lg shadow p-6">
                  <h3 className="text-lg font-semibold mb-3 text-green-700 flex items-center gap-2">
                    <TrendingUp className="w-5 h-5" />
                    Bull Case
                  </h3>
                  <p className="text-gray-700">{result.bull_case}</p>
                </div>
                <div className="bg-white rounded-lg shadow p-6">
                  <h3 className="text-lg font-semibold mb-3 text-red-700 flex items-center gap-2">
                    <TrendingDown className="w-5 h-5" />
                    Bear Case
                  </h3>
                  <p className="text-gray-700">{result.bear_case}</p>
                </div>
              </div>

              {/* Metadata */}
              <div className="bg-gray-50 rounded-lg p-4 text-sm text-gray-600 flex items-center justify-between">
                <div>
                  <span className="font-semibold">Model:</span> {result.model_used}
                </div>
                <div>
                  <span className="font-semibold">Processing Time:</span> {result.processing_time_ms.toFixed(0)}ms
                </div>
                <div>
                  <span className="font-semibold">Analyzed:</span> {new Date(result.analyzed_at).toLocaleString()}
                </div>
              </div>
            </div>
          )}
        </>
      )}

      {/* Reasoning Trace Tab */}
      {activeTab === 'trace' && result && (
        <LogicTraceViewer
          trace={{
            id: 'trace_' + Date.now(),
            ticker: result.primary_beneficiary?.ticker || 'UNKNOWN',
            signal: result.primary_beneficiary?.action || 'HOLD',
            totalTime: result.processing_time_ms,
            confidence: result.primary_beneficiary?.confidence || 0,
            steps: result.reasoning_trace.map((step, idx) => ({
              id: `step_${idx}`,
              stepNumber: idx + 1,
              title: `Reasoning Step ${idx + 1}`,
              description: step,
              inputs: [],
              output: 'Processed',
              confidence: 0.9,
              timestamp: new Date().toISOString()
            })),
            debate: undefined // Add debate data if available in future
          }}
        />
      )}

      {/* Knowledge Graph Tab */}
      {activeTab === 'knowledge' && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <Network className="w-5 h-5" />
            Knowledge Graph Explorer
          </h2>
          <div className="flex gap-3 mb-4">
            <input
              type="text"
              className="flex-1 p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              placeholder="Enter company name (e.g., Google, Nvidia)"
              value={knowledgeEntity}
              onChange={(e) => setKnowledgeEntity(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && searchKnowledge()}
            />
            <button
              onClick={searchKnowledge}
              className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
            >
              Search
            </button>
          </div>

          {knowledgeRelations.length > 0 && (
            <div className="space-y-2">
              {knowledgeRelations.map((rel, index) => (
                <div key={index} className="p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center gap-2 text-sm">
                    <span className="font-semibold">{rel.subject}</span>
                    <span className="text-gray-500">→</span>
                    <span className="px-2 py-1 bg-purple-100 text-purple-700 rounded">{rel.relation}</span>
                    <span className="text-gray-500">→</span>
                    <span className="font-semibold">{rel.object}</span>
                    <span className={`ml-auto ${getConfidenceColor(rel.confidence)}`}>
                      {(rel.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                  {rel.evidence && (
                    <p className="text-xs text-gray-600 mt-1">{rel.evidence}</p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* History Tab */}
      {activeTab === 'history' && (
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold flex items-center gap-2">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Analysis History ({historyTotal} total)
            </h2>
            <button
              onClick={loadHistory}
              disabled={historyLoading}
              className="px-4 py-2 text-sm bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:bg-gray-400"
            >
              {historyLoading ? 'Loading...' : 'Refresh'}
            </button>
          </div>

          {historyLoading ? (
            <div className="flex justify-center items-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
            </div>
          ) : history.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <Brain className="w-12 h-12 mx-auto mb-3 text-gray-400" />
              <p>No analysis history yet</p>
              <p className="text-sm mt-1">Run an analysis to start building your history</p>
            </div>
          ) : (
            <div className="space-y-3">
              {history.map((item) => (
                <div key={item.id} className="p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-xs text-gray-500">
                          {new Date(item.created_at).toLocaleString()}
                        </span>
                        <span className="text-xs px-2 py-1 bg-purple-100 text-purple-700 rounded">
                          {item.model_used}
                        </span>
                        <span className="text-xs text-gray-500">
                          {item.processing_time_ms}ms
                        </span>
                      </div>
                      <p className="font-semibold text-purple-700 mb-2">{item.theme}</p>
                      <p className="text-sm text-gray-700 line-clamp-2 mb-2">{item.news_text}</p>
                      <div className="flex flex-wrap gap-2 text-xs">
                        {item.primary_beneficiary_ticker && (
                          <span className="px-2 py-1 bg-green-100 text-green-700 rounded">
                            Primary: {item.primary_beneficiary_ticker} ({item.primary_beneficiary_action})
                          </span>
                        )}
                        {item.hidden_beneficiary_ticker && (
                          <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded">
                            Hidden: {item.hidden_beneficiary_ticker} ({item.hidden_beneficiary_action})
                          </span>
                        )}
                        {item.loser_ticker && (
                          <span className="px-2 py-1 bg-red-100 text-red-700 rounded">
                            Loser: {item.loser_ticker} ({item.loser_action})
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="flex flex-col gap-2">
                      <button
                        onClick={() => loadFromHistory(item)}
                        className="px-3 py-1 text-xs bg-purple-600 text-white rounded hover:bg-purple-700"
                      >
                        Load
                      </button>
                      <button
                        onClick={() => deleteHistoryItem(item.id)}
                        className="px-3 py-1 text-xs bg-red-600 text-white rounded hover:bg-red-700"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default DeepReasoning;

import React, { useState } from 'react';
import { Brain, TrendingUp, TrendingDown, Network, Search, Lightbulb, AlertTriangle } from 'lucide-react';
import axios from 'axios';

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

const DeepReasoning: React.FC = () => {
  const [newsText, setNewsText] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ReasoningResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [knowledgeEntity, setKnowledgeEntity] = useState('');
  const [knowledgeRelations, setKnowledgeRelations] = useState<KnowledgeRelation[]>([]);

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
              setNewsText('Google announced TPU v6 with Anthropic signing 1M TPU contract');
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

          {/* Reasoning Trace */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold mb-4">Reasoning Trace</h3>
            <div className="space-y-3">
              {result.reasoning_trace.map((step, index) => (
                <div key={index} className="flex gap-3">
                  <div className="flex-shrink-0 w-8 h-8 bg-purple-100 text-purple-700 rounded-full flex items-center justify-center font-semibold">
                    {index + 1}
                  </div>
                  <p className="text-gray-700 pt-1">{step}</p>
                </div>
              ))}
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

      {/* Knowledge Graph Explorer */}
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
    </div>
  );
};

export default DeepReasoning;

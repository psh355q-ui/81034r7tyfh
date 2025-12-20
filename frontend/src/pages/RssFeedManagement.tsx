/**
 * RSS Feed Management Page
 * 
 * Features:
 * - View all feeds with statistics
 * - Add/Edit/Delete feeds
 * - Apply Gemini suggestions
 * - Toggle feed status
 * - Health monitoring
 * 
 * Author: AI Trading System
 * Date: 2025-11-15
 */

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Rss,
  Plus,
  Edit,
  Trash2,
  Power,
  PowerOff,
  RefreshCw,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Zap,
  ExternalLink,
  Copy,
  Settings,
  Search,
} from 'lucide-react';

// ============================================================================
// Types
// ============================================================================

interface RSSFeed {
  id: number;
  name: string;
  url: string;
  category: string;
  enabled: boolean;
  last_crawled_at: string | null;
  success_count: number;
  error_count: number;
  error_rate: number;
  last_error: string | null;
  created_at: string | null;
}

interface FeedHealth {
  total_feeds: number;
  active_feeds: number;
  inactive_feeds: number;
  healthy_feeds: number;
  problematic_feeds: number;
  average_error_rate: number;
  feeds_needing_attention: {
    id: number;
    name: string;
    error_rate: number;
    last_error: string;
    suggestion?: string;
  }[];
}

interface GeminiDiagnosis {
  feed_id: number;
  diagnosis: string;
  likely_cause: string;
  suggested_fix: string;
  alternative_urls: string[];
}

// ============================================================================
// API Functions
// ============================================================================

const API_BASE = '/api/feeds';

async function fetchFeeds(): Promise<RSSFeed[]> {
  const response = await fetch(API_BASE);
  if (!response.ok) throw new Error('Failed to fetch feeds');
  return response.json();
}

async function fetchFeedHealth(): Promise<FeedHealth> {
  const response = await fetch(`${API_BASE}/health/summary`);
  if (!response.ok) throw new Error('Failed to fetch health');
  return response.json();
}

async function createFeed(data: Partial<RSSFeed>): Promise<RSSFeed> {
  const response = await fetch(API_BASE, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error('Failed to create feed');
  return response.json();
}

async function updateFeed(id: number, data: Partial<RSSFeed>): Promise<RSSFeed> {
  const response = await fetch(`${API_BASE}/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error('Failed to update feed');
  return response.json();
}

async function deleteFeed(id: number): Promise<void> {
  const response = await fetch(`${API_BASE}/${id}`, {
    method: 'DELETE',
  });
  if (!response.ok) throw new Error('Failed to delete feed');
}

async function toggleFeed(id: number): Promise<void> {
  const response = await fetch(`${API_BASE}/${id}/toggle`, {
    method: 'PATCH',
  });
  if (!response.ok) throw new Error('Failed to toggle feed');
}

async function applySuggestion(feedId: number, newUrl: string): Promise<void> {
  const response = await fetch(`${API_BASE}/apply-suggestion`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      feed_id: feedId,
      new_url: newUrl,
      disable_old: false,
    }),
  });
  if (!response.ok) throw new Error('Failed to apply suggestion');
}

async function testFeedUrl(url: string): Promise<any> {
  const response = await fetch(`${API_BASE}/test-url`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url }),
  });
  if (!response.ok) throw new Error('Failed to test URL');
  return response.json();
}

async function discoverFeeds(): Promise<{ success: boolean; discovered: number; added: number }> {
  const response = await fetch(`${API_BASE}/discover`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });
  if (!response.ok) throw new Error('Failed to discover feeds');
  return response.json();
}

// ============================================================================
// Components
// ============================================================================

interface FeedCardProps {
  feed: RSSFeed;
  onEdit: (feed: RSSFeed) => void;
  onDelete: (id: number) => void;
  onToggle: (id: number) => void;
  diagnosis?: GeminiDiagnosis;
  onApplySuggestion?: (feedId: number, newUrl: string) => void;
}

const FeedCard: React.FC<FeedCardProps> = ({
  feed,
  onEdit,
  onDelete,
  onToggle,
  diagnosis,
  onApplySuggestion,
}) => {
  const [showDetails, setShowDetails] = useState(false);

  const errorRateColor =
    feed.error_rate < 0.05 ? 'text-green-500' :
      feed.error_rate < 0.15 ? 'text-yellow-500' :
        'text-red-500';

  const statusIcon = feed.enabled ? (
    <Power className="w-5 h-5 text-green-500" />
  ) : (
    <PowerOff className="w-5 h-5 text-gray-400" />
  );

  return (
    <div className={`
      bg-white rounded-lg shadow-sm border p-4
      ${!feed.enabled ? 'opacity-60' : ''}
      ${feed.error_rate > 0.1 ? 'border-red-200' : 'border-gray-200'}
    `}>
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <Rss className="w-5 h-5 text-orange-500" />
          <h3 className="font-semibold text-gray-900">{feed.name}</h3>
          <span className="text-xs px-2 py-0.5 bg-gray-100 rounded-full">
            {feed.category}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => onToggle(feed.id)}
            className="p-1 hover:bg-gray-100 rounded"
            title={feed.enabled ? 'Disable' : 'Enable'}
          >
            {statusIcon}
          </button>
          <button
            onClick={() => onEdit(feed)}
            className="p-1 hover:bg-gray-100 rounded"
            title="Edit"
          >
            <Edit className="w-4 h-4 text-gray-600" />
          </button>
          <button
            onClick={() => onDelete(feed.id)}
            className="p-1 hover:bg-red-50 rounded"
            title="Delete"
          >
            <Trash2 className="w-4 h-4 text-red-500" />
          </button>
        </div>
      </div>

      {/* URL */}
      <div className="flex items-center gap-2 mb-3">
        <input
          type="text"
          value={feed.url}
          readOnly
          className="flex-1 text-sm bg-gray-50 rounded px-2 py-1 truncate"
        />
        <button
          onClick={() => navigator.clipboard.writeText(feed.url)}
          className="p-1 hover:bg-gray-100 rounded"
          title="Copy URL"
        >
          <Copy className="w-4 h-4 text-gray-500" />
        </button>
        <a
          href={feed.url}
          target="_blank"
          rel="noopener noreferrer"
          className="p-1 hover:bg-gray-100 rounded"
          title="Open in browser"
        >
          <ExternalLink className="w-4 h-4 text-gray-500" />
        </a>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4 mb-3 text-sm">
        <div>
          <div className="text-gray-500">Success</div>
          <div className="font-medium text-green-600">{feed.success_count}</div>
        </div>
        <div>
          <div className="text-gray-500">Errors</div>
          <div className="font-medium text-red-600">{feed.error_count}</div>
        </div>
        <div>
          <div className="text-gray-500">Error Rate</div>
          <div className={`font-medium ${errorRateColor}`}>
            {(feed.error_rate * 100).toFixed(1)}%
          </div>
        </div>
      </div>

      {/* Last crawled */}
      <div className="text-xs text-gray-500 mb-2">
        Last crawled: {feed.last_crawled_at || 'Never'}
      </div>

      {/* Error message */}
      {feed.last_error && (
        <div className="bg-red-50 border border-red-200 rounded p-2 mb-3">
          <div className="flex items-center gap-2 text-red-700 text-sm font-medium">
            <AlertTriangle className="w-4 h-4" />
            Last Error
          </div>
          <div className="text-xs text-red-600 mt-1">{feed.last_error}</div>
        </div>
      )}

      {/* Gemini Diagnosis */}
      {diagnosis && (
        <div className="bg-purple-50 border border-purple-200 rounded p-3 mt-3">
          <div className="flex items-center gap-2 mb-2">
            <div className="bg-gradient-to-r from-purple-500 to-pink-500 text-white text-xs px-2 py-0.5 rounded">
              🤖 Gemini AI Diagnosis
            </div>
          </div>

          <div className="text-sm space-y-2">
            <div>
              <span className="font-medium text-purple-900">Likely Cause:</span>
              <span className="ml-2 px-2 py-0.5 bg-purple-100 rounded text-purple-700 text-xs">
                {diagnosis.likely_cause}
              </span>
            </div>

            <div>
              <span className="font-medium text-purple-900">Diagnosis:</span>
              <p className="text-gray-700 mt-1">{diagnosis.diagnosis}</p>
            </div>

            <div>
              <span className="font-medium text-purple-900">Suggested Fix:</span>
              <p className="text-gray-700 bg-white p-2 rounded mt-1 border border-purple-100">
                {diagnosis.suggested_fix}
              </p>
            </div>

            {diagnosis.alternative_urls.length > 0 && (
              <div>
                <span className="font-medium text-purple-900">Alternative URLs:</span>
                <div className="mt-1 space-y-1">
                  {diagnosis.alternative_urls.map((url, i) => (
                    <div key={i} className="flex items-center gap-2">
                      <a
                        href={url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:underline text-xs flex-1 truncate"
                      >
                        {url}
                      </a>
                      <button
                        onClick={() => onApplySuggestion?.(feed.id, url)}
                        className="flex items-center gap-1 px-2 py-1 bg-purple-600 text-white text-xs rounded hover:bg-purple-700"
                      >
                        <Zap className="w-3 h-3" />
                        Apply
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

// Feed Form Modal
interface FeedFormProps {
  feed?: RSSFeed | null;
  onSave: (data: Partial<RSSFeed>) => void;
  onClose: () => void;
}

const FeedFormModal: React.FC<FeedFormProps> = ({ feed, onSave, onClose }) => {
  const [name, setName] = useState(feed?.name || '');
  const [url, setUrl] = useState(feed?.url || '');
  const [category, setCategory] = useState(feed?.category || 'global');
  const [enabled, setEnabled] = useState(feed?.enabled ?? true);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<any>(null);

  const handleTest = async () => {
    setTesting(true);
    setTestResult(null);
    try {
      const result = await testFeedUrl(url);
      setTestResult(result);
      if (result.valid && !name) {
        setName(result.title);
      }
    } catch (error) {
      setTestResult({ valid: false, error: 'Failed to test URL' });
    } finally {
      setTesting(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave({ name, url, category, enabled });
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-lg mx-4">
        <div className="p-4 border-b flex items-center justify-between">
          <h2 className="text-lg font-semibold">
            {feed ? 'Edit Feed' : 'Add New Feed'}
          </h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
            <XCircle className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-4 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Feed URL *
            </label>
            <div className="flex gap-2">
              <input
                type="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                className="flex-1 border rounded px-3 py-2"
                placeholder="https://example.com/rss"
                required
              />
              <button
                type="button"
                onClick={handleTest}
                disabled={!url || testing}
                className="px-3 py-2 bg-gray-100 hover:bg-gray-200 rounded text-sm"
              >
                {testing ? 'Testing...' : 'Test'}
              </button>
            </div>

            {testResult && (
              <div className={`mt-2 p-2 rounded text-sm ${testResult.valid ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'
                }`}>
                {testResult.valid ? (
                  <div>
                    <div className="font-medium flex items-center gap-1">
                      <CheckCircle className="w-4 h-4" />
                      Valid RSS Feed
                    </div>
                    <div>Title: {testResult.title}</div>
                    <div>Entries: {testResult.entry_count}</div>
                  </div>
                ) : (
                  <div className="flex items-center gap-1">
                    <XCircle className="w-4 h-4" />
                    Invalid: {testResult.error}
                  </div>
                )}
              </div>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Feed Name *
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full border rounded px-3 py-2"
              placeholder="Reuters Business"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Category
            </label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full border rounded px-3 py-2"
            >
              <option value="global">Global</option>
              <option value="finance">Finance</option>
              <option value="technology">Technology</option>
              <option value="crypto">Crypto</option>
              <option value="earnings">Earnings</option>
            </select>
          </div>

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="enabled"
              checked={enabled}
              onChange={(e) => setEnabled(e.target.checked)}
              className="rounded"
            />
            <label htmlFor="enabled" className="text-sm text-gray-700">
              Enable feed immediately
            </label>
          </div>

          <div className="flex justify-end gap-2 pt-4 border-t">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              {feed ? 'Update Feed' : 'Add Feed'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Health Summary Card
const HealthSummary: React.FC<{ health: FeedHealth }> = ({ health }) => {
  return (
    <div className="bg-white rounded-lg shadow-sm border p-4">
      <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
        <Settings className="w-5 h-5 text-gray-600" />
        Feed Health Summary
      </h3>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
        <div className="text-center">
          <div className="text-2xl font-bold text-gray-900">{health.total_feeds}</div>
          <div className="text-sm text-gray-500">Total Feeds</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-green-600">{health.active_feeds}</div>
          <div className="text-sm text-gray-500">Active</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-green-600">{health.healthy_feeds}</div>
          <div className="text-sm text-gray-500">Healthy</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-red-600">{health.problematic_feeds}</div>
          <div className="text-sm text-gray-500">Problematic</div>
        </div>
      </div>

      <div className="text-sm text-gray-600">
        Average Error Rate: {(health.average_error_rate * 100).toFixed(2)}%
      </div>

      {health.feeds_needing_attention.length > 0 && (
        <div className="mt-4">
          <div className="text-sm font-medium text-red-700 mb-2">
            ⚠️ Feeds Needing Attention:
          </div>
          <div className="space-y-2">
            {health.feeds_needing_attention.map((feed) => (
              <div key={feed.id} className="bg-red-50 p-2 rounded text-sm">
                <div className="font-medium">{feed.name}</div>
                <div className="text-gray-600">Error rate: {(feed.error_rate * 100).toFixed(1)}%</div>
                <div className="text-red-600 text-xs">{feed.last_error}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

// ============================================================================
// Main Page Component
// ============================================================================

export const RssFeedManagement: React.FC = () => {
  const queryClient = useQueryClient();
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingFeed, setEditingFeed] = useState<RSSFeed | null>(null);
  const [filter, setFilter] = useState<'all' | 'active' | 'inactive' | 'error'>('all');
  const [discovering, setDiscovering] = useState(false);
  const [discoveryResult, setDiscoveryResult] = useState<{ discovered: number; added: number } | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Queries
  const { data: feeds = [], isLoading, error } = useQuery({
    queryKey: ['feeds'],
    queryFn: fetchFeeds,
    refetchInterval: 60000, // Refresh every minute
  });

  const { data: health } = useQuery({
    queryKey: ['feedHealth'],
    queryFn: fetchFeedHealth,
    refetchInterval: 60000,
  });

  // Mutations
  const createMutation = useMutation({
    mutationFn: createFeed,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['feeds'] });
      queryClient.invalidateQueries({ queryKey: ['feedHealth'] });
      setShowAddModal(false);
      setErrorMessage(null);
    },
    onError: (error: any) => {
      // Extract error message from response
      const message = error?.message || 'Failed to create feed';
      setErrorMessage(message);
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<RSSFeed> }) =>
      updateFeed(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['feeds'] });
      queryClient.invalidateQueries({ queryKey: ['feedHealth'] });
      setEditingFeed(null);
      setErrorMessage(null);
    },
    onError: (error: any) => {
      const message = error?.message || 'Failed to update feed';
      setErrorMessage(message);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteFeed,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['feeds'] });
    },
  });

  const toggleMutation = useMutation({
    mutationFn: toggleFeed,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['feeds'] });
    },
  });

  const applySuggestionMutation = useMutation({
    mutationFn: ({ feedId, newUrl }: { feedId: number; newUrl: string }) =>
      applySuggestion(feedId, newUrl),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['feeds'] });
    },
  });

  // Filter feeds
  const filteredFeeds = feeds.filter((feed) => {
    switch (filter) {
      case 'active':
        return feed.enabled;
      case 'inactive':
        return !feed.enabled;
      case 'error':
        return feed.error_rate > 0.1;
      default:
        return true;
    }
  });

  // Handle actions
  const handleSave = (data: Partial<RSSFeed>) => {
    if (editingFeed) {
      updateMutation.mutate({ id: editingFeed.id, data });
    } else {
      createMutation.mutate(data);
    }
  };

  const handleDelete = (id: number) => {
    if (window.confirm('Are you sure you want to delete this feed?')) {
      deleteMutation.mutate(id);
    }
  };

  const handleDiscoverFeeds = async () => {
    setDiscovering(true);
    setDiscoveryResult(null);

    try {
      const result = await discoverFeeds();
      if (result.success) {
        setDiscoveryResult({ discovered: result.discovered, added: result.added });
        queryClient.invalidateQueries({ queryKey: ['feeds'] });
        queryClient.invalidateQueries({ queryKey: ['feedHealth'] });

        // Auto-hide result after 5 seconds
        setTimeout(() => setDiscoveryResult(null), 5000);
      }
    } catch (error) {
      console.error('Discovery failed:', error);
      alert('Failed to discover feeds. See console for details.');
    } finally {
      setDiscovering(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 animate-spin text-gray-400" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded p-4">
        <div className="text-red-700 font-medium">Failed to load feeds</div>
        <div className="text-red-600 text-sm">{String(error)}</div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <Rss className="w-7 h-7 text-orange-500" />
          RSS Feed Management
        </h1>
        <div className="flex gap-2">
          <button
            onClick={handleDiscoverFeeds}
            disabled={discovering}
            className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {discovering ? (
              <RefreshCw className="w-4 h-4 animate-spin" />
            ) : (
              <Search className="w-4 h-4" />
            )}
            {discovering ? 'Discovering...' : 'Discover Feeds'}
          </button>
          <button
            onClick={() => setShowAddModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            <Plus className="w-4 h-4" />
            Add Feed
          </button>
        </div>
      </div>

      {/* Discovery Result */}
      {discoveryResult && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-center gap-2 text-green-700 font-medium">
            <CheckCircle className="w-5 h-5" />
            Discovery Complete!
          </div>
          <div className="mt-2 text-sm text-green-600">
            Found {discoveryResult.discovered} sources, added {discoveryResult.added} new feeds
          </div>
        </div>
      )}

      {/* Error Message */}
      {errorMessage && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-red-700 font-medium">
              <AlertTriangle className="w-5 h-5" />
              {errorMessage.includes('name') && errorMessage.includes('exists')
                ? '이름 중복'
                : errorMessage.includes('URL') && errorMessage.includes('exists')
                  ? 'URL 중복'
                  : '오류 발생'}
            </div>
            <button
              onClick={() => setErrorMessage(null)}
              className="text-red-500 hover:text-red-700"
            >
              <XCircle className="w-5 h-5" />
            </button>
          </div>
          <div className="mt-2 text-sm text-red-600">
            {errorMessage}
          </div>
          <div className="mt-2 text-xs text-red-500">
            {errorMessage.includes('name') && errorMessage.includes('exists')
              ? '💡 해결: 다른 이름을 사용하세요'
              : errorMessage.includes('URL') && errorMessage.includes('exists')
                ? '💡 해결: 이미 추가된 Feed입니다. 목록에서 확인하세요'
                : '💡 해결: 입력값을 확인하고 다시 시도하세요'}
          </div>
        </div>
      )}

      {/* Health Summary */}
      {health && <HealthSummary health={health} />}

      {/* Filters */}
      <div className="flex gap-2">
        {(['all', 'active', 'inactive', 'error'] as const).map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-3 py-1 rounded text-sm ${filter === f
              ? 'bg-blue-100 text-blue-700'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
          >
            {f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
      </div>

      {/* Feed Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredFeeds.map((feed) => (
          <FeedCard
            key={feed.id}
            feed={feed}
            onEdit={(f) => setEditingFeed(f)}
            onDelete={handleDelete}
            onToggle={(id) => toggleMutation.mutate(id)}
            onApplySuggestion={(feedId, newUrl) =>
              applySuggestionMutation.mutate({ feedId, newUrl })
            }
          />
        ))}
      </div>

      {filteredFeeds.length === 0 && (
        <div className="text-center py-12 text-gray-500">
          No feeds found for selected filter
        </div>
      )}

      {/* Modals */}
      {(showAddModal || editingFeed) && (
        <FeedFormModal
          feed={editingFeed}
          onSave={handleSave}
          onClose={() => {
            setShowAddModal(false);
            setEditingFeed(null);
          }}
        />
      )}
    </div>
  );
};

export default RssFeedManagement;

/**
 * Notification Settings UI Component
 * 
 * Features:
 * - Configure Telegram notifications
 * - Configure Slack notifications
 * - Set alert filters
 * - Test notifications
 * 
 * Author: AI Trading System
 * Date: 2025-11-15
 */

import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Bell,
  Send,
  Settings,
  CheckCircle,
  AlertTriangle,
  MessageSquare,
  Hash,
} from 'lucide-react';

// Types
interface NotificationSettings {
  telegram: {
    enabled: boolean;
    min_priority: string;
    rate_limit_per_minute: number;
    throttle_minutes: number;
  };
  slack: {
    enabled: boolean;
    rate_limit_per_minute: number;
  };
}

// API Configuration
const API_BASE = '/api';
const API_KEY = import.meta.env.VITE_API_KEY || '';

const apiHeaders = {
  'Content-Type': 'application/json',
  'X-API-Key': API_KEY,
};

// API Functions
const fetchNotificationSettings = async (): Promise<NotificationSettings> => {
  const response = await fetch(`${API_BASE}/api/notifications/settings`, {
    headers: apiHeaders,
  });
  if (!response.ok) throw new Error('Failed to fetch settings');
  return response.json();
};

const updateNotificationSettings = async (
  settings: Partial<NotificationSettings>
): Promise<NotificationSettings> => {
  const response = await fetch(`${API_BASE}/api/notifications/settings`, {
    method: 'PUT',
    headers: apiHeaders,
    body: JSON.stringify(settings),
  });
  if (!response.ok) throw new Error('Failed to update settings');
  return response.json();
};

const sendTestNotification = async (
  channel: string
): Promise<{ success: Record<string, boolean>; message: string }> => {
  const response = await fetch(`${API_BASE}/api/notifications/test`, {
    method: 'POST',
    headers: apiHeaders,
    body: JSON.stringify({ channel }),
  });
  if (!response.ok) throw new Error('Failed to send test notification');
  return response.json();
};

// Component
export const NotificationSettings: React.FC = () => {
  const queryClient = useQueryClient();

  // Form state
  const [telegramEnabled, setTelegramEnabled] = useState(false);
  const [telegramMinPriority, setTelegramMinPriority] = useState('HIGH');
  const [telegramRateLimit, setTelegramRateLimit] = useState(20);
  const [telegramThrottle, setTelegramThrottle] = useState(5);

  const [slackEnabled, setSlackEnabled] = useState(false);
  const [slackRateLimit, setSlackRateLimit] = useState(30);

  const [testChannel, setTestChannel] = useState('all');
  const [testResult, setTestResult] = useState<string | null>(null);

  // Queries
  const { data: settings, isLoading } = useQuery({
    queryKey: ['notification-settings'],
    queryFn: fetchNotificationSettings,
  });

  // Update form when settings load
  useEffect(() => {
    if (settings) {
      setTelegramEnabled(settings.telegram.enabled);
      setTelegramMinPriority(settings.telegram.min_priority);
      setTelegramRateLimit(settings.telegram.rate_limit_per_minute);
      setTelegramThrottle(settings.telegram.throttle_minutes);
      setSlackEnabled(settings.slack.enabled);
      setSlackRateLimit(settings.slack.rate_limit_per_minute);
    }
  }, [settings]);

  // Mutations
  const updateMutation = useMutation({
    mutationFn: updateNotificationSettings,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notification-settings'] });
      alert('Settings saved successfully!');
    },
    onError: (error: Error) => {
      alert(`Failed to save: ${error.message}`);
    },
  });

  const testMutation = useMutation({
    mutationFn: sendTestNotification,
    onSuccess: (data) => {
      setTestResult(data.message);
      setTimeout(() => setTestResult(null), 5000);
    },
    onError: (error: Error) => {
      setTestResult(`Error: ${error.message}`);
      setTimeout(() => setTestResult(null), 5000);
    },
  });

  // Handlers
  const handleSave = () => {
    updateMutation.mutate({
      telegram: {
        enabled: telegramEnabled,
        min_priority: telegramMinPriority,
        rate_limit_per_minute: telegramRateLimit,
        throttle_minutes: telegramThrottle,
      },
      slack: {
        enabled: slackEnabled,
        rate_limit_per_minute: slackRateLimit,
      },
    });
  };

  const handleTest = () => {
    testMutation.mutate(testChannel);
  };

  if (isLoading) {
    return <div className="p-6">Loading settings...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold flex items-center gap-2">
          <Bell className="w-6 h-6 text-blue-500" />
          Notification Settings
        </h2>
        <button
          onClick={handleSave}
          disabled={updateMutation.isPending}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
        >
          <Settings className="w-4 h-4" />
          {updateMutation.isPending ? 'Saving...' : 'Save Settings'}
        </button>
      </div>

      {/* Telegram Settings */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center gap-3 mb-4">
          <Send className="w-6 h-6 text-blue-400" />
          <h3 className="text-lg font-semibold">Telegram Notifications</h3>
          <label className="ml-auto flex items-center gap-2">
            <input
              type="checkbox"
              checked={telegramEnabled}
              onChange={(e) => setTelegramEnabled(e.target.checked)}
              className="w-5 h-5 text-blue-600"
            />
            <span className="text-sm font-medium">Enabled</span>
          </label>
        </div>

        <div className={`space-y-4 ${!telegramEnabled ? 'opacity-50' : ''}`}>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Minimum Priority Level
            </label>
            <select
              value={telegramMinPriority}
              onChange={(e) => setTelegramMinPriority(e.target.value)}
              disabled={!telegramEnabled}
              className="w-full border rounded-lg px-3 py-2"
            >
              <option value="LOW">LOW - All alerts</option>
              <option value="MEDIUM">MEDIUM - Important & above</option>
              <option value="HIGH">HIGH - High priority only</option>
              <option value="CRITICAL">CRITICAL - Critical alerts only</option>
            </select>
            <p className="text-xs text-gray-500 mt-1">
              Only alerts at this priority or higher will be sent
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Rate Limit (messages/minute): {telegramRateLimit}
            </label>
            <input
              type="range"
              min="5"
              max="60"
              value={telegramRateLimit}
              onChange={(e) => setTelegramRateLimit(parseInt(e.target.value))}
              disabled={!telegramEnabled}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-gray-500">
              <span>5/min</span>
              <span>60/min</span>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Duplicate Throttle (minutes): {telegramThrottle}
            </label>
            <input
              type="range"
              min="1"
              max="30"
              value={telegramThrottle}
              onChange={(e) => setTelegramThrottle(parseInt(e.target.value))}
              disabled={!telegramEnabled}
              className="w-full"
            />
            <p className="text-xs text-gray-500 mt-1">
              Prevent duplicate news alerts within this time window
            </p>
          </div>
        </div>
      </div>

      {/* Slack Settings */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center gap-3 mb-4">
          <Hash className="w-6 h-6 text-purple-500" />
          <h3 className="text-lg font-semibold">Slack Notifications</h3>
          <label className="ml-auto flex items-center gap-2">
            <input
              type="checkbox"
              checked={slackEnabled}
              onChange={(e) => setSlackEnabled(e.target.checked)}
              className="w-5 h-5 text-purple-600"
            />
            <span className="text-sm font-medium">Enabled</span>
          </label>
        </div>

        <div className={`space-y-4 ${!slackEnabled ? 'opacity-50' : ''}`}>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Rate Limit (messages/minute): {slackRateLimit}
            </label>
            <input
              type="range"
              min="5"
              max="60"
              value={slackRateLimit}
              onChange={(e) => setSlackRateLimit(parseInt(e.target.value))}
              disabled={!slackEnabled}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-gray-500">
              <span>5/min</span>
              <span>60/min</span>
            </div>
          </div>

          <div className="bg-gray-50 rounded p-3">
            <p className="text-sm text-gray-600">
              <strong>Note:</strong> Slack webhook URL must be configured in environment variables
              (SLACK_WEBHOOK_URL)
            </p>
          </div>
        </div>
      </div>

      {/* Test Notifications */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center gap-3 mb-4">
          <MessageSquare className="w-6 h-6 text-green-500" />
          <h3 className="text-lg font-semibold">Test Notifications</h3>
        </div>

        <div className="flex items-center gap-3">
          <select
            value={testChannel}
            onChange={(e) => setTestChannel(e.target.value)}
            className="border rounded-lg px-3 py-2"
          >
            <option value="all">All Channels</option>
            <option value="telegram">Telegram Only</option>
            <option value="slack">Slack Only</option>
          </select>

          <button
            onClick={handleTest}
            disabled={testMutation.isPending}
            className="bg-green-500 text-white px-4 py-2 rounded-lg hover:bg-green-600 disabled:opacity-50 flex items-center gap-2"
          >
            <Send className="w-4 h-4" />
            {testMutation.isPending ? 'Sending...' : 'Send Test'}
          </button>

          {testResult && (
            <div
              className={`flex items-center gap-2 px-3 py-2 rounded ${
                testResult.includes('success')
                  ? 'bg-green-100 text-green-700'
                  : 'bg-yellow-100 text-yellow-700'
              }`}
            >
              {testResult.includes('success') ? (
                <CheckCircle className="w-4 h-4" />
              ) : (
                <AlertTriangle className="w-4 h-4" />
              )}
              <span className="text-sm">{testResult}</span>
            </div>
          )}
        </div>

        <p className="text-xs text-gray-500 mt-3">
          This will send a test notification to the selected channel(s) to verify your
          configuration.
        </p>
      </div>

      {/* Help Section */}
      <div className="bg-blue-50 rounded-lg p-4">
        <h4 className="font-semibold text-blue-800 mb-2">Configuration Help</h4>
        <div className="text-sm text-blue-700 space-y-2">
          <p>
            <strong>Telegram Setup:</strong>
          </p>
          <ol className="list-decimal list-inside ml-2 space-y-1">
            <li>Create a bot with @BotFather on Telegram</li>
            <li>Get your bot token</li>
            <li>
              Get your chat ID (send a message to @userinfobot or use the bot API)
            </li>
            <li>Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env</li>
          </ol>

          <p className="mt-3">
            <strong>Slack Setup:</strong>
          </p>
          <ol className="list-decimal list-inside ml-2 space-y-1">
            <li>
              Go to{' '}
              <a
                href="https://api.slack.com/apps"
                target="_blank"
                rel="noopener noreferrer"
                className="underline"
              >
                Slack API
              </a>
            </li>
            <li>Create a new app and enable Incoming Webhooks</li>
            <li>Create a webhook for your channel</li>
            <li>Set SLACK_WEBHOOK_URL in .env</li>
          </ol>
        </div>
      </div>
    </div>
  );
};

export default NotificationSettings;

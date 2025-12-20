import React, { useState, useEffect } from 'react';
import { X, TrendingUp, TrendingDown, DollarSign, AlertCircle, CheckCircle } from 'lucide-react';

interface Signal {
  id: number;
  ticker: string;
  action: string;
  signal_type: string;
  confidence: number;
  reasoning: string;
  generated_at: string;
  entry_price?: number;
}

interface ExecuteTradeModalProps {
  signal: Signal | null;
  isOpen: boolean;
  onClose: () => void;
  onExecute: (signalId: number, entryPrice: number, shares: number) => Promise<void>;
}

export const ExecuteTradeModal: React.FC<ExecuteTradeModalProps> = ({
  signal,
  isOpen,
  onClose,
  onExecute
}) => {
  const [entryPrice, setEntryPrice] = useState<string>('');
  const [shares, setShares] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const [currentPrice, setCurrentPrice] = useState<number | null>(null);
  const [error, setError] = useState<string>('');
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    if (signal && isOpen) {
      // Fetch current market price
      fetchCurrentPrice(signal.ticker);
      setEntryPrice('');
      setShares('100');
      setError('');
      setSuccess(false);
    }
  }, [signal, isOpen]);

  const fetchCurrentPrice = async (ticker: string) => {
    try {
      setCurrentPrice(null);

      // Auto-detect API URL
      const API_BASE_URL = window.location.hostname === 'localhost'
        ? 'http://localhost:8001'
        : `http://${window.location.hostname}:8000`;

      const response = await fetch(`${API_BASE_URL}/api/market/price/${ticker}`);

      if (!response.ok) {
        throw new Error('Failed to fetch price');
      }

      const data = await response.json();

      if (data.price) {
        setCurrentPrice(data.price);
        setEntryPrice(data.price.toFixed(2));
      } else {
        // No price available
        setCurrentPrice(null);
        setEntryPrice('');
      }
    } catch (err) {
      console.error('Failed to fetch current price:', err);
      setCurrentPrice(null);
      setEntryPrice('');
    }
  };

  const handleExecute = async () => {
    if (!signal) return;

    const priceValue = parseFloat(entryPrice);
    const sharesValue = parseInt(shares);

    // Validation
    if (isNaN(priceValue) || priceValue <= 0) {
      setError('Invalid price');
      return;
    }

    if (isNaN(sharesValue) || sharesValue <= 0) {
      setError('Invalid number of shares');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      await onExecute(signal.id, priceValue, sharesValue);
      setSuccess(true);

      // Auto-close after success
      setTimeout(() => {
        onClose();
      }, 1500);
    } catch (err: any) {
      setError(err.message || 'Failed to execute trade');
    } finally {
      setIsLoading(false);
    }
  };

  const calculateTotal = () => {
    const priceValue = parseFloat(entryPrice);
    const sharesValue = parseInt(shares);

    if (isNaN(priceValue) || isNaN(sharesValue)) return 0;

    return priceValue * sharesValue;
  };

  if (!isOpen || !signal) return null;

  const total = calculateTotal();
  const isBuy = signal.action === 'BUY';

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div className="flex items-center gap-3">
            {isBuy ? (
              <TrendingUp className="w-6 h-6 text-green-500" />
            ) : (
              <TrendingDown className="w-6 h-6 text-red-500" />
            )}
            <div>
              <h2 className="text-xl font-bold">Execute Trade</h2>
              <p className="text-sm text-gray-500">
                {signal.ticker} - {signal.action}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Signal Info */}
          <div className="bg-gray-50 rounded-lg p-4 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Signal Type</span>
              <span className={`text-sm font-semibold px-2 py-1 rounded ${signal.signal_type === 'PRIMARY' ? 'bg-blue-100 text-blue-700' :
                  signal.signal_type === 'HIDDEN' ? 'bg-purple-100 text-purple-700' :
                    'bg-yellow-100 text-yellow-700'
                }`}>
                {signal.signal_type}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Confidence</span>
              <span className="text-sm font-semibold">{(signal.confidence * 100).toFixed(1)}%</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Current Market Price</span>
              <span className="text-sm font-semibold">
                {currentPrice ? `$${currentPrice.toFixed(2)}` : 'Loading...'}
              </span>
            </div>
          </div>

          {/* Trade Details Form */}
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Entry Price ($)
              </label>
              <div className="relative">
                <DollarSign className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="number"
                  step="0.01"
                  value={entryPrice}
                  onChange={(e) => setEntryPrice(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="0.00"
                  disabled={isLoading || success}
                />
              </div>
              <p className="mt-1 text-xs text-gray-500">
                Auto-filled with current market price
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Number of Shares
              </label>
              <input
                type="number"
                step="1"
                value={shares}
                onChange={(e) => setShares(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="100"
                disabled={isLoading || success}
              />
            </div>

            {/* Total Cost */}
            <div className="bg-blue-50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700">Total Investment</span>
                <span className="text-2xl font-bold text-blue-600">
                  ${total.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </span>
              </div>
              <p className="text-xs text-gray-500 mt-1">
                {shares} shares × ${entryPrice} per share
              </p>
            </div>
          </div>

          {/* Reasoning */}
          <div>
            <h3 className="text-sm font-medium text-gray-700 mb-2">Signal Reasoning</h3>
            <div className="bg-gray-50 rounded-lg p-3 text-sm text-gray-600 max-h-32 overflow-y-auto">
              {signal.reasoning}
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3 flex items-start gap-2">
              <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}

          {/* Success Message */}
          {success && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-3 flex items-start gap-2">
              <CheckCircle className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-green-700">Trade executed successfully!</p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 p-6 border-t bg-gray-50">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-700 hover:bg-gray-200 rounded-lg transition-colors"
            disabled={isLoading}
          >
            Cancel
          </button>
          <button
            onClick={handleExecute}
            disabled={isLoading || success || !entryPrice || !shares}
            className={`px-6 py-2 rounded-lg font-medium transition-colors flex items-center gap-2 ${isBuy
                ? 'bg-green-500 hover:bg-green-600 text-white'
                : 'bg-red-500 hover:bg-red-600 text-white'
              } disabled:opacity-50 disabled:cursor-not-allowed`}
          >
            {isLoading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent" />
                Executing...
              </>
            ) : success ? (
              <>
                <CheckCircle className="w-4 h-4" />
                Executed
              </>
            ) : (
              <>
                {isBuy ? 'Buy' : 'Sell'} {signal.ticker}
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

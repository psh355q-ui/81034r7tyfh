import React, { useState, useEffect } from 'react';
import { X, TrendingDown, DollarSign, AlertCircle, CheckCircle } from 'lucide-react';

interface Position {
  ticker: string;
  signal_type: string;
  action: string;
  entry_price: number;
  current_price: number;
  return_pct: number;
  days_held: number;
}

interface ClosePositionModalProps {
  position: Position | null;
  signalId: number | null;
  isOpen: boolean;
  onClose: () => void;
  onClosePosition: (signalId: number, exitPrice: number) => Promise<void>;
}

export const ClosePositionModal: React.FC<ClosePositionModalProps> = ({
  position,
  signalId,
  isOpen,
  onClose,
  onClosePosition
}) => {
  const [exitPrice, setExitPrice] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string>('');
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    if (position && isOpen) {
      // Auto-fill with current market price
      setExitPrice(position.current_price.toFixed(2));
      setError('');
      setSuccess(false);
    }
  }, [position, isOpen]);

  const handleClose = async () => {
    if (!position || !signalId) return;

    const priceValue = parseFloat(exitPrice);

    // Validation
    if (isNaN(priceValue) || priceValue <= 0) {
      setError('Invalid price');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      await onClosePosition(signalId, priceValue);
      setSuccess(true);

      // Auto-close after success
      setTimeout(() => {
        onClose();
      }, 1500);
    } catch (err: any) {
      setError(err.message || 'Failed to close position');
    } finally {
      setIsLoading(false);
    }
  };

  const calculateProfit = () => {
    if (!position) return { pct: 0, amount: 0 };

    const priceValue = parseFloat(exitPrice);
    if (isNaN(priceValue)) return { pct: 0, amount: 0 };

    let returnPct, profitAmount;

    if (position.action === 'BUY') {
      returnPct = ((priceValue - position.entry_price) / position.entry_price) * 100;
      profitAmount = priceValue - position.entry_price;
    } else {
      returnPct = ((position.entry_price - priceValue) / position.entry_price) * 100;
      profitAmount = position.entry_price - priceValue;
    }

    return { pct: returnPct, amount: profitAmount };
  };

  if (!isOpen || !position) return null;

  const { pct: profitPct, amount: profitAmount } = calculateProfit();
  const isProfit = profitAmount >= 0;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-xl w-full">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div className="flex items-center gap-3">
            <TrendingDown className="w-6 h-6 text-orange-500" />
            <div>
              <h2 className="text-xl font-bold">Close Position</h2>
              <p className="text-sm text-gray-500">{position.ticker}</p>
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
          {/* Position Info */}
          <div className="bg-gray-50 rounded-lg p-4 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Entry Price</span>
              <span className="text-sm font-semibold">${position.entry_price.toFixed(2)}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Current Price</span>
              <span className="text-sm font-semibold">${position.current_price.toFixed(2)}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Days Held</span>
              <span className="text-sm font-semibold">{position.days_held} days</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Current Return</span>
              <span className={`text-sm font-semibold ${position.return_pct >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {position.return_pct >= 0 ? '+' : ''}{position.return_pct.toFixed(2)}%
              </span>
            </div>
          </div>

          {/* Exit Price Input */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Exit Price ($)
            </label>
            <div className="relative">
              <DollarSign className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="number"
                step="0.01"
                value={exitPrice}
                onChange={(e) => setExitPrice(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="0.00"
                disabled={isLoading || success}
              />
            </div>
            <p className="mt-1 text-xs text-gray-500">
              Auto-filled with current market price
            </p>
          </div>

          {/* Projected Profit/Loss */}
          <div className={`rounded-lg p-4 ${isProfit ? 'bg-green-50' : 'bg-red-50'}`}>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700">Projected Return</span>
              <span className={`text-2xl font-bold ${isProfit ? 'text-green-600' : 'text-red-600'}`}>
                {profitPct >= 0 ? '+' : ''}{profitPct.toFixed(2)}%
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Profit/Loss per Share</span>
              <span className={`text-lg font-semibold ${isProfit ? 'text-green-600' : 'text-red-600'}`}>
                ${Math.abs(profitAmount).toFixed(2)} {isProfit ? 'Profit' : 'Loss'}
              </span>
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
              <p className="text-sm text-green-700">Position closed successfully!</p>
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
            onClick={handleClose}
            disabled={isLoading || success || !exitPrice}
            className="px-6 py-2 bg-orange-500 hover:bg-orange-600 text-white rounded-lg font-medium transition-colors flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent" />
                Closing...
              </>
            ) : success ? (
              <>
                <CheckCircle className="w-4 h-4" />
                Closed
              </>
            ) : (
              <>
                Close Position
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

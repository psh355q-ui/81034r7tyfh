/**
 * TickerAutocompleteInput Component
 * 
 * Reusable input component with S&P500 ticker autocomplete
 * Supports:
 * - Shadow tracking (shows suggestion in gray)
 * - Single ticker mode
 * - Multiple tickers mode (comma-separated)
 * - Tab to accept, Enter to submit
 * - Validation
 */

import React, { useState, useRef, useEffect } from 'react';
import { getAutocompleteSuggestion, validateTicker, convertKoreanToTicker } from '../../utils/tickerUtils';

interface TickerAutocompleteInputProps {
    value: string;
    onChange: (value: string) => void;
    onSubmit?: () => void;
    placeholder?: string;
    label?: string;
    multi?: boolean; // Support multiple tickers (comma-separated)
    error?: string | null;
    className?: string;
    disabled?: boolean;
}

export const TickerAutocompleteInput: React.FC<TickerAutocompleteInputProps> = ({
    value,
    onChange,
    onSubmit,
    placeholder = 'Enter ticker (e.g., AAPL)',
    label,
    multi = false,
    error,
    className = '',
    disabled = false,
}) => {
    const [autocompleteSuggestion, setAutocompleteSuggestion] = useState('');
    const inputRef = useRef<HTMLInputElement>(null);

    // Get autocomplete suggestion based on current cursor position
    const getMultiTickerSuggestion = (text: string, cursorPos: number): { suggestion: string; prefix: string } => {
        // Find the current ticker being typed (between last comma and cursor)
        const beforeCursor = text.substring(0, cursorPos);
        const lastCommaIndex = beforeCursor.lastIndexOf(',');
        const currentTicker = beforeCursor.substring(lastCommaIndex + 1).trim();

        if (!currentTicker) return { suggestion: '', prefix: '' };

        const suggestion = getAutocompleteSuggestion(currentTicker);
        if (suggestion && suggestion !== currentTicker.toUpperCase()) {
            return {
                suggestion: suggestion.slice(currentTicker.length),
                prefix: currentTicker.toUpperCase(),
            };
        }

        return { suggestion: '', prefix: '' };
    };

    // Handle input change
    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const newValue = e.target.value.toUpperCase();
        onChange(newValue);

        if (multi) {
            const cursorPos = e.target.selectionStart || newValue.length;
            const { suggestion } = getMultiTickerSuggestion(newValue, cursorPos);
            setAutocompleteSuggestion(suggestion);
        } else {
            const suggestion = getAutocompleteSuggestion(newValue);
            if (suggestion && suggestion !== newValue) {
                setAutocompleteSuggestion(suggestion.slice(newValue.length));
            } else {
                setAutocompleteSuggestion('');
            }
        }
    };

    // Handle keyboard events
    const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
        if (e.key === 'Tab' && autocompleteSuggestion) {
            e.preventDefault();

            if (multi) {
                const cursorPos = inputRef.current?.selectionStart || value.length;
                const beforeCursor = value.substring(0, cursorPos);
                const afterCursor = value.substring(cursorPos);
                const lastCommaIndex = beforeCursor.lastIndexOf(',');
                const prefix = beforeCursor.substring(0, lastCommaIndex + 1);
                const currentTicker = beforeCursor.substring(lastCommaIndex + 1).trim();

                const newValue = prefix + (prefix && prefix.trim() ? ' ' : '') + currentTicker + autocompleteSuggestion + afterCursor;
                onChange(newValue);
                setAutocompleteSuggestion('');
            } else {
                onChange(value + autocompleteSuggestion);
                setAutocompleteSuggestion('');
            }
        } else if (e.key === 'Enter') {
            e.preventDefault();

            // Convert Korean to ticker before submit  
            const convertedValue = multi
                ? value.split(',').map(t => convertKoreanToTicker(t.trim())).join(', ')
                : convertKoreanToTicker(value.trim());

            // Update value if conversion happened
            if (convertedValue !== value) {
                onChange(convertedValue);
                // Wait a tick for state to update, then submit
                setTimeout(() => {
                    if (onSubmit) onSubmit();
                }, 0);
            } else {
                // No conversion needed, submit immediately
                if (onSubmit) onSubmit();
            }
        }
    };

    // Render shadow text for autocomplete
    const renderShadow = () => {
        if (!autocompleteSuggestion) return null;

        if (multi) {
            const cursorPos = inputRef.current?.selectionStart || value.length;
            const beforeCursor = value.substring(0, cursorPos);
            const { prefix } = getMultiTickerSuggestion(value, cursorPos);

            return (
                <div className="absolute inset-0 pointer-events-none flex items-center px-3 overflow-hidden whitespace-nowrap">
                    <span className="text-transparent select-none">{beforeCursor}</span>
                    <span className="text-gray-400 select-none">{autocompleteSuggestion}</span>
                </div>
            );
        } else {
            return (
                <div className="absolute inset-0 pointer-events-none flex items-center px-3">
                    <span className="text-transparent select-none">{value}</span>
                    <span className="text-gray-400 select-none">{autocompleteSuggestion}</span>
                </div>
            );
        }
    };

    return (
        <div className={className}>
            {label && (
                <label className="block text-sm font-medium text-gray-700 mb-1">
                    {label}
                </label>
            )}
            <div className="relative">
                {renderShadow()}
                <input
                    ref={inputRef}
                    type="text"
                    value={value}
                    onChange={handleChange}
                    onKeyDown={handleKeyDown}
                    placeholder={placeholder}
                    disabled={disabled}
                    className={`block w-full px-3 py-2 border ${error ? 'border-red-500' : 'border-gray-300'
                        } rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed`}
                />
            </div>
            {autocompleteSuggestion && !disabled && (
                <p className="text-xs text-blue-600 mt-1">
                    Press Tab to autocomplete
                    {multi && ' (works after each comma)'}
                </p>
            )}
            {error && (
                <p className="text-xs text-red-600 mt-1">{error}</p>
            )}
        </div>
    );
};

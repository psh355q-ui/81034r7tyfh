/**
 * PersonaModeSwitcher - Mode Selection Dropdown
 * 
 * 📊 Data Sources:
 *   - PersonaContext: currentMode, setMode
 *   - personaApi: getPersonaModes
 * 
 * 📤 Used By:
 *   - Header.tsx
 * 
 * 📝 Notes:
 *   - Dropdown with 4 modes (Dividend, Long-Term, Trading, Aggressive)
 *   - Color-coded badges per mode
 *   - Shows loading state during mode switch
 */

import React, { useState, useRef, useEffect } from 'react';
import { ChevronDown, Check, Loader2 } from 'lucide-react';
import { usePersona, MODE_THEMES, PersonaMode } from '../../contexts/PersonaContext';

const MODE_LABELS: Record<PersonaMode, { label: string; description: string }> = {
    dividend: {
        label: '💰 배당',
        description: '안정적인 현금흐름 추구',
    },
    long_term: {
        label: '🎯 장기투자',
        description: '가치/성장주 장기 보유',
    },
    trading: {
        label: '📈 트레이딩',
        description: '단기 모멘텀 매매',
    },
    aggressive: {
        label: '🔥 공격적',
        description: '레버리지/고위험 투자',
    },
};

export const PersonaModeSwitcher: React.FC = () => {
    const { currentMode, setMode, isLoading } = usePersona();
    const [isOpen, setIsOpen] = useState(false);
    const dropdownRef = useRef<HTMLDivElement>(null);

    const currentTheme = MODE_THEMES[currentMode];
    const currentLabel = MODE_LABELS[currentMode];

    // Close dropdown when clicking outside
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
                setIsOpen(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const handleModeSelect = async (mode: PersonaMode) => {
        if (mode === currentMode) {
            setIsOpen(false);
            return;
        }
        try {
            await setMode(mode);
            setIsOpen(false);
        } catch (error) {
            console.error('Failed to switch mode:', error);
        }
    };

    return (
        <div className="relative" ref={dropdownRef}>
            <button
                onClick={() => setIsOpen(!isOpen)}
                disabled={isLoading}
                className={`
          flex items-center gap-2 px-3 py-2 rounded-lg
          border-2 transition-all duration-200
          ${isLoading ? 'opacity-50 cursor-wait' : 'hover:shadow-md cursor-pointer'}
        `}
                style={{
                    borderColor: currentTheme.primary,
                    backgroundColor: currentTheme.bgClass.includes('green') ? '#ECFDF5' :
                        currentTheme.bgClass.includes('blue') ? '#EFF6FF' :
                            currentTheme.bgClass.includes('amber') ? '#FFFBEB' :
                                '#FEF2F2',
                }}
            >
                {isLoading ? (
                    <Loader2 className="animate-spin" size={16} />
                ) : (
                    <span className="text-lg">{currentLabel.label.split(' ')[0]}</span>
                )}
                <span className="font-medium text-gray-700 hidden sm:inline">
                    {currentLabel.label.split(' ')[1]}
                </span>
                <ChevronDown
                    size={16}
                    className={`text-gray-500 transition-transform ${isOpen ? 'rotate-180' : ''}`}
                />
            </button>

            {/* Dropdown Menu */}
            {isOpen && (
                <div className="absolute right-0 mt-2 w-56 bg-white rounded-lg shadow-xl border border-gray-200 z-50">
                    <div className="py-1">
                        {(Object.keys(MODE_LABELS) as PersonaMode[]).map((mode) => {
                            const theme = MODE_THEMES[mode];
                            const label = MODE_LABELS[mode];
                            const isSelected = mode === currentMode;

                            return (
                                <button
                                    key={mode}
                                    onClick={() => handleModeSelect(mode)}
                                    className={`
                    w-full px-4 py-3 text-left flex items-center justify-between
                    hover:bg-gray-50 transition-colors
                    ${isSelected ? 'bg-gray-50' : ''}
                  `}
                                >
                                    <div>
                                        <div className="flex items-center gap-2">
                                            <span
                                                className="w-3 h-3 rounded-full"
                                                style={{ backgroundColor: theme.primary }}
                                            />
                                            <span className="font-medium text-gray-900">{label.label}</span>
                                        </div>
                                        <p className="text-xs text-gray-500 mt-0.5 ml-5">
                                            {label.description}
                                        </p>
                                    </div>
                                    {isSelected && <Check size={16} className="text-green-500" />}
                                </button>
                            );
                        })}
                    </div>
                </div>
            )}
        </div>
    );
};

export default PersonaModeSwitcher;

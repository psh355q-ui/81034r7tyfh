/**
 * PersonaContext - Global Persona State Management
 * 
 * 📊 Data Sources:
 *   - API: /api/persona/current (current mode)
 *   - API: /api/persona/switch (mode switching)
 *   - LocalStorage: persona_mode (persistence)
 * 
 * 🔗 Dependencies:
 *   - react: createContext, useContext, useState, useEffect
 *   - ../services/personaApi: getCurrentMode, switchPersonaMode
 * 
 * 📤 Used By:
 *   - App.tsx (Provider wrapper)
 *   - Header.tsx (ModeSwitcher)
 *   - Dashboard components
 * 
 * 📝 Notes:
 *   - Provides persona mode to all components
 *   - Handles mode switching with API call
 *   - Persists mode in localStorage
 */

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import {
    PersonaMode,
    PersonaModeInfo,
    getCurrentMode,
    switchPersonaMode as apiSwitchMode
} from '../services/personaApi';

// Theme configuration per mode
const MODE_THEMES: Record<PersonaMode, { primary: string; secondary: string; bgClass: string; icon: string }> = {
    dividend: {
        primary: '#10B981', // green-500
        secondary: '#6B7280',
        bgClass: 'bg-green-50',
        icon: '💰',
    },
    long_term: {
        primary: '#3B82F6', // blue-500
        secondary: '#64748B',
        bgClass: 'bg-blue-50',
        icon: '🎯',
    },
    trading: {
        primary: '#F59E0B', // amber-500
        secondary: '#EA580C',
        bgClass: 'bg-amber-50',
        icon: '📈',
    },
    aggressive: {
        primary: '#EF4444', // red-500
        secondary: '#F43F5E',
        bgClass: 'bg-red-50',
        icon: '🔥',
    },
};

interface PersonaContextType {
    currentMode: PersonaMode;
    modeInfo: PersonaModeInfo | null;
    theme: typeof MODE_THEMES[PersonaMode];
    isLoading: boolean;
    error: string | null;
    setMode: (mode: PersonaMode) => Promise<void>;
    refreshMode: () => Promise<void>;
}

const PersonaContext = createContext<PersonaContextType | undefined>(undefined);

export const usePersona = () => {
    const context = useContext(PersonaContext);
    if (!context) {
        throw new Error('usePersona must be used within PersonaProvider');
    }
    return context;
};

interface PersonaProviderProps {
    children: ReactNode;
}

export const PersonaProvider: React.FC<PersonaProviderProps> = ({ children }) => {
    const [currentMode, setCurrentMode] = useState<PersonaMode>(() => {
        const saved = localStorage.getItem('persona_mode');
        return (saved as PersonaMode) || 'trading';
    });
    const [modeInfo, setModeInfo] = useState<PersonaModeInfo | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const theme = MODE_THEMES[currentMode];

    // Fetch current mode from backend on mount
    const refreshMode = async () => {
        try {
            setIsLoading(true);
            setError(null);
            const data = await getCurrentMode();
            setModeInfo(data);

            // Only update state and localStorage if backend has a different mode
            // This preserves user's preference when backend has default value
            const savedMode = localStorage.getItem('persona_mode');
            if (savedMode && savedMode !== data.mode) {
                // Keep the saved mode - user preference takes priority
                console.log(`[PersonaContext] Preserving saved mode: ${savedMode} (backend: ${data.mode})`);
                setCurrentMode(savedMode as PersonaMode);
                // Don't update localStorage - keep user preference
            } else {
                setCurrentMode(data.mode as PersonaMode);
                localStorage.setItem('persona_mode', data.mode);
            }
        } catch (err) {
            console.error('Failed to fetch current mode:', err);
            // On API failure, keep using the saved mode from localStorage
            // Don't set error - just silently continue with saved preference
            const savedMode = localStorage.getItem('persona_mode');
            if (savedMode) {
                console.log(`[PersonaContext] API failed, using saved mode: ${savedMode}`);
                setCurrentMode(savedMode as PersonaMode);
            }
        } finally {
            setIsLoading(false);
        }
    };

    // Switch mode
    const setMode = async (mode: PersonaMode) => {
        try {
            setIsLoading(true);
            setError(null);
            const result = await apiSwitchMode(mode);
            if (result.success) {
                setCurrentMode(mode);
                localStorage.setItem('persona_mode', mode);
                await refreshMode(); // Refresh full mode info
            }
        } catch (err) {
            console.error('Failed to switch mode:', err);
            setError('Failed to switch mode');
            throw err;
        } finally {
            setIsLoading(false);
        }
    };

    // Load mode on mount
    useEffect(() => {
        refreshMode();
    }, []);

    return (
        <PersonaContext.Provider
            value={{
                currentMode,
                modeInfo,
                theme,
                isLoading,
                error,
                setMode,
                refreshMode,
            }}
        >
            {children}
        </PersonaContext.Provider>
    );
};

export { MODE_THEMES };
export type { PersonaMode };

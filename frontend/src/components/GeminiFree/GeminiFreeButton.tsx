/**
 * Gemini Free Chat Floating Button
 * 
 * 우측 하단 플로팅 버튼
 * 클릭 시 무료 Gemini 채팅 열림
 */

import React, { useState, useEffect } from 'react';
import { Zap } from 'lucide-react';
import { GeminiFreePopup } from './GeminiFreePopup';
import { getGeminiUsage } from '../../services/geminiFreeService';

export const GeminiFreeButton: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [isHovered, setIsHovered] = useState(false);
  const [remainingRequests, setRemainingRequests] = useState<number | null>(null);

  // Fetch remaining requests on mount
  useEffect(() => {
    const fetchUsage = async () => {
      try {
        const stats = await getGeminiUsage();
        setRemainingRequests(stats.requests.remaining);
      } catch (err) {
        console.error('Failed to fetch usage:', err);
      }
    };

    fetchUsage();
    // Refresh every 5 minutes
    const interval = setInterval(fetchUsage, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <>
      {/* Floating Button */}
      <div className="fixed bottom-6 right-6 z-40">
        <button
          onClick={() => setIsOpen(!isOpen)}
          onMouseEnter={() => setIsHovered(true)}
          onMouseLeave={() => setIsHovered(false)}
          className={`
            relative flex items-center justify-center
            w-14 h-14 rounded-full shadow-lg
            transition-all duration-300 transform
            ${isOpen 
              ? 'bg-gray-600 hover:bg-gray-700' 
              : 'bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600 hover:scale-110'
            }
            focus:outline-none focus:ring-4 focus:ring-blue-300
          `}
          aria-label={isOpen ? 'Gemini Chat 닫기' : 'Gemini Chat 열기'}
        >
          <Zap className="text-white" size={24} />
          
          {/* Badge: Remaining requests */}
          {!isOpen && remainingRequests !== null && (
            <div className="absolute -top-1 -right-1 bg-green-500 text-white text-xs font-bold rounded-full min-w-[20px] h-5 flex items-center justify-center px-1">
              {remainingRequests > 999 ? '1K+' : remainingRequests}
            </div>
          )}
        </button>

        {/* Tooltip */}
        {isHovered && !isOpen && (
          <div className="absolute bottom-full right-0 mb-2 px-3 py-2 bg-gray-900 text-white text-sm rounded-lg whitespace-nowrap animate-fade-in">
            <div className="font-medium">Gemini 무료 Chat</div>
            <div className="text-xs text-gray-300">
              {remainingRequests !== null 
                ? `오늘 ${remainingRequests}회 남음 • $0`
                : '1,500회/일 무료'}
            </div>
            <div className="absolute top-full right-4 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-900" />
          </div>
        )}
      </div>

      {/* Chat Popup */}
      <GeminiFreePopup isOpen={isOpen} onClose={() => setIsOpen(false)} />
    </>
  );
};

export default GeminiFreeButton;

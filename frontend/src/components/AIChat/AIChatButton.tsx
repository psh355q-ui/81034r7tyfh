/**
 * AI Chat Floating Button
 * 
 * 우측 하단에 고정된 플로팅 버튼
 * 클릭 시 AI Chat 팝업 열림
 */

import React, { useState } from 'react';
import { MessageSquare, X } from 'lucide-react';
import { AIChatPopup } from './AIChatPopup';

export const AIChatButton: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [isHovered, setIsHovered] = useState(false);

  return (
    <>
      {/* Floating Button */}
      <div className="fixed bottom-6 right-6 z-40">
        <button
          onClick={() => setIsOpen(!isOpen)}
          onMouseEnter={() => setIsHovered(true)}
          onMouseLeave={() => setIsHovered(false)}
          className={`
            flex items-center justify-center
            w-14 h-14 rounded-full shadow-lg
            transition-all duration-300 transform
            ${isOpen 
              ? 'bg-red-500 hover:bg-red-600 rotate-90' 
              : 'bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 hover:scale-110'
            }
            focus:outline-none focus:ring-4 focus:ring-blue-300
          `}
          aria-label={isOpen ? 'AI Chat 닫기' : 'AI Chat 열기'}
        >
          {isOpen ? (
            <X className="text-white" size={24} />
          ) : (
            <MessageSquare className="text-white" size={24} />
          )}
        </button>

        {/* Tooltip */}
        {isHovered && !isOpen && (
          <div className="absolute bottom-full right-0 mb-2 px-3 py-2 bg-gray-900 text-white text-sm rounded-lg whitespace-nowrap animate-fade-in">
            AI에게 질문하기
            <div className="absolute top-full right-4 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-900" />
          </div>
        )}
      </div>

      {/* Chat Popup */}
      <AIChatPopup isOpen={isOpen} onClose={() => setIsOpen(false)} />
    </>
  );
};

export default AIChatButton;

/**
 * GlobalMacro Page - 글로벌 매크로 분석 페이지
 * 
 * Phase F5: 프론트엔드 시각화
 * 
 * 글로벌 매크로 대시보드와 추론 뷰어를 통합한 페이지
 */

import React, { useState } from 'react';
import GlobalMacroPanel from '../components/GlobalMacroPanel';
import LogicTraceViewer from '../components/LogicTraceViewer';

type TabType = 'macro' | 'trace';

const GlobalMacro: React.FC = () => {
    const [activeTab, setActiveTab] = useState<TabType>('macro');

    return (
        <div className="global-macro-page">
            <style>{`
        .global-macro-page {
          min-height: 100vh;
          background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        }
        
        .page-nav {
          display: flex;
          gap: 8px;
          padding: 16px 24px;
          background: rgba(0, 0, 0, 0.2);
          border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .nav-tab {
          padding: 12px 24px;
          border: none;
          border-radius: 8px;
          font-size: 14px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s;
          color: #a0aec0;
          background: transparent;
        }
        
        .nav-tab:hover {
          background: rgba(255, 255, 255, 0.1);
          color: #fff;
        }
        
        .nav-tab.active {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: #fff;
        }
        
        .page-content {
          min-height: calc(100vh - 80px);
        }
      `}</style>

            <nav className="page-nav">
                <button
                    className={`nav-tab ${activeTab === 'macro' ? 'active' : ''}`}
                    onClick={() => setActiveTab('macro')}
                >
                    🌍 글로벌 매크로
                </button>
                <button
                    className={`nav-tab ${activeTab === 'trace' ? 'active' : ''}`}
                    onClick={() => setActiveTab('trace')}
                >
                    🔍 추론 추적
                </button>
            </nav>

            <div className="page-content">
                {activeTab === 'macro' && <GlobalMacroPanel />}
                {activeTab === 'trace' && <LogicTraceViewer />}
            </div>
        </div>
    );
};

export default GlobalMacro;

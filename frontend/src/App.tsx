import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AnalysisProvider } from './contexts/AnalysisContext';
import { GlobalAnalysisProgress } from './components/News/GlobalAnalysisProgress';
import { Layout } from './components/Layout/Layout';
import { Dashboard } from './pages/Dashboard';
import { Analysis } from './pages/Analysis';
import { Monitor } from './pages/Monitor';
import { Settings } from './pages/Settings';
import { NewsAggregation } from './pages/NewsAggregation';
import { AIReviewPage } from './pages/AIReviewPage';
import { Logs } from './pages/Logs';
import { RssFeedManagement } from './pages/RssFeedManagement';
import { CEOAnalysis } from './pages/CEOAnalysis';
import { IncrementalDashboard } from './pages/IncrementalDashboard';
import { NewsAnalysisLab } from './pages/NewsAnalysisLab';
import Reports from './pages/Reports';
import AdvancedAnalytics from './pages/AdvancedAnalytics';
import DeepReasoning from './pages/DeepReasoning';
import TradingDashboard from './pages/TradingDashboard';
import SignalDetail from './pages/SignalDetail';
import PortfolioManagement from './pages/PortfolioManagement';
import BacktestDashboard from './pages/BacktestDashboard';
import GlobalMacro from './pages/GlobalMacro';
import WarRoomPage from './pages/WarRoomPage';
// import { AIChatButton } from './components/AIChat/AIChatButton';
// import { GeminiFreeButton } from './components/GeminiFree/GeminiFreeButton';

const App: React.FC = () => {
  return (
    <AnalysisProvider>
      <Router>
        <Layout>
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/analysis" element={<Analysis />} />
            <Route path="/ceo-analysis" element={<CEOAnalysis />} />
            <Route path="/incremental" element={<IncrementalDashboard />} />
            <Route path="/monitor" element={<Monitor />} />
            <Route path="/news" element={<NewsAggregation />} />
            <Route path="/news-analysis-lab" element={<NewsAnalysisLab />} />
            <Route path="/rss-management" element={<RssFeedManagement />} />
            <Route path="/ai-review" element={<AIReviewPage />} />
            <Route path="/reports" element={<Reports />} />
            <Route path="/advanced-analytics" element={<AdvancedAnalytics />} />
            <Route path="/deep-reasoning" element={<DeepReasoning />} />
            <Route path="/trading" element={<TradingDashboard />} />
            <Route path="/trading/signal/:id" element={<SignalDetail />} />
            <Route path="/backtest" element={<BacktestDashboard />} />
            <Route path="/portfolio" element={<PortfolioManagement />} />
            <Route path="/global-macro" element={<GlobalMacro />} />
            <Route path="/war-room" element={<WarRoomPage />} />
            <Route path="/logs" element={<Logs />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </Layout>

        {/* Global Analysis Progress - visible on ALL pages */}
        <GlobalAnalysisProgress />

        {/* AI Chat 플로팅 버튼 - 전역 */}
        {/* <AIChatButton /> */}

        {/* Gemini 무료 Chat 버튼 */}
        {/* <GeminiFreeButton /> */}
      </Router>
    </AnalysisProvider>
  );
};

export default App;

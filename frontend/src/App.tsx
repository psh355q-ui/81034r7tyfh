import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AnalysisProvider } from './contexts/AnalysisContext';
import { PersonaProvider } from './contexts/PersonaContext';
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
import { NewsAnalysisLab } from './pages/NewsAnalysisLab';
import Reports from './pages/Reports';
import AdvancedAnalytics from './pages/AdvancedAnalytics';
import DeepReasoning from './pages/DeepReasoning';
import TradingDashboard from './pages/TradingDashboard';
import SignalDetail from './pages/SignalDetail';
import BacktestDashboard from './pages/BacktestDashboard';

import WarRoomPage from './pages/WarRoomPage';
import IntelligenceDashboard from './pages/IntelligenceDashboard';
import { VideoIntelligence } from './pages/VideoIntelligence';
import SignalConsolidationPage from './pages/SignalConsolidationPage';
import { CostReport } from './pages/CostReport';
import DataBackfill from './pages/DataBackfill';
import Orders from './pages/Orders';  // 🆕 Phase 27
import PartitionDashboard from './pages/PartitionDashboard'; // 🆕 Phase 6.2 Partition Dashboard
import Portfolio from './pages/Portfolio';  // 🆕 Phase 27 (new portfolio page)
import DividendDashboard from './pages/DividendDashboard';  // 🆕 Phase 21 (dividend intelligence)
import AccountabilityDashboard from './pages/AccountabilityDashboard';  // 🆕 Phase 29 (AI accountability)
import FailureLearningDashboard from './pages/FailureLearningDashboard';  // 🆕 Phase 29 확장 (auto-learning)
import MultiAssetDashboard from './pages/MultiAssetDashboard';  // 🆕 Phase 30 (multi-asset support)
import PortfolioOptimizationPage from './pages/PortfolioOptimizationPage';  // 🆕 Phase 31 (portfolio optimization)
import CorrelationDashboard from './pages/CorrelationDashboard';  // 🆕 Phase 32 (asset correlation)
import LiveDashboard from './pages/LiveDashboard'; // 🆕 Phase 4 (real-time execution)

import Performance from './pages/Performance';  // 🆕 Phase 25.2 (performance dashboard)
import FeedbackDashboard from './pages/FeedbackDashboard'; // 🆕 Phase 6
import StrategyDashboard from './pages/StrategyDashboard'; // 🆕 Phase 5 (Multi-Strategy Orchestration)
// ... (imports)

// ...


// import { AIChatButton } from './components/AIChat/AIChatButton';
// import { GeminiFreeButton } from './components/GeminiFree/GeminiFreeButton';

const App: React.FC = () => {
  return (
    <PersonaProvider>
      <AnalysisProvider>
        <Router>
          <Layout>

            <Routes>
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/analysis" element={<Analysis />} />
              <Route path="/ceo-analysis" element={<CEOAnalysis />} />
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

              <Route path="/partitions" element={<PartitionDashboard />} /> {/* 🆕 Phase 6.2 AI Partitions */}
              <Route path="/portfolio" element={<Portfolio />} />  {/* 🆕 Phase 6 Integrated Portfolio */}
              <Route path="/orders" element={<Orders />} />  {/* 🆕 Phase 27 Orders Page */}
              <Route path="/performance" element={<Performance />} />  {/* 🆕 Phase 25.2 Performance Dashboard */}
              <Route path="/dividend" element={<DividendDashboard />} />  {/* 🆕 Phase 21 Dividend Intelligence */}
              <Route path="/accountability" element={<AccountabilityDashboard />} />  {/* 🆕 Phase 29 Accountability System */}
              <Route path="/learning" element={<FailureLearningDashboard />} />  {/* 🆕 Phase 29 확장 Auto-Learning */}
              <Route path="/multi-asset" element={<MultiAssetDashboard />} />  {/* 🆕 Phase 30 Multi-Asset Support */}
              <Route path="/portfolio-optimization" element={<PortfolioOptimizationPage />} />  {/* 🆕 Phase 31 Portfolio Optimization */}
              <Route path="/correlation" element={<CorrelationDashboard />} />  {/* 🆕 Phase 32 Asset Correlation */}

              <Route path="/feedback" element={<FeedbackDashboard />} />  {/* 🆕 Phase 6 */}
              <Route path="/strategies" element={<StrategyDashboard />} />  {/* 🆕 Phase 5 Multi-Strategy Orchestration */}

              <Route path="/intelligence" element={<IntelligenceDashboard />} />  {/* 🆕 Market Intelligence v2.0 */}
              <Route path="/video-intelligence" element={<VideoIntelligence />} />  {/* 🆕 Video Thinking Layer */}
              <Route path="/war-room" element={<WarRoomPage />} />
              <Route path="/signal-consolidation" element={<SignalConsolidationPage />} />
              <Route path="/cost-report" element={<CostReport />} />
              <Route path="/data-backfill" element={<DataBackfill />} />
              <Route path="/live-dashboard" element={<LiveDashboard />} />  {/* 🆕 Phase 4 Real-time Dashboard */}
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
    </PersonaProvider>
  );
};

export default App;

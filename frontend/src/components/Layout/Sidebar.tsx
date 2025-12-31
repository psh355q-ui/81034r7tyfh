import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  LayoutDashboard, TrendingUp, Activity, Newspaper, Rss, FileText,
  FileSearch, Settings, X, MessageSquare, TrendingDown, BarChart3,
  LineChart, Brain, Zap, PieChart, TestTube2, Wallet, Globe,
  ChevronDown, ChevronRight, DollarSign, Database, Target, Coins, GraduationCap,
  Network
} from 'lucide-react';

interface NavItem {
  path: string;
  icon: React.ElementType;
  label: string;
}

interface NavCategory {
  title: string;
  items: NavItem[];
}

interface SidebarProps {
  isOpen?: boolean;
  onClose?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ isOpen = true, onClose }) => {
  const location = useLocation();
  const [expandedCategories, setExpandedCategories] = useState<string[]>(['Overview', 'Trading & Strategy', 'Portfolio & Risk']);

  const navCategories: NavCategory[] = [
    {
      title: 'Overview',
      items: [
        { path: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
        { path: '/portfolio', icon: PieChart, label: 'Portfolio' },
        { path: '/dividend', icon: DollarSign, label: 'Dividend Intelligence' },
      ]
    },
    {
      title: 'Trading & Strategy',
      items: [
        { path: '/war-room', icon: MessageSquare, label: 'AI War Room' },
        { path: '/trading', icon: Zap, label: 'Trading Signals' },
        { path: '/backtest', icon: TestTube2, label: 'Backtest' },
        { path: '/deep-reasoning', icon: Brain, label: 'Deep Reasoning' },
      ]
    },
    {
      title: 'Analysis',
      items: [
        { path: '/global-macro', icon: Globe, label: 'Global Macro' },
        { path: '/ceo-analysis', icon: MessageSquare, label: 'CEO Analysis' },
        { path: '/analysis', icon: TrendingUp, label: 'Analysis' },
        { path: '/cost-report', icon: DollarSign, label: 'Emergency Cost' },
        { path: '/advanced-analytics', icon: LineChart, label: 'Advanced Analytics' },
        { path: '/ai-review', icon: FileText, label: 'AI Review' },
      ]
    },
    {
      title: 'Data & News',
      items: [
        { path: '/data-backfill', icon: Database, label: 'Data Backfill' },
        { path: '/news', icon: Newspaper, label: 'News' },
        { path: '/rss-management', icon: Rss, label: 'RSS Management' },
      ]
    },
    {
      title: 'System & Operations',
      items: [
        { path: '/monitor', icon: Activity, label: 'Monitor' },
        { path: '/accountability', icon: Target, label: 'Accountability' },
        { path: '/learning', icon: GraduationCap, label: 'Auto-Learning' },
        { path: '/reports', icon: BarChart3, label: 'Reports' },
        { path: '/incremental', icon: TrendingDown, label: 'Cost Savings' },
        { path: '/logs', icon: FileSearch, label: 'Logs' },
        { path: '/settings', icon: Settings, label: 'Settings' },
      ]
    },
    {
      title: 'Under Development',
      items: [
        { path: '/signal-consolidation', icon: BarChart3, label: 'Signal Consolidation' },
        { path: '/multi-asset', icon: Coins, label: 'Multi-Asset' },
        { path: '/portfolio-optimization', icon: Target, label: 'Portfolio Optimization' },
        { path: '/correlation', icon: Network, label: 'Asset Correlation' },
      ]
    }
  ];

  // Auto-expand category based on current route
  useEffect(() => {
    const currentCategory = navCategories.find(cat =>
      cat.items.some(item => item.path === location.pathname)
    );

    if (currentCategory && !expandedCategories.includes(currentCategory.title)) {
      setExpandedCategories(prev => [...prev, currentCategory.title]);
    }
  }, [location.pathname]);

  const toggleCategory = (title: string) => {
    setExpandedCategories(prev =>
      prev.includes(title)
        ? prev.filter(t => t !== title)
        : [...prev, title]
    );
  };

  const isActive = (path: string) => location.pathname === path;

  return (
    <>
      {/* Mobile Overlay */}
      <div
        className={`fixed inset-0 bg-black bg-opacity-50 z-20 lg:hidden transition-opacity duration-200 ${isOpen ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'
          }`}
        onClick={onClose}
      />

      {/* Sidebar */}
      <aside className={`
        fixed lg:static inset-y-0 left-0 z-30 w-64 bg-gray-900 text-white min-h-screen 
        transform transition-transform duration-200 ease-in-out overflow-y-auto
        ${isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
      `}>
        <div className="flex items-center justify-between p-4 lg:hidden">
          <span className="text-xl font-bold">Menu</span>
          <button onClick={onClose} className="p-1 hover:bg-gray-800 rounded">
            <X size={24} />
          </button>
        </div>

        <div className="p-4 space-y-4">
          {navCategories.map((category) => (
            <div key={category.title} className="space-y-1">
              <button
                onClick={() => toggleCategory(category.title)}
                className="flex items-center justify-between w-full px-2 py-1.5 text-xs font-semibold text-gray-400 uppercase tracking-wider hover:text-white transition-colors"
              >
                <span>{category.title}</span>
                {expandedCategories.includes(category.title) ? (
                  <ChevronDown size={14} />
                ) : (
                  <ChevronRight size={14} />
                )}
              </button>

              <div className={`space-y-1 ${expandedCategories.includes(category.title) ? 'block' : 'hidden'}`}>
                {category.items.map(({ path, icon: Icon, label }) => (
                  <Link
                    key={path}
                    to={path}
                    onClick={() => onClose?.()}
                    className={`flex items-center space-x-3 px-4 py-2 text-sm rounded-lg transition-colors ${isActive(path)
                      ? 'bg-blue-600 text-white'
                      : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                      }`}
                  >
                    <Icon size={18} />
                    <span>{label}</span>
                  </Link>
                ))}
              </div>
            </div>
          ))}
        </div>

        <div className="p-4 border-t border-gray-800">
          <div className="text-xs text-gray-500">
            <p>Version 1.0.0</p>
            <p>© 2025 AI Trading System</p>
          </div>
        </div>
      </aside>
    </>
  );
};

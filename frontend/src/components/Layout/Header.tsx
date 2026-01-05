import React, { useState } from 'react';
import { Bell, User, Menu } from 'lucide-react';
import { NotificationCenter, Notification } from '../Notifications/NotificationCenter';
import { PersonaModeSwitcher } from '../Persona/ModeSwitcher';

const MOCK_NOTIFICATIONS: Notification[] = [

  {
    id: '1',
    type: 'warning',
    title: 'High Volatility Detected',
    message: 'AAPL volatility has exceeded the safety threshold (2.5%).',
    timestamp: new Date(Date.now() - 1000 * 60 * 5), // 5 mins ago
    read: false,
  },
  {
    id: '2',
    type: 'success',
    title: 'Buy Order Executed',
    message: 'Successfully bought 10 shares of MSFT at $350.20.',
    timestamp: new Date(Date.now() - 1000 * 60 * 30), // 30 mins ago
    read: false,
  },
  {
    id: '3',
    type: 'info',
    title: 'Market Open',
    message: 'US Markets are now open. Trading session started.',
    timestamp: new Date(Date.now() - 1000 * 60 * 60 * 2), // 2 hours ago
    read: true,
  },
];

interface HeaderProps {
  onMenuClick?: () => void;
}

export const Header: React.FC<HeaderProps> = ({ onMenuClick }) => {
  const [isNotificationsOpen, setIsNotificationsOpen] = useState(false);
  const [notifications, setNotifications] = useState<Notification[]>(MOCK_NOTIFICATIONS);

  const handleMarkAsRead = (id: string) => {
    setNotifications(prev => prev.map(n =>
      n.id === id ? { ...n, read: true } : n
    ));
  };

  const handleClearAll = () => {
    setNotifications([]);
  };

  const unreadCount = notifications.filter(n => !n.read).length;

  return (
    <header className="bg-white shadow-sm border-b border-gray-200 relative">
      <div className="flex items-center justify-between px-4 lg:px-6 py-4">
        <div className="flex items-center gap-3">
          <button
            onClick={onMenuClick}
            className="lg:hidden p-2 text-gray-600 hover:bg-gray-100 rounded-lg"
          >
            <Menu size={24} />
          </button>
          <h2 className="text-xl lg:text-2xl font-bold text-gray-900 truncate">AI Trading System</h2>
        </div>

        <div className="flex items-center gap-2 lg:gap-4">
          {/* Persona Mode Switcher */}
          <PersonaModeSwitcher />

          <div className="relative">
            <button

              onClick={() => setIsNotificationsOpen(!isNotificationsOpen)}
              className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors relative"
            >
              <Bell size={20} />
              {unreadCount > 0 && (
                <span className="absolute top-1.5 right-1.5 w-2.5 h-2.5 bg-red-500 rounded-full border-2 border-white"></span>
              )}
            </button>

            <NotificationCenter
              isOpen={isNotificationsOpen}
              onClose={() => setIsNotificationsOpen(false)}
              notifications={notifications}
              onMarkAsRead={handleMarkAsRead}
              onClearAll={handleClearAll}
            />
          </div>

          <button className="flex items-center gap-2 p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors">
            <User size={20} />
            <span className="hidden lg:inline text-sm font-medium">Admin</span>
          </button>
        </div>
      </div>
    </header>
  );
};

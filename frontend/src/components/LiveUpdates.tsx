import React, { useState, useEffect } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';
import { Bell, AlertCircle, TrendingUp, Package, Users, Newspaper } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface LiveUpdate {
  id: string;
  type: 'score' | 'player_status' | 'lineup_alert' | 'waiver' | 'trade' | 'news';
  title: string;
  message: string;
  timestamp: Date;
  icon: React.ReactNode;
  color: string;
}

export function LiveUpdates() {
  const [updates, setUpdates] = useState<LiveUpdate[]>([]);
  const [showNotifications, setShowNotifications] = useState(true);

  const { isConnected } = useWebSocket({
    onScoreUpdate: (data) => {
      addUpdate({
        type: 'score',
        title: 'Score Update',
        message: `${data.team_name}: ${data.current_score} pts (was ${data.previous_score})`,
        icon: <TrendingUp className="w-4 h-4" />,
        color: 'text-green-600',
      });
    },
    onPlayerStatusChange: (data) => {
      addUpdate({
        type: 'player_status',
        title: 'Player Status Change',
        message: `${data.player_name} is now ${data.new_status}`,
        icon: <AlertCircle className="w-4 h-4" />,
        color: data.new_status === 'ACTIVE' ? 'text-green-600' : 'text-red-600',
      });
    },
    onLineupAlert: (data) => {
      addUpdate({
        type: 'lineup_alert',
        title: 'Lineup Alert',
        message: data.message || `${data.issues?.length || 0} lineup issues detected`,
        icon: <Bell className="w-4 h-4" />,
        color: 'text-yellow-600',
      });
    },
    onWaiverProcessed: (data) => {
      addUpdate({
        type: 'waiver',
        title: 'Waiver Processed',
        message: data.message,
        icon: <Package className="w-4 h-4" />,
        color: 'text-blue-600',
      });
    },
    onTradeUpdate: (data) => {
      addUpdate({
        type: 'trade',
        title: 'Trade Update',
        message: data.message,
        icon: <Users className="w-4 h-4" />,
        color: 'text-purple-600',
      });
    },
    onLeagueNews: (data) => {
      addUpdate({
        type: 'news',
        title: 'League News',
        message: data.message,
        icon: <Newspaper className="w-4 h-4" />,
        color: 'text-gray-600',
      });
    },
  });

  const addUpdate = (update: Omit<LiveUpdate, 'id' | 'timestamp'>) => {
    const newUpdate: LiveUpdate = {
      ...update,
      id: `${Date.now()}-${Math.random()}`,
      timestamp: new Date(),
    };
    
    setUpdates((prev) => [newUpdate, ...prev].slice(0, 10)); // Keep last 10 updates
  };

  // Auto-dismiss old updates
  useEffect(() => {
    const interval = setInterval(() => {
      setUpdates((prev) =>
        prev.filter((update) => {
          const age = Date.now() - update.timestamp.getTime();
          return age < 30000; // Keep updates for 30 seconds
        })
      );
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  if (!showNotifications) {
    return (
      <button
        onClick={() => setShowNotifications(true)}
        className="fixed bottom-4 right-4 bg-blue-600 text-white p-3 rounded-full shadow-lg hover:bg-blue-700 transition-colors"
      >
        <Bell className="w-6 h-6" />
        {updates.length > 0 && (
          <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
            {updates.length}
          </span>
        )}
      </button>
    );
  }

  return (
    <div className="fixed bottom-4 right-4 w-96 max-h-96 bg-white rounded-lg shadow-xl border border-gray-200 overflow-hidden">
      <div className="p-4 bg-gray-50 border-b border-gray-200 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Bell className="w-5 h-5 text-gray-600" />
          <h3 className="font-semibold text-gray-900">Live Updates</h3>
          {isConnected ? (
            <span className="text-xs text-green-600 flex items-center gap-1">
              <span className="w-2 h-2 bg-green-600 rounded-full animate-pulse" />
              Connected
            </span>
          ) : (
            <span className="text-xs text-gray-500">Disconnected</span>
          )}
        </div>
        <button
          onClick={() => setShowNotifications(false)}
          className="text-gray-400 hover:text-gray-600"
        >
          ×
        </button>
      </div>

      <div className="overflow-y-auto max-h-80">
        <AnimatePresence>
          {updates.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              <Bell className="w-8 h-8 mx-auto mb-2 text-gray-400" />
              <p className="text-sm">No updates yet</p>
              <p className="text-xs mt-1">Updates will appear here in real-time</p>
            </div>
          ) : (
            updates.map((update) => (
              <motion.div
                key={update.id}
                initial={{ opacity: 0, x: 100 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -100 }}
                className="p-4 border-b border-gray-100 hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-start gap-3">
                  <div className={`mt-1 ${update.color}`}>{update.icon}</div>
                  <div className="flex-1">
                    <h4 className="text-sm font-medium text-gray-900">{update.title}</h4>
                    <p className="text-sm text-gray-600 mt-1">{update.message}</p>
                    <p className="text-xs text-gray-400 mt-1">
                      {formatTime(update.timestamp)}
                    </p>
                  </div>
                </div>
              </motion.div>
            ))
          )}
        </AnimatePresence>
      </div>

      {updates.length > 0 && (
        <div className="p-2 bg-gray-50 border-t border-gray-200">
          <button
            onClick={() => setUpdates([])}
            className="text-xs text-gray-500 hover:text-gray-700 w-full text-center"
          >
            Clear all
          </button>
        </div>
      )}
    </div>
  );
}

function formatTime(date: Date): string {
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  const seconds = Math.floor(diff / 1000);
  
  if (seconds < 60) {
    return 'Just now';
  } else if (seconds < 3600) {
    const minutes = Math.floor(seconds / 60);
    return `${minutes}m ago`;
  } else {
    return date.toLocaleTimeString();
  }
}
import { useEffect, useRef, useCallback, useState } from 'react';
import { io, Socket } from 'socket.io-client';
import { useAuthStore } from '../store/useAuthStore';

interface DraftUpdate {
  type: 'pick_made' | 'user_on_clock' | 'status_change' | 'sync_error';
  data: any;
  timestamp: string;
}

interface LiveUpdate {
  data: any;
  timestamp: string;
}

interface UseWebSocketOptions {
  draftSessionId?: string | number;
  onPickMade?: (data: any) => void;
  onUserOnClock?: (data: any) => void;
  onStatusChange?: (data: any) => void;
  onSyncError?: (data: any) => void;
  // Live update handlers
  onScoreUpdate?: (data: any) => void;
  onPlayerStatusChange?: (data: any) => void;
  onLineupAlert?: (data: any) => void;
  onWaiverProcessed?: (data: any) => void;
  onTradeUpdate?: (data: any) => void;
  onLeagueNews?: (data: any) => void;
}

export function useWebSocket({
  draftSessionId,
  onPickMade,
  onUserOnClock,
  onStatusChange,
  onSyncError,
  onScoreUpdate,
  onPlayerStatusChange,
  onLineupAlert,
  onWaiverProcessed,
  onTradeUpdate,
  onLeagueNews,
}: UseWebSocketOptions) {
  const socketRef = useRef<Socket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<DraftUpdate | null>(null);
  const { user } = useAuthStore();

  const connect = useCallback(() => {
    if (!draftSessionId || !user) return;

    // Connect to WebSocket server (same as API server)
    const socket = io(import.meta.env.VITE_WS_URL || 'http://localhost:8000', {
      path: '/socket.io',
      transports: ['websocket', 'polling'],
      auth: {
        token: localStorage.getItem('auth_token'),
      },
    });

    socketRef.current = socket;

    // Connection events
    socket.on('connect', () => {
      console.log('WebSocket connected');
      setIsConnected(true);

      // Join draft session room
      socket.emit('join_draft_session', {
        user_id: user.id,
        draft_session_id: draftSessionId,
      });
    });

    socket.on('disconnect', () => {
      console.log('WebSocket disconnected');
      setIsConnected(false);
    });

    socket.on('error', (error) => {
      console.error('WebSocket error:', error);
    });

    // Draft events
    socket.on('joined_draft', (data) => {
      console.log('Joined draft session:', data);
    });

    socket.on('draft_update', (update: DraftUpdate) => {
      console.log('Draft update received:', update);
      setLastUpdate(update);

      // Call appropriate handler based on update type
      switch (update.type) {
        case 'pick_made':
          onPickMade?.(update.data);
          break;
        case 'user_on_clock':
          onUserOnClock?.(update.data);
          break;
        case 'status_change':
          onStatusChange?.(update.data);
          break;
        case 'sync_error':
          onSyncError?.(update.data);
          break;
      }
    });

    // Live update events
    socket.on('score_update', (update: LiveUpdate) => {
      console.log('Score update received:', update);
      onScoreUpdate?.(update.data);
    });

    socket.on('player_status_change', (update: LiveUpdate) => {
      console.log('Player status change received:', update);
      onPlayerStatusChange?.(update.data);
    });

    socket.on('lineup_alert', (update: LiveUpdate) => {
      console.log('Lineup alert received:', update);
      onLineupAlert?.(update.data);
    });

    socket.on('waiver_processed', (update: LiveUpdate) => {
      console.log('Waiver processed received:', update);
      onWaiverProcessed?.(update.data);
    });

    socket.on('trade_update', (update: LiveUpdate) => {
      console.log('Trade update received:', update);
      onTradeUpdate?.(update.data);
    });

    socket.on('league_news', (update: LiveUpdate) => {
      console.log('League news received:', update);
      onLeagueNews?.(update.data);
    });

    return () => {
      socket.disconnect();
    };
  }, [
    draftSessionId,
    user,
    onPickMade,
    onUserOnClock,
    onStatusChange,
    onSyncError,
    onScoreUpdate,
    onPlayerStatusChange,
    onLineupAlert,
    onWaiverProcessed,
    onTradeUpdate,
    onLeagueNews,
  ]);

  const disconnect = useCallback(() => {
    if (socketRef.current) {
      // Leave draft session
      if (draftSessionId) {
        socketRef.current.emit('leave_draft_session', {
          draft_session_id: draftSessionId,
        });
      }

      socketRef.current.disconnect();
      socketRef.current = null;
      setIsConnected(false);
    }
  }, [draftSessionId]);

  // Auto-connect when component mounts
  useEffect(() => {
    const cleanup = connect();
    return () => {
      cleanup?.();
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    isConnected,
    lastUpdate,
    connect,
    disconnect,
  };
}
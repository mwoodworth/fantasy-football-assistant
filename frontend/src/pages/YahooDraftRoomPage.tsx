import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Loader2, AlertCircle } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/common/Card';
import { Alert } from '../components/common/Alert';
import { YahooDraftBoard } from '../components/yahoo/YahooDraftBoard';
import { YahooDraftRecommendations } from '../components/yahoo/YahooDraftRecommendations';
import { YahooDraftLiveTracker } from '../components/yahoo/YahooDraftLiveTracker';
import { yahooService } from '../services/yahoo';
import type { YahooLeague, YahooDraftSession } from '../services/yahooTypes';
import { toast } from '../utils/toast';
import { useWebSocket } from '../hooks/useWebSocket';

export const YahooDraftRoomPage: React.FC = () => {
  const { leagueKey } = useParams<{ leagueKey: string }>();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [league, setLeague] = useState<YahooLeague | null>(null);
  const [draftSession, setDraftSession] = useState<YahooDraftSession | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showDraftPositionModal, setShowDraftPositionModal] = useState(false);
  const [draftPosition, setDraftPosition] = useState(1);

  // WebSocket connection for real-time updates
  const { isConnected, lastMessage } = useWebSocket();

  useEffect(() => {
    if (leagueKey) {
      loadLeagueAndDraft();
    }
  }, [leagueKey]);

  useEffect(() => {
    // Handle WebSocket messages
    if (lastMessage && draftSession) {
      const data = JSON.parse(lastMessage.data);
      
      if (data.session_id === draftSession.session_id) {
        switch (data.type) {
          case 'user_on_clock':
            toast.success('It\'s your turn to pick!', {
              duration: 10000,
              icon: '🎯'
            });
            // Refresh draft status
            refreshDraftStatus();
            break;
            
          case 'pick_made':
            if (data.is_user_pick) {
              toast.success(`You drafted ${data.player_name}`);
            }
            // Refresh will happen in live tracker
            break;
            
          case 'turn_approaching':
            toast.info(`Your turn in ${data.picks_away} picks`, {
              duration: 5000
            });
            break;
            
          case 'draft_completed':
            toast.success('Draft completed!');
            setDraftSession(prev => prev ? { ...prev, status: 'completed' } : null);
            break;
            
          case 'sync_error':
            toast.error(`Sync error: ${data.error}`);
            break;
        }
      }
    }
  }, [lastMessage, draftSession]);

  const loadLeagueAndDraft = async () => {
    try {
      setLoading(true);
      setError(null);

      // Get league details
      const leagueData = await yahooService.getLeagueDetails(leagueKey!);
      setLeague(leagueData.league);

      // Check if there's an existing draft session
      // For now, we'll need to handle this differently since we don't have a way
      // to get existing sessions by league. In a real implementation, you'd
      // probably want to add an endpoint for this.
      
      // Check if league is in draft mode
      if (leagueData.league.draft_status === 'drafting') {
        setShowDraftPositionModal(true);
      } else if (leagueData.league.draft_status === 'predraft') {
        setError('Draft has not started yet');
      } else {
        setError('Draft has already been completed');
      }
    } catch (err) {
      console.error('Failed to load league:', err);
      setError('Failed to load league data');
    } finally {
      setLoading(false);
    }
  };

  const startDraftSession = async () => {
    if (!leagueKey) return;

    try {
      const session = await yahooService.startDraftSession(leagueKey, draftPosition);
      setDraftSession(session);
      setShowDraftPositionModal(false);
      toast.success('Draft session started!');
    } catch (err) {
      console.error('Failed to start draft session:', err);
      toast.error('Failed to start draft session');
    }
  };

  const refreshDraftStatus = async () => {
    if (!draftSession) return;

    try {
      const session = await yahooService.getDraftSession(draftSession.session_id);
      setDraftSession(session);
    } catch (err) {
      console.error('Failed to refresh draft status:', err);
    }
  };

  const handleSyncToggle = async (enabled: boolean) => {
    if (!draftSession) return;

    try {
      await yahooService.toggleDraftSync(draftSession.session_id, enabled);
      setDraftSession(prev => prev ? { ...prev, live_sync_enabled: enabled } : null);
      toast.success(`Live sync ${enabled ? 'enabled' : 'disabled'}`);
    } catch (err) {
      console.error('Failed to toggle sync:', err);
      toast.error('Failed to toggle sync');
    }
  };

  const handleManualSync = async () => {
    if (!draftSession) return;

    try {
      const result = await yahooService.syncDraft(draftSession.session_id);
      if (result.success) {
        await refreshDraftStatus();
        toast.success('Draft synced successfully');
      }
    } catch (err) {
      console.error('Failed to sync draft:', err);
      toast.error('Failed to sync draft');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <div>{error}</div>
        </Alert>
      </div>
    );
  }

  if (showDraftPositionModal) {
    return (
      <div className="container mx-auto px-4 py-8">
        <Card className="max-w-md mx-auto">
          <CardHeader>
            <CardTitle>Enter Your Draft Position</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-muted-foreground">
              What position are you drafting from in {league?.name}?
            </p>
            <div>
              <label className="block text-sm font-medium mb-2">
                Draft Position (1-{league?.num_teams || 12})
              </label>
              <input
                type="number"
                min="1"
                max={league?.num_teams || 12}
                value={draftPosition}
                onChange={(e) => setDraftPosition(parseInt(e.target.value) || 1)}
                className="w-full px-3 py-2 border rounded-md"
              />
            </div>
            <button
              onClick={startDraftSession}
              className="w-full bg-primary text-white py-2 rounded-md hover:bg-primary-dark"
            >
              Start Draft Session
            </button>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!draftSession) {
    return (
      <div className="container mx-auto px-4 py-8">
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <div>No active draft session</div>
        </Alert>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">Yahoo Draft Room</h1>
        <p className="text-muted-foreground mt-2">
          {league?.name} - Pick #{draftSession.user_draft_position}
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main draft board */}
        <div className="lg:col-span-2">
          <YahooDraftBoard
            session={draftSession}
            onSyncToggle={handleSyncToggle}
            onManualSync={handleManualSync}
            onRefresh={refreshDraftStatus}
          />
        </div>

        {/* Side panel */}
        <div className="space-y-6">
          {/* Live tracker */}
          <YahooDraftLiveTracker
            sessionId={draftSession.session_id}
            onPickMade={refreshDraftStatus}
          />

          {/* Recommendations */}
          <YahooDraftRecommendations
            sessionId={draftSession.session_id}
            currentPick={draftSession.current_pick}
            isUserTurn={draftSession.picks_until_turn === 0}
          />
        </div>
      </div>
    </div>
  );
};
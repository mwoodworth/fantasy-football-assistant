import React, { useState, useEffect } from 'react';
import { Activity, Clock } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../common/Card';
import { Badge } from '../common/Badge';
import { yahooService } from '../../services/yahoo';
import type { YahooDraftStatus, YahooDraftEvent } from '../../services/yahooTypes';

interface YahooDraftLiveTrackerProps {
  sessionId: number;
  onPickMade?: () => void;
}

export const YahooDraftLiveTracker: React.FC<YahooDraftLiveTrackerProps> = ({
  sessionId,
  onPickMade
}) => {
  const [draftStatus, setDraftStatus] = useState<YahooDraftStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDraftStatus();
    
    // Poll for updates every 10 seconds
    const interval = setInterval(() => {
      if (draftStatus?.sync_enabled) {
        loadDraftStatus();
      }
    }, 10000);

    return () => clearInterval(interval);
  }, [sessionId, draftStatus?.sync_enabled]);

  const loadDraftStatus = async () => {
    try {
      const status = await yahooService.getLiveDraftStatus(sessionId);
      
      // Check if new picks were made
      if (draftStatus && status.recent_picks.length > 0) {
        const latestPick = status.recent_picks[0];
        const previousLatest = draftStatus.recent_picks[0];
        
        if (!previousLatest || latestPick.pick_number > previousLatest.pick_number) {
          onPickMade?.();
        }
      }
      
      setDraftStatus(status);
    } catch (err) {
      console.error('Failed to load draft status:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMinutes = Math.floor((now.getTime() - date.getTime()) / 60000);
    
    if (diffMinutes < 1) return 'Just now';
    if (diffMinutes < 60) return `${diffMinutes}m ago`;
    return `${Math.floor(diffMinutes / 60)}h ago`;
  };

  if (loading || !draftStatus) {
    return (
      <Card>
        <CardContent className="py-8 text-center text-muted-foreground">
          Loading draft status...
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Activity className="w-5 h-5" />
          Live Tracker
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Current status */}
        <div className="flex items-center justify-between">
          <span className="text-sm text-muted-foreground">Status</span>
          {draftStatus.is_user_turn ? (
            <Badge variant="warning" className="animate-pulse">
              Your Turn!
            </Badge>
          ) : draftStatus.picks_until_turn <= 3 ? (
            <Badge variant="secondary">
              {draftStatus.picks_until_turn} picks away
            </Badge>
          ) : (
            <Badge variant="default">
              {draftStatus.picks_until_turn} picks away
            </Badge>
          )}
        </div>

        {/* Current pick info */}
        <div className="border-t pt-4">
          <p className="text-sm font-medium mb-2">
            Pick {draftStatus.current_pick} - Round {draftStatus.current_round}
          </p>
        </div>

        {/* Recent picks */}
        <div className="border-t pt-4">
          <h4 className="text-sm font-medium mb-3">Recent Picks</h4>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {draftStatus.recent_picks.length === 0 ? (
              <p className="text-sm text-muted-foreground">No picks made yet</p>
            ) : (
              draftStatus.recent_picks.map((pick, index) => (
                <div
                  key={`${pick.pick_number}-${index}`}
                  className="flex items-center justify-between text-sm py-2 border-b last:border-0"
                >
                  <div className="flex-1">
                    <span className="font-medium">
                      Pick {pick.pick_number}
                    </span>
                    <span className="text-muted-foreground mx-2">•</span>
                    <span className="font-medium">{pick.player_name}</span>
                  </div>
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <Clock className="w-3 h-3" />
                    <span className="text-xs">{formatTime(pick.timestamp)}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
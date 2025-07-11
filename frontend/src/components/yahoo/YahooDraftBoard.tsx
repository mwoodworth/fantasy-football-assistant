import React, { useState, useEffect } from 'react';
import { RefreshCw, Wifi, WifiOff, Clock, Users } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../common/Card';
import { Button } from '../common/Button';
import { Badge } from '../common/Badge';
import { YahooDraftBoardGrid } from './YahooDraftBoardGrid';
import type { YahooDraftSession } from '../../services/yahooTypes';

interface YahooDraftBoardProps {
  session: YahooDraftSession;
  onSyncToggle: (enabled: boolean) => void;
  onManualSync: () => void;
  onRefresh: () => void;
}

export const YahooDraftBoard: React.FC<YahooDraftBoardProps> = ({
  session,
  onSyncToggle,
  onManualSync,
  onRefresh
}) => {
  const [lastSyncTime, setLastSyncTime] = useState<string>('Never');

  useEffect(() => {
    if (session.last_sync) {
      const updateSyncTime = () => {
        const syncDate = new Date(session.last_sync!);
        const now = new Date();
        const diffSeconds = Math.floor((now.getTime() - syncDate.getTime()) / 1000);
        
        if (diffSeconds < 60) {
          setLastSyncTime(`${diffSeconds}s ago`);
        } else if (diffSeconds < 3600) {
          setLastSyncTime(`${Math.floor(diffSeconds / 60)}m ago`);
        } else {
          setLastSyncTime(`${Math.floor(diffSeconds / 3600)}h ago`);
        }
      };

      updateSyncTime();
      const interval = setInterval(updateSyncTime, 10000);
      return () => clearInterval(interval);
    }
  }, [session.last_sync]);

  const getDraftProgress = () => {
    const totalPicks = session.num_teams * 15; // Assuming 15 rounds
    const currentProgress = ((session.current_pick - 1) / totalPicks) * 100;
    return Math.min(currentProgress, 100);
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex justify-between items-center">
          <CardTitle className="flex items-center gap-2">
            <Users className="w-5 h-5" />
            Draft Board
          </CardTitle>
          
          <div className="flex items-center gap-2">
            {/* Sync status */}
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Clock className="w-4 h-4" />
              <span>Last sync: {lastSyncTime}</span>
            </div>

            {/* Sync toggle */}
            <Button
              variant="outline"
              size="sm"
              onClick={() => onSyncToggle(!session.live_sync_enabled)}
              className={session.live_sync_enabled ? 'text-green-600' : 'text-gray-600'}
            >
              {session.live_sync_enabled ? (
                <>
                  <Wifi className="w-4 h-4 mr-1" />
                  Live
                </>
              ) : (
                <>
                  <WifiOff className="w-4 h-4 mr-1" />
                  Paused
                </>
              )}
            </Button>

            {/* Manual sync */}
            <Button
              variant="outline"
              size="sm"
              onClick={onManualSync}
            >
              <RefreshCw className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Draft status */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <p className="text-sm text-muted-foreground">Current Pick</p>
            <p className="text-2xl font-bold">{session.current_pick}</p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Round</p>
            <p className="text-2xl font-bold">{session.current_round}</p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Your Position</p>
            <p className="text-2xl font-bold">#{session.user_draft_position}</p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Picks Until You</p>
            <p className="text-2xl font-bold">
              {session.picks_until_turn === 0 ? (
                <Badge variant="warning">Your Turn!</Badge>
              ) : (
                session.picks_until_turn
              )}
            </p>
          </div>
        </div>

        {/* Progress bar */}
        <div>
          <div className="flex justify-between text-sm text-muted-foreground mb-2">
            <span>Draft Progress</span>
            <span>{Math.round(getDraftProgress())}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-primary h-2 rounded-full transition-all duration-300"
              style={{ width: `${getDraftProgress()}%` }}
            />
          </div>
        </div>

        {/* Draft board grid */}
        <YahooDraftBoardGrid
          draftedPlayers={session.drafted_players}
          numTeams={session.num_teams}
          currentPick={session.current_pick}
          userTeamKey={session.user_draft_position.toString()}
        />
      </CardContent>
    </Card>
  );
};
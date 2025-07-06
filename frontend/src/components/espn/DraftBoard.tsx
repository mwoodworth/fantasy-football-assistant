import { Clock, Users } from 'lucide-react';
import { type DraftSession } from '../../services/espn';
import { Card } from '../common/Card';
import { Badge } from '../common/Badge';

interface DraftBoardProps {
  session: DraftSession;
}

export function DraftBoard({ session }: DraftBoardProps) {
  const draftedPlayers = session.drafted_players || [];
  const recentPicks = draftedPlayers.slice(-5).reverse(); // Last 5 picks, most recent first

  const getPositionColor = (position: string) => {
    const colors: Record<string, string> = {
      'QB': 'bg-red-100 text-red-800',
      'RB': 'bg-green-100 text-green-800',
      'WR': 'bg-blue-100 text-blue-800',
      'TE': 'bg-yellow-100 text-yellow-800',
      'K': 'bg-gray-100 text-gray-800',
      'DEF': 'bg-purple-100 text-purple-800',
    };
    return colors[position] || 'bg-gray-100 text-gray-800';
  };

  const getRoundPosition = (pickNumber: number, teamCount: number) => {
    const round = Math.ceil(pickNumber / teamCount);
    const positionInRound = ((pickNumber - 1) % teamCount) + 1;
    return { round, positionInRound };
  };

  const formatTimeAgo = (timestamp: string) => {
    const now = new Date();
    const pickTime = new Date(timestamp);
    const diffMs = now.getTime() - pickTime.getTime();
    const diffMins = Math.floor(diffMs / (1000 * 60));
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    
    return pickTime.toLocaleDateString();
  };

  return (
    <div className="space-y-4">
      {/* Draft Progress */}
      <Card className="p-4">
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-medium flex items-center gap-2">
            <Clock className="h-4 w-4" />
            Draft Progress
          </h3>
          <span className="text-sm text-gray-500">
            {session.current_pick} / {session.total_picks} picks
          </span>
        </div>
        
        <div className="w-full bg-gray-200 rounded-full h-2 mb-3">
          <div 
            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${(session.current_pick / session.total_picks) * 100}%` }}
          />
        </div>
        
        <div className="text-sm text-gray-600 space-y-1">
          <div className="flex justify-between">
            <span>Round {session.current_round} of 16</span>
            <span>{Math.round((session.current_pick / session.total_picks) * 100)}% complete</span>
          </div>
        </div>
      </Card>

      {/* Recent Picks */}
      <Card className="p-4">
        <h3 className="font-medium mb-3 flex items-center gap-2">
          <Users className="h-4 w-4" />
          Recent Picks
        </h3>
        
        {recentPicks.length > 0 ? (
          <div className="space-y-3">
            {recentPicks.map((pick: any) => {
              const { round, positionInRound } = getRoundPosition(
                pick.pick_number, 
                session.league?.team_count || 10
              );
              
              return (
                <div 
                  key={`${pick.pick_number}-${pick.player_id}`}
                  className={`p-3 rounded border ${
                    pick.drafted_by_user 
                      ? 'bg-green-50 border-green-200' 
                      : 'bg-gray-50 border-gray-200'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-medium">{pick.player_name}</span>
                        <Badge className={getPositionColor(pick.position)} size="sm">
                          {pick.position}
                        </Badge>
                        <span className="text-sm text-gray-500">{pick.team}</span>
                        {pick.drafted_by_user && (
                          <Badge variant="success" size="sm">Your Pick</Badge>
                        )}
                      </div>
                      <div className="text-xs text-gray-600">
                        Pick #{pick.pick_number} • Round {round}, Position {positionInRound}
                      </div>
                    </div>
                    
                    <div className="text-right text-xs text-gray-500">
                      {pick.timestamp && formatTimeAgo(pick.timestamp)}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="text-center py-6 text-gray-500">
            <Users className="h-8 w-8 mx-auto mb-2 text-gray-300" />
            <p>No picks made yet</p>
            <p className="text-sm">Draft picks will appear here</p>
          </div>
        )}
      </Card>

      {/* Draft Stats */}
      <Card className="p-4">
        <h3 className="font-medium mb-3">Position Breakdown</h3>
        
        {draftedPlayers.length > 0 ? (
          <div className="space-y-2">
            {Object.entries(
              draftedPlayers.reduce((acc: Record<string, number>, pick: any) => {
                acc[pick.position] = (acc[pick.position] || 0) + 1;
                return acc;
              }, {})
            ).map(([position, count]) => (
              <div key={position} className="flex justify-between text-sm">
                <span className="flex items-center gap-2">
                  <Badge className={getPositionColor(position)} size="sm">
                    {position}
                  </Badge>
                </span>
                <span className="text-gray-600">{count as number} picked</span>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-500 text-sm">No position data yet</p>
        )}
      </Card>
    </div>
  );
}
import { useQuery } from '@tanstack/react-query';
import { DashboardService } from '../../services/dashboard';
import type { LiveScore } from '../../services/dashboard';
import { Badge } from '../common/Badge';
import { Clock } from 'lucide-react';
import { cn } from '../../utils/cn';

export function LiveScoreTicker() {
  const { data: liveScores, isLoading } = useQuery({
    queryKey: ['liveScores'],
    queryFn: () => DashboardService.getLiveScores(),
    refetchInterval: 15000, // Update every 15 seconds
    staleTime: 5000,
  });

  if (isLoading || !liveScores || liveScores.length === 0) {
    return null;
  }

  const getGameStatusBadge = (score: LiveScore) => {
    if (score.isComplete) {
      return <Badge variant="secondary" size="sm">Final</Badge>;
    }
    
    if (score.quarter === 'Halftime') {
      return <Badge variant="warning" size="sm">Halftime</Badge>;
    }
    
    return (
      <Badge variant="success" size="sm" className="animate-pulse">
        {score.quarter} {score.timeRemaining}
      </Badge>
    );
  };

  const getScoreColor = (teamScore: number, opponentScore: number) => {
    if (teamScore > opponentScore) {
      return 'text-green-700 font-bold';
    } else if (teamScore < opponentScore) {
      return 'text-red-600';
    }
    return 'text-gray-700';
  };

  return (
    <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg p-4 text-white">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold flex items-center">
          <Clock className="w-4 h-4 mr-2" />
          Live Scores
        </h3>
        <div className="flex items-center space-x-1">
          <div className="w-2 h-2 bg-red-400 rounded-full animate-pulse"></div>
          <span className="text-sm text-blue-100">Live</span>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {liveScores.map((score) => (
          <div
            key={score.gameId}
            className="bg-white/10 backdrop-blur-sm rounded-lg p-3 border border-white/20"
          >
            <div className="flex justify-between items-center mb-2">
              <span className="text-xs text-blue-100">{score.gameTime}</span>
              {getGameStatusBadge(score)}
            </div>

            <div className="space-y-2">
              {/* Away Team */}
              <div className="flex justify-between items-center">
                <div className="flex items-center space-x-2">
                  <span className="font-semibold text-sm">{score.awayTeam}</span>
                </div>
                <span className={cn(
                  'text-lg font-bold',
                  getScoreColor(score.awayScore, score.homeScore)
                )}>
                  {score.awayScore}
                </span>
              </div>

              {/* Home Team */}
              <div className="flex justify-between items-center">
                <div className="flex items-center space-x-2">
                  <span className="font-semibold text-sm">{score.homeTeam}</span>
                </div>
                <span className={cn(
                  'text-lg font-bold',
                  getScoreColor(score.homeScore, score.awayScore)
                )}>
                  {score.homeScore}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
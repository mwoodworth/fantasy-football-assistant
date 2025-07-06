import { useState } from 'react';
import { useParams, useLocation, Navigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  Clock, 
  Users, 
  Trophy, 
  Target, 
  TrendingUp, 
  AlertCircle,
  CheckCircle,
  RefreshCw
} from 'lucide-react';
import { espnService, type DraftSession, type ESPNLeague } from '../services/espn';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { DraftRecommendations } from '../components/espn/DraftRecommendations';
import { DraftBoard } from '../components/espn/DraftBoard';
import { ManualPickEntry } from '../components/espn/ManualPickEntry';

export function DraftRoomPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const location = useLocation();
  const queryClient = useQueryClient();
  
  // Get session and league from navigation state or fetch if not available
  const [session] = useState<DraftSession | null>(location.state?.session || null);
  const [league] = useState<ESPNLeague | null>(location.state?.league || null);
  const [showManualPick, setShowManualPick] = useState(false);

  // Fetch recommendations for current pick
  const { 
    data: recommendations, 
    isLoading: recommendationsLoading,
    error: recommendationsError,
    refetch: refetchRecommendations 
  } = useQuery({
    queryKey: ['draft-recommendations', sessionId],
    queryFn: () => espnService.getDraftRecommendations(parseInt(sessionId!)),
    enabled: !!sessionId && !!session,
    refetchInterval: session?.is_live_synced ? 10000 : false, // Auto-refresh every 10s if live syncing
  });

  // Record pick mutation
  const recordPickMutation = useMutation({
    mutationFn: ({ pick }: { pick: any }) => 
      espnService.recordDraftPick(parseInt(sessionId!), pick),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['draft-recommendations'] });
      setShowManualPick(false);
    },
  });

  if (!sessionId) {
    return <Navigate to="/espn/leagues" replace />;
  }

  if (!session || !league) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading draft session...</div>
      </div>
    );
  }

  const isUserTurn = session.current_pick === session.next_user_pick;
  const picksUntilTurn = session.picks_until_user_turn;

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{league.league_name}</h1>
            <p className="text-gray-600">Draft Room • {league.season} Season</p>
          </div>
          <div className="flex items-center gap-4">
            {session.is_live_synced ? (
              <Badge variant="success" className="flex items-center gap-1">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                Live Sync
              </Badge>
            ) : (
              <Badge variant="secondary">Manual Mode</Badge>
            )}
            <Button
              variant="outline"
              size="sm"
              onClick={() => refetchRecommendations()}
              className="flex items-center gap-1"
            >
              <RefreshCw className="h-4 w-4" />
              Refresh
            </Button>
          </div>
        </div>

        {/* Draft Status */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="flex items-center gap-3">
            <Clock className="h-5 w-5 text-gray-400" />
            <div>
              <p className="text-sm text-gray-600">Current Pick</p>
              <p className="font-semibold">{session.current_pick}</p>
            </div>
          </div>
          
          <div className="flex items-center gap-3">
            <Trophy className="h-5 w-5 text-gray-400" />
            <div>
              <p className="text-sm text-gray-600">Round</p>
              <p className="font-semibold">{session.current_round} of 16</p>
            </div>
          </div>
          
          <div className="flex items-center gap-3">
            <Users className="h-5 w-5 text-gray-400" />
            <div>
              <p className="text-sm text-gray-600">Your Position</p>
              <p className="font-semibold">{session.user_pick_position}</p>
            </div>
          </div>
          
          <div className="flex items-center gap-3">
            <Target className="h-5 w-5 text-gray-400" />
            <div>
              <p className="text-sm text-gray-600">Next Pick</p>
              <p className="font-semibold">
                {isUserTurn ? 'Your turn!' : `${picksUntilTurn} picks away`}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Turn Indicator */}
      {isUserTurn && (
        <Card className="bg-green-50 border-green-200 p-4">
          <div className="flex items-center gap-3">
            <CheckCircle className="h-6 w-6 text-green-600" />
            <div className="flex-1">
              <h3 className="font-medium text-green-900">It's your turn to pick!</h3>
              <p className="text-green-700 text-sm">
                Pick #{session.current_pick} • Round {session.current_round}
              </p>
            </div>
            {!session.is_live_synced && (
              <Button 
                onClick={() => setShowManualPick(true)}
                className="bg-green-600 hover:bg-green-700"
              >
                Enter Pick
              </Button>
            )}
          </div>
        </Card>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Draft Recommendations */}
        <div className="lg:col-span-2">
          <Card className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <TrendingUp className="h-5 w-5" />
                Draft Recommendations
              </h2>
              {recommendationsLoading && (
                <div className="text-sm text-gray-500">Loading...</div>
              )}
            </div>

            {recommendationsError ? (
              <div className="text-center py-8">
                <AlertCircle className="h-8 w-8 text-red-500 mx-auto mb-2" />
                <p className="text-red-600 mb-4">Failed to load recommendations</p>
                <Button onClick={() => refetchRecommendations()}>Try Again</Button>
              </div>
            ) : recommendations ? (
              <DraftRecommendations 
                recommendations={recommendations}
                isUserTurn={isUserTurn}
                onSelectPlayer={() => {
                  if (!session.is_live_synced && isUserTurn) {
                    // Auto-fill manual pick form with recommended player
                    setShowManualPick(true);
                  }
                }}
              />
            ) : (
              <div className="text-center py-8 text-gray-500">
                No recommendations available
              </div>
            )}
          </Card>
        </div>

        {/* Draft Board & Your Team */}
        <div className="space-y-6">
          <DraftBoard session={session} />
          
          {/* Your Current Roster */}
          <Card className="p-4">
            <h3 className="font-medium mb-3">Your Roster</h3>
            <div className="space-y-2">
              {session.user_roster && session.user_roster.length > 0 ? (
                session.user_roster.map((pick: any, index: number) => (
                  <div key={index} className="flex justify-between text-sm">
                    <span>{pick.player_name}</span>
                    <span className="text-gray-500">{pick.position}</span>
                  </div>
                ))
              ) : (
                <p className="text-gray-500 text-sm">No picks yet</p>
              )}
            </div>
          </Card>
        </div>
      </div>

      {/* Manual Pick Entry Modal */}
      {showManualPick && (
        <ManualPickEntry
          session={session}
          onSubmit={(pick) => recordPickMutation.mutate({ pick })}
          onCancel={() => setShowManualPick(false)}
          isSubmitting={recordPickMutation.isPending}
        />
      )}
    </div>
  );
}
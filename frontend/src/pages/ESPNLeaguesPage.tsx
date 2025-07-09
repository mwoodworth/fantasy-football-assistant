import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, Calendar, Users, Trophy, Settings, Trash2, Play, RotateCcw } from 'lucide-react';
import { espnService, type ESPNLeague } from '../services/espn';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { Modal } from '../components/common/Modal';
import { ConnectLeagueForm } from '../components/espn/ConnectLeagueForm';
import { DraftSessionModal } from '../components/espn/DraftSessionModal';
import { LeagueSettingsModal } from '../components/espn/LeagueSettingsModal';

export function ESPNLeaguesPage() {
  const [showConnectModal, setShowConnectModal] = useState(false);
  const [showDraftModal, setShowDraftModal] = useState(false);
  const [showSettingsModal, setShowSettingsModal] = useState(false);
  const [selectedLeague, setSelectedLeague] = useState<ESPNLeague | null>(null);
  const [includeArchived, setIncludeArchived] = useState(false);
  const queryClient = useQueryClient();

  // Fetch user's leagues
  const { data: leagues = [], isLoading, error } = useQuery({
    queryKey: ['espn-leagues', includeArchived],
    queryFn: () => espnService.getMyLeagues(includeArchived),
  });

  // Disconnect league mutation
  const disconnectMutation = useMutation({
    mutationFn: espnService.disconnectLeague,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['espn-leagues'] });
    },
  });

  // Unarchive league mutation
  const unarchiveMutation = useMutation({
    mutationFn: espnService.unarchiveLeague,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['espn-leagues'] });
    },
  });

  // Permanently delete league mutation
  const permanentDeleteMutation = useMutation({
    mutationFn: espnService.permanentlyDeleteLeague,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['espn-leagues'] });
    },
  });

  const handleDisconnectLeague = async (leagueId: number) => {
    if (confirm('Are you sure you want to disconnect this league? This will archive the league but preserve historical data.')) {
      disconnectMutation.mutate(leagueId);
    }
  };

  const handleUnarchiveLeague = async (leagueId: number) => {
    if (confirm('Are you sure you want to reactivate this league? It will start syncing data again.')) {
      unarchiveMutation.mutate(leagueId);
    }
  };

  const handlePermanentDelete = async (leagueId: number, leagueName: string) => {
    const confirmText = prompt(`To permanently delete this league, type "${leagueName}" below:`);
    if (confirmText === leagueName) {
      permanentDeleteMutation.mutate(leagueId);
    }
  };

  const handleStartDraft = (league: ESPNLeague) => {
    setSelectedLeague(league);
    setShowDraftModal(true);
  };

  const handleShowSettings = (league: ESPNLeague) => {
    setSelectedLeague(league);
    setShowSettingsModal(true);
  };

  const getSyncStatusBadge = (status: string) => {
    const { text, color } = espnService.formatSyncStatus(status);
    return <Badge variant={color}>{text}</Badge>;
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading your ESPN leagues...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center text-red-600 p-4">
        Error loading leagues. Please try again.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">ESPN Leagues</h1>
          <p className="text-gray-600 mt-1">
            Connect and manage your ESPN fantasy football leagues
          </p>
        </div>
        <Button onClick={() => setShowConnectModal(true)} className="flex items-center gap-2">
          <Plus className="h-4 w-4" />
          Connect League
        </Button>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4">
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={includeArchived}
            onChange={(e) => setIncludeArchived(e.target.checked)}
            className="rounded border-gray-300"
          />
          <span className="text-sm text-gray-700">Include archived leagues</span>
        </label>
      </div>

      {/* Leagues Grid */}
      {leagues.length === 0 ? (
        <Card className="text-center py-12">
          <Trophy className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No ESPN leagues connected</h3>
          <p className="text-gray-600 mb-4">
            Connect your first ESPN league to get started with draft assistance and insights.
          </p>
          <Button onClick={() => setShowConnectModal(true)}>
            Connect Your First League
          </Button>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {leagues.map((league) => (
            <Card key={league.id} className="p-6">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h3 className="font-semibold text-gray-900 mb-1">
                    {league.league_name}
                  </h3>
                  <p className="text-sm text-gray-600">
                    {league.season} Season • {league.team_count} Teams
                  </p>
                </div>
                <div className="flex gap-1">
                  {getSyncStatusBadge(league.sync_status)}
                  {league.is_archived && <Badge variant="secondary">Archived</Badge>}
                </div>
              </div>

              <div className="space-y-3">
                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <Calendar className="h-4 w-4" />
                  <span>
                    Draft: {league.draft_date 
                      ? new Date(league.draft_date).toLocaleDateString()
                      : 'Not scheduled'
                    }
                  </span>
                </div>

                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <Users className="h-4 w-4" />
                  <span>
                    Your Team: {league.user_team_name || 'Unknown'}
                  </span>
                </div>

                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <Trophy className="h-4 w-4" />
                  <span>{espnService.formatScoreType(league.scoring_type)}</span>
                </div>
              </div>

              <div className="flex gap-2 mt-4 pt-4 border-t">
                {!league.draft_completed && league.is_active && (
                  <Button
                    size="sm"
                    onClick={() => handleStartDraft(league)}
                    className="flex items-center gap-1"
                  >
                    <Play className="h-3 w-3" />
                    Draft
                  </Button>
                )}
                
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => handleShowSettings(league)}
                  className="flex items-center gap-1"
                >
                  <Settings className="h-3 w-3" />
                  Settings
                </Button>

                {league.is_archived ? (
                  <>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleUnarchiveLeague(league.id)}
                      className="flex items-center gap-1 text-green-600 hover:text-green-700"
                    >
                      <RotateCcw className="h-3 w-3" />
                      Reactivate
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handlePermanentDelete(league.id, league.league_name)}
                      className="flex items-center gap-1 text-red-600 hover:text-red-700"
                    >
                      <Trash2 className="h-3 w-3" />
                      Delete
                    </Button>
                  </>
                ) : (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleDisconnectLeague(league.id)}
                    className="flex items-center gap-1 text-red-600 hover:text-red-700"
                  >
                    <Trash2 className="h-3 w-3" />
                    Archive
                  </Button>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Connect League Modal */}
      <Modal
        isOpen={showConnectModal}
        onClose={() => setShowConnectModal(false)}
        title="Connect ESPN League"
      >
        <ConnectLeagueForm
          onSuccess={() => {
            setShowConnectModal(false);
            queryClient.invalidateQueries({ queryKey: ['espn-leagues'] });
          }}
          onCancel={() => setShowConnectModal(false)}
        />
      </Modal>

      {/* Draft Session Modal */}
      {selectedLeague && (
        <DraftSessionModal
          isOpen={showDraftModal}
          onClose={() => {
            setShowDraftModal(false);
            setSelectedLeague(null);
          }}
          league={selectedLeague}
        />
      )}

      {/* League Settings Modal */}
      {selectedLeague && (
        <LeagueSettingsModal
          isOpen={showSettingsModal}
          onClose={() => {
            setShowSettingsModal(false);
            setSelectedLeague(null);
          }}
          league={selectedLeague}
        />
      )}
    </div>
  );
}
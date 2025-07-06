import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Settings, AlertCircle, Trash2, Archive, RefreshCw } from 'lucide-react';
import { espnService, type ESPNLeague } from '../../services/espn';
import { Modal } from '../common/Modal';
import { Button } from '../common/Button';
import { Card } from '../common/Card';
import { Badge } from '../common/Badge';
import { Input } from '../common/Input';

interface LeagueSettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  league: ESPNLeague;
}

export function LeagueSettingsModal({ isOpen, onClose, league }: LeagueSettingsModalProps) {
  const [customName, setCustomName] = useState(league.league_name);
  const [confirmDelete, setConfirmDelete] = useState('');
  const queryClient = useQueryClient();

  // Update league mutation (placeholder for now)
  const updateLeagueMutation = useMutation({
    mutationFn: async (updates: { league_name?: string }) => {
      // TODO: Implement league update endpoint
      await new Promise(resolve => setTimeout(resolve, 1000)); // Mock delay
      return updates;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['espn-leagues'] });
      onClose();
    },
  });

  // Disconnect league mutation
  const disconnectMutation = useMutation({
    mutationFn: espnService.disconnectLeague,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['espn-leagues'] });
      onClose();
    },
  });

  // Refresh league data mutation (placeholder)
  const refreshMutation = useMutation({
    mutationFn: async () => {
      // TODO: Implement league refresh endpoint
      await new Promise(resolve => setTimeout(resolve, 2000)); // Mock delay
      return {};
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['espn-leagues'] });
    },
  });

  const handleUpdateName = () => {
    if (customName !== league.league_name) {
      updateLeagueMutation.mutate({ league_name: customName });
    }
  };

  const handleDisconnect = () => {
    if (confirmDelete === league.league_name) {
      disconnectMutation.mutate(league.id);
    }
  };

  const handleRefresh = () => {
    refreshMutation.mutate();
  };

  const getSyncStatusBadge = (status: string) => {
    const { text, color } = espnService.formatSyncStatus(status);
    return <Badge variant={color}>{text}</Badge>;
  };

  return (
    <Modal 
      isOpen={isOpen} 
      onClose={onClose} 
      title="League Settings"
      size="lg"
    >
      <div className="space-y-6">
        {/* League Info */}
        <Card className="bg-gray-50 p-4">
          <div className="flex items-start justify-between mb-3">
            <div>
              <h3 className="font-medium text-gray-900">{league.league_name}</h3>
              <p className="text-sm text-gray-600">
                ESPN League ID: {league.espn_league_id} • {league.season} Season
              </p>
            </div>
            <div className="flex gap-2">
              {getSyncStatusBadge(league.sync_status)}
              {league.is_archived && <Badge variant="secondary">Archived</Badge>}
            </div>
          </div>
          
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-600">Teams:</span>
              <span className="ml-2 font-medium">{league.team_count}</span>
            </div>
            <div>
              <span className="text-gray-600">Scoring:</span>
              <span className="ml-2 font-medium">{espnService.formatScoreType(league.scoring_type)}</span>
            </div>
            <div>
              <span className="text-gray-600">Draft Status:</span>
              <span className="ml-2 font-medium">
                {league.draft_completed ? 'Completed' : 'Pending'}
              </span>
            </div>
            <div>
              <span className="text-gray-600">Your Team:</span>
              <span className="ml-2 font-medium">{league.user_team_name || 'Unknown'}</span>
            </div>
          </div>
        </Card>

        {/* League Name Update */}
        <div>
          <h4 className="font-medium text-gray-900 mb-3">League Display Name</h4>
          <div className="flex gap-3">
            <Input
              type="text"
              value={customName}
              onChange={(e) => setCustomName(e.target.value)}
              placeholder="Enter custom league name"
              className="flex-1"
            />
            <Button
              onClick={handleUpdateName}
              disabled={customName === league.league_name || updateLeagueMutation.isPending}
              size="sm"
            >
              {updateLeagueMutation.isPending ? 'Updating...' : 'Update'}
            </Button>
          </div>
          <p className="text-xs text-gray-500 mt-1">
            Customize how this league appears in your dashboard
          </p>
        </div>

        {/* League Actions */}
        <div>
          <h4 className="font-medium text-gray-900 mb-3">League Actions</h4>
          <div className="space-y-3">
            
            {/* Refresh League Data */}
            <Card className="p-4">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h5 className="font-medium mb-1">Refresh League Data</h5>
                  <p className="text-sm text-gray-600">
                    Sync the latest information from ESPN including roster, scores, and settings.
                  </p>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleRefresh}
                  disabled={refreshMutation.isPending}
                  className="ml-4 flex items-center gap-1"
                >
                  <RefreshCw className={`h-3 w-3 ${refreshMutation.isPending ? 'animate-spin' : ''}`} />
                  {refreshMutation.isPending ? 'Syncing...' : 'Refresh'}
                </Button>
              </div>
            </Card>

            {/* Archive League */}
            {!league.is_archived && (
              <Card className="p-4 border-yellow-200 bg-yellow-50">
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3">
                    <Archive className="h-5 w-5 text-yellow-600 mt-0.5" />
                    <div className="flex-1">
                      <h5 className="font-medium text-yellow-900 mb-1">Archive League</h5>
                      <p className="text-sm text-yellow-800">
                        Archive this league to remove it from your active leagues while preserving historical data.
                      </p>
                    </div>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleDisconnect}
                    className="ml-4 text-yellow-700 border-yellow-300 hover:bg-yellow-100"
                  >
                    Archive
                  </Button>
                </div>
              </Card>
            )}

            {/* Disconnect League */}
            <Card className="p-4 border-red-200 bg-red-50">
              <div className="flex items-start gap-3">
                <AlertCircle className="h-5 w-5 text-red-600 mt-0.5" />
                <div className="flex-1">
                  <h5 className="font-medium text-red-900 mb-2">Disconnect League</h5>
                  <p className="text-sm text-red-800 mb-3">
                    This will permanently disconnect this league from your account. 
                    Historical data will be preserved but you'll need to reconnect to access it again.
                  </p>
                  
                  <div className="space-y-3">
                    <div>
                      <label className="block text-sm font-medium text-red-900 mb-1">
                        Type the league name to confirm:
                      </label>
                      <Input
                        type="text"
                        value={confirmDelete}
                        onChange={(e) => setConfirmDelete(e.target.value)}
                        placeholder={league.league_name}
                        className="border-red-300 focus:border-red-500 focus:ring-red-500"
                      />
                    </div>
                    
                    <Button
                      onClick={handleDisconnect}
                      disabled={confirmDelete !== league.league_name || disconnectMutation.isPending}
                      className="bg-red-600 hover:bg-red-700 text-white flex items-center gap-1"
                      size="sm"
                    >
                      <Trash2 className="h-3 w-3" />
                      {disconnectMutation.isPending ? 'Disconnecting...' : 'Disconnect League'}
                    </Button>
                  </div>
                </div>
              </div>
            </Card>
          </div>
        </div>

        {/* Error Display */}
        {(updateLeagueMutation.error || disconnectMutation.error || refreshMutation.error) && (
          <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded text-sm text-red-700">
            <AlertCircle className="h-4 w-4" />
            <span>
              {updateLeagueMutation.error?.message || 
               disconnectMutation.error?.message || 
               refreshMutation.error?.message || 
               'An error occurred. Please try again.'}
            </span>
          </div>
        )}

        {/* Success Messages */}
        {refreshMutation.isSuccess && (
          <div className="flex items-center gap-2 p-3 bg-green-50 border border-green-200 rounded text-sm text-green-700">
            <Settings className="h-4 w-4" />
            <span>League data refreshed successfully!</span>
          </div>
        )}

        {/* Close Button */}
        <div className="flex justify-end pt-4 border-t">
          <Button variant="outline" onClick={onClose}>
            Close
          </Button>
        </div>
      </div>
    </Modal>
  );
}
import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Settings, AlertCircle, Trash2, Archive, RefreshCw, Key, Lock } from 'lucide-react';
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
  const [showCookieSection, setShowCookieSection] = useState(false);
  const [cookieData, setCookieData] = useState({
    espnS2: league.espn_s2 || '',
    swid: league.swid || ''
  });
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

  // Update ESPN cookies mutation
  const updateCookiesMutation = useMutation({
    mutationFn: async ({ espnS2, swid }: { espnS2: string; swid: string }) => {
      return espnService.updateESPNCookies(league.id, espnS2, swid);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['espn-leagues'] });
      setShowCookieSection(false);
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

  const handleUpdateCookies = () => {
    if (cookieData.espnS2 && cookieData.swid) {
      updateCookiesMutation.mutate({
        espnS2: cookieData.espnS2,
        swid: cookieData.swid
      });
    }
  };

  const handleCancelCookieUpdate = () => {
    setShowCookieSection(false);
    setCookieData({
      espnS2: league.espn_s2 || '',
      swid: league.swid || ''
    });
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

        {/* ESPN Authentication */}
        <div>
          <h4 className="font-medium text-gray-900 mb-3">ESPN Authentication</h4>
          
          {!showCookieSection ? (
            <Card className="p-4">
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-3">
                  <Key className="h-5 w-5 text-blue-600 mt-0.5" />
                  <div className="flex-1">
                    <h5 className="font-medium mb-1">Update ESPN Cookies</h5>
                    <p className="text-sm text-gray-600">
                      Update your ESPN s2 and swid cookies to maintain access to private league data.
                      {league.espn_s2 && league.swid && (
                        <span className="text-green-600 ml-1">✓ Currently configured</span>
                      )}
                    </p>
                  </div>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowCookieSection(true)}
                  className="ml-4 flex items-center gap-1"
                >
                  <Lock className="h-3 w-3" />
                  Update Cookies
                </Button>
              </div>
            </Card>
          ) : (
            <Card className="p-4 border-blue-200 bg-blue-50">
              <div className="space-y-4">
                <div className="flex items-start gap-3">
                  <Key className="h-5 w-5 text-blue-600 mt-0.5" />
                  <div className="flex-1">
                    <h5 className="font-medium text-blue-900 mb-1">Update ESPN Cookies</h5>
                    <p className="text-sm text-blue-800 mb-3">
                      Enter your updated ESPN authentication cookies to continue accessing private league data.
                    </p>
                  </div>
                </div>
                
                <div className="space-y-3">
                  <div>
                    <label className="block text-sm font-medium text-blue-900 mb-1">
                      ESPN S2 Cookie
                    </label>
                    <Input
                      type="password"
                      value={cookieData.espnS2}
                      onChange={(e) => setCookieData(prev => ({ ...prev, espnS2: e.target.value }))}
                      placeholder="Paste your ESPN S2 cookie here"
                      className="border-blue-300 focus:border-blue-500 focus:ring-blue-500"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-blue-900 mb-1">
                      ESPN SWID Cookie
                    </label>
                    <Input
                      type="password"
                      value={cookieData.swid}
                      onChange={(e) => setCookieData(prev => ({ ...prev, swid: e.target.value }))}
                      placeholder="Paste your ESPN SWID cookie here"
                      className="border-blue-300 focus:border-blue-500 focus:ring-blue-500"
                    />
                  </div>
                </div>
                
                <div className="p-3 bg-blue-100 border border-blue-200 rounded-md">
                  <p className="text-blue-900 text-sm">
                    <strong>How to get your ESPN cookies:</strong><br />
                    1. Log into ESPN Fantasy in your browser<br />
                    2. Open Developer Tools (F12)<br />
                    3. Go to Application/Storage → Cookies → espn.com<br />
                    4. Copy the values for "espn_s2" and "SWID"
                  </p>
                </div>
                
                <div className="flex justify-end gap-3">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleCancelCookieUpdate}
                    disabled={updateCookiesMutation.isPending}
                  >
                    Cancel
                  </Button>
                  <Button
                    size="sm"
                    onClick={handleUpdateCookies}
                    disabled={!cookieData.espnS2 || !cookieData.swid || updateCookiesMutation.isPending}
                  >
                    {updateCookiesMutation.isPending ? 'Updating...' : 'Update Cookies'}
                  </Button>
                </div>
              </div>
            </Card>
          )}
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
        {(updateLeagueMutation.error || disconnectMutation.error || refreshMutation.error || updateCookiesMutation.error) && (
          <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded text-sm text-red-700">
            <AlertCircle className="h-4 w-4" />
            <span>
              {updateLeagueMutation.error?.message || 
               disconnectMutation.error?.message || 
               refreshMutation.error?.message || 
               updateCookiesMutation.error?.message ||
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

        {updateCookiesMutation.isSuccess && (
          <div className="flex items-center gap-2 p-3 bg-green-50 border border-green-200 rounded text-sm text-green-700">
            <Key className="h-4 w-4" />
            <span>ESPN cookies updated successfully!</span>
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
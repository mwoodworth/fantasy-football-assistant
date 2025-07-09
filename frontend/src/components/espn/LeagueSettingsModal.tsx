import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Settings, AlertCircle, Trash2, Archive, RefreshCw, Key, Lock, Trophy, Users, Calendar, Shield } from 'lucide-react';
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
      title={
        <div className="flex items-center gap-2">
          <Settings className="h-5 w-5 text-gray-600" />
          <span>League Settings</span>
        </div>
      }
      size="lg"
    >
      <div className="space-y-6">
        {/* League Info Header */}
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-6 rounded-lg border border-blue-100">
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-start gap-3">
              <Trophy className="h-8 w-8 text-blue-600 mt-0.5" />
              <div>
                <h3 className="text-xl font-semibold text-gray-900">{league.league_name}</h3>
                <p className="text-sm text-gray-600 mt-1">
                  ESPN League ID: {league.espn_league_id} • {league.season} Season
                </p>
              </div>
            </div>
            <div className="flex gap-2">
              {getSyncStatusBadge(league.sync_status)}
              {league.is_archived && <Badge variant="secondary">Archived</Badge>}
            </div>
          </div>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="flex items-center gap-2">
              <Users className="h-4 w-4 text-gray-500" />
              <div>
                <p className="text-xs text-gray-500">Teams</p>
                <p className="font-semibold text-gray-900">{league.team_count}</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Trophy className="h-4 w-4 text-gray-500" />
              <div>
                <p className="text-xs text-gray-500">Scoring</p>
                <p className="font-semibold text-gray-900">{espnService.formatScoreType(league.scoring_type)}</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Calendar className="h-4 w-4 text-gray-500" />
              <div>
                <p className="text-xs text-gray-500">Draft Status</p>
                <p className="font-semibold text-gray-900">
                  {league.draft_completed ? 'Completed' : 'Pending'}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Shield className="h-4 w-4 text-gray-500" />
              <div>
                <p className="text-xs text-gray-500">Your Team</p>
                <p className="font-semibold text-gray-900">{league.user_team_name || 'Not Set'}</p>
              </div>
            </div>
          </div>
        </div>

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
            <div className="border border-red-200 rounded-lg overflow-hidden">
              <div className="bg-red-50 p-4">
                <div className="flex items-start gap-3">
                  <div className="p-2 bg-red-100 rounded-lg">
                    <Trash2 className="h-5 w-5 text-red-600" />
                  </div>
                  <div className="flex-1">
                    <h5 className="font-semibold text-red-900 mb-1">Disconnect League</h5>
                    <p className="text-sm text-red-700">
                      Remove this league from your account. This action cannot be undone.
                    </p>
                  </div>
                </div>
              </div>
              
              <div className="p-4 bg-white border-t border-red-200">
                <div className="space-y-4">
                  <div className="p-3 bg-red-50 border border-red-200 rounded text-sm">
                    <p className="text-red-800">
                      <strong>Warning:</strong> Disconnecting will:
                    </p>
                    <ul className="list-disc list-inside mt-2 text-red-700 space-y-1">
                      <li>Remove this league from your active leagues</li>
                      <li>Delete any saved preferences for this league</li>
                      <li>Require re-authentication if you reconnect later</li>
                    </ul>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      To confirm, type <span className="font-semibold text-red-600">"{league.league_name}"</span> below:
                    </label>
                    <Input
                      type="text"
                      value={confirmDelete}
                      onChange={(e) => setConfirmDelete(e.target.value)}
                      placeholder="Type league name to confirm"
                      className={`${
                        confirmDelete === league.league_name
                          ? 'border-green-500 focus:border-green-600 focus:ring-green-500'
                          : 'border-gray-300 focus:border-red-500 focus:ring-red-500'
                      }`}
                    />
                    {confirmDelete && confirmDelete !== league.league_name && (
                      <p className="text-xs text-red-600 mt-1">
                        League name doesn't match. Please type exactly: {league.league_name}
                      </p>
                    )}
                  </div>
                  
                  <Button
                    onClick={handleDisconnect}
                    disabled={confirmDelete !== league.league_name || disconnectMutation.isPending}
                    variant="destructive"
                    className="w-full"
                  >
                    {disconnectMutation.isPending ? (
                      <>
                        <RefreshCw className="h-4 w-4 animate-spin mr-2" />
                        Disconnecting...
                      </>
                    ) : (
                      <>
                        <Trash2 className="h-4 w-4 mr-2" />
                        Disconnect League
                      </>
                    )}
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Error Display */}
        {(updateLeagueMutation.error || disconnectMutation.error || refreshMutation.error || updateCookiesMutation.error) && (
          <div className="flex items-start gap-3 p-4 bg-red-50 border border-red-200 rounded-lg">
            <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-red-700">
              <p className="font-medium mb-1">Error</p>
              <p>
                {(() => {
                  const error = updateLeagueMutation.error || disconnectMutation.error || 
                               refreshMutation.error || updateCookiesMutation.error;
                  
                  if (error && typeof error === 'object' && 'response' in error) {
                    const axiosError = error as { response?: { data?: { detail?: string } } };
                    if (axiosError.response?.data?.detail) {
                      return axiosError.response.data.detail;
                    }
                  }
                  
                  return (error as Error)?.message || 'An error occurred. Please try again.';
                })()}
              </p>
            </div>
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
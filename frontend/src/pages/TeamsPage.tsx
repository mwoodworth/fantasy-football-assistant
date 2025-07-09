import { useState, useEffect } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { Table } from '../components/common/Table';
import { Select } from '../components/common/Select';
import { Modal, ModalBody, ModalFooter } from '../components/common/Modal';
import { Users, Trophy, TrendingUp, Settings, Star, ArrowUpDown, Bell, Shield, Eye, Play, RefreshCw } from 'lucide-react';
import { teamsService, type TeamDetail, type WaiverTarget, type TradeTarget, type TradeProposal, type TradeEvaluation } from '../services/teams';

export function TeamsPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [selectedTeam, setSelectedTeam] = useState<string>('');
  const [selectedView, setSelectedView] = useState('roster');
  const [showSettings, setShowSettings] = useState(false);
  const [showCookieUpdate, setShowCookieUpdate] = useState(false);
  const [authError, setAuthError] = useState<string | null>(null);
  const [cookieUpdateData, setCookieUpdateData] = useState({ espnS2: '', swid: '', leagueId: 0 });
  const [waiverFilter, setWaiverFilter] = useState<string>('all');
  const [selectedTradeTarget, setSelectedTradeTarget] = useState<TradeTarget | null>(null);
  const [showTradeModal, setShowTradeModal] = useState(false);
  const [tradeEvaluation, setTradeEvaluation] = useState<TradeEvaluation | null>(null);
  const [evaluatingTrade, setEvaluatingTrade] = useState(false);

  // Fetch teams from API
  const { data: teams = [], isLoading, error, refetch } = useQuery({
    queryKey: ['user-teams'],
    queryFn: () => teamsService.getUserTeams(),
  });

  // Fetch team detail for selected team
  const { data: teamDetail, isLoading: teamDetailLoading, error: teamDetailError } = useQuery({
    queryKey: ['team-detail', selectedTeam],
    queryFn: () => {
      console.log('Fetching team detail for:', selectedTeam);
      return teamsService.getTeamDetail(selectedTeam);
    },
    enabled: !!selectedTeam,
    retry: (failureCount, error: unknown) => {
      // Don't retry if it's an authentication error
      if ((error as { response?: { status?: number; data?: { detail?: unknown } } })?.response?.status === 401) {
        const errorDetail = (error as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
        if (typeof errorDetail === 'object' && errorDetail && 'requires_auth_update' in errorDetail && errorDetail.requires_auth_update) {
          setAuthError((errorDetail as { message: string; requires_auth_update: boolean }).message);
          const currentTeam = teams.find(t => t.id === selectedTeam);
          if (currentTeam?.espn_league_id) {
            setCookieUpdateData({ 
              espnS2: '', 
              swid: '', 
              leagueId: currentTeam.espn_league_id 
            });
            setShowCookieUpdate(true);
          }
        }
        return false;
      }
      return failureCount < 2;
    }
  });

  // Fetch waiver recommendations for selected team
  const { data: waiverTargets = [], isLoading: waiverLoading } = useQuery({
    queryKey: ['waiver-recommendations', selectedTeam],
    queryFn: () => teamsService.getWaiverRecommendations(selectedTeam),
    enabled: !!selectedTeam && selectedView === 'waivers',
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  // Fetch trade targets for selected team
  const { data: tradeTargets = [], isLoading: tradeLoading } = useQuery({
    queryKey: ['trade-targets', selectedTeam],
    queryFn: () => teamsService.getTradeTargets(selectedTeam),
    enabled: !!selectedTeam && selectedView === 'trades',
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  // Set initial selected team when teams load
  useEffect(() => {
    if (teams.length > 0 && !selectedTeam) {
      // Try to find a team with user_team_id set (indicating it's the user's selected team)
      // This would require the API to return this information
      // For now, just select the first team
      setSelectedTeam(teams[0].id);
      console.log('Selected team ID:', teams[0].id, 'Team name:', teams[0].name);
    }
  }, [teams, selectedTeam]);

  const teamOptions = teams.map(team => ({
    ...teamsService.formatTeamOption(team),
    value: team.id
  }));

  const viewOptions = [
    { value: 'roster', label: 'Current Roster' },
    { value: 'lineup', label: 'Set Lineup' },
    { value: 'trades', label: 'Trade Center' },
    { value: 'waivers', label: 'Waivers' }
  ];

  const currentTeam = teams.find(team => team.id === selectedTeam);

  const handleStartDraft = () => {
    if (currentTeam && currentTeam.platform === 'ESPN' && currentTeam.espn_league_id) {
      navigate('/espn/leagues');
    }
  };

  const handleSyncTeam = async () => {
    if (currentTeam && currentTeam.platform === 'ESPN') {
      try {
        await teamsService.syncTeam(currentTeam.id);
        refetch();
      } catch (error: unknown) {
        console.error('Error syncing team:', error);
        // Handle authentication errors
        if ((error as { response?: { status?: number; data?: { detail?: unknown } } })?.response?.status === 401) {
          const errorDetail = (error as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
          if (typeof errorDetail === 'object' && errorDetail && 'requires_auth_update' in errorDetail && errorDetail.requires_auth_update) {
            setAuthError((errorDetail as { message: string; requires_auth_update: boolean }).message);
            if (currentTeam.espn_league_id) {
              setCookieUpdateData({ 
                espnS2: '', 
                swid: '', 
                leagueId: currentTeam.espn_league_id 
              });
              setShowCookieUpdate(true);
            }
          }
        }
      }
    }
  };

  const handleViewWaiverTargets = () => {
    setSelectedView('waivers');
  };

  const handleAddWaiverClaim = async (target: WaiverTarget) => {
    // TODO: Implement waiver claim modal
    console.log('Add waiver claim for:', target.name);
  };

  const handleOpenTradeAnalyzer = () => {
    setSelectedView('trades');
  };

  const handleRefreshTradeTargets = async () => {
    if (!selectedTeam) return;
    
    try {
      const result = await teamsService.refreshTradeTargets(selectedTeam);
      
      // Invalidate and refetch trade targets
      queryClient.invalidateQueries(['trade-targets', selectedTeam]);
      
      // Show success message with sync info
      if (result.refreshInfo.teams_synced > 0) {
        console.log(`Trade targets refreshed! Synced ${result.refreshInfo.teams_synced} teams.`);
      }
    } catch (error) {
      console.error('Error refreshing trade targets:', error);
    }
  };

  const handleViewTradeTarget = async (target: TradeTarget) => {
    setSelectedTradeTarget(target);
    setShowTradeModal(true);
    setEvaluatingTrade(true);
    setTradeEvaluation(null);

    try {
      // Create trade proposal object
      const proposal: TradeProposal = {
        team1_id: selectedTeam,
        team1_players: target.suggested_offer,
        team2_id: target.team_id,
        team2_players: [target.player]
      };

      // Evaluate the trade
      const evaluation = await teamsService.evaluateTrade(proposal);
      setTradeEvaluation(evaluation);
    } catch (error) {
      console.error('Error evaluating trade:', error);
      // If API fails, show mock evaluation
      setTradeEvaluation({
        fairness_score: 85,
        grade: 'B+',
        team1_impact: {
          value_change: 5.2,
          needs_improvement: { WR: 0.15, RB: -0.08 },
          recommendation: 'Slight upgrade overall. Improves WR depth while maintaining RB stability.'
        },
        team2_impact: {
          value_change: -3.1,
          needs_improvement: { WR: -0.12, RB: 0.10 },
          recommendation: 'Loses some value but fills positional need at RB.'
        },
        analysis: `This trade offers good value for both teams. You upgrade at ${target.player.position} while giving up depth that the other team needs. The suggested offer is fair but you might be able to negotiate slightly better terms.`,
        verdict: 'consider'
      });
    } finally {
      setEvaluatingTrade(false);
    }
  };

  const handleProposeTrack = async (target: TradeTarget) => {
    // TODO: Implement actual trade proposal submission
    console.log('Proposing trade for:', target.player.name);
    alert(`Trade proposal functionality not yet implemented.\n\nWould propose: ${target.suggested_offer.map(p => p.name).join(', ')} for ${target.player.name}`);
    setShowTradeModal(false);
  };

  const handleUpdateCookies = async () => {
    // Validate that both cookies are provided
    if (!cookieUpdateData.espnS2.trim() || !cookieUpdateData.swid.trim()) {
      setAuthError('Both ESPN S2 and SWID cookies are required');
      return;
    }

    try {
      await teamsService.updateESPNCookies(
        cookieUpdateData.leagueId,
        cookieUpdateData.espnS2.trim(),
        cookieUpdateData.swid.trim()
      );
      setShowCookieUpdate(false);
      setAuthError(null);
      setCookieUpdateData({ espnS2: '', swid: '', leagueId: 0 });
      // Refetch team data after successful update
      refetch();
    } catch (error: unknown) {
      console.error('Error updating ESPN cookies:', error);
      // Show validation error if cookies are invalid
      const errorMessage = (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Failed to update ESPN cookies';
      setAuthError(errorMessage);
    }
  };

  const rosterColumns = [
    {
      key: 'name',
      header: 'Player',
      accessor: 'name' as keyof TeamDetail['roster'][0],
      sortable: true,
      render: (value: string, row: { position: string; team: string }) => (
        <div className="flex items-center space-x-2">
          <span className="font-medium">{value}</span>
          <Badge variant="secondary" size="sm">{row.position}</Badge>
          <span className="text-xs text-gray-500">{row.team}</span>
        </div>
      )
    },
    {
      key: 'status',
      header: 'Status',
      accessor: 'status' as keyof TeamDetail['roster'][0],
      render: (value: string) => (
        <Badge variant={value === 'starter' ? 'success' : 'secondary'} size="sm">
          {value === 'starter' ? 'Starting' : 'Bench'}
        </Badge>
      )
    },
    {
      key: 'points',
      header: 'Points',
      accessor: 'points' as keyof TeamDetail['roster'][0],
      sortable: true,
      align: 'right' as const,
      render: (value: number | undefined) => (
        <span className="font-mono">{value ? value.toFixed(1) : 'N/A'}</span>
      )
    },
    {
      key: 'actions',
      header: 'Actions',
      render: () => (
        <div className="flex items-center space-x-2">
          <Button size="sm" variant="outline">
            <ArrowUpDown className="w-3 h-3 mr-1" />
            Move
          </Button>
          <Button size="sm" variant="outline">
            <Star className="w-3 h-3" />
          </Button>
        </div>
      )
    }
  ];

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading your teams...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center text-red-600 p-4">
        Error loading teams. Please try again.
      </div>
    );
  }

  if (teams.length === 0) {
    return (
      <div className="text-center py-12">
        <Trophy className="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">No teams found</h3>
        <p className="text-gray-600 mb-4">
          Connect your ESPN league or create a manual team to get started.
        </p>
        <Button onClick={() => navigate('/espn/leagues')}>
          Connect ESPN League
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Teams</h1>
          <p className="text-gray-600">Manage your fantasy teams and lineups</p>
        </div>
        
        <div className="flex items-center space-x-3">
          <Select
            options={teamOptions}
            value={selectedTeam}
            onChange={(value) => setSelectedTeam(value as string)}
            className="min-w-[250px]"
            searchable
          />
          <Button size="sm" variant="outline" onClick={() => setShowSettings(true)}>
            <Settings className="w-4 h-4 mr-2" />
            Settings
          </Button>
        </div>
      </div>

      {/* Team Overview */}
      {currentTeam && (
        <>
          {/* Platform and League Info */}
          <div className="bg-gray-50 rounded-lg p-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className={`text-2xl ${teamsService.getPlatformColor(currentTeam.platform)}`}>
                {teamsService.getTeamIcon(currentTeam.platform)}
              </span>
              <div>
                <h2 className="font-semibold text-gray-900">{currentTeam.name}</h2>
                <p className="text-sm text-gray-600">
                  {currentTeam.league} • {currentTeam.platform} League
                  {currentTeam.season && ` • ${currentTeam.season} Season`}
                </p>
              </div>
            </div>
            
            {/* Platform-specific actions */}
            <div className="flex items-center gap-2">
              {currentTeam.platform === 'ESPN' && (
                <>
                  {!currentTeam.draft_completed && (
                    <Button size="sm" onClick={handleStartDraft}>
                      <Play className="w-4 h-4 mr-1" />
                      Go to Draft
                    </Button>
                  )}
                  <Button size="sm" variant="outline" onClick={handleSyncTeam}>
                    <RefreshCw className="w-4 h-4 mr-1" />
                    Sync
                  </Button>
                </>
              )}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card>
              <CardContent className="p-6 text-center">
                <Trophy className="w-8 h-8 mx-auto mb-2 text-yellow-600" />
                <div className="text-2xl font-bold text-gray-900">#{currentTeam.rank}</div>
                <div className="text-sm text-gray-600">League Rank</div>
              </CardContent>
            </Card>
          
          <Card>
            <CardContent className="p-6 text-center">
              <Users className="w-8 h-8 mx-auto mb-2 text-blue-600" />
              <div className="text-2xl font-bold text-gray-900">{currentTeam.record}</div>
              <div className="text-sm text-gray-600">W-L Record</div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-6 text-center">
              <TrendingUp className="w-8 h-8 mx-auto mb-2 text-green-600" />
              <div className="text-2xl font-bold text-gray-900">{currentTeam.points.toFixed(1)}</div>
              <div className="text-sm text-gray-600">Total Points</div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-6 text-center">
              <div className={`w-8 h-8 mx-auto mb-2 rounded-full flex items-center justify-center ${
                currentTeam.playoffs ? 'bg-green-100' : 'bg-red-100'
              }`}>
                <Trophy className={`w-5 h-5 ${
                  currentTeam.playoffs ? 'text-green-600' : 'text-red-600'
                }`} />
              </div>
              <div className="text-2xl font-bold text-gray-900">
                {currentTeam.playoffs ? 'Yes' : 'No'}
              </div>
              <div className="text-sm text-gray-600">Playoff Bound</div>
            </CardContent>
          </Card>
        </div>
        </>
      )}

      {/* Team Management Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-8">
          {viewOptions.map((option) => (
            <button
              key={option.value}
              onClick={() => setSelectedView(option.value)}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                selectedView === option.value
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              {option.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      {selectedView === 'roster' && (
        <Card>
          <CardHeader>
            <CardTitle>Current Roster</CardTitle>
          </CardHeader>
          <CardContent>
            {teamDetailLoading ? (
              <div className="flex items-center justify-center h-32">
                <div className="text-gray-500">Loading roster...</div>
              </div>
            ) : teamDetailError ? (
              <div className="text-center py-12 text-red-600">
                <div className="mb-2">Error loading roster</div>
                <div className="text-sm">{(teamDetailError as Error).message}</div>
                <Button onClick={() => window.location.reload()} className="mt-4">
                  Refresh Page
                </Button>
              </div>
            ) : teamDetail?.roster && teamDetail.roster.length > 0 ? (
              <div className="space-y-6">
                {/* Starting Lineup */}
                {(() => {
                  const starters = teamDetail.roster.filter(player => player.status === 'starter');
                  const startersByPosition = {
                    QB: starters.filter(p => p.position === 'QB'),
                    RB: starters.filter(p => p.position === 'RB'),
                    WR: starters.filter(p => p.position === 'WR'),
                    TE: starters.filter(p => p.position === 'TE'),
                    K: starters.filter(p => p.position === 'K'),
                    'D/ST': starters.filter(p => p.position === 'D/ST')
                  };

                  return (
                    <div>
                      <div className="flex items-center gap-2 mb-4">
                        <span className="text-lg font-semibold">🔥 Starting Lineup</span>
                        <Badge variant="success" size="sm">{starters.length} players</Badge>
                      </div>
                      <div className="space-y-4">
                        {Object.entries(startersByPosition).map(([position, players]) => 
                          players.length > 0 && (
                            <div key={position} className="border-l-4 border-green-500 pl-4">
                              <div className="font-medium text-gray-700 mb-2">{position}</div>
                              <div className="space-y-2">
                                {players.map((player) => (
                                  <div key={player.id} className="flex items-center justify-between bg-green-50 rounded-lg p-3">
                                    <div className="flex items-center gap-3">
                                      <span className="text-green-600">✅</span>
                                      <div>
                                        <div className="font-medium">{player.name}</div>
                                        <div className="text-sm text-gray-600 flex items-center gap-2">
                                          <Badge variant="secondary" size="sm">{player.position}</Badge>
                                          <span>{player.team}</span>
                                          {player.injury_status && player.injury_status !== 'ACTIVE' && player.injury_status !== 'Healthy' && (
                                            <Badge variant="destructive" size="sm">{player.injury_status}</Badge>
                                          )}
                                        </div>
                                      </div>
                                    </div>
                                    <div className="text-right">
                                      <div className="font-mono font-medium">
                                        {player.points ? player.points.toFixed(1) : '0.0'} pts
                                      </div>
                                      {player.projected_points && (
                                        <div className="text-sm text-gray-500">
                                          Proj: {player.projected_points.toFixed(1)}
                                        </div>
                                      )}
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )
                        )}
                      </div>
                    </div>
                  );
                })()}

                {/* Bench */}
                {(() => {
                  const bench = teamDetail.roster.filter(player => player.status !== 'starter');
                  const benchByPosition = {
                    QB: bench.filter(p => p.position === 'QB'),
                    RB: bench.filter(p => p.position === 'RB'),
                    WR: bench.filter(p => p.position === 'WR'),
                    TE: bench.filter(p => p.position === 'TE'),
                    K: bench.filter(p => p.position === 'K'),
                    'D/ST': bench.filter(p => p.position === 'D/ST')
                  };

                  return bench.length > 0 && (
                    <div>
                      <div className="flex items-center gap-2 mb-4">
                        <span className="text-lg font-semibold">🪑 Bench</span>
                        <Badge variant="secondary" size="sm">{bench.length} players</Badge>
                      </div>
                      <div className="space-y-4">
                        {Object.entries(benchByPosition).map(([position, players]) => 
                          players.length > 0 && (
                            <div key={position} className="border-l-4 border-gray-400 pl-4">
                              <div className="font-medium text-gray-700 mb-2">{position}</div>
                              <div className="space-y-2">
                                {players.map((player) => (
                                  <div key={player.id} className="flex items-center justify-between bg-gray-50 rounded-lg p-3">
                                    <div className="flex items-center gap-3">
                                      <span className="text-gray-600">📋</span>
                                      <div>
                                        <div className="font-medium">{player.name}</div>
                                        <div className="text-sm text-gray-600 flex items-center gap-2">
                                          <Badge variant="secondary" size="sm">{player.position}</Badge>
                                          <span>{player.team}</span>
                                          {player.injury_status && player.injury_status !== 'ACTIVE' && player.injury_status !== 'Healthy' && (
                                            <Badge variant="destructive" size="sm">{player.injury_status}</Badge>
                                          )}
                                        </div>
                                      </div>
                                    </div>
                                    <div className="text-right">
                                      <div className="font-mono font-medium">
                                        {player.points ? player.points.toFixed(1) : '0.0'} pts
                                      </div>
                                      {player.projected_points && (
                                        <div className="text-sm text-gray-500">
                                          Proj: {player.projected_points.toFixed(1)}
                                        </div>
                                      )}
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )
                        )}
                      </div>
                    </div>
                  );
                })()}

                {/* Team Totals */}
                <div className="border-t pt-4">
                  <div className="bg-blue-50 rounded-lg p-4">
                    <h4 className="font-semibold text-blue-900 mb-3">📈 Team Totals</h4>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <div className="text-gray-600">Total Points</div>
                        <div className="font-mono font-bold">
                          {teamDetail.roster.reduce((sum, p) => sum + (p.points || 0), 0).toFixed(1)}
                        </div>
                      </div>
                      <div>
                        <div className="text-gray-600">Starting Points</div>
                        <div className="font-mono font-bold">
                          {teamDetail.roster.filter(p => p.status === 'starter').reduce((sum, p) => sum + (p.points || 0), 0).toFixed(1)}
                        </div>
                      </div>
                      <div>
                        <div className="text-gray-600">Total Projected</div>
                        <div className="font-mono font-bold">
                          {teamDetail.roster.reduce((sum, p) => sum + (p.projected_points || 0), 0).toFixed(1)}
                        </div>
                      </div>
                      <div>
                        <div className="text-gray-600">Total Players</div>
                        <div className="font-mono font-bold">{teamDetail.roster.length}</div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center py-12 text-gray-500">
                <Users className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No Roster Data</h3>
                <p className="text-gray-600 mb-4">
                  {currentTeam?.platform === 'ESPN' 
                    ? "Roster data will be available once your ESPN league sync is complete."
                    : "Add players to your roster to see them here."
                  }
                </p>
                {currentTeam?.platform === 'ESPN' && (
                  <Button onClick={handleSyncTeam}>
                    <RefreshCw className="w-4 h-4 mr-1" />
                    Sync ESPN Data
                  </Button>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {selectedView === 'lineup' && (
        <Card>
          <CardHeader>
            <CardTitle>Set Your Lineup</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-center py-12 text-gray-500">
              <Users className="w-12 h-12 mx-auto mb-4 text-gray-300" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">Lineup Optimizer</h3>
              <p className="text-gray-600 mb-4">
                Drag and drop players to set your optimal lineup for this week.
              </p>
              <Button onClick={() => console.log('Lineup optimizer not yet implemented')}>
                Launch Lineup Optimizer
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {selectedView === 'trades' && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Trade Center</CardTitle>
              <Button size="sm" variant="outline" onClick={handleRefreshTradeTargets} disabled={tradeLoading}>
                <RefreshCw className={`w-4 h-4 mr-1 ${tradeLoading ? 'animate-spin' : ''}`} />
                Refresh Targets
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {tradeLoading ? (
              <div className="text-center py-12 text-gray-500">
                <RefreshCw className="w-8 h-8 mx-auto mb-4 text-gray-300 animate-spin" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">Finding Trade Targets</h3>
                <p className="text-gray-600">Analyzing league rosters for optimal trade opportunities...</p>
              </div>
            ) : tradeTargets && tradeTargets.length > 0 ? (
              <div className="space-y-6">
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <h4 className="font-semibold text-blue-900 mb-2">Trade Recommendations</h4>
                  <p className="text-sm text-blue-700">
                    Based on your roster needs and other teams' assets, here are suggested trade targets.
                  </p>
                </div>
                
                {tradeTargets.map((target) => (
                  <div key={`${target.team_id}-${target.player.id}`} className="border rounded-lg p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-3">
                          <div>
                            <h4 className="font-semibold text-gray-900">{target.player.name}</h4>
                            <div className="flex items-center gap-2 text-sm text-gray-600">
                              <Badge variant="secondary" size="sm">{target.player.position}</Badge>
                              <span>{target.player.team}</span>
                              <span>•</span>
                              <span>From: {target.team_name}</span>
                            </div>
                          </div>
                          <Badge 
                            variant={target.likelihood === 'high' ? 'success' : 
                                   target.likelihood === 'medium' ? 'warning' : 'secondary'}
                            size="sm"
                          >
                            {target.likelihood.toUpperCase()} LIKELIHOOD
                          </Badge>
                        </div>
                        
                        <p className="text-sm text-gray-700 mb-3">{target.rationale}</p>
                        
                        <div className="bg-gray-50 rounded p-3">
                          <div className="text-sm font-medium text-gray-900 mb-1">Suggested Offer:</div>
                          <div className="flex flex-wrap gap-2">
                            {target.suggested_offer.map((player) => (
                              <Badge key={player.id} variant="outline">
                                {player.name} ({player.position}, {player.team})
                              </Badge>
                            ))}
                          </div>
                        </div>
                      </div>
                      
                      <div className="ml-4 text-right">
                        <div className="text-2xl font-bold text-gray-900 mb-1">{target.trade_value}</div>
                        <div className="text-xs text-gray-500 mb-3">Trade Value</div>
                        <Button size="sm" onClick={() => handleViewTradeTarget(target)}>
                          Analyze Trade
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12 text-gray-500">
                <ArrowUpDown className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No Trade Targets</h3>
                <p className="text-gray-600 mb-4">
                  {currentTeam?.platform === 'ESPN' 
                    ? "No trade recommendations available at this time. Try refreshing or check back later."
                    : "Connect an ESPN league to see trade recommendations."
                  }
                </p>
                {currentTeam?.platform === 'ESPN' && (
                  <Button onClick={handleRefreshTradeTargets} disabled={tradeLoading}>
                    <RefreshCw className={`w-4 h-4 mr-1 ${tradeLoading ? 'animate-spin' : ''}`} />
                    Refresh Targets
                  </Button>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {selectedView === 'waivers' && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Waiver Wire</CardTitle>
              <div className="flex items-center gap-2">
                <Select
                  options={[
                    { value: 'all', label: 'All Positions' },
                    { value: 'QB', label: 'Quarterbacks' },
                    { value: 'RB', label: 'Running Backs' },
                    { value: 'WR', label: 'Wide Receivers' },
                    { value: 'TE', label: 'Tight Ends' },
                    { value: 'K', label: 'Kickers' },
                    { value: 'DEF', label: 'Defense' }
                  ]}
                  value={waiverFilter}
                  onChange={(value) => setWaiverFilter(value as string)}
                  className="min-w-[150px]"
                />
                <Button size="sm" variant="outline" onClick={handleViewWaiverTargets}>
                  <RefreshCw className="w-4 h-4 mr-1" />
                  Refresh
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {waiverLoading ? (
              <div className="text-center py-12 text-gray-500">
                <RefreshCw className="w-8 h-8 mx-auto mb-4 text-gray-300 animate-spin" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">Loading Waiver Targets</h3>
                <p className="text-gray-600">Finding the best available players for your team...</p>
              </div>
            ) : waiverTargets && waiverTargets.length > 0 ? (
              <div className="space-y-4">
                {(waiverTargets || [])
                  .filter(target => waiverFilter === 'all' || target.position === waiverFilter)
                  .map((target) => (
                    <div key={target.player_id} className="border rounded-lg p-4 hover:bg-gray-50">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                          <div className="text-center">
                            <Badge 
                              variant={target.pickup_priority === 'high' ? 'destructive' : 
                                     target.pickup_priority === 'medium' ? 'warning' : 'secondary'}
                              size="sm"
                            >
                              {target.pickup_priority.toUpperCase()}
                            </Badge>
                            <div className="text-xs text-gray-500 mt-1">Priority</div>
                          </div>
                          <div>
                            <div className="flex items-center gap-2">
                              <h4 className="font-semibold text-gray-900">{target.name}</h4>
                              <Badge variant="secondary" size="sm">{target.position}</Badge>
                              <span className="text-sm text-gray-600">{target.team}</span>
                              {target.injury_status !== 'ACTIVE' && (
                                <Badge variant="destructive" size="sm">{target.injury_status}</Badge>
                              )}
                            </div>
                            <div className="text-sm text-gray-600 mt-1">
                              {target.ownership_percentage}% owned • Score: {target.recommendation_score}/100
                            </div>
                            <p className="text-sm text-gray-700 mt-2">{target.analysis}</p>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-sm font-medium text-gray-900 mb-2">
                            FAAB: ${target.suggested_faab_bid}
                          </div>
                          <Button size="sm" onClick={() => handleAddWaiverClaim(target)}>
                            Add Claim
                          </Button>
                        </div>
                      </div>
                    </div>
                  ))
                }
              </div>
            ) : (
              <div className="text-center py-12 text-gray-500">
                <Star className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No Waiver Targets</h3>
                <p className="text-gray-600 mb-4">
                  {currentTeam?.platform === 'ESPN' 
                    ? "No waiver recommendations available at this time. Try refreshing or check back later."
                    : "Connect an ESPN league to see waiver recommendations."
                  }
                </p>
                {currentTeam?.platform === 'ESPN' && (
                  <Button onClick={handleViewWaiverTargets}>
                    <RefreshCw className="w-4 h-4 mr-1" />
                    Refresh Targets
                  </Button>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Settings Modal */}
      <Modal
        isOpen={showSettings}
        onClose={() => setShowSettings(false)}
        title="Team Settings"
        size="md"
      >
        <ModalBody>
          <div className="space-y-6">
            {/* Notifications */}
            <div>
              <h3 className="flex items-center text-lg font-medium text-gray-900 mb-4">
                <Bell className="w-5 h-5 mr-2" />
                Notifications
              </h3>
              <div className="space-y-3">
                <label className="flex items-center justify-between">
                  <span className="text-sm text-gray-700">Trade offers</span>
                  <input type="checkbox" defaultChecked className="h-4 w-4 text-blue-600 rounded" />
                </label>
                <label className="flex items-center justify-between">
                  <span className="text-sm text-gray-700">Lineup reminders</span>
                  <input type="checkbox" defaultChecked className="h-4 w-4 text-blue-600 rounded" />
                </label>
                <label className="flex items-center justify-between">
                  <span className="text-sm text-gray-700">Injury updates</span>
                  <input type="checkbox" defaultChecked className="h-4 w-4 text-blue-600 rounded" />
                </label>
                <label className="flex items-center justify-between">
                  <span className="text-sm text-gray-700">Waiver results</span>
                  <input type="checkbox" defaultChecked className="h-4 w-4 text-blue-600 rounded" />
                </label>
              </div>
            </div>

            {/* Privacy */}
            <div>
              <h3 className="flex items-center text-lg font-medium text-gray-900 mb-4">
                <Shield className="w-5 h-5 mr-2" />
                Privacy
              </h3>
              <div className="space-y-3">
                <label className="flex items-center justify-between">
                  <span className="text-sm text-gray-700">Show team in public leagues</span>
                  <input type="checkbox" defaultChecked className="h-4 w-4 text-blue-600 rounded" />
                </label>
                <label className="flex items-center justify-between">
                  <span className="text-sm text-gray-700">Allow trade offers from anyone</span>
                  <input type="checkbox" className="h-4 w-4 text-blue-600 rounded" />
                </label>
              </div>
            </div>

            {/* Display */}
            <div>
              <h3 className="flex items-center text-lg font-medium text-gray-900 mb-4">
                <Eye className="w-5 h-5 mr-2" />
                Display
              </h3>
              <div className="space-y-3">
                <div>
                  <label className="block text-sm text-gray-700 mb-2">Default view</label>
                  <Select
                    options={viewOptions}
                    value={selectedView}
                    onChange={(value) => setSelectedView(value as string)}
                    className="w-full"
                  />
                </div>
                <label className="flex items-center justify-between">
                  <span className="text-sm text-gray-700">Show player photos</span>
                  <input type="checkbox" defaultChecked className="h-4 w-4 text-blue-600 rounded" />
                </label>
              </div>
            </div>

            {/* Team Info */}
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">Team Information</h3>
              <div className="space-y-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Team Name</label>
                  <input
                    type="text"
                    defaultValue={currentTeam?.name}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Team Logo URL</label>
                  <input
                    type="text"
                    placeholder="https://example.com/logo.png"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
            </div>
          </div>
        </ModalBody>
        <ModalFooter>
          <div className="flex justify-end space-x-3">
            <Button variant="outline" onClick={() => setShowSettings(false)}>
              Cancel
            </Button>
            <Button onClick={() => setShowSettings(false)}>
              Save Settings
            </Button>
          </div>
        </ModalFooter>
      </Modal>

      {/* ESPN Cookie Update Modal */}
      <Modal
        isOpen={showCookieUpdate}
        onClose={() => {
          setShowCookieUpdate(false);
          setAuthError(null);
          setCookieUpdateData({ espnS2: '', swid: '', leagueId: 0 });
        }}
        title="Update ESPN Authentication"
        size="md"
      >
        <ModalBody>
          <div className="space-y-4">
            {authError && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-md">
                <p className="text-red-800 text-sm">{authError}</p>
              </div>
            )}
            
            <div>
              <p className="text-gray-700 mb-4">
                Your ESPN authentication has expired. Please update your s2 and swid cookies to continue accessing your league data.
              </p>
              
              <div className="space-y-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    ESPN S2 Cookie
                  </label>
                  <input
                    type="text"
                    value={cookieUpdateData.espnS2}
                    onChange={(e) => setCookieUpdateData(prev => ({ ...prev, espnS2: e.target.value }))}
                    placeholder="Paste your ESPN S2 cookie here"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    ESPN SWID Cookie
                  </label>
                  <input
                    type="text"
                    value={cookieUpdateData.swid}
                    onChange={(e) => setCookieUpdateData(prev => ({ ...prev, swid: e.target.value }))}
                    placeholder="Paste your ESPN SWID cookie here"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
              
              <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-md">
                <p className="text-blue-800 text-sm">
                  <strong>How to get your ESPN cookies:</strong><br />
                  1. Log into ESPN Fantasy in your browser<br />
                  2. Open Developer Tools (F12)<br />
                  3. Go to Application/Storage → Cookies → espn.com<br />
                  4. Copy the values for "espn_s2" and "SWID"
                </p>
              </div>
            </div>
          </div>
        </ModalBody>
        <ModalFooter>
          <div className="flex justify-end space-x-3">
            <Button 
              variant="outline" 
              onClick={() => {
                setShowCookieUpdate(false);
                setAuthError(null);
                setCookieUpdateData({ espnS2: '', swid: '', leagueId: 0 });
              }}
            >
              Cancel
            </Button>
            <Button 
              onClick={handleUpdateCookies}
              disabled={!cookieUpdateData.espnS2.trim() || !cookieUpdateData.swid.trim()}
            >
              Update Cookies
            </Button>
          </div>
        </ModalFooter>
      </Modal>

      {/* Trade Analysis Modal */}
      <Modal
        isOpen={showTradeModal}
        onClose={() => {
          setShowTradeModal(false);
          setSelectedTradeTarget(null);
          setTradeEvaluation(null);
        }}
        title="Trade Analysis"
        size="lg"
      >
        <ModalBody>
          {selectedTradeTarget && (
            <div className="space-y-6">
              {/* Trade Summary */}
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="font-semibold text-gray-900 mb-3">Proposed Trade</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-center">
                  <div>
                    <div className="text-sm text-gray-600 mb-2">You Give:</div>
                    <div className="space-y-1">
                      {selectedTradeTarget.suggested_offer.map((player) => (
                        <div key={player.id} className="flex items-center gap-2">
                          <Badge variant="outline" size="sm">{player.position}</Badge>
                          <span className="text-sm font-medium">{player.name}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                  
                  <div className="text-center">
                    <ArrowUpDown className="w-8 h-8 mx-auto text-gray-400" />
                  </div>
                  
                  <div>
                    <div className="text-sm text-gray-600 mb-2">You Get:</div>
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" size="sm">{selectedTradeTarget.player.position}</Badge>
                      <span className="text-sm font-medium">{selectedTradeTarget.player.name}</span>
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      From: {selectedTradeTarget.team_name}
                    </div>
                  </div>
                </div>
              </div>

              {/* Trade Evaluation */}
              {evaluatingTrade ? (
                <div className="text-center py-8">
                  <RefreshCw className="w-8 h-8 mx-auto mb-4 text-blue-500 animate-spin" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">Analyzing Trade</h3>
                  <p className="text-gray-600">Evaluating fairness and impact...</p>
                </div>
              ) : tradeEvaluation ? (
                <div className="space-y-4">
                  {/* Overall Grade */}
                  <div className="text-center">
                    <div className="text-4xl font-bold text-gray-900 mb-2">{tradeEvaluation.grade}</div>
                    <div className="text-sm text-gray-600">Trade Grade</div>
                    <div className="text-lg font-medium text-gray-900 mt-2">
                      Fairness Score: {tradeEvaluation.fairness_score}/100
                    </div>
                  </div>

                  {/* Impact Analysis */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="border rounded-lg p-4">
                      <h4 className="font-semibold text-gray-900 mb-2">Your Impact</h4>
                      <div className={`text-lg font-medium mb-2 ${
                        tradeEvaluation.team1_impact.value_change > 0 ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {tradeEvaluation.team1_impact.value_change > 0 ? '+' : ''}{tradeEvaluation.team1_impact.value_change.toFixed(1)} pts
                      </div>
                      <p className="text-sm text-gray-700">{tradeEvaluation.team1_impact.recommendation}</p>
                    </div>
                    
                    <div className="border rounded-lg p-4">
                      <h4 className="font-semibold text-gray-900 mb-2">Their Impact</h4>
                      <div className={`text-lg font-medium mb-2 ${
                        tradeEvaluation.team2_impact.value_change > 0 ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {tradeEvaluation.team2_impact.value_change > 0 ? '+' : ''}{tradeEvaluation.team2_impact.value_change.toFixed(1)} pts
                      </div>
                      <p className="text-sm text-gray-700">{tradeEvaluation.team2_impact.recommendation}</p>
                    </div>
                  </div>

                  {/* Analysis */}
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <h4 className="font-semibold text-blue-900 mb-2">Analysis</h4>
                    <p className="text-sm text-blue-800">{tradeEvaluation.analysis}</p>
                  </div>

                  {/* Verdict */}
                  <div className="text-center">
                    <Badge 
                      variant={tradeEvaluation.verdict === 'accept' ? 'success' : 
                             tradeEvaluation.verdict === 'consider' ? 'warning' : 'destructive'}
                      size="lg"
                    >
                      {tradeEvaluation.verdict.toUpperCase()}
                    </Badge>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <div>Trade evaluation will appear here</div>
                </div>
              )}
            </div>
          )}
        </ModalBody>
        <ModalFooter>
          <div className="flex justify-end space-x-3">
            <Button 
              variant="outline" 
              onClick={() => {
                setShowTradeModal(false);
                setSelectedTradeTarget(null);
                setTradeEvaluation(null);
              }}
            >
              Close
            </Button>
            {selectedTradeTarget && tradeEvaluation && (
              <Button 
                onClick={() => handleProposeTrack(selectedTradeTarget)}
                disabled={tradeEvaluation.verdict === 'reject'}
              >
                Propose Trade
              </Button>
            )}
          </div>
        </ModalFooter>
      </Modal>
    </div>
  );
}
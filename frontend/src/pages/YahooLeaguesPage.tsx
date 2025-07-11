import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Trophy,
  Users,
  Calendar,
  ExternalLink,
  Loader2,
  AlertCircle,
  Plus,
  RefreshCw,
  LogOut
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Alert } from '../components/common/Alert';
import { Badge } from '../components/common/Badge';
import { yahooService } from '../services/yahoo';
import type { YahooLeague, YahooAuthStatus } from '../services/yahooTypes';
import { toast } from '../utils/toast';

export const YahooLeaguesPage: React.FC = () => {
  const navigate = useNavigate();
  const [authStatus, setAuthStatus] = useState<YahooAuthStatus | null>(null);
  const [leagues, setLeagues] = useState<YahooLeague[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    try {
      const status = await yahooService.getAuthStatus();
      setAuthStatus(status);
      
      if (status.authenticated) {
        await loadLeagues();
      }
    } catch (err) {
      console.error('Failed to check auth status:', err);
      setAuthStatus({ authenticated: false, user_id: 0 });
    } finally {
      setLoading(false);
    }
  };

  const loadLeagues = async () => {
    try {
      setError(null);
      const data = await yahooService.getLeagues();
      setLeagues(data);
    } catch (err) {
      console.error('Failed to load leagues:', err);
      setError('Failed to load Yahoo leagues. Please try again.');
    }
  };

  const handleConnect = async () => {
    try {
      const { auth_url } = await yahooService.getAuthUrl();
      window.location.href = auth_url;
    } catch (err) {
      console.error('Failed to get auth URL:', err);
      toast.error('Failed to start Yahoo authentication');
    }
  };

  const handleDisconnect = async () => {
    if (!confirm('Are you sure you want to disconnect your Yahoo account?')) {
      return;
    }

    try {
      await yahooService.disconnect();
      setAuthStatus({ authenticated: false, user_id: authStatus?.user_id || 0 });
      setLeagues([]);
      toast.success('Yahoo account disconnected');
    } catch (err) {
      console.error('Failed to disconnect:', err);
      toast.error('Failed to disconnect Yahoo account');
    }
  };

  const handleSync = async (leagueKey: string) => {
    setSyncing(leagueKey);
    try {
      const result = await yahooService.syncLeague(leagueKey);
      if (result.success) {
        toast.success(`Synced ${result.league_name} (${result.teams_synced} teams)`);
        await loadLeagues();
      } else {
        throw new Error(result.error || 'Sync failed');
      }
    } catch (err) {
      console.error('Failed to sync league:', err);
      toast.error('Failed to sync league data');
    } finally {
      setSyncing(null);
    }
  };

  const getDraftStatusColor = (status: string) => {
    switch (status) {
      case 'predraft':
        return 'secondary';
      case 'drafting':
        return 'warning';
      case 'postdraft':
        return 'success';
      default:
        return 'default';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!authStatus?.authenticated) {
    return (
      <div className="container mx-auto px-4 py-8">
        <Card className="max-w-2xl mx-auto">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Trophy className="w-6 h-6" />
              Connect Yahoo Fantasy
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-muted-foreground">
              Connect your Yahoo Fantasy account to import your leagues, track your teams,
              and get AI-powered insights for your Yahoo fantasy football leagues.
            </p>
            
            <div className="bg-muted p-4 rounded-lg">
              <h4 className="font-semibold mb-2">What you'll get:</h4>
              <ul className="space-y-1 text-sm text-muted-foreground">
                <li>• Import all your Yahoo fantasy leagues</li>
                <li>• Real-time roster tracking and updates</li>
                <li>• AI-powered trade suggestions</li>
                <li>• Waiver wire recommendations</li>
                <li>• Cross-platform player analysis</li>
              </ul>
            </div>

            <Alert>
              <AlertCircle className="h-4 w-4" />
              <div>
                <p className="text-sm">
                  You'll be redirected to Yahoo to authorize access. We only request
                  read permissions and never make changes to your leagues.
                </p>
              </div>
            </Alert>

            <Button onClick={handleConnect} className="w-full">
              <Plus className="w-4 h-4 mr-2" />
              Connect Yahoo Account
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold">Yahoo Fantasy Leagues</h1>
          <p className="text-muted-foreground mt-2">
            Manage and track your Yahoo fantasy football leagues
          </p>
        </div>
        
        <div className="flex gap-2">
          <Button onClick={() => loadLeagues()} variant="outline">
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
          <Button onClick={handleDisconnect} variant="outline" className="text-destructive">
            <LogOut className="w-4 h-4 mr-2" />
            Disconnect
          </Button>
        </div>
      </div>

      {error && (
        <Alert variant="destructive" className="mb-6">
          <AlertCircle className="h-4 w-4" />
          <div>{error}</div>
        </Alert>
      )}

      {leagues.length === 0 ? (
        <Card>
          <CardContent className="text-center py-12">
            <Trophy className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
            <h3 className="text-lg font-semibold mb-2">No Leagues Found</h3>
            <p className="text-muted-foreground">
              You don't have any Yahoo fantasy leagues for the current season.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {leagues.map((league) => (
            <Card
              key={league.league_key}
              className="hover:shadow-lg transition-shadow cursor-pointer"
              onClick={() => navigate(`/yahoo/leagues/${league.league_key}`)}
            >
              <CardHeader>
                <div className="flex justify-between items-start">
                  <CardTitle className="text-lg">{league.name}</CardTitle>
                  <Badge variant={getDraftStatusColor(league.draft_status)}>
                    {league.draft_status}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground flex items-center gap-1">
                    <Users className="w-4 h-4" />
                    {league.num_teams} teams
                  </span>
                  <span className="text-muted-foreground flex items-center gap-1">
                    <Calendar className="w-4 h-4" />
                    {league.season}
                  </span>
                </div>

                {league.user_team && (
                  <div className="border-t pt-3">
                    <div className="flex justify-between items-center">
                      <div>
                        <p className="font-semibold text-sm">{league.user_team.name}</p>
                        <p className="text-xs text-muted-foreground">
                          Rank: {league.user_team.rank || 'N/A'} | 
                          Record: {league.user_team.wins}-{league.user_team.losses}
                          {league.user_team.ties > 0 && `-${league.user_team.ties}`}
                        </p>
                      </div>
                    </div>
                  </div>
                )}

                <div className="flex gap-2 pt-2">
                  {league.draft_status === 'drafting' && (
                    <Button
                      size="sm"
                      variant="primary"
                      className="flex-1"
                      onClick={(e) => {
                        e.stopPropagation();
                        navigate(`/yahoo/draft/${league.league_key}`);
                      }}
                    >
                      <Trophy className="w-4 h-4 mr-1" />
                      Enter Draft
                    </Button>
                  )}
                  <Button
                    size="sm"
                    variant="outline"
                    className={league.draft_status === 'drafting' ? '' : 'flex-1'}
                    onClick={(e) => {
                      e.stopPropagation();
                      navigate(`/yahoo/leagues/${league.league_key}`);
                    }}
                  >
                    <ExternalLink className="w-4 h-4 mr-1" />
                    View
                  </Button>
                  {league.draft_status !== 'drafting' && (
                    <Button
                      size="sm"
                      variant="outline"
                      className="flex-1"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleSync(league.league_key);
                      }}
                      disabled={syncing === league.league_key}
                    >
                      {syncing === league.league_key ? (
                        <Loader2 className="w-4 h-4 mr-1 animate-spin" />
                      ) : (
                        <RefreshCw className="w-4 h-4 mr-1" />
                      )}
                      Sync
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};
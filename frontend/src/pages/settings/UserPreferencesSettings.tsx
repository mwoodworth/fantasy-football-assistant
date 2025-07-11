import { useState, useEffect } from 'react';
import { useAuthStore } from '../../store/useAuthStore';
import { Button } from '../../components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { Alert, AlertDescription } from '../../components/ui/alert';
import { Loader2, AlertCircle, CheckCircle } from 'lucide-react';
import api from '../../services/api';

interface Preferences {
  favorite_team: string | null;
  default_league_size: number;
  preferred_scoring: string;
}

const NFL_TEAMS = [
  { value: 'ARI', label: 'Arizona Cardinals' },
  { value: 'ATL', label: 'Atlanta Falcons' },
  { value: 'BAL', label: 'Baltimore Ravens' },
  { value: 'BUF', label: 'Buffalo Bills' },
  { value: 'CAR', label: 'Carolina Panthers' },
  { value: 'CHI', label: 'Chicago Bears' },
  { value: 'CIN', label: 'Cincinnati Bengals' },
  { value: 'CLE', label: 'Cleveland Browns' },
  { value: 'DAL', label: 'Dallas Cowboys' },
  { value: 'DEN', label: 'Denver Broncos' },
  { value: 'DET', label: 'Detroit Lions' },
  { value: 'GB', label: 'Green Bay Packers' },
  { value: 'HOU', label: 'Houston Texans' },
  { value: 'IND', label: 'Indianapolis Colts' },
  { value: 'JAX', label: 'Jacksonville Jaguars' },
  { value: 'KC', label: 'Kansas City Chiefs' },
  { value: 'LAC', label: 'Los Angeles Chargers' },
  { value: 'LAR', label: 'Los Angeles Rams' },
  { value: 'LV', label: 'Las Vegas Raiders' },
  { value: 'MIA', label: 'Miami Dolphins' },
  { value: 'MIN', label: 'Minnesota Vikings' },
  { value: 'NE', label: 'New England Patriots' },
  { value: 'NO', label: 'New Orleans Saints' },
  { value: 'NYG', label: 'New York Giants' },
  { value: 'NYJ', label: 'New York Jets' },
  { value: 'PHI', label: 'Philadelphia Eagles' },
  { value: 'PIT', label: 'Pittsburgh Steelers' },
  { value: 'SEA', label: 'Seattle Seahawks' },
  { value: 'SF', label: 'San Francisco 49ers' },
  { value: 'TB', label: 'Tampa Bay Buccaneers' },
  { value: 'TEN', label: 'Tennessee Titans' },
  { value: 'WAS', label: 'Washington Commanders' },
];

export function UserPreferencesSettings() {
  const { user, updateUser } = useAuthStore();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [preferences, setPreferences] = useState<Preferences>({
    favorite_team: null,
    default_league_size: 12,
    preferred_scoring: 'standard',
  });

  useEffect(() => {
    fetchPreferences();
  }, []);

  const fetchPreferences = async () => {
    try {
      const response = await api.get('/user/preferences');
      setPreferences(response.data);
    } catch (err: any) {
      setError('Failed to load preferences');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await api.put('/user/preferences', preferences);
      
      // Update local user state
      if (user) {
        updateUser({
          ...user,
          favorite_team: preferences.favorite_team,
          default_league_size: preferences.default_league_size,
          preferred_scoring: preferences.preferred_scoring,
        });
      }
      
      setSuccess('Preferences updated successfully');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update preferences');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6">
      <div className="border-b pb-4 mb-6">
        <h2 className="text-xl font-semibold text-gray-900">Fantasy Preferences</h2>
        <p className="mt-1 text-sm text-gray-600">
          Customize your fantasy football experience
        </p>
      </div>

      {error && (
        <Alert variant="destructive" className="mb-6">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {success && (
        <Alert className="mb-6 bg-green-50 border-green-200">
          <CheckCircle className="h-4 w-4 text-green-600" />
          <AlertDescription className="text-green-800">{success}</AlertDescription>
        </Alert>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Favorite NFL Team
          </label>
          <Select
            value={preferences.favorite_team || 'none'}
            onValueChange={(value) => 
              setPreferences({ ...preferences, favorite_team: value === 'none' ? null : value })
            }
          >
            <SelectTrigger className="w-full">
              <SelectValue placeholder="Select your favorite team" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="none">No favorite team</SelectItem>
              {NFL_TEAMS.map((team) => (
                <SelectItem key={team.value} value={team.value}>
                  {team.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <p className="mt-1 text-xs text-gray-500">
            We'll highlight your team's players and provide relevant news
          </p>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Default League Size
          </label>
          <Select
            value={preferences.default_league_size.toString()}
            onValueChange={(value) => 
              setPreferences({ ...preferences, default_league_size: parseInt(value) })
            }
          >
            <SelectTrigger className="w-full">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="6">6 Teams</SelectItem>
              <SelectItem value="8">8 Teams</SelectItem>
              <SelectItem value="10">10 Teams</SelectItem>
              <SelectItem value="12">12 Teams</SelectItem>
              <SelectItem value="14">14 Teams</SelectItem>
              <SelectItem value="16">16 Teams</SelectItem>
              <SelectItem value="18">18 Teams</SelectItem>
              <SelectItem value="20">20 Teams</SelectItem>
            </SelectContent>
          </Select>
          <p className="mt-1 text-xs text-gray-500">
            Used as default when creating mock drafts or analyzing players
          </p>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Preferred Scoring System
          </label>
          <Select
            value={preferences.preferred_scoring}
            onValueChange={(value) => 
              setPreferences({ ...preferences, preferred_scoring: value })
            }
          >
            <SelectTrigger className="w-full">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="standard">Standard Scoring</SelectItem>
              <SelectItem value="ppr">PPR (Point Per Reception)</SelectItem>
              <SelectItem value="half_ppr">Half PPR (0.5 Per Reception)</SelectItem>
            </SelectContent>
          </Select>
          <p className="mt-1 text-xs text-gray-500">
            Default scoring system for player projections and rankings
          </p>
        </div>

        <div className="pt-4 border-t">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Notification Preferences</h3>
          <div className="space-y-3">
            <label className="flex items-center">
              <input
                type="checkbox"
                className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                defaultChecked
              />
              <span className="ml-2 text-sm text-gray-700">
                Player news and updates
              </span>
            </label>
            <label className="flex items-center">
              <input
                type="checkbox"
                className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                defaultChecked
              />
              <span className="ml-2 text-sm text-gray-700">
                Trade suggestions
              </span>
            </label>
            <label className="flex items-center">
              <input
                type="checkbox"
                className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                defaultChecked
              />
              <span className="ml-2 text-sm text-gray-700">
                Waiver wire recommendations
              </span>
            </label>
            <label className="flex items-center">
              <input
                type="checkbox"
                className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
              />
              <span className="ml-2 text-sm text-gray-700">
                Weekly newsletters
              </span>
            </label>
          </div>
        </div>

        <div className="flex justify-end pt-4 border-t">
          <Button type="submit" disabled={loading}>
            {loading ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Saving...
              </>
            ) : (
              'Save Preferences'
            )}
          </Button>
        </div>
      </form>
    </div>
  );
}
import { useState, useEffect } from 'react';
import { useMutation } from '@tanstack/react-query';
import { AlertCircle, HelpCircle, Loader2, Users, ChevronRight } from 'lucide-react';
import { espnService, type LeagueConnection } from '../../services/espn';
import { Button } from '../common/Button';
import { Input } from '../common/Input';
import { Select } from '../common/Select';

interface ConnectLeagueFormProps {
  onSuccess: () => void;
  onCancel: () => void;
}

interface Team {
  id: number;
  name: string;
  owner?: string;
  abbreviation?: string;
}

export function ConnectLeagueForm({ onSuccess, onCancel }: ConnectLeagueFormProps) {
  const [formData, setFormData] = useState<LeagueConnection & { user_team_id?: number }>({
    espn_league_id: 0,
    season: new Date().getFullYear(),
    league_name: '',
    espn_s2: '',
    swid: '',
    user_team_id: undefined,
  });
  const [showPrivateHelp, setShowPrivateHelp] = useState(false);
  const [teams, setTeams] = useState<Team[]>([]);
  const [loadingTeams, setLoadingTeams] = useState(false);
  const [teamsError, setTeamsError] = useState<string | null>(null);

  const connectMutation = useMutation({
    mutationFn: espnService.connectLeague,
    onSuccess: () => {
      onSuccess();
    },
  });

  // Auto-load teams when league ID and season are provided
  useEffect(() => {
    if (formData.espn_league_id > 0 && formData.season) {
      // Debounce the API call
      const timer = setTimeout(() => {
        fetchTeams();
      }, 500);
      
      return () => clearTimeout(timer);
    }
  }, [formData.espn_league_id, formData.season]);

  const fetchTeams = async () => {
    if (!formData.espn_league_id || !formData.season) {
      console.log('Skipping team fetch - missing league ID or season');
      return;
    }
    
    console.log('Fetching teams for league:', formData.espn_league_id, 'season:', formData.season);
    
    setLoadingTeams(true);
    setTeamsError(null);
    setTeams([]);
    
    try {
      // Fetch teams from ESPN API
      const token = localStorage.getItem('token');
      if (!token) {
        console.warn('No auth token found, skipping team fetch');
        return;
      }
      
      const response = await fetch(
        `/api/espn/leagues/${formData.espn_league_id}/teams?season=${formData.season}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        }
      );
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('API error response:', errorText);
        throw new Error(`Failed to fetch teams: ${response.status}`);
      }
      
      const result = await response.json();
      console.log('Teams API response:', result);
      
      if (result.success && result.data && Array.isArray(result.data)) {
        const teamsData: Team[] = result.data.map((team: any, index: number) => ({
          id: team.id || team.teamId || index + 1,
          name: team.name || (team.location ? `${team.location} ${team.nickname}` : `Team ${index + 1}`),
          owner: team.primaryOwner || team.owners?.[0] || 'Unknown Owner',
          abbreviation: team.abbrev || team.abbreviation || 'TM',
        }));
        console.log('Parsed teams data:', teamsData);
        setTeams(teamsData);
      } else {
        console.warn('Invalid response format, using mock data');
        throw new Error('Invalid response format');
      }
    } catch (error) {
      console.error('Failed to fetch teams:', error);
      setTeamsError('Failed to load teams. You can still continue without selecting a team.');
      
      // Fall back to mock data if API fails
      const mockTeams: Team[] = Array.from({ length: 10 }, (_, i) => ({
        id: i + 1,
        name: `Team ${i + 1}`,
        owner: `Owner ${i + 1}`,
        abbreviation: `T${i + 1}`,
      }));
      setTeams(mockTeams);
    } finally {
      setLoadingTeams(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validate required fields
    if (!formData.espn_league_id || !espnService.validateLeagueId(formData.espn_league_id.toString())) {
      return;
    }
    
    if (!espnService.validateSeason(formData.season)) {
      return;
    }

    // If teams were loaded, require team selection
    if (teams.length > 0 && !formData.user_team_id) {
      setTeamsError('Please select your team from the list');
      return;
    }

    connectMutation.mutate(formData);
  };

  const handleInputChange = (field: keyof typeof formData, value: string | number) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  try {
    return (
      <div className="space-y-6 p-6">
        <form onSubmit={handleSubmit} className="space-y-6">
        {/* Basic League Information */}
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <span className="text-2xl">🏈</span>
            League Information
          </h3>
          
          <div className="grid grid-cols-2 gap-4">
            {/* League ID */}
            <div className="col-span-2 sm:col-span-1">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                ESPN League ID *
              </label>
              <Input
                type="number"
                value={formData.espn_league_id || ''}
                onChange={(e) => {
                  const value = e.target.value;
                  if (value === '') {
                    handleInputChange('espn_league_id', 0);
                  } else {
                    const parsed = parseInt(value);
                    if (!isNaN(parsed)) {
                      handleInputChange('espn_league_id', parsed);
                    }
                  }
                }}
                placeholder="123456789"
                required
                className="w-full"
              />
              <p className="text-xs text-gray-500 mt-1">
                From URL: ...leagueId=<strong>123456789</strong>
              </p>
            </div>

            {/* Season */}
            <div className="col-span-2 sm:col-span-1">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Season *
              </label>
              <Input
                type="number"
                value={formData.season}
                onChange={(e) => handleInputChange('season', parseInt(e.target.value))}
                min={2020}
                max={new Date().getFullYear() + 1}
                required
                className="w-full"
              />
            </div>
          </div>

          {/* Custom League Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Custom League Name
            </label>
            <Input
              type="text"
              value={formData.league_name}
              onChange={(e) => handleInputChange('league_name', e.target.value)}
              placeholder="My Awesome League (optional)"
              className="w-full"
            />
          </div>
        </div>

        {/* Team Selection */}
        {(teams.length > 0 || loadingTeams) && (
          <div className="space-y-4 p-4 bg-green-50 rounded-lg border border-green-200">
            <h3 className="text-lg font-semibold text-green-900 flex items-center gap-2">
              <Users className="h-5 w-5" />
              Select Your Team
            </h3>
            
            {loadingTeams ? (
              <div className="flex items-center justify-center py-4">
                <Loader2 className="h-6 w-6 animate-spin text-green-600" />
                <span className="ml-2 text-sm text-gray-600">Loading teams...</span>
              </div>
            ) : (
              <div>
                <Select
                  value={formData.user_team_id?.toString() || ''}
                  onChange={(value) => handleInputChange('user_team_id', parseInt(value))}
                  className="w-full"
                  required={teams.length > 0}
                >
                  <option value="">Choose your team...</option>
                  {teams.map((team) => (
                    <option key={team.id} value={team.id}>
                      {team.name} {team.owner ? `(${team.owner})` : ''}
                    </option>
                  ))}
                </Select>
                <p className="text-xs text-green-700 mt-2">
                  This will be your default team when viewing league data
                </p>
              </div>
            )}
            
            {teamsError && (
              <div className="text-sm text-red-600 mt-2">
                {teamsError}
              </div>
            )}
          </div>
        )}

        {/* Private League Section */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <button
            type="button"
            onClick={() => setShowPrivateHelp(!showPrivateHelp)}
            className="w-full flex items-center justify-between text-left"
          >
            <div className="flex items-center gap-3">
              <HelpCircle className="h-5 w-5 text-blue-600 flex-shrink-0" />
              <div>
                <h4 className="font-medium text-blue-900">Private League Settings</h4>
                <p className="text-sm text-blue-700 mt-1">
                  Required for private leagues
                </p>
              </div>
            </div>
            <ChevronRight className={`h-5 w-5 text-blue-600 transition-transform ${showPrivateHelp ? 'rotate-90' : ''}`} />
          </button>

          {showPrivateHelp && (
            <div className="mt-4 space-y-4">
              <div className="bg-white rounded-lg p-4 space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    ESPN S2 Cookie
                  </label>
                  <Input
                    type="text"
                    value={formData.espn_s2}
                    onChange={(e) => handleInputChange('espn_s2', e.target.value)}
                    placeholder="Long alphanumeric string..."
                    className="w-full font-mono text-sm"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    ESPN SWID Cookie
                  </label>
                  <Input
                    type="text"
                    value={formData.swid}
                    onChange={(e) => handleInputChange('swid', e.target.value)}
                    placeholder="{XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX}"
                    className="w-full font-mono text-sm"
                  />
                </div>

                <div className="bg-gray-50 rounded p-3 text-xs text-gray-700">
                  <p className="font-semibold mb-2">How to find these cookies:</p>
                  <ol className="list-decimal list-inside space-y-1">
                    <li>Open ESPN Fantasy in your browser</li>
                    <li>Open Developer Tools (F12)</li>
                    <li>Go to Application → Cookies → espn.com</li>
                    <li>Find and copy "espn_s2" and "SWID" values</li>
                  </ol>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Error Display */}
        {connectMutation.error && (
          <div className="flex items-start gap-3 p-4 bg-red-50 border border-red-200 rounded-lg">
            <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-red-700">
              <p className="font-medium">Connection Failed</p>
              <p className="mt-1">
                {connectMutation.error instanceof Error 
                  ? connectMutation.error.message 
                  : 'Please check your league ID and try again.'}
              </p>
            </div>
          </div>
        )}

        {/* Submit Buttons */}
        <div className="flex gap-3 pt-2">
          <Button
            type="submit"
            disabled={connectMutation.isPending || (teams.length > 0 && !formData.user_team_id)}
            className="flex-1"
          >
            {connectMutation.isPending ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin mr-2" />
                Connecting...
              </>
            ) : (
              'Connect League'
            )}
          </Button>
          <Button
            type="button"
            variant="outline"
            onClick={onCancel}
            disabled={connectMutation.isPending}
          >
            Cancel
          </Button>
        </div>
      </form>
    </div>
    );
  } catch (error) {
    console.error('Error rendering ConnectLeagueForm:', error);
    return (
      <div className="p-6 text-red-600">
        <p>An error occurred while rendering the form. Please refresh the page.</p>
        <p className="text-sm mt-2">Error: {error instanceof Error ? error.message : 'Unknown error'}</p>
      </div>
    );
  }
}
import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { AlertCircle, HelpCircle } from 'lucide-react';
import { espnService, type LeagueConnection } from '../../services/espn';
import { Button } from '../common/Button';
import { Input } from '../common/Input';
import { Card } from '../common/Card';

interface ConnectLeagueFormProps {
  onSuccess: () => void;
  onCancel: () => void;
}

export function ConnectLeagueForm({ onSuccess, onCancel }: ConnectLeagueFormProps) {
  const [formData, setFormData] = useState<LeagueConnection>({
    espn_league_id: 0,
    season: new Date().getFullYear(),
    league_name: '',
    espn_s2: '',
    swid: '',
  });
  const [showPrivateHelp, setShowPrivateHelp] = useState(false);

  const connectMutation = useMutation({
    mutationFn: espnService.connectLeague,
    onSuccess: () => {
      onSuccess();
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validate required fields
    if (!formData.espn_league_id || !espnService.validateLeagueId(formData.espn_league_id.toString())) {
      return;
    }
    
    if (!espnService.validateSeason(formData.season)) {
      return;
    }

    connectMutation.mutate(formData);
  };

  const handleInputChange = (field: keyof LeagueConnection, value: string | number) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  return (
    <div className="space-y-6">
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* League ID */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            ESPN League ID *
          </label>
          <Input
            type="number"
            value={formData.espn_league_id || ''}
            onChange={(e) => handleInputChange('espn_league_id', parseInt(e.target.value) || 0)}
            placeholder="e.g., 123456789"
            required
          />
          <p className="text-xs text-gray-500 mt-1">
            Found in your ESPN league URL: espn.com/fantasy/football/league?leagueId=<strong>123456789</strong>
          </p>
        </div>

        {/* Season */}
        <div>
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
          />
        </div>

        {/* Custom League Name */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Custom League Name (Optional)
          </label>
          <Input
            type="text"
            value={formData.league_name}
            onChange={(e) => handleInputChange('league_name', e.target.value)}
            placeholder="e.g., My Awesome League"
          />
          <p className="text-xs text-gray-500 mt-1">
            Leave blank to use the league name from ESPN
          </p>
        </div>

        {/* Private League Section */}
        <Card className="bg-blue-50 border-blue-200 p-4">
          <div className="flex items-start gap-3">
            <HelpCircle className="h-5 w-5 text-blue-600 mt-0.5" />
            <div className="flex-1">
              <h4 className="font-medium text-blue-900 mb-2">Private League?</h4>
              <p className="text-sm text-blue-800 mb-3">
                If your league is private, you'll need to provide authentication cookies.
              </p>
              
              <button
                type="button"
                onClick={() => setShowPrivateHelp(!showPrivateHelp)}
                className="text-sm text-blue-600 hover:text-blue-700 underline"
              >
                {showPrivateHelp ? 'Hide instructions' : 'Show instructions'}
              </button>

              {showPrivateHelp && (
                <div className="mt-3 p-3 bg-white rounded border space-y-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      ESPN S2 Cookie
                    </label>
                    <Input
                      type="text"
                      value={formData.espn_s2}
                      onChange={(e) => handleInputChange('espn_s2', e.target.value)}
                      placeholder="Long alphanumeric string..."
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
                    />
                  </div>

                  <div className="text-xs text-gray-600 space-y-1">
                    <p><strong>How to find these cookies:</strong></p>
                    <ol className="list-decimal list-inside space-y-1">
                      <li>Open your browser's developer tools (F12)</li>
                      <li>Go to your ESPN league page</li>
                      <li>Open the "Application" or "Storage" tab</li>
                      <li>Find "Cookies" → "espn.com"</li>
                      <li>Copy the values for "espn_s2" and "SWID"</li>
                    </ol>
                  </div>
                </div>
              )}
            </div>
          </div>
        </Card>

        {/* Error Display */}
        {connectMutation.error && (
          <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded text-sm text-red-700">
            <AlertCircle className="h-4 w-4" />
            <span>
              {connectMutation.error instanceof Error 
                ? connectMutation.error.message 
                : 'Failed to connect league. Please check your league ID and try again.'}
            </span>
          </div>
        )}

        {/* Submit Buttons */}
        <div className="flex gap-3 pt-4">
          <Button
            type="submit"
            disabled={connectMutation.isPending}
            className="flex-1"
          >
            {connectMutation.isPending ? 'Connecting...' : 'Connect League'}
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
}
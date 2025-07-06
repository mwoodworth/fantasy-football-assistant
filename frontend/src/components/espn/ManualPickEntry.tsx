import { useState } from 'react';
import { Search } from 'lucide-react';
import { type DraftSession, type DraftPick } from '../../services/espn';
import { Modal } from '../common/Modal';
import { Button } from '../common/Button';
import { Input } from '../common/Input';
import { Select } from '../common/Select';
import { Badge } from '../common/Badge';

interface ManualPickEntryProps {
  session: DraftSession;
  onSubmit: (pick: DraftPick) => void;
  onCancel: () => void;
  isSubmitting: boolean;
}

const NFL_TEAMS = [
  'ARI', 'ATL', 'BAL', 'BUF', 'CAR', 'CHI', 'CIN', 'CLE', 'DAL', 'DEN',
  'DET', 'GB', 'HOU', 'IND', 'JAX', 'KC', 'LV', 'LAC', 'LAR', 'MIA',
  'MIN', 'NE', 'NO', 'NYG', 'NYJ', 'PHI', 'PIT', 'SF', 'SEA', 'TB',
  'TEN', 'WAS'
];

const POSITIONS = ['QB', 'RB', 'WR', 'TE', 'K', 'DEF'];

export function ManualPickEntry({ 
  session, 
  onSubmit, 
  onCancel, 
  isSubmitting 
}: ManualPickEntryProps) {
  const [pick, setPick] = useState<Partial<DraftPick>>({
    player_id: 0,
    player_name: '',
    position: '',
    team: '',
    pick_number: session.current_pick,
    drafted_by_user: session.current_pick === session.next_user_pick,
  });


  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!pick.player_name || !pick.position || !pick.team) {
      return;
    }

    const draftPick: DraftPick = {
      player_id: pick.player_id || Date.now(), // Use timestamp as fallback ID
      player_name: pick.player_name,
      position: pick.position,
      team: pick.team,
      pick_number: pick.pick_number!,
      drafted_by_user: pick.drafted_by_user!,
    };

    onSubmit(draftPick);
  };

  const handleInputChange = (field: keyof DraftPick, value: any) => {
    setPick(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const isUserPick = pick.pick_number === session.next_user_pick;

  return (
    <Modal 
      isOpen={true} 
      onClose={onCancel} 
      title={`Enter Draft Pick #${session.current_pick}`}
      size="lg"
    >
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Pick Info */}
        <div className="bg-gray-50 p-4 rounded-lg">
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-600">Pick Number:</span>
              <span className="ml-2 font-medium">#{session.current_pick}</span>
            </div>
            <div>
              <span className="text-gray-600">Round:</span>
              <span className="ml-2 font-medium">{session.current_round}</span>
            </div>
          </div>
          
          {isUserPick && (
            <div className="mt-2 flex items-center gap-2">
              <Badge variant="success">Your Pick</Badge>
              <span className="text-sm text-green-700">This pick will be added to your roster</span>
            </div>
          )}
        </div>

        {/* Player Search */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Player Name *
          </label>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input
              type="text"
              value={pick.player_name}
              onChange={(e) => handleInputChange('player_name', e.target.value)}
              placeholder="Enter player name..."
              className="pl-10"
              required
            />
          </div>
        </div>

        {/* Position */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Position *
          </label>
          <Select
            options={POSITIONS.map(position => ({ value: position, label: position }))}
            value={pick.position}
            onChange={(value) => handleInputChange('position', value)}
            placeholder="Select position"
          />
        </div>

        {/* Team */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            NFL Team *
          </label>
          <Select
            options={NFL_TEAMS.map(team => ({ value: team, label: team }))}
            value={pick.team}
            onChange={(value) => handleInputChange('team', value)}
            placeholder="Select team"
          />
        </div>

        {/* Pick Number Override */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Pick Number
          </label>
          <Input
            type="number"
            value={pick.pick_number}
            onChange={(e) => handleInputChange('pick_number', parseInt(e.target.value))}
            min={1}
            max={session.total_picks}
          />
          <p className="text-xs text-gray-500 mt-1">
            Usually you don't need to change this unless you're entering past picks
          </p>
        </div>

        {/* User Pick Toggle */}
        <div>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={pick.drafted_by_user}
              onChange={(e) => handleInputChange('drafted_by_user', e.target.checked)}
              className="rounded border-gray-300"
            />
            <span className="text-sm text-gray-700">This is my pick</span>
          </label>
        </div>

        {/* Submit Buttons */}
        <div className="flex gap-3 pt-4 border-t">
          <Button
            type="submit"
            disabled={isSubmitting || !pick.player_name || !pick.position || !pick.team}
            className="flex-1"
          >
            {isSubmitting ? 'Recording Pick...' : 'Record Pick'}
          </Button>
          <Button
            type="button"
            variant="outline"
            onClick={onCancel}
            disabled={isSubmitting}
          >
            Cancel
          </Button>
        </div>
      </form>
    </Modal>
  );
}
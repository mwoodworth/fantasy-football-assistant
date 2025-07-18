import { useState, useEffect } from 'react';
import { useMutation } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { Play, AlertCircle } from 'lucide-react';
import { espnService, type ESPNLeague, type DraftSessionStart } from '../../services/espn';
import { Modal } from '../common/Modal';
import { Button } from '../common/Button';
import { Input } from '../common/Input';
import { Card } from '../common/Card';

interface DraftSessionModalProps {
  isOpen: boolean;
  onClose: () => void;
  league: ESPNLeague;
}

export function DraftSessionModal({ isOpen, onClose, league }: DraftSessionModalProps) {
  const navigate = useNavigate();
  const [draftPosition, setDraftPosition] = useState(league.user_draft_position || 1);
  const [liveSync, setLiveSync] = useState(true);

  // Auto-populate draft position from league data
  useEffect(() => {
    if (league.user_draft_position) {
      setDraftPosition(league.user_draft_position);
    }
  }, [league.user_draft_position]);

  const startDraftMutation = useMutation({
    mutationFn: espnService.startDraftSession,
    onSuccess: (session) => {
      // Navigate to draft room with session data
      navigate(`/espn/draft/${session.id}`, { 
        state: { session, league }
      });
      onClose();
    },
  });

  const handleStartDraft = () => {
    const draftData: DraftSessionStart = {
      league_id: league.id,
      draft_position: draftPosition,
      live_sync: liveSync,
    };

    startDraftMutation.mutate(draftData);
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Start Draft Session">
      <div className="space-y-6">
        {/* League Info */}
        <Card className="bg-gray-50 p-4">
          <h3 className="font-medium text-gray-900 mb-2">{league.league_name}</h3>
          <div className="text-sm text-gray-600 space-y-1">
            <p>{league.season} Season • {league.team_count} Teams</p>
            <p>Scoring: {espnService.formatScoreType(league.scoring_type)}</p>
            {league.draft_date && (
              <p>Draft Date: {new Date(league.draft_date).toLocaleDateString()}</p>
            )}
          </div>
        </Card>

        {/* Draft Position */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Your Draft Position
          </label>
          <Input
            type="number"
            min={1}
            max={league.team_count}
            value={draftPosition}
            onChange={(e) => setDraftPosition(parseInt(e.target.value) || 1)}
            className="w-24"
          />
          <p className="text-xs text-gray-500 mt-1">
            Position {draftPosition} of {league.team_count} (Snake draft)
          </p>
        </div>

        {/* Live Sync Option */}
        <div className="flex items-center gap-3">
          <input
            type="checkbox"
            id="live-sync"
            checked={liveSync}
            onChange={(e) => setLiveSync(e.target.checked)}
            className="h-4 w-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500"
          />
          <label htmlFor="live-sync" className="text-sm text-gray-700">
            Enable Live ESPN Sync
            <span className="block text-xs text-gray-500">
              Automatically sync picks with your ESPN draft in real-time
            </span>
          </label>
        </div>


        {/* Warning for completed drafts */}
        {league.draft_completed && (
          <div className="flex items-center gap-2 p-3 bg-yellow-50 border border-yellow-200 rounded text-sm text-yellow-800">
            <AlertCircle className="h-4 w-4" />
            <span>
              This league's draft appears to be completed. You can still use draft mode for practice or analysis.
            </span>
          </div>
        )}

        {/* Error Display */}
        {startDraftMutation.error && (
          <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded text-sm text-red-700">
            <AlertCircle className="h-4 w-4" />
            <span>
              {startDraftMutation.error instanceof Error 
                ? startDraftMutation.error.message 
                : 'Failed to start draft session. Please try again.'}
            </span>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex gap-3">
          <Button
            onClick={handleStartDraft}
            disabled={startDraftMutation.isPending}
            className="flex-1 flex items-center justify-center gap-2"
          >
            {startDraftMutation.isPending ? (
              'Starting...'
            ) : (
              <>
                <Play className="h-4 w-4" />
                Start Draft Session
              </>
            )}
          </Button>
          <Button
            variant="outline"
            onClick={onClose}
            disabled={startDraftMutation.isPending}
          >
            Cancel
          </Button>
        </div>
      </div>
    </Modal>
  );
}
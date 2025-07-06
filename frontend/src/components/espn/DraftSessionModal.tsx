import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { Play, Wifi, WifiOff, AlertCircle } from 'lucide-react';
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
  const [draftPosition, setDraftPosition] = useState(1);
  const [liveSync, setLiveSync] = useState(true);

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

        {/* Sync Options */}
        <div className="space-y-4">
          <h4 className="font-medium text-gray-900">Draft Sync Options</h4>
          
          <div className="space-y-3">
            <label className="flex items-start gap-3 cursor-pointer">
              <input
                type="radio"
                name="syncMode"
                checked={liveSync}
                onChange={() => setLiveSync(true)}
                className="mt-1"
              />
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <Wifi className="h-4 w-4 text-green-600" />
                  <span className="font-medium">Live Sync (Recommended)</span>
                </div>
                <p className="text-sm text-gray-600 mt-1">
                  Automatically sync with ESPN draft room. Get real-time updates as picks are made.
                </p>
              </div>
            </label>

            <label className="flex items-start gap-3 cursor-pointer">
              <input
                type="radio"
                name="syncMode"
                checked={!liveSync}
                onChange={() => setLiveSync(false)}
                className="mt-1"
              />
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <WifiOff className="h-4 w-4 text-gray-600" />
                  <span className="font-medium">Manual Entry</span>
                </div>
                <p className="text-sm text-gray-600 mt-1">
                  Manually enter picks as they happen. Use this if live sync is not working.
                </p>
              </div>
            </label>
          </div>
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
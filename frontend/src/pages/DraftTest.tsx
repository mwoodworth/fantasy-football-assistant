import React, { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '../components/common/Card'
import { Button } from '../components/common/Button'
import { SimpleSelect as Select } from '../components/common/SimpleSelect'
import { Label } from '../components/common/Label'
import { DraftBoardGrid } from '../components/draft/DraftBoardGrid'
import { generateMockDraftSession } from '../utils/mockDraftData'

export function DraftTest() {
  const [teamCount, setTeamCount] = useState(12)
  const [userPosition, setUserPosition] = useState(3)
  const [currentPick, setCurrentPick] = useState(25)
  const [totalRounds, setTotalRounds] = useState(16)
  
  const mockSession = generateMockDraftSession(1, teamCount, userPosition, currentPick, totalRounds)
  
  const handleSimulatePick = () => {
    if (currentPick <= teamCount * totalRounds) {
      setCurrentPick(currentPick + 1)
    }
  }
  
  const handleReset = () => {
    setCurrentPick(1)
  }
  
  return (
    <div className="container mx-auto p-6 space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Draft Board Test</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div>
              <Label htmlFor="team-count">Number of Teams</Label>
              <Select
                id="team-count"
                value={teamCount.toString()}
                onValueChange={(value) => {
                  setTeamCount(parseInt(value))
                  setCurrentPick(1)
                }}
              >
                <option value="8">8 Teams</option>
                <option value="10">10 Teams</option>
                <option value="12">12 Teams</option>
                <option value="14">14 Teams</option>
              </Select>
            </div>
            
            <div>
              <Label htmlFor="user-position">Your Draft Position</Label>
              <Select
                id="user-position"
                value={userPosition.toString()}
                onValueChange={(value) => setUserPosition(parseInt(value))}
              >
                {Array.from({ length: teamCount }, (_, i) => (
                  <option key={i + 1} value={i + 1}>
                    Position {i + 1}
                  </option>
                ))}
              </Select>
            </div>
            
            <div>
              <Label htmlFor="current-pick">Current Pick</Label>
              <input
                id="current-pick"
                type="number"
                min="1"
                max={teamCount * totalRounds}
                value={currentPick}
                onChange={(e) => setCurrentPick(parseInt(e.target.value) || 1)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              />
            </div>
            
            <div>
              <Label htmlFor="total-rounds">Total Rounds</Label>
              <Select
                id="total-rounds"
                value={totalRounds.toString()}
                onValueChange={(value) => setTotalRounds(parseInt(value))}
              >
                <option value="12">12 Rounds</option>
                <option value="14">14 Rounds</option>
                <option value="16">16 Rounds</option>
                <option value="18">18 Rounds</option>
              </Select>
            </div>
          </div>
          
          <div className="flex gap-2 mb-6">
            <Button onClick={handleSimulatePick} disabled={currentPick > teamCount * totalRounds}>
              Simulate Next Pick
            </Button>
            <Button variant="outline" onClick={handleReset}>
              Reset Draft
            </Button>
          </div>
          
          <div className="mb-4 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-gray-600">Current Round:</span>{' '}
              <span className="font-semibold">{mockSession.current_round}</span>
            </div>
            <div>
              <span className="text-gray-600">Your Next Pick:</span>{' '}
              <span className="font-semibold">{mockSession.next_user_pick > 0 ? `#${mockSession.next_user_pick}` : 'Done'}</span>
            </div>
            <div>
              <span className="text-gray-600">Picks Until Your Turn:</span>{' '}
              <span className="font-semibold">{mockSession.picks_until_user_turn > 0 ? mockSession.picks_until_user_turn : '-'}</span>
            </div>
            <div>
              <span className="text-gray-600">Total Picks Made:</span>{' '}
              <span className="font-semibold">{mockSession.drafted_players.length}</span>
            </div>
          </div>
          
          <DraftBoardGrid
            picks={mockSession.drafted_players}
            teams={mockSession.teams}
            totalRounds={totalRounds}
            currentPick={currentPick}
            userTeamId={mockSession.user_team_id}
          />
        </CardContent>
      </Card>
    </div>
  )
}
import { useState } from 'react';
import { Chart } from '../components/analytics/Chart';
import { PlayerPerformanceChart } from '../components/analytics/PlayerPerformanceChart';
import { TeamAnalyticsWidget } from '../components/analytics/TeamAnalyticsWidget';
import { Card, CardContent, CardHeader, CardTitle } from '../components/common/Card';
import { Select } from '../components/common/Select';
import { Badge } from '../components/common/Badge';
import { BarChart3, TrendingUp, Users, Target, Calendar } from 'lucide-react';

// Mock data for demonstration
const mockPlayerPerformances = [
  { week: 1, points: 18.4, projected: 16.2, opponent: 'DAL', gameResult: 'win' as const },
  { week: 2, points: 24.7, projected: 18.1, opponent: 'NYG', gameResult: 'win' as const },
  { week: 3, points: 12.3, projected: 19.5, opponent: 'SF', gameResult: 'loss' as const },
  { week: 4, points: 31.2, projected: 17.8, opponent: 'MIA', gameResult: 'win' as const },
  { week: 5, points: 16.8, projected: 20.1, opponent: 'BUF', gameResult: 'loss' as const },
  { week: 6, points: 22.5, projected: 18.9, opponent: 'WAS', gameResult: 'win' as const },
  { week: 7, points: 19.7, projected: 17.4, opponent: 'PHI', gameResult: 'win' as const },
  { week: 8, points: 14.2, projected: 19.8, opponent: 'DEN', gameResult: 'loss' as const },
];

const mockTeamAnalytics = {
  weeklyScores: [
    { week: 1, points: 127.4, rank: 3 },
    { week: 2, points: 145.2, rank: 1 },
    { week: 3, points: 98.7, rank: 9 },
    { week: 4, points: 156.8, rank: 1 },
    { week: 5, points: 112.3, rank: 6 },
    { week: 6, points: 134.9, rank: 2 },
    { week: 7, points: 141.2, rank: 2 },
    { week: 8, points: 108.5, rank: 8 },
  ],
  positionBreakdown: [
    { position: 'QB', points: 312.4, percentage: 24.8 },
    { position: 'RB', points: 387.2, percentage: 30.7 },
    { position: 'WR', points: 298.7, percentage: 23.7 },
    { position: 'TE', points: 156.3, percentage: 12.4 },
    { position: 'K', points: 67.8, percentage: 5.4 },
    { position: 'DEF', points: 38.6, percentage: 3.0 },
  ],
  matchupHistory: [
    { week: 1, opponent: 'Team Alpha', result: 'win' as const, points: 127.4, opponentPoints: 115.2 },
    { week: 2, opponent: 'Team Beta', result: 'win' as const, points: 145.2, opponentPoints: 132.1 },
    { week: 3, opponent: 'Team Gamma', result: 'loss' as const, points: 98.7, opponentPoints: 118.9 },
    { week: 4, opponent: 'Team Delta', result: 'win' as const, points: 156.8, opponentPoints: 143.2 },
    { week: 5, opponent: 'Team Epsilon', result: 'loss' as const, points: 112.3, opponentPoints: 125.7 },
    { week: 6, opponent: 'Team Zeta', result: 'win' as const, points: 134.9, opponentPoints: 128.4 },
    { week: 7, opponent: 'Team Eta', result: 'win' as const, points: 141.2, opponentPoints: 136.8 },
    { week: 8, opponent: 'Team Theta', result: 'loss' as const, points: 108.5, opponentPoints: 119.3 },
  ],
  projectedFinish: { position: 3, playoffChance: 75.4, championshipChance: 12.8 },
  strengthOfSchedule: { remaining: 0.52, overall: 0.48 },
};

const leagueStatsData = [
  { label: 'You', value: 1024.2, color: '#3B82F6' },
  { label: 'Team Alpha', value: 987.5, color: '#10B981' },
  { label: 'Team Beta', value: 965.3, color: '#F59E0B' },
  { label: 'Team Gamma', value: 943.1, color: '#EF4444' },
  { label: 'Team Delta', value: 921.7, color: '#8B5CF6' },
  { label: 'Others', value: 4250.8, color: '#6B7280' },
];

export function AnalyticsPage() {
  const [selectedView, setSelectedView] = useState('overview');
  const [selectedPlayer, setSelectedPlayer] = useState('josh-allen');
  const [timeRange, setTimeRange] = useState('season');

  const viewOptions = [
    { value: 'overview', label: 'Team Overview' },
    { value: 'players', label: 'Player Analysis' },
    { value: 'league', label: 'League Comparison' },
    { value: 'projections', label: 'Projections' },
  ];

  const playerOptions = [
    { value: 'josh-allen', label: 'Josh Allen (QB)' },
    { value: 'christian-mccaffrey', label: 'Christian McCaffrey (RB)' },
    { value: 'stefon-diggs', label: 'Stefon Diggs (WR)' },
    { value: 'travis-kelce', label: 'Travis Kelce (TE)' },
  ];

  const timeRangeOptions = [
    { value: 'season', label: 'Full Season' },
    { value: 'last-4', label: 'Last 4 Weeks' },
    { value: 'last-6', label: 'Last 6 Weeks' },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Analytics</h1>
          <p className="text-gray-600">Deep dive into your team's performance</p>
        </div>
        
        <div className="flex items-center space-x-3">
          <Select
            options={viewOptions}
            value={selectedView}
            onChange={(value) => setSelectedView(value as string)}
            className="min-w-[160px]"
          />
          <Select
            options={timeRangeOptions}
            value={timeRange}
            onChange={(value) => setTimeRange(value as string)}
            className="min-w-[140px]"
          />
        </div>
      </div>

      {/* Overview Tab */}
      {selectedView === 'overview' && (
        <div className="space-y-6">
          {/* Quick Stats */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center space-x-2">
                  <TrendingUp className="w-5 h-5 text-green-600" />
                  <div>
                    <div className="text-2xl font-bold text-gray-900">1,024.2</div>
                    <div className="text-sm text-gray-600">Total Points</div>
                  </div>
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center space-x-2">
                  <Target className="w-5 h-5 text-blue-600" />
                  <div>
                    <div className="text-2xl font-bold text-gray-900">3rd</div>
                    <div className="text-sm text-gray-600">League Rank</div>
                  </div>
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center space-x-2">
                  <Users className="w-5 h-5 text-purple-600" />
                  <div>
                    <div className="text-2xl font-bold text-gray-900">75.4%</div>
                    <div className="text-sm text-gray-600">Playoff Chance</div>
                  </div>
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center space-x-2">
                  <Calendar className="w-5 h-5 text-yellow-600" />
                  <div>
                    <div className="text-2xl font-bold text-gray-900">5-3</div>
                    <div className="text-sm text-gray-600">W-L Record</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Team Analytics */}
          <TeamAnalyticsWidget 
            analytics={mockTeamAnalytics}
            teamName="Your Team"
          />
        </div>
      )}

      {/* Player Analysis Tab */}
      {selectedView === 'players' && (
        <div className="space-y-6">
          <div className="flex items-center space-x-4">
            <Select
              options={playerOptions}
              value={selectedPlayer}
              onChange={(value) => setSelectedPlayer(value as string)}
              className="min-w-[200px]"
            />
            <Badge variant="default" size="sm">
              {timeRange === 'season' ? 'Full Season' : 
               timeRange === 'last-4' ? 'Last 4 Weeks' : 'Last 6 Weeks'}
            </Badge>
          </div>

          <PlayerPerformanceChart
            playerName="Josh Allen"
            position="QB"
            team="BUF"
            performances={mockPlayerPerformances}
          />
        </div>
      )}

      {/* League Comparison Tab */}
      {selectedView === 'league' && (
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <BarChart3 className="w-5 h-5" />
                <span>League Standings</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Chart
                data={leagueStatsData}
                type="bar"
                height={400}
                width={800}
                showGrid={true}
                showLabels={true}
                title=""
                className="border-0 p-0"
              />
            </CardContent>
          </Card>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Position vs League Average</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {[
                    { pos: 'QB', yourAvg: 19.5, leagueAvg: 17.8, rank: 3 },
                    { pos: 'RB', yourAvg: 24.2, leagueAvg: 22.1, rank: 2 },
                    { pos: 'WR', yourAvg: 18.7, leagueAvg: 19.3, rank: 6 },
                    { pos: 'TE', yourAvg: 9.8, leagueAvg: 11.2, rank: 8 },
                  ].map((pos) => (
                    <div key={pos.pos} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                      <div className="flex items-center space-x-3">
                        <Badge variant="secondary" size="sm">{pos.pos}</Badge>
                        <span className="text-sm font-medium">#{pos.rank} in league</span>
                      </div>
                      <div className="text-right">
                        <div className="text-sm font-bold">{pos.yourAvg.toFixed(1)} vs {pos.leagueAvg.toFixed(1)}</div>
                        <div className={`text-xs ${pos.yourAvg > pos.leagueAvg ? 'text-green-600' : 'text-red-600'}`}>
                          {pos.yourAvg > pos.leagueAvg ? '+' : ''}{(pos.yourAvg - pos.leagueAvg).toFixed(1)}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Strengths & Weaknesses</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <h4 className="font-medium text-green-700 mb-2">🔥 Strengths</h4>
                    <ul className="space-y-1 text-sm text-gray-600">
                      <li>• Elite QB production (19.5 ppg, #3 in league)</li>
                      <li>• Strong RB depth (24.2 ppg, #2 in league)</li>
                      <li>• Consistent weekly output</li>
                    </ul>
                  </div>
                  
                  <div>
                    <h4 className="font-medium text-red-700 mb-2">⚠️ Areas to Improve</h4>
                    <ul className="space-y-1 text-sm text-gray-600">
                      <li>• WR production below league average</li>
                      <li>• TE position needs upgrade</li>
                      <li>• Inconsistent kicker performance</li>
                    </ul>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      )}

      {/* Projections Tab */}
      {selectedView === 'projections' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Season Projection</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="text-center">
                    <div className="text-3xl font-bold text-blue-600">11-6</div>
                    <div className="text-sm text-gray-600">Projected Final Record</div>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4 text-center">
                    <div>
                      <div className="text-xl font-bold text-green-600">75.4%</div>
                      <div className="text-xs text-gray-600">Playoff Chance</div>
                    </div>
                    <div>
                      <div className="text-xl font-bold text-yellow-600">12.8%</div>
                      <div className="text-xs text-gray-600">Championship</div>
                    </div>
                  </div>
                  
                  <div className="bg-gray-50 p-3 rounded">
                    <div className="text-sm font-medium mb-2">Most Likely Outcomes:</div>
                    <div className="space-y-1 text-xs text-gray-600">
                      <div>• 3rd place finish (32.1% chance)</div>
                      <div>• 2nd place finish (24.7% chance)</div>
                      <div>• 4th place finish (18.6% chance)</div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Remaining Schedule</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {[
                    { week: 9, opponent: 'Team Kappa', difficulty: 'Easy', winChance: 78 },
                    { week: 10, opponent: 'Team Lambda', difficulty: 'Medium', winChance: 62 },
                    { week: 11, opponent: 'Team Mu', difficulty: 'Hard', winChance: 35 },
                    { week: 12, opponent: 'Team Nu', difficulty: 'Medium', winChance: 58 },
                    { week: 13, opponent: 'Team Xi', difficulty: 'Easy', winChance: 72 },
                  ].map((game) => (
                    <div key={game.week} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                      <div className="flex items-center space-x-3">
                        <span className="text-sm font-medium">Week {game.week}</span>
                        <span className="text-sm text-gray-600">{game.opponent}</span>
                        <Badge 
                          variant={
                            game.difficulty === 'Easy' ? 'success' :
                            game.difficulty === 'Medium' ? 'warning' : 'error'
                          }
                          size="sm"
                        >
                          {game.difficulty}
                        </Badge>
                      </div>
                      <div className="text-sm font-medium text-gray-900">
                        {game.winChance}% win
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}
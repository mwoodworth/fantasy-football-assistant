import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { Table } from '../components/common/Table';
import { Select } from '../components/common/Select';
import { Users, Trophy, TrendingUp, Settings, Star, ArrowUpDown } from 'lucide-react';

// Mock team data
const mockTeams = [
  {
    id: 1,
    name: 'Thunder Bolts',
    league: 'Championship League',
    record: '8-5',
    points: 1247.8,
    rank: 2,
    playoffs: true,
    active: true
  },
  {
    id: 2,
    name: 'Fantasy Kings',
    league: 'Friends League',
    record: '6-7',
    points: 1189.3,
    rank: 7,
    playoffs: false,
    active: true
  }
];

const mockRoster = [
  { id: 1, name: 'Josh Allen', position: 'QB', team: 'BUF', status: 'starter', points: 287.4 },
  { id: 2, name: 'Christian McCaffrey', position: 'RB', team: 'SF', status: 'starter', points: 234.7 },
  { id: 3, name: 'Stefon Diggs', position: 'WR', team: 'BUF', status: 'starter', points: 198.3 },
  { id: 4, name: 'Travis Kelce', position: 'TE', team: 'KC', status: 'starter', points: 156.8 },
  { id: 5, name: 'Dak Prescott', position: 'QB', team: 'DAL', status: 'bench', points: 145.2 },
  { id: 6, name: 'Tony Pollard', position: 'RB', team: 'DAL', status: 'bench', points: 134.9 },
];

export function TeamsPage() {
  const [selectedTeam, setSelectedTeam] = useState('1');
  const [selectedView, setSelectedView] = useState('roster');

  const teamOptions = mockTeams.map(team => ({
    value: team.id.toString(),
    label: `${team.name} (${team.league})`
  }));

  const viewOptions = [
    { value: 'roster', label: 'Current Roster' },
    { value: 'lineup', label: 'Set Lineup' },
    { value: 'trades', label: 'Trade Center' },
    { value: 'waivers', label: 'Waivers' }
  ];

  const currentTeam = mockTeams.find(team => team.id.toString() === selectedTeam);

  const rosterColumns = [
    {
      key: 'name',
      header: 'Player',
      accessor: 'name' as keyof typeof mockRoster[0],
      sortable: true,
      render: (value: string, row: any) => (
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
      accessor: 'status' as keyof typeof mockRoster[0],
      render: (value: string) => (
        <Badge variant={value === 'starter' ? 'success' : 'secondary'} size="sm">
          {value === 'starter' ? 'Starting' : 'Bench'}
        </Badge>
      )
    },
    {
      key: 'points',
      header: 'Points',
      accessor: 'points' as keyof typeof mockRoster[0],
      sortable: true,
      align: 'right' as const,
      render: (value: number) => (
        <span className="font-mono">{value.toFixed(1)}</span>
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
            className="min-w-[200px]"
          />
          <Button size="sm" variant="outline">
            <Settings className="w-4 h-4 mr-2" />
            Settings
          </Button>
        </div>
      </div>

      {/* Team Overview */}
      {currentTeam && (
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
            <Table
              data={mockRoster}
              columns={rosterColumns}
              sortable={true}
              hoverable={true}
            />
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
              <Button>
                Launch Lineup Optimizer
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {selectedView === 'trades' && (
        <Card>
          <CardHeader>
            <CardTitle>Trade Center</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-center py-12 text-gray-500">
              <ArrowUpDown className="w-12 h-12 mx-auto mb-4 text-gray-300" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">Trade Analyzer</h3>
              <p className="text-gray-600 mb-4">
                Evaluate trade proposals and find optimal trading partners.
              </p>
              <Button>
                Open Trade Analyzer
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {selectedView === 'waivers' && (
        <Card>
          <CardHeader>
            <CardTitle>Waiver Wire</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-center py-12 text-gray-500">
              <Star className="w-12 h-12 mx-auto mb-4 text-gray-300" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">Waiver Targets</h3>
              <p className="text-gray-600 mb-4">
                Find the best available players and set your waiver claims.
              </p>
              <Button>
                View Waiver Targets
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
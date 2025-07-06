import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { PlayerPerformanceChart } from '../components/analytics/PlayerPerformanceChart';
import { Chart } from '../components/analytics/Chart';
import { Card, CardContent, CardHeader, CardTitle } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { Modal, ModalBody } from '../components/common/Modal';
import { 
  ArrowLeft, 
  TrendingUp, 
 
  Target, 
  Calendar, 
  MapPin,
  DollarSign,
  Users,
  Activity,
  AlertCircle,
  Star,
  Plus,
  BarChart3
} from 'lucide-react';
import { cn } from '../utils/cn';

// Mock player data for demonstration
const mockPlayerData = {
  id: 1,
  name: 'Josh Allen',
  position: 'QB',
  team: 'BUF',
  jersey: 17,
  age: 27,
  height: '6\'5"',
  weight: 237,
  college: 'Wyoming',
  experience: 6,
  salary: 43000000,
  ownership: 98.2,
  adp: 1.2,
  injuryStatus: 'Healthy',
  nextOpponent: 'MIA',
  nextGameTime: 'Sunday 1:00 PM ET',
  byeWeek: 13,
  stats: {
    passingYards: 2876,
    passingTDs: 21,
    interceptions: 12,
    rushingYards: 387,
    rushingTDs: 8,
    completionPercentage: 65.4,
    qbr: 67.8
  },
  projections: {
    season: { points: 312.4, rank: 3 },
    nextWeek: { points: 22.1, floor: 16.8, ceiling: 28.7 },
    playoffs: { points: 89.3, rank: 2 }
  },
  news: [
    {
      title: 'Allen throws for 4 TDs in win over Dolphins',
      source: 'ESPN',
      time: '2 hours ago',
      impact: 'positive'
    },
    {
      title: 'Bills offense clicking on all cylinders',
      source: 'NFL.com',
      time: '1 day ago',
      impact: 'positive'
    },
    {
      title: 'Weather concerns for Sunday\'s game',
      source: 'Yahoo Sports',
      time: '2 days ago',
      impact: 'neutral'
    }
  ],
  similarPlayers: [
    { name: 'Lamar Jackson', position: 'QB', team: 'BAL', similarity: 87 },
    { name: 'Kyler Murray', position: 'QB', team: 'ARI', similarity: 82 },
    { name: 'Jalen Hurts', position: 'QB', team: 'PHI', similarity: 79 }
  ]
};

const mockPerformances = [
  { week: 1, points: 18.4, projected: 16.2, opponent: 'DAL', gameResult: 'win' as const },
  { week: 2, points: 24.7, projected: 18.1, opponent: 'NYG', gameResult: 'win' as const },
  { week: 3, points: 12.3, projected: 19.5, opponent: 'SF', gameResult: 'loss' as const },
  { week: 4, points: 31.2, projected: 17.8, opponent: 'MIA', gameResult: 'win' as const },
  { week: 5, points: 16.8, projected: 20.1, opponent: 'BUF', gameResult: 'loss' as const },
  { week: 6, points: 22.5, projected: 18.9, opponent: 'WAS', gameResult: 'win' as const },
  { week: 7, points: 19.7, projected: 17.4, opponent: 'PHI', gameResult: 'win' as const },
  { week: 8, points: 14.2, projected: 19.8, opponent: 'DEN', gameResult: 'loss' as const },
];

const mockMatchupData = [
  { label: 'vs DAL', value: 18.4, color: '#10B981' },
  { label: 'vs NYG', value: 24.7, color: '#10B981' },
  { label: 'vs SF', value: 12.3, color: '#EF4444' },
  { label: 'vs MIA', value: 31.2, color: '#10B981' },
  { label: 'vs BUF', value: 16.8, color: '#EF4444' },
  { label: 'vs WAS', value: 22.5, color: '#10B981' },
  { label: 'vs PHI', value: 19.7, color: '#10B981' },
  { label: 'vs DEN', value: 14.2, color: '#EF4444' },
];

export function PlayerDetailPage() {
  const { playerId: _playerId } = useParams<{ playerId: string }>();
  const navigate = useNavigate();
  const [selectedTab, setSelectedTab] = useState('overview');
  const [showCompareModal, setShowCompareModal] = useState(false);
  const [isWatchlisted, setIsWatchlisted] = useState(false);

  // In a real app, this would fetch player data from the API
  // const { data: player, isLoading, error } = useQuery({
  //   queryKey: ['player', playerId],
  //   queryFn: () => PlayerService.getPlayer(Number(playerId)),
  // });

  const player = mockPlayerData; // Using mock data for demo
  const isLoading = false;
  const error = null;

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-48 mb-4"></div>
          <div className="h-32 bg-gray-200 rounded mb-6"></div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="h-64 bg-gray-200 rounded"></div>
            <div className="h-64 bg-gray-200 rounded"></div>
            <div className="h-64 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error || !player) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Player not found</h3>
          <p className="text-gray-600 mb-4">The player you're looking for doesn't exist.</p>
          <Button onClick={() => navigate('/players')}>
            Back to Players
          </Button>
        </div>
      </div>
    );
  }

  const tabs = [
    { key: 'overview', label: 'Overview', icon: Activity },
    { key: 'performance', label: 'Performance', icon: TrendingUp },
    { key: 'matchups', label: 'Matchups', icon: Target },
    { key: 'news', label: 'News', icon: AlertCircle },
  ];

  const getInjuryStatusColor = () => {
    switch (player.injuryStatus) {
      case 'Healthy':
        return 'bg-green-100 text-green-800';
      case 'Questionable':
        return 'bg-yellow-100 text-yellow-800';
      case 'Doubtful':
        return 'bg-orange-100 text-orange-800';
      case 'Out':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="space-y-6">
      {/* Back Button */}
      <Button
        variant="ghost"
        size="sm"
        onClick={() => navigate('/players')}
        className="mb-4"
      >
        <ArrowLeft className="w-4 h-4 mr-2" />
        Back to Players
      </Button>

      {/* Player Header */}
      <Card>
        <CardContent className="p-6">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between">
            <div className="flex items-start space-x-4">
              {/* Player Avatar/Jersey */}
              <div className="w-16 h-16 bg-gray-100 rounded-lg flex items-center justify-center">
                <span className="text-2xl font-bold text-gray-600">#{player.jersey}</span>
              </div>
              
              <div className="flex-1">
                <div className="flex items-center space-x-3 mb-2">
                  <h1 className="text-2xl font-bold text-gray-900">{player.name}</h1>
                  <Badge className="bg-blue-100 text-blue-800">{player.position}</Badge>
                  <Badge className="bg-gray-100 text-gray-800">{player.team}</Badge>
                  <Badge className={getInjuryStatusColor()}>{player.injuryStatus}</Badge>
                </div>
                
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm text-gray-600">
                  <div>Age: {player.age}</div>
                  <div>Height: {player.height}</div>
                  <div>Weight: {player.weight} lbs</div>
                  <div>Experience: {player.experience} years</div>
                </div>
                
                <div className="flex items-center space-x-4 mt-3 text-sm text-gray-600">
                  <div className="flex items-center space-x-1">
                    <MapPin className="w-4 h-4" />
                    <span>{player.college}</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <DollarSign className="w-4 h-4" />
                    <span>${(player.salary / 1000000).toFixed(1)}M</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <Users className="w-4 h-4" />
                    <span>{player.ownership}% owned</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex items-center space-x-3 mt-4 md:mt-0">
              <Button
                variant={isWatchlisted ? 'primary' : 'outline'}
                size="sm"
                onClick={() => setIsWatchlisted(!isWatchlisted)}
              >
                <Star className={cn('w-4 h-4 mr-2', isWatchlisted && 'fill-current')} />
                {isWatchlisted ? 'Watchlisted' : 'Add to Watchlist'}
              </Button>
              
              <Button variant="outline" size="sm" onClick={() => setShowCompareModal(true)}>
                <BarChart3 className="w-4 h-4 mr-2" />
                Compare
              </Button>
              
              <Button size="sm">
                <Plus className="w-4 h-4 mr-2" />
                Add to Team
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Next Game Info */}
      <Card className="bg-gradient-to-r from-blue-50 to-purple-50 border-blue-200">
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Calendar className="w-5 h-5 text-blue-600" />
              <div>
                <div className="font-medium text-gray-900">Next Game: vs {player.nextOpponent}</div>
                <div className="text-sm text-gray-600">{player.nextGameTime}</div>
              </div>
            </div>
            <div className="text-right">
              <div className="text-lg font-bold text-blue-600">{player.projections.nextWeek.points} pts</div>
              <div className="text-sm text-gray-600">projected</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-8">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.key}
                onClick={() => setSelectedTab(tab.key)}
                className={cn(
                  'flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm',
                  selectedTab === tab.key
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                )}
              >
                <Icon className="w-4 h-4" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Tab Content */}
      {selectedTab === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Season Stats */}
          <Card>
            <CardHeader>
              <CardTitle>Season Stats</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex justify-between">
                  <span className="text-gray-600">Passing Yards</span>
                  <span className="font-medium">{player.stats.passingYards.toLocaleString()}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Passing TDs</span>
                  <span className="font-medium">{player.stats.passingTDs}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Interceptions</span>
                  <span className="font-medium">{player.stats.interceptions}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Rushing Yards</span>
                  <span className="font-medium">{player.stats.rushingYards}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Rushing TDs</span>
                  <span className="font-medium">{player.stats.rushingTDs}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Completion %</span>
                  <span className="font-medium">{player.stats.completionPercentage}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">QBR</span>
                  <span className="font-medium">{player.stats.qbr}</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Projections */}
          <Card>
            <CardHeader>
              <CardTitle>Projections</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                <div>
                  <h4 className="font-medium text-gray-900 mb-3">Season</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Total Points</span>
                      <span className="font-medium">{player.projections.season.points}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Rank</span>
                      <span className="font-medium">#{player.projections.season.rank}</span>
                    </div>
                  </div>
                </div>
                
                <div>
                  <h4 className="font-medium text-gray-900 mb-3">Next Week</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Projection</span>
                      <span className="font-medium">{player.projections.nextWeek.points}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Floor</span>
                      <span className="font-medium text-red-600">{player.projections.nextWeek.floor}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Ceiling</span>
                      <span className="font-medium text-green-600">{player.projections.nextWeek.ceiling}</span>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Similar Players */}
          <Card>
            <CardHeader>
              <CardTitle>Similar Players</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {player.similarPlayers.map((similar, i) => (
                  <div key={i} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                    <div>
                      <div className="font-medium text-sm">{similar.name}</div>
                      <div className="text-xs text-gray-600">{similar.position} - {similar.team}</div>
                    </div>
                    <div className="text-sm font-medium text-blue-600">
                      {similar.similarity}% similar
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {selectedTab === 'performance' && (
        <PlayerPerformanceChart
          playerName={player.name}
          position={player.position}
          team={player.team}
          performances={mockPerformances}
        />
      )}

      {selectedTab === 'matchups' && (
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Matchup Performance</CardTitle>
            </CardHeader>
            <CardContent>
              <Chart
                data={mockMatchupData}
                type="bar"
                height={300}
                width={800}
                showGrid={true}
                showLabels={true}
                className="border-0 p-0"
              />
            </CardContent>
          </Card>
        </div>
      )}

      {selectedTab === 'news' && (
        <Card>
          <CardHeader>
            <CardTitle>Recent News</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {player.news.map((article, i) => (
                <div key={i} className="border-l-4 border-blue-500 pl-4">
                  <h4 className="font-medium text-gray-900">{article.title}</h4>
                  <div className="flex items-center space-x-2 mt-1">
                    <span className="text-sm text-gray-600">{article.source}</span>
                    <span className="text-gray-300">•</span>
                    <span className="text-sm text-gray-600">{article.time}</span>
                    <Badge 
                      variant={
                        article.impact === 'positive' ? 'success' :
                        article.impact === 'negative' ? 'error' : 'secondary'
                      }
                      size="sm"
                    >
                      {article.impact}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Compare Modal */}
      <Modal
        isOpen={showCompareModal}
        onClose={() => setShowCompareModal(false)}
        title="Compare Players"
        size="lg"
      >
        <ModalBody>
          <p className="text-gray-600">Player comparison feature coming soon...</p>
        </ModalBody>
      </Modal>
    </div>
  );
}
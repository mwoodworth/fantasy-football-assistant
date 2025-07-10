import { useState } from 'react';
import { X, TrendingUp, TrendingDown, Activity, Target, Shield, Heart, Info, ChevronLeft, ChevronRight } from 'lucide-react';
import type { Player } from '../../types/player';
import { Modal, ModalBody } from '../common/Modal';
import { Button } from '../common/Button';
import { Badge } from '../common/Badge';
import { Card, CardContent, CardHeader, CardTitle } from '../common/Card';
import { Sparkline } from '../common/Sparkline';
import { cn } from '../../utils/cn';

interface PlayerDetailsModalProps {
  player: Player | null;
  isOpen: boolean;
  onClose: () => void;
  onNext?: () => void;
  onPrevious?: () => void;
  hasNext?: boolean;
  hasPrevious?: boolean;
}

const POSITION_COLORS = {
  QB: 'bg-red-100 text-red-800',
  RB: 'bg-green-100 text-green-800',
  WR: 'bg-blue-100 text-blue-800',
  TE: 'bg-yellow-100 text-yellow-800',
  K: 'bg-purple-100 text-purple-800',
  DEF: 'bg-gray-100 text-gray-800',
};

const INJURY_STATUS_COLORS = {
  'Healthy': 'bg-green-100 text-green-800',
  'Questionable': 'bg-yellow-100 text-yellow-800',
  'Doubtful': 'bg-orange-100 text-orange-800',
  'Out': 'bg-red-100 text-red-800',
  'IR': 'bg-red-100 text-red-800',
  'Q': 'bg-yellow-100 text-yellow-800',
  'D': 'bg-orange-100 text-orange-800',
  'O': 'bg-red-100 text-red-800',
  'PUP': 'bg-gray-100 text-gray-800',
};

export function PlayerDetailsModal({ 
  player, 
  isOpen, 
  onClose,
  onNext,
  onPrevious,
  hasNext,
  hasPrevious
}: PlayerDetailsModalProps) {
  const [activeTab, setActiveTab] = useState<'overview' | 'stats' | 'trends' | 'news'>('overview');

  if (!player) return null;

  const getPerformanceTrend = () => {
    if (!player.points_last_3_weeks || player.points_last_3_weeks.length < 2) return null;
    const recent = player.points_last_3_weeks[player.points_last_3_weeks.length - 1];
    const previous = player.points_last_3_weeks[player.points_last_3_weeks.length - 2];
    
    if (recent > previous * 1.1) return 'up';
    if (recent < previous * 0.9) return 'down';
    return 'stable';
  };

  const performanceTrend = getPerformanceTrend();

  return (
    <Modal 
      isOpen={isOpen} 
      onClose={onClose}
      title={player.name}
      size="xl"
    >
      <ModalBody>
      {/* Player Header Info */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <Badge className={POSITION_COLORS[player.position as keyof typeof POSITION_COLORS] || 'bg-gray-100 text-gray-800'}>
            {player.position}
          </Badge>
          <span className="text-gray-600">{player.team}</span>
          {player.bye_week && (
            <span className="text-sm text-gray-500">BYE: {player.bye_week}</span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {hasPrevious && (
            <Button
              size="sm"
              variant="outline"
              onClick={onPrevious}
              className="p-1"
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
          )}
          {hasNext && (
            <Button
              size="sm"
              variant="outline"
              onClick={onNext}
              className="p-1"
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
          )}
        </div>
      </div>

      {/* Injury Status Alert */}
      {player.injury_status && player.injury_status !== 'Healthy' && (
        <div className={cn(
          "mb-4 p-3 rounded-lg flex items-center gap-2",
          player.injury_status === 'Out' || player.injury_status === 'O' ? 'bg-red-50' :
          player.injury_status === 'Doubtful' || player.injury_status === 'D' ? 'bg-orange-50' :
          'bg-yellow-50'
        )}>
          <Info className="h-4 w-4" />
          <span className="font-medium">Injury Status:</span>
          <Badge className={INJURY_STATUS_COLORS[player.injury_status as keyof typeof INJURY_STATUS_COLORS]}>
            {player.injury_status}
          </Badge>
          {player.injury_notes && (
            <span className="text-sm text-gray-600 ml-2">{player.injury_notes}</span>
          )}
        </div>
      )}

      {/* Tab Navigation */}
      <div className="flex gap-2 mb-6 border-b">
        {(['overview', 'stats', 'trends', 'news'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={cn(
              "px-4 py-2 font-medium text-sm capitalize transition-colors border-b-2 -mb-px",
              activeTab === tab
                ? "text-primary-600 border-primary-600"
                : "text-gray-600 border-transparent hover:text-gray-900"
            )}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="space-y-6">
        {activeTab === 'overview' && (
          <>
            {/* Key Metrics */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {player.projected_points && (
                <Card>
                  <CardContent className="p-4">
                    <div className="text-sm text-gray-600 mb-1">Projected Points</div>
                    <div className="text-2xl font-bold text-gray-900">
                      {player.projected_points.toFixed(1)}
                    </div>
                  </CardContent>
                </Card>
              )}
              
              {player.average_points_last_3 && (
                <Card>
                  <CardContent className="p-4">
                    <div className="text-sm text-gray-600 mb-1">L3 Average</div>
                    <div className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                      {player.average_points_last_3.toFixed(1)}
                      {performanceTrend === 'up' && <TrendingUp className="h-4 w-4 text-green-500" />}
                      {performanceTrend === 'down' && <TrendingDown className="h-4 w-4 text-red-500" />}
                      {performanceTrend === 'stable' && <Activity className="h-4 w-4 text-gray-500" />}
                    </div>
                  </CardContent>
                </Card>
              )}
              
              {player.consistency_rating && (
                <Card>
                  <CardContent className="p-4">
                    <div className="text-sm text-gray-600 mb-1">Consistency</div>
                    <div className="text-2xl font-bold text-gray-900">
                      {player.consistency_rating}%
                    </div>
                    <div className="mt-1">
                      <div className="w-full h-2 bg-gray-200 rounded-full">
                        <div 
                          className="h-full bg-blue-500 rounded-full"
                          style={{ width: `${player.consistency_rating}%` }}
                        />
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}
              
              {player.matchup_rating && (
                <Card>
                  <CardContent className="p-4">
                    <div className="text-sm text-gray-600 mb-1">Matchup Rating</div>
                    <div className="text-2xl font-bold text-gray-900">
                      {player.matchup_rating}/10
                    </div>
                    <div className="flex items-center gap-1 mt-1">
                      {[...Array(5)].map((_, i) => (
                        <div
                          key={i}
                          className={cn(
                            "w-3 h-3 rounded-full",
                            i < Math.ceil(player.matchup_rating / 2)
                              ? player.matchup_rating >= 8 ? "bg-green-500" 
                                : player.matchup_rating >= 5 ? "bg-yellow-500" 
                                : "bg-red-500"
                              : "bg-gray-300"
                          )}
                        />
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>

            {/* Fantasy Relevance */}
            <Card>
              <CardHeader>
                <CardTitle>Fantasy Relevance</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {player.ownership_percentage !== undefined && (
                    <div>
                      <div className="text-sm text-gray-600">Ownership</div>
                      <div className="text-lg font-semibold">{player.ownership_percentage}%</div>
                    </div>
                  )}
                  {player.start_percentage !== undefined && (
                    <div>
                      <div className="text-sm text-gray-600">Start %</div>
                      <div className="text-lg font-semibold">{player.start_percentage}%</div>
                    </div>
                  )}
                  {player.boom_bust_rating && (
                    <div>
                      <div className="text-sm text-gray-600">Profile</div>
                      <Badge variant="outline" className="mt-1">{player.boom_bust_rating}</Badge>
                    </div>
                  )}
                  {player.trade_value !== undefined && (
                    <div>
                      <div className="text-sm text-gray-600">Trade Value</div>
                      <div className="text-lg font-semibold">{player.trade_value}</div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Season Outlook */}
            {player.season_outlook && (
              <Card>
                <CardHeader>
                  <CardTitle>Season Outlook</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-gray-700">{player.season_outlook}</p>
                </CardContent>
              </Card>
            )}
          </>
        )}

        {activeTab === 'stats' && (
          <>
            {/* Projected Stats */}
            {player.projected_stats && (
              <Card>
                <CardHeader>
                  <CardTitle>Projected Stats</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                    {Object.entries(player.projected_stats).map(([key, value]) => (
                      <div key={key}>
                        <div className="text-sm text-gray-600 capitalize">
                          {key.replace(/_/g, ' ')}
                        </div>
                        <div className="text-lg font-semibold">{value}</div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Advanced Metrics */}
            <Card>
              <CardHeader>
                <CardTitle>Advanced Metrics</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  {player.target_share !== undefined && (
                    <div>
                      <div className="text-sm text-gray-600">Target Share</div>
                      <div className="text-lg font-semibold">{player.target_share}%</div>
                    </div>
                  )}
                  {player.red_zone_touches !== undefined && (
                    <div>
                      <div className="text-sm text-gray-600">RZ Touches</div>
                      <div className="text-lg font-semibold">{player.red_zone_touches}</div>
                    </div>
                  )}
                  {player.snap_count_percentage !== undefined && (
                    <div>
                      <div className="text-sm text-gray-600">Snap %</div>
                      <div className="text-lg font-semibold">{player.snap_count_percentage}%</div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </>
        )}

        {activeTab === 'trends' && (
          <>
            {/* Performance Chart */}
            {player.points_last_3_weeks && player.points_last_3_weeks.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Recent Performance</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">Last 3 Weeks Trend</span>
                      <Sparkline 
                        data={player.points_last_3_weeks} 
                        width={200} 
                        height={50}
                        showDots
                      />
                    </div>
                    <div className="grid grid-cols-3 gap-4 mt-4">
                      {player.points_last_3_weeks.map((points, index) => (
                        <div key={index} className="text-center">
                          <div className="text-sm text-gray-600">
                            Week {17 - (player.points_last_3_weeks!.length - 1 - index)}
                          </div>
                          <div className="text-lg font-semibold">{points.toFixed(1)} pts</div>
                        </div>
                      ))}
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Trend Analysis */}
            <Card>
              <CardHeader>
                <CardTitle>Trend Analysis</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-gray-600">Overall Trend</span>
                    <div className="flex items-center gap-2">
                      {performanceTrend === 'up' && (
                        <>
                          <TrendingUp className="h-5 w-5 text-green-500" />
                          <span className="text-green-600 font-medium">Trending Up</span>
                        </>
                      )}
                      {performanceTrend === 'down' && (
                        <>
                          <TrendingDown className="h-5 w-5 text-red-500" />
                          <span className="text-red-600 font-medium">Trending Down</span>
                        </>
                      )}
                      {performanceTrend === 'stable' && (
                        <>
                          <Activity className="h-5 w-5 text-gray-500" />
                          <span className="text-gray-600 font-medium">Stable</span>
                        </>
                      )}
                    </div>
                  </div>
                  
                  {player.waiver_priority && (
                    <div className="flex items-center justify-between">
                      <span className="text-gray-600">Waiver Priority</span>
                      <Badge variant={player.waiver_priority <= 3 ? 'default' : 'secondary'}>
                        #{player.waiver_priority}
                      </Badge>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </>
        )}

        {activeTab === 'news' && (
          <>
            {/* Latest News */}
            {player.latest_news ? (
              <Card>
                <CardHeader>
                  <CardTitle>Latest News</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div>
                      <div className="flex items-start justify-between mb-2">
                        <h4 className="font-medium text-gray-900">{player.latest_news.headline}</h4>
                        <Badge 
                          variant={
                            player.latest_news.impact === 'positive' ? 'success' :
                            player.latest_news.impact === 'negative' ? 'destructive' :
                            'secondary'
                          }
                          className="ml-2"
                        >
                          {player.latest_news.impact}
                        </Badge>
                      </div>
                      <p className="text-sm text-gray-600 mb-2">{player.latest_news.summary}</p>
                      <p className="text-xs text-gray-500">
                        {new Date(player.latest_news.date).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ) : (
              <Card>
                <CardContent className="py-12 text-center">
                  <p className="text-gray-500">No recent news available</p>
                </CardContent>
              </Card>
            )}

            {/* Matchup Info */}
            {(player.opponent_rank || player.weather_impact) && (
              <Card>
                <CardHeader>
                  <CardTitle>Matchup Information</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {player.opponent_rank && (
                      <div className="flex items-center justify-between">
                        <span className="text-gray-600">Opponent Rank vs {player.position}</span>
                        <Badge 
                          variant={
                            player.opponent_rank <= 10 ? 'success' :
                            player.opponent_rank <= 20 ? 'secondary' :
                            'destructive'
                          }
                        >
                          #{player.opponent_rank}
                        </Badge>
                      </div>
                    )}
                    {player.weather_impact && (
                      <div className="flex items-center justify-between">
                        <span className="text-gray-600">Weather Impact</span>
                        <span className="text-sm">{player.weather_impact}</span>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            )}
          </>
        )}
      </div>

      {/* Action Buttons */}
      <div className="flex justify-end gap-3 mt-6 pt-4 border-t">
        <Button variant="outline" onClick={onClose}>
          Close
        </Button>
        <Button variant="primary">
          Add to Watchlist
        </Button>
      </div>
      </ModalBody>
    </Modal>
  );
}
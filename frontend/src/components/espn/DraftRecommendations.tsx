import { Star, TrendingUp, Clock, Target } from 'lucide-react';
import { type DraftRecommendation, type PlayerRecommendation } from '../../services/espn';
import { Card } from '../common/Card';
import { Badge } from '../common/Badge';
import { Button } from '../common/Button';

interface DraftRecommendationsProps {
  recommendations: DraftRecommendation;
  isUserTurn: boolean;
  onSelectPlayer: (player: PlayerRecommendation) => void;
}

export function DraftRecommendations({ 
  recommendations, 
  isUserTurn, 
  onSelectPlayer 
}: DraftRecommendationsProps) {
  
  const getPositionColor = (position: string) => {
    const colors: Record<string, string> = {
      'QB': 'bg-red-100 text-red-800',
      'RB': 'bg-green-100 text-green-800',
      'WR': 'bg-blue-100 text-blue-800',
      'TE': 'bg-yellow-100 text-yellow-800',
      'K': 'bg-gray-100 text-gray-800',
      'DEF': 'bg-purple-100 text-purple-800',
    };
    return colors[position] || 'bg-gray-100 text-gray-800';
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600';
    if (confidence >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="space-y-6">
      {/* AI Strategy Summary */}
      <Card className="bg-blue-50 border-blue-200 p-4">
        <div className="flex items-start gap-3">
          <Target className="h-5 w-5 text-blue-600 mt-0.5" />
          <div className="flex-1">
            <h3 className="font-medium text-blue-900 mb-2">
              Pick #{recommendations.pick_number} Strategy
            </h3>
            <p className="text-blue-800 text-sm mb-3">
              {recommendations.strategy_reasoning}
            </p>
            
            {recommendations.ai_insights.length > 0 && (
              <div className="space-y-1">
                <p className="text-xs font-medium text-blue-900">Key Insights:</p>
                <ul className="text-xs text-blue-800 space-y-1">
                  {recommendations.ai_insights.map((insight, index) => (
                    <li key={index} className="flex items-start gap-1">
                      <span className="text-blue-600">•</span>
                      <span>{insight}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
            
            <div className="flex items-center gap-2 mt-3">
              <span className="text-xs text-blue-700">Confidence:</span>
              <span className={`text-xs font-medium ${getConfidenceColor(recommendations.confidence_score)}`}>
                {Math.round(recommendations.confidence_score * 100)}%
              </span>
            </div>
          </div>
        </div>
      </Card>

      {/* Top Recommendation */}
      <Card className="border-green-200 p-4">
        <div className="flex items-center gap-2 mb-3">
          <Star className="h-4 w-4 text-yellow-500 fill-current" />
          <span className="font-medium text-green-900">Top Recommendation</span>
        </div>
        
        <div className="flex items-center justify-between mb-3">
          <div>
            <h3 className="font-semibold text-lg">{recommendations.primary_recommendation.name}</h3>
            <div className="flex items-center gap-2 mt-1">
              <Badge className={getPositionColor(recommendations.primary_recommendation.position)}>
                {recommendations.primary_recommendation.position}
              </Badge>
              <span className="text-sm text-gray-600">{recommendations.primary_recommendation.team}</span>
            </div>
          </div>
          <div className="text-right">
            <div className="text-lg font-bold text-green-600">
              {recommendations.primary_recommendation.score.toFixed(1)}
            </div>
            <div className="text-xs text-gray-500">Score</div>
          </div>
        </div>

        <p className="text-sm text-gray-700 mb-3">
          {recommendations.primary_recommendation.reasoning}
        </p>

        {recommendations.primary_recommendation.projected_points && (
          <div className="grid grid-cols-3 gap-4 text-center text-sm bg-gray-50 rounded p-3">
            <div>
              <div className="font-medium">{recommendations.primary_recommendation.projected_points.toFixed(1)}</div>
              <div className="text-xs text-gray-500">Proj. Points</div>
            </div>
            {recommendations.primary_recommendation.vor && (
              <div>
                <div className="font-medium">{recommendations.primary_recommendation.vor.toFixed(1)}</div>
                <div className="text-xs text-gray-500">VOR</div>
              </div>
            )}
            {recommendations.primary_recommendation.adp && (
              <div>
                <div className="font-medium">{recommendations.primary_recommendation.adp.toFixed(1)}</div>
                <div className="text-xs text-gray-500">ADP</div>
              </div>
            )}
          </div>
        )}

        {isUserTurn && (
          <Button 
            className="w-full mt-4 bg-green-600 hover:bg-green-700"
            onClick={() => onSelectPlayer(recommendations.primary_recommendation)}
          >
            Select This Player
          </Button>
        )}
      </Card>

      {/* Alternative Options */}
      <div>
        <h3 className="font-medium mb-3 flex items-center gap-2">
          <TrendingUp className="h-4 w-4" />
          Alternative Options
        </h3>
        
        <div className="space-y-3">
          {recommendations.recommended_players.slice(1, 6).map((player) => (
            <Card key={player.player_id} className="p-3 hover:bg-gray-50 transition-colors">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-medium">{player.name}</span>
                    <Badge className={getPositionColor(player.position)} size="sm">
                      {player.position}
                    </Badge>
                    <span className="text-sm text-gray-500">{player.team}</span>
                  </div>
                  <p className="text-xs text-gray-600">{player.reasoning}</p>
                </div>
                
                <div className="text-right ml-4">
                  <div className="font-medium text-blue-600">
                    {player.score.toFixed(1)}
                  </div>
                  {isUserTurn && (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => onSelectPlayer(player)}
                      className="mt-1"
                    >
                      Select
                    </Button>
                  )}
                </div>
              </div>
            </Card>
          ))}
        </div>
      </div>

      {/* Next Pick Strategy */}
      {recommendations.next_pick_strategy && (
        <Card className="bg-gray-50 p-4">
          <div className="flex items-start gap-3">
            <Clock className="h-4 w-4 text-gray-600 mt-0.5" />
            <div>
              <h4 className="font-medium text-gray-900 mb-1">Next Pick Strategy</h4>
              <p className="text-sm text-gray-700">{recommendations.next_pick_strategy}</p>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}
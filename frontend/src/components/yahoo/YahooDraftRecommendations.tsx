import React, { useState, useEffect } from 'react';
import { Brain, TrendingUp, AlertTriangle, Target, RefreshCw, Loader2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../common/Card';
import { Button } from '../common/Button';
import { Badge } from '../common/Badge';
import { Alert } from '../common/Alert';
import { yahooService } from '../../services/yahoo';
import type { YahooDraftRecommendation } from '../../services/yahooTypes';

interface YahooDraftRecommendationsProps {
  sessionId: number;
  currentPick: number;
  isUserTurn: boolean;
}

export const YahooDraftRecommendations: React.FC<YahooDraftRecommendationsProps> = ({
  sessionId,
  currentPick,
  isUserTurn
}) => {
  const [recommendations, setRecommendations] = useState<YahooDraftRecommendation | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastLoadedPick, setLastLoadedPick] = useState<number | null>(null);

  useEffect(() => {
    // Load recommendations when it's user's turn or pick changes
    if (isUserTurn || (currentPick !== lastLoadedPick && currentPick > 0)) {
      loadRecommendations();
    }
  }, [currentPick, isUserTurn]);

  const loadRecommendations = async (forceRefresh = false) => {
    try {
      setLoading(true);
      setError(null);
      
      const data = await yahooService.getDraftRecommendations(sessionId, forceRefresh);
      setRecommendations(data);
      setLastLoadedPick(currentPick);
    } catch (err) {
      console.error('Failed to load recommendations:', err);
      setError('Failed to load recommendations');
    } finally {
      setLoading(false);
    }
  };

  const getPositionColor = (position: string) => {
    const colors: Record<string, string> = {
      QB: 'bg-red-100 text-red-800',
      RB: 'bg-green-100 text-green-800',
      WR: 'bg-blue-100 text-blue-800',
      TE: 'bg-purple-100 text-purple-800',
      K: 'bg-orange-100 text-orange-800',
      DEF: 'bg-gray-100 text-gray-800'
    };
    return colors[position] || 'bg-gray-100 text-gray-800';
  };

  const getConfidenceLabel = (score: number) => {
    if (score >= 0.8) return { label: 'High', color: 'success' };
    if (score >= 0.6) return { label: 'Medium', color: 'warning' };
    return { label: 'Low', color: 'secondary' };
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex justify-between items-center">
          <CardTitle className="flex items-center gap-2">
            <Brain className="w-5 h-5" />
            AI Recommendations
          </CardTitle>
          <Button
            size="sm"
            variant="outline"
            onClick={() => loadRecommendations(true)}
            disabled={loading}
          >
            {loading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <RefreshCw className="w-4 h-4" />
            )}
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {loading && !recommendations ? (
          <div className="py-8 text-center">
            <Loader2 className="w-8 h-8 animate-spin mx-auto mb-2 text-primary" />
            <p className="text-sm text-muted-foreground">Analyzing available players...</p>
          </div>
        ) : error ? (
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <div>{error}</div>
          </Alert>
        ) : recommendations ? (
          <>
            {/* Confidence score */}
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Confidence</span>
              <Badge variant={getConfidenceLabel(recommendations.confidence_score).color as any}>
                {getConfidenceLabel(recommendations.confidence_score).label}
              </Badge>
            </div>

            {/* Primary recommendation */}
            {recommendations.primary && (
              <div className="border rounded-lg p-4 bg-primary-light">
                <h4 className="font-semibold mb-2 flex items-center gap-2">
                  <Target className="w-4 h-4" />
                  Top Pick
                </h4>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">{recommendations.primary.name}</p>
                    <p className="text-sm text-muted-foreground">
                      {recommendations.primary.team} • 
                      <Badge className={`ml-2 ${getPositionColor(recommendations.primary.position)}`}>
                        {recommendations.primary.position}
                      </Badge>
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium">{recommendations.primary.points.total} pts</p>
                    <p className="text-xs text-muted-foreground">projected</p>
                  </div>
                </div>
              </div>
            )}

            {/* AI insights */}
            {recommendations.ai_insights && (
              <div className="border-t pt-4">
                <p className="text-sm text-muted-foreground italic">
                  "{recommendations.ai_insights}"
                </p>
              </div>
            )}

            {/* Value picks */}
            {recommendations.value_picks.length > 0 && (
              <div className="border-t pt-4">
                <h4 className="font-semibold mb-3 flex items-center gap-2">
                  <TrendingUp className="w-4 h-4" />
                  Best Value
                </h4>
                <div className="space-y-2">
                  {recommendations.value_picks.slice(0, 3).map((player, index) => (
                    <div key={index} className="flex items-center justify-between text-sm">
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{player.name}</span>
                        <Badge className={getPositionColor(player.position)}>
                          {player.position}
                        </Badge>
                      </div>
                      <span className="text-muted-foreground">
                        {player.points.total} pts
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Positional needs */}
            {Object.keys(recommendations.positional_needs).length > 0 && (
              <div className="border-t pt-4">
                <h4 className="font-semibold mb-3">Position Needs</h4>
                <div className="grid grid-cols-3 gap-2">
                  {Object.entries(recommendations.positional_needs)
                    .sort(([, a], [, b]) => b - a)
                    .slice(0, 6)
                    .map(([position, need]) => (
                      <div
                        key={position}
                        className={`text-center py-1 px-2 rounded text-xs ${
                          need > 0.7 ? 'bg-red-100 text-red-800' :
                          need > 0.4 ? 'bg-yellow-100 text-yellow-800' :
                          'bg-green-100 text-green-800'
                        }`}
                      >
                        {position}
                      </div>
                    ))}
                </div>
              </div>
            )}

            {/* Players to avoid */}
            {recommendations.avoid_players.length > 0 && (
              <div className="border-t pt-4">
                <h4 className="font-semibold mb-3 flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-red-600" />
                  Avoid
                </h4>
                <div className="space-y-1">
                  {recommendations.avoid_players.slice(0, 2).map((player, index) => (
                    <p key={index} className="text-sm text-muted-foreground">
                      {player.name} ({player.position})
                    </p>
                  ))}
                </div>
              </div>
            )}
          </>
        ) : (
          <div className="py-8 text-center text-muted-foreground">
            <Brain className="w-8 h-8 mx-auto mb-2 opacity-20" />
            <p className="text-sm">Recommendations will appear when available</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
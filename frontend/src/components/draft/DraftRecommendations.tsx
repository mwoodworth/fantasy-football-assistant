import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { TrendingUp, Brain, AlertCircle, Target, Star } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '../common/Card'
import { Badge } from '../common/Badge'
import { Alert, AlertDescription } from '../common/Alert'
import { Progress } from '../common/Progress'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../common/Tabs'
import { cn } from '../../utils/cn'
import { espnApi } from '../../api/espn'

interface Player {
  player_id: number
  name: string
  position: string
  team: string
  projected_points: number
  vor: number
  recommendation_score: number
  tier: number
  adp: number
  reasoning: string
}

interface AIAnalysis {
  overall_strategy: string
  confidence: number
  key_insights: string[]
  next_pick_strategy: string
}

interface PositionalNeed {
  position: string
  filled: number
  required: number
  need_level: number
}

interface DraftRecommendation {
  recommendations: Player[]
  ai_analysis: AIAnalysis
  positional_needs?: PositionalNeed[]
  context: {
    pick_number: number
    round: number
    next_user_pick?: number
    picks_until_turn?: number
  }
}

interface DraftRecommendationsProps {
  sessionId: number
  onSelectPlayer?: (player: Player) => void
}

export function DraftRecommendations({ sessionId, onSelectPlayer }: DraftRecommendationsProps) {
  const { data: recommendation, isLoading, error, refetch } = useQuery<DraftRecommendation>({
    queryKey: ['draft-recommendations', sessionId],
    queryFn: async () => {
      const response = await espnApi.get(`/draft/${sessionId}/recommendations`)
      return response.data
    },
    refetchInterval: 30000, // Refresh every 30 seconds
    enabled: true,
  })

  if (isLoading) {
    return (
      <Card>
        <CardContent className="p-8">
          <div className="flex items-center justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          Failed to load recommendations. {error instanceof Error ? error.message : 'Unknown error'}
        </AlertDescription>
      </Alert>
    )
  }

  if (!recommendation) {
    return null
  }

  const getPositionColor = (position: string) => {
    switch (position) {
      case 'QB':
        return 'bg-red-100 text-red-800'
      case 'RB':
        return 'bg-green-100 text-green-800'
      case 'WR':
        return 'bg-blue-100 text-blue-800'
      case 'TE':
        return 'bg-purple-100 text-purple-800'
      case 'K':
        return 'bg-orange-100 text-orange-800'
      case 'DEF':
        return 'bg-gray-100 text-gray-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getTierColor = (tier: number) => {
    switch (tier) {
      case 1:
        return 'text-yellow-600'
      case 2:
        return 'text-gray-600'
      case 3:
        return 'text-orange-600'
      default:
        return 'text-gray-400'
    }
  }

  return (
    <div className="space-y-4">
      {/* AI Strategy Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="h-5 w-5 text-purple-600" />
            AI Draft Strategy
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* Overall Strategy */}
            <div>
              <p className="text-sm text-gray-900 leading-relaxed">
                {recommendation.ai_analysis.overall_strategy}
              </p>
              <div className="flex items-center gap-2 mt-2">
                <span className="text-xs text-gray-500">Confidence:</span>
                <Progress 
                  value={recommendation.ai_analysis.confidence * 100} 
                  className="h-2 w-24"
                />
                <span className="text-xs text-gray-600">
                  {Math.round(recommendation.ai_analysis.confidence * 100)}%
                </span>
              </div>
            </div>

            {/* Key Insights */}
            {recommendation.ai_analysis.key_insights.length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-2">Key Insights</h4>
                <ul className="space-y-1">
                  {recommendation.ai_analysis.key_insights.map((insight, index) => (
                    <li key={index} className="flex items-start gap-2">
                      <Target className="h-3 w-3 text-blue-600 mt-0.5 flex-shrink-0" />
                      <span className="text-sm text-gray-600">{insight}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Next Pick Strategy */}
            {recommendation.ai_analysis.next_pick_strategy && (
              <div className="pt-2 border-t">
                <p className="text-sm text-gray-600">
                  <span className="font-medium">Next Pick Strategy:</span>{' '}
                  {recommendation.ai_analysis.next_pick_strategy}
                </p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Recommendations Card */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-green-600" />
              Top Recommendations
            </CardTitle>
            <Badge variant="secondary">
              Pick #{recommendation.context.pick_number} • Round {recommendation.context.round}
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="recommendations">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="recommendations">Player Rankings</TabsTrigger>
              <TabsTrigger value="needs">Positional Needs</TabsTrigger>
            </TabsList>

            <TabsContent value="recommendations" className="mt-4">
              <div className="space-y-2">
                {recommendation.recommendations.map((player, index) => (
                  <button
                    key={player.player_id}
                    onClick={() => onSelectPlayer?.(player)}
                    className={cn(
                      "w-full p-3 rounded-lg border transition-all",
                      "hover:bg-gray-50 hover:border-gray-300",
                      index === 0 && "border-green-500 bg-green-50"
                    )}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1 text-left">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-semibold text-gray-900">
                            {index + 1}. {player.name}
                          </span>
                          <Badge variant="secondary" className={getPositionColor(player.position)}>
                            {player.position}
                          </Badge>
                          <span className="text-sm text-gray-500">{player.team}</span>
                          {player.tier <= 3 && (
                            <Star className={cn("h-4 w-4", getTierColor(player.tier))} />
                          )}
                        </div>
                        <div className="flex items-center gap-4 text-xs text-gray-600">
                          <span>Proj: {player.projected_points.toFixed(1)} pts</span>
                          <span>VOR: +{player.vor.toFixed(1)}</span>
                          <span>ADP: {player.adp.toFixed(1)}</span>
                          <span className="font-medium text-green-600">
                            Score: {player.recommendation_score.toFixed(1)}
                          </span>
                        </div>
                        <p className="text-xs text-gray-500 mt-1">{player.reasoning}</p>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </TabsContent>

            <TabsContent value="needs" className="mt-4">
              {recommendation.positional_needs && recommendation.positional_needs.length > 0 ? (
                <div className="space-y-3">
                  {recommendation.positional_needs.map((need) => (
                    <div key={need.position} className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <Badge className={getPositionColor(need.position)}>
                          {need.position}
                        </Badge>
                        <span className="text-sm text-gray-600">
                          {need.filled}/{need.required} filled
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Progress 
                          value={(1 - need.need_level) * 100} 
                          className="h-2 w-24"
                        />
                        <span className={cn(
                          "text-xs font-medium",
                          need.need_level > 0.7 ? "text-red-600" : 
                          need.need_level > 0.3 ? "text-yellow-600" : 
                          "text-green-600"
                        )}>
                          {need.need_level > 0.7 ? "High" : 
                           need.need_level > 0.3 ? "Medium" : 
                           "Low"} Need
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-center text-gray-500 py-4">
                  No positional needs data available
                </p>
              )}
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  )
}
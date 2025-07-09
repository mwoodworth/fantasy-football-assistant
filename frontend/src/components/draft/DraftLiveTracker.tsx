import React, { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Clock, Users, AlertCircle, TrendingUp } from 'lucide-react'
import { Alert, AlertDescription } from '../common/Alert'
import { Card, CardContent, CardHeader, CardTitle } from '../common/Card'
import { Badge } from '../common/Badge'
import { Progress } from '../common/Progress'
import { espnApi } from '../../api/espn'

interface DraftLiveStatus {
  session_id: number
  draft_status: string
  current_pick: number
  current_round: number
  current_pick_team_id: number | null
  is_user_turn: boolean
  recent_picks: Array<{
    player_id: number
    player_name: string
    position: string
    team: string
    pick_number: number
    drafted_by_user: boolean
  }>
  next_pick_info: {
    next_user_pick: number
    picks_until_turn: number
    estimated_time: number
  } | null
  last_sync: string | null
  sync_errors: string[]
}

interface DraftLiveTrackerProps {
  sessionId: number
  onUserTurn?: () => void
}

export function DraftLiveTracker({ sessionId, onUserTurn }: DraftLiveTrackerProps) {
  const [lastUserTurn, setLastUserTurn] = useState(false)
  const [timeUntilPick, setTimeUntilPick] = useState<number | null>(null)

  // Poll for draft updates every 5 seconds
  const { data: liveStatus, isError, error } = useQuery<DraftLiveStatus>({
    queryKey: ['draft-live-status', sessionId],
    queryFn: async () => {
      const response = await espnApi.get(`/draft/${sessionId}/live-status`)
      return response.data
    },
    refetchInterval: 5000, // Poll every 5 seconds
    enabled: true,
  })

  // Handle user turn notification
  useEffect(() => {
    if (liveStatus?.is_user_turn && !lastUserTurn) {
      onUserTurn?.()
      // Play notification sound if available
      const audio = new Audio('/sounds/your-turn.mp3')
      audio.play().catch(() => {
        // Ignore audio play errors
      })
    }
    setLastUserTurn(liveStatus?.is_user_turn || false)
  }, [liveStatus?.is_user_turn, lastUserTurn, onUserTurn])

  // Update countdown timer
  useEffect(() => {
    if (liveStatus?.next_pick_info?.estimated_time) {
      const interval = setInterval(() => {
        setTimeUntilPick((prev) => {
          if (prev === null || prev <= 0) return null
          return prev - 1
        })
      }, 1000)

      setTimeUntilPick(liveStatus.next_pick_info.estimated_time)

      return () => clearInterval(interval)
    }
  }, [liveStatus?.next_pick_info?.estimated_time])

  if (isError) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          Error loading draft status: {error instanceof Error ? error.message : 'Unknown error'}
        </AlertDescription>
      </Alert>
    )
  }

  if (!liveStatus) {
    return (
      <div className="flex items-center justify-center p-4">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
      </div>
    )
  }

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  const getDraftStatusColor = (status: string) => {
    switch (status) {
      case 'in_progress':
        return 'bg-green-500'
      case 'paused':
        return 'bg-yellow-500'
      case 'completed':
        return 'bg-gray-500'
      default:
        return 'bg-blue-500'
    }
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

  return (
    <div className="space-y-4">
      {/* Draft Status Header */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg">Live Draft Status</CardTitle>
            <Badge className={`${getDraftStatusColor(liveStatus.draft_status)} text-white`}>
              {liveStatus.draft_status.replace('_', ' ').toUpperCase()}
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <p className="text-sm text-gray-600">Current Pick</p>
              <p className="text-2xl font-bold">{liveStatus.current_pick}</p>
            </div>
            <div className="text-center">
              <p className="text-sm text-gray-600">Round</p>
              <p className="text-2xl font-bold">{liveStatus.current_round}</p>
            </div>
            <div className="text-center">
              <p className="text-sm text-gray-600">Your Next Pick</p>
              <p className="text-2xl font-bold">
                {liveStatus.next_pick_info?.next_user_pick || '-'}
              </p>
            </div>
            <div className="text-center">
              <p className="text-sm text-gray-600">Picks Until Turn</p>
              <p className="text-2xl font-bold">
                {liveStatus.next_pick_info?.picks_until_turn || '-'}
              </p>
            </div>
          </div>

          {/* Progress to next pick */}
          {liveStatus.next_pick_info && liveStatus.next_pick_info.picks_until_turn > 0 && (
            <div className="mt-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-600">Progress to your pick</span>
                <span className="text-sm font-medium">
                  {timeUntilPick !== null ? formatTime(timeUntilPick) : '-'}
                </span>
              </div>
              <Progress
                value={
                  ((liveStatus.next_pick_info.next_user_pick - liveStatus.current_pick) /
                    liveStatus.next_pick_info.picks_until_turn) *
                  100
                }
                className="h-2"
              />
            </div>
          )}

          {/* User turn alert */}
          {liveStatus.is_user_turn && (
            <Alert className="mt-4 border-green-500 bg-green-50">
              <AlertCircle className="h-4 w-4 text-green-600" />
              <AlertDescription className="text-green-800 font-medium">
                It's your turn to pick!
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Recent Picks */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Clock className="h-5 w-5" />
            Recent Picks
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {liveStatus.recent_picks.length === 0 ? (
              <p className="text-sm text-gray-500 text-center py-4">
                No picks made yet
              </p>
            ) : (
              liveStatus.recent_picks.map((pick) => (
                <div
                  key={pick.pick_number}
                  className={`flex items-center justify-between p-2 rounded-lg ${
                    pick.drafted_by_user ? 'bg-blue-50 border border-blue-200' : 'bg-gray-50'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <span className="text-sm font-medium text-gray-600">
                      #{pick.pick_number}
                    </span>
                    <div>
                      <p className="font-medium">{pick.player_name}</p>
                      <div className="flex items-center gap-2 mt-1">
                        <Badge variant="secondary" className={getPositionColor(pick.position)}>
                          {pick.position}
                        </Badge>
                        <span className="text-xs text-gray-600">{pick.team}</span>
                      </div>
                    </div>
                  </div>
                  {pick.drafted_by_user && (
                    <Badge variant="default" className="bg-blue-600">
                      Your Pick
                    </Badge>
                  )}
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>

      {/* Sync Status */}
      {liveStatus.sync_errors.length > 0 && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Sync errors: {liveStatus.sync_errors.join(', ')}
          </AlertDescription>
        </Alert>
      )}

      {liveStatus.last_sync && (
        <p className="text-xs text-gray-500 text-center">
          Last synced: {new Date(liveStatus.last_sync).toLocaleTimeString()}
        </p>
      )}
    </div>
  )
}
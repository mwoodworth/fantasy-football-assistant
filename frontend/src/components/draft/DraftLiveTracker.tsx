import React, { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Clock, Users, AlertCircle, TrendingUp, Wifi } from 'lucide-react'
import { Alert, AlertDescription } from '../common/Alert'
import { Card, CardContent, CardHeader, CardTitle } from '../common/Card'
import { Badge } from '../common/Badge'
import { Progress } from '../common/Progress'
import { espnApi } from '../../api/espn'
// import { useWebSocket } from '../../hooks/useWebSocket' // Temporarily disabled until socket.io-client is installed

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
  const [liveData, setLiveData] = useState<Partial<DraftLiveStatus>>({})

  // Poll for initial data and as fallback
  const { data: liveStatus, isError, error, refetch } = useQuery<DraftLiveStatus>({
    queryKey: ['draft-live-status', sessionId],
    queryFn: async () => {
      const response = await espnApi.get(`/draft/${sessionId}/live-status`)
      return response.data
    },
    refetchInterval: 5000, // Poll every 5 seconds (WebSocket temporarily disabled)
    enabled: true,
  })

  // WebSocket connection for real-time updates
  // Temporarily disabled until socket.io-client is installed
  const isConnected = false
  /*
  const { isConnected } = useWebSocket({
    draftSessionId: sessionId,
    onPickMade: (data) => {
      console.log('Pick made via WebSocket:', data)
      // Update recent picks
      setLiveData(prev => ({
        ...prev,
        recent_picks: [
          ...(prev.recent_picks || []).slice(-9), // Keep last 9
          {
            player_id: data.player_id,
            player_name: data.player_name || 'Unknown Player',
            position: data.position || 'N/A',
            team: data.team || 'N/A',
            pick_number: data.pick_number,
            drafted_by_user: data.is_user_pick || false,
          }
        ],
        current_pick: data.pick_number + 1,
        current_round: data.round,
      }))
      // Refetch full data to sync
      refetch()
    },
    onUserOnClock: (data) => {
      console.log('User on clock via WebSocket:', data)
      setLiveData(prev => ({ ...prev, is_user_turn: true }))
      onUserTurn?.()
    },
    onStatusChange: (data) => {
      console.log('Draft status change via WebSocket:', data)
      setLiveData(prev => ({ ...prev, draft_status: data.status }))
      refetch()
    },
    onSyncError: (data) => {
      console.error('Sync error via WebSocket:', data)
    },
  })
  */

  // Merge polling data with WebSocket updates
  const mergedStatus = { ...liveStatus, ...liveData } as DraftLiveStatus

  // Handle user turn notification
  useEffect(() => {
    if (mergedStatus?.is_user_turn && !lastUserTurn) {
      onUserTurn?.()
      // Play notification sound if available
      const audio = new Audio('/sounds/your-turn.mp3')
      audio.play().catch(() => {
        // Ignore audio play errors
      })
    }
    setLastUserTurn(mergedStatus?.is_user_turn || false)
  }, [mergedStatus?.is_user_turn, lastUserTurn, onUserTurn])

  // Update countdown timer
  useEffect(() => {
    if (mergedStatus?.next_pick_info?.estimated_time) {
      const interval = setInterval(() => {
        setTimeUntilPick((prev) => {
          if (prev === null || prev <= 0) return null
          return prev - 1
        })
      }, 1000)

      setTimeUntilPick(mergedStatus.next_pick_info.estimated_time)

      return () => clearInterval(interval)
    }
  }, [mergedStatus?.next_pick_info?.estimated_time])

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

  if (!mergedStatus || !mergedStatus) {
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
            <CardTitle className="text-lg flex items-center gap-2">
              Live Draft Status
              {isConnected && (
                <Wifi className="h-4 w-4 text-green-600" title="Real-time updates active" />
              )}
            </CardTitle>
            <Badge className={`${getDraftStatusColor(mergedStatus.draft_status)} text-white`}>
              {mergedStatus.draft_status.replace('_', ' ').toUpperCase()}
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <p className="text-sm text-gray-600">Current Pick</p>
              <p className="text-2xl font-bold">{mergedStatus.current_pick}</p>
            </div>
            <div className="text-center">
              <p className="text-sm text-gray-600">Round</p>
              <p className="text-2xl font-bold">{mergedStatus.current_round}</p>
            </div>
            <div className="text-center">
              <p className="text-sm text-gray-600">Your Next Pick</p>
              <p className="text-2xl font-bold">
                {mergedStatus.next_pick_info?.next_user_pick || '-'}
              </p>
            </div>
            <div className="text-center">
              <p className="text-sm text-gray-600">Picks Until Turn</p>
              <p className="text-2xl font-bold">
                {mergedStatus.next_pick_info?.picks_until_turn || '-'}
              </p>
            </div>
          </div>

          {/* Progress to next pick */}
          {mergedStatus.next_pick_info && mergedStatus.next_pick_info.picks_until_turn > 0 && (
            <div className="mt-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-600">Progress to your pick</span>
                <span className="text-sm font-medium">
                  {timeUntilPick !== null ? formatTime(timeUntilPick) : '-'}
                </span>
              </div>
              <Progress
                value={
                  ((mergedStatus.next_pick_info.next_user_pick - mergedStatus.current_pick) /
                    mergedStatus.next_pick_info.picks_until_turn) *
                  100
                }
                className="h-2"
              />
            </div>
          )}

          {/* User turn alert */}
          {mergedStatus.is_user_turn && (
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
            {mergedStatus.recent_picks.length === 0 ? (
              <p className="text-sm text-gray-500 text-center py-4">
                No picks made yet
              </p>
            ) : (
              mergedStatus.recent_picks.map((pick) => (
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
      {mergedStatus.sync_errors.length > 0 && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Sync errors: {mergedStatus.sync_errors.join(', ')}
          </AlertDescription>
        </Alert>
      )}

      <div className="flex items-center justify-between text-xs text-gray-500">
        <span className="flex items-center gap-1">
          {isConnected ? (
            <>
              <Wifi className="h-3 w-3 text-green-600" />
              Real-time updates active
            </>
          ) : (
            <>
              <Wifi className="h-3 w-3 text-gray-400" />
              Connecting...
            </>
          )}
        </span>
        {mergedStatus.last_sync && (
          <span>
            Last synced: {new Date(mergedStatus.last_sync).toLocaleTimeString()}
          </span>
        )}
      </div>
    </div>
  )
}
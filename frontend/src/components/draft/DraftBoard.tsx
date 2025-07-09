import React, { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { Users, Play, Pause, RefreshCw, Wifi, WifiOff } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card'
import { Button } from '../ui/button'
import { Switch } from '../ui/switch'
import { Label } from '../ui/label'
import { Alert, AlertDescription } from '../ui/alert'
import { DraftLiveTracker } from './DraftLiveTracker'
import { espnApi } from '../../api/espn'

interface DraftSession {
  id: number
  session_token: string
  league_id: number
  current_pick: number
  current_round: number
  user_pick_position: number
  is_active: boolean
  is_live_synced: boolean
  next_user_pick: number
  picks_until_user_turn: number
  started_at: string
}

interface DraftBoardProps {
  sessionId?: number
  leagueId: number
}

export function DraftBoard({ sessionId: initialSessionId, leagueId }: DraftBoardProps) {
  const [activeSessionId, setActiveSessionId] = useState<number | null>(initialSessionId || null)
  const [showNotification, setShowNotification] = useState(false)
  const queryClient = useQueryClient()

  // Get or create draft session
  const { data: session, isLoading: sessionLoading } = useQuery<DraftSession>({
    queryKey: ['draft-session', leagueId],
    queryFn: async () => {
      if (activeSessionId) {
        const response = await espnApi.get(`/draft/session/${activeSessionId}`)
        return response.data
      }
      // Check for existing session
      const response = await espnApi.get(`/draft/sessions/active?league_id=${leagueId}`)
      if (response.data) {
        setActiveSessionId(response.data.id)
        return response.data
      }
      return null
    },
    enabled: true,
  })

  // Start draft session mutation
  const startDraftMutation = useMutation({
    mutationFn: async (draftPosition: number) => {
      const response = await espnApi.post('/draft/start', {
        league_id: leagueId,
        draft_position: draftPosition,
        live_sync: true,
      })
      return response.data
    },
    onSuccess: (data) => {
      setActiveSessionId(data.id)
      queryClient.invalidateQueries({ queryKey: ['draft-session', leagueId] })
      toast.success('Draft session started!')
    },
    onError: (error) => {
      toast.error('Failed to start draft session')
      console.error('Start draft error:', error)
    },
  })

  // Toggle sync mutation
  const toggleSyncMutation = useMutation({
    mutationFn: async ({ sessionId, enable }: { sessionId: number; enable: boolean }) => {
      const response = await espnApi.post(`/draft/${sessionId}/toggle-sync?enable=${enable}`)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['draft-session', leagueId] })
      queryClient.invalidateQueries({ queryKey: ['draft-live-status'] })
    },
  })

  // Handle user turn notification
  const handleUserTurn = () => {
    setShowNotification(true)
    // Show browser notification if permitted
    if ('Notification' in window && Notification.permission === 'granted') {
      new Notification('Your Turn to Draft!', {
        body: 'It\'s your turn to make a pick in the draft.',
        icon: '/logo192.png',
      })
    }
  }

  // Request notification permission on mount
  useEffect(() => {
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission()
    }
  }, [])

  if (sessionLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div>
      </div>
    )
  }

  // Show draft start screen if no active session
  if (!session) {
    return (
      <Card className="max-w-md mx-auto">
        <CardHeader>
          <CardTitle>Start Draft Session</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <Alert>
              <AlertDescription>
                Enter your draft position to start tracking the draft in real-time.
              </AlertDescription>
            </Alert>
            <div className="grid grid-cols-3 gap-2">
              {[...Array(12)].map((_, i) => (
                <Button
                  key={i + 1}
                  variant="outline"
                  onClick={() => startDraftMutation.mutate(i + 1)}
                  disabled={startDraftMutation.isPending}
                >
                  Position {i + 1}
                </Button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {/* Draft Controls */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Users className="h-5 w-5" />
              Draft Board
            </CardTitle>
            <div className="flex items-center gap-4">
              <div className="flex items-center space-x-2">
                <Switch
                  id="live-sync"
                  checked={session.is_live_synced}
                  onCheckedChange={(checked) =>
                    toggleSyncMutation.mutate({ sessionId: session.id, enable: checked })
                  }
                  disabled={toggleSyncMutation.isPending}
                />
                <Label htmlFor="live-sync" className="flex items-center gap-2 cursor-pointer">
                  {session.is_live_synced ? (
                    <>
                      <Wifi className="h-4 w-4 text-green-600" />
                      Live Sync On
                    </>
                  ) : (
                    <>
                      <WifiOff className="h-4 w-4 text-gray-400" />
                      Live Sync Off
                    </>
                  )}
                </Label>
              </div>
              <Button variant="outline" size="sm">
                <RefreshCw className="h-4 w-4 mr-2" />
                Manual Sync
              </Button>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Turn Notification */}
      {showNotification && (
        <Alert className="border-green-500 bg-green-50">
          <AlertDescription className="flex items-center justify-between">
            <span className="text-green-800 font-medium">
              🎯 It's your turn to draft! Make your pick.
            </span>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowNotification(false)}
            >
              Dismiss
            </Button>
          </AlertDescription>
        </Alert>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Live Tracker - Left Column */}
        <div className="lg:col-span-1">
          <DraftLiveTracker sessionId={session.id} onUserTurn={handleUserTurn} />
        </div>

        {/* Draft Board - Main Content */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle>Draft Progress</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-10 gap-1">
                {/* Draft grid will be implemented here */}
                <p className="col-span-10 text-center text-gray-500 py-8">
                  Draft board visualization coming soon...
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Player Rankings */}
          <Card className="mt-6">
            <CardHeader>
              <CardTitle>Available Players</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-center text-gray-500 py-8">
                Player rankings and recommendations coming soon...
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
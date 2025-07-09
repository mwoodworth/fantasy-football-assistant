import React from 'react'
import { cn } from '../../utils/cn'

interface DraftPick {
  player_id: number
  player_name: string
  position: string
  team: string
  pick_number: number
  round: number
  team_id: number
  drafted_by_user?: boolean
}

interface Team {
  id: number
  name: string
  abbreviation?: string
}

interface DraftBoardGridProps {
  picks: DraftPick[]
  teams: Team[]
  totalRounds: number
  currentPick: number
  userTeamId?: number
}

export function DraftBoardGrid({
  picks,
  teams,
  totalRounds,
  currentPick,
  userTeamId,
}: DraftBoardGridProps) {
  // Create a map of picks by round and team
  const pickMap = new Map<string, DraftPick>()
  picks.forEach((pick) => {
    const key = `${pick.round}-${pick.team_id}`
    pickMap.set(key, pick)
  })

  // Get position color
  const getPositionColor = (position: string) => {
    switch (position) {
      case 'QB':
        return 'bg-red-100 text-red-800 border-red-200'
      case 'RB':
        return 'bg-green-100 text-green-800 border-green-200'
      case 'WR':
        return 'bg-blue-100 text-blue-800 border-blue-200'
      case 'TE':
        return 'bg-purple-100 text-purple-800 border-purple-200'
      case 'K':
        return 'bg-orange-100 text-orange-800 border-orange-200'
      case 'D/ST':
      case 'DEF':
        return 'bg-gray-100 text-gray-800 border-gray-200'
      default:
        return 'bg-gray-50 text-gray-700 border-gray-200'
    }
  }

  // Calculate which pick number corresponds to each cell
  const getPickNumber = (round: number, teamIndex: number) => {
    // Snake draft logic
    if (round % 2 === 1) {
      // Odd rounds go left to right
      return (round - 1) * teams.length + teamIndex + 1
    } else {
      // Even rounds go right to left
      return (round - 1) * teams.length + (teams.length - teamIndex)
    }
  }

  return (
    <div className="overflow-x-auto">
      <div className="min-w-max">
        {/* Header row with team names */}
        <div className="grid grid-cols-[auto_repeat(var(--team-count),_1fr)] gap-1 mb-1" 
             style={{ '--team-count': teams.length } as React.CSSProperties}>
          <div className="w-12 h-10" /> {/* Empty corner cell */}
          {teams.map((team) => (
            <div
              key={team.id}
              className={cn(
                "text-center p-2 text-sm font-semibold truncate",
                "bg-gray-100 rounded-t",
                team.id === userTeamId && "bg-blue-100 text-blue-800"
              )}
              title={team.name}
            >
              {team.abbreviation || team.name.substring(0, 3).toUpperCase()}
            </div>
          ))}
        </div>

        {/* Rounds */}
        {Array.from({ length: totalRounds }, (_, roundIndex) => {
          const round = roundIndex + 1
          const isSnakeReverse = round % 2 === 0

          return (
            <div
              key={round}
              className="grid grid-cols-[auto_repeat(var(--team-count),_1fr)] gap-1 mb-1"
              style={{ '--team-count': teams.length } as React.CSSProperties}
            >
              {/* Round number */}
              <div className="w-12 h-20 flex items-center justify-center bg-gray-100 rounded-l text-sm font-semibold">
                R{round}
              </div>

              {/* Team picks for this round */}
              {teams.map((team, teamIndex) => {
                const pickNumber = getPickNumber(round, teamIndex)
                const pick = pickMap.get(`${round}-${team.id}`)
                const isCurrentPick = pickNumber === currentPick
                const isPastPick = pickNumber < currentPick
                const isUserPick = pick?.drafted_by_user || team.id === userTeamId

                return (
                  <div
                    key={`${round}-${team.id}`}
                    className={cn(
                      "relative h-20 p-1 rounded border-2 transition-all",
                      pick ? getPositionColor(pick.position) : "bg-gray-50 border-gray-200",
                      isCurrentPick && "ring-2 ring-yellow-400 border-yellow-400 animate-pulse",
                      isUserPick && pick && "ring-1 ring-blue-400",
                      !pick && isPastPick && "bg-gray-100",
                      !pick && !isPastPick && "bg-white hover:bg-gray-50"
                    )}
                  >
                    {/* Pick number indicator */}
                    <div className="absolute top-0 right-0 text-xs text-gray-500 px-1">
                      #{pickNumber}
                    </div>

                    {pick ? (
                      <div className="h-full flex flex-col justify-center">
                        <div className="text-xs font-semibold truncate" title={pick.player_name}>
                          {pick.player_name}
                        </div>
                        <div className="text-xs text-gray-600 flex items-center gap-1">
                          <span className="font-medium">{pick.position}</span>
                          <span className="text-gray-400">•</span>
                          <span className="truncate">{pick.team}</span>
                        </div>
                      </div>
                    ) : (
                      <div className="h-full flex items-center justify-center">
                        {isCurrentPick ? (
                          <div className="text-xs font-medium text-yellow-700">ON CLOCK</div>
                        ) : isPastPick ? (
                          <div className="text-xs text-gray-400">-</div>
                        ) : (
                          <div className="text-xs text-gray-400">{pickNumber}</div>
                        )}
                      </div>
                    )}

                    {/* Snake draft direction indicator */}
                    {teamIndex === 0 && !isSnakeReverse && (
                      <div className="absolute -left-6 top-1/2 -translate-y-1/2 text-gray-400">
                        →
                      </div>
                    )}
                    {teamIndex === teams.length - 1 && isSnakeReverse && (
                      <div className="absolute -right-6 top-1/2 -translate-y-1/2 text-gray-400">
                        ←
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          )
        })}

        {/* Legend */}
        <div className="mt-4 flex flex-wrap gap-4 text-xs">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-red-100 border border-red-200 rounded"></div>
            <span>QB</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-green-100 border border-green-200 rounded"></div>
            <span>RB</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-blue-100 border border-blue-200 rounded"></div>
            <span>WR</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-purple-100 border border-purple-200 rounded"></div>
            <span>TE</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-orange-100 border border-orange-200 rounded"></div>
            <span>K</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-gray-100 border border-gray-200 rounded"></div>
            <span>DEF</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 border-2 border-yellow-400 rounded"></div>
            <span>Current Pick</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 ring-1 ring-blue-400 rounded"></div>
            <span>Your Picks</span>
          </div>
        </div>
      </div>
    </div>
  )
}
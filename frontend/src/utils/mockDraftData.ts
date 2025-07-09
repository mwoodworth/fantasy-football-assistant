// Mock data generator for testing draft board visualization

export interface MockDraftPick {
  player_id: number
  player_name: string
  position: string
  team: string
  pick_number: number
  round: number
  team_id: number
  drafted_by_user?: boolean
}

export interface MockTeam {
  id: number
  name: string
  abbreviation?: string
}

const playerNames = [
  // QBs
  { name: "Patrick Mahomes", position: "QB", team: "KC" },
  { name: "Josh Allen", position: "QB", team: "BUF" },
  { name: "Lamar Jackson", position: "QB", team: "BAL" },
  { name: "Jalen Hurts", position: "QB", team: "PHI" },
  { name: "Joe Burrow", position: "QB", team: "CIN" },
  { name: "Justin Herbert", position: "QB", team: "LAC" },
  { name: "Dak Prescott", position: "QB", team: "DAL" },
  { name: "Tua Tagovailoa", position: "QB", team: "MIA" },
  
  // RBs
  { name: "Christian McCaffrey", position: "RB", team: "SF" },
  { name: "Austin Ekeler", position: "RB", team: "LAC" },
  { name: "Derrick Henry", position: "RB", team: "TEN" },
  { name: "Josh Jacobs", position: "RB", team: "LV" },
  { name: "Nick Chubb", position: "RB", team: "CLE" },
  { name: "Tony Pollard", position: "RB", team: "DAL" },
  { name: "Saquon Barkley", position: "RB", team: "NYG" },
  { name: "Jonathan Taylor", position: "RB", team: "IND" },
  { name: "Aaron Jones", position: "RB", team: "GB" },
  { name: "Najee Harris", position: "RB", team: "PIT" },
  { name: "Travis Etienne", position: "RB", team: "JAX" },
  { name: "Kenneth Walker", position: "RB", team: "SEA" },
  
  // WRs
  { name: "Tyreek Hill", position: "WR", team: "MIA" },
  { name: "Ja'Marr Chase", position: "WR", team: "CIN" },
  { name: "Justin Jefferson", position: "WR", team: "MIN" },
  { name: "Stefon Diggs", position: "WR", team: "BUF" },
  { name: "A.J. Brown", position: "WR", team: "PHI" },
  { name: "CeeDee Lamb", position: "WR", team: "DAL" },
  { name: "Davante Adams", position: "WR", team: "LV" },
  { name: "Cooper Kupp", position: "WR", team: "LAR" },
  { name: "Amon-Ra St. Brown", position: "WR", team: "DET" },
  { name: "Jaylen Waddle", position: "WR", team: "MIA" },
  { name: "DeVonta Smith", position: "WR", team: "PHI" },
  { name: "Chris Olave", position: "WR", team: "NO" },
  { name: "DK Metcalf", position: "WR", team: "SEA" },
  { name: "Calvin Ridley", position: "WR", team: "JAX" },
  { name: "Tee Higgins", position: "WR", team: "CIN" },
  
  // TEs
  { name: "Travis Kelce", position: "TE", team: "KC" },
  { name: "Mark Andrews", position: "TE", team: "BAL" },
  { name: "T.J. Hockenson", position: "TE", team: "MIN" },
  { name: "George Kittle", position: "TE", team: "SF" },
  { name: "Dallas Goedert", position: "TE", team: "PHI" },
  { name: "Darren Waller", position: "TE", team: "NYG" },
  
  // Kickers
  { name: "Justin Tucker", position: "K", team: "BAL" },
  { name: "Harrison Butker", position: "K", team: "KC" },
  { name: "Daniel Carlson", position: "K", team: "LV" },
  
  // Defense
  { name: "San Francisco", position: "DEF", team: "SF" },
  { name: "Buffalo", position: "DEF", team: "BUF" },
  { name: "Dallas", position: "DEF", team: "DAL" },
  { name: "Philadelphia", position: "DEF", team: "PHI" },
  { name: "New England", position: "DEF", team: "NE" },
]

export function generateMockTeams(count: number = 12): MockTeam[] {
  const teamNames = [
    { name: "Team Alpha", abbreviation: "ALP" },
    { name: "Team Bravo", abbreviation: "BRV" },
    { name: "Team Charlie", abbreviation: "CHA" },
    { name: "Team Delta", abbreviation: "DEL" },
    { name: "Team Echo", abbreviation: "ECH" },
    { name: "Team Foxtrot", abbreviation: "FOX" },
    { name: "Team Golf", abbreviation: "GLF" },
    { name: "Team Hotel", abbreviation: "HTL" },
    { name: "Team India", abbreviation: "IND" },
    { name: "Team Juliet", abbreviation: "JUL" },
    { name: "Team Kilo", abbreviation: "KIL" },
    { name: "Team Lima", abbreviation: "LIM" },
  ]
  
  return teamNames.slice(0, count).map((team, index) => ({
    id: index + 1,
    name: team.name,
    abbreviation: team.abbreviation,
  }))
}

export function generateMockDraftPicks(
  teams: MockTeam[],
  rounds: number = 5,
  currentPick: number = 25,
  userTeamId: number = 3
): MockDraftPick[] {
  const picks: MockDraftPick[] = []
  const usedPlayers = new Set<number>()
  
  // Calculate how many picks to generate (up to current pick)
  const totalPicksToGenerate = Math.min(currentPick - 1, teams.length * rounds)
  
  for (let pickNum = 1; pickNum <= totalPicksToGenerate; pickNum++) {
    // Calculate round and team for snake draft
    const round = Math.ceil(pickNum / teams.length)
    let teamIndex: number
    
    if (round % 2 === 1) {
      // Odd rounds: normal order (1, 2, 3, ...)
      teamIndex = (pickNum - 1) % teams.length
    } else {
      // Even rounds: reverse order (..., 3, 2, 1)
      teamIndex = teams.length - 1 - ((pickNum - 1) % teams.length)
    }
    
    // Find an unused player
    let playerIndex: number
    do {
      playerIndex = Math.floor(Math.random() * playerNames.length)
    } while (usedPlayers.has(playerIndex))
    
    usedPlayers.add(playerIndex)
    const player = playerNames[playerIndex]
    const team = teams[teamIndex]
    
    picks.push({
      player_id: 1000 + playerIndex,
      player_name: player.name,
      position: player.position,
      team: player.team,
      pick_number: pickNum,
      round: round,
      team_id: team.id,
      drafted_by_user: team.id === userTeamId,
    })
  }
  
  return picks
}

export function generateMockDraftSession(
  leagueId: number,
  teamCount: number = 12,
  userPosition: number = 3,
  currentPick: number = 25,
  totalRounds: number = 16
) {
  const teams = generateMockTeams(teamCount)
  const userTeamId = userPosition // Assuming team ID matches draft position
  const picks = generateMockDraftPicks(teams, totalRounds, currentPick, userTeamId)
  
  const currentRound = Math.ceil(currentPick / teamCount)
  const nextUserPick = calculateNextUserPick(currentPick, userPosition, teamCount, totalRounds)
  
  return {
    id: 1,
    session_token: "mock-session-token",
    league_id: leagueId,
    current_pick: currentPick,
    current_round: currentRound,
    user_pick_position: userPosition,
    is_active: true,
    is_live_synced: false,
    next_user_pick: nextUserPick,
    picks_until_user_turn: nextUserPick - currentPick,
    started_at: new Date().toISOString(),
    total_rounds: totalRounds,
    drafted_players: picks,
    teams,
    user_team_id: userTeamId,
  }
}

function calculateNextUserPick(
  currentPick: number,
  userPosition: number,
  teamCount: number,
  totalRounds: number
): number {
  for (let pick = currentPick; pick <= teamCount * totalRounds; pick++) {
    const round = Math.ceil(pick / teamCount)
    let teamIndex: number
    
    if (round % 2 === 1) {
      // Odd rounds: normal order
      teamIndex = (pick - 1) % teamCount + 1
    } else {
      // Even rounds: reverse order
      teamIndex = teamCount - ((pick - 1) % teamCount)
    }
    
    if (teamIndex === userPosition) {
      return pick
    }
  }
  
  return -1 // No more picks for user
}
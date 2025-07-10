import type { Player } from '../types/player';

// NFL Teams
const NFL_TEAMS = [
  'ARI', 'ATL', 'BAL', 'BUF', 'CAR', 'CHI', 'CIN', 'CLE',
  'DAL', 'DEN', 'DET', 'GB', 'HOU', 'IND', 'JAX', 'KC',
  'LAC', 'LAR', 'LV', 'MIA', 'MIN', 'NE', 'NO', 'NYG',
  'NYJ', 'PHI', 'PIT', 'SEA', 'SF', 'TB', 'TEN', 'WAS'
];

// Bye weeks by team (2024 example)
const BYE_WEEKS: Record<string, number> = {
  'ARI': 11, 'ATL': 12, 'BAL': 14, 'BUF': 12, 'CAR': 7, 'CHI': 7,
  'CIN': 12, 'CLE': 5, 'DAL': 7, 'DEN': 14, 'DET': 9, 'GB': 6,
  'HOU': 14, 'IND': 14, 'JAX': 12, 'KC': 6, 'LAC': 5, 'LAR': 10,
  'LV': 13, 'MIA': 6, 'MIN': 13, 'NE': 14, 'NO': 11, 'NYG': 11,
  'NYJ': 10, 'PHI': 5, 'PIT': 6, 'SEA': 10, 'SF': 9, 'TB': 5,
  'TEN': 7, 'WAS': 14
};

// Player name templates by position
const QB_NAMES = [
  'Patrick Mahomes', 'Josh Allen', 'Jalen Hurts', 'Lamar Jackson', 'Joe Burrow',
  'Justin Herbert', 'Dak Prescott', 'Tua Tagovailoa', 'Trevor Lawrence', 'Justin Fields',
  'Deshaun Watson', 'Kirk Cousins', 'Geno Smith', 'Jared Goff', 'Daniel Jones',
  'Russell Wilson', 'Aaron Rodgers', 'Derek Carr', 'Mac Jones', 'Kenny Pickett'
];

const RB_NAMES = [
  'Christian McCaffrey', 'Austin Ekeler', 'Nick Chubb', 'Derrick Henry', 'Saquon Barkley',
  'Josh Jacobs', 'Tony Pollard', 'Jonathan Taylor', 'Bijan Robinson', 'Jahmyr Gibbs',
  'Breece Hall', 'Kenneth Walker', 'Najee Harris', 'Aaron Jones', 'Travis Etienne',
  'Miles Sanders', 'Dameon Pierce', 'Rachaad White', 'Isiah Pacheco', 'James Cook',
  'Javonte Williams', 'Alexander Mattison', 'Brian Robinson', 'Zack Moss', 'Khalil Herbert'
];

const WR_NAMES = [
  'Tyreek Hill', 'Stefon Diggs', 'Justin Jefferson', 'Ja\'Marr Chase', 'CeeDee Lamb',
  'A.J. Brown', 'Davante Adams', 'Cooper Kupp', 'Amon-Ra St. Brown', 'Jaylen Waddle',
  'Chris Olave', 'DeVonta Smith', 'DK Metcalf', 'Calvin Ridley', 'Tee Higgins',
  'Amari Cooper', 'Mike Evans', 'Keenan Allen', 'Terry McLaurin', 'Tyler Lockett',
  'Christian Watson', 'Drake London', 'George Pickens', 'Diontae Johnson', 'Michael Pittman'
];

const TE_NAMES = [
  'Travis Kelce', 'Mark Andrews', 'T.J. Hockenson', 'George Kittle', 'Dallas Goedert',
  'Darren Waller', 'Kyle Pitts', 'Evan Engram', 'Cole Kmet', 'Pat Freiermuth',
  'David Njoku', 'Tyler Higbee', 'Dalton Schultz', 'Greg Dulcich', 'Chigoziem Okonkwo'
];

const K_NAMES = [
  'Justin Tucker', 'Daniel Carlson', 'Harrison Butker', 'Tyler Bass', 'Evan McPherson',
  'Jason Myers', 'Younghoe Koo', 'Jake Elliott', 'Graham Gano', 'Cameron Dicker'
];

const DEF_NAMES = [
  'San Francisco', 'Buffalo', 'Dallas', 'New England', 'Philadelphia',
  'Baltimore', 'New York Jets', 'Denver', 'Cleveland', 'Pittsburgh',
  'Kansas City', 'Miami', 'Cincinnati', 'Jacksonville', 'Seattle'
];

// Generate random stats based on position and tier
function generateStats(position: string, tier: number) {
  const variance = () => Math.random() * 0.4 - 0.2; // -20% to +20% variance
  
  switch (position) {
    case 'QB':
      const qbBase = tier === 1 ? 300 : tier === 2 ? 250 : 200;
      return {
        passing_yards: Math.round(qbBase * (1 + variance())),
        passing_tds: tier === 1 ? 2.5 : tier === 2 ? 1.8 : 1.2,
        rushing_yards: Math.round((tier === 1 ? 25 : 10) * (1 + variance())),
        rushing_tds: Math.random() > 0.7 ? 0.3 : 0
      };
      
    case 'RB':
      const rbBase = tier === 1 ? 80 : tier === 2 ? 60 : 40;
      return {
        rushing_yards: Math.round(rbBase * (1 + variance())),
        rushing_tds: tier === 1 ? 0.7 : tier === 2 ? 0.4 : 0.2,
        receptions: tier === 1 ? 4 : tier === 2 ? 2.5 : 1.5,
        receiving_yards: Math.round((tier === 1 ? 30 : 15) * (1 + variance())),
        receiving_tds: Math.random() > 0.8 ? 0.2 : 0,
        carries: Math.round((tier === 1 ? 18 : tier === 2 ? 12 : 8) * (1 + variance()))
      };
      
    case 'WR':
      const wrBase = tier === 1 ? 80 : tier === 2 ? 60 : 40;
      return {
        receptions: tier === 1 ? 6 : tier === 2 ? 4 : 2.5,
        receiving_yards: Math.round(wrBase * (1 + variance())),
        receiving_tds: tier === 1 ? 0.6 : tier === 2 ? 0.3 : 0.1,
        targets: Math.round((tier === 1 ? 9 : tier === 2 ? 6 : 4) * (1 + variance()))
      };
      
    case 'TE':
      const teBase = tier === 1 ? 60 : tier === 2 ? 40 : 25;
      return {
        receptions: tier === 1 ? 5 : tier === 2 ? 3 : 2,
        receiving_yards: Math.round(teBase * (1 + variance())),
        receiving_tds: tier === 1 ? 0.5 : tier === 2 ? 0.2 : 0.1,
        targets: Math.round((tier === 1 ? 7 : tier === 2 ? 5 : 3) * (1 + variance()))
      };
      
    default:
      return {};
  }
}

// Calculate fantasy points based on stats
function calculateFantasyPoints(stats: any, position: string, scoringType = 'half_ppr'): number {
  let points = 0;
  
  // Passing
  points += (stats.passing_yards || 0) * 0.04;
  points += (stats.passing_tds || 0) * 4;
  
  // Rushing
  points += (stats.rushing_yards || 0) * 0.1;
  points += (stats.rushing_tds || 0) * 6;
  
  // Receiving
  const receptionPoints = scoringType === 'ppr' ? 1 : scoringType === 'half_ppr' ? 0.5 : 0;
  points += (stats.receptions || 0) * receptionPoints;
  points += (stats.receiving_yards || 0) * 0.1;
  points += (stats.receiving_tds || 0) * 6;
  
  // Special positions
  if (position === 'K') {
    points = 7 + Math.random() * 6; // 7-13 points
  } else if (position === 'DEF') {
    points = 6 + Math.random() * 8; // 6-14 points
  }
  
  return Math.round(points * 10) / 10;
}

// Generate recent performance data
function generateRecentPerformance(avgPoints: number) {
  const performances = [];
  for (let i = 0; i < 3; i++) {
    const variance = (Math.random() - 0.5) * avgPoints * 0.6; // ±30% variance
    performances.push(Math.max(0, Math.round((avgPoints + variance) * 10) / 10));
  }
  return performances;
}

// Generate news items
function generateNews(player: Partial<Player>): Player['latest_news'] {
  const newsTemplates = {
    positive: [
      `${player.name} looking sharp in practice`,
      `Coach praises ${player.name}'s recent performance`,
      `${player.name} expected to see increased workload`,
      `Favorable matchup ahead for ${player.name}`
    ],
    negative: [
      `${player.name} dealing with minor ${['ankle', 'knee', 'shoulder'][Math.floor(Math.random() * 3)]} issue`,
      `${player.name} limited in practice`,
      `Tough matchup on tap for ${player.name}`,
      `${player.name} struggling with consistency`
    ],
    neutral: [
      `${player.name} maintains starter role`,
      `No injury designation for ${player.name}`,
      `${player.name} preparing for division rival`,
      `Status quo expected for ${player.name}`
    ]
  };
  
  const impact = player.trend === 'up' ? 'positive' : player.trend === 'down' ? 'negative' : 'neutral';
  const templates = newsTemplates[impact];
  const headline = templates[Math.floor(Math.random() * templates.length)];
  
  return {
    date: new Date(Date.now() - Math.random() * 48 * 60 * 60 * 1000).toISOString(), // Within 48 hours
    headline,
    summary: `${headline}. Fantasy managers should monitor the situation.`,
    impact
  };
}

// Main function to generate mock players
export function generateMockPlayers(): Player[] {
  const players: Player[] = [];
  let playerId = 1;
  
  // Generate QBs
  QB_NAMES.forEach((name, index) => {
    const tier = index < 5 ? 1 : index < 12 ? 2 : 3;
    const team = NFL_TEAMS[index % NFL_TEAMS.length];
    const stats = generateStats('QB', tier);
    const projectedPoints = calculateFantasyPoints(stats, 'QB');
    const recentPerformances = generateRecentPerformance(projectedPoints);
    const avgLast3 = recentPerformances.reduce((a, b) => a + b, 0) / 3;
    const trend = avgLast3 > projectedPoints * 1.1 ? 'up' : avgLast3 < projectedPoints * 0.9 ? 'down' : 'stable';
    
    players.push({
      id: playerId++,
      name,
      position: 'QB',
      team,
      bye_week: BYE_WEEKS[team],
      projected_points: projectedPoints,
      average_points: projectedPoints * (0.9 + Math.random() * 0.2),
      trend,
      ownership_percentage: tier === 1 ? 95 + Math.random() * 5 : tier === 2 ? 60 + Math.random() * 30 : 10 + Math.random() * 40,
      trade_value: tier === 1 ? 80 + Math.random() * 20 : tier === 2 ? 40 + Math.random() * 30 : 10 + Math.random() * 20,
      espn_id: 1000 + playerId,
      projected_stats: stats,
      points_last_3_weeks: recentPerformances,
      average_points_last_3: avgLast3,
      consistency_rating: 70 + Math.random() * 30,
      boom_bust_rating: tier === 1 ? 'Consistent' : Math.random() > 0.5 ? 'Boom/Bust' : 'High Floor',
      start_percentage: tier === 1 ? 90 + Math.random() * 10 : tier === 2 ? 50 + Math.random() * 40 : 5 + Math.random() * 30,
      matchup_rating: Math.floor(Math.random() * 10) + 1,
      latest_news: generateNews({ name, trend }),
      injury_status: Math.random() > 0.85 ? 'Questionable' : 'Healthy'
    });
  });
  
  // Generate RBs
  RB_NAMES.forEach((name, index) => {
    const tier = index < 8 ? 1 : index < 18 ? 2 : 3;
    const team = NFL_TEAMS[index % NFL_TEAMS.length];
    const stats = generateStats('RB', tier);
    const projectedPoints = calculateFantasyPoints(stats, 'RB');
    const recentPerformances = generateRecentPerformance(projectedPoints);
    const avgLast3 = recentPerformances.reduce((a, b) => a + b, 0) / 3;
    const trend = avgLast3 > projectedPoints * 1.1 ? 'up' : avgLast3 < projectedPoints * 0.9 ? 'down' : 'stable';
    
    players.push({
      id: playerId++,
      name,
      position: 'RB',
      team,
      bye_week: BYE_WEEKS[team],
      projected_points: projectedPoints,
      average_points: projectedPoints * (0.9 + Math.random() * 0.2),
      trend,
      ownership_percentage: tier === 1 ? 98 + Math.random() * 2 : tier === 2 ? 70 + Math.random() * 25 : 20 + Math.random() * 40,
      trade_value: tier === 1 ? 85 + Math.random() * 15 : tier === 2 ? 45 + Math.random() * 25 : 15 + Math.random() * 20,
      espn_id: 2000 + playerId,
      projected_stats: stats,
      points_last_3_weeks: recentPerformances,
      average_points_last_3: avgLast3,
      consistency_rating: tier === 1 ? 80 + Math.random() * 20 : 50 + Math.random() * 30,
      boom_bust_rating: tier === 1 ? 'High Floor' : Math.random() > 0.6 ? 'Boom/Bust' : 'Consistent',
      target_share: stats.targets ? (stats.targets / 50) * 100 : undefined,
      red_zone_touches: Math.floor(Math.random() * (tier === 1 ? 5 : 3)),
      start_percentage: tier === 1 ? 95 + Math.random() * 5 : tier === 2 ? 60 + Math.random() * 35 : 10 + Math.random() * 30,
      matchup_rating: Math.floor(Math.random() * 10) + 1,
      latest_news: generateNews({ name, trend }),
      injury_status: Math.random() > 0.8 ? ['Questionable', 'Doubtful'][Math.floor(Math.random() * 2)] : 'Healthy'
    });
  });
  
  // Generate WRs
  WR_NAMES.forEach((name, index) => {
    const tier = index < 8 ? 1 : index < 18 ? 2 : 3;
    const team = NFL_TEAMS[index % NFL_TEAMS.length];
    const stats = generateStats('WR', tier);
    const projectedPoints = calculateFantasyPoints(stats, 'WR');
    const recentPerformances = generateRecentPerformance(projectedPoints);
    const avgLast3 = recentPerformances.reduce((a, b) => a + b, 0) / 3;
    const trend = avgLast3 > projectedPoints * 1.1 ? 'up' : avgLast3 < projectedPoints * 0.9 ? 'down' : 'stable';
    
    players.push({
      id: playerId++,
      name,
      position: 'WR',
      team,
      bye_week: BYE_WEEKS[team],
      projected_points: projectedPoints,
      average_points: projectedPoints * (0.9 + Math.random() * 0.2),
      trend,
      ownership_percentage: tier === 1 ? 96 + Math.random() * 4 : tier === 2 ? 65 + Math.random() * 30 : 15 + Math.random() * 40,
      trade_value: tier === 1 ? 75 + Math.random() * 20 : tier === 2 ? 40 + Math.random() * 25 : 10 + Math.random() * 20,
      espn_id: 3000 + playerId,
      projected_stats: stats,
      points_last_3_weeks: recentPerformances,
      average_points_last_3: avgLast3,
      consistency_rating: 60 + Math.random() * 30,
      boom_bust_rating: tier === 1 ? 'Consistent' : Math.random() > 0.5 ? 'Boom/Bust' : 'High Ceiling',
      target_share: stats.targets ? (stats.targets / 120) * 100 : undefined,
      red_zone_touches: Math.floor(Math.random() * 3),
      snap_count_percentage: tier === 1 ? 85 + Math.random() * 15 : tier === 2 ? 65 + Math.random() * 20 : 40 + Math.random() * 30,
      start_percentage: tier === 1 ? 92 + Math.random() * 8 : tier === 2 ? 55 + Math.random() * 35 : 8 + Math.random() * 25,
      matchup_rating: Math.floor(Math.random() * 10) + 1,
      latest_news: generateNews({ name, trend }),
      injury_status: Math.random() > 0.82 ? 'Questionable' : 'Healthy'
    });
  });
  
  // Generate TEs
  TE_NAMES.forEach((name, index) => {
    const tier = index < 4 ? 1 : index < 10 ? 2 : 3;
    const team = NFL_TEAMS[index % NFL_TEAMS.length];
    const stats = generateStats('TE', tier);
    const projectedPoints = calculateFantasyPoints(stats, 'TE');
    const recentPerformances = generateRecentPerformance(projectedPoints);
    const avgLast3 = recentPerformances.reduce((a, b) => a + b, 0) / 3;
    const trend = avgLast3 > projectedPoints * 1.1 ? 'up' : avgLast3 < projectedPoints * 0.9 ? 'down' : 'stable';
    
    players.push({
      id: playerId++,
      name,
      position: 'TE',
      team,
      bye_week: BYE_WEEKS[team],
      projected_points: projectedPoints,
      average_points: projectedPoints * (0.9 + Math.random() * 0.2),
      trend,
      ownership_percentage: tier === 1 ? 90 + Math.random() * 10 : tier === 2 ? 50 + Math.random() * 35 : 10 + Math.random() * 30,
      trade_value: tier === 1 ? 70 + Math.random() * 20 : tier === 2 ? 30 + Math.random() * 20 : 5 + Math.random() * 15,
      espn_id: 4000 + playerId,
      projected_stats: stats,
      points_last_3_weeks: recentPerformances,
      average_points_last_3: avgLast3,
      consistency_rating: tier === 1 ? 75 + Math.random() * 20 : 45 + Math.random() * 30,
      boom_bust_rating: tier === 1 ? 'Consistent' : 'Boom/Bust',
      target_share: stats.targets ? (stats.targets / 80) * 100 : undefined,
      red_zone_touches: Math.floor(Math.random() * (tier === 1 ? 3 : 1)),
      start_percentage: tier === 1 ? 88 + Math.random() * 12 : tier === 2 ? 40 + Math.random() * 40 : 5 + Math.random() * 20,
      matchup_rating: Math.floor(Math.random() * 10) + 1,
      latest_news: generateNews({ name, trend }),
      injury_status: Math.random() > 0.85 ? 'Questionable' : 'Healthy'
    });
  });
  
  // Generate Kickers
  K_NAMES.forEach((name, index) => {
    const team = NFL_TEAMS[index % NFL_TEAMS.length];
    const projectedPoints = 7 + Math.random() * 4;
    const recentPerformances = generateRecentPerformance(projectedPoints);
    const avgLast3 = recentPerformances.reduce((a, b) => a + b, 0) / 3;
    
    players.push({
      id: playerId++,
      name,
      position: 'K',
      team,
      bye_week: BYE_WEEKS[team],
      projected_points: projectedPoints,
      average_points: projectedPoints,
      trend: 'stable',
      ownership_percentage: index < 5 ? 70 + Math.random() * 25 : 20 + Math.random() * 40,
      trade_value: 5 + Math.random() * 10,
      espn_id: 5000 + playerId,
      points_last_3_weeks: recentPerformances,
      average_points_last_3: avgLast3,
      consistency_rating: 80 + Math.random() * 20,
      boom_bust_rating: 'Consistent',
      start_percentage: index < 5 ? 80 + Math.random() * 15 : 30 + Math.random() * 40,
      matchup_rating: Math.floor(Math.random() * 10) + 1,
      injury_status: 'Healthy'
    });
  });
  
  // Generate Defenses
  DEF_NAMES.forEach((name, index) => {
    const projectedPoints = 8 + Math.random() * 5;
    const recentPerformances = generateRecentPerformance(projectedPoints);
    const avgLast3 = recentPerformances.reduce((a, b) => a + b, 0) / 3;
    const trend = avgLast3 > projectedPoints * 1.2 ? 'up' : avgLast3 < projectedPoints * 0.8 ? 'down' : 'stable';
    
    players.push({
      id: playerId++,
      name: name + ' D/ST',
      position: 'DEF',
      team: name.substring(0, 3).toUpperCase(),
      bye_week: Math.floor(Math.random() * 8) + 5, // Random bye week 5-12
      projected_points: projectedPoints,
      average_points: projectedPoints,
      trend,
      ownership_percentage: index < 5 ? 75 + Math.random() * 20 : 25 + Math.random() * 40,
      trade_value: index < 5 ? 20 + Math.random() * 15 : 5 + Math.random() * 10,
      espn_id: 6000 + playerId,
      points_last_3_weeks: recentPerformances,
      average_points_last_3: avgLast3,
      consistency_rating: 60 + Math.random() * 30,
      boom_bust_rating: 'Boom/Bust',
      start_percentage: index < 5 ? 85 + Math.random() * 10 : 35 + Math.random() * 40,
      matchup_rating: Math.floor(Math.random() * 10) + 1,
      latest_news: generateNews({ name: name + ' D/ST', trend }),
      injury_status: 'Healthy'
    });
  });
  
  return players;
}

// Export a default set of players
export const mockPlayers = generateMockPlayers();
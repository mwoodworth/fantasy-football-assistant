export interface Player {
  id: number;
  name: string;
  position: string;
  team: string;
  bye_week: number;
  injury_status?: string;
  projected_points?: number;
  average_points?: number;
  trend?: 'up' | 'down' | 'stable';
  ownership_percentage?: number;
  trade_value?: number;
  
  // ESPN specific fields
  espn_id?: number;
  espn_player_id?: string;
  
  // Enhanced projections
  projected_stats?: {
    passing_yards?: number;
    passing_tds?: number;
    rushing_yards?: number;
    rushing_tds?: number;
    receptions?: number;
    receiving_yards?: number;
    receiving_tds?: number;
    targets?: number;
    carries?: number;
  };
  
  // Performance tracking
  points_last_3_weeks?: number[];
  average_points_last_3?: number;
  consistency_rating?: number; // 0-100 score
  boom_bust_rating?: string; // 'Consistent' | 'Boom/Bust' | 'High Floor' | 'High Ceiling'
  
  // Advanced metrics
  target_share?: number; // Percentage of team targets
  red_zone_touches?: number;
  snap_count_percentage?: number;
  
  // Fantasy relevance
  start_percentage?: number;
  roster_percentage?: number;
  waiver_priority?: number;
  faab_value?: number;
  
  // News and updates
  latest_news?: {
    date: string;
    headline: string;
    summary: string;
    impact?: 'positive' | 'negative' | 'neutral';
  };
  injury_notes?: string;
  injury_designation?: 'Q' | 'D' | 'O' | 'IR' | 'PUP';
  season_outlook?: string;
  
  // Matchup data
  opponent_rank?: number; // Opponent's rank vs position
  matchup_rating?: number; // 1-10 matchup favorability
  weather_impact?: string;
}

export interface PlayersFilterOptions {
  position?: string;
  team?: string;
  status?: string;
  searchTerm?: string;
  hideInjured?: boolean;
  freeAgentsOnly?: boolean;
  sortBy?: 'projected' | 'average' | 'name' | 'ownership';
  sortOrder?: 'asc' | 'desc';
}

export interface PlayersResponse {
  players: Player[];
  total: number;
  page: number;
  limit: number;
}
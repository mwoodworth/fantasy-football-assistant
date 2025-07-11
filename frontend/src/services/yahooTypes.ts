// Yahoo Fantasy Types

export type YahooAuthStatus = {
  authenticated: boolean;
  user_id: number;
};

export type YahooLeague = {
  league_key: string;
  league_id: string;
  name: string;
  season: number;
  num_teams: number;
  scoring_type: string;
  draft_status: string;
  current_week: number;
  user_team?: YahooTeam;
  teams?: YahooTeam[];
};

export type YahooTeam = {
  team_key: string;
  team_id: number;
  name: string;
  manager_name?: string;
  logo_url?: string;
  rank?: number;
  points_for?: number;
  points_against?: number;
  wins?: number;
  losses?: number;
  ties?: number;
  is_owned_by_current_login?: boolean;
};

export type YahooPlayer = {
  player_id: string;
  name: string;
  first_name: string;
  last_name: string;
  position: string;
  team: string;
  bye_week: number;
  status: string;
  injury_status?: string;
  ownership: {
    percentage_owned: number;
    change: number;
  };
  points: {
    total: number;
    average: number;
  };
  projections: {
    season: number;
    week: number;
  };
  source: 'yahoo';
};

export type YahooTransaction = {
  transaction_key: string;
  type: string;
  status: string;
  timestamp: number;
  players?: YahooPlayer[];
};

export type YahooDraftSession = {
  session_id: number;
  session_token: string;
  draft_position: number;
  league_name: string;
  num_teams: number;
  status: string;
  current_pick: number;
  current_round: number;
  user_draft_position: number;
  picks_until_turn: number;
  drafted_players: YahooDraftPick[];
  live_sync_enabled: boolean;
  last_sync: string | null;
};

export type YahooDraftPick = {
  pick: number;
  round: number;
  team_key: string;
  player_key: string;
  player_name: string;
};

export type YahooDraftRecommendation = {
  recommendations: YahooPlayer[];
  primary: YahooPlayer | null;
  positional_needs: Record<string, number>;
  value_picks: YahooPlayer[];
  sleepers: YahooPlayer[];
  avoid_players: YahooPlayer[];
  ai_insights: string;
  confidence_score: number;
  generated_at: string;
};

export type YahooDraftStatus = {
  status: string;
  current_pick: number;
  current_round: number;
  is_user_turn: boolean;
  picks_until_turn: number;
  recent_picks: YahooDraftEvent[];
  last_sync: string | null;
  sync_enabled: boolean;
};

export type YahooDraftEvent = {
  pick_number: number;
  round: number;
  team_key: string;
  player_name: string;
  player_key: string;
  timestamp: string;
};
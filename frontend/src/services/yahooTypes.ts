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
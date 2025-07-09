import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:6001/api'

// Create axios instance with default config
export const espnApi = axios.create({
  baseURL: `${API_BASE_URL}/espn`,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add auth token to requests
espnApi.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Handle auth errors
espnApi.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized access
      localStorage.removeItem('auth_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// ESPN API types
export interface ESPNLeague {
  id: number
  espn_league_id: number
  season: number
  league_name: string
  is_active: boolean
  is_archived: boolean
  team_count: number
  scoring_type: string
  draft_date: string | null
  draft_completed: boolean
  user_draft_position: number | null
  sync_status: string
  last_sync: string | null
  user_team_name: string | null
  league_type_description: string
}

export interface DraftSession {
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

export interface DraftPick {
  player_id: number
  player_name: string
  position: string
  team: string
  pick_number: number
  drafted_by_user: boolean
}

// ESPN API methods
export const espnService = {
  // League methods
  async getLeagues() {
    const response = await espnApi.get<ESPNLeague[]>('/leagues')
    return response.data
  },

  async connectLeague(data: {
    espn_league_id: number
    season: number
    league_name?: string
    espn_s2?: string
    swid?: string
    user_team_id?: number
  }) {
    const response = await espnApi.post<ESPNLeague>('/leagues/connect', data)
    return response.data
  },

  async disconnectLeague(leagueId: number) {
    const response = await espnApi.delete(`/leagues/${leagueId}`)
    return response.data
  },

  async permanentlyDeleteLeague(leagueId: number) {
    const response = await espnApi.delete(`/leagues/${leagueId}/permanent`)
    return response.data
  },

  async unarchiveLeague(leagueId: number) {
    const response = await espnApi.put(`/leagues/${leagueId}/unarchive`)
    return response.data
  },

  async syncLeague(leagueId: number) {
    const response = await espnApi.post(`/leagues/${leagueId}/sync`)
    return response.data
  },

  // Draft methods
  async startDraftSession(data: {
    league_id: number
    draft_position: number
    live_sync?: boolean
  }) {
    const response = await espnApi.post<DraftSession>('/draft/start', data)
    return response.data
  },

  async getDraftSession(sessionId: number) {
    const response = await espnApi.get<DraftSession>(`/draft/session/${sessionId}`)
    return response.data
  },

  async getActiveDraftSession(leagueId: number) {
    const response = await espnApi.get<DraftSession | null>(`/draft/sessions/active?league_id=${leagueId}`)
    return response.data
  },

  async getDraftLiveStatus(sessionId: number) {
    const response = await espnApi.get(`/draft/${sessionId}/live-status`)
    return response.data
  },

  async toggleDraftSync(sessionId: number, enable: boolean) {
    const response = await espnApi.post(`/draft/${sessionId}/toggle-sync?enable=${enable}`)
    return response.data
  },

  async makeDraftPick(sessionId: number, playerId: number) {
    const response = await espnApi.post(`/draft/${sessionId}/pick`, { player_id: playerId })
    return response.data
  },

  async getDraftRecommendations(sessionId: number) {
    const response = await espnApi.get(`/draft/${sessionId}/recommendations`)
    return response.data
  },
}
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface ESPNLeague {
  id: number;
  espn_id: number;
  league_name: string;
  season: number;
  team_count: number;
  user_team_id?: number;
  user_team_name?: string;
}

interface ESPNStore {
  selectedLeague: ESPNLeague | null;
  availableLeagues: ESPNLeague[];
  
  // Actions
  setSelectedLeague: (league: ESPNLeague | null) => void;
  setAvailableLeagues: (leagues: ESPNLeague[]) => void;
  clearESPNData: () => void;
}

export const useESPNStore = create<ESPNStore>()(
  persist(
    (set) => ({
      selectedLeague: null,
      availableLeagues: [],
      
      setSelectedLeague: (league) => set({ selectedLeague: league }),
      setAvailableLeagues: (leagues) => set({ availableLeagues: leagues }),
      clearESPNData: () => set({ selectedLeague: null, availableLeagues: [] }),
    }),
    {
      name: 'espn-storage',
    }
  )
);
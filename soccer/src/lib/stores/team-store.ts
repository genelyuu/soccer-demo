"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";

interface TeamStore {
  selectedTeamId: string | null;
  setSelectedTeam: (id: string) => void;
  _isHydrated: boolean;
  _setHydrated: () => void;
}

export const useTeamStore = create<TeamStore>()(
  persist(
    (set) => ({
      selectedTeamId: null,
      setSelectedTeam: (id: string) => set({ selectedTeamId: id }),
      _isHydrated: false,
      _setHydrated: () => set({ _isHydrated: true }),
    }),
    {
      name: "team-store",
      onRehydrateStorage: () => (state) => {
        state?._setHydrated();
      },
    },
  ),
);

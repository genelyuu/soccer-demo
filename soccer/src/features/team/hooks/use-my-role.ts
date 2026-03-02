"use client";

import { useTeams } from "./use-team";
import { useTeamStore } from "@/lib/stores/team-store";
import type { TeamRole } from "@/lib/types";

/**
 * 현재 선택된 팀에서 사용자의 역할을 반환하는 훅.
 * selectedTeamId가 없거나 팀 데이터가 없으면 null 반환.
 */
export function useMyRole(): { role: TeamRole | null; isLoading: boolean } {
  const { data, isLoading } = useTeams();
  const selectedTeamId = useTeamStore((s) => s.selectedTeamId);

  if (isLoading) return { role: null, isLoading: true };
  if (!selectedTeamId || !data?.teams) return { role: null, isLoading: false };

  const team = data.teams.find((t) => t.id === selectedTeamId);
  return { role: team?.my_role ?? null, isLoading: false };
}

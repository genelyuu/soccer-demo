"use client";

import { useEffect, useMemo } from "react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useTeams } from "@/features/team/hooks/use-team";
import { useTeamStore } from "@/lib/stores/team-store";

export function TeamSelector() {
  const { data, isLoading } = useTeams();
  const { selectedTeamId, setSelectedTeam, _isHydrated } = useTeamStore();

  const teams = useMemo(() => data?.teams ?? [], [data?.teams]);

  // 팀이 1개면 자동 선택
  useEffect(() => {
    if (_isHydrated && teams.length === 1 && !selectedTeamId) {
      setSelectedTeam(teams[0].id);
    }
  }, [teams, selectedTeamId, setSelectedTeam, _isHydrated]);

  if (!_isHydrated || isLoading) {
    return (
      <div className="h-10 w-[160px] animate-pulse rounded-md bg-muted border border-transparent" />
    );
  }

  if (teams.length === 0) {
    return null;
  }

  return (
    <Select
      value={selectedTeamId ?? undefined}
      onValueChange={setSelectedTeam}
    >
      <SelectTrigger className="w-[160px]">
        <SelectValue placeholder="팀 선택" />
      </SelectTrigger>
      <SelectContent>
        {teams.map((team) => (
          <SelectItem key={team.id} value={team.id}>
            {team.name}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}

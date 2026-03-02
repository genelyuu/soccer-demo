"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getMatches, getMatch, createMatch, updateMatch, type CreateMatchPayload, type MatchFilterOptions } from "../api";

export function useMatches(teamId: string, options?: MatchFilterOptions) {
  return useQuery({
    queryKey: ["matches", teamId, options],
    queryFn: () => getMatches(teamId, options),
    enabled: !!teamId,
  });
}

export function useMatch(id: string) {
  return useQuery({
    queryKey: ["match", id],
    queryFn: () => getMatch(id),
    enabled: !!id,
  });
}

export function useCreateMatch() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createMatch,
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["matches", variables.team_id] });
    },
  });
}

export function useUpdateMatch() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, ...payload }: { id: string } & Partial<CreateMatchPayload>) =>
      updateMatch(id, payload),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["match", data.match.id] });
      queryClient.invalidateQueries({ queryKey: ["matches"] });
    },
  });
}

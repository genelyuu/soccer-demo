"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getMembers, addMember, updateMemberRole, removeMember } from "../api";
import type { TeamRole } from "@/lib/types";

export function useMembers(teamId: string) {
  return useQuery({
    queryKey: ["members", teamId],
    queryFn: () => getMembers(teamId),
    enabled: !!teamId,
  });
}

export function useAddMember(teamId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: { email: string; role?: string }) =>
      addMember(teamId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["members", teamId] });
    },
  });
}

export function useUpdateMemberRole(teamId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ memberId, role }: { memberId: string; role: TeamRole }) =>
      updateMemberRole(teamId, memberId, role),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["members", teamId] });
    },
  });
}

export function useRemoveMember(teamId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (memberId: string) => removeMember(teamId, memberId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["members", teamId] });
    },
  });
}

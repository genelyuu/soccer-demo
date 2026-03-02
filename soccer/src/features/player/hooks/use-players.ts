"use client";

import { useQuery } from "@tanstack/react-query";
import { getPlayers, getPlayer } from "../api";

export function usePlayers(page = 1, limit = 20) {
  return useQuery({
    queryKey: ["players", page, limit],
    queryFn: () => getPlayers(page, limit),
  });
}

export function usePlayer(id: string) {
  return useQuery({
    queryKey: ["player", id],
    queryFn: () => getPlayer(id),
    enabled: !!id,
  });
}

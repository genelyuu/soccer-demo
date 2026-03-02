import axios from "axios";
import type { User } from "@/lib/types";

export interface PlayersResponse {
  players: User[];
  count: number;
  page: number;
  limit: number;
}

export async function getPlayers(
  page = 1,
  limit = 20,
): Promise<PlayersResponse> {
  const { data } = await axios.get("/api/players", {
    params: { page, limit, orderBy: "name", ascending: "true" },
  });
  return data;
}

export async function getPlayer(
  id: string,
): Promise<{ player: User }> {
  const { data } = await axios.get(`/api/players/${id}`);
  return data;
}

import axios from "axios";
import type { Match, MatchStatus, Attendance } from "@/lib/types";

export interface CreateMatchPayload {
  team_id: string;
  title: string;
  description?: string;
  match_date: string;
  location?: string;
  opponent?: string;
}

export interface MatchFilterOptions {
  status?: MatchStatus;
  sort?: "asc" | "desc";
  limit?: number;
}

export async function getMatches(teamId: string, options?: MatchFilterOptions): Promise<{ matches: Match[] }> {
  const params = new URLSearchParams({ team_id: teamId });
  if (options?.status) params.set("status", options.status);
  if (options?.sort) params.set("sort", options.sort);
  if (options?.limit) params.set("limit", String(options.limit));
  const { data } = await axios.get(`/api/matches?${params.toString()}`);
  return data;
}

export async function getMatch(id: string): Promise<{ match: Match; attendances: Attendance[] }> {
  const { data } = await axios.get(`/api/matches/${id}`);
  return data;
}

export async function createMatch(payload: CreateMatchPayload): Promise<{ match: Match }> {
  const { data } = await axios.post("/api/matches", payload);
  return data;
}

export async function updateMatch(id: string, payload: Partial<CreateMatchPayload>): Promise<{ match: Match }> {
  const { data } = await axios.patch(`/api/matches/${id}`, payload);
  return data;
}

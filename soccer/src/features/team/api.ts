import axios from "axios";
import type { Team, TeamMember, TeamRole } from "@/lib/types";

export interface TeamWithRole extends Team {
  my_role: TeamRole;
}

export interface MemberWithUser extends Pick<TeamMember, "id" | "role" | "joined_at"> {
  users: { id: string; name: string; email: string; avatar_url: string | null };
}

export interface MembersResponse {
  members: MemberWithUser[];
  my_role: TeamRole;
}

// ─── 팀 CRUD ────────────────────────────────────────────────

export async function getTeams(): Promise<{ teams: TeamWithRole[] }> {
  const { data } = await axios.get("/api/teams");
  return data;
}

export async function getTeam(teamId: string): Promise<{ team: Team; my_role: TeamRole }> {
  const { data } = await axios.get(`/api/teams/${teamId}`);
  return data;
}

export async function createTeam(payload: { name: string; description?: string }): Promise<{ team: Team }> {
  const { data } = await axios.post("/api/teams", payload);
  return data;
}

export async function updateTeam(
  teamId: string,
  payload: { name?: string; description?: string },
): Promise<{ team: Team }> {
  const { data } = await axios.patch(`/api/teams/${teamId}`, payload);
  return data;
}

export async function deleteTeam(teamId: string): Promise<{ message: string }> {
  const { data } = await axios.delete(`/api/teams/${teamId}`);
  return data;
}

// ─── 멤버 관리 ──────────────────────────────────────────────

export async function getMembers(teamId: string): Promise<MembersResponse> {
  const { data } = await axios.get(`/api/teams/${teamId}/members`);
  return data;
}

export async function addMember(
  teamId: string,
  payload: { email: string; role?: string },
): Promise<{ message: string }> {
  const { data } = await axios.post(`/api/teams/${teamId}/members`, payload);
  return data;
}

export async function updateMemberRole(
  teamId: string,
  memberId: string,
  role: TeamRole,
): Promise<{ message: string }> {
  const { data } = await axios.patch(`/api/teams/${teamId}/members/${memberId}`, { role });
  return data;
}

export async function removeMember(
  teamId: string,
  memberId: string,
): Promise<{ message: string }> {
  const { data } = await axios.delete(`/api/teams/${teamId}/members/${memberId}`);
  return data;
}

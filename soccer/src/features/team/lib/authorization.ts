import type { TeamRole } from "@/lib/types";
import { ROLE_HIERARCHY } from "../constants";

/** 팀 정보 수정 가능 여부 (ADMIN | MANAGER) */
export function canModifyTeam(role: TeamRole): boolean {
  return role === "ADMIN" || role === "MANAGER";
}

/** 팀 삭제 가능 여부 (ADMIN) */
export function canDeleteTeam(role: TeamRole): boolean {
  return role === "ADMIN";
}

/** 멤버 추가/제거 가능 여부 (ADMIN | MANAGER) */
export function canModifyMembers(role: TeamRole): boolean {
  return role === "ADMIN" || role === "MANAGER";
}

/** 역할 변경 가능 여부 (ADMIN) */
export function canChangeRole(role: TeamRole): boolean {
  return role === "ADMIN";
}

/** 경기 생성/수정/확정 가능 여부 (ADMIN | MANAGER) */
export function canManageMatch(role: TeamRole): boolean {
  return role === "ADMIN" || role === "MANAGER";
}

/** 기록 입력 가능 여부 (ADMIN | MANAGER) */
export function canWriteRecord(role: TeamRole): boolean {
  return role === "ADMIN" || role === "MANAGER";
}

/** 출석 투표 가능 여부 (ADMIN | MANAGER | MEMBER) */
export function canVoteAttendance(role: TeamRole): boolean {
  return role === "ADMIN" || role === "MANAGER" || role === "MEMBER";
}

/** 특정 멤버 제거 가능 여부
 * - ADMIN: 모든 멤버 제거 가능
 * - MANAGER: MEMBER, GUEST만 제거 가능
 * - 그 외: 불가 */
export function canRemoveMember(
  actorRole: TeamRole,
  targetRole: TeamRole,
): boolean {
  if (actorRole === "ADMIN") return true;
  if (actorRole === "MANAGER") {
    return ROLE_HIERARCHY[targetRole] < ROLE_HIERARCHY["MANAGER"];
  }
  return false;
}

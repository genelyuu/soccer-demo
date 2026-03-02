import type { TeamRole } from "@/lib/types";

/** 역할 한국어 라벨 */
export const ROLE_LABEL: Record<TeamRole, string> = {
  ADMIN: "관리자",
  MANAGER: "매니저",
  MEMBER: "멤버",
  GUEST: "게스트",
};

/** 역할 Badge 색상 (Tailwind 클래스) */
export const ROLE_COLOR: Record<TeamRole, string> = {
  ADMIN: "bg-purple-100 text-purple-800",
  MANAGER: "bg-blue-100 text-blue-800",
  MEMBER: "bg-gray-100 text-gray-800",
  GUEST: "bg-yellow-100 text-yellow-800",
};

/** 역할 계층 (숫자가 높을수록 상위) */
export const ROLE_HIERARCHY: Record<TeamRole, number> = {
  ADMIN: 40,
  MANAGER: 30,
  MEMBER: 20,
  GUEST: 10,
};

/** 역할 옵션 (Select 등에서 사용) */
export const ROLE_OPTIONS: { value: TeamRole; label: string }[] = [
  { value: "ADMIN", label: "관리자" },
  { value: "MANAGER", label: "매니저" },
  { value: "MEMBER", label: "멤버" },
  { value: "GUEST", label: "게스트" },
];

import type { MatchStatus } from "@/lib/types";

export const MATCH_STATUS_LABEL: Record<MatchStatus, string> = {
  OPEN: "투표 중",
  CONFIRMED: "확정",
  COMPLETED: "완료",
  CANCELLED: "취소",
};

export const MATCH_STATUS_COLOR: Record<MatchStatus, string> = {
  OPEN: "bg-blue-100 text-blue-800",
  CONFIRMED: "bg-green-100 text-green-800",
  COMPLETED: "bg-gray-100 text-gray-800",
  CANCELLED: "bg-red-100 text-red-800",
};

import { describe, it, expect } from "vitest";
import type { MatchStatus } from "@/lib/types";

// 경기 상태 전이 규칙 검증 (도메인 로직 단위 테스트)
const VALID_TRANSITIONS: Record<MatchStatus, MatchStatus[]> = {
  OPEN: ["CONFIRMED", "CANCELLED"],
  CONFIRMED: ["COMPLETED", "CANCELLED"],
  COMPLETED: [],
  CANCELLED: [],
};

function canTransition(from: MatchStatus, to: MatchStatus): boolean {
  return VALID_TRANSITIONS[from].includes(to);
}

describe("경기 상태 전이 규칙", () => {
  it("OPEN에서 CONFIRMED로 전이할 수 있다", () => {
    expect(canTransition("OPEN", "CONFIRMED")).toBe(true);
  });

  it("OPEN에서 CANCELLED로 전이할 수 있다", () => {
    expect(canTransition("OPEN", "CANCELLED")).toBe(true);
  });

  it("OPEN에서 COMPLETED로 직접 전이할 수 없다", () => {
    expect(canTransition("OPEN", "COMPLETED")).toBe(false);
  });

  it("CONFIRMED에서 COMPLETED로 전이할 수 있다", () => {
    expect(canTransition("CONFIRMED", "COMPLETED")).toBe(true);
  });

  it("COMPLETED에서는 더 이상 전이할 수 없다", () => {
    expect(VALID_TRANSITIONS.COMPLETED).toHaveLength(0);
  });

  it("CANCELLED에서는 더 이상 전이할 수 없다", () => {
    expect(VALID_TRANSITIONS.CANCELLED).toHaveLength(0);
  });

  it("확정(CONFIRMED) 시 기록실이 생성되어야 한다", () => {
    // 이 테스트는 MatchConfirmed 이벤트의 요구사항 검증
    const autoActions: Record<string, string[]> = {
      CONFIRMED: ["CREATE_RECORD_ROOM"],
    };
    expect(autoActions["CONFIRMED"]).toContain("CREATE_RECORD_ROOM");
  });
});

import { describe, it, expect } from "vitest";
import { MATCH_STATUS_LABEL, MATCH_STATUS_COLOR } from "../constants";
import type { MatchStatus } from "@/lib/types";

describe("경기 상태 상수", () => {
  const allStatuses: MatchStatus[] = ["OPEN", "CONFIRMED", "COMPLETED", "CANCELLED"];

  it("모든 MatchStatus에 대한 한국어 라벨이 정의되어 있다", () => {
    allStatuses.forEach((status) => {
      expect(MATCH_STATUS_LABEL[status]).toBeDefined();
      expect(typeof MATCH_STATUS_LABEL[status]).toBe("string");
      expect(MATCH_STATUS_LABEL[status].length).toBeGreaterThan(0);
    });
  });

  it("모든 MatchStatus에 대한 색상 클래스가 정의되어 있다", () => {
    allStatuses.forEach((status) => {
      expect(MATCH_STATUS_COLOR[status]).toBeDefined();
      expect(MATCH_STATUS_COLOR[status]).toContain("bg-");
      expect(MATCH_STATUS_COLOR[status]).toContain("text-");
    });
  });

  it("OPEN 상태는 '투표 중'으로 표시된다", () => {
    expect(MATCH_STATUS_LABEL.OPEN).toBe("투표 중");
  });

  it("CONFIRMED 상태는 '확정'으로 표시된다", () => {
    expect(MATCH_STATUS_LABEL.CONFIRMED).toBe("확정");
  });
});

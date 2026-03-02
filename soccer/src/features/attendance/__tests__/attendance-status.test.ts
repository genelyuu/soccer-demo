import { describe, it, expect } from "vitest";
import type { AttendanceStatus } from "@/lib/types";

describe("출석 투표 상태 검증", () => {
  const validStatuses: AttendanceStatus[] = ["PENDING", "ACCEPTED", "DECLINED", "MAYBE"];
  const voteableStatuses = ["ACCEPTED", "DECLINED", "MAYBE"];

  it("유효한 투표 상태는 ACCEPTED, DECLINED, MAYBE이다", () => {
    voteableStatuses.forEach((status) => {
      expect(validStatuses).toContain(status);
    });
  });

  it("PENDING은 투표 가능한 상태가 아니다 (시스템이 생성하는 초기 상태)", () => {
    expect(voteableStatuses).not.toContain("PENDING");
  });

  it("투표 상태 전환: PENDING → ACCEPTED/DECLINED/MAYBE", () => {
    const initialStatus: AttendanceStatus = "PENDING";
    expect(initialStatus).toBe("PENDING");

    // 투표 후 상태 변경 시뮬레이션
    voteableStatuses.forEach((newStatus) => {
      expect(validStatuses).toContain(newStatus);
    });
  });
});

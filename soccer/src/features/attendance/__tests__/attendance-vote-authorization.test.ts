import { describe, it, expect } from "vitest";
import { canVoteAttendance } from "@/features/team/lib/authorization";
import type { TeamRole } from "@/lib/types";

describe("출석 투표 권한 검증 — canVoteAttendance", () => {
  it("ADMIN은 출석 투표할 수 있다", () => {
    expect(canVoteAttendance("ADMIN")).toBe(true);
  });

  it("MANAGER는 출석 투표할 수 있다", () => {
    expect(canVoteAttendance("MANAGER")).toBe(true);
  });

  it("MEMBER는 출석 투표할 수 있다", () => {
    expect(canVoteAttendance("MEMBER")).toBe(true);
  });

  it("GUEST는 출석 투표할 수 없다", () => {
    expect(canVoteAttendance("GUEST")).toBe(false);
  });

  it("허용된 역할만 투표 가능하다", () => {
    const allRoles: TeamRole[] = ["ADMIN", "MANAGER", "MEMBER", "GUEST"];
    const allowed = allRoles.filter(canVoteAttendance);
    expect(allowed).toEqual(["ADMIN", "MANAGER", "MEMBER"]);
  });

  it("GUEST 역할은 명시적으로 차단된다", () => {
    const deniedRoles: TeamRole[] = ["GUEST"];
    for (const role of deniedRoles) {
      expect(canVoteAttendance(role)).toBe(false);
    }
  });
});

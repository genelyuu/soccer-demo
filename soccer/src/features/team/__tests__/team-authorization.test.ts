import { describe, it, expect } from "vitest";
import {
  canModifyTeam,
  canDeleteTeam,
  canModifyMembers,
  canChangeRole,
  canRemoveMember,
} from "../lib/authorization";
import type { TeamRole } from "@/lib/types";

const ALL_ROLES: TeamRole[] = ["ADMIN", "MANAGER", "MEMBER", "GUEST"];

describe("팀 권한 검증", () => {
  describe("canModifyTeam — 팀 수정 권한", () => {
    it("ADMIN은 팀을 수정할 수 있다", () => {
      expect(canModifyTeam("ADMIN")).toBe(true);
    });

    it("MANAGER는 팀을 수정할 수 있다", () => {
      expect(canModifyTeam("MANAGER")).toBe(true);
    });

    it("MEMBER는 팀을 수정할 수 없다", () => {
      expect(canModifyTeam("MEMBER")).toBe(false);
    });

    it("GUEST는 팀을 수정할 수 없다", () => {
      expect(canModifyTeam("GUEST")).toBe(false);
    });
  });

  describe("canDeleteTeam — 팀 삭제 권한", () => {
    it("ADMIN만 팀을 삭제할 수 있다", () => {
      expect(canDeleteTeam("ADMIN")).toBe(true);
    });

    it.each(["MANAGER", "MEMBER", "GUEST"] as TeamRole[])(
      "%s는 팀을 삭제할 수 없다",
      (role) => {
        expect(canDeleteTeam(role)).toBe(false);
      },
    );
  });

  describe("canModifyMembers — 멤버 추가/제거 권한", () => {
    it("ADMIN은 멤버를 관리할 수 있다", () => {
      expect(canModifyMembers("ADMIN")).toBe(true);
    });

    it("MANAGER는 멤버를 관리할 수 있다", () => {
      expect(canModifyMembers("MANAGER")).toBe(true);
    });

    it("MEMBER는 멤버를 관리할 수 없다", () => {
      expect(canModifyMembers("MEMBER")).toBe(false);
    });

    it("GUEST는 멤버를 관리할 수 없다", () => {
      expect(canModifyMembers("GUEST")).toBe(false);
    });
  });

  describe("canChangeRole — 역할 변경 권한", () => {
    it("ADMIN만 역할을 변경할 수 있다", () => {
      expect(canChangeRole("ADMIN")).toBe(true);
    });

    it.each(["MANAGER", "MEMBER", "GUEST"] as TeamRole[])(
      "%s는 역할을 변경할 수 없다",
      (role) => {
        expect(canChangeRole(role)).toBe(false);
      },
    );
  });

  describe("canRemoveMember — 멤버 제거 권한", () => {
    it("ADMIN은 모든 역할의 멤버를 제거할 수 있다", () => {
      for (const target of ALL_ROLES) {
        expect(canRemoveMember("ADMIN", target)).toBe(true);
      }
    });

    it("MANAGER는 MEMBER를 제거할 수 있다", () => {
      expect(canRemoveMember("MANAGER", "MEMBER")).toBe(true);
    });

    it("MANAGER는 GUEST를 제거할 수 있다", () => {
      expect(canRemoveMember("MANAGER", "GUEST")).toBe(true);
    });

    it("MANAGER는 ADMIN을 제거할 수 없다", () => {
      expect(canRemoveMember("MANAGER", "ADMIN")).toBe(false);
    });

    it("MANAGER는 다른 MANAGER를 제거할 수 없다", () => {
      expect(canRemoveMember("MANAGER", "MANAGER")).toBe(false);
    });

    it("MEMBER는 누구도 제거할 수 없다", () => {
      for (const target of ALL_ROLES) {
        expect(canRemoveMember("MEMBER", target)).toBe(false);
      }
    });

    it("GUEST는 누구도 제거할 수 없다", () => {
      for (const target of ALL_ROLES) {
        expect(canRemoveMember("GUEST", target)).toBe(false);
      }
    });
  });
});

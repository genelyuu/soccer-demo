import { describe, it, expect } from "vitest";
import { z } from "zod";

// API 라우트에서 사용하는 스키마를 동일하게 정의하여 단위 테스트
const addMemberSchema = z.object({
  email: z.string().email("유효한 이메일을 입력해주세요"),
  role: z.enum(["MANAGER", "MEMBER", "GUEST"]).default("MEMBER"),
});

const updateRoleSchema = z.object({
  role: z.enum(["ADMIN", "MANAGER", "MEMBER", "GUEST"], {
    errorMap: () => ({ message: "유효하지 않은 역할입니다" }),
  }),
});

describe("멤버 추가 입력 검증", () => {
  it("유효한 이메일과 역할은 성공한다", () => {
    const result = addMemberSchema.safeParse({
      email: "user@example.com",
      role: "MEMBER",
    });
    expect(result.success).toBe(true);
  });

  it("역할 미지정 시 기본값은 MEMBER이다", () => {
    const result = addMemberSchema.safeParse({ email: "user@example.com" });
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.role).toBe("MEMBER");
    }
  });

  it("잘못된 이메일은 실패한다", () => {
    const result = addMemberSchema.safeParse({
      email: "not-an-email",
      role: "MEMBER",
    });
    expect(result.success).toBe(false);
    if (!result.success) {
      expect(result.error.issues[0].message).toBe("유효한 이메일을 입력해주세요");
    }
  });

  it("ADMIN 역할로 추가할 수 없다", () => {
    const result = addMemberSchema.safeParse({
      email: "user@example.com",
      role: "ADMIN",
    });
    expect(result.success).toBe(false);
  });

  it("유효하지 않은 역할은 실패한다", () => {
    const result = addMemberSchema.safeParse({
      email: "user@example.com",
      role: "SUPERADMIN",
    });
    expect(result.success).toBe(false);
  });

  it("이메일 누락은 실패한다", () => {
    const result = addMemberSchema.safeParse({ role: "MEMBER" });
    expect(result.success).toBe(false);
  });
});

describe("역할 변경 입력 검증", () => {
  it.each(["ADMIN", "MANAGER", "MEMBER", "GUEST"] as const)(
    "%s 역할 변경은 성공한다",
    (role) => {
      const result = updateRoleSchema.safeParse({ role });
      expect(result.success).toBe(true);
    },
  );

  it("유효하지 않은 역할은 실패한다", () => {
    const result = updateRoleSchema.safeParse({ role: "OWNER" });
    expect(result.success).toBe(false);
    if (!result.success) {
      expect(result.error.issues[0].message).toBe("유효하지 않은 역할입니다");
    }
  });

  it("역할 누락은 실패한다", () => {
    const result = updateRoleSchema.safeParse({});
    expect(result.success).toBe(false);
  });
});

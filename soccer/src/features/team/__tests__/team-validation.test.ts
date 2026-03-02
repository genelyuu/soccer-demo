import { describe, it, expect } from "vitest";
import { z } from "zod";

// API 라우트에서 사용하는 스키마를 동일하게 정의하여 단위 테스트
const createTeamSchema = z.object({
  name: z.string().min(1, "팀명을 입력해주세요"),
  description: z.string().optional(),
});

const updateTeamSchema = z.object({
  name: z.string().min(1, "팀명을 입력해주세요").optional(),
  description: z.string().optional(),
});

describe("팀 생성 입력 검증", () => {
  it("유효한 입력은 성공한다", () => {
    const result = createTeamSchema.safeParse({
      name: "FC 서울",
      description: "서울 동호회",
    });
    expect(result.success).toBe(true);
  });

  it("description 없이도 성공한다", () => {
    const result = createTeamSchema.safeParse({ name: "FC 서울" });
    expect(result.success).toBe(true);
  });

  it("빈 팀명은 실패한다", () => {
    const result = createTeamSchema.safeParse({ name: "" });
    expect(result.success).toBe(false);
    if (!result.success) {
      expect(result.error.issues[0].message).toBe("팀명을 입력해주세요");
    }
  });

  it("팀명 누락은 실패한다", () => {
    const result = createTeamSchema.safeParse({});
    expect(result.success).toBe(false);
  });
});

describe("팀 수정 입력 검증", () => {
  it("name만 수정할 수 있다", () => {
    const result = updateTeamSchema.safeParse({ name: "새 팀명" });
    expect(result.success).toBe(true);
  });

  it("description만 수정할 수 있다", () => {
    const result = updateTeamSchema.safeParse({ description: "새 설명" });
    expect(result.success).toBe(true);
  });

  it("빈 객체도 유효하다", () => {
    const result = updateTeamSchema.safeParse({});
    expect(result.success).toBe(true);
  });

  it("빈 name은 실패한다", () => {
    const result = updateTeamSchema.safeParse({ name: "" });
    expect(result.success).toBe(false);
    if (!result.success) {
      expect(result.error.issues[0].message).toBe("팀명을 입력해주세요");
    }
  });
});

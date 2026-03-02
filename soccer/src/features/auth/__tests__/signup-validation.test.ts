import { describe, it, expect } from "vitest";
import { z } from "zod";

// signup API에서 사용하는 스키마를 동일하게 정의하여 단위 테스트
const signupSchema = z.object({
  email: z.string().email("유효한 이메일을 입력해주세요"),
  password: z.string().min(6, "비밀번호는 최소 6자 이상이어야 합니다"),
  name: z.string().min(1, "이름을 입력해주세요"),
});

describe("회원가입 입력 검증", () => {
  it("유효한 입력은 성공한다", () => {
    const result = signupSchema.safeParse({
      email: "test@example.com",
      password: "password123",
      name: "테스트",
    });

    expect(result.success).toBe(true);
  });

  it("잘못된 이메일은 실패한다", () => {
    const result = signupSchema.safeParse({
      email: "invalid-email",
      password: "password123",
      name: "테스트",
    });

    expect(result.success).toBe(false);
    if (!result.success) {
      expect(result.error.issues[0].message).toBe("유효한 이메일을 입력해주세요");
    }
  });

  it("6자 미만 비밀번호는 실패한다", () => {
    const result = signupSchema.safeParse({
      email: "test@example.com",
      password: "12345",
      name: "테스트",
    });

    expect(result.success).toBe(false);
    if (!result.success) {
      expect(result.error.issues[0].message).toBe("비밀번호는 최소 6자 이상이어야 합니다");
    }
  });

  it("빈 이름은 실패한다", () => {
    const result = signupSchema.safeParse({
      email: "test@example.com",
      password: "password123",
      name: "",
    });

    expect(result.success).toBe(false);
    if (!result.success) {
      expect(result.error.issues[0].message).toBe("이름을 입력해주세요");
    }
  });
});

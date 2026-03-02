import { type Page } from "@playwright/test";

/**
 * 로그인 헬퍼 — /auth/signin 페이지에서 이메일/비밀번호로 로그인
 * 데모 비밀번호는 Supabase Auth에 등록된 값 사용 (로컬 기본: "password123")
 */
export async function login(
  page: Page,
  email: string,
  password = "password123",
) {
  await page.goto("/auth/signin");
  await page.getByLabel("이메일").fill(email);
  await page.getByLabel("비밀번호").fill(password);
  await page.getByRole("button", { name: "로그인" }).click();
  // 로그인 후 메인 페이지로 리다이렉트 대기
  await page.waitForURL("/", { timeout: 10_000 });
}

/** 데모 사용자 정보 (supabase/seed.sql 기준) */
export const DEMO_USERS = {
  admin: { email: "admin@demo.com", name: "관리자 김철수" },
  manager: { email: "manager@demo.com", name: "매니저 이영희" },
  player1: { email: "player1@demo.com", name: "선수 박민수" },
  player2: { email: "player2@demo.com", name: "선수 정수진" },
  player3: { email: "player3@demo.com", name: "선수 최동현" },
} as const;

/** 데모 팀 ID */
export const DEMO_TEAM_ID = "10000000-0000-0000-0000-000000000001";

/** 데모 경기 ID */
export const DEMO_MATCH_IDS = {
  weekendLeague: "20000000-0000-0000-0000-000000000001",
  practiceMatch: "20000000-0000-0000-0000-000000000002",
} as const;

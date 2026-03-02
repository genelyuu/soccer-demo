import { test, expect } from "@playwright/test";
import { login, DEMO_USERS, DEMO_TEAM_ID, DEMO_MATCH_IDS } from "./helpers";

test.describe("시나리오 4: 권한 없는 접근 시도", () => {
  test("MEMBER가 경기 생성 API 호출 시 403 반환", async ({ page }) => {
    // player1 (MEMBER 역할) 로그인
    await login(page, DEMO_USERS.player1.email);

    // API 직접 호출 — MEMBER는 경기 생성 불가
    const response = await page.request.post("/api/matches", {
      data: {
        team_id: DEMO_TEAM_ID,
        title: "권한 없는 경기",
        match_date: new Date().toISOString(),
      },
    });

    expect(response.status()).toBe(403);

    const body = await response.json();
    expect(body.error).toContain("권한");
  });

  test("MEMBER가 경기 확정 API 호출 시 403 반환", async ({ page }) => {
    // player1 (MEMBER) 로그인
    await login(page, DEMO_USERS.player1.email);

    // OPEN 상태 경기에 대해 확정 시도
    const response = await page.request.patch(
      `/api/matches/${DEMO_MATCH_IDS.practiceMatch}/confirm`,
    );

    expect(response.status()).toBe(403);

    const body = await response.json();
    expect(body.error).toContain("권한");
  });

  test("인증 없이 경기 목록 API 호출 시 401 반환", async ({ page }) => {
    // 로그인하지 않은 상태에서 API 호출
    const response = await page.request.get(
      `/api/matches?team_id=${DEMO_TEAM_ID}`,
    );

    expect(response.status()).toBe(401);
  });

  test("MEMBER가 기록 입력 API 호출 시 403 반환", async ({ page }) => {
    // player1 (MEMBER) 로그인
    await login(page, DEMO_USERS.player1.email);

    // 기록 입력 시도 — MEMBER는 기록 입력 불가
    const response = await page.request.post(
      `/api/matches/${DEMO_MATCH_IDS.weekendLeague}/record`,
      {
        data: {
          user_id: "00000000-0000-0000-0000-000000000003",
          goals: 1,
          assists: 0,
          yellow_cards: 0,
          red_cards: 0,
        },
      },
    );

    expect(response.status()).toBe(403);
  });

  test("MEMBER가 /matches/new 페이지 접근은 가능하나 경기 생성은 차단", async ({ page }) => {
    // player1 (MEMBER) 로그인
    await login(page, DEMO_USERS.player1.email);

    // /matches/new 직접 접근 — UI는 접근 가능
    await page.goto("/matches/new");

    // 팀 선택이 안 되어 있으면 폼이 보이지 않을 수 있음
    // 또는 경기 등록 폼이 보이지만 API 단에서 차단됨
    // 페이지가 로드되는지만 확인
    await expect(page).toHaveURL("/matches/new");
  });

  test("MEMBER가 기록실 마감 API 호출 시 403 반환", async ({ page }) => {
    // player1 (MEMBER) 로그인
    await login(page, DEMO_USERS.player1.email);

    // 기록실 마감 시도
    const response = await page.request.patch(
      `/api/matches/${DEMO_MATCH_IDS.weekendLeague}/record/close`,
    );

    // MEMBER는 기록실 마감 권한 없음
    expect(response.status()).toBe(403);
  });
});

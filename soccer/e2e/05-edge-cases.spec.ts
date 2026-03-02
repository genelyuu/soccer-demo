import { test, expect } from "@playwright/test";
import { login, DEMO_USERS, DEMO_MATCH_IDS } from "./helpers";

test.describe("시나리오 5: 에지 케이스 — 중복 확정 멱등성, 마감 후 투표 차단", () => {
  test("이미 확정된 경기를 다시 확정 시도 → 멱등하게 기존 기록실 반환", async ({ page }) => {
    // 매니저로 로그인
    await login(page, DEMO_USERS.manager.email);

    // 첫 번째 확정
    const firstResponse = await page.request.patch(
      `/api/matches/${DEMO_MATCH_IDS.weekendLeague}/confirm`,
    );
    expect(firstResponse.ok()).toBeTruthy();
    const firstBody = await firstResponse.json();

    // 두 번째 확정 (중복)
    const secondResponse = await page.request.patch(
      `/api/matches/${DEMO_MATCH_IDS.weekendLeague}/confirm`,
    );
    expect(secondResponse.ok()).toBeTruthy();
    const secondBody = await secondResponse.json();

    // 기존 기록실이 반환되어야 함
    expect(secondBody.record_room).toBeTruthy();
    expect(secondBody.record_room.id).toBe(firstBody.record_room.id);
  });

  test("CONFIRMED 상태 경기에서 투표 시도 → 409 '투표가 마감되었습니다'", async ({ page }) => {
    // 먼저 매니저로 경기 확정
    await login(page, DEMO_USERS.manager.email);
    await page.request.patch(
      `/api/matches/${DEMO_MATCH_IDS.weekendLeague}/confirm`,
    );

    // 선수로 재로그인
    await login(page, DEMO_USERS.player1.email);

    // 확정된 경기에 투표 시도
    const response = await page.request.patch(
      `/api/matches/${DEMO_MATCH_IDS.weekendLeague}/attendance`,
      {
        data: { status: "ACCEPTED" },
      },
    );

    expect(response.status()).toBe(409);

    const body = await response.json();
    expect(body.error).toContain("마감");
  });

  test("CONFIRMED 상태 경기에서 UI 투표 버튼이 숨겨짐", async ({ page }) => {
    // 매니저로 경기 확정
    await login(page, DEMO_USERS.manager.email);
    await page.request.patch(
      `/api/matches/${DEMO_MATCH_IDS.weekendLeague}/confirm`,
    );

    // 선수로 재로그인 후 경기 상세 확인
    await login(page, DEMO_USERS.player1.email);
    await page.goto(`/matches/${DEMO_MATCH_IDS.weekendLeague}`);

    // CONFIRMED 상태에서는 투표 섹션이 보이지 않아야 함
    await expect(page.getByText("내 출석 투표")).not.toBeVisible();
  });

  test("기록실 CLOSED 후 기록 입력 API 호출 → 409 '기록실이 마감되었습니다'", async ({ page }) => {
    // 매니저로 경기 확정
    await login(page, DEMO_USERS.manager.email);

    // 경기 확정 (이미 확정이면 멱등)
    await page.request.patch(
      `/api/matches/${DEMO_MATCH_IDS.weekendLeague}/confirm`,
    );

    // 기록실 마감
    await page.request.patch(
      `/api/matches/${DEMO_MATCH_IDS.weekendLeague}/record/close`,
    );

    // 마감된 기록실에 기록 입력 시도
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

    expect(response.status()).toBe(409);

    const body = await response.json();
    expect(body.error).toContain("마감");
  });

  test("존재하지 않는 경기 접근 시 에러 표시", async ({ page }) => {
    await login(page, DEMO_USERS.manager.email);

    // 존재하지 않는 UUID로 접근
    await page.goto("/matches/00000000-0000-0000-0000-000000000099");

    // 에러 메시지 또는 404 관련 표시 확인
    await expect(
      page.getByText(/실패|찾을 수 없|존재하지 않|오류/),
    ).toBeVisible({ timeout: 10_000 });
  });

  test("존재하지 않는 경기의 기록실 접근 시 에러 표시", async ({ page }) => {
    await login(page, DEMO_USERS.manager.email);

    // 존재하지 않는 경기의 기록실 접근
    await page.goto("/matches/00000000-0000-0000-0000-000000000099/record");

    // 기록실이 없다는 에러 메시지 확인
    await expect(
      page.getByText(/기록실이 아직 생성되지 않았습니다|실패|오류/),
    ).toBeVisible({ timeout: 10_000 });
  });
});

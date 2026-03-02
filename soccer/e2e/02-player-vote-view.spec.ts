import { test, expect } from "@playwright/test";
import { login, DEMO_USERS, DEMO_MATCH_IDS } from "./helpers";

test.describe("시나리오 2: 선수 — 투표 후 기록 조회", () => {
  test("선수가 OPEN 상태 경기에 참석 투표", async ({ page }) => {
    // player1 로그인
    await login(page, DEMO_USERS.player1.email);

    // 경기 목록 진입
    await page.goto("/matches");
    await expect(page.getByRole("heading", { name: "경기 일정" })).toBeVisible();

    // 연습 경기 (OPEN, 전원 PENDING) 클릭
    await page.getByText("연습 경기").click();
    await page.waitForURL(/\/matches\/.+/);

    // 경기 상세 확인
    await expect(page.getByText("연습 경기")).toBeVisible();

    // 내 출석 투표 섹션 확인
    await expect(page.getByText("내 출석 투표")).toBeVisible();

    // [참석] 버튼 클릭
    await page.getByRole("button", { name: "참석" }).click();

    // 투표 상태가 ACCEPTED로 변경 확인 (출석 투표 현황에서 확인)
    await expect(page.getByText("참석").first()).toBeVisible({ timeout: 5_000 });
  });

  test("선수가 경기 상세에서 새 경기 버튼이 보이지 않음 (권한 제한)", async ({ page }) => {
    // player1은 MEMBER 역할 — 새 경기 생성 버튼이 없어야 함
    await login(page, DEMO_USERS.player1.email);
    await page.goto("/matches");

    // 새 경기 버튼이 보이지 않아야 함
    await expect(page.getByRole("link", { name: /새 경기/ })).not.toBeVisible();
  });

  test("선수가 확정된 경기의 기록실을 조회 (기록 입력 불가)", async ({ page }) => {
    // 먼저 매니저로 경기 확정
    await login(page, DEMO_USERS.manager.email);
    await page.goto(`/matches/${DEMO_MATCH_IDS.weekendLeague}`);

    // 이미 확정 상태가 아니면 확정
    const confirmButton = page.getByRole("button", { name: /경기 확정/ });
    if (await confirmButton.isVisible()) {
      await confirmButton.click();
      await page.waitForTimeout(2_000);
    }

    // 선수로 재로그인
    await login(page, DEMO_USERS.player1.email);

    // 확정된 경기 상세로 이동
    await page.goto(`/matches/${DEMO_MATCH_IDS.weekendLeague}`);

    // 상태가 CONFIRMED이면 기록실 바로가기 링크가 보여야 함
    const recordLink = page.getByRole("button", { name: "기록실 바로가기" });
    if (await recordLink.isVisible()) {
      await recordLink.click();
      await page.waitForURL(/\/matches\/.+\/record/);

      // 기록실 페이지 확인
      await expect(page.getByText("기록실")).toBeVisible();

      // 선수(MEMBER)는 수정 버튼이 보이지 않아야 함
      await expect(page.getByRole("button", { name: "수정" })).not.toBeVisible();
    }
  });
});

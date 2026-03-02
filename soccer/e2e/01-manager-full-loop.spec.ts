import { test, expect } from "@playwright/test";
import { login, DEMO_USERS } from "./helpers";

test.describe("시나리오 1: 운영자 전체 루프 — 경기 생성부터 기록 완료까지", () => {
  test.beforeEach(async ({ page }) => {
    // MANAGER 역할로 로그인
    await login(page, DEMO_USERS.manager.email);
  });

  test("경기 목록 페이지 진입 후 새 경기 생성 버튼 확인", async ({ page }) => {
    await page.goto("/matches");
    await expect(page.getByRole("heading", { name: "경기 일정" })).toBeVisible();
    await expect(page.getByRole("link", { name: /새 경기/ })).toBeVisible();
  });

  test("새 경기 생성 → 목록 리다이렉트 → 상세 → 확정 → 기록실", async ({ page }) => {
    // 1. 경기 목록 진입
    await page.goto("/matches");

    // 2. [새 경기] 클릭 → /matches/new
    await page.getByRole("link", { name: /새 경기/ }).click();
    await page.waitForURL("/matches/new");

    // 3. 경기 정보 입력
    await page.getByLabel("경기명 *").fill("E2E 테스트 경기");
    await page.getByLabel("경기 일시 *").fill("2026-03-01T14:00");
    await page.getByLabel("장소").fill("잠실 운동장");
    await page.getByLabel("상대팀").fill("FC 테스트");

    // 4. [경기 등록] 클릭
    await page.getByRole("button", { name: "경기 등록" }).click();

    // 5. /matches로 리다이렉트 확인
    await page.waitForURL("/matches", { timeout: 10_000 });

    // 6. 새 경기 카드 확인
    await expect(page.getByText("E2E 테스트 경기")).toBeVisible();

    // 7. 경기 카드 클릭 → 상세 페이지
    await page.getByText("E2E 테스트 경기").click();
    await page.waitForURL(/\/matches\/.+/);

    // 8. 출석 투표 현황 확인
    await expect(page.getByText("출석 투표 현황")).toBeVisible();

    // 9. [경기 확정] 클릭
    await page.getByRole("button", { name: /경기 확정/ }).click();

    // 10. 상태가 CONFIRMED로 변경 확인
    await expect(page.getByText("확정")).toBeVisible({ timeout: 5_000 });

    // 11. [기록실 바로가기] 클릭
    await page.getByRole("button", { name: "기록실 바로가기" }).click();
    await page.waitForURL(/\/matches\/.+\/record/);

    // 12. 기록실 페이지 확인
    await expect(page.getByText("기록실")).toBeVisible();
    await expect(page.getByText("입력 가능")).toBeVisible();
  });

  test("기록실에서 선수별 스탯 입력 및 저장", async ({ page }) => {
    // 기존 OPEN 상태의 데모 경기를 확정하고 기록 입력 테스트
    // (시드 데이터의 주말 리그전 사용)
    const matchId = "20000000-0000-0000-0000-000000000001";

    // 경기 상세로 이동
    await page.goto(`/matches/${matchId}`);
    await expect(page.getByText("주말 리그전")).toBeVisible();

    // OPEN 상태면 확정 버튼 클릭
    const confirmButton = page.getByRole("button", { name: /경기 확정/ });
    if (await confirmButton.isVisible()) {
      await confirmButton.click();
      await expect(page.getByText("확정")).toBeVisible({ timeout: 5_000 });
    }

    // 기록실 바로가기
    await page.getByRole("button", { name: "기록실 바로가기" }).click();
    await page.waitForURL(/\/matches\/.+\/record/);

    // 기록실 페이지에서 테이블 확인
    await expect(page.getByText("기록실")).toBeVisible();

    // 선수 기록에 수정 버튼이 있으면 클릭
    const editButton = page.getByRole("button", { name: "수정" }).first();
    if (await editButton.isVisible()) {
      await editButton.click();

      // 기록 입력 폼
      await expect(page.getByText("기록 입력")).toBeVisible();

      // 득점, 어시스트 입력
      await page.getByLabel("득점").fill("2");
      await page.getByLabel("어시스트").fill("1");

      // 저장
      await page.getByRole("button", { name: "저장" }).click();

      // 저장 성공 확인 (폼이 닫히고 테이블에 반영)
      await expect(page.getByText("기록 입력")).not.toBeVisible({ timeout: 5_000 });
    }
  });
});

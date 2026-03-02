import { test, expect } from "@playwright/test";

test.describe("시나리오 3: 회원가입 → 팀 가입", () => {
  test("회원가입 페이지 접근 및 폼 확인", async ({ page }) => {
    await page.goto("/auth/signup");

    // 회원가입 폼 확인
    await expect(page.getByRole("heading", { name: "회원가입" })).toBeVisible();
    await expect(page.getByLabel("이름")).toBeVisible();
    await expect(page.getByLabel("이메일")).toBeVisible();
    await expect(page.getByLabel("비밀번호")).toBeVisible();
    await expect(page.getByRole("button", { name: "회원가입" })).toBeVisible();
  });

  test("회원가입 → 자동 로그인 → 메인 리다이렉트", async ({ page }) => {
    // 고유 이메일 생성 (중복 방지)
    const uniqueEmail = `e2e-test-${Date.now()}@test.com`;

    await page.goto("/auth/signup");

    // 폼 입력
    await page.getByLabel("이름").fill("새 선수");
    await page.getByLabel("이메일").fill(uniqueEmail);
    await page.getByLabel("비밀번호").fill("password123");

    // [회원가입] 클릭
    await page.getByRole("button", { name: "회원가입" }).click();

    // 자동 로그인 후 메인 페이지로 리다이렉트
    await page.waitForURL("/", { timeout: 15_000 });
  });

  test("신규 사용자가 팀 페이지 접근 시 '소속된 팀이 없습니다' 메시지", async ({ page }) => {
    // 새 계정으로 회원가입
    const uniqueEmail = `e2e-team-${Date.now()}@test.com`;

    await page.goto("/auth/signup");
    await page.getByLabel("이름").fill("팀 없는 유저");
    await page.getByLabel("이메일").fill(uniqueEmail);
    await page.getByLabel("비밀번호").fill("password123");
    await page.getByRole("button", { name: "회원가입" }).click();
    await page.waitForURL("/", { timeout: 15_000 });

    // /team 진입
    await page.goto("/team");

    // 소속 팀이 없다는 메시지 확인
    await expect(page.getByText("소속된 팀이 없습니다")).toBeVisible({ timeout: 10_000 });
  });

  test("유효하지 않은 이메일로 회원가입 시도 → HTML5 유효성 검증", async ({ page }) => {
    await page.goto("/auth/signup");

    await page.getByLabel("이름").fill("테스트");
    await page.getByLabel("이메일").fill("invalid-email");
    await page.getByLabel("비밀번호").fill("password123");
    await page.getByRole("button", { name: "회원가입" }).click();

    // HTML5 email 유효성 검사로 인해 제출이 막혀야 함
    // 여전히 회원가입 페이지에 머물러야 함
    await expect(page).toHaveURL(/\/auth\/signup/);
  });

  test("짧은 비밀번호로 회원가입 시도 → 유효성 검증", async ({ page }) => {
    await page.goto("/auth/signup");

    await page.getByLabel("이름").fill("테스트");
    await page.getByLabel("이메일").fill("short-pw@test.com");
    await page.getByLabel("비밀번호").fill("123");
    await page.getByRole("button", { name: "회원가입" }).click();

    // 최소 6자 minLength 유효성 검사로 인해 제출이 막혀야 함
    await expect(page).toHaveURL(/\/auth\/signup/);
  });

  test("로그인 페이지에서 회원가입 링크 이동", async ({ page }) => {
    await page.goto("/auth/signin");

    // 회원가입 링크 클릭
    await page.getByRole("link", { name: "회원가입" }).click();
    await page.waitForURL("/auth/signup");

    await expect(page.getByRole("heading", { name: "회원가입" })).toBeVisible();
  });
});

# 테스트 전략 문서 (Task 0018)

> 근거: `vitest.config.ts`, `package.json:10-12`

## 테스트 피라미드

```
         /\
        /  \     E2E (Playwright — 미구현)
       /    \    → 핵심 운영 루프 5개 시나리오
      /------\
     /        \   통합 테스트 (API 레벨)
    /          \  → 핵심 루프 3-5개
   /------------\
  /              \  단위 테스트 (Vitest)
 /                \ → 도메인 로직, 검증, 상수
/------------------\
```

## 테스트 도구

| 도구 | 용도 | 근거 |
|------|------|------|
| Vitest | 단위/통합 테스트 러너 | `package.json:65`, `vitest.config.ts` |
| @testing-library/react | 컴포넌트 테스트 | `package.json:53` |
| @testing-library/jest-dom | DOM assertion | `package.json:52` |
| jsdom | 브라우저 환경 시뮬레이션 | `vitest.config.ts:5` |
| [UNKNOWN] Playwright | E2E 테스트 | 미설치, Task 0020에서 결정 |

## 테스트 실행 명령

```bash
npm run test              # 전체 테스트 실행
npm run test:watch        # 감시 모드
npm run test:coverage     # 커버리지 리포트
npx vitest run src/features/match  # 특정 기능 테스트
```

## 현재 테스트 현황

| 테스트 파일 | 테스트 수 | 카테고리 |
|------------|---------|---------|
| `src/test/smoke.test.ts` | 1 | 스모크 |
| `src/features/auth/__tests__/signup-validation.test.ts` | 4 | 단위 (검증) |
| `src/features/auth/__tests__/auth-options.test.ts` | 3 | 단위 (설정) |
| `src/features/match/__tests__/match-constants.test.ts` | 4 | 단위 (상수) |
| `src/features/match/__tests__/match-status-transition.test.ts` | 7 | 단위 (도메인) |
| `src/features/attendance/__tests__/attendance-status.test.ts` | 3 | 단위 (도메인) |
| **합계** | **22** | |

## 커버리지 기준 (현실적)

| 영역 | 최소 기준 | 이상적 |
|------|---------|-------|
| 도메인 로직 (상태 전이, 검증) | 80% | 100% |
| API 라우트 | [UNKNOWN — 통합 테스트로 커버] | - |
| UI 컴포넌트 | 핵심 흐름 1개 이상 | - |
| 전체 | 측정 후 결정 | - |

## TDD 원칙

1. **실패 테스트 작성** — 구현 전에 기대 동작을 테스트로 명세
2. **성공 테스트** — 최소한의 코드로 테스트 통과
3. **리팩터** — 테스트 보호 하에 구조 개선
- 근거: `.claude/teams/config.json:38`

## 검증 체크리스트
- [ ] `npm run test` 실행 시 모든 테스트가 통과하는가?
- [ ] 핵심 유스케이스(경기 생성→투표→확정→기록)가 테스트로 보호되는가?
- [ ] 새 기능 추가 시 관련 테스트가 함께 작성되었는가?

# ADR-002: MVP 완성 — 팀 병렬 진행 및 구현 결정

## 상태
승인

## 맥락
핵심 운영 루프(일정→출석→확정→기록)의 기능 구현은 완료되었으나, MVP 출시를 가로막는 4개 크리티컬 블로커가 존재했다:
1. 팀 ID 하드코딩 (DEMO_TEAM_ID)
2. 네비게이션/레이아웃 부재
3. 홈 페이지 미구현 (EasyNext 보일러플레이트 상태)
4. 기록실 마감(Close) 기능 미구현

## 결정

### 1. 3트랙 병렬 진행
팀 에이전트를 3개 트랙으로 분리하여 병렬 작업을 진행했다.

| 트랙 | 담당 | 태스크 | 근거 |
|------|------|--------|------|
| A. Backend | backend-api | 기록실 마감 엔드포인트 | 독립 API 추가, 프론트 의존 없음 |
| B. Frontend | frontend-ui | 네비게이션, 홈, 팀선택기, 역할 UI | 순차 의존 (헤더→홈→역할) |
| C. Design | design-system | 토큰/모션 적용 | 헤더 완료 후 Phase B 진행 |

- 근거: `.claude/teams/config.json` 에이전트 역할 분리
- 의존관계: Task #3(홈)→#2(헤더), Task #5(역할UI)→#4(팀선택기), Task #6(모션)→#2(헤더)

### 2. 기록실 마감 엔드포인트 설계
- **방식**: `PATCH /api/matches/[id]/record/close`
- **전이**: record_room.status OPEN→CLOSED + match.status CONFIRMED→COMPLETED
- **선택 근거**: 기존 confirm 엔드포인트와 동일 패턴 유지, 멱등성 보장
- 근거: `src/app/api/matches/[id]/confirm/route.ts` 패턴, `docs/api/DB_SCHEMA.md:91-110`

### 3. 팀 선택기 — Zustand + localStorage
- **방식**: Zustand 스토어 + persist 미들웨어 (localStorage)
- **선택 근거**: React Query(서버 상태)와 Zustand(클라이언트 상태) 분리 원칙 유지
- **대안 검토**: URL 파라미터 방식 — 새로고침 시 유지되나, 모든 링크에 teamId 전파 필요하여 복잡도 높음. 기각.
- 근거: `src/lib/stores/team-store.ts`, `CLAUDE.md` (State: Zustand 클라이언트)

### 4. 모션 시스템 4패턴 표준화
- **패턴**: page-transition, stagger-list, modal-motion, toast-motion
- **원칙**: 모션 유틸 컴포넌트를 통해서만 적용, 산재 애니메이션 금지
- **접근성**: prefers-reduced-motion 전역 대응 (CSS + JS 이중 체크)
- 근거: `docs/design/MOTION.md`, `.claude/teams/config.json:74` (motion-system 에이전트 정의)

### 5. 역할 기반 UI 처리 전략
- **이중 방어**: API 서버에서 권한 차단(403) + 클라이언트에서 버튼 숨김/비활성화
- **선택 근거**: API 차단만으로는 UX 불량, UI 숨김만으로는 보안 취약. 이중 적용이 MVP 수준의 최선.
- **미적용**: 미들웨어 레벨 라우트 가드 (MVP 이후 검토 — `docs/quality/RISK_REGISTER.md:R-006`)
- 근거: `docs/04_SECURITY_AND_ROLES/RBAC_MATRIX.md`

## 결과

### 생성/수정된 파일

**Backend (Task #1)**:
- `src/app/api/matches/[id]/record/close/route.ts` — 기록실 마감 엔드포인트
- `src/features/record/__tests__/record-room-close.test.ts` — 단위 테스트 8개

**Frontend (Task #2, #3, #4, #5)**:
- `src/components/layout/header.tsx` — 공통 헤더
- `src/components/layout/team-selector.tsx` — 팀 선택 드롭다운
- `src/lib/stores/team-store.ts` — Zustand 팀 스토어
- `src/app/layout.tsx` — 레이아웃 수정
- `src/app/page.tsx` — 홈 대시보드
- `src/app/matches/page.tsx` — DEMO_TEAM_ID 제거
- `src/app/matches/new/page.tsx` — DEMO_TEAM_ID 제거

**Design (Task #6)**:
- `src/components/motion/page-transition.tsx`
- `src/components/motion/stagger-list.tsx`
- `src/components/motion/modal-motion.tsx`
- `src/components/motion/toast-motion.tsx`
- `src/components/motion/index.ts`
- `src/app/globals.css` — prefers-reduced-motion 추가

### 검증
- `npm run typecheck` — 통과
- `npm run test` — 73개 테스트 전체 통과 (신규 8개 포함)

## [UNKNOWN]
- 프로덕션 환경에서의 Zustand persist 동작 (SSR hydration mismatch 가능성)
- 모션 성능 — 저사양 모바일 기기에서의 프레임 드롭 여부
- 팀 전환 시 경기 목록 캐시 무효화 타이밍

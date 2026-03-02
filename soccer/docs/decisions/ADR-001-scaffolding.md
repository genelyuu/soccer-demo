# ADR-001: EasyNext.js 기반 프로젝트 스캐폴딩

## 상태
승인

## 맥락
축구 동호회 운영 루프 MVP를 위한 프로젝트 초기 구조를 결정해야 한다.

## 결정
EasyNext CLI v0.1.39 (`@easynext/cli`)를 사용하여 프로젝트를 스캐폴딩했다.

### 선택 근거
- **EasyNext.js**: Next.js App Router + shadcn/ui + Tailwind CSS + framer-motion + Supabase를 사전 구성
  - 근거: 태스크 정의 `.claude/tasks/easynext-football-mvp/0001.json`
- **Supabase**: BaaS로 PostgreSQL + RLS + Auth 제공, 별도 백엔드 서버 불필요
  - 근거: `.cursor/rules/global.mdc:11` — Supabase를 BaaS로 권장
- **NextAuth.js (v4)**: JWT 전략 기반 인증
  - 근거: `src/lib/auth.ts:29-31`
- **Vitest + Testing Library**: TDD 요구사항 충족
  - 근거: `.claude/teams/config.json:86` — TDD 품질 게이트 에이전트 정의
- **Next.js 15** (16이 아닌): EasyNext 템플릿 호환성 유지
  - 근거: Next.js 16에서 `eslint` 옵션이 NextConfig에서 제거됨, `next.config.ts:5`

### 기술 스택 요약
| 레이어 | 선택 | 근거 파일 |
|--------|------|----------|
| 프레임워크 | Next.js 15 (App Router) | `package.json:37` |
| UI | shadcn/ui + Radix | `package.json:13-26` |
| 스타일 | Tailwind CSS 3.4 | `tailwind.config.ts` |
| 상태 | Zustand + React Query | `package.json:46,28` |
| 백엔드 | Supabase | `src/lib/supabase/` |
| 인증 | NextAuth.js v4 (JWT) | `src/lib/auth.ts` |
| 테스트 | Vitest + Testing Library | `vitest.config.ts` |
| 모션 | framer-motion | `package.json:35` |

## 결과
- `npm run dev` → 로컬 서버 1분 내 실행 확인
- `npm run build` → 빌드 성공
- `npm run test` → 스모크 테스트 통과
- `npm run typecheck` → 타입 체크 통과

## [UNKNOWN]
- 프로덕션 Supabase 프로젝트 설정 상세
- OAuth 프로바이더 (카카오 등) 구체적 설정
- Vercel 배포 파이프라인 상세

# 배포 및 로컬 실행 가이드

> 근거: `package.json:5-9` (스크립트 정의), `next.config.ts` (빌드 설정)

## 로컬 개발 서버 실행 (1분 이내)

```bash
# 1. 의존성 설치
npm install

# 2. 환경변수 설정
cp .env.example .env.local
# .env.local 파일을 열어 Supabase URL/Key, NextAuth 시크릿 등을 설정

# 3. 개발 서버 실행 (Turbopack 사용)
npm run dev
# → http://localhost:3000
```

## 빌드 및 프로덕션 실행

```bash
# 빌드
npm run build

# 프로덕션 서버 실행
npm start
```

## 주요 명령어

| 명령어 | 설명 | 근거 |
|--------|------|------|
| `npm run dev` | 개발 서버 (Turbopack) | `package.json:6` |
| `npm run build` | 프로덕션 빌드 | `package.json:7` |
| `npm start` | 프로덕션 서버 | `package.json:8` |
| `npm run lint` | ESLint 린트 | `package.json:9` |
| `npm run test` | Vitest 테스트 실행 | `package.json:10` |
| `npm run test:watch` | 테스트 감시 모드 | `package.json:11` |
| `npm run typecheck` | TypeScript 타입 체크 | `package.json:13` |

## 기술 스택

| 항목 | 선택 | 버전 | 근거 |
|------|------|------|------|
| 프레임워크 | Next.js (App Router) | ^16 | `package.json:32` |
| 스캐폴딩 | EasyNext CLI | v0.1.39 | 프로젝트 초기화 도구 |
| UI 컴포넌트 | shadcn/ui + Radix | - | `package.json:13-22` |
| 스타일링 | Tailwind CSS | ^3.4 | `package.json:58` |
| 상태 관리 | Zustand (클라이언트), React Query (서버) | ^4, ^5 | `package.json:41,23` |
| 폼 | react-hook-form + zod | ^7, ^3 | `package.json:36,40` |
| 애니메이션 | framer-motion | ^11 | `package.json:30` |
| 백엔드 | Supabase (BaaS) | - | `package.json:42` |
| 인증 | NextAuth.js (JWT) | ^4 | `package.json:43` |
| 테스트 | Vitest + Testing Library | ^4, ^16 | `package.json:61,49` |
| 패키지 매니저 | npm | 11.7+ | `.cursor/rules/global.mdc:168` |

## 배포 대상

- **MVP 단계**: Vercel (Next.js 네이티브 지원)
- **DB**: Supabase (호스팅형 PostgreSQL)
- [UNKNOWN] 프로덕션 배포 파이프라인 상세 (MVP 이후 결정)

## 검증 체크리스트

- [ ] `npm install` 후 에러 없이 완료되는가?
- [ ] `npm run dev` 후 http://localhost:3000 접속 가능한가?
- [ ] `npm run build` 에러 없이 완료되는가?
- [ ] `npm run test` 실행 가능한가?
- [ ] `npm run typecheck` 에러 없이 통과하는가?

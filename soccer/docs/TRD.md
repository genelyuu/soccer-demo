# 기술 요구사항 문서 (TRD)

> 축구 동호회 운영 루프 MVP
> 최종 업데이트: 2026-02-11
> 근거: 코드베이스 전체 분석 기반

---

## 1. 시스템 개요

### 1.1 프로젝트 목적

축구 동호회의 핵심 운영 루프를 디지털화하여 **일정 생성 → 출석/투표 → 경기 확정 → 기록 입력** 4단계를 웹 애플리케이션으로 제공한다.

### 1.2 대상 사용자

| 페르소나 | 설명 | 주요 행동 |
|---------|------|----------|
| 운영자 (ADMIN/MANAGER) | 동호회 관리자 | 경기 생성, 출석 확인, 확정, 기록 관리 |
| 선수 (MEMBER) | 일반 회원 | 출석 투표, 기록 조회 |
| 게스트 (GUEST) | 비활성 회원 | 조회만 가능 |

### 1.3 핵심 운영 루프

```
일정 생성(Schedule) → 출석/투표(Attendance) → 경기 확정(Confirm) → 기록 입력(Record)
```

- 경기 생성 시 → 팀 멤버 전원 Attendance 자동 생성
- 경기 확정 시 → RecordRoom 자동 생성 (멱등성 보장)

---

## 2. 기술 스택

### 2.1 프론트엔드

| 기술 | 버전 | 용도 |
|------|------|------|
| Next.js | 15.5.x | App Router, Turbopack, SSR/CSR |
| React | 19.0.0 | UI 렌더링 |
| TypeScript | 5.x | 타입 안전성 |
| Tailwind CSS | 3.4.x | 유틸리티 퍼스트 스타일링 |
| shadcn/ui | - | 컴포넌트 라이브러리 (Radix UI 기반) |
| Framer Motion | 11.x | 애니메이션 |
| Zustand | 4.x | 클라이언트 상태 관리 (팀 선택 등) |
| React Query | 5.x | 서버 상태 관리 (캐시, 뮤테이션) |
| React Hook Form | 7.x | 폼 상태 관리 |
| Zod | 3.x | 스키마 검증 |

### 2.2 백엔드

| 기술 | 버전 | 용도 |
|------|------|------|
| Next.js API Routes | 15.5.x | REST API 엔드포인트 |
| NextAuth.js | 4.24.x | 인증 (JWT 전략) |
| Supabase | - | PostgreSQL + Auth + RLS |

### 2.3 유틸리티

| 기술 | 용도 |
|------|------|
| date-fns 4.x | 날짜 처리 |
| ts-pattern 5.x | 패턴 매칭 |
| es-toolkit 1.x | 유틸리티 함수 |
| lucide-react | 아이콘 |
| axios | HTTP 클라이언트 |

### 2.4 테스트

| 기술 | 용도 |
|------|------|
| Vitest 4.x | 단위/통합 테스트 |
| @testing-library/react 16.x | 컴포넌트 테스트 |
| Playwright 1.58.x | E2E 테스트 |

### 2.5 패키지 관리자

- **npm** (npm only 정책)

---

## 3. 아키텍처 설계

### 3.1 전체 아키텍처

```
┌─────────────────────────────────────────────────────────┐
│                    클라이언트 (브라우저)                     │
│  ┌───────────┐  ┌──────────┐  ┌──────────┐              │
│  │ React     │  │ Zustand  │  │ React    │              │
│  │ Components│  │ Store    │  │ Query    │              │
│  └─────┬─────┘  └────┬─────┘  └────┬─────┘              │
│        │              │              │                    │
│        └──────────────┴──────────────┘                    │
│                       │ HTTP (axios)                      │
└───────────────────────┼───────────────────────────────────┘
                        │
┌───────────────────────┼───────────────────────────────────┐
│              Next.js API Routes (서버)                      │
│  ┌────────────────────┼────────────────────────────────┐  │
│  │    NextAuth.js (JWT 인증)                            │  │
│  │    ┌───────────────┼──────────────────────────┐     │  │
│  │    │       API Route Handlers                  │     │  │
│  │    │   (인증 확인 → 권한 확인 → 비즈니스 로직)      │     │  │
│  │    └───────────────┼──────────────────────────┘     │  │
│  └────────────────────┼────────────────────────────────┘  │
│                       │ Supabase Client (Service Role)     │
└───────────────────────┼───────────────────────────────────┘
                        │
┌───────────────────────┼───────────────────────────────────┐
│                  Supabase (PostgreSQL)                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                │
│  │   Auth   │  │  Tables  │  │   RLS    │                │
│  │  (인증)   │  │  (데이터) │  │  (정책)   │                │
│  └──────────┘  └──────────┘  └──────────┘                │
└───────────────────────────────────────────────────────────┘
```

### 3.2 디렉토리 구조

```
src/
├── app/                          # Next.js App Router
│   ├── layout.tsx                # 루트 레이아웃 (Providers 포함)
│   ├── providers.tsx             # QueryClient, Theme, Session
│   ├── page.tsx                  # 홈/대시보드
│   ├── auth/                     # 인증 페이지
│   ├── matches/                  # 경기 페이지
│   ├── team/                     # 팀 페이지
│   ├── profile/                  # 프로필 페이지
│   └── api/                      # API 라우트
│       ├── auth/                 # 인증 API
│       ├── matches/              # 경기 API
│       ├── teams/                # 팀 API
│       └── users/                # 사용자 API
├── features/                     # 기능 모듈 (Feature-based)
│   ├── auth/                     # 인증
│   ├── match/                    # 경기
│   ├── attendance/               # 출석/투표
│   ├── record/                   # 기록실
│   └── team/                     # 팀/멤버
├── components/                   # 공유 컴포넌트
│   ├── ui/                       # shadcn/ui
│   ├── layout/                   # 레이아웃 (헤더, 팀 셀렉터)
│   └── motion/                   # 모션 래퍼
├── lib/                          # 공유 라이브러리
│   ├── auth.ts                   # NextAuth 설정
│   ├── types.ts                  # 도메인 타입
│   ├── supabase/                 # Supabase 클라이언트
│   └── stores/                   # Zustand 스토어
└── hooks/                        # 공유 훅
```

### 3.3 Feature 모듈 구조

각 기능 모듈(`src/features/[name]/`)은 다음 구조를 따른다:

```
feature/
├── api.ts              # HTTP API 호출 함수
├── hooks/              # React 훅 (React Query 래퍼)
├── components/         # UI 컴포넌트
├── lib/                # 비즈니스 로직 (authorization 등)
├── constants/          # 상수 (라벨, 컬러 등)
└── __tests__/          # 테스트
```

### 3.4 상태 관리 전략

| 구분 | 도구 | 용도 | 캐시 키 패턴 |
|------|------|------|-------------|
| 서버 상태 | React Query v5 | API 데이터 페칭, 캐시, 뮤테이션 | `["teams"]`, `["matches", teamId]`, `["match", id]` |
| 클라이언트 상태 | Zustand | 팀 선택 상태 | localStorage `"team-store"` 영속화 |
| 폼 상태 | React Hook Form | 입력 폼 관리 | - |

**React Query 뮤테이션 전략:**
- `useCreateMatch()` → `["matches", team_id]` 무효화
- `useUpdateMatch()` → `["match", id]` + `["matches"]` 무효화
- `useAddMember()` → 커스텀 onSuccess 콜백

**Zustand 스토어:**
- `selectedTeamId`: 현재 선택된 팀 ID (null 가능)
- `persist` 미들웨어로 localStorage 영속화
- `_isHydrated` 플래그로 SSR/CSR 불일치 방지

---

## 4. 데이터베이스 설계

### 4.1 엔터티 관계도 (ERD)

```
Users ──1:N──→ Team_Members ──N:1──→ Teams
  │                                     │
  ├──1:N──→ Matches ←──N:1─────────────┘
  │            │
  │            ├──1:N──→ Attendances ←──N:1── Users
  │            │
  │            └──1:1──→ Record_Rooms
  │                          │
  │                          └──1:N──→ Match_Records ←──N:1── Users
  │
  └── (created_by 참조)
```

### 4.2 테이블 명세

#### users

| 필드 | 타입 | 제약 | 설명 |
|------|------|------|------|
| id | UUID | PK, gen_random_uuid() | 사용자 고유 ID |
| email | TEXT | UNIQUE, NOT NULL | 로그인 이메일 |
| name | TEXT | NOT NULL | 표시 이름 |
| avatar_url | TEXT | nullable | 프로필 이미지 URL |
| created_at | TIMESTAMPTZ | default now() | 생성 시각 |
| updated_at | TIMESTAMPTZ | default now() | 수정 시각 |

- 인덱스: `idx_users_email` (email)

#### teams

| 필드 | 타입 | 제약 | 설명 |
|------|------|------|------|
| id | UUID | PK | 팀 고유 ID |
| name | TEXT | NOT NULL | 팀명 |
| description | TEXT | nullable | 팀 설명 |
| logo_url | TEXT | nullable | 팀 로고 URL |
| created_by | UUID | FK → users(id) | 생성자 |
| created_at | TIMESTAMPTZ | default now() | |
| updated_at | TIMESTAMPTZ | default now() | |

#### team_members

| 필드 | 타입 | 제약 | 설명 |
|------|------|------|------|
| id | UUID | PK | |
| team_id | UUID | FK → teams(id) | 소속 팀 |
| user_id | UUID | FK → users(id) | 소속 사용자 |
| role | team_role | ENUM | 역할 |
| joined_at | TIMESTAMPTZ | default now() | 가입 시각 |

- UNIQUE(team_id, user_id) — 한 팀에 동일 사용자 중복 불가
- 인덱스: `idx_team_members_team`, `idx_team_members_user`

#### matches

| 필드 | 타입 | 제약 | 설명 |
|------|------|------|------|
| id | UUID | PK | |
| team_id | UUID | FK → teams(id) | 소속 팀 |
| title | TEXT | NOT NULL | 경기명 |
| description | TEXT | nullable | 경기 설명 |
| match_date | TIMESTAMPTZ | NOT NULL | 경기 일시 |
| location | TEXT | nullable | 장소 |
| opponent | TEXT | nullable | 상대팀명 |
| status | match_status | ENUM | 경기 상태 |
| created_by | UUID | FK → users(id) | 생성자 |
| confirmed_at | TIMESTAMPTZ | nullable | 확정 시각 |
| completed_at | TIMESTAMPTZ | nullable | 완료 시각 |
| created_at | TIMESTAMPTZ | default now() | |
| updated_at | TIMESTAMPTZ | default now() | |

- 인덱스: `idx_matches_team`, `idx_matches_status`, `idx_matches_date`

#### attendances

| 필드 | 타입 | 제약 | 설명 |
|------|------|------|------|
| id | UUID | PK | |
| match_id | UUID | FK → matches(id) | 소속 경기 |
| user_id | UUID | FK → users(id) | 투표자 |
| status | attendance_status | ENUM | 투표 상태 |
| voted_at | TIMESTAMPTZ | nullable | 투표 시각 |
| created_at | TIMESTAMPTZ | default now() | |
| updated_at | TIMESTAMPTZ | default now() | |

- UNIQUE(match_id, user_id) — 경기당 1인 1투표
- 인덱스: `idx_attendances_match`, `idx_attendances_user`

#### record_rooms

| 필드 | 타입 | 제약 | 설명 |
|------|------|------|------|
| id | UUID | PK | |
| match_id | UUID | FK → matches(id), **UNIQUE** | 1경기 1기록실 |
| status | record_room_status | ENUM | 기록실 상태 |
| created_at | TIMESTAMPTZ | default now() | |
| closed_at | TIMESTAMPTZ | nullable | 마감 시각 |

- match_id UNIQUE — 중복 확정 시 INSERT 실패로 멱등성 보장

#### match_records

| 필드 | 타입 | 제약 | 설명 |
|------|------|------|------|
| id | UUID | PK | |
| record_room_id | UUID | FK → record_rooms(id) | 소속 기록실 |
| user_id | UUID | FK → users(id) | 선수 |
| goals | INT | default 0 | 득점 |
| assists | INT | default 0 | 어시스트 |
| yellow_cards | INT | default 0 | 경고 |
| red_cards | INT | default 0 | 퇴장 |
| memo | TEXT | nullable | 메모 |
| created_at | TIMESTAMPTZ | default now() | |
| updated_at | TIMESTAMPTZ | default now() | |

- UNIQUE(record_room_id, user_id) — 기록실당 선수당 1개 레코드
- 인덱스: `idx_match_records_room`, `idx_match_records_user`

### 4.3 ENUM 타입

| 이름 | 값 |
|------|---|
| team_role | `ADMIN`, `MANAGER`, `MEMBER`, `GUEST` |
| match_status | `OPEN`, `CONFIRMED`, `COMPLETED`, `CANCELLED` |
| attendance_status | `PENDING`, `ACCEPTED`, `DECLINED`, `MAYBE` |
| record_room_status | `OPEN`, `CLOSED` |

### 4.4 RLS (Row Level Security) 정책

#### 읽기 정책

| 테이블 | 정책 | 조건 |
|--------|------|------|
| users | users_read_own | 자기 정보만 조회 |
| teams | teams_read_member | 소속 팀만 조회 |
| team_members | team_members_read | 소속 팀 멤버만 조회 |
| matches | matches_read_team | 소속 팀 경기만 조회 |
| attendances | attendances_read_team | 소속 팀 경기 투표만 조회 |
| record_rooms | record_rooms_read | 소속 팀 기록실만 조회 |
| match_records | match_records_read | 소속 팀 기록만 조회 |

#### 쓰기 정책

| 테이블 | INSERT | UPDATE | DELETE |
|--------|--------|--------|--------|
| users | 자기 자신 | 자기 자신 | - |
| teams | 인증된 사용자 | ADMIN | ADMIN |
| team_members | ADMIN/MANAGER | ADMIN | ADMIN |
| matches | ADMIN/MANAGER | ADMIN/MANAGER | ADMIN |
| attendances | ADMIN/MANAGER | 자기 투표만 | - |
| record_rooms | ADMIN/MANAGER | ADMIN/MANAGER | - |
| match_records | ADMIN/MANAGER | ADMIN/MANAGER | - |

---

## 5. API 설계

### 5.1 공통 규약

- **기본 URL**: `/api`
- **인증**: NextAuth JWT (httpOnly 쿠키, `next-auth.session-token`)
- **에러 포맷**: `{ "error": "한국어 메시지" }`
- **에러 코드**: 400(검증 실패), 401(인증 필요), 403(권한 부족), 404(리소스 없음), 409(상태 충돌), 500(서버 에러)

### 5.2 엔드포인트 목록

#### 인증 API

| 메서드 | 경로 | 설명 | 권한 |
|--------|------|------|------|
| POST | `/api/auth/signup` | 회원가입 | 공개 |
| POST | `/api/auth/callback/credentials` | 로그인 (NextAuth) | 공개 |
| GET | `/api/auth/me` | 현재 사용자 조회 | 인증 필수 |

#### 팀 API

| 메서드 | 경로 | 설명 | 권한 |
|--------|------|------|------|
| GET | `/api/teams` | 소속 팀 목록 | 인증 필수 |
| POST | `/api/teams` | 팀 생성 | 인증 필수 (자동 ADMIN) |
| GET | `/api/teams/[teamId]` | 팀 상세 | 팀 소속 |
| PATCH | `/api/teams/[teamId]` | 팀 수정 | ADMIN |
| DELETE | `/api/teams/[teamId]` | 팀 삭제 | ADMIN |
| GET | `/api/teams/[teamId]/members` | 멤버 목록 | 팀 소속 |
| POST | `/api/teams/[teamId]/members` | 멤버 추가 | ADMIN/MANAGER |
| PATCH | `/api/teams/[teamId]/members/[memberId]` | 역할 변경 | ADMIN |
| DELETE | `/api/teams/[teamId]/members/[memberId]` | 멤버 제거 | ADMIN/MANAGER (계층 기반) |

#### 경기 API

| 메서드 | 경로 | 설명 | 권한 |
|--------|------|------|------|
| GET | `/api/matches` | 경기 목록 (팀별) | 팀 소속 |
| POST | `/api/matches` | 경기 생성 | ADMIN/MANAGER |
| GET | `/api/matches/[id]` | 경기 상세 | 팀 소속 |
| PATCH | `/api/matches/[id]` | 경기 수정 | ADMIN/MANAGER |
| DELETE | `/api/matches/[id]` | 경기 삭제 | ADMIN |
| PATCH | `/api/matches/[id]/attendance` | 출석 투표 | ADMIN/MANAGER/MEMBER |
| PATCH | `/api/matches/[id]/confirm` | 경기 확정 | ADMIN/MANAGER |
| GET | `/api/matches/[id]/record` | 기록실 조회 | 팀 소속 |
| POST | `/api/matches/[id]/record` | 기록 제출 | ADMIN/MANAGER |
| PATCH | `/api/matches/[id]/record/close` | 기록실 마감 | ADMIN/MANAGER |

### 5.3 주요 API 상세

#### POST /api/auth/signup

```
요청: { email: string, password: string, name: string }
검증: email(이메일 형식), password(최소 6자), name(필수)
성공: 201 { user: { id, email, name } }
실패: 400(검증 실패), 409(이미 존재), 500(서버 에러)
```

#### POST /api/matches

```
요청: { team_id: string(UUID), title: string, description?: string, match_date: string, location?: string, opponent?: string }
처리:
  1. 인증 확인 → 팀 소속 확인 → ADMIN/MANAGER 권한 확인
  2. 경기 INSERT (status: OPEN)
  3. 팀 멤버 전원 Attendance BULK INSERT (status: PENDING)
성공: 201 { match: { ... }, attendances: [...] }
```

#### PATCH /api/matches/[id]/attendance

```
요청: { status: "ACCEPTED" | "DECLINED" | "MAYBE" }
전제: 경기 status가 OPEN일 때만 투표 가능
처리: 해당 사용자의 Attendance UPDATE
성공: 200 { attendance: { ... } }
실패: 409(투표 마감됨 — 경기가 OPEN이 아닐 때)
```

#### PATCH /api/matches/[id]/confirm

```
요청: (바디 없음)
전제: 경기 status가 OPEN일 때만 확정 가능
처리:
  1. Match status → CONFIRMED, confirmed_at 기록
  2. RecordRoom 자동 INSERT (status: OPEN)
  3. UNIQUE(match_id) 제약으로 멱등성 보장
성공: 200 { match: { ... }, recordRoom: { ... } }
실패: 409(OPEN 상태 아님)
```

#### PATCH /api/matches/[id]/record/close

```
요청: (바디 없음)
전제: RecordRoom status가 OPEN일 때만 마감 가능
처리:
  1. RecordRoom status → CLOSED, closed_at 기록
  2. Match status → COMPLETED, completed_at 기록
성공: 200 { recordRoom: { ... } }
```

---

## 6. 인증 및 인가

### 6.1 인증 아키텍처

```
[브라우저] → POST /api/auth/callback/credentials (email, password)
    → [NextAuth] → Supabase Auth signInWithPassword
    → JWT 토큰 발급 → httpOnly 쿠키 설정 (next-auth.session-token)
    → 이후 요청 시 쿠키 자동 전송 → getServerSession()으로 인증 확인
```

- **인증 방식**: Credentials Provider (이메일/비밀번호)
- **토큰 전략**: JWT (서명: NEXTAUTH_SECRET)
- **만료**: 30일 (NextAuth 기본값)
- **저장**: httpOnly 쿠키 (XSS 방어)

### 6.2 세션 구조

```typescript
// JWT 토큰 (서버)
{ sub: "user-uuid" }

// 세션 객체 (클라이언트/서버)
{ user: { id: string, name?: string, email?: string, image?: string } }
```

### 6.3 RBAC (역할 기반 접근 제어)

#### 역할 정의

| 역할 | 코드 | 우선순위 | 설명 |
|------|------|---------|------|
| ADMIN | `ADMIN` | 40 | 팀 최고 관리자, 생성자에게 자동 부여 |
| MANAGER | `MANAGER` | 30 | 경기/기록 관리자 |
| MEMBER | `MEMBER` | 20 | 일반 선수, 투표만 가능 |
| GUEST | `GUEST` | 10 | 조회만 가능 |

#### 권한 매트릭스

| 기능 | ADMIN | MANAGER | MEMBER | GUEST |
|------|-------|---------|--------|-------|
| 팀 생성 | O | O | O | O |
| 팀 수정/삭제 | O | X | X | X |
| 멤버 추가 | O | O | X | X |
| 역할 변경 | O | X | X | X |
| 경기 생성 | O | O | X | X |
| 경기 수정 | O | O | X | X |
| 출석 투표 | O | O | O | X |
| 경기 확정 | O | O | X | X |
| 기록 입력 | O | O | X | X |
| 기록 조회 | O | O | O | O |

#### 권한 체크 위치 (3중 방어)

1. **클라이언트 (UI)**: `canManageMatch()`, `canVoteAttendance()` 등으로 버튼/폼 숨김
2. **서버 (API Route)**: `getServerSession()` + `team_members.role` 쿼리로 권한 검증
3. **데이터베이스 (RLS)**: Row Level Security 정책으로 데이터 격리

### 6.4 환경 변수 (키 이름만)

| 키 | 용도 |
|---|------|
| `NEXTAUTH_URL` | NextAuth 콜백 URL |
| `NEXTAUTH_SECRET` | JWT 서명 시크릿 |
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase 엔드포인트 |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase 공개 키 |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase 서비스 역할 키 (서버 전용) |

---

## 7. 프론트엔드 설계

### 7.1 라우팅 구조

| 경로 | 페이지 | 권한 |
|------|--------|------|
| `/` | 홈/대시보드 | 인증 필수 |
| `/auth/signin` | 로그인 | 공개 |
| `/auth/signup` | 회원가입 | 공개 |
| `/matches` | 경기 목록 | 팀 소속 |
| `/matches/new` | 경기 생성 | MANAGER+ |
| `/matches/[id]` | 경기 상세 | 팀 소속 |
| `/matches/[id]/record` | 기록실 | 팀 소속 (입력: MANAGER+) |
| `/team` | 팀 관리 | 인증 필수 |
| `/team/members` | 멤버 관리 | 팀 소속 (관리: MANAGER+) |
| `/profile` | 프로필 | 인증 필수 |

### 7.2 컴포넌트 패턴

- **Client Components**: 모든 UI 컴포넌트에 `'use client'` 지시어 사용
- **Page params**: Next.js 15 규칙에 따라 `Promise` 타입 사용
- **폼 검증**: React Hook Form + Zod 스키마
- **경로 별칭**: `@/*` → `./src/*`

### 7.3 모션 시스템

4가지 표준 패턴만 사용 (Framer Motion):

| 패턴 | 컴포넌트 | 용도 |
|------|---------|------|
| PageTransition | `<PageTransition>` | 페이지 진입/퇴장 |
| StaggerList | `<StaggerList>`, `<StaggerItem>` | 리스트 항목 순차 등장 |
| ModalMotion | `<ModalMotion>` | 다이얼로그/모달 |
| ToastMotion | `<ToastMotion>` | 토스트 알림 |

- `prefers-reduced-motion` 미디어 쿼리 전역 지원

### 7.4 디자인 토큰

- **컬러**: shadcn/ui CSS 변수 기반 (`--background`, `--primary`, `--destructive` 등)
- **타이포그래피**: Geist Sans / Geist Mono
- **스페이싱**: Tailwind 4px 단위 시스템
- **라디우스**: CSS 변수 기반 (`--radius`, `calc(--radius - 2px)`)
- **상태 컬러**: OPEN(blue), CONFIRMED(green), COMPLETED(gray), CANCELLED(red)

---

## 8. 비기능 요구사항

### 8.1 성능

- 모바일 퍼스트 반응형 디자인
- Turbopack 기반 개발 서버 (빠른 HMR)
- React Query 캐시를 통한 불필요한 재요청 방지

### 8.2 보안

- JWT httpOnly 쿠키 (XSS 방어)
- Supabase RLS로 데이터 격리
- 3중 권한 체크 (클라이언트 UI → API Route → DB RLS)
- Zod 스키마로 입력 검증 (인젝션 방어)
- 비밀번호 해싱은 Supabase Auth에 위임

### 8.3 접근성

- `prefers-reduced-motion` 전역 지원
- 시맨틱 HTML (Radix UI 기반)
- 키보드 내비게이션 지원

### 8.4 데이터 무결성

- UNIQUE 제약으로 중복 방지 (팀 멤버, 출석, 기록)
- record_rooms.match_id UNIQUE로 멱등성 보장
- TIMESTAMPTZ로 타임존 처리

---

## 9. 테스트 전략

### 9.1 테스트 피라미드

```
         /\
        /  \     E2E (Playwright)
       /    \    → 핵심 운영 루프 시나리오
      /------\
     /        \   통합 테스트
    /          \  → API 레벨 (3-5개)
   /------------\
  /              \  단위 테스트 (Vitest)
 /                \ → 도메인 로직, 검증, 상수, 권한
/------------------\
```

### 9.2 테스트 현황

| 테스트 파일 | 테스트 수 | 카테고리 |
|------------|---------|---------|
| match-operation-loop.test.ts | 다수 | 도메인 (5시나리오, 7권한) |
| match-status-transition.test.ts | 7 | 상태 전이 |
| match-constants.test.ts | 4 | 상수 |
| attendance-status.test.ts | 3 | 출석 상태 |
| attendance-vote-authorization.test.ts | 다수 | 권한 |
| team-authorization.test.ts | 다수 | 팀 권한 |
| team-validation.test.ts | 다수 | 검증 |
| member-validation.test.ts | 다수 | 멤버 검증 |
| record-room-close.test.ts | 8 | 기록실 마감 |
| auth-options.test.ts | 3 | 인증 설정 |
| signup-validation.test.ts | 4 | 회원가입 검증 |

### 9.3 품질 게이트

- 핵심 유스케이스: E2E 또는 통합 테스트 1개 이상
- 핵심 도메인 서비스: TDD로 단위 테스트 선행 작성
- 프론트엔드: 디자인 토큰 및 컴포넌트 명세 준수
- 모션: 4가지 표준 패턴만 사용
- 구조 변경 시 테스트 커버리지 필수

---

## 10. 마이그레이션 관리

### 10.1 마이그레이션 파일

| 파일 | 내용 |
|------|------|
| `00001_initial_schema.sql` | 핵심 7개 테이블 + ENUM + 읽기 RLS + 인덱스 |
| `00002_rls_write_policies.sql` | 쓰기 RLS 정책 (INSERT/UPDATE/DELETE) |
| `00003_training_wellness_schema.sql` | 훈련/웰니스 확장 스키마 (미래 범위) |
| `00004_etl_views.sql` | ETL/리포팅 뷰 |

### 10.2 실행 방법

Supabase CLI 또는 대시보드를 통해 마이그레이션 실행.

---

## 11. [UNKNOWN] — 미확정 사항

| 항목 | 현재 상태 | 비고 |
|------|---------|------|
| 알림 시스템 | UI 내 상태 표시로 대체 | 이메일/푸시/인앱 미정 |
| OAuth 소셜 로그인 | MVP 범위 밖 | 카카오/Google 등 |
| 비밀번호 재설정 | 미구현 | |
| 투표 마감 시간 자동 처리 | 미정의 | |
| SSR 하이드레이션 | Zustand persist와 불일치 가능 | _isHydrated 플래그로 완화 |
| 미들웨어 라우트 가드 | API 레벨만 (미들웨어 미적용) | |
| Soft delete vs Hard delete | 현재 Hard delete | |
| 다크모드 | ThemeProvider 있으나 토큰 미정의 | |
| 다중 팀 전환 UX | 기본 드롭다운만 | |

---

## 12. 검증 체크리스트

- [ ] 핵심 운영 루프 4단계가 모두 구현되었는가?
- [ ] 자동 전이 2건(경기→투표, 확정→기록실)이 동작하는가?
- [ ] RBAC 4역할이 모든 API에서 검증되는가?
- [ ] RLS 정책이 데이터 격리를 보장하는가?
- [ ] `npm run typecheck && npm run lint && npm run test` 통과하는가?
- [ ] 멱등성(중복 확정 방지)이 DB UNIQUE 제약으로 보장되는가?

# 기능명세서

> 축구 동호회 운영 루프 MVP — 기능 상세 명세
> 최종 업데이트: 2026-02-11
> 근거: 코드베이스 전체 분석 기반

---

## 1. 기능 요약

### 1.1 기능 목록

| ID | 기능 | 유저스토리 | 우선순위 | 상태 |
|----|------|-----------|---------|------|
| F-01 | 회원가입/로그인 | US-01 | P1 | 구현 완료 |
| F-02 | 팀 생성 및 관리 | US-02 | P1 | 구현 완료 |
| F-03 | 팀 멤버 관리 | US-02 | P1 | 구현 완료 |
| F-04 | 경기 일정 등록 | US-03 | P1 | 구현 완료 |
| F-05 | 출석/투표 | US-04 | P1 | 구현 완료 |
| F-06 | 경기 확정 | US-05 | P1 | 구현 완료 |
| F-07 | 기록 입력 | US-06 | P1 | 구현 완료 |
| F-08 | 기록실 마감 | US-06 | P1 | 구현 완료 |
| F-09 | 대시보드 | - | P1 | 구현 완료 |
| F-10 | 팀 선택 | - | P1 | 구현 완료 |

### 1.2 핵심 운영 루프

```
F-04 경기 생성  →  F-05 출석/투표  →  F-06 경기 확정  →  F-07 기록 입력  →  F-08 기록실 마감
   │                                      │
   └─ 자동: Attendance 생성               └─ 자동: RecordRoom 생성
```

---

## 2. F-01: 회원가입/로그인

### 2.1 개요

사용자가 이메일과 비밀번호로 계정을 생성하고 로그인하여 시스템을 이용할 수 있다.

### 2.2 관련 파일

- 페이지: `src/app/auth/signin/page.tsx`, `src/app/auth/signup/page.tsx`
- API: `src/app/api/auth/signup/route.ts`, `src/app/api/auth/[...nextauth]/route.ts`, `src/app/api/auth/me/route.ts`
- 기능 모듈: `src/features/auth/`
- 설정: `src/lib/auth.ts`

### 2.3 회원가입

#### 입력 필드

| 필드 | 타입 | 검증 규칙 | 필수 |
|------|------|----------|------|
| 이메일 | TEXT | 이메일 형식 (Zod email) | O |
| 비밀번호 | TEXT | 최소 6자 | O |
| 이름 | TEXT | 1자 이상 | O |

#### 처리 흐름

```
1. 사용자가 회원가입 폼 작성
2. Zod 스키마 검증 (클라이언트 + 서버)
3. Supabase Auth signUp (이메일/비밀번호)
4. users 테이블에 프로필 INSERT
5. 성공 시 로그인 페이지로 리다이렉트
```

#### 에러 케이스

| 조건 | HTTP | 메시지 |
|------|------|--------|
| 입력 검증 실패 | 400 | Zod 에러 메시지 |
| 이메일 중복 | 409 | 이미 존재하는 이메일 |
| 서버 에러 | 500 | 서버 에러 메시지 |

### 2.4 로그인

#### 입력 필드

| 필드 | 타입 | 필수 |
|------|------|------|
| 이메일 | TEXT | O |
| 비밀번호 | TEXT | O |

#### 처리 흐름

```
1. 사용자가 로그인 폼 작성
2. NextAuth signIn("credentials", { email, password })
3. Supabase Auth signInWithPassword로 검증
4. JWT 토큰 발급 → httpOnly 쿠키 설정
5. 성공 시 홈(/) 으로 리다이렉트
```

#### 세션 유지

- JWT 쿠키 기반, 만료 30일
- 페이지 이동 시 세션 자동 유지
- `useAuth()` 훅으로 클라이언트에서 세션 상태 접근

### 2.5 테스트

| 테스트 | 파일 | 검증 항목 |
|--------|------|----------|
| 회원가입 검증 | `src/features/auth/__tests__/signup-validation.test.ts` | 이메일 형식, 비밀번호 길이, 이름 필수 |
| 인증 설정 | `src/features/auth/__tests__/auth-options.test.ts` | JWT 콜백, 세션 구조 |

---

## 3. F-02: 팀 생성 및 관리

### 3.1 개요

인증된 사용자가 새 팀을 생성하고, 팀 정보를 수정/삭제할 수 있다. 팀 생성자는 자동으로 ADMIN 역할을 부여받는다.

### 3.2 관련 파일

- 페이지: `src/app/team/page.tsx`
- API: `src/app/api/teams/route.ts`, `src/app/api/teams/[teamId]/route.ts`
- 기능 모듈: `src/features/team/`
- 컴포넌트: `src/features/team/components/team-info-card.tsx`, `team-edit-form.tsx`

### 3.3 팀 생성

#### 입력 필드

| 필드 | 타입 | 검증 규칙 | 필수 |
|------|------|----------|------|
| 팀명 | TEXT | 1자 이상 | O |
| 설명 | TEXT | - | X |
| 로고 URL | TEXT | URL 형식 | X |

#### 처리 흐름

```
1. 사용자가 팀 생성 폼 작성
2. teams 테이블에 INSERT (created_by: 현재 사용자)
3. team_members 테이블에 INSERT (role: ADMIN) — 생성자 자동 가입
4. React Query ["teams"] 캐시 무효화
```

#### 비즈니스 규칙

- 모든 인증된 사용자가 팀을 생성할 수 있다
- 팀 생성자에게 ADMIN 역할이 자동 부여된다
- 한 사용자가 여러 팀에 소속될 수 있다

### 3.4 팀 수정

| 권한 | 허용 역할 |
|------|----------|
| 팀 정보 수정 | ADMIN만 |
| 팀 삭제 | ADMIN만 |

#### 수정 가능 필드

- 팀명, 설명, 로고 URL

### 3.5 팀 조회

- 홈 페이지에서 소속 팀 목록 표시
- 팀 카드: 팀명, 설명, 멤버 수, 역할 표시
- ADMIN에게만 수정/삭제 버튼 표시

### 3.6 테스트

| 테스트 | 파일 | 검증 항목 |
|--------|------|----------|
| 팀 검증 | `src/features/team/__tests__/team-validation.test.ts` | 입력 검증 |
| 팀 권한 | `src/features/team/__tests__/team-authorization.test.ts` | 역할별 권한 |

---

## 4. F-03: 팀 멤버 관리

### 4.1 개요

ADMIN/MANAGER가 이메일로 멤버를 초대하고, 역할을 관리할 수 있다. ADMIN만 역할 변경이 가능하다.

### 4.2 관련 파일

- 페이지: `src/app/team/members/page.tsx`
- API: `src/app/api/teams/[teamId]/members/route.ts`, `src/app/api/teams/[teamId]/members/[memberId]/route.ts`
- 컴포넌트: `src/features/team/components/member-list.tsx`, `member-add-form.tsx`, `member-role-select.tsx`
- 권한: `src/features/team/lib/authorization.ts`

### 4.3 멤버 추가

#### 입력 필드

| 필드 | 타입 | 검증 규칙 | 필수 |
|------|------|----------|------|
| 이메일 | TEXT | 이메일 형식, 등록된 사용자 | O |
| 역할 | ENUM | MANAGER/MEMBER/GUEST | O |

#### 처리 흐름

```
1. ADMIN/MANAGER가 이메일과 역할을 입력
2. users 테이블에서 이메일로 사용자 조회
3. 이미 팀 소속인지 확인 (UNIQUE 제약)
4. team_members 테이블에 INSERT
```

#### 에러 케이스

| 조건 | HTTP | 메시지 |
|------|------|--------|
| 권한 부족 | 403 | "멤버 추가 권한이 없습니다" |
| 이미 소속 | 409 | "이미 팀에 소속된 사용자입니다" |
| 사용자 미존재 | 404 | "사용자를 찾을 수 없습니다" |

### 4.4 역할 변경

| 항목 | 내용 |
|------|------|
| 허용 역할 | ADMIN만 |
| 변경 가능 값 | ADMIN, MANAGER, MEMBER, GUEST |

### 4.5 멤버 제거

| 항목 | 내용 |
|------|------|
| 허용 역할 | ADMIN/MANAGER (계층 기반) |
| 제약 | 자신보다 낮은 역할의 멤버만 제거 가능 |

#### 역할 계층

```
ADMIN (40) > MANAGER (30) > MEMBER (20) > GUEST (10)
```

- ADMIN: 모든 멤버 제거 가능
- MANAGER: MEMBER, GUEST만 제거 가능
- MEMBER/GUEST: 제거 불가

### 4.6 권한 검사 함수

| 함수 | 용도 | 허용 역할 |
|------|------|----------|
| `canModifyTeam(role)` | 팀 수정 | ADMIN, MANAGER |
| `canDeleteTeam(role)` | 팀 삭제 | ADMIN |
| `canModifyMembers(role)` | 멤버 추가/제거 | ADMIN, MANAGER |
| `canChangeRole(role)` | 역할 변경 | ADMIN |
| `canRemoveMember(actor, target)` | 멤버 제거 (계층) | 상위 역할만 |

### 4.7 화면 구성

- **멤버 목록**: 이름, 이메일, 역할 뱃지, 가입일
- **멤버 추가 폼**: MANAGER+ 에게만 표시
- **역할 변경 드롭다운**: ADMIN에게만 표시
- **제거 버튼**: 권한에 따라 조건부 표시

### 4.8 테스트

| 테스트 | 파일 | 검증 항목 |
|--------|------|----------|
| 멤버 검증 | `src/features/team/__tests__/member-validation.test.ts` | 입력 검증 |

---

## 5. F-04: 경기 일정 등록 (운영 루프 Step 1)

### 5.1 개요

ADMIN/MANAGER가 경기 일정을 생성한다. **생성과 동시에 팀 멤버 전원에 대한 출석 투표가 자동으로 생성된다.**

### 5.2 관련 파일

- 페이지: `src/app/matches/page.tsx`, `src/app/matches/new/page.tsx`
- API: `src/app/api/matches/route.ts`
- 기능 모듈: `src/features/match/`
- 컴포넌트: `src/features/match/components/create-match-form.tsx`, `match-list.tsx`, `match-card.tsx`

### 5.3 경기 생성

#### 입력 필드

| 필드 | 타입 | 검증 규칙 | 필수 |
|------|------|----------|------|
| 경기명 | TEXT | 1자 이상 (Zod) | O |
| 설명 | TEXT | - | X |
| 경기 일시 | TIMESTAMPTZ | datetime 형식 | O |
| 장소 | TEXT | - | X |
| 상대팀 | TEXT | - | X |

#### 처리 흐름

```
1. ADMIN/MANAGER가 경기 생성 폼 작성
2. Zod 스키마 검증 (team_id: UUID, title: min 1, match_date: datetime)
3. matches 테이블에 INSERT (status: OPEN)
4. 팀 멤버 전원 조회
5. attendances 테이블에 BULK INSERT (status: PENDING) — 자동 생성
6. React Query ["matches", team_id] 캐시 무효화
```

#### 자동 처리 (핵심)

```
경기 INSERT (status: OPEN)
    └─→ 팀 멤버 N명에 대해 Attendance BULK INSERT (status: PENDING)
```

- 경기 생성과 동시에 팀 소속 전체 멤버의 출석 레코드가 자동 생성됨
- 각 Attendance의 초기 상태는 `PENDING` (미응답)

### 5.4 경기 목록 조회

#### 필터/정렬

| 파라미터 | 설명 | 기본값 |
|---------|------|--------|
| team_id | 팀 ID (필수) | 선택된 팀 |
| status | 상태 필터 | 전체 |
| sort | 정렬 | match_date 기준 |
| limit | 조회 수 | - |

#### 화면 구성

- **경기 카드**: 경기명, 일시(date-fns 포맷), 장소, 상대팀, 상태 뱃지
- **상태 뱃지 색상**: OPEN(파랑), CONFIRMED(초록), COMPLETED(회색), CANCELLED(빨강)
- **새 경기 버튼**: MANAGER+ 에게만 표시

### 5.5 경기 수정/삭제

| 작업 | 권한 | 조건 |
|------|------|------|
| 수정 | ADMIN/MANAGER | OPEN 상태일 때만 |
| 삭제 | ADMIN | - |

#### 에러 케이스

| 조건 | HTTP | 메시지 |
|------|------|--------|
| 권한 부족 | 403 | "경기 생성 권한이 없습니다" |
| OPEN 아닌 상태에서 수정 | 409 | "OPEN 상태의 경기만 수정할 수 있습니다" |

### 5.6 테스트

| 테스트 | 파일 | 검증 항목 |
|--------|------|----------|
| 상수 | `src/features/match/__tests__/match-constants.test.ts` | 상태 라벨, 컬러 |
| 상태 전이 | `src/features/match/__tests__/match-status-transition.test.ts` | OPEN→CONFIRMED→COMPLETED |
| 운영 루프 | `src/features/match/__tests__/match-operation-loop.test.ts` | 5시나리오, 7권한 레벨 |

---

## 6. F-05: 출석/투표 (운영 루프 Step 2)

### 6.1 개요

ADMIN/MANAGER/MEMBER가 경기에 대해 참석/불참/보류를 투표한다. GUEST는 투표 불가.

### 6.2 관련 파일

- 페이지: `src/app/matches/[id]/page.tsx` (경기 상세 내 투표 섹션)
- API: `src/app/api/matches/[id]/attendance/route.ts`
- 기능 모듈: `src/features/attendance/`
- 컴포넌트: `src/features/attendance/components/vote-buttons.tsx`

### 6.3 투표

#### 입력 값

| 값 | 코드 | 설명 |
|----|------|------|
| 참석 | `ACCEPTED` | 경기에 참석 |
| 불참 | `DECLINED` | 경기에 불참 |
| 보류 | `MAYBE` | 미정 |

#### 전제 조건

- 경기 상태가 `OPEN`일 때만 투표 가능
- ADMIN/MANAGER/MEMBER 역할만 투표 가능 (GUEST 불가)
- 본인의 Attendance만 변경 가능

#### 처리 흐름

```
1. 사용자가 참석/불참/보류 버튼 클릭
2. 경기 status 확인 (OPEN이 아니면 409)
3. 해당 사용자의 Attendance UPDATE (status + voted_at)
4. 투표 현황 갱신
```

#### 상태 전이

```
PENDING → ACCEPTED
PENDING → DECLINED
PENDING → MAYBE
ACCEPTED → DECLINED  (변경 가능)
ACCEPTED → MAYBE     (변경 가능)
DECLINED → ACCEPTED  (변경 가능)
...
```

- 투표는 경기가 OPEN인 동안 **무제한 변경 가능**
- 경기가 CONFIRMED/COMPLETED/CANCELLED이면 투표 불가

### 6.4 투표 현황

경기 상세 페이지에서 투표 현황을 확인할 수 있다.

| 표시 항목 | 설명 |
|----------|------|
| 참석 N명 | ACCEPTED 수 |
| 불참 N명 | DECLINED 수 |
| 보류 N명 | MAYBE 수 |
| 미응답 N명 | PENDING 수 |
| 내 투표 상태 | 현재 사용자의 투표 상태 하이라이트 |

### 6.5 화면 구성

- **투표 버튼 3개**: 참석(초록), 불참(빨강), 보류(노랑)
- 현재 선택된 투표 상태 하이라이트
- GUEST에게는 투표 버튼 비표시
- OPEN 상태가 아닌 경기에서는 투표 버튼 비활성화

### 6.6 에러 케이스

| 조건 | HTTP | 메시지 |
|------|------|--------|
| 경기가 OPEN 아님 | 409 | "투표가 마감되었습니다" |
| 권한 부족 | 403 | 투표 권한 없음 |

### 6.7 테스트

| 테스트 | 파일 | 검증 항목 |
|--------|------|----------|
| 출석 상태 | `src/features/attendance/__tests__/attendance-status.test.ts` | 상태 전이 |
| 투표 권한 | `src/features/attendance/__tests__/attendance-vote-authorization.test.ts` | 역할별 투표 가능 여부 |

---

## 7. F-06: 경기 확정 (운영 루프 Step 3)

### 7.1 개요

ADMIN/MANAGER가 투표 결과를 확인하고 경기를 확정한다. **확정과 동시에 기록실(RecordRoom)이 자동으로 생성된다.** 중복 확정 시 멱등성이 보장된다.

### 7.2 관련 파일

- 페이지: `src/app/matches/[id]/page.tsx` (경기 상세 내 확정 버튼)
- API: `src/app/api/matches/[id]/confirm/route.ts`
- 컴포넌트: `src/features/attendance/components/confirm-button.tsx`

### 7.3 확정 처리

#### 전제 조건

- 경기 상태가 `OPEN`일 때만 확정 가능
- ADMIN/MANAGER 역할만 확정 가능

#### 처리 흐름

```
1. ADMIN/MANAGER가 확정 버튼 클릭
2. 경기 status 확인 (OPEN이 아니면 409)
3. Match status → CONFIRMED, confirmed_at 기록
4. RecordRoom INSERT (status: OPEN) — 자동 생성
5. React Query ["match", id] + ["matches"] 캐시 무효화
```

#### 자동 처리 (핵심)

```
경기 확정 (Match status: OPEN → CONFIRMED)
    └─→ RecordRoom 자동 INSERT (status: OPEN)
```

### 7.4 멱등성 보장

- record_rooms 테이블의 `match_id`에 UNIQUE 제약
- 동일 경기에 대한 중복 확정 시 RecordRoom INSERT가 DB 레벨에서 실패
- 이미 CONFIRMED인 경기는 409 응답

```
첫 번째 확정: Match → CONFIRMED + RecordRoom 생성 → 성공 (200)
두 번째 확정: Match status가 CONFIRMED → 409 (OPEN이 아님)
```

### 7.5 에러 케이스

| 조건 | HTTP | 메시지 |
|------|------|--------|
| OPEN 아닌 상태 | 409 | "OPEN 상태의 경기만 확정할 수 있습니다" |
| 권한 부족 | 403 | "경기 확정 권한이 없습니다" |

### 7.6 화면 구성

- **확정 버튼**: MANAGER+ 에게만 표시, OPEN 상태일 때만 활성화
- 확정 완료 후 상태 뱃지가 CONFIRMED(초록)으로 변경
- 기록실 링크 활성화

---

## 8. F-07: 기록 입력 (운영 루프 Step 4)

### 8.1 개요

ADMIN/MANAGER가 확정된 경기의 기록실에서 선수별 스탯을 입력한다. MEMBER/GUEST는 조회만 가능.

### 8.2 관련 파일

- 페이지: `src/app/matches/[id]/record/page.tsx`
- API: `src/app/api/matches/[id]/record/route.ts`
- 기능 모듈: `src/features/record/`

### 8.3 기록 제출

#### 입력 필드

| 필드 | 타입 | 기본값 | 설명 |
|------|------|--------|------|
| user_id | UUID | - | 선수 ID |
| goals | INT | 0 | 득점 |
| assists | INT | 0 | 어시스트 |
| yellow_cards | INT | 0 | 경고 |
| red_cards | INT | 0 | 퇴장 |
| memo | TEXT | null | 메모 |

#### 전제 조건

- 경기 상태가 `CONFIRMED`일 때만 기록 가능
- RecordRoom 상태가 `OPEN`일 때만 기록 가능
- ADMIN/MANAGER 역할만 기록 입력 가능

#### 처리 흐름

```
1. ADMIN/MANAGER가 선수별 스탯 입력
2. RecordRoom status 확인 (OPEN이 아니면 409)
3. match_records 테이블에 INSERT/UPSERT
4. UNIQUE(record_room_id, user_id) — 선수당 1개 레코드
```

#### 비즈니스 규칙

- 한 선수당 기록실에서 하나의 레코드만 존재 (UNIQUE 제약)
- 기록실이 마감(CLOSED)되면 입력/수정 불가
- MEMBER/GUEST는 기록 조회만 가능

### 8.4 기록 조회

- 기록실 페이지에서 모든 선수의 스탯을 테이블 형태로 표시
- 표시 항목: 선수 이름, 득점, 어시스트, 경고, 퇴장, 메모
- JOIN 쿼리로 사용자 이름/아바타 포함 (`RecordWithUser` 타입)

### 8.5 에러 케이스

| 조건 | HTTP | 메시지 |
|------|------|--------|
| 기록실 없음 | 404 | "기록실이 없습니다" |
| 기록실 마감 | 409 | "기록실이 마감되었습니다" |
| 권한 부족 | 403 | "기록 입력 권한이 없습니다" |

---

## 9. F-08: 기록실 마감

### 9.1 개요

ADMIN/MANAGER가 기록 입력을 완료하고 기록실을 마감한다. 마감 시 경기 상태가 자동으로 COMPLETED로 전이된다.

### 9.2 관련 파일

- API: `src/app/api/matches/[id]/record/close/route.ts`

### 9.3 마감 처리

#### 전제 조건

- RecordRoom 상태가 `OPEN`일 때만 마감 가능
- ADMIN/MANAGER 역할만 마감 가능

#### 처리 흐름

```
1. ADMIN/MANAGER가 기록실 마감 버튼 클릭
2. RecordRoom status 확인 (OPEN이 아니면 무시/멱등)
3. RecordRoom status → CLOSED, closed_at 기록
4. Match status → COMPLETED, completed_at 기록
```

#### 자동 처리

```
기록실 마감 (RecordRoom status: OPEN → CLOSED)
    └─→ Match status: CONFIRMED → COMPLETED (자동 전이)
```

### 9.4 멱등성

- 이미 CLOSED인 기록실에 대한 중복 마감 요청은 멱등하게 처리
- 8개 테스트 케이스로 검증됨

### 9.5 테스트

| 테스트 | 파일 | 검증 항목 |
|--------|------|----------|
| 기록실 마감 | `src/features/record/__tests__/record-room-close.test.ts` | 상태 전이, 멱등성, 권한 (8개 케이스) |

---

## 10. F-09: 대시보드

### 10.1 개요

로그인한 사용자에게 홈 화면에서 소속 팀, 다가오는 경기, 주요 KPI를 보여준다.

### 10.2 관련 파일

- 페이지: `src/app/page.tsx`

### 10.3 화면 구성

#### 비로그인 상태

- GuestLanding 컴포넌트 표시 (로그인/회원가입 안내)

#### 로그인 + 팀 미선택 상태

- NoTeamCta 컴포넌트 표시 (팀 생성/가입 안내)

#### 로그인 + 팀 선택 상태

| 섹션 | 설명 |
|------|------|
| KPI 카드 | 핵심 지표 (경기 수, 출석률 등) |
| 다가오는 경기 | 가까운 일정 표시 |
| 팀 목록 | 소속 팀 목록 |

---

## 11. F-10: 팀 선택

### 11.1 개요

사용자가 여러 팀에 소속된 경우, 헤더의 드롭다운으로 활성 팀을 선택한다. 선택된 팀은 localStorage에 영속화되어 세션 간 유지된다.

### 11.2 관련 파일

- 컴포넌트: `src/components/layout/team-selector.tsx`, `src/components/layout/header.tsx`
- 스토어: `src/lib/stores/team-store.ts`

### 11.3 동작

```
1. 헤더의 팀 셀렉터 드롭다운에서 팀 선택
2. Zustand store의 selectedTeamId 갱신
3. localStorage "team-store"에 영속화
4. 팀 의존적 데이터(경기 목록 등) 자동 갱신 (React Query key에 teamId 포함)
```

### 11.4 주의 사항

- SSR/CSR 하이드레이션 불일치 방지를 위해 `_isHydrated` 플래그 사용
- 팀 미선택 시 경기 관련 기능 비활성화

---

## 12. 엔터티 상태 전이 전체 다이어그램

### 12.1 Match (경기) 상태 전이

```
OPEN ─────────→ CONFIRMED ──────→ COMPLETED
  │                  │
  └──→ CANCELLED ←───┘
```

| 전이 | 트리거 | 자동 처리 |
|------|--------|----------|
| → OPEN | 경기 생성 | Attendance BULK 생성 |
| OPEN → CONFIRMED | 운영자 확정 | RecordRoom 자동 생성 |
| CONFIRMED → COMPLETED | 기록실 마감 | - |
| Any → CANCELLED | 운영자 취소 | - |

### 12.2 Attendance (출석) 상태 전이

```
PENDING → ACCEPTED / DECLINED / MAYBE
```

- 경기가 OPEN인 동안 자유롭게 변경 가능
- 경기 확정 후 투표 불가

### 12.3 RecordRoom (기록실) 상태 전이

```
OPEN → CLOSED
```

- 경기 확정 시 자동 생성 (OPEN)
- 운영자 마감 시 CLOSED로 전이
- CLOSED 시 기록 입력 불가

---

## 13. 도메인 이벤트 흐름

```
[운영자] 경기 생성 (F-04)
    │
    ▼
MatchCreated ──자동──→ AttendanceBulkCreated (팀 전원)
    │                        │
    ▼                        ▼
Match(OPEN)           Attendance(PENDING) × N명
                             │
                      [선수] 투표 (F-05)
                             │
                             ▼
                      AttendanceVoted
                      (ACCEPTED / DECLINED / MAYBE)
                             │
                      [운영자] 확정 (F-06)
                             │
                             ▼
                      MatchConfirmed ──자동──→ RecordRoomCreated
                             │                       │
                             ▼                       ▼
                      Match(CONFIRMED)        RecordRoom(OPEN)
                                                     │
                                              [운영자] 기록 입력 (F-07)
                                                     │
                                                     ▼
                                              RecordSubmitted
                                                     │
                                              [운영자] 마감 (F-08)
                                                     │
                                                     ▼
                                              RecordRoom(CLOSED)
                                              Match(COMPLETED)
```

---

## 14. 화면 흐름 (User Flow)

### 14.1 운영자 핵심 플로우

```
홈(/) → 경기 목록(/matches) → [+] 경기 생성(/matches/new)
    → 폼 작성 → 제출 → (자동: 투표 생성)
    → 경기 상세(/matches/[id]) → 투표 현황 확인
    → [확정] 버튼 클릭 → (자동: 기록실 생성)
    → 기록실(/matches/[id]/record) → 스탯 입력
    → [마감] 버튼 클릭 → 경기 완료
```

### 14.2 선수 핵심 플로우

```
홈(/) → 경기 목록(/matches) → 경기 상세(/matches/[id])
    → [참석/불참/보류] 투표
    → (확정 후) 기록실(/matches/[id]/record) → 기록 조회
```

---

## 15. 비기능 요구사항 (기능 관점)

### 15.1 에러 처리

| HTTP 코드 | 의미 | 사용 장면 |
|----------|------|----------|
| 400 | 입력 검증 실패 | Zod 스키마 검증 실패 |
| 401 | 인증 필요 | 미로그인 상태 |
| 403 | 권한 부족 | 역할 미달 |
| 404 | 리소스 없음 | 경기/팀/사용자 조회 실패 |
| 409 | 상태 충돌 | 이미 확정, 기록실 마감, 중복 가입 |
| 500 | 서버 에러 | DB 쿼리 실패 |

- 모든 에러 메시지는 한국어로 제공
- 표준 포맷: `{ "error": "한국어 에러 메시지" }`

### 15.2 데이터 무결성

| 제약 | 테이블 | 효과 |
|------|--------|------|
| UNIQUE(team_id, user_id) | team_members | 한 팀에 중복 가입 방지 |
| UNIQUE(match_id, user_id) | attendances | 경기당 1인 1투표 |
| UNIQUE(match_id) | record_rooms | 경기당 기록실 1개 (멱등성) |
| UNIQUE(record_room_id, user_id) | match_records | 선수당 기록 1개 |

### 15.3 접근성

- 역할에 따른 UI 요소 조건부 표시/숨김
- 투표 버튼에 현재 상태 시각적 피드백
- 상태 뱃지 컬러 코딩

---

## 16. MVP 범위 외 (OUT OF SCOPE)

| 기능 | 사유 | 대체 방안 |
|------|------|----------|
| 알림 시스템 (푸시/이메일) | 외부 서비스 의존 | UI 내 상태 표시 |
| 캘린더 뷰 | 추가 라이브러리 필요 | 리스트 뷰 |
| OAuth 소셜 로그인 | 프로바이더 설정 복잡 | 이메일/비밀번호만 |
| 대결/랭킹 | 도메인 복잡도 급증 | 최소 프로토타입(P2) |
| 실시간 업데이트 | 인프라 복잡도 | 수동 새로고침 |
| 통계 대시보드 | 집계 쿼리/차트 | 기록실 조회 |
| 파일 업로드 | 스토리지 설정 | URL 입력만 |
| 다국어 지원 | 불필요한 복잡도 | 한국어 단일 |
| 비밀번호 재설정 | 추가 플로우 필요 | MVP 이후 |

---

## 17. 검증 체크리스트

### 기능 완료 검증

- [ ] F-01: 이메일/비밀번호로 회원가입 및 로그인이 동작하는가?
- [ ] F-02: 팀 생성 시 생성자에게 ADMIN이 자동 부여되는가?
- [ ] F-03: ADMIN만 역할 변경이 가능한가?
- [ ] F-04: 경기 생성 시 팀 전원의 Attendance가 자동 생성되는가?
- [ ] F-05: OPEN 상태 경기에서만 투표가 가능한가?
- [ ] F-05: GUEST는 투표할 수 없는가?
- [ ] F-06: 확정 시 RecordRoom이 자동 생성되는가?
- [ ] F-06: 중복 확정이 멱등하게 처리되는가?
- [ ] F-07: CONFIRMED 경기에서만 기록 입력이 가능한가?
- [ ] F-08: 기록실 마감 시 경기 상태가 COMPLETED로 전이되는가?

### 운영 루프 E2E 검증

- [ ] 경기 생성 → 투표 → 확정 → 기록 → 마감 전체 플로우가 동작하는가?
- [ ] 각 단계에서 권한별 접근 제어가 올바른가?
- [ ] 자동 전이(생성→투표, 확정→기록실)가 모두 동작하는가?

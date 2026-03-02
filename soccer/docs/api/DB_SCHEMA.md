# DB 스키마 문서

> 근거: `supabase/migrations/00001_initial_schema.sql`
> DB: Supabase (PostgreSQL)

## 엔터티 관계도 (ERD)

```
Users ──1:N──→ Team_Members ──N:1──→ Teams
  │                                     │
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

## 테이블 상세

### users
| 필드 | 타입 | 제약 | 설명 |
|------|------|------|------|
| id | UUID | PK, default gen_random_uuid() | |
| email | TEXT | UNIQUE, NOT NULL | 로그인 이메일 |
| name | TEXT | NOT NULL | 표시 이름 |
| avatar_url | TEXT | nullable | 프로필 이미지 |
| created_at | TIMESTAMPTZ | default now() | |
| updated_at | TIMESTAMPTZ | default now() | |

- 인덱스: `idx_users_email` (email)
- 근거: `supabase/migrations/00001_initial_schema.sql:7-15`

### teams
| 필드 | 타입 | 제약 | 설명 |
|------|------|------|------|
| id | UUID | PK | |
| name | TEXT | NOT NULL | 팀명 |
| description | TEXT | nullable | |
| logo_url | TEXT | nullable | |
| created_by | UUID | FK → users(id) | 생성자 |
| created_at | TIMESTAMPTZ | | |
| updated_at | TIMESTAMPTZ | | |

- 근거: `supabase/migrations/00001_initial_schema.sql:20-29`

### team_members
| 필드 | 타입 | 제약 | 설명 |
|------|------|------|------|
| id | UUID | PK | |
| team_id | UUID | FK → teams(id), UNIQUE(team_id, user_id) | |
| user_id | UUID | FK → users(id) | |
| role | team_role | ENUM: ADMIN/MANAGER/MEMBER/GUEST | 역할 |
| joined_at | TIMESTAMPTZ | | |

- 인덱스: `idx_team_members_team`, `idx_team_members_user`
- UNIQUE(team_id, user_id) — 한 팀에 같은 사용자 중복 불가
- 근거: `supabase/migrations/00001_initial_schema.sql:34-46`

### matches
| 필드 | 타입 | 제약 | 설명 |
|------|------|------|------|
| id | UUID | PK | |
| team_id | UUID | FK → teams(id) | 소속 팀 |
| title | TEXT | NOT NULL | 경기명 |
| description | TEXT | nullable | |
| match_date | TIMESTAMPTZ | NOT NULL | 경기 일시 |
| location | TEXT | nullable | 장소 |
| opponent | TEXT | nullable | 상대팀명 |
| status | match_status | ENUM: OPEN/CONFIRMED/COMPLETED/CANCELLED | 상태 |
| created_by | UUID | FK → users(id) | 생성자 |
| confirmed_at | TIMESTAMPTZ | nullable | 확정 시각 |
| completed_at | TIMESTAMPTZ | nullable | 완료 시각 |
| created_at | TIMESTAMPTZ | | |
| updated_at | TIMESTAMPTZ | | |

- 인덱스: `idx_matches_team`, `idx_matches_status`, `idx_matches_date`
- 상태 전이: OPEN → CONFIRMED → COMPLETED (또는 CANCELLED)
- 근거: `supabase/migrations/00001_initial_schema.sql:51-67`

### attendances
| 필드 | 타입 | 제약 | 설명 |
|------|------|------|------|
| id | UUID | PK | |
| match_id | UUID | FK → matches(id), UNIQUE(match_id, user_id) | |
| user_id | UUID | FK → users(id) | |
| status | attendance_status | ENUM: PENDING/ACCEPTED/DECLINED/MAYBE | 투표 상태 |
| voted_at | TIMESTAMPTZ | nullable | 투표 시각 |
| created_at | TIMESTAMPTZ | | |
| updated_at | TIMESTAMPTZ | | |

- 인덱스: `idx_attendances_match`, `idx_attendances_user`
- UNIQUE(match_id, user_id) — 경기당 1인 1투표
- 근거: `supabase/migrations/00001_initial_schema.sql:72-86`

### record_rooms
| 필드 | 타입 | 제약 | 설명 |
|------|------|------|------|
| id | UUID | PK | |
| match_id | UUID | FK → matches(id), **UNIQUE** | 1경기 1기록실 (멱등성) |
| status | record_room_status | ENUM: OPEN/CLOSED | |
| created_at | TIMESTAMPTZ | | |
| closed_at | TIMESTAMPTZ | nullable | |

- **match_id UNIQUE** — 경기당 기록실 1개만 생성 가능 → 중복 확정 시 INSERT 실패로 멱등성 보장
- 근거: `supabase/migrations/00001_initial_schema.sql:91-99`

### match_records
| 필드 | 타입 | 제약 | 설명 |
|------|------|------|------|
| id | UUID | PK | |
| record_room_id | UUID | FK → record_rooms(id) | |
| user_id | UUID | FK → users(id) | 선수 |
| goals | INT | default 0 | 득점 |
| assists | INT | default 0 | 어시스트 |
| yellow_cards | INT | default 0 | 경고 |
| red_cards | INT | default 0 | 퇴장 |
| memo | TEXT | nullable | 메모 |
| created_at | TIMESTAMPTZ | | |
| updated_at | TIMESTAMPTZ | | |

- UNIQUE(record_room_id, user_id) — 기록실당 선수당 1개 레코드
- 인덱스: `idx_match_records_room`, `idx_match_records_user`
- 근거: `supabase/migrations/00001_initial_schema.sql:104-117`

## ENUM 타입

| 이름 | 값 | 근거 |
|------|---|------|
| team_role | ADMIN, MANAGER, MEMBER, GUEST | `supabase/migrations/00001_initial_schema.sql:34` |
| match_status | OPEN, CONFIRMED, COMPLETED, CANCELLED | `supabase/migrations/00001_initial_schema.sql:51` |
| attendance_status | PENDING, ACCEPTED, DECLINED, MAYBE | `supabase/migrations/00001_initial_schema.sql:72` |
| record_room_status | OPEN, CLOSED | `supabase/migrations/00001_initial_schema.sql:91` |

## 상태 전이 규칙

### Match 상태 전이
```
OPEN ─────→ CONFIRMED ──→ COMPLETED
  │              │
  └──→ CANCELLED ←──┘
```

- OPEN → CONFIRMED: 운영자 확정 (PATCH /matches/{id}/confirm)
  - **자동**: RecordRoom 생성 (UNIQUE 제약으로 멱등성 보장)
- CONFIRMED → COMPLETED: 기록 입력 완료 후 운영자 수동
- 어느 상태에서든 → CANCELLED: 운영자 취소

### 경기 생성 시 자동 처리
- Match INSERT → 팀 멤버 전원에 대한 Attendance 레코드 BULK INSERT (status: PENDING)

## RLS 정책 요약

| 테이블 | 정책 | 설명 |
|--------|------|------|
| users | users_read_own | 자기 정보만 조회 |
| teams | teams_read_member | 소속 팀만 조회 |
| team_members | team_members_read | 소속 팀 멤버만 조회 |
| matches | matches_read_team | 소속 팀 경기만 조회 |
| attendances | attendances_read_team | 소속 팀 경기 투표만 조회 |
| record_rooms | record_rooms_read | 소속 팀 기록실만 조회 |
| match_records | match_records_read | 소속 팀 기록만 조회 |

> 쓰기 정책은 MVP에서 Service Role Key를 통한 서버 사이드 처리로 우회
> [UNKNOWN] 세분화된 쓰기 RLS 정책 (역할별 INSERT/UPDATE/DELETE)

## [UNKNOWN]
- 팀 간 대결 스키마 (MVP 범위 밖, 0010에서 설계 메모로 대체)
- soft delete 여부 (현재 hard delete)
- 타임존 처리 상세 (현재 TIMESTAMPTZ 사용)
- 마이그레이션 실행 방법 (Supabase 대시보드 또는 CLI)

## 검증 체크리스트
- [ ] 경기 확정 시 기록실이 자동 생성되는 구조가 스키마에 반영되었는가? (record_rooms.match_id UNIQUE)
- [ ] 도메인/인프라/프레젠테이션 경계 분리가 가능한 구조인가?
- [ ] ENUM 상태 전이가 docs/product/DOMAIN_EVENTS.md와 일치하는가?
- [ ] 시드 데이터가 최소 운영 루프 테스트에 충분한가?

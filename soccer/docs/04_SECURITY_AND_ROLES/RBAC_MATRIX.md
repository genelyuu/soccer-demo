# RBAC 역할 매트릭스 (Task 0011)

> 근거: `supabase/migrations/00001_initial_schema.sql:34` (team_role ENUM)
> API 권한 체크: 각 API 라우트 파일

## 역할 정의

| 역할 | 코드 | 설명 |
|------|------|------|
| ADMIN | `ADMIN` | 팀 최고 관리자. 팀 생성자에게 자동 부여 |
| MANAGER | `MANAGER` | 경기/기록 관리자. 일정 생성/확정/기록 입력 가능 |
| MEMBER | `MEMBER` | 일반 선수. 조회/투표만 가능 |
| GUEST | `GUEST` | 게스트. 조회만 가능 (투표 불가) |

## 기능별 권한 매트릭스

### API 엔드포인트

| 기능 | 엔드포인트 | ADMIN | MANAGER | MEMBER | GUEST | 근거 |
|------|-----------|-------|---------|--------|-------|------|
| 팀 생성 | POST /api/teams | O (자동 ADMIN) | O (자동 ADMIN) | O (자동 ADMIN) | O (자동 ADMIN) | `src/app/api/teams/route.ts:42` |
| 팀 조회 | GET /api/teams | O | O | O | O | 인증만 필요 |
| 멤버 목록 | GET /api/teams/{id}/members | O | O | O | O | `src/app/api/teams/[teamId]/members/route.ts:22` |
| 멤버 추가 | POST /api/teams/{id}/members | O | O | X | X | `src/app/api/teams/[teamId]/members/route.ts:62` |
| 역할 변경 | PATCH /api/teams/{id}/members | O | X | X | X | `src/app/api/teams/[teamId]/members/route.ts:101` |
| 경기 생성 | POST /api/matches | O | O | X | X | `src/app/api/matches/route.ts:76` |
| 경기 목록 | GET /api/matches | O | O | O | O | `src/app/api/matches/route.ts:20` |
| 경기 수정 | PATCH /api/matches/{id} | O | O | X | X | `src/app/api/matches/[id]/route.ts:82` |
| 출석 투표 | PATCH /api/matches/{id}/attendance | O | O | O | X | `src/app/api/matches/[id]/attendance/route.ts` |
| 경기 확정 | PATCH /api/matches/{id}/confirm | O | O | X | X | `src/app/api/matches/[id]/confirm/route.ts:47` |
| 기록 조회 | GET /api/matches/{id}/record | O | O | O | O | `src/app/api/matches/[id]/record/route.ts:14` |
| 기록 입력 | POST /api/matches/{id}/record | O | O | X | X | `src/app/api/matches/[id]/record/route.ts:75` |

### 화면별 접근

| 페이지 | ADMIN | MANAGER | MEMBER | GUEST | 근거 |
|--------|-------|---------|--------|-------|------|
| /auth/signin, /auth/signup | O | O | O | O | 공개 |
| / (홈) | O | O | O | O | `docs/ui/IA.md` |
| /matches (목록) | O | O | O | O | |
| /matches/new (생성) | O | O | X (UI 표시, API 차단) | X | |
| /matches/[id] (상세) | O | O | O | O | |
| /matches/[id]/record (기록실) | O (입력/조회) | O (입력/조회) | O (조회만) | O (조회만) | |
| /team | O | O | O | O | |
| /team/members (관리) | O (전체) | O (초대만) | O (조회만) | O (조회만) | |

## 검증 체크리스트
- [ ] 각 엔드포인트에 요구 역할이 명시되었는가?
- [ ] MEMBER가 경기 생성/확정/기록 입력을 할 수 없는가?
- [ ] ADMIN만 역할 변경이 가능한가?
- [ ] GUEST는 투표조차 할 수 없는가? [UNKNOWN — 현재 API에서 팀 소속 확인만 수행]

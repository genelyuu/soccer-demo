# 팀/멤버 관리 API 문서

> 근거: `src/app/api/teams/route.ts`, `src/app/api/teams/[teamId]/route.ts`, `src/app/api/teams/[teamId]/members/route.ts`, `src/app/api/teams/[teamId]/members/[memberId]/route.ts`

## 팀 CRUD

### GET /api/teams
- **설명**: 내가 소속된 팀 목록 조회
- **권한**: 인증 필수
- **응답**: `{ "teams": [{ ...team, "my_role": "ADMIN" }] }`

### POST /api/teams
- **설명**: 팀 생성 (생성자는 자동으로 ADMIN)
- **권한**: 인증 필수
- **요청**: `{ "name": "...", "description": "..." }`
- **응답**: `{ "team": { ... } }` (201)

### GET /api/teams/{teamId}
- **설명**: 팀 상세 조회
- **권한**: 팀 소속 MEMBER 이상
- **응답**: `{ "team": { ... }, "my_role": "ADMIN" }`

### PATCH /api/teams/{teamId}
- **설명**: 팀 정보 수정
- **권한**: ADMIN / MANAGER
- **요청**: `{ "name?": "...", "description?": "..." }`
- **응답**: `{ "team": { ... } }`

### DELETE /api/teams/{teamId}
- **설명**: 팀 삭제 (CASCADE로 멤버도 삭제)
- **권한**: ADMIN만
- **응답**: `{ "message": "팀이 삭제되었습니다" }`

## 멤버 관리

### GET /api/teams/{teamId}/members
- **설명**: 팀 멤버 목록 조회 (유저 정보 JOIN)
- **권한**: 팀 소속 MEMBER 이상
- **응답**: `{ "members": [{ "id", "role", "joined_at", "users": { "id", "name", "email", "avatar_url" } }], "my_role": "..." }`

### POST /api/teams/{teamId}/members
- **설명**: 멤버 초대 (이메일로 검색)
- **권한**: ADMIN / MANAGER
- **요청**: `{ "email": "...", "role?": "MEMBER" }`
- **에러**: 409 (이미 소속), 404 (사용자 없음)

### PATCH /api/teams/{teamId}/members/{memberId}
- **설명**: 멤버 역할 변경
- **권한**: ADMIN만
- **요청**: `{ "role": "MANAGER" }`

### DELETE /api/teams/{teamId}/members/{memberId}
- **설명**: 멤버 제거
- **권한**: ADMIN (전체) / MANAGER (MEMBER, GUEST만)

## 권한 모델

순수 함수로 구현 (`src/features/team/lib/authorization.ts`):

| 함수 | 설명 | 허용 역할 |
|------|------|-----------|
| `canModifyTeam(role)` | 팀 수정 | ADMIN, MANAGER |
| `canDeleteTeam(role)` | 팀 삭제 | ADMIN |
| `canModifyMembers(role)` | 멤버 추가/제거 | ADMIN, MANAGER |
| `canChangeRole(role)` | 역할 변경 | ADMIN |
| `canRemoveMember(actor, target)` | 특정 멤버 제거 | ADMIN: 전체 / MANAGER: MEMBER, GUEST만 |

## 권한 체계

| 역할 | 팀 수정 | 팀 삭제 | 멤버 초대 | 역할 변경 | 멤버 제거 |
|------|---------|---------|---------|---------|---------|
| ADMIN | O | O | O | O | 전체 |
| MANAGER | O | X | O | X | MEMBER/GUEST |
| MEMBER | X | X | X | X | X |
| GUEST | X | X | X | X | X |

## 테스트

| 파일 | 설명 |
|------|------|
| `src/features/team/__tests__/team-authorization.test.ts` | 권한 검증 (23개 테스트) |
| `src/features/team/__tests__/team-validation.test.ts` | 팀 Zod 스키마 검증 (8개) |
| `src/features/team/__tests__/member-validation.test.ts` | 멤버 Zod 스키마 검증 (12개) |

## 검증 체크리스트
- [x] 팀 생성자가 자동으로 ADMIN이 되는가?
- [x] MEMBER/GUEST가 팀을 수정/삭제할 수 없는가?
- [x] ADMIN만 역할을 변경할 수 있는가?
- [x] MANAGER가 ADMIN/MANAGER를 제거할 수 없는가?
- [x] 이미 소속된 사용자를 다시 초대하면 에러가 발생하는가?
- [x] 권한 함수 단위 테스트 통과

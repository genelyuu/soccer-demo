# 프론트 권한 처리 문서 (Task 0013)

> 근거: `src/features/team/lib/authorization.ts`, `docs/04_SECURITY_AND_ROLES/RBAC_MATRIX.md`

## 현재 구현 상태

MVP에서는 **API 레벨 권한 체크**가 주된 방어선이며, 프론트엔드는 보조적 역할을 수행한다.

### API 레벨 (서버 사이드)
- 각 API 라우트에서 `getServerSession` + `team_members.role` 확인
- 근거: 각 `route.ts` 파일

### 프론트 레벨 (클라이언트)
- 멤버 관리 페이지: `myRole`에 따라 초대 폼 표시/숨김
  - 근거: `src/app/team/members/page.tsx`
- [UNKNOWN] 라우트 가드 미구현 — 현재 모든 페이지 접근 가능, API에서 차단

## 권한 부족 시 UI

| 상황 | 현재 처리 | 개선 방향 |
|------|---------|---------|
| MEMBER가 경기 생성 | 폼은 보이나 API 403 | 버튼 숨김 또는 비활성화 |
| 비로그인 사용자 | API 401 | 로그인 페이지로 리다이렉트 |
| 팀 미소속 | API 403 | "팀에 소속되어 있지 않습니다" 안내 |

## [UNKNOWN]
- Route Guard / Layout Guard 구현 (middleware.ts)
- 403 전용 안내 페이지
- 권한 변경 시 UI 자동 갱신

## 검증 체크리스트
- [ ] 권한 없는 사용자가 API 호출 시 적절한 에러가 표시되는가?
- [ ] MANAGER 이상만 경기 생성/확정/기록 입력이 가능한가?

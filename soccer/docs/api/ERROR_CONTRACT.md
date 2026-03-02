# API 에러 규약 문서 (Task 0012)

> 근거: 각 API 라우트 파일의 에러 응답 패턴

## 표준 에러 포맷

```json
{
  "error": "한국어 에러 메시지"
}
```

## HTTP 상태 코드

| 코드 | 의미 | 사용 위치 |
|------|------|----------|
| 400 | 잘못된 요청 (입력 검증 실패) | zod 스키마 검증 실패 |
| 401 | 인증 필요 | `getServerSession()` 실패 시 |
| 403 | 권한 부족 | 역할 확인 실패 (MEMBER가 MANAGER 작업 시도) |
| 404 | 리소스 없음 | 경기/팀/사용자 조회 실패 |
| 409 | 충돌 (상태 불일치) | 이미 확정된 경기, 중복 회원가입, OPEN이 아닌 상태에서 투표 |
| 500 | 서버 에러 | DB 쿼리 실패 등 |

## 에러 메시지 목록

| 에러 | 코드 | 근거 |
|------|------|------|
| "인증이 필요합니다" | 401 | 모든 인증 필요 API |
| "팀에 소속되어 있지 않습니다" | 403 | `src/app/api/matches/route.ts:38` |
| "경기 생성 권한이 없습니다" | 403 | `src/app/api/matches/route.ts:79` |
| "경기 확정 권한이 없습니다" | 403 | `src/app/api/matches/[id]/confirm/route.ts:50` |
| "기록 입력 권한이 없습니다" | 403 | `src/app/api/matches/[id]/record/route.ts:78` |
| "멤버 추가 권한이 없습니다" | 403 | `src/app/api/teams/[teamId]/members/route.ts:65` |
| "역할 변경 권한이 없습니다" | 403 | `src/app/api/teams/[teamId]/members/route.ts:104` |
| "경기를 찾을 수 없습니다" | 404 | 경기 조회 실패 시 |
| "사용자를 찾을 수 없습니다" | 404 | `src/app/api/auth/me/route.ts:18` |
| "기록실이 없습니다" | 404 | `src/app/api/matches/[id]/record/route.ts:35` |
| "투표가 마감되었습니다" | 409 | `src/app/api/matches/[id]/attendance/route.ts:36` |
| "OPEN 상태의 경기만 수정할 수 있습니다" | 409 | `src/app/api/matches/[id]/route.ts:77` |
| "OPEN 상태의 경기만 확정할 수 있습니다" | 409 | `src/app/api/matches/[id]/confirm/route.ts:43` |
| "기록실이 마감되었습니다" | 409 | `src/app/api/matches/[id]/record/route.ts:90` |
| "이미 팀에 소속된 사용자입니다" | 409 | `src/app/api/teams/[teamId]/members/route.ts:84` |

## 검증 체크리스트
- [ ] 모든 API가 동일한 에러 포맷을 사용하는가?
- [ ] 401/403이 적절히 구분되는가? (인증 vs. 권한)
- [ ] 에러 메시지가 사용자에게 도움이 되는 한국어인가?

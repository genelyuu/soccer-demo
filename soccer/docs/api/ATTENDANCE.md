# 출석/투표 문서

> 근거: `src/app/api/matches/[id]/attendance/route.ts`, `src/features/attendance/`

## 자동 생성 규칙

경기 생성 시(POST /api/matches) 팀 소속 전체 멤버에 대해 Attendance 레코드가 자동 생성된다.
- 초기 상태: `PENDING`
- 근거: `src/app/api/matches/route.ts:94-102`

## 상태 모델

```
PENDING → ACCEPTED | DECLINED | MAYBE
```

| 상태 | 설명 | 투표 마감 전 변경 가능 |
|------|------|---------------------|
| PENDING | 미응답 (자동 생성 초기값) | - |
| ACCEPTED | 참석 | O |
| DECLINED | 불참 | O |
| MAYBE | 보류 | O |

## API

### PATCH /api/matches/{id}/attendance
- **설명**: 출석 투표 (참석/불참/보류)
- **권한**: 팀 소속 MEMBER 이상
- **제약**: 경기 상태가 `OPEN`일 때만 투표 가능
- **요청**: `{ "status": "ACCEPTED" | "DECLINED" | "MAYBE" }`
- **응답**: `{ "attendance": {...} }`
- 근거: `src/app/api/matches/[id]/attendance/route.ts`

## 검증 체크리스트
- [ ] 경기 생성 시 팀 전원에 대한 Attendance가 자동 생성되는가?
- [ ] OPEN 상태에서만 투표가 가능한가?
- [ ] 투표 변경이 가능한가 (ACCEPTED → DECLINED 등)?

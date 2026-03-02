# 기록실 (RecordRoom) 문서

> 근거: `src/app/api/matches/[id]/confirm/route.ts`, `src/app/api/matches/[id]/record/route.ts`

## 자동 전이 규칙

경기 확정(PATCH /api/matches/{id}/confirm) 시 RecordRoom이 자동으로 생성된다.
- 근거: `src/app/api/matches/[id]/confirm/route.ts:68-76`

### 이벤트 흐름
```
MatchConfirmed → RecordRoomCreated (자동)
```

## 멱등성

- `record_rooms.match_id`에 UNIQUE 제약이 있음
- 중복 확정 시: 이미 확정된 경기는 기존 기록실을 반환 (409가 아닌 200)
- 근거: `src/app/api/matches/[id]/confirm/route.ts:34-42`, `supabase/migrations/00001_initial_schema.sql:93`

## 실패/재시도 정책

- RecordRoom INSERT 실패 시 UNIQUE 위반 체크 후 기존 레코드 반환
- 경기 상태는 이미 CONFIRMED로 변경된 상태이므로 기록실만 재생성 시도
- [UNKNOWN] 트랜잭션 롤백 전략 (경기 확정 성공 + 기록실 생성 실패 시)

## API

### PATCH /api/matches/{id}/confirm
- **설명**: 경기 확정 + 기록실 자동 생성
- **권한**: MANAGER 이상
- **제약**: OPEN 상태만 확정 가능
- **응답**: `{ "match": {...}, "record_room": {...} }`
- 근거: `src/app/api/matches/[id]/confirm/route.ts`

### GET /api/matches/{id}/record
- **설명**: 기록실 조회 (기록 목록 포함)
- **권한**: 팀 소속 MEMBER 이상
- **응답**: `{ "record_room": {...}, "records": [...] }`

### POST /api/matches/{id}/record
- **설명**: 기록 입력/수정 (UPSERT)
- **권한**: MANAGER 이상
- **제약**: 기록실 상태가 OPEN일 때만 입력 가능
- **요청**: `{ "user_id": "...", "goals": 0, "assists": 0, "yellow_cards": 0, "red_cards": 0, "memo": "..." }`
- 근거: `src/app/api/matches/[id]/record/route.ts`

## 검증 체크리스트
- [ ] 경기 확정 시 기록실이 자동 생성되는가?
- [ ] 중복 확정 시 기존 기록실이 반환되는가 (멱등성)?
- [ ] 기록실 OPEN 상태에서만 기록 입력이 가능한가?

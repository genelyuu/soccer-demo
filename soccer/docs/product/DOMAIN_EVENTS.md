# 도메인 이벤트 흐름

> 근거: `.claude/tasks/easynext-football-mvp/0002.json`, `0007.json`
> 핵심 이벤트 4개: 생성/투표/확정/기록 + 자동 전이

## 엔터티 상태 전이

### Match (경기)

```
DRAFT → OPEN → CONFIRMED → COMPLETED → CANCELLED
  │        │        │           │
  │        │        │           └─ 기록 입력 완료 후
  │        │        └─ 운영자 확정 시 (자동: RecordRoom 생성)
  │        └─ 투표 시작 (자동: Attendance 레코드 생성)
  └─ 경기 생성 직후 → 즉시 OPEN으로 전이
```

| 상태 | 설명 | 전이 조건 |
|------|------|----------|
| `DRAFT` | 초안 (사용하지 않을 수 있음) | 경기 생성 시 |
| `OPEN` | 출석 투표 진행 중 | 경기 생성 직후 자동 전이 |
| `CONFIRMED` | 경기 확정, 기록 입력 가능 | 운영자 수동 확정 |
| `COMPLETED` | 기록 입력 완료 | 운영자 수동 완료 처리 |
| `CANCELLED` | 취소됨 | 언제든 운영자가 취소 가능 |

### Attendance (출석/투표)

```
PENDING → ACCEPTED / DECLINED / MAYBE
```

| 상태 | 설명 |
|------|------|
| `PENDING` | 아직 응답하지 않음 |
| `ACCEPTED` | 참석 |
| `DECLINED` | 불참 |
| `MAYBE` | 보류 |

### RecordRoom (기록실)

```
OPEN → CLOSED
```

| 상태 | 설명 |
|------|------|
| `OPEN` | 기록 입력 가능 |
| `CLOSED` | 기록 확정 (수정 불가) |

---

## 도메인 이벤트

### 1. MatchCreated (경기 생성)
- **트리거**: 운영자가 경기 일정을 등록
- **자동 후속 액션**:
  - 팀 소속 전체 멤버에 대한 `Attendance` 레코드 생성 (상태: PENDING)
  - 경기 상태를 `OPEN`으로 전이
- 근거: `.claude/tasks/easynext-football-mvp/0006.json:14`

```
MatchCreated
  ├─→ AttendanceBulkCreated (팀 멤버 수만큼)
  └─→ Match.status = OPEN
```

### 2. AttendanceVoted (출석 투표)
- **트리거**: 선수가 참석/불참/보류를 선택
- **후속 액션**: 투표 현황 업데이트
- 근거: `.claude/tasks/easynext-football-mvp/0006.json:17`

```
AttendanceVoted
  └─→ AttendanceSummary 갱신 (참석 N명, 불참 M명, 보류 K명)
```

### 3. MatchConfirmed (경기 확정)
- **트리거**: 운영자가 경기를 확정
- **자동 후속 액션**:
  - `RecordRoom` 자동 생성 (상태: OPEN)
  - 확정 참석자 명단 확정
- **멱등성**: 이미 확정된 경기를 다시 확정해도 중복 RecordRoom 생성 방지
- 근거: `.claude/tasks/easynext-football-mvp/0007.json:14-16`

```
MatchConfirmed
  ├─→ RecordRoomCreated (자동)
  ├─→ Match.status = CONFIRMED
  └─→ 확정 참석자 스냅샷 저장
```

### 4. RecordSubmitted (기록 입력)
- **트리거**: 운영자가 기록실에서 스탯을 입력
- **데이터**: 득점, 어시스트, 경고, 퇴장, 메모
- 근거: `.claude/tasks/easynext-football-mvp/0008.json`

```
RecordSubmitted
  └─→ PlayerStats 갱신
```

---

## 이벤트 흐름 전체 다이어그램

```
[운영자] 경기 생성
    │
    ▼
MatchCreated ──자동──→ AttendanceBulkCreated (팀 전원)
    │                        │
    ▼                        ▼
Match(OPEN)           Attendance(PENDING) × N명
                             │
                      [선수] 투표
                             │
                             ▼
                      AttendanceVoted
                      (ACCEPTED/DECLINED/MAYBE)
                             │
                      [운영자] 확정
                             │
                             ▼
                      MatchConfirmed ──자동──→ RecordRoomCreated
                             │                       │
                             ▼                       ▼
                      Match(CONFIRMED)        RecordRoom(OPEN)
                                                     │
                                              [운영자] 기록 입력
                                                     │
                                                     ▼
                                              RecordSubmitted
                                                     │
                                                     ▼
                                              Match(COMPLETED)
```

## [UNKNOWN]
- 이벤트 전파 방식: 동기 함수 호출 vs. 이벤트 버스 — MVP에서는 동기 호출로 시작
- 실패 시 재시도 정책 상세 (기록실 생성 실패 시)
- 알림 이벤트 (MatchConfirmed → 참석자에게 알림) — MVP 범위 밖 가능성

## 검증 체크리스트
- [ ] 핵심 이벤트 4개(생성/투표/확정/기록)가 모두 정의되었는가?
- [ ] 자동 전이 2개(경기 생성→투표 자동 생성, 확정→기록실 자동 생성)가 명시되었는가?
- [ ] 각 엔터티의 상태 전이가 명확한가?
- [ ] 멱등성 요구사항(중복 확정 방지)이 포함되었는가?

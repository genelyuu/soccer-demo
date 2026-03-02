# 대결/랭킹 최소 프로토타입 (Task 0010)

> 근거: `.claude/tasks/easynext-football-mvp/0010.json`
> 레퍼런스: ninety-minute-app, Soccer-Friend

## MVP에서 포함하는 범위

### 랭킹 계산 최소 규칙
- **승/무/패 기반**: 경기 결과(COMPLETED)의 득점 합계로 승패 판정
- **산출 데이터**: match_records 테이블의 goals 합계로 팀 총 득점 계산
- [UNKNOWN] 개인 랭킹 vs. 팀 랭킹 — MVP에서는 개인 스탯 요약만 제공

### 데이터 요구사항
- 기존 `match_records` 테이블로 충분 (추가 테이블 불필요)
- 집계 쿼리: `SELECT user_id, SUM(goals), SUM(assists) FROM match_records GROUP BY user_id`
- 근거: `supabase/migrations/00001_initial_schema.sql:104-117`

## MVP에서 제외하는 범위

| 기능 | 제외 이유 |
|------|---------|
| 팀 간 대결 매칭 | 스코프 초과 — 단일 팀 운영 루프에 집중 |
| ELO/글리코 랭킹 시스템 | 과잉 구현 — 승/무/패 카운트로 충분 |
| 랭킹 리더보드 UI | MVP 범위 밖 — 개인 프로필에서 스탯 확인으로 대체 |
| 대결 신청/수락 플로우 | 별도 팀 간 통신 필요 — MVP 후 설계 |

## API/화면 확장 포인트

| 항목 | 확장 방향 | 현재 상태 |
|------|---------|---------|
| GET /api/stats?user_id= | 개인 통산 스탯 조회 | [UNKNOWN] MVP 후반 구현 가능 |
| GET /api/teams/{id}/rankings | 팀 내 랭킹 | [UNKNOWN] 집계 쿼리로 구현 가능 |
| /rankings 페이지 | 리더보드 UI | [UNKNOWN] |
| 대결 매칭 API | 팀 간 매칭 요청/수락 | [UNKNOWN] 별도 엔터티 필요 |

## 검증 체크리스트
- [ ] 기존 match_records 스키마로 랭킹 데이터를 집계할 수 있는가?
- [ ] MVP 범위가 명확히 제한되었는가? (과잉 구현 방지)

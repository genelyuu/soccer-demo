# 기록실 UI 문서

> 근거: `src/app/matches/[id]/record/page.tsx`, `src/features/record/`

## 페이지: /matches/[id]/record

### 화면 구성
1. **기록실 상태 배지** — OPEN(입력 가능) / CLOSED(마감됨)
2. **기록 테이블** — 선수별 득점/어시스트/경고/퇴장/메모
3. **기록 입력 폼** — 선수 선택 후 스탯 입력 (OPEN 상태에서만)

### 최소 필드 (확장 가능 구조)
| 필드 | 타입 | 설명 |
|------|------|------|
| goals | number | 득점 |
| assists | number | 어시스트 |
| yellow_cards | number | 경고 |
| red_cards | number | 퇴장 |
| memo | string | 메모 |

### 상태 처리
- **로딩**: "기록실을 불러오는 중..."
- **에러 (기록실 없음)**: "기록실이 아직 생성되지 않았습니다. 경기를 먼저 확정해주세요."
- **빈 기록**: "아직 입력된 기록이 없습니다"

### UPSERT 동작
- 이미 입력된 선수의 기록을 수정하면 UPDATE로 동작
- 근거: `src/app/api/matches/[id]/record/route.ts:100` (onConflict)

## 검증 체크리스트
- [ ] 확정 전 경기의 기록실 접근 시 적절한 안내가 표시되는가?
- [ ] OPEN 상태에서만 기록 입력이 가능한가?
- [ ] 기존 기록 수정이 UPSERT로 동작하는가?

# 경기 관련 페이지 문서

> 근거: `src/app/matches/`, `src/features/match/`

## 페이지 구성

### /matches — 경기 목록
- **컴포넌트**: `src/app/matches/page.tsx`
- **상태**: 로딩 / 에러 / 빈 목록 / 목록 표시
- **권한**: MEMBER 이상 (팀 소속 확인은 API에서 수행)
- **기능**:
  - 경기 목록을 카드 형태로 표시
  - 각 카드에 경기명, 날짜, 장소, 상대팀, 상태 배지 표시
  - [+] 새 경기 버튼 (MANAGER+ 전용 — UI에서는 항상 표시, API에서 권한 체크)
- 근거: `src/features/match/components/match-list.tsx`, `match-card.tsx`

### /matches/new — 경기 생성
- **컴포넌트**: `src/app/matches/new/page.tsx`
- **폼 필드**: 경기명(필수), 경기 일시(필수), 장소, 상대팀, 설명
- **검증**: zod 스키마 (`src/app/api/matches/route.ts:8-15`)
- **성공 시**: /matches로 리다이렉트
- **안내**: "경기 생성 시 팀 멤버 전원에게 출석 투표가 자동으로 생성됩니다"
- 근거: `src/features/match/components/create-match-form.tsx`

### /matches/[id] — 경기 상세
- **컴포넌트**: `src/app/matches/[id]/page.tsx`
- **표시 정보**: 경기 기본 정보 + 출석 투표 현황
- **투표 현황**: 참석/불참/대기 인원수 + 멤버별 투표 상태
- **액션**:
  - CONFIRMED 상태 시 "기록실 바로가기" 버튼 표시
- 근거: `src/app/matches/[id]/page.tsx`

## API 연동

| API | 메서드 | 용도 | 근거 |
|-----|--------|------|------|
| `/api/matches?team_id=` | GET | 경기 목록 | `src/app/api/matches/route.ts:20` |
| `/api/matches` | POST | 경기 생성 + 출석 자동 생성 | `src/app/api/matches/route.ts:56` |
| `/api/matches/[id]` | GET | 경기 상세 + 투표 현황 | `src/app/api/matches/[id]/route.ts:15` |
| `/api/matches/[id]` | PATCH | 경기 수정 (OPEN 상태만) | `src/app/api/matches/[id]/route.ts:57` |

## 상태별 UI

| 경기 상태 | 배지 색상 | 가능한 액션 |
|----------|---------|------------|
| OPEN (투표 중) | 파랑 | 투표, 수정 |
| CONFIRMED (확정) | 초록 | 기록실 이동 |
| COMPLETED (완료) | 회색 | 기록 조회만 |
| CANCELLED (취소) | 빨강 | - |

근거: `src/features/match/constants/index.ts`

## 에러/로딩 처리

- **로딩**: "경기 목록을 불러오는 중..." / "경기 정보를 불러오는 중..."
- **에러**: "경기 목록을 불러오는데 실패했습니다"
- **빈 상태**: "등록된 경기가 없습니다"

## [UNKNOWN]
- 캘린더 뷰 구현 (현재 리스트 뷰만 구현, 캘린더 라이브러리 미선택)
- 경기 삭제 기능 (MVP 범위 여부)
- 무한 스크롤/페이지네이션 (경기 수 증가 시)

## 검증 체크리스트
- [ ] 경기 생성 시 출석/투표가 자동 준비되도록 UI에 안내가 있는가?
- [ ] 상태별 배지 색상이 구분되는가?
- [ ] 로딩/에러/빈 상태가 모두 처리되었는가?

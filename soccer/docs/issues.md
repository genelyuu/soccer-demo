# MVP 품질 비판 이슈 목록

> 근거: 코드 리뷰 2026-02-10, skeptic 관점 분석
> 분류: P(성능), S(속도), A(미감)

## 이슈 요약

| ID | 분류 | 심각도 | 이슈 | 현재 상태 | 영향 범위 | 담당 |
|----|------|--------|------|----------|----------|------|
| I-01 | P | **높음** | 전체 페이지 `'use client'` — SSR 이점 제로 | 모든 page.tsx가 CSR | 전체 | frontend |
| I-02 | P | **높음** | 홈 페이지 워터폴 요청 (useSession→useTeams→useMatches 직렬) | page.tsx:210 | 홈 | frontend |
| I-03 | P | **중간** | 경기 목록 클라이언트 필터링 — 페이지네이션/서버 필터 없음 | match-list.tsx:33-46 | /matches | backend+frontend |
| I-04 | P | **중간** | framer-motion 번들 비용 (186-212KB First Load JS) | 전체 모션 컴포넌트 | 전체 | frontend |
| I-05 | P | **낮음** | StaggerItem마다 useReducedMotion() 중복 호출 | stagger-list.tsx:54 | 리스트 페이지 | frontend |
| I-06 | P | **낮음** | `(r as any).users?.name` 타입 안전성 포기 | record/page.tsx:137 | 기록실 | backend |
| I-07 | S | **중간** | CSR 3단계 렌더링 (빈화면→스켈레톤→데이터) 체감 속도 저하 | 모든 페이지 | 전체 | frontend |
| I-08 | S | **중간** | React Query staleTime/gcTime 미설정 — 매번 refetch | 모든 useQuery | 전체 | frontend |
| I-09 | S | **낮음** | PageTransition 0.2s fade-in이 오히려 체감 속도 저하 | page-transition.tsx | 전체 | frontend |
| I-10 | S | **낮음** | Zustand hydration 전 팀 선택기 깜빡임 | team-selector.tsx | 헤더 | frontend |
| I-11 | A | **높음** | 브랜드 정체성 제로 — shadcn 기본 흑백 테마 그대로 | globals.css, tailwind.config.ts | 전체 | design |
| I-12 | A | **높음** | 헤더에 로고/아이콘 없음, 브랜드 컬러 없음 | header.tsx | 헤더 | design |
| I-13 | A | **중간** | 경기 상태별 시각적 차이가 Badge 텍스트 하나뿐 | match-card.tsx:23 | /matches | design |
| I-14 | A | **중간** | GuestLanding이 단조로움 — 이미지/특징 설명 없음 | page.tsx:20-38 | 홈(비로그인) | design |
| I-15 | A | **중간** | 홈 대시보드 정보 밀도 낮음 — 숫자 요약/KPI 없음 | page.tsx:148-206 | 홈 | frontend |
| I-16 | A | **중간** | 기록실 테이블 raw HTML — shadcn Table 미사용, 모바일 UX 불량 | record/page.tsx:122-157 | 기록실 | frontend |
| I-17 | A | **낮음** | 로그인 페이지 min-h-screen + 헤더 충돌 | signin/page.tsx:42 | 로그인 | frontend |
| I-18 | A | **낮음** | 다크모드 .dark CSS 정의 있으나 토글 UI 없음 | globals.css:34-59 | 전체 | design |
| I-19 | A | **낮음** | 타이포그래피 단조 — weight/size 변화 부족 | 전체 | 전체 | design |

## 브랜드 정체성 설정

> 근거: soccer_rnd 프로젝트 도메인 분석 (스포츠 사이언스 + 데이터 기반 운영)

### 컨셉: "데이터로 움직이는 동호회"
soccer_rnd의 스포츠 사이언스 DNA(ATL/CTL/ACWR, HRV 지표)를 반영하여, 단순 일정 관리가 아닌 **데이터 기반 운영**을 지향하는 브랜드.

### 컬러 팔레트

| 토큰 | HSL | Hex | 용도 |
|------|-----|-----|------|
| **pitch-green** (primary) | `142 64% 42%` | #26A54A | 주요 액션, 잔디/그라운드 |
| **sky-blue** (accent) | `210 80% 56%` | #2E8EE6 | 보조 강조, 하늘/전략 |
| **whistle-amber** | `38 92% 56%` | #F0A020 | 경고/알림, 심판 호루라기 |
| **card-red** (destructive) | `0 72% 56%` | #D94040 | 위험/삭제, 레드카드 |
| **turf-dark** | `142 30% 18%` | #203D28 | 다크 배경, 짙은 잔디 |
| **chalk-white** | `0 0% 98%` | #FAFAFA | 라이트 배경, 라인 |

### 타이포그래피
- 제목: **Geist Sans Bold** + letter-spacing tight
- 본문: Geist Sans Regular
- 숫자/KPI: **Geist Mono** (데이터 강조)
- 크기 체계: text-xs / text-sm / text-base / text-lg / text-xl / text-2xl / text-4xl

### 아이콘/로고
- 헤더 로고: lucide-react `Trophy` 아이콘 + "PITCH" 텍스트
- 앱 이름 변경: "축구 동호회" → **"PITCH"** (간결하고 기억하기 쉬운 영문 브랜드)
- 부제: "데이터로 움직이는 동호회 운영"

### 상태 시각화
| 상태 | 배경 | 아이콘 | 카드 테두리 |
|------|------|--------|-----------|
| OPEN | pitch-green/10 | Circle (투표 진행) | left-border green |
| CONFIRMED | sky-blue/10 | CheckCircle | left-border blue |
| COMPLETED | muted | Archive | left-border gray |
| CANCELLED | destructive/10 | XCircle | left-border red |

## 우선순위 실행 계획

### Phase 1: 브랜드 + 디자인 기반 (독립)
- I-11, I-12, I-13, I-18, I-19 → design 트랙

### Phase 2: 성능 + 속도 (병렬)
- I-02, I-04, I-05, I-06, I-08, I-09, I-10 → frontend 트랙
- I-03 → backend + frontend

### Phase 3: UX 개선 (Phase 1 완료 후)
- I-14, I-15, I-16, I-17 → frontend 트랙 (새 브랜드 적용 필요)

### 보류 (구조 변경 필요)
- I-01, I-07 → SSR 전환은 대규모 리팩터링. 현 MVP에서는 React Query prefetch + staleTime으로 대체.

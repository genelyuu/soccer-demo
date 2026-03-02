# SOLID 체크리스트 (Task 0018)

> 근거: `.claude/teams/config.json:86`

## 현재 아키텍처 SOLID 평가

### S — 단일 책임 원칙 (Single Responsibility)
- [x] API 라우트: 각 파일이 하나의 리소스만 담당
  - `src/app/api/matches/route.ts` — 경기 목록/생성
  - `src/app/api/matches/[id]/route.ts` — 경기 상세/수정
  - `src/app/api/matches/[id]/confirm/route.ts` — 경기 확정
  - `src/app/api/matches/[id]/record/route.ts` — 기록 관리
- [x] Feature 모듈: api.ts / hooks / components / constants 분리
- [ ] API 라우트 내 비즈니스 로직 분리 필요 — 현재 라우트에 직접 구현

### O — 개방-폐쇄 원칙 (Open-Closed)
- [x] 타입 시스템: ENUM으로 상태 정의, 새 상태 추가 시 타입 레벨 강제
- [x] 컴포넌트: shadcn/ui 래핑으로 확장 가능
- [ ] 권한 체크 로직이 각 라우트에 인라인 — 미들웨어로 추출 필요

### L — 리스코프 치환 원칙 (Liskov Substitution)
- [x] Supabase 클라이언트: createClient / createPureClient로 용도별 분리
- N/A — 클래스 상속 미사용 (함수형 패러다임)

### I — 인터페이스 분리 원칙 (Interface Segregation)
- [x] 타입 정의: 엔터티별 개별 인터페이스 (`src/lib/types.ts`)
- [x] API 응답: 필요한 필드만 select

### D — 의존성 역전 원칙 (Dependency Inversion)
- [x] Supabase 클라이언트: `src/lib/supabase/` 어댑터 계층으로 분리
- [x] 인증: NextAuth 어댑터로 분리 (`src/lib/auth.ts`)
- [ ] 도메인 서비스 레이어 부재 — API 라우트가 직접 DB 접근

## 리팩터링 제안 (MVP 후)

1. **도메인 서비스 추출**: API 라우트 → 도메인 서비스 → 리포지토리
2. **권한 미들웨어**: 각 라우트의 인라인 체크 → 공통 미들웨어/가드
3. **이벤트 버스**: 동기 호출 → 도메인 이벤트 발행/구독

## 검증 체크리스트
- [ ] 도메인/인프라/프레젠테이션 경계가 식별 가능한가?
- [ ] 외부 의존성(Supabase)이 어댑터 계층으로 격리되었는가?
- [ ] 테스트 보호 없이 구조 변경이 이루어지지 않았는가?

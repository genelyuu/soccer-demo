# 화면 IA (Information Architecture)

> 근거: `.claude/tasks/easynext-football-mvp/0002.json`, `0005.json`, `0008.json`, `0009.json`
> 디렉토리 구조 규칙: `.cursor/rules/global.mdc:35-46`

## 페이지 목록

| 경로 | 페이지명 | 설명 | 권한 | 태스크 근거 |
|------|---------|------|------|------------|
| `/` | 홈/대시보드 | 다가오는 경기, 최근 기록 요약 | 로그인 필수 | - |
| `/auth/signin` | 로그인 | 이메일/비밀번호 로그인 | 공개 | `0004.json` |
| `/auth/signup` | 회원가입 | 계정 생성 | 공개 | `0004.json` |
| `/matches` | 경기 목록 | 리스트/캘린더 뷰 | MEMBER+ | `0005.json` |
| `/matches/new` | 경기 생성 | 일정 등록 폼 | MANAGER+ | `0005.json` |
| `/matches/[id]` | 경기 상세 | 투표 현황, 경기 정보 | MEMBER+ | `0005.json` |
| `/matches/[id]/record` | 기록실 | 스탯/메모 입력/조회 | MEMBER+ (입력: MANAGER+) | `0008.json` |
| `/team` | 팀 정보 | 팀 설정, 기본 정보 | MEMBER+ | `0009.json` |
| `/team/members` | 멤버 관리 | 멤버 목록, 초대, 역할 | MANAGER+ (조회: MEMBER+) | `0009.json` |

## 네비게이션 구조

```
┌─────────────────────────────────────┐
│  🏠 로고/홈   ⚽ 경기   👥 팀   👤 프로필  │  ← 하단 탭 (모바일) / 사이드바 (데스크톱)
└─────────────────────────────────────┘
```

### 주 네비게이션 (Bottom Tab / Sidebar)
1. **홈** (`/`) — 대시보드
2. **경기** (`/matches`) — 경기 목록 (리스트/캘린더 전환)
3. **팀** (`/team`) — 팀 정보/멤버
4. **프로필** — 내 정보, 로그아웃

### 경기 상세 내부 탭
- **정보** — 일시, 장소, 상대팀
- **투표** — 출석/투표 현황 + 내 투표
- **기록** — 기록실 (확정 후 활성화)

## 화면 흐름

### 운영자 핵심 플로우
```
홈 → 경기 목록 → [+] 경기 생성 → (자동: 투표 생성)
→ 경기 상세 (투표 현황 확인) → [확정] 버튼
→ 기록실 (스탯 입력) → 완료
```

### 선수 핵심 플로우
```
홈 → 경기 목록 → 경기 상세 → [참석/불참/보류] 투표
→ (확정 후) 기록실 조회
```

## 레이아웃 구조

```
src/app/
├── layout.tsx                    # 루트 레이아�트 (providers, 폰트)
├── page.tsx                      # 홈/대시보드
├── auth/
│   ├── signin/page.tsx           # 로그인
│   └── signup/page.tsx           # 회원가입
├── matches/
│   ├── page.tsx                  # 경기 목록
│   ├── new/page.tsx              # 경기 생성
│   └── [id]/
│       ├── page.tsx              # 경기 상세
│       └── record/page.tsx       # 기록실
└── team/
    ├── page.tsx                  # 팀 정보
    └── members/page.tsx          # 멤버 관리
```

## 기능별 Feature 디렉토리

```
src/features/
├── auth/                         # 인증 관련
│   ├── components/
│   ├── hooks/
│   ├── lib/
│   └── api.ts
├── match/                        # 경기 관련
│   ├── components/
│   ├── hooks/
│   ├── lib/
│   ├── constants/
│   └── api.ts
├── attendance/                   # 출석/투표
│   ├── components/
│   ├── hooks/
│   └── api.ts
├── record/                       # 기록실
│   ├── components/
│   ├── hooks/
│   └── api.ts
└── team/                         # 팀/멤버
    ├── components/
    ├── hooks/
    └── api.ts
```

## 반응형 전략

- **모바일 퍼스트**: 하단 탭 네비게이션
- **데스크톱**: 사이드바 네비게이션으로 전환
- [UNKNOWN] 구체적 브레이크포인트 — Tailwind 기본값 사용 예정 (sm: 640px, md: 768px, lg: 1024px)

## [UNKNOWN]
- 다크모드 지원 범위 (ThemeProvider 설정은 있으나 디자인 토큰 미확정)
- 알림 페이지/패널 구조
- 경기 캘린더 뷰의 라이브러리 선택

## 검증 체크리스트
- [ ] 운영 루프 4단계 각각에 대응하는 페이지가 존재하는가?
- [ ] 운영자/선수별 접근 가능 페이지가 권한 기준으로 구분되었는가?
- [ ] 네비게이션에서 핵심 페이지로의 접근이 2탭 이내인가?
- [ ] Feature 디렉토리가 `.cursor/rules/global.mdc:42-46` 규칙을 따르는가?

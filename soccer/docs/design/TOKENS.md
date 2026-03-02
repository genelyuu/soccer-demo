# 디자인 토큰 명세 (Task 0014)

> 근거: `tailwind.config.ts`, `src/app/globals.css`
> 소스: shadcn/ui 기본 테마 + EasyNext 템플릿

## 컬러 토큰

shadcn/ui CSS 변수 기반. Tailwind 유틸리티 클래스로 접근.

| 토큰 | CSS 변수 | Tailwind 클래스 | 용도 | 근거 |
|------|---------|----------------|------|------|
| background | --background | bg-background | 페이지 배경 | `tailwind.config.ts:20` |
| foreground | --foreground | text-foreground | 기본 텍스트 | `tailwind.config.ts:21` |
| primary | --primary | bg-primary, text-primary | 주요 액션 (버튼, 링크) | `tailwind.config.ts:22-25` |
| secondary | --secondary | bg-secondary | 보조 액션 | `tailwind.config.ts:26-29` |
| destructive | --destructive | bg-destructive, text-destructive | 위험/삭제 | `tailwind.config.ts:30-33` |
| muted | --muted | text-muted-foreground | 비활성/보조 텍스트 | `tailwind.config.ts:34-37` |
| accent | --accent | bg-accent | 강조/hover | `tailwind.config.ts:38-41` |
| card | --card | bg-card | 카드 배경 | `tailwind.config.ts:46-49` |
| border | --border | border | 테두리 | `tailwind.config.ts:17` |
| input | --input | | 입력 필드 테두리 | `tailwind.config.ts:18` |
| ring | --ring | ring | 포커스 링 | `tailwind.config.ts:19` |

### 경기 상태별 컬러

| 상태 | 클래스 | 근거 |
|------|--------|------|
| OPEN (투표 중) | `bg-blue-100 text-blue-800` | `src/features/match/constants/index.ts:9` |
| CONFIRMED (확정) | `bg-green-100 text-green-800` | |
| COMPLETED (완료) | `bg-gray-100 text-gray-800` | |
| CANCELLED (취소) | `bg-red-100 text-red-800` | |

## 타이포그래피

| 용도 | 클래스 | 근거 |
|------|--------|------|
| 페이지 제목 | `text-2xl font-bold` | 실제 사용 패턴 |
| 카드 제목 | `text-lg` (CardTitle) | shadcn CardTitle |
| 본문 | 기본 (16px) | Tailwind 기본 |
| 보조 텍스트 | `text-sm text-muted-foreground` | 실제 사용 패턴 |
| 에러 메시지 | `text-sm text-destructive` | 실제 사용 패턴 |
| 폰트 | Geist Sans / Geist Mono | `src/app/layout.tsx:6-13` |

## 스페이싱

Tailwind 기본 4px 단위. 주요 사용 패턴:
- 컨테이너 패딩: `container py-6` (`tailwind.config.ts:9-10`, padding: 2rem)
- 요소 간 간격: `space-y-4`, `space-y-6`, `gap-2`, `gap-4`
- 카드 내부: CardContent 기본 패딩

## 라디우스

| 크기 | CSS 변수 | 근거 |
|------|---------|------|
| lg | --radius | `tailwind.config.ts:52` |
| md | calc(--radius - 2px) | `tailwind.config.ts:53` |
| sm | calc(--radius - 4px) | `tailwind.config.ts:54` |

## 규칙
- **임의 색/간격 사용 금지** — 토큰 기반만 허용
- 새로운 색상이 필요하면 globals.css에 CSS 변수 추가 후 tailwind.config.ts에 등록

## [UNKNOWN]
- 다크모드 토큰 값 (ThemeProvider 설정은 있으나 다크모드 CSS 변수 미정의)
- Figma 연동 (현재 코드 기반으로 역산)

## 검증 체크리스트
- [ ] 모든 UI에서 토큰 기반 클래스만 사용하는가?
- [ ] 하드코딩된 hex/rgb 값이 없는가?

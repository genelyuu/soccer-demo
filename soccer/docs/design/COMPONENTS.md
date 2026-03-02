# 컴포넌트 규격 문서 (Task 0015)

> 근거: `src/components/ui/`, `components.json`

## 기본 UI 컴포넌트 (shadcn/ui)

| 컴포넌트 | 파일 | 용도 | 근거 |
|---------|------|------|------|
| Button | `src/components/ui/button.tsx` | 모든 액션 버튼 | variants: default/destructive/outline/secondary/ghost/link |
| Input | `src/components/ui/input.tsx` | 텍스트 입력 | |
| Textarea | `src/components/ui/textarea.tsx` | 여러 줄 입력 | |
| Card | `src/components/ui/card.tsx` | 카드 컨테이너 | CardHeader/CardTitle/CardDescription/CardContent |
| Badge | `src/components/ui/badge.tsx` | 상태 배지 | variants: default/secondary/destructive/outline |
| Label | `src/components/ui/label.tsx` | 폼 레이블 | |
| Form | `src/components/ui/form.tsx` | react-hook-form 연동 | |
| Select | `src/components/ui/select.tsx` | 드롭다운 선택 | |
| Sheet | `src/components/ui/sheet.tsx` | 슬라이드 패널 | |
| Toast | `src/components/ui/toast.tsx` | 알림 토스트 | |
| Toaster | `src/components/ui/toaster.tsx` | 토스트 프로바이더 | |
| Accordion | `src/components/ui/accordion.tsx` | 접이식 패널 | |
| Avatar | `src/components/ui/avatar.tsx` | 사용자 프로필 이미지 | |
| Checkbox | `src/components/ui/checkbox.tsx` | 체크박스 | |
| Dialog | (import from radix) | 모달 다이얼로그 | |
| DropdownMenu | `src/components/ui/dropdown-menu.tsx` | 드롭다운 메뉴 | |
| Separator | `src/components/ui/separator.tsx` | 구분선 | |

## 프로젝트 전용 컴포넌트

| 컴포넌트 | 파일 | 용도 |
|---------|------|------|
| MatchCard | `src/features/match/components/match-card.tsx` | 경기 카드 (목록용) |
| MatchList | `src/features/match/components/match-list.tsx` | 경기 목록 |
| CreateMatchForm | `src/features/match/components/create-match-form.tsx` | 경기 생성 폼 |
| VoteButtons | `src/features/attendance/components/vote-buttons.tsx` | 출석 투표 버튼 |
| ConfirmButton | `src/features/attendance/components/confirm-button.tsx` | 경기 확정 버튼 |
| AuthProvider | `src/components/auth/auth-provider.tsx` | NextAuth 세션 프로바이더 |

## 접근성 체크리스트 (초안)

- [ ] 모든 인터랙티브 요소에 키보드로 접근 가능한가?
- [ ] 폼 필드에 적절한 label이 연결되어 있는가? (htmlFor/id)
- [ ] 에러 메시지가 시각적 + aria-live로 전달되는가? [UNKNOWN]
- [ ] 포커스 링이 명확히 보이는가? (ring 토큰 사용)
- [ ] 버튼의 disabled 상태에서 aria-disabled가 적용되는가?
- [ ] 색상만으로 정보를 전달하지 않는가? (배지 텍스트 + 색상 조합)

## 규칙
- 모든 페이지는 공통 컴포넌트 사용 (중복 스타일 금지)
- 새 shadcn 컴포넌트 추가: `npx shadcn@latest add [component]`
  - 근거: `.cursor/rules/global.mdc:158-163`

## 검증 체크리스트
- [ ] 모든 페이지에서 공통 컴포넌트를 사용하는가?
- [ ] 인라인 스타일이나 중복 CSS 클래스가 없는가?

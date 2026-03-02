# 디자인 적용 문서 (Task 0017)

> 근거: `docs/design/TOKENS.md`, `docs/design/COMPONENTS.md`, `docs/design/MOTION.md`

## 적용 범위

### 토큰 적용 현황

| 페이지 | 컬러 토큰 | 타이포 | 스페이싱 | 상태 |
|--------|---------|-------|---------|------|
| /auth/signin | O | O | O | 완료 |
| /auth/signup | O | O | O | 완료 |
| /matches | O | O | O | 완료 |
| /matches/new | O | O | O | 완료 |
| /matches/[id] | O | O | O | 완료 |
| /matches/[id]/record | O | O | O | 완료 |
| /team | O | O | O | 완료 |
| /team/members | O | O | O | 완료 |

### 컴포넌트 적용 현황

모든 페이지에서 shadcn/ui 공통 컴포넌트 사용 확인:
- Button, Input, Card, Badge, Label, Textarea — 전체 적용
- 인라인 스타일 사용: 없음
- 중복 CSS 클래스: 없음

### 모션 적용 현황

| 패턴 | 적용 | 상태 |
|------|------|------|
| 페이지 전환 | [UNKNOWN] | 래퍼 미적용 |
| 리스트 진입 | [UNKNOWN] | 래퍼 미적용 |
| 모달/시트 | shadcn 내장 | 적용됨 |
| 토스트 | shadcn 내장 | 적용됨 |

> MVP에서는 shadcn 내장 애니메이션만 사용. framer-motion 래퍼는 후속 작업.

## 검증 체크리스트
- [ ] 토큰 미준수 발견 시 리팩터링이 테스트 보호 후 수행되었는가?
- [ ] 모든 페이지에서 공통 컴포넌트를 사용하는가?

# 모션 시스템 문서 (Task 0016)

> 근거: framer-motion (`package.json:35`), tailwindcss-animate (`package.json:59`)
> 원칙: 상태 변화 중심의 절제된 애니메이션. 과도한 장식 금지.

## 4개 표준 패턴

### 1. 페이지 전환 (Page Transition)
```tsx
// 사용: 라우트 변경 시
const pageVariants = {
  initial: { opacity: 0, y: 8 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -8 },
};

const pageTransition = {
  duration: 0.2,
  ease: "easeOut",
};
```

### 2. 리스트 진입 (List Stagger)
```tsx
// 사용: 카드 목록, 멤버 목록 등
const listVariants = {
  animate: {
    transition: { staggerChildren: 0.05 },
  },
};

const itemVariants = {
  initial: { opacity: 0, y: 4 },
  animate: { opacity: 1, y: 0 },
};
```

### 3. 모달/시트 (Modal/Sheet)
```tsx
// 사용: Dialog, Sheet 열기/닫기
// shadcn/ui + Radix 내장 애니메이션 사용
// tailwindcss-animate의 기본 키프레임 활용
```

### 4. 토스트 (Toast)
```tsx
// 사용: 성공/에러 알림
// shadcn toast 컴포넌트의 내장 애니메이션 사용
// 근거: src/components/ui/toast.tsx
```

## 사용 규칙

1. **상태 변화에만 적용** — 정적 요소에 애니메이션 금지
2. **duration 0.2s 이하** — 빠르고 절제된 모션
3. **ease-out 기본** — 자연스러운 감속
4. **과도한 scale/rotate 금지** — opacity/translate만 사용
5. **산재된 애니메이션 구현 금지** — 위 4개 패턴만 사용

## prefers-reduced-motion 대응

```tsx
// framer-motion 자동 대응
// <motion.div> 컴포넌트는 prefers-reduced-motion: reduce 시 자동으로 애니메이션 비활성화

// CSS 레벨 대응
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

## 모션 유틸 래퍼 [UNKNOWN — 필요 시 구현]

| 컴포넌트 | 용도 | 상태 |
|---------|------|------|
| MotionPage | 페이지 전환 래퍼 | 패턴 정의됨, 래퍼 미구현 |
| MotionListItem | 리스트 항목 진입 | 패턴 정의됨, 래퍼 미구현 |
| MotionModal | 모달 애니메이션 | shadcn 내장 사용 |

> MVP에서는 패턴만 정의하고, 0017 태스크에서 실제 적용

## 검증 체크리스트
- [ ] 정적 요소에 불필요한 애니메이션이 적용되지 않았는가?
- [ ] prefers-reduced-motion 설정 시 모션이 비활성화되는가?
- [ ] 표준 4개 패턴 외의 애니메이션이 사용되지 않았는가?

'use client';

import { motion, useReducedMotion, AnimatePresence } from 'framer-motion';
import type { ReactNode } from 'react';

const toastVariants = {
  initial: { opacity: 0, x: 100 },
  animate: { opacity: 1, x: 0 },
  exit: { opacity: 0, x: 100 },
};

const toastTransition = {
  duration: 0.2,
  ease: 'easeOut' as const,
};

interface ToastMotionProps {
  children: ReactNode;
  isVisible: boolean;
  className?: string;
}

/**
 * 토스트 slide-in 애니메이션 래퍼.
 *
 * 참고: shadcn/ui Toast 컴포넌트는 tailwindcss-animate 기반
 * 내장 애니메이션을 사용하므로, 기본 Toaster에서는 이 래퍼가 불필요.
 * 커스텀 토스트 UI가 필요한 경우에만 사용.
 */
export function ToastMotion({ children, isVisible, className }: ToastMotionProps) {
  const shouldReduceMotion = useReducedMotion();

  if (shouldReduceMotion) {
    return isVisible ? <div className={className}>{children}</div> : null;
  }

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial="initial"
          animate="animate"
          exit="exit"
          variants={toastVariants}
          transition={toastTransition}
          className={className}
        >
          {children}
        </motion.div>
      )}
    </AnimatePresence>
  );
}

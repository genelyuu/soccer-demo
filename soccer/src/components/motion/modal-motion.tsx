'use client';

import { motion, useReducedMotion, AnimatePresence } from 'framer-motion';
import type { ReactNode } from 'react';

const overlayVariants = {
  initial: { opacity: 0 },
  animate: { opacity: 1 },
  exit: { opacity: 0 },
};

const contentVariants = {
  initial: { opacity: 0, scale: 0.95 },
  animate: { opacity: 1, scale: 1 },
  exit: { opacity: 0, scale: 0.95 },
};

const modalTransition = {
  duration: 0.15,
  ease: 'easeOut' as const,
};

interface ModalMotionProps {
  children: ReactNode;
  isOpen: boolean;
  className?: string;
}

/** 모달 콘텐츠 scale + fade 애니메이션 래퍼 */
export function ModalMotion({ children, isOpen, className }: ModalMotionProps) {
  const shouldReduceMotion = useReducedMotion();

  if (shouldReduceMotion) {
    return isOpen ? <div className={className}>{children}</div> : null;
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial="initial"
          animate="animate"
          exit="exit"
          variants={contentVariants}
          transition={modalTransition}
          className={className}
        >
          {children}
        </motion.div>
      )}
    </AnimatePresence>
  );
}

interface ModalOverlayMotionProps {
  isOpen: boolean;
  className?: string;
}

/** 모달 오버레이 fade 애니메이션 */
export function ModalOverlayMotion({ isOpen, className }: ModalOverlayMotionProps) {
  const shouldReduceMotion = useReducedMotion();

  if (shouldReduceMotion) {
    return isOpen ? <div className={className} /> : null;
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial="initial"
          animate="animate"
          exit="exit"
          variants={overlayVariants}
          transition={modalTransition}
          className={className}
        />
      )}
    </AnimatePresence>
  );
}

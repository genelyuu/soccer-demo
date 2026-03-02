'use client';

import { createContext, useContext } from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import type { ReactNode } from 'react';

const ReducedMotionContext = createContext(false);

const listVariants = {
  animate: {
    transition: { staggerChildren: 0.05 },
  },
};

const itemVariants = {
  initial: { opacity: 0, y: 4 },
  animate: { opacity: 1, y: 0 },
};

const itemTransition = {
  duration: 0.2,
  ease: 'easeOut' as const,
};

interface StaggerListProps {
  children: ReactNode;
  className?: string;
}

/** 리스트 항목 순차 진입 컨테이너 */
export function StaggerList({ children, className }: StaggerListProps) {
  const shouldReduceMotion = useReducedMotion();
  const reduced = !!shouldReduceMotion;

  if (reduced) {
    return (
      <ReducedMotionContext.Provider value={true}>
        <div className={className}>{children}</div>
      </ReducedMotionContext.Provider>
    );
  }

  return (
    <ReducedMotionContext.Provider value={false}>
      <motion.div
        initial="initial"
        animate="animate"
        variants={listVariants}
        className={className}
      >
        {children}
      </motion.div>
    </ReducedMotionContext.Provider>
  );
}

interface StaggerItemProps {
  children: ReactNode;
  className?: string;
}

/** 리스트 항목 순차 진입 아이템 (StaggerList 내부에서 사용) */
export function StaggerItem({ children, className }: StaggerItemProps) {
  const shouldReduceMotion = useContext(ReducedMotionContext);

  if (shouldReduceMotion) {
    return <div className={className}>{children}</div>;
  }

  return (
    <motion.div
      variants={itemVariants}
      transition={itemTransition}
      className={className}
    >
      {children}
    </motion.div>
  );
}

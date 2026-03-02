'use client';

import type { ReactNode } from 'react';
import { cn } from '@/lib/utils';

interface PageTransitionProps {
  children: ReactNode;
  className?: string;
}

/** 페이지 전환 애니메이션 래퍼 (CSS @keyframes fade + slide-up, framer-motion 미사용) */
export function PageTransition({ children, className }: PageTransitionProps) {
  return (
    <div className={cn('animate-page-in', className)}>
      {children}
    </div>
  );
}

import React, { useEffect, useState } from 'react';

interface ApprovalStampProps {
  status: 'approved' | 'rejected';
  onAnimationEnd?: () => void;
}

export const ApprovalStamp: React.FC<ApprovalStampProps> = ({ status, onAnimationEnd }) => {
  const [shouldAnimate, setShouldAnimate] = useState(true);

  useEffect(() => {
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReducedMotion) {
      setShouldAnimate(false);
      if (onAnimationEnd) onAnimationEnd();
    }
  }, [onAnimationEnd]);

  const colorClass = status === 'approved' ? 'text-success drop-shadow-[0_0_15px_rgba(16,185,129,0.5)]' : 'text-danger drop-shadow-[0_0_15px_rgba(239,68,68,0.5)]';
  const bgClass = status === 'approved' ? 'bg-success/10 border-success/30' : 'bg-danger/10 border-danger/30';
  const animationClass = shouldAnimate ? 'motion-safe:animate-[statusPop_400ms_ease-out_forwards]' : '';

  return (
    <div 
      className={`absolute inset-0 z-10 pointer-events-none rounded-2xl flex items-center justify-center backdrop-blur-[2px] opacity-100 ${animationClass}`}
      onAnimationEnd={onAnimationEnd}
    >
      <div className={`flex flex-col items-center justify-center gap-2 p-6 rounded-2xl border backdrop-blur-md ${bgClass}`}>
        <svg 
          width="48" height="48" viewBox="0 0 24 24" 
          fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"
          className={`${colorClass}`} 
        >
          {status === 'approved' ? (
            <path d="M20 6L9 17l-5-5" />
          ) : (
            <path d="M18 6L6 18M6 6l12 12" />
          )}
        </svg>
        <span className={`text-lg font-bold tracking-widest uppercase ${colorClass}`}>
          {status}
        </span>
      </div>
    </div>
  );
};

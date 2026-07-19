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

  const colorClass = status === 'approved' ? 'text-[#5c7264]' : 'text-[#825b5b]';
  const bgClass = status === 'approved' ? 'bg-success/20 border-success/30' : 'bg-danger/20 border-danger/30';
  const animationClass = shouldAnimate ? 'motion-safe:animate-[statusPop_400ms_ease-out_forwards]' : '';

  return (
    <div 
      className={`absolute inset-0 z-10 pointer-events-none rounded-xl flex items-center justify-center bg-background/50 backdrop-blur-[1px] opacity-100 ${animationClass}`}
      onAnimationEnd={onAnimationEnd}
    >
      <div className={`flex flex-col items-center justify-center gap-1 p-4 rounded-xl border shadow-sm ${bgClass}`}>
        <svg 
          width="40" height="40" viewBox="0 0 24 24" 
          fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"
          className={`${colorClass}`} 
        >
          {status === 'approved' ? (
            <path d="M20 6L9 17l-5-5" />
          ) : (
            <path d="M18 6L6 18M6 6l12 12" />
          )}
        </svg>
        <span className={`text-sm font-bold tracking-widest uppercase ${colorClass}`}>
          {status}
        </span>
      </div>
    </div>
  );
};

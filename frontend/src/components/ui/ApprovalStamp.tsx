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
      // Fire immediately if no animation
      if (onAnimationEnd) onAnimationEnd();
    }
  }, [onAnimationEnd]);

  const colorClass = status === 'approved' ? 'text-verdigris' : 'text-rust';
  const animationClass = shouldAnimate ? 'motion-safe:animate-[stampIn_200ms_cubic-bezier(0.175,0.885,0.32,1.275)_forwards]' : '';

  return (
    <div 
      className={`absolute top-5 right-5 pointer-events-none transform -rotate-6 scale-100 opacity-100 ${animationClass}`}
      onAnimationEnd={onAnimationEnd}
    >
      <svg 
        width="72" height="72" viewBox="0 0 100 100" 
        className={`${colorClass}`} 
        xmlns="http://www.w3.org/2000/svg"
      >
        <circle 
          cx="50" cy="50" r="44" fill="none" stroke="currentColor" 
          strokeWidth="4" strokeDasharray="12,3,6,2,8,2" 
        />
        <circle 
          cx="50" cy="50" r="38" fill="none" stroke="currentColor" 
          strokeWidth="1.5" strokeDasharray="8,2" 
        />
        <text 
          x="50" y="55" fontFamily="var(--font-mono)" fontSize="16" 
          fontWeight="bold" fill="currentColor" textAnchor="middle" letterSpacing="1"
        >
          {status.toUpperCase()}
        </text>
      </svg>
    </div>
  );
};

import React from 'react';
import type { HTMLAttributes } from 'react';

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  status: 'pending' | 'approved' | 'rejected';
}

export const Badge: React.FC<BadgeProps> = ({ status, className = '', ...props }) => {
  const baseStyles = 'inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-semibold rounded-full uppercase tracking-wider font-body';
  
  const statusConfig = {
    pending: {
      styles: 'bg-[#FDF7E7] text-signal-gold',
      icon: (
        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      )
    },
    approved: {
      styles: 'bg-[#EEF5F1] text-verdigris',
      icon: (
        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
        </svg>
      )
    },
    rejected: {
      styles: 'bg-[#FDF3F2] text-rust',
      icon: (
        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
        </svg>
      )
    }
  };

  const config = statusConfig[status];

  return (
    <span className={`${baseStyles} ${config.styles} ${className}`} {...props}>
      {config.icon}
      {status}
    </span>
  );
};

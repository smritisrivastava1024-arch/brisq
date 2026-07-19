import type { ReactNode } from 'react';

interface CardProps {
  children: ReactNode;
  className?: string;
  hoverShadow?: boolean;
}

export function Card({ children, className = '', hoverShadow = false }: CardProps) {
  return (
    <div 
      className={`
        glass-panel rounded-2xl overflow-hidden
        ${hoverShadow ? 'transition-all duration-300 hover:border-white/20 hover:shadow-[0_8px_30px_rgba(0,0,0,0.4)] hover:-translate-y-[2px]' : ''}
        ${className}
      `}
    >
      {children}
    </div>
  );
}

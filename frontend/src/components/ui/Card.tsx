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
        minimal-panel rounded-xl overflow-hidden
        ${hoverShadow ? 'transition-all duration-200 hover:border-text-dim hover:shadow-md' : ''}
        ${className}
      `}
    >
      {children}
    </div>
  );
}

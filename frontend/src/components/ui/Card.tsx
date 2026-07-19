import React from 'react';
import type { HTMLAttributes } from 'react';

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  hoverShadow?: boolean;
}

export const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className = '', hoverShadow = false, ...props }, ref) => {
    const baseStyles = 'bg-parchment border border-parchment-dim rounded-ledger overflow-hidden transition-shadow';
    const shadowStyle = hoverShadow ? 'hover:shadow-[0_1px_3px_rgba(20,27,46,0.08)]' : '';

    return (
      <div
        ref={ref}
        className={`${baseStyles} ${shadowStyle} ${className}`}
        {...props}
      />
    );
  }
);

Card.displayName = 'Card';

import React from 'react';
import type { HTMLAttributes } from 'react';

export const Skeleton: React.FC<HTMLAttributes<HTMLDivElement>> = ({ className = '', ...props }) => {
  return (
    <div
      className={`bg-parchment-dim rounded-ledger motion-safe:animate-pulse ${className}`}
      {...props}
    />
  );
};

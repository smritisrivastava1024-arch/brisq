import React from 'react';
import type { ButtonHTMLAttributes } from 'react';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost';
  size?: 'sm' | 'md';
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className = '', variant = 'primary', size = 'md', ...props }, ref) => {
    const baseStyles = 'inline-flex items-center justify-center font-body font-semibold rounded-ledger transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-signal-gold disabled:opacity-50 disabled:cursor-not-allowed';
    
    const sizeStyles = {
      sm: 'px-3 py-1.5 text-sm',
      md: 'px-4 py-2 text-base',
    };

    const variantStyles = {
      primary: 'bg-signal-gold text-ink-navy hover:bg-[#b08531]',
      secondary: 'bg-parchment-dim text-ink-navy hover:bg-[#c8c0ac]',
      danger: 'bg-rust text-white hover:bg-[#993b31]',
      ghost: 'bg-transparent text-ink-navy hover:bg-ink-navy/5',
    };

    return (
      <button
        ref={ref}
        className={`${baseStyles} ${sizeStyles[size]} ${variantStyles[variant]} ${className}`}
        {...props}
      />
    );
  }
);

Button.displayName = 'Button';

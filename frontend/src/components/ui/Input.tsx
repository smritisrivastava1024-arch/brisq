import React from 'react';
import type { InputHTMLAttributes } from 'react';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, className = '', id, ...props }, ref) => {
    const inputId = id || label.replace(/\s+/g, '-').toLowerCase();
    
    return (
      <div className={`flex flex-col gap-1.5 ${className}`}>
        <label htmlFor={inputId} className="text-sm font-semibold text-ink-navy">
          {label}
        </label>
        <input
          ref={ref}
          id={inputId}
          className={`
            bg-white border rounded-ledger px-3.5 py-2.5 text-ink-navy font-body outline-none transition-colors
            focus-visible:ring-2 focus-visible:ring-signal-gold
            ${error ? 'border-rust focus:border-rust' : 'border-parchment-dim focus:border-signal-gold'}
          `}
          {...props}
        />
        {error && <span className="text-sm text-rust mt-0.5">{error}</span>}
      </div>
    );
  }
);

Input.displayName = 'Input';

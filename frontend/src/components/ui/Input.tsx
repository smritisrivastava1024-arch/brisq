import { forwardRef } from 'react';
import type { InputHTMLAttributes } from 'react';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  error?: string;
  label?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className = '', error, label, ...props }, ref) => {
    return (
      <div className="flex flex-col gap-1.5 w-full">
        {label && <label className="text-sm font-medium text-text-muted mb-0.5">{label}</label>}
        <input
          ref={ref}
          className={`
            w-full bg-surface/50 border border-white/10 rounded-lg px-4 py-2.5 text-sm text-text-main placeholder-text-muted
            transition-all duration-200 outline-none
            focus:border-primary/50 focus:ring-1 focus:ring-primary/50 focus:bg-surface/80
            disabled:opacity-50
            ${error ? 'border-danger/50 focus:border-danger focus:ring-danger/50' : ''}
            ${className}
          `}
          {...props}
        />
        {error && <span className="text-xs text-danger font-medium ml-1">{error}</span>}
      </div>
    );
  }
);

Input.displayName = 'Input';

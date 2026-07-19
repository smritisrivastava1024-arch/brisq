import { forwardRef } from 'react';
import type { TextareaHTMLAttributes } from 'react';

interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  error?: string;
  label?: string;
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className = '', error, label, ...props }, ref) => {
    return (
      <div className="flex flex-col gap-1.5 w-full">
        {label && <label className="text-sm font-medium text-text-muted mb-0.5">{label}</label>}
        <textarea
          ref={ref}
          className={`
            w-full bg-surface/50 border border-white/10 rounded-lg px-4 py-2.5 text-sm text-text-main placeholder-text-muted
            transition-all duration-200 outline-none
            focus:border-primary/50 focus:ring-1 focus:ring-primary/50 focus:bg-surface/80
            disabled:opacity-50 min-h-[80px]
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

Textarea.displayName = 'Textarea';

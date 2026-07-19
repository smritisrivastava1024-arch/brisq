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
        {label && <label className="text-sm font-medium text-text-main mb-0.5">{label}</label>}
        <textarea
          ref={ref}
          className={`
            w-full bg-surface border border-[#E8E3DA] rounded-md px-4 py-2.5 text-sm text-text-main placeholder-text-muted
            transition-all duration-200 outline-none
            focus:border-primary focus:ring-1 focus:ring-primary focus:bg-surface
            disabled:opacity-50 min-h-[80px] shadow-sm
            ${error ? 'border-danger focus:border-danger focus:ring-danger' : ''}
            ${className}
          `}
          {...props}
        />
        {error && <span className="text-xs text-danger font-medium">{error}</span>}
      </div>
    );
  }
);

Textarea.displayName = 'Textarea';

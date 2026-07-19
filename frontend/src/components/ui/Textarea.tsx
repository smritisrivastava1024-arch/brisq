import React from 'react';
import type { TextareaHTMLAttributes } from 'react';

interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label: string;
  error?: string;
}

export const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ label, error, className = '', id, ...props }, ref) => {
    const textareaId = id || label.replace(/\s+/g, '-').toLowerCase();
    
    return (
      <div className={`flex flex-col gap-1.5 ${className}`}>
        <label htmlFor={textareaId} className="text-sm font-semibold text-ink-navy">
          {label}
        </label>
        <textarea
          ref={ref}
          id={textareaId}
          className={`
            bg-white border rounded-ledger px-3.5 py-2.5 text-ink-navy font-body outline-none transition-colors resize-y min-h-[80px]
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

Textarea.displayName = 'Textarea';

import type { ButtonHTMLAttributes, ReactNode } from 'react';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode;
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost';
  size?: 'sm' | 'md';
}

export function Button({ 
  children, 
  variant = 'secondary', 
  size = 'md', 
  className = '', 
  ...props 
}: ButtonProps) {
  
  const base = "inline-flex items-center justify-center font-medium transition-colors duration-200 disabled:opacity-50 disabled:pointer-events-none rounded-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50 focus-visible:ring-offset-2 focus-visible:ring-offset-background";
  
  const sizeClasses = {
    sm: "px-3 py-1.5 text-sm",
    md: "px-4 py-2 text-sm",
  };
  
  const variantClasses = {
    primary: "bg-primary text-white hover:bg-primary-hover shadow-sm",
    secondary: "bg-surface text-text-main border border-[#E8E3DA] hover:bg-surface-lighter hover:border-text-dim",
    danger: "bg-surface text-danger border border-[#E8E3DA] hover:bg-danger/10 hover:border-danger/30",
    ghost: "text-text-muted hover:text-text-main hover:bg-surface-lighter",
  };

  return (
    <button 
      className={`${base} ${sizeClasses[size]} ${variantClasses[variant]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}

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
  
  const base = "inline-flex items-center justify-center font-medium transition-all duration-200 disabled:opacity-50 disabled:pointer-events-none rounded-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50 focus-visible:ring-offset-2 focus-visible:ring-offset-background";
  
  const sizeClasses = {
    sm: "px-3.5 py-1.5 text-sm",
    md: "px-5 py-2.5 text-sm",
  };
  
  const variantClasses = {
    primary: "bg-primary-gradient text-white shadow-[0_0_15px_rgba(139,92,246,0.3)] hover:shadow-[0_0_25px_rgba(139,92,246,0.5)] hover:-translate-y-[1px]",
    secondary: "bg-white/5 text-text-main border border-white/10 hover:bg-white/10 hover:border-white/20 hover:-translate-y-[1px]",
    danger: "bg-danger/20 text-danger border border-danger/30 hover:bg-danger/30 hover:shadow-[0_0_15px_rgba(239,68,68,0.2)] hover:-translate-y-[1px]",
    ghost: "text-text-muted hover:text-text-main hover:bg-white/5",
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

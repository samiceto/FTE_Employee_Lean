import { ReactNode } from 'react';

interface CardProps {
  children: ReactNode;
  className?: string;
  hover?: boolean;
  glow?: string;
  onClick?: () => void;
}

export default function Card({ children, className = '', hover = false, glow, onClick }: CardProps) {
  const hoverClass = hover ? 'hover:border-slate-600 hover:bg-slate-800/60 transition-all duration-200 cursor-pointer' : '';
  const glowClass = glow ? `shadow-lg` : '';
  const style = glow ? { boxShadow: `0 0 24px ${glow}` } : undefined;

  return (
    <div
      onClick={onClick}
      className={`rounded-xl border border-slate-800 bg-slate-900/60 backdrop-blur-sm ${hoverClass} ${glowClass} ${className}`}
      style={style}
    >
      {children}
    </div>
  );
}

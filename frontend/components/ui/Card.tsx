import { ReactNode } from 'react';

interface CardProps {
  children: ReactNode;
  className?: string;
  hover?: boolean;
  glow?: string;
  onClick?: () => void;
}

export default function Card({ children, className = '', hover = false, glow, onClick }: CardProps) {
  const hoverClass = hover ? 'glass-card-hover cursor-pointer' : '';
  const style = glow ? { boxShadow: `0 0 24px ${glow}` } : undefined;

  return (
    <div
      onClick={onClick}
      className={`rounded-xl glass-card ${hoverClass} ${className}`}
      style={style}
    >
      {children}
    </div>
  );
}

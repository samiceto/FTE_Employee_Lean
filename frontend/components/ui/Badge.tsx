interface BadgeProps {
  children: React.ReactNode;
  variant?: 'green' | 'red' | 'yellow' | 'blue' | 'purple' | 'orange' | 'gray' | 'cyan';
  size?: 'sm' | 'md';
}

const variantStyles: Record<string, string> = {
  green: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/20',
  red: 'bg-red-500/15 text-red-400 border-red-500/20',
  yellow: 'bg-yellow-500/15 text-yellow-400 border-yellow-500/20',
  blue: 'bg-blue-500/15 text-blue-400 border-blue-500/20',
  purple: 'bg-purple-500/15 text-purple-400 border-purple-500/20',
  orange: 'bg-orange-500/15 text-orange-400 border-orange-500/20',
  gray: 'bg-slate-500/15 text-slate-400 border-slate-500/20',
  cyan: 'bg-cyan-500/15 text-cyan-400 border-cyan-500/20',
};

export default function Badge({ children, variant = 'gray', size = 'sm' }: BadgeProps) {
  const sizeClass = size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-3 py-1 text-sm';
  return (
    <span className={`inline-flex items-center rounded-full border font-medium ${sizeClass} ${variantStyles[variant]}`}>
      {children}
    </span>
  );
}

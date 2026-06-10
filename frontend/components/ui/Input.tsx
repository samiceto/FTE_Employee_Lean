import { InputHTMLAttributes, ReactNode } from 'react';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  hint?: string;
  error?: string;
  icon?: ReactNode;
  suffix?: ReactNode;
}

export default function Input({ label, hint, error, icon, suffix, className = '', ...props }: InputProps) {
  return (
    <div className="flex flex-col gap-1.5">
      {label && <label className="text-sm font-medium text-slate-300">{label}</label>}
      <div className="relative flex items-center">
        {icon && (
          <div className="absolute left-3 text-slate-500 pointer-events-none">
            {icon}
          </div>
        )}
        <input
          className={`w-full rounded-lg border border-slate-700 bg-slate-800/60 text-slate-200 placeholder-slate-500 text-sm px-3 py-2.5 transition-all duration-150 focus:outline-none focus:border-emerald-500/60 focus:ring-1 focus:ring-emerald-500/20 ${icon ? 'pl-9' : ''} ${suffix ? 'pr-9' : ''} ${error ? 'border-red-500/50' : ''} ${className}`}
          {...props}
        />
        {suffix && (
          <div className="absolute right-3 text-slate-500">
            {suffix}
          </div>
        )}
      </div>
      {hint && !error && <p className="text-xs text-slate-500">{hint}</p>}
      {error && <p className="text-xs text-red-400">{error}</p>}
    </div>
  );
}

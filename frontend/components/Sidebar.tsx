'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard, KeyRound, Bot, Activity, ListTodo,
  CheckCircle, Mail, ScrollText, Settings,
  ChevronLeft, ChevronRight, BarChart3, Cpu, Zap,
} from 'lucide-react';

const NAV = [
  { label: 'Overview', href: '/', icon: LayoutDashboard },
  { label: 'Credentials', href: '/credentials', icon: KeyRound },
  { label: 'Agents', href: '/agents', icon: Bot },
  { label: 'Processes', href: '/processes', icon: Cpu },
  { label: 'Task Queue', href: '/tasks', icon: ListTodo },
  { label: 'Approvals', href: '/approvals', icon: CheckCircle },
  { label: 'Email', href: '/email', icon: Mail },
  { label: 'Analytics', href: '/analytics', icon: BarChart3 },
  { label: 'Audit Logs', href: '/logs', icon: ScrollText },
  { label: 'Settings', href: '/settings', icon: Settings },
];

export default function Sidebar({ open, onToggle }: { open: boolean; onToggle: () => void }) {
  const pathname = usePathname();

  return (
    <aside
      className="flex flex-col border-r border-slate-800 transition-all duration-300 shrink-0"
      style={{
        width: open ? '240px' : '64px',
        background: 'var(--bg-surface)',
        minHeight: '100vh',
      }}
    >
      {/* Logo */}
      <div className="flex items-center h-16 px-4 border-b border-slate-800 gap-3 overflow-hidden">
        <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-emerald-500/15 border border-emerald-500/20 shrink-0">
          <Zap size={16} className="text-emerald-400" />
        </div>
        {open && (
          <div className="overflow-hidden">
            <p className="text-sm font-bold text-slate-100 whitespace-nowrap">FTE AI Employee</p>
            <p className="text-xs text-slate-500 whitespace-nowrap">Control Dashboard</p>
          </div>
        )}
      </div>

      {/* Nav */}
      <nav className="flex-1 py-4 px-2 flex flex-col gap-0.5" aria-label="Main navigation">
        {NAV.map(({ label, href, icon: Icon }) => {
          const active = pathname === href || (href !== '/' && pathname.startsWith(href));
          return (
            <Link
              key={href}
              href={href}
              title={!open ? label : undefined}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 cursor-pointer ${
                active
                  ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/20'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800 border border-transparent'
              }`}
            >
              <Icon size={16} className="shrink-0" />
              {open && <span className="whitespace-nowrap overflow-hidden">{label}</span>}
            </Link>
          );
        })}
      </nav>

      {/* System status indicator */}
      {open && (
        <div className="mx-3 mb-3 p-3 rounded-lg bg-slate-800/60 border border-slate-700">
          <div className="flex items-center gap-2 mb-2">
            <Activity size={12} className="text-emerald-400" />
            <span className="text-xs font-medium text-slate-300">System Health</span>
          </div>
          <div className="flex items-center justify-between text-xs">
            <span className="text-slate-500">9 / 11 online</span>
            <span className="text-emerald-400 font-medium">82%</span>
          </div>
          <div className="mt-1.5 h-1.5 rounded-full bg-slate-700 overflow-hidden">
            <div className="h-full rounded-full bg-emerald-500" style={{ width: '82%' }} />
          </div>
        </div>
      )}

      {/* Toggle button */}
      <button
        onClick={onToggle}
        className="flex items-center justify-center h-10 border-t border-slate-800 text-slate-500 hover:text-slate-300 hover:bg-slate-800 transition-colors cursor-pointer"
        aria-label={open ? 'Collapse sidebar' : 'Expand sidebar'}
      >
        {open ? <ChevronLeft size={16} /> : <ChevronRight size={16} />}
      </button>
    </aside>
  );
}

'use client';

import { Menu, Bell, RefreshCw, CircleDot } from 'lucide-react';
import { useState } from 'react';

export default function Header({ onMenuClick }: { onMenuClick: () => void }) {
  const [syncing, setSyncing] = useState(false);

  const handleSync = () => {
    setSyncing(true);
    setTimeout(() => setSyncing(false), 2000);
  };

  return (
    <header
      className="flex items-center justify-between h-16 px-6 border-b border-slate-800 shrink-0"
      style={{ background: 'var(--bg-surface)' }}
    >
      <div className="flex items-center gap-4">
        <button
          onClick={onMenuClick}
          className="p-2 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors cursor-pointer"
          aria-label="Toggle sidebar"
        >
          <Menu size={18} />
        </button>

        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full border border-emerald-500/20 bg-emerald-500/10">
          <CircleDot size={12} className="text-emerald-400 animate-pulse-dot" />
          <span className="text-xs font-medium text-emerald-400">System Active</span>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={handleSync}
          className="p-2 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors cursor-pointer"
          title="Sync status"
          aria-label="Sync system status"
        >
          <RefreshCw size={16} className={syncing ? 'animate-spin' : ''} />
        </button>

        <button
          className="relative p-2 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors cursor-pointer"
          aria-label="Notifications"
        >
          <Bell size={16} />
          <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 rounded-full bg-red-400" />
        </button>

        <div className="w-px h-6 bg-slate-700 mx-1" />

        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-full bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center">
            <span className="text-xs font-bold text-emerald-400">S</span>
          </div>
          <div className="hidden sm:block">
            <p className="text-xs font-medium text-slate-200">Sami Ullah</p>
            <p className="text-xs text-slate-500">Admin</p>
          </div>
        </div>
      </div>
    </header>
  );
}

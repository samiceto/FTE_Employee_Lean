'use client';

import { useState } from 'react';
import { mockProcesses } from '../../lib/mock-data';
import type { Process } from '../../lib/types';
import Card from '../../components/ui/Card';
import Badge from '../../components/ui/Badge';
import Button from '../../components/ui/Button';
import StatusDot from '../../components/ui/StatusDot';
import { Cpu, Play, Square, RotateCcw, AlertTriangle, Clock, Activity } from 'lucide-react';

export default function ProcessesPage() {
  const [processes, setProcesses] = useState<Process[]>(mockProcesses);
  const [loadingId, setLoadingId] = useState<string | null>(null);

  const handleAction = (id: string, action: 'start' | 'stop' | 'restart') => {
    setLoadingId(id);
    setTimeout(() => {
      setProcesses(prev => prev.map(p => {
        if (p.id !== id) return p;
        if (action === 'stop') return { ...p, status: 'stopped' as const, pid: undefined, cpu: 0, memory: 0, uptime: undefined };
        return { ...p, status: 'online' as const, pid: Math.floor(Math.random() * 50000 + 10000), cpu: 0.2, memory: 45, uptime: 'just now' };
      }));
      setLoadingId(null);
    }, 1500);
  };

  const online = processes.filter(p => p.status === 'online').length;
  const errored = processes.filter(p => p.status === 'errored').length;
  const stopped = processes.filter(p => p.status === 'stopped').length;
  const totalCpu = processes.reduce((sum, p) => sum + p.cpu, 0);
  const totalMem = processes.reduce((sum, p) => sum + p.memory, 0);

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <Cpu size={20} className="text-blue-400" /> Process Monitor
          </h1>
          <p className="text-sm text-slate-500 mt-0.5">PM2 process management — {processes.length} total processes</p>
        </div>
        <div className="flex gap-2">
          <Button variant="primary" icon={<Play size={14} />} onClick={() => processes.filter(p => p.status !== 'online').forEach(p => handleAction(p.id, 'start'))}>
            Start All
          </Button>
          <Button variant="danger" icon={<RotateCcw size={14} />}>
            Restart All
          </Button>
        </div>
      </div>

      {/* Summary bar */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {[
          { label: 'Online', value: online, color: 'text-emerald-400', bg: 'bg-emerald-500/10 border-emerald-500/20' },
          { label: 'Errored', value: errored, color: 'text-red-400', bg: 'bg-red-500/10 border-red-500/20' },
          { label: 'Stopped', value: stopped, color: 'text-slate-400', bg: 'bg-slate-500/10 border-slate-700' },
          { label: 'Total CPU', value: `${totalCpu.toFixed(1)}%`, color: 'text-blue-400', bg: 'bg-blue-500/10 border-blue-500/20' },
        ].map(({ label, value, color, bg }) => (
          <Card key={label} className={`p-4 border ${bg}`}>
            <p className="text-xs text-slate-500">{label}</p>
            <p className={`text-2xl font-bold mt-1 ${color}`}>{value}</p>
          </Card>
        ))}
      </div>

      {/* Process table */}
      <Card className="overflow-hidden">
        <div className="px-5 py-3 border-b border-slate-800 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
            <Activity size={14} className="text-blue-400" /> All Processes
          </h2>
          <span className="text-xs text-slate-500">Total Memory: {(totalMem / 1024).toFixed(1)} GB</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-800">
                <th className="text-left px-5 py-3 text-xs font-medium text-slate-500">Process</th>
                <th className="text-left px-3 py-3 text-xs font-medium text-slate-500">Status</th>
                <th className="text-left px-3 py-3 text-xs font-medium text-slate-500 hidden sm:table-cell">PID</th>
                <th className="text-left px-3 py-3 text-xs font-medium text-slate-500 hidden md:table-cell">CPU</th>
                <th className="text-left px-3 py-3 text-xs font-medium text-slate-500 hidden md:table-cell">Memory</th>
                <th className="text-left px-3 py-3 text-xs font-medium text-slate-500 hidden lg:table-cell">Uptime</th>
                <th className="text-left px-3 py-3 text-xs font-medium text-slate-500 hidden lg:table-cell">Restarts</th>
                <th className="text-right px-5 py-3 text-xs font-medium text-slate-500">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/50">
              {processes.map(proc => {
                const isLoading = loadingId === proc.id;
                return (
                  <tr key={proc.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="px-5 py-3">
                      <code className="text-sm text-slate-200 font-mono">{proc.name}</code>
                    </td>
                    <td className="px-3 py-3">
                      <div className="flex items-center gap-2">
                        <StatusDot status={proc.status as 'online' | 'stopped' | 'errored'} />
                        <Badge variant={
                          proc.status === 'online' ? 'green' :
                          proc.status === 'errored' ? 'red' :
                          proc.status === 'launching' ? 'blue' : 'gray'
                        }>
                          {proc.status}
                        </Badge>
                      </div>
                    </td>
                    <td className="px-3 py-3 hidden sm:table-cell">
                      <span className="text-xs text-slate-500 font-mono">{proc.pid ?? '—'}</span>
                    </td>
                    <td className="px-3 py-3 hidden md:table-cell">
                      <div className="flex items-center gap-2">
                        <div className="w-16 h-1.5 rounded-full bg-slate-700 overflow-hidden">
                          <div className="h-full rounded-full bg-blue-500" style={{ width: `${Math.min(proc.cpu * 10, 100)}%` }} />
                        </div>
                        <span className="text-xs text-slate-400">{proc.cpu}%</span>
                      </div>
                    </td>
                    <td className="px-3 py-3 hidden md:table-cell">
                      <span className="text-xs text-slate-400">{proc.memory > 0 ? `${proc.memory} MB` : '—'}</span>
                    </td>
                    <td className="px-3 py-3 hidden lg:table-cell">
                      <span className="text-xs text-slate-500 flex items-center gap-1">
                        <Clock size={10} />{proc.uptime ?? '—'}
                      </span>
                    </td>
                    <td className="px-3 py-3 hidden lg:table-cell">
                      <span className={`text-xs ${proc.restarts > 0 ? 'text-yellow-400' : 'text-slate-500'}`}>
                        {proc.restarts > 0 && <AlertTriangle size={10} className="inline mr-1" />}
                        {proc.restarts}
                      </span>
                    </td>
                    <td className="px-5 py-3">
                      <div className="flex items-center justify-end gap-1.5">
                        {proc.status !== 'online' ? (
                          <Button size="sm" variant="primary" loading={isLoading} onClick={() => handleAction(proc.id, 'start')} icon={<Play size={11} />}>
                            Start
                          </Button>
                        ) : (
                          <Button size="sm" variant="danger" loading={isLoading} onClick={() => handleAction(proc.id, 'stop')} icon={<Square size={11} />}>
                            Stop
                          </Button>
                        )}
                        <Button size="sm" variant="ghost" loading={isLoading} onClick={() => handleAction(proc.id, 'restart')} icon={<RotateCcw size={11} />}>
                          <span className="hidden sm:inline">Restart</span>
                        </Button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}

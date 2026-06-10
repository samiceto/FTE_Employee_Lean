'use client';

import { useState } from 'react';
import { mockAgents } from '../../lib/mock-data';
import type { Agent } from '../../lib/types';
import Card from '../../components/ui/Card';
import Badge from '../../components/ui/Badge';
import Button from '../../components/ui/Button';
import StatusDot from '../../components/ui/StatusDot';
import Modal from '../../components/ui/Modal';
import {
  Bot, Play, Square, RotateCcw, Clock, AlertTriangle,
  Info, ChevronDown, ChevronUp, Activity, KeyRound, Search,
} from 'lucide-react';
import Input from '../../components/ui/Input';

export default function AgentsPage() {
  const [agents, setAgents] = useState<Agent[]>(mockAgents);
  const [selected, setSelected] = useState<Agent | null>(null);
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [search, setSearch] = useState('');
  const [loadingId, setLoadingId] = useState<string | null>(null);

  const filtered = agents.filter(a =>
    a.name.toLowerCase().includes(search.toLowerCase()) ||
    a.description.toLowerCase().includes(search.toLowerCase())
  );

  const toggleExpand = (id: string) => {
    const next = new Set(expanded);
    next.has(id) ? next.delete(id) : next.add(id);
    setExpanded(next);
  };

  const handleAction = (id: string, action: 'start' | 'stop' | 'restart') => {
    setLoadingId(id);
    setTimeout(() => {
      setAgents(prev => prev.map(a => {
        if (a.id !== id) return a;
        const newStatus = action === 'stop' ? 'stopped' : 'running';
        return { ...a, status: newStatus, lastRun: action !== 'stop' ? 'just now' : a.lastRun };
      }));
      setLoadingId(null);
    }, 1500);
  };

  const running = agents.filter(a => a.status === 'running').length;
  const errors = agents.filter(a => a.status === 'error').length;
  const stopped = agents.filter(a => a.status === 'stopped').length;

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <Bot size={20} className="text-emerald-400" /> Agent Control
          </h1>
          <p className="text-sm text-slate-500 mt-0.5">Manage all AI agents and watchers</p>
        </div>
        <div className="flex gap-3">
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
            <div className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
            <span className="text-xs font-medium text-emerald-400">{running} running</span>
          </div>
          {errors > 0 && (
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-red-500/10 border border-red-500/20">
              <AlertTriangle size={12} className="text-red-400" />
              <span className="text-xs font-medium text-red-400">{errors} errors</span>
            </div>
          )}
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 border border-slate-700">
            <div className="w-1.5 h-1.5 rounded-full bg-slate-500" />
            <span className="text-xs font-medium text-slate-400">{stopped} stopped</span>
          </div>
        </div>
      </div>

      <Input placeholder="Search agents..." value={search} onChange={e => setSearch(e.target.value)} icon={<Search size={14} />} />

      <div className="space-y-3">
        {filtered.map(agent => {
          const isExpanded = expanded.has(agent.id);
          const isLoading = loadingId === agent.id;

          return (
            <Card key={agent.id} className={agent.status === 'error' ? 'border-red-500/20' : ''}>
              <div className="p-4">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-start gap-3 min-w-0 flex-1">
                    <StatusDot status={agent.status as 'running' | 'stopped' | 'error' | 'idle'} />
                    <div className="min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <h3 className="text-sm font-semibold text-slate-200">{agent.name}</h3>
                        <Badge variant={
                          agent.status === 'running' ? 'green' :
                          agent.status === 'error' ? 'red' :
                          agent.status === 'idle' ? 'yellow' : 'gray'
                        }>
                          {agent.status}
                        </Badge>
                        {agent.interval && <Badge variant="blue">{agent.interval}</Badge>}
                      </div>
                      <p className="text-xs text-slate-500 mt-0.5">{agent.description}</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    <button
                      onClick={() => setSelected(agent)}
                      className="p-1.5 text-slate-500 hover:text-slate-300 transition-colors cursor-pointer"
                      title="Details"
                    >
                      <Info size={14} />
                    </button>
                    <button
                      onClick={() => toggleExpand(agent.id)}
                      className="p-1.5 text-slate-500 hover:text-slate-300 transition-colors cursor-pointer"
                    >
                      {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                    </button>
                  </div>
                </div>

                {/* Quick stats row */}
                <div className="flex items-center gap-4 mt-3 pt-3 border-t border-slate-800">
                  <div className="flex items-center gap-1.5 text-xs text-slate-500">
                    <Activity size={11} />
                    <span>{agent.tasksProcessed} tasks processed</span>
                  </div>
                  {agent.lastRun && (
                    <div className="flex items-center gap-1.5 text-xs text-slate-500">
                      <Clock size={11} />
                      <span>Last: {agent.lastRun}</span>
                    </div>
                  )}
                  {agent.nextRun && (
                    <div className="flex items-center gap-1.5 text-xs text-slate-500">
                      <Clock size={11} />
                      <span>Next: {agent.nextRun}</span>
                    </div>
                  )}
                  {agent.errorsToday > 0 && (
                    <div className="flex items-center gap-1.5 text-xs text-red-400">
                      <AlertTriangle size={11} />
                      <span>{agent.errorsToday} error{agent.errorsToday > 1 ? 's' : ''} today</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Expanded controls */}
              {isExpanded && (
                <div className="border-t border-slate-800 px-4 py-3 flex items-center justify-between gap-4 bg-slate-800/30">
                  <div className="flex items-center gap-1.5 text-xs text-slate-500">
                    <KeyRound size={11} />
                    <span>Needs: {agent.credentials.join(', ')}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    {agent.status !== 'running' && (
                      <Button size="sm" variant="primary" loading={isLoading} onClick={() => handleAction(agent.id, 'start')} icon={<Play size={12} />}>
                        Start
                      </Button>
                    )}
                    {agent.status === 'running' && (
                      <Button size="sm" variant="danger" loading={isLoading} onClick={() => handleAction(agent.id, 'stop')} icon={<Square size={12} />}>
                        Stop
                      </Button>
                    )}
                    <Button size="sm" variant="outline" loading={isLoading} onClick={() => handleAction(agent.id, 'restart')} icon={<RotateCcw size={12} />}>
                      Restart
                    </Button>
                  </div>
                </div>
              )}
            </Card>
          );
        })}
      </div>

      {/* Detail modal */}
      <Modal open={!!selected} onClose={() => setSelected(null)} title={selected?.name ?? ''} size="md">
        {selected && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              {[
                { label: 'Status', value: selected.status },
                { label: 'Tasks Processed', value: selected.tasksProcessed },
                { label: 'Errors Today', value: selected.errorsToday },
                { label: 'Interval', value: selected.interval ?? 'On-demand' },
                { label: 'Last Run', value: selected.lastRun ?? 'Never' },
                { label: 'Uptime', value: selected.uptime ?? '—' },
              ].map(({ label, value }) => (
                <div key={label} className="p-3 rounded-lg bg-slate-800/60 border border-slate-700">
                  <p className="text-xs text-slate-500">{label}</p>
                  <p className="text-sm font-medium text-slate-200 mt-0.5">{value}</p>
                </div>
              ))}
            </div>
            <div className="p-3 rounded-lg bg-slate-800/60 border border-slate-700">
              <p className="text-xs text-slate-500 mb-1.5">Required Credentials</p>
              <div className="flex flex-wrap gap-1.5">
                {selected.credentials.map(c => (
                  <Badge key={c} variant="blue">{c}</Badge>
                ))}
              </div>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}

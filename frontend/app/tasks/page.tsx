'use client';

import { useState } from 'react';
import { mockTasks } from '../../lib/mock-data';
import type { Task } from '../../lib/types';
import Card from '../../components/ui/Card';
import Badge from '../../components/ui/Badge';
import Button from '../../components/ui/Button';
import Modal from '../../components/ui/Modal';
import { ListTodo, Clock, Filter, ChevronRight, Search, Eye } from 'lucide-react';
import Input from '../../components/ui/Input';

const statusConfig = {
  pending: { label: 'Pending', color: 'yellow', stage: 'Need Action' },
  in_progress: { label: 'In Progress', color: 'blue', stage: 'Processing' },
  approved: { label: 'Approved', color: 'green', stage: 'Ready' },
  rejected: { label: 'Rejected', color: 'red', stage: 'Rejected' },
  done: { label: 'Done', color: 'gray', stage: 'Completed' },
};

const priorityColor = {
  critical: 'red',
  high: 'orange',
  medium: 'yellow',
  low: 'gray',
};

const platformColor: Record<string, string> = {
  gmail: 'blue', linkedin: 'blue', instagram: 'purple',
  x: 'gray', facebook: 'blue', whatsapp: 'green', odoo: 'yellow', slack: 'orange',
};

const STAGES = ['pending', 'in_progress', 'approved', 'done', 'rejected'] as const;

export default function TaskQueuePage() {
  const [tasks, setTasks] = useState<Task[]>(mockTasks);
  const [selected, setSelected] = useState<Task | null>(null);
  const [search, setSearch] = useState('');
  const [filterStatus, setFilterStatus] = useState<string>('all');

  const filtered = tasks.filter(t => {
    const matchSearch = t.title.toLowerCase().includes(search.toLowerCase());
    const matchStatus = filterStatus === 'all' || t.status === filterStatus;
    return matchSearch && matchStatus;
  });

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-100 flex items-center gap-2">
          <ListTodo size={20} className="text-yellow-400" /> Task Queue
        </h1>
        <p className="text-sm text-slate-500 mt-0.5">All tasks flowing through the AI Employee pipeline</p>
      </div>

      {/* Pipeline flow */}
      <Card className="p-4">
        <div className="flex items-center gap-1 overflow-x-auto pb-1">
          {STAGES.map((stage, i) => {
            const count = tasks.filter(t => t.status === stage).length;
            const cfg = statusConfig[stage];
            return (
              <div key={stage} className="flex items-center gap-1 shrink-0">
                <button
                  onClick={() => setFilterStatus(filterStatus === stage ? 'all' : stage)}
                  className={`flex flex-col items-center px-4 py-2.5 rounded-lg border text-xs font-medium transition-all cursor-pointer ${
                    filterStatus === stage
                      ? 'bg-emerald-500/15 border-emerald-500/30 text-emerald-400'
                      : 'border-slate-700 text-slate-400 hover:border-slate-600 hover:text-slate-300'
                  }`}
                >
                  <span className="text-lg font-bold text-slate-100">{count}</span>
                  <span>{cfg.stage}</span>
                </button>
                {i < STAGES.length - 1 && <ChevronRight size={14} className="text-slate-700 shrink-0" />}
              </div>
            );
          })}
        </div>
      </Card>

      <div className="flex flex-col sm:flex-row gap-3">
        <Input
          className="flex-1"
          placeholder="Search tasks..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          icon={<Search size={14} />}
        />
        <div className="flex items-center gap-2 text-xs text-slate-500">
          <Filter size={12} />
          <span>{filtered.length} results</span>
        </div>
      </div>

      <div className="space-y-2">
        {filtered.length === 0 && (
          <Card className="p-8 text-center">
            <p className="text-sm text-slate-500">No tasks match your filter.</p>
          </Card>
        )}
        {filtered.map(task => {
          const cfg = statusConfig[task.status];
          return (
            <Card key={task.id} hover className="p-4" onClick={() => setSelected(task)}>
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-sm font-medium text-slate-200">{task.title}</span>
                  </div>
                  <div className="flex items-center gap-2 mt-1.5 flex-wrap">
                    <Badge variant={cfg.color as 'green' | 'yellow' | 'red' | 'blue' | 'gray'}>{cfg.label}</Badge>
                    <Badge variant={priorityColor[task.priority] as 'red' | 'orange' | 'yellow' | 'gray'}>{task.priority}</Badge>
                    {task.platform && <Badge variant={platformColor[task.platform] as 'blue' | 'purple' | 'gray' | 'green' | 'yellow' | 'orange'}>{task.platform}</Badge>}
                    <span className="text-xs text-slate-500 flex items-center gap-1">
                      <Clock size={10} />{task.createdAt}
                    </span>
                  </div>
                  {task.description && <p className="text-xs text-slate-500 mt-1.5 truncate">{task.description}</p>}
                </div>
                <Button size="sm" variant="ghost" icon={<Eye size={12} />} onClick={e => { e.stopPropagation(); setSelected(task); }}>
                  View
                </Button>
              </div>
            </Card>
          );
        })}
      </div>

      <Modal open={!!selected} onClose={() => setSelected(null)} title="Task Details" size="md">
        {selected && (
          <div className="space-y-4">
            <h3 className="text-sm font-medium text-slate-200">{selected.title}</h3>
            <div className="grid grid-cols-2 gap-3">
              {[
                { label: 'Status', value: <Badge variant={statusConfig[selected.status].color as 'green' | 'yellow' | 'red' | 'blue' | 'gray'}>{statusConfig[selected.status].label}</Badge> },
                { label: 'Priority', value: <Badge variant={priorityColor[selected.priority] as 'red' | 'orange' | 'yellow' | 'gray'}>{selected.priority}</Badge> },
                { label: 'Type', value: selected.type },
                { label: 'Platform', value: selected.platform ?? '—' },
                { label: 'Created', value: selected.createdAt },
                { label: 'Updated', value: selected.updatedAt ?? '—' },
              ].map(({ label, value }) => (
                <div key={label} className="p-3 rounded-lg bg-slate-800/60 border border-slate-700">
                  <p className="text-xs text-slate-500">{label}</p>
                  <div className="text-sm font-medium text-slate-200 mt-0.5">{value}</div>
                </div>
              ))}
            </div>
            {selected.description && (
              <div className="p-3 rounded-lg bg-slate-800/60 border border-slate-700">
                <p className="text-xs text-slate-500 mb-1">Description</p>
                <p className="text-sm text-slate-300">{selected.description}</p>
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
}

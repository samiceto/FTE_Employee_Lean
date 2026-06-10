'use client';

import { useState } from 'react';
import { mockAuditLogs } from '../../lib/mock-data';
import type { AuditLog } from '../../lib/types';
import Card from '../../components/ui/Card';
import Badge from '../../components/ui/Badge';
import Button from '../../components/ui/Button';
import Input from '../../components/ui/Input';
import { ScrollText, Search, Filter, CheckCircle, XCircle, Download, RefreshCw } from 'lucide-react';

const extraLogs: AuditLog[] = [
  { id: '9', timestamp: '2026-05-01T10:22:00Z', event_type: 'plan.executed', component: 'ReasoningAgent', message: 'Generated Plan_20260501_102200.md with 5 tasks (priority: high)', success: true },
  { id: '10', timestamp: '2026-05-01T10:18:30Z', event_type: 'social.post', component: 'XWatcher', message: 'Tweet published: "Excited to share our latest..."', success: true },
  { id: '11', timestamp: '2026-05-01T10:15:00Z', event_type: 'task.failed', component: 'WhatsAppWatcher', message: 'Playwright session timeout — WhatsApp disconnected', success: false },
  { id: '12', timestamp: '2026-05-01T10:10:45Z', event_type: 'expense.created', component: 'OdooConnector', message: 'Expense recorded: Cloud Services March — $180', success: true },
  { id: '13', timestamp: '2026-05-01T10:05:22Z', event_type: 'email.classified', component: 'EmailClassifier', message: 'Email from client@acmecorp.com classified as URGENT', success: true },
  { id: '14', timestamp: '2026-05-01T09:58:10Z', event_type: 'agent.started', component: 'ExecutionAgent', message: 'Ralph Wiggum Loop started — interval: 5m', success: true },
  { id: '15', timestamp: '2026-05-01T09:50:00Z', event_type: 'agent.started', component: 'ReasoningAgent', message: 'Reasoning Loop started — interval: 30m', success: true },
];

const allLogs = [...mockAuditLogs, ...extraLogs].sort(
  (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
);

const EVENT_TYPES = [...new Set(allLogs.map(l => l.event_type))];
const COMPONENTS = [...new Set(allLogs.map(l => l.component))];

export default function LogsPage() {
  const [search, setSearch] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [filterComponent, setFilterComponent] = useState('all');
  const [filterResult, setFilterResult] = useState<'all' | 'success' | 'failed'>('all');
  const [refreshing, setRefreshing] = useState(false);

  const handleRefresh = () => {
    setRefreshing(true);
    setTimeout(() => setRefreshing(false), 1000);
  };

  const filtered = allLogs.filter(log => {
    const matchSearch =
      log.message.toLowerCase().includes(search.toLowerCase()) ||
      log.component.toLowerCase().includes(search.toLowerCase()) ||
      log.event_type.toLowerCase().includes(search.toLowerCase());
    const matchType = filterType === 'all' || log.event_type === filterType;
    const matchComponent = filterComponent === 'all' || log.component === filterComponent;
    const matchResult = filterResult === 'all' || (filterResult === 'success' ? log.success : !log.success);
    return matchSearch && matchType && matchComponent && matchResult;
  });

  const successCount = allLogs.filter(l => l.success).length;
  const failedCount = allLogs.filter(l => !l.success).length;

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <ScrollText size={20} className="text-cyan-400" /> Audit Logs
          </h1>
          <p className="text-sm text-slate-500 mt-0.5">{allLogs.length} events · 30-day retention</p>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-400 font-medium">
            <CheckCircle size={11} /> {successCount} success
          </div>
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-red-500/10 border border-red-500/20 text-xs text-red-400 font-medium">
            <XCircle size={11} /> {failedCount} failed
          </div>
          <Button size="sm" variant="outline" icon={<RefreshCw size={12} className={refreshing ? 'animate-spin' : ''} />} onClick={handleRefresh}>
            Refresh
          </Button>
          <Button size="sm" variant="ghost" icon={<Download size={12} />}>
            Export
          </Button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <Input
          className="flex-1"
          placeholder="Search logs..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          icon={<Search size={14} />}
        />
        <select
          value={filterType}
          onChange={e => setFilterType(e.target.value)}
          className="px-3 py-2.5 rounded-lg border border-slate-700 bg-slate-800/60 text-sm text-slate-200 focus:outline-none focus:border-emerald-500/60 cursor-pointer"
        >
          <option value="all">All event types</option>
          {EVENT_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
        </select>
        <select
          value={filterComponent}
          onChange={e => setFilterComponent(e.target.value)}
          className="px-3 py-2.5 rounded-lg border border-slate-700 bg-slate-800/60 text-sm text-slate-200 focus:outline-none focus:border-emerald-500/60 cursor-pointer"
        >
          <option value="all">All components</option>
          {COMPONENTS.map(c => <option key={c} value={c}>{c}</option>)}
        </select>
        <div className="flex gap-1 p-1 rounded-lg bg-slate-800 border border-slate-700 shrink-0">
          {(['all', 'success', 'failed'] as const).map(r => (
            <button
              key={r}
              onClick={() => setFilterResult(r)}
              className={`px-3 py-1 rounded-md text-xs font-medium capitalize transition-all cursor-pointer ${
                filterResult === r ? 'bg-slate-700 text-slate-100' : 'text-slate-400 hover:text-slate-300'
              }`}
            >
              {r}
            </button>
          ))}
        </div>
      </div>

      <div className="flex items-center gap-2 text-xs text-slate-500">
        <Filter size={11} /> Showing {filtered.length} of {allLogs.length} events
      </div>

      {/* Log entries */}
      <Card className="overflow-hidden">
        <div className="divide-y divide-slate-800/50 font-mono">
          {filtered.map(log => (
            <div key={log.id} className="flex items-start gap-4 px-5 py-3 hover:bg-slate-800/30 transition-colors">
              <div className="mt-0.5 shrink-0">
                {log.success
                  ? <CheckCircle size={14} className="text-emerald-400" />
                  : <XCircle size={14} className="text-red-400" />
                }
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-xs text-slate-400">{new Date(log.timestamp).toISOString().replace('T', ' ').replace('Z', '')}</span>
                  <Badge variant="gray">{log.component}</Badge>
                  <Badge variant={log.success ? 'green' : 'red'}>{log.event_type}</Badge>
                </div>
                <p className="text-xs text-slate-300 mt-0.5 font-sans">{log.message}</p>
              </div>
            </div>
          ))}
          {filtered.length === 0 && (
            <div className="px-5 py-8 text-center">
              <p className="text-sm text-slate-500">No logs match your filters.</p>
            </div>
          )}
        </div>
      </Card>
    </div>
  );
}

'use client';

import { mockAgents, mockProcesses, mockTasks, mockAuditLogs } from '../lib/mock-data';
import Card from '../components/ui/Card';
import Badge from '../components/ui/Badge';
import StatusDot from '../components/ui/StatusDot';
import {
  Bot, Cpu, ListTodo, CheckCircle, AlertTriangle,
  TrendingUp, Activity, Clock, ArrowRight, Zap,
  Mail, Share2, Database, BarChart3,
} from 'lucide-react';
import Link from 'next/link';

function StatCard({ icon: Icon, label, value, sub, color, href }: {
  icon: React.ElementType; label: string; value: string | number;
  sub: string; color: string; href: string;
}) {
  return (
    <Link href={href}>
      <Card hover className="p-5 cursor-pointer group">
        <div className="flex items-start justify-between">
          <div className={`p-2.5 rounded-lg border ${color}`}>
            <Icon size={18} />
          </div>
          <ArrowRight size={14} className="text-slate-600 group-hover:text-slate-400 transition-colors" />
        </div>
        <div className="mt-4">
          <p className="text-2xl font-bold text-slate-100">{value}</p>
          <p className="text-sm font-medium text-slate-300 mt-0.5">{label}</p>
          <p className="text-xs text-slate-500 mt-1">{sub}</p>
        </div>
      </Card>
    </Link>
  );
}

export default function DashboardPage() {
  const running = mockAgents.filter(a => a.status === 'running').length;
  const errors = mockAgents.filter(a => a.status === 'error').length;
  const onlineProcs = mockProcesses.filter(p => p.status === 'online').length;
  const pendingTasks = mockTasks.filter(t => t.status === 'pending').length;
  const pendingApprovals = mockTasks.filter(t => t.status === 'approved').length;

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-100">System Overview</h1>
        <p className="text-sm text-slate-500 mt-0.5">Real-time status of your AI Employee automation system</p>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={Bot} label="Active Agents" value={running} sub={`${errors} with errors`} color="bg-emerald-500/10 border-emerald-500/20 text-emerald-400" href="/agents" />
        <StatCard icon={Cpu} label="Processes Online" value={onlineProcs} sub={`of ${mockProcesses.length} total`} color="bg-blue-500/10 border-blue-500/20 text-blue-400" href="/processes" />
        <StatCard icon={ListTodo} label="Tasks Pending" value={pendingTasks} sub="awaiting processing" color="bg-yellow-500/10 border-yellow-500/20 text-yellow-400" href="/tasks" />
        <StatCard icon={CheckCircle} label="Needs Approval" value={pendingApprovals} sub="drafts ready to review" color="bg-purple-500/10 border-purple-500/20 text-purple-400" href="/approvals" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <Card className="p-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                <Bot size={16} className="text-emerald-400" /> Agent Status
              </h2>
              <Link href="/agents" className="text-xs text-emerald-400 hover:text-emerald-300 flex items-center gap-1 cursor-pointer transition-colors">
                View all <ArrowRight size={12} />
              </Link>
            </div>
            <div className="space-y-2">
              {mockAgents.slice(0, 6).map(agent => (
                <div key={agent.id} className="flex items-center justify-between py-2.5 px-3 rounded-lg bg-slate-800/40 hover:bg-slate-800/70 transition-colors">
                  <div className="flex items-center gap-3 min-w-0">
                    <StatusDot status={agent.status as 'running' | 'stopped' | 'error' | 'idle'} />
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-slate-200 truncate">{agent.name}</p>
                      {agent.lastRun && (
                        <p className="text-xs text-slate-500 flex items-center gap-1">
                          <Clock size={10} /> {agent.lastRun}
                        </p>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <span className="text-xs text-slate-500 hidden sm:block">{agent.tasksProcessed} tasks</span>
                    {agent.errorsToday > 0 && <Badge variant="red">{agent.errorsToday} err</Badge>}
                    <Badge variant={agent.status === 'running' ? 'green' : agent.status === 'error' ? 'red' : agent.status === 'idle' ? 'yellow' : 'gray'}>
                      {agent.status}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>

        <div className="space-y-4">
          <Card className="p-5">
            <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2 mb-4">
              <Activity size={16} className="text-blue-400" /> Integration Health
            </h2>
            <div className="space-y-2.5">
              {[
                { name: 'Groq AI', icon: Zap, status: 'green', label: 'Active' },
                { name: 'Gmail', icon: Mail, status: 'green', label: 'Polling' },
                { name: 'WhatsApp', icon: Share2, status: 'red', label: 'Disconnected' },
                { name: 'Odoo', icon: Database, status: 'green', label: 'Connected' },
                { name: 'Slack', icon: BarChart3, status: 'green', label: 'Active' },
              ].map(({ name, icon: Icon, status, label }) => (
                <div key={name} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Icon size={14} className="text-slate-500" />
                    <span className="text-sm text-slate-300">{name}</span>
                  </div>
                  <Badge variant={status as 'green' | 'red'}>{label}</Badge>
                </div>
              ))}
            </div>
          </Card>

          <Card className="p-5">
            <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2 mb-4">
              <TrendingUp size={16} className="text-purple-400" /> Quick Actions
            </h2>
            <div className="grid grid-cols-2 gap-2">
              {[
                { label: 'Add Credentials', href: '/credentials', color: 'text-emerald-400', bg: 'bg-emerald-500/10 hover:bg-emerald-500/20 border-emerald-500/20' },
                { label: 'View Approvals', href: '/approvals', color: 'text-purple-400', bg: 'bg-purple-500/10 hover:bg-purple-500/20 border-purple-500/20' },
                { label: 'Manage Agents', href: '/agents', color: 'text-blue-400', bg: 'bg-blue-500/10 hover:bg-blue-500/20 border-blue-500/20' },
                { label: 'Audit Logs', href: '/logs', color: 'text-yellow-400', bg: 'bg-yellow-500/10 hover:bg-yellow-500/20 border-yellow-500/20' },
              ].map(({ label, href, color, bg }) => (
                <Link key={href} href={href}>
                  <button className={`w-full p-3 rounded-lg border text-xs font-medium ${color} ${bg} transition-colors cursor-pointer text-center`}>
                    {label}
                  </button>
                </Link>
              ))}
            </div>
          </Card>
        </div>
      </div>

      <Card className="p-5">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
            <Activity size={16} className="text-cyan-400" /> Recent Audit Activity
          </h2>
          <Link href="/logs" className="text-xs text-emerald-400 hover:text-emerald-300 flex items-center gap-1 cursor-pointer transition-colors">
            View all logs <ArrowRight size={12} />
          </Link>
        </div>
        <div className="space-y-2">
          {mockAuditLogs.slice(0, 5).map(log => (
            <div key={log.id} className="flex items-start gap-4 py-2.5 px-3 rounded-lg bg-slate-800/40">
              <div className={`mt-1.5 w-1.5 h-1.5 rounded-full shrink-0 ${log.success ? 'bg-emerald-400' : 'bg-red-400'}`} />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-xs font-medium text-slate-300">{log.component}</span>
                  <Badge variant={log.success ? 'green' : 'red'}>{log.event_type}</Badge>
                </div>
                <p className="text-xs text-slate-500 mt-0.5 truncate">{log.message}</p>
              </div>
              <span className="text-xs text-slate-600 shrink-0 hidden sm:block">
                {new Date(log.timestamp).toLocaleTimeString()}
              </span>
            </div>
          ))}
        </div>
      </Card>

      {errors > 0 && (
        <Card className="p-4 border-red-500/20" glow="rgba(239,68,68,0.08)">
          <div className="flex items-center gap-3">
            <AlertTriangle size={18} className="text-red-400 shrink-0" />
            <div className="flex-1">
              <p className="text-sm font-medium text-red-300">Action Required</p>
              <p className="text-xs text-slate-500 mt-0.5">WhatsApp Watcher is disconnected — session expired. Re-scan QR code to restore.</p>
            </div>
            <Link href="/agents">
              <button className="text-xs text-red-400 hover:text-red-300 flex items-center gap-1 cursor-pointer whitespace-nowrap transition-colors">
                Fix now <ArrowRight size={12} />
              </button>
            </Link>
          </div>
        </Card>
      )}
    </div>
  );
}

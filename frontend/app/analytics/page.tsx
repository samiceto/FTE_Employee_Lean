'use client';

import Card from '../../components/ui/Card';
import { BarChart3, TrendingUp, Users, Zap, Clock, CheckCircle, DollarSign, Activity } from 'lucide-react';

const weeklyData = [
  { day: 'Mon', tasks: 12, emails: 4, posts: 3 },
  { day: 'Tue', tasks: 18, emails: 6, posts: 5 },
  { day: 'Wed', tasks: 8, emails: 2, posts: 2 },
  { day: 'Thu', tasks: 22, emails: 8, posts: 4 },
  { day: 'Fri', tasks: 15, emails: 5, posts: 6 },
  { day: 'Sat', tasks: 6, emails: 1, posts: 1 },
  { day: 'Sun', tasks: 3, emails: 0, posts: 0 },
];

const maxTasks = Math.max(...weeklyData.map(d => d.tasks));

function BarChart({ data, maxVal, color }: { data: typeof weeklyData; maxVal: number; color: string }) {
  return (
    <div className="flex items-end gap-2 h-24">
      {data.map(d => (
        <div key={d.day} className="flex-1 flex flex-col items-center gap-1">
          <div
            className={`w-full rounded-t-sm ${color} transition-all`}
            style={{ height: `${(d.tasks / maxVal) * 100}%`, minHeight: d.tasks > 0 ? '4px' : '0' }}
          />
          <span className="text-xs text-slate-600">{d.day}</span>
        </div>
      ))}
    </div>
  );
}

export default function AnalyticsPage() {
  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-100 flex items-center gap-2">
          <BarChart3 size={20} className="text-purple-400" /> Analytics & Reports
        </h1>
        <p className="text-sm text-slate-500 mt-0.5">Weekly performance overview — last 7 days</p>
      </div>

      {/* KPI grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: 'Tasks Processed', value: '84', change: '+12%', icon: CheckCircle, color: 'text-emerald-400', bg: 'bg-emerald-500/10 border-emerald-500/20' },
          { label: 'Emails Handled', value: '26', change: '+5%', icon: Activity, color: 'text-blue-400', bg: 'bg-blue-500/10 border-blue-500/20' },
          { label: 'Posts Published', value: '21', change: '+8%', icon: TrendingUp, color: 'text-purple-400', bg: 'bg-purple-500/10 border-purple-500/20' },
          { label: 'Time Saved (est.)', value: '41h', change: 'this week', icon: Clock, color: 'text-yellow-400', bg: 'bg-yellow-500/10 border-yellow-500/20' },
        ].map(({ label, value, change, icon: Icon, color, bg }) => (
          <Card key={label} className={`p-5 border ${bg}`}>
            <div className="flex items-start justify-between">
              <Icon size={18} className={color} />
              <span className="text-xs text-emerald-400 font-medium">{change}</span>
            </div>
            <p className="text-2xl font-bold text-slate-100 mt-3">{value}</p>
            <p className="text-xs text-slate-500 mt-0.5">{label}</p>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Task chart */}
        <Card className="p-5">
          <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2 mb-4">
            <Zap size={14} className="text-emerald-400" /> Tasks This Week
          </h2>
          <BarChart data={weeklyData} maxVal={maxTasks} color="bg-emerald-500/70" />
          <div className="mt-3 flex items-center justify-between text-xs text-slate-500">
            <span>84 total tasks</span>
            <span>Avg: 12/day</span>
          </div>
        </Card>

        {/* Platform breakdown */}
        <Card className="p-5">
          <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2 mb-4">
            <Users size={14} className="text-blue-400" /> Platform Breakdown
          </h2>
          <div className="space-y-3">
            {[
              { label: 'LinkedIn', posts: 4, pct: 67, color: 'bg-blue-500' },
              { label: 'X / Twitter', posts: 11, pct: 100, color: 'bg-slate-400' },
              { label: 'Instagram', posts: 2, pct: 33, color: 'bg-pink-500' },
              { label: 'Facebook', posts: 0, pct: 0, color: 'bg-blue-300' },
              { label: 'Email', posts: 26, pct: 85, color: 'bg-emerald-500' },
            ].map(({ label, posts, pct, color }) => (
              <div key={label}>
                <div className="flex items-center justify-between text-xs mb-1">
                  <span className="text-slate-300">{label}</span>
                  <span className="text-slate-500">{posts} posts</span>
                </div>
                <div className="h-1.5 rounded-full bg-slate-700 overflow-hidden">
                  <div className={`h-full rounded-full ${color} transition-all`} style={{ width: `${pct}%` }} />
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* Financial summary */}
        <Card className="p-5">
          <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2 mb-4">
            <DollarSign size={14} className="text-yellow-400" /> Financial Summary (Odoo)
          </h2>
          <div className="grid grid-cols-2 gap-4">
            {[
              { label: 'Invoices Created', value: '$12,400', sub: '3 this week' },
              { label: 'Expenses Logged', value: '$2,180', sub: '8 entries' },
              { label: 'Net Revenue', value: '$10,220', sub: 'this month' },
              { label: 'Pending Invoices', value: '$5,000', sub: '1 outstanding' },
            ].map(({ label, value, sub }) => (
              <div key={label} className="p-3 rounded-lg bg-slate-800/60 border border-slate-700">
                <p className="text-xs text-slate-500">{label}</p>
                <p className="text-base font-bold text-slate-100 mt-1">{value}</p>
                <p className="text-xs text-slate-600 mt-0.5">{sub}</p>
              </div>
            ))}
          </div>
        </Card>

        {/* Agent efficiency */}
        <Card className="p-5">
          <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2 mb-4">
            <Activity size={14} className="text-cyan-400" /> Agent Efficiency
          </h2>
          <div className="space-y-3">
            {[
              { name: 'Reasoning Agent', tasks: 142, success: 98, color: 'bg-emerald-500' },
              { name: 'Execution Agent', tasks: 89, success: 94, color: 'bg-blue-500' },
              { name: 'Gmail Watcher', tasks: 31, success: 100, color: 'bg-cyan-500' },
              { name: 'Cloud Agent', tasks: 23, success: 100, color: 'bg-purple-500' },
            ].map(({ name, tasks, success, color }) => (
              <div key={name}>
                <div className="flex items-center justify-between text-xs mb-1">
                  <span className="text-slate-300">{name}</span>
                  <span className="text-slate-500">{tasks} tasks · <span className="text-emerald-400">{success}%</span> success</span>
                </div>
                <div className="h-1.5 rounded-full bg-slate-700 overflow-hidden">
                  <div className={`h-full rounded-full ${color}`} style={{ width: `${success}%` }} />
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}

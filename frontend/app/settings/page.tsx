'use client';

import { useState } from 'react';
import Card from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import Input from '../../components/ui/Input';
import { Settings, Save, Bell, Clock, Database, Shield, RefreshCw, AlertTriangle } from 'lucide-react';

interface ToggleProps {
  checked: boolean;
  onChange: (v: boolean) => void;
  label: string;
  description?: string;
}

function Toggle({ checked, onChange, label, description }: ToggleProps) {
  return (
    <div className="flex items-start justify-between gap-4">
      <div>
        <p className="text-sm font-medium text-slate-200">{label}</p>
        {description && <p className="text-xs text-slate-500 mt-0.5">{description}</p>}
      </div>
      <button
        role="switch"
        aria-checked={checked}
        onClick={() => onChange(!checked)}
        className={`relative inline-flex items-center h-5 w-9 rounded-full transition-colors duration-200 cursor-pointer shrink-0 ${checked ? 'bg-emerald-500' : 'bg-slate-600'}`}
      >
        <span className={`inline-block w-3.5 h-3.5 rounded-full bg-white shadow transition-transform duration-200 ${checked ? 'translate-x-4' : 'translate-x-0.5'}`} />
      </button>
    </div>
  );
}

export default function SettingsPage() {
  const [saved, setSaved] = useState(false);
  const [config, setConfig] = useState({
    reasoningInterval: '30',
    executionInterval: '5',
    gmailInterval: '2',
    auditRetention: '30',
    odooUrl: 'http://localhost:8069',
    odooDb: 'FTE',
    slackChannel: '#general',
    vaultPath: '/ai_employee_vault',
    autoApprove: false,
    notifyOnError: true,
    notifyOnSuccess: false,
    weeklyBriefing: true,
    emailEnabled: true,
    accountingEnabled: true,
    debugMode: false,
    retryOnFail: true,
    maxRetries: '3',
  });

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const update = (key: string, value: string | boolean) => setConfig(prev => ({ ...prev, [key]: value }));

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <Settings size={20} className="text-slate-400" /> System Settings
          </h1>
          <p className="text-sm text-slate-500 mt-0.5">Configure agent intervals, integrations, and behavior</p>
        </div>
        <Button variant="primary" icon={<Save size={14} />} onClick={handleSave} loading={saved}>
          {saved ? 'Saved!' : 'Save Changes'}
        </Button>
      </div>

      {/* Agent intervals */}
      <Card className="p-5 space-y-4">
        <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
          <Clock size={14} className="text-blue-400" /> Agent Intervals
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <Input
            label="Reasoning Agent (min)"
            type="number"
            value={config.reasoningInterval}
            onChange={e => update('reasoningInterval', e.target.value)}
            hint="Default: every 30 minutes"
          />
          <Input
            label="Execution Agent (min)"
            type="number"
            value={config.executionInterval}
            onChange={e => update('executionInterval', e.target.value)}
            hint="Default: every 5 minutes (Ralph)"
          />
          <Input
            label="Gmail Watcher (min)"
            type="number"
            value={config.gmailInterval}
            onChange={e => update('gmailInterval', e.target.value)}
            hint="Default: every 2 minutes"
          />
        </div>
      </Card>

      {/* Integrations */}
      <Card className="p-5 space-y-4">
        <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
          <Database size={14} className="text-yellow-400" /> Integrations
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Input label="Odoo Server URL" value={config.odooUrl} onChange={e => update('odooUrl', e.target.value)} />
          <Input label="Odoo Database Name" value={config.odooDb} onChange={e => update('odooDb', e.target.value)} />
          <Input label="Slack Default Channel" value={config.slackChannel} onChange={e => update('slackChannel', e.target.value)} />
          <Input label="Vault Path" value={config.vaultPath} onChange={e => update('vaultPath', e.target.value)} hint="Root path for the AI Employee vault" />
        </div>
      </Card>

      {/* Notifications */}
      <Card className="p-5 space-y-4">
        <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
          <Bell size={14} className="text-orange-400" /> Notifications
        </h2>
        <div className="space-y-4">
          <Toggle checked={config.notifyOnError} onChange={v => update('notifyOnError', v)} label="Notify on Error" description="Send Slack alert when an agent encounters an error" />
          <Toggle checked={config.notifyOnSuccess} onChange={v => update('notifyOnSuccess', v)} label="Notify on Success" description="Send Slack notification for completed tasks" />
          <Toggle checked={config.weeklyBriefing} onChange={v => update('weeklyBriefing', v)} label="Weekly CEO Briefing" description="Auto-generate and post business summary every Sunday 11 PM" />
        </div>
      </Card>

      {/* Feature toggles */}
      <Card className="p-5 space-y-4">
        <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
          <Shield size={14} className="text-purple-400" /> Feature Toggles
        </h2>
        <div className="space-y-4">
          <Toggle checked={config.emailEnabled} onChange={v => update('emailEnabled', v)} label="Email Integration" description="Enable Gmail watcher and email drafting" />
          <Toggle checked={config.accountingEnabled} onChange={v => update('accountingEnabled', v)} label="Accounting Integration" description="Enable Odoo invoice and expense creation" />
          <Toggle checked={config.autoApprove} onChange={v => update('autoApprove', v)} label="Auto-Approve Drafts" description="Automatically approve AI-generated drafts without review" />
        </div>
      </Card>

      {/* Error recovery */}
      <Card className="p-5 space-y-4">
        <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
          <RefreshCw size={14} className="text-cyan-400" /> Error Recovery
        </h2>
        <div className="space-y-4">
          <Toggle checked={config.retryOnFail} onChange={v => update('retryOnFail', v)} label="Retry on Failure" description="Use exponential backoff on transient errors" />
          <Input
            label="Max Retry Attempts"
            type="number"
            value={config.maxRetries}
            onChange={e => update('maxRetries', e.target.value)}
            hint="Default: 3 attempts with 1–60s delay"
          />
          <Input
            label="Audit Log Retention (days)"
            type="number"
            value={config.auditRetention}
            onChange={e => update('auditRetention', e.target.value)}
            hint="Logs older than this are automatically deleted"
          />
          <Toggle checked={config.debugMode} onChange={v => update('debugMode', v)} label="Debug Mode" description="Verbose logging — generates large log files" />
        </div>
      </Card>

      {/* Danger zone */}
      <Card className="p-5 border-red-500/20">
        <h2 className="text-sm font-semibold text-red-400 flex items-center gap-2 mb-4">
          <AlertTriangle size={14} /> Danger Zone
        </h2>
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-slate-200">Clear Task Queue</p>
              <p className="text-xs text-slate-500">Removes all pending tasks from Need_Action/</p>
            </div>
            <Button size="sm" variant="danger">Clear Queue</Button>
          </div>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-slate-200">Reset Execution State</p>
              <p className="text-xs text-slate-500">Clears all agent execution state files</p>
            </div>
            <Button size="sm" variant="danger">Reset State</Button>
          </div>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-slate-200">Stop All Processes</p>
              <p className="text-xs text-slate-500">Shuts down all PM2 processes immediately</p>
            </div>
            <Button size="sm" variant="danger">Stop All</Button>
          </div>
        </div>
      </Card>
    </div>
  );
}

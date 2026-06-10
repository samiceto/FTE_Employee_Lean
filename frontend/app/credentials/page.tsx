'use client';

import { useState } from 'react';
import { mockCredentials } from '../../lib/mock-data';
import type { Credential } from '../../lib/types';
import Card from '../../components/ui/Card';
import Badge from '../../components/ui/Badge';
import Button from '../../components/ui/Button';
import Input from '../../components/ui/Input';
import Modal from '../../components/ui/Modal';
import { KeyRound, Eye, EyeOff, Plus, Search, Edit2, Check, AlertCircle, Bot, Mail, Share2, DollarSign, Bell, Settings } from 'lucide-react';

const categoryConfig = {
  ai: { label: 'AI / LLM', icon: Bot, color: 'text-purple-400', bg: 'bg-purple-500/10 border-purple-500/20' },
  email: { label: 'Email', icon: Mail, color: 'text-blue-400', bg: 'bg-blue-500/10 border-blue-500/20' },
  social: { label: 'Social Media', icon: Share2, color: 'text-emerald-400', bg: 'bg-emerald-500/10 border-emerald-500/20' },
  accounting: { label: 'Accounting', icon: DollarSign, color: 'text-yellow-400', bg: 'bg-yellow-500/10 border-yellow-500/20' },
  notifications: { label: 'Notifications', icon: Bell, color: 'text-orange-400', bg: 'bg-orange-500/10 border-orange-500/20' },
  other: { label: 'Other', icon: Settings, color: 'text-slate-400', bg: 'bg-slate-500/10 border-slate-500/20' },
};

const CATEGORIES = Object.keys(categoryConfig) as Array<keyof typeof categoryConfig>;

export default function CredentialsPage() {
  const [credentials, setCredentials] = useState<Credential[]>(mockCredentials);
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState<string>('all');
  const [revealed, setRevealed] = useState<Set<string>>(new Set());
  const [editModal, setEditModal] = useState<Credential | null>(null);
  const [editValue, setEditValue] = useState('');
  const [saved, setSaved] = useState<string | null>(null);

  const filtered = credentials.filter(c => {
    const matchSearch = c.service.toLowerCase().includes(search.toLowerCase()) || c.keyName.toLowerCase().includes(search.toLowerCase());
    const matchFilter = filter === 'all' || c.category === filter;
    return matchSearch && matchFilter;
  });

  const grouped = CATEGORIES.reduce((acc, cat) => {
    const items = filtered.filter(c => c.category === cat);
    if (items.length > 0) acc[cat] = items;
    return acc;
  }, {} as Record<string, Credential[]>);

  const toggleReveal = (id: string) => {
    const next = new Set(revealed);
    next.has(id) ? next.delete(id) : next.add(id);
    setRevealed(next);
  };

  const openEdit = (cred: Credential) => {
    setEditModal(cred);
    setEditValue(cred.value || '');
  };

  const saveEdit = () => {
    if (!editModal) return;
    setCredentials(prev => prev.map(c =>
      c.id === editModal.id
        ? { ...c, value: editValue, isSet: editValue.length > 0, lastUpdated: 'just now' }
        : c
    ));
    setSaved(editModal.id);
    setTimeout(() => setSaved(null), 2000);
    setEditModal(null);
  };

  const setCount = credentials.filter(c => c.isSet).length;

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <KeyRound size={20} className="text-emerald-400" /> Credentials Manager
          </h1>
          <p className="text-sm text-slate-500 mt-0.5">{setCount} of {credentials.length} keys configured</p>
        </div>
        <div className="flex items-center gap-2">
          <div className="h-2 w-24 rounded-full bg-slate-700 overflow-hidden">
            <div className="h-full rounded-full bg-emerald-500 transition-all" style={{ width: `${(setCount / credentials.length) * 100}%` }} />
          </div>
          <span className="text-sm font-medium text-emerald-400">{Math.round((setCount / credentials.length) * 100)}%</span>
        </div>
      </div>

      {/* Search + filter */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="flex-1">
          <Input
            placeholder="Search credentials..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            icon={<Search size={14} />}
          />
        </div>
        <div className="flex gap-2 flex-wrap">
          {['all', ...CATEGORIES].map(cat => (
            <button
              key={cat}
              onClick={() => setFilter(cat)}
              className={`px-3 py-2 rounded-lg text-xs font-medium border transition-all cursor-pointer ${
                filter === cat
                  ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30'
                  : 'text-slate-400 border-slate-700 hover:border-slate-600 hover:text-slate-300'
              }`}
            >
              {cat === 'all' ? 'All' : categoryConfig[cat as keyof typeof categoryConfig].label}
            </button>
          ))}
        </div>
      </div>

      {/* Credential groups */}
      {Object.entries(grouped).map(([cat, items]) => {
        const cfg = categoryConfig[cat as keyof typeof categoryConfig];
        const Icon = cfg.icon;
        return (
          <div key={cat}>
            <div className="flex items-center gap-2 mb-3">
              <div className={`p-1.5 rounded-lg border ${cfg.bg}`}>
                <Icon size={14} className={cfg.color} />
              </div>
              <h2 className="text-sm font-semibold text-slate-300">{cfg.label}</h2>
              <span className="text-xs text-slate-600">({items.length})</span>
            </div>
            <Card className="overflow-hidden">
              <div className="divide-y divide-slate-800">
                {items.map(cred => (
                  <div key={cred.id} className="flex items-center gap-4 px-5 py-4 hover:bg-slate-800/30 transition-colors">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-sm font-medium text-slate-200">{cred.keyName}</span>
                        {cred.isSet ? (
                          <Badge variant="green"><Check size={10} className="mr-0.5" />Set</Badge>
                        ) : (
                          <Badge variant="red"><AlertCircle size={10} className="mr-0.5" />Missing</Badge>
                        )}
                      </div>
                      <p className="text-xs text-slate-500 mt-0.5">{cred.description}</p>
                      {cred.lastUpdated && (
                        <p className="text-xs text-slate-600 mt-0.5">Updated {cred.lastUpdated}</p>
                      )}
                    </div>

                    <div className="flex items-center gap-2">
                      {cred.isSet && (
                        <div className="hidden sm:flex items-center gap-2">
                          <code className="text-xs text-slate-400 font-mono bg-slate-800 px-2 py-1 rounded">
                            {revealed.has(cred.id)
                              ? (cred.keyName.toLowerCase().includes('url') || cred.keyName.toLowerCase().includes('host') ? cred.value : cred.value ? '••••••••••••' + cred.value.slice(-4) : '(empty)')
                              : '••••••••••••'}
                          </code>
                          <button
                            onClick={() => toggleReveal(cred.id)}
                            className="p-1.5 text-slate-500 hover:text-slate-300 transition-colors cursor-pointer"
                            aria-label={revealed.has(cred.id) ? 'Hide value' : 'Show value'}
                          >
                            {revealed.has(cred.id) ? <EyeOff size={14} /> : <Eye size={14} />}
                          </button>
                        </div>
                      )}
                      <Button size="sm" variant="outline" icon={<Edit2 size={12} />} onClick={() => openEdit(cred)}>
                        {cred.isSet ? 'Update' : 'Set Key'}
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          </div>
        );
      })}

      {/* Edit modal */}
      <Modal
        open={!!editModal}
        onClose={() => setEditModal(null)}
        title={`Update ${editModal?.keyName}`}
        footer={
          <>
            <Button variant="ghost" onClick={() => setEditModal(null)}>Cancel</Button>
            <Button variant="primary" onClick={saveEdit} loading={saved === editModal?.id}>
              Save Key
            </Button>
          </>
        }
      >
        {editModal && (
          <div className="space-y-4">
            <div className="p-3 rounded-lg bg-slate-800/50 border border-slate-700">
              <p className="text-xs text-slate-400">{editModal.description}</p>
              <p className="text-xs text-slate-600 mt-1">Service: {editModal.service}</p>
            </div>
            <Input
              label={editModal.keyName}
              type={editModal.keyName.toLowerCase().includes('url') || editModal.keyName.toLowerCase().includes('host') ? 'text' : 'password'}
              value={editValue}
              onChange={e => setEditValue(e.target.value)}
              placeholder={editModal.isSet ? 'Enter new value to update...' : 'Enter value...'}
              hint="Changes are applied immediately to all agents on save."
            />
            {!editModal.isSet && (
              <div className="flex items-center gap-2 text-xs text-yellow-400">
                <AlertCircle size={12} />
                This key is required for {editModal.service} to function.
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
}

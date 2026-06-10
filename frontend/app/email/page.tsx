'use client';

import { useState } from 'react';
import Card from '../../components/ui/Card';
import Badge from '../../components/ui/Badge';
import Button from '../../components/ui/Button';
import Modal from '../../components/ui/Modal';
import { Mail, Inbox, Send, Clock, Star, AlertCircle, Eye, CheckCircle, XCircle } from 'lucide-react';

const emails = [
  { id: '1', from: 'client@acmecorp.com', subject: 'Re: Q2 Project Timeline', preview: 'Hi, following up on the updated timeline we discussed...', time: '2 hours ago', priority: 'high', status: 'pending', draft: 'Hi,\n\nThank you for following up. The updated timeline for Q2 is as follows:\n\n- Phase 1 (Design): May 15\n- Phase 2 (Development): June 1\n- Phase 3 (Testing): June 20\n- Final Delivery: June 30\n\nPlease let me know if you have any questions.\n\nBest regards,\nSami' },
  { id: '2', from: 'vendor@techsupply.com', subject: 'Invoice #INV-2026-089', preview: 'Please find attached invoice for cloud services...', time: '4 hours ago', priority: 'medium', status: 'pending', draft: null },
  { id: '3', from: 'hr@company.com', subject: 'Team Meeting Rescheduled', preview: 'The Friday standup has been moved to Monday at 10am...', time: 'yesterday', priority: 'low', status: 'sent', draft: null },
  { id: '4', from: 'noreply@stripe.com', subject: 'Payment Received', preview: 'Your payment of $1,200 has been processed successfully...', time: '2 days ago', priority: 'low', status: 'done', draft: null },
];

export default function EmailPage() {
  const [selected, setSelected] = useState<typeof emails[0] | null>(null);
  const [processing, setProcessing] = useState<string | null>(null);
  const [sent, setSent] = useState<Set<string>>(new Set());

  const handleSend = (id: string) => {
    setProcessing(id);
    setTimeout(() => {
      setSent(prev => new Set([...prev, id]));
      setProcessing(null);
      setSelected(null);
    }, 1500);
  };

  const pending = emails.filter(e => e.status === 'pending' && !sent.has(e.id));

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-100 flex items-center gap-2">
          <Mail size={20} className="text-blue-400" /> Email Management
        </h1>
        <p className="text-sm text-slate-500 mt-0.5">Monitor incoming emails · Review AI-drafted replies</p>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {[
          { label: 'Inbox', value: emails.length, icon: Inbox, color: 'text-blue-400' },
          { label: 'Pending Reply', value: pending.length, icon: Clock, color: 'text-yellow-400' },
          { label: 'Sent Today', value: 3, icon: Send, color: 'text-emerald-400' },
          { label: 'Important', value: emails.filter(e => e.priority === 'high').length, icon: Star, color: 'text-orange-400' },
        ].map(({ label, value, icon: Icon, color }) => (
          <Card key={label} className="p-4">
            <div className="flex items-center gap-3">
              <Icon size={18} className={color} />
              <div>
                <p className="text-xs text-slate-500">{label}</p>
                <p className="text-xl font-bold text-slate-100">{value}</p>
              </div>
            </div>
          </Card>
        ))}
      </div>

      <Card className="overflow-hidden">
        <div className="px-5 py-3 border-b border-slate-800 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
            <Inbox size={14} className="text-blue-400" /> Inbox
          </h2>
          <Badge variant="blue">{emails.length} emails</Badge>
        </div>
        <div className="divide-y divide-slate-800/50">
          {emails.map(email => {
            const isSent = sent.has(email.id);
            return (
              <div
                key={email.id}
                className="flex items-start gap-4 px-5 py-4 hover:bg-slate-800/30 transition-colors cursor-pointer"
                onClick={() => setSelected(email)}
              >
                <div className={`mt-1 w-2 h-2 rounded-full shrink-0 ${email.priority === 'high' ? 'bg-orange-400' : email.priority === 'medium' ? 'bg-yellow-400' : 'bg-slate-600'}`} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-sm font-medium text-slate-200">{email.from}</span>
                    {email.priority === 'high' && <AlertCircle size={12} className="text-orange-400" />}
                  </div>
                  <p className="text-sm text-slate-300 truncate">{email.subject}</p>
                  <p className="text-xs text-slate-500 truncate mt-0.5">{email.preview}</p>
                </div>
                <div className="flex flex-col items-end gap-2 shrink-0">
                  <span className="text-xs text-slate-600">{email.time}</span>
                  <div className="flex items-center gap-1">
                    {isSent ? (
                      <Badge variant="green">Sent</Badge>
                    ) : email.status === 'pending' && email.draft ? (
                      <Badge variant="yellow">Draft Ready</Badge>
                    ) : email.status === 'done' ? (
                      <Badge variant="gray">Done</Badge>
                    ) : null}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </Card>

      {/* Email detail modal */}
      <Modal
        open={!!selected}
        onClose={() => setSelected(null)}
        title={selected?.subject ?? ''}
        size="lg"
        footer={selected?.draft && !sent.has(selected?.id ?? '') ? (
          <>
            <Button variant="danger" icon={<XCircle size={14} />} onClick={() => setSelected(null)}>Reject Draft</Button>
            <Button variant="primary" loading={processing === selected?.id} icon={<CheckCircle size={14} />} onClick={() => selected && handleSend(selected.id)}>
              Send Reply
            </Button>
          </>
        ) : undefined}
      >
        {selected && (
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <span className="text-sm text-slate-400">From:</span>
              <span className="text-sm text-slate-200 font-medium">{selected.from}</span>
              <Badge variant={selected.priority === 'high' ? 'orange' : selected.priority === 'medium' ? 'yellow' : 'gray'}>
                {selected.priority}
              </Badge>
            </div>
            <div className="p-4 rounded-lg bg-slate-800/60 border border-slate-700">
              <p className="text-xs text-slate-500 mb-2">Email Preview</p>
              <p className="text-sm text-slate-300">{selected.preview}</p>
            </div>
            {selected.draft ? (
              <div className="p-4 rounded-lg bg-emerald-500/5 border border-emerald-500/20">
                <div className="flex items-center gap-2 mb-2">
                  <Send size={12} className="text-emerald-400" />
                  <p className="text-xs text-emerald-400 font-medium">AI-Generated Draft Reply</p>
                </div>
                <pre className="text-sm text-slate-200 whitespace-pre-wrap font-sans leading-relaxed">
                  {selected.draft}
                </pre>
              </div>
            ) : (
              <div className="p-4 rounded-lg bg-slate-800/40 border border-slate-700 text-center">
                <p className="text-xs text-slate-500">No draft available — AI is processing this email.</p>
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
}

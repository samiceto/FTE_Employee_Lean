'use client';

import { useState } from 'react';
import { mockTasks } from '../../lib/mock-data';
import type { Task } from '../../lib/types';
import Card from '../../components/ui/Card';
import Badge from '../../components/ui/Badge';
import Button from '../../components/ui/Button';
import Modal from '../../components/ui/Modal';
import { CheckCircle, XCircle, Eye, AlertTriangle, Clock, ThumbsUp, ThumbsDown } from 'lucide-react';

const draftContent: Record<string, string> = {
  '2': `🚀 AI is transforming the workforce in 2025. Here's what top companies are doing differently:\n\n1. Automating repetitive tasks (saving 40+ hours/week)\n2. Using AI for smarter hiring decisions\n3. Building AI-human collaboration workflows\n\nThe companies that adapt now will lead the next decade.\n\nAre you leveraging AI in your business yet? Drop a comment below 👇\n\n#AI #FutureOfWork #BusinessGrowth #Automation`,
  '5': `✨ Something exciting is coming...\n\nStay tuned — we can't wait to share it with you! 🎉\n\n#ProductLaunch #ComingSoon #Innovation`,
};

export default function ApprovalsPage() {
  const [tasks, setTasks] = useState<Task[]>(mockTasks);
  const [selected, setSelected] = useState<Task | null>(null);
  const [processing, setProcessing] = useState<string | null>(null);

  const pendingApprovals = tasks.filter(t => t.status === 'approved' || t.status === 'pending');

  const handleDecision = (id: string, decision: 'approve' | 'reject') => {
    setProcessing(id);
    setTimeout(() => {
      setTasks(prev => prev.map(t =>
        t.id === id
          ? { ...t, status: decision === 'approve' ? 'done' : 'rejected', updatedAt: 'just now' }
          : t
      ));
      setProcessing(null);
      setSelected(null);
    }, 1200);
  };

  const platformColors: Record<string, string> = {
    linkedin: 'blue', instagram: 'purple', x: 'gray',
    facebook: 'blue', gmail: 'blue', odoo: 'yellow', whatsapp: 'green',
  };

  const approved = tasks.filter(t => t.status === 'done').length;
  const rejected = tasks.filter(t => t.status === 'rejected').length;

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <CheckCircle size={20} className="text-purple-400" /> Approval Workflow
          </h1>
          <p className="text-sm text-slate-500 mt-0.5">Review and approve AI-generated drafts before execution</p>
        </div>
        <div className="flex gap-3 text-xs">
          <div className="px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 font-medium">
            {approved} approved
          </div>
          <div className="px-3 py-1.5 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 font-medium">
            {rejected} rejected
          </div>
        </div>
      </div>

      {pendingApprovals.length === 0 ? (
        <Card className="p-12 text-center">
          <ThumbsUp size={32} className="text-emerald-400 mx-auto mb-3" />
          <p className="text-sm font-medium text-slate-300">All caught up!</p>
          <p className="text-xs text-slate-500 mt-1">No pending approvals at this time.</p>
        </Card>
      ) : (
        <div className="space-y-3">
          {pendingApprovals.map(task => {
            const isProcessing = processing === task.id;
            const hasDraft = !!draftContent[task.id];

            return (
              <Card key={task.id} className={task.priority === 'critical' ? 'border-red-500/20' : ''}>
                <div className="p-4">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        {task.priority === 'critical' && <AlertTriangle size={14} className="text-red-400" />}
                        <span className="text-sm font-medium text-slate-200">{task.title}</span>
                      </div>
                      <div className="flex items-center gap-2 mt-1.5 flex-wrap">
                        <Badge variant={platformColors[task.platform ?? ''] as 'blue' | 'purple' | 'gray' | 'green' | 'yellow' ?? 'gray'}>
                          {task.platform}
                        </Badge>
                        <Badge variant={
                          task.priority === 'critical' ? 'red' :
                          task.priority === 'high' ? 'orange' :
                          task.priority === 'medium' ? 'yellow' : 'gray'
                        }>
                          {task.priority}
                        </Badge>
                        <span className="text-xs text-slate-500 flex items-center gap-1">
                          <Clock size={10} /> {task.createdAt}
                        </span>
                      </div>
                      {task.description && (
                        <p className="text-xs text-slate-500 mt-1.5">{task.description}</p>
                      )}
                    </div>

                    <div className="flex items-center gap-2 shrink-0">
                      {hasDraft && (
                        <Button size="sm" variant="ghost" icon={<Eye size={12} />} onClick={() => setSelected(task)}>
                          Preview
                        </Button>
                      )}
                      <Button
                        size="sm" variant="danger"
                        loading={isProcessing}
                        icon={<XCircle size={12} />}
                        onClick={() => handleDecision(task.id, 'reject')}
                      >
                        Reject
                      </Button>
                      <Button
                        size="sm" variant="primary"
                        loading={isProcessing}
                        icon={<CheckCircle size={12} />}
                        onClick={() => handleDecision(task.id, 'approve')}
                      >
                        Approve
                      </Button>
                    </div>
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      )}

      {/* Recently processed */}
      <div>
        <h2 className="text-sm font-semibold text-slate-400 mb-3">Recently Processed</h2>
        <div className="space-y-2">
          {tasks.filter(t => t.status === 'done' || t.status === 'rejected').map(task => (
            <div key={task.id} className="flex items-center justify-between px-4 py-3 rounded-lg bg-slate-800/30 border border-slate-800">
              <div className="flex items-center gap-3 min-w-0">
                {task.status === 'done'
                  ? <ThumbsUp size={14} className="text-emerald-400 shrink-0" />
                  : <ThumbsDown size={14} className="text-red-400 shrink-0" />
                }
                <span className="text-sm text-slate-300 truncate">{task.title}</span>
              </div>
              <Badge variant={task.status === 'done' ? 'green' : 'red'}>
                {task.status === 'done' ? 'Approved' : 'Rejected'}
              </Badge>
            </div>
          ))}
        </div>
      </div>

      {/* Preview modal */}
      <Modal
        open={!!selected}
        onClose={() => setSelected(null)}
        title="Content Preview"
        size="md"
        footer={
          <>
            <Button variant="danger" icon={<XCircle size={14} />} onClick={() => selected && handleDecision(selected.id, 'reject')}>
              Reject
            </Button>
            <Button variant="primary" icon={<CheckCircle size={14} />} onClick={() => selected && handleDecision(selected.id, 'approve')}>
              Approve & Post
            </Button>
          </>
        }
      >
        {selected && (
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <Badge variant="blue">{selected.platform}</Badge>
              <Badge variant={selected.priority === 'critical' ? 'red' : selected.priority === 'high' ? 'orange' : 'yellow'}>
                {selected.priority}
              </Badge>
            </div>
            <div className="p-4 rounded-lg bg-slate-800/60 border border-slate-700">
              <pre className="text-sm text-slate-200 whitespace-pre-wrap font-sans leading-relaxed">
                {draftContent[selected.id] ?? 'No draft preview available.'}
              </pre>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}

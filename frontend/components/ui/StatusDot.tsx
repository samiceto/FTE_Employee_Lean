type StatusType = 'online' | 'running' | 'stopped' | 'error' | 'errored' | 'idle' | 'launching';

const config: Record<StatusType, { color: string; pulse: boolean; label: string }> = {
  online: { color: 'bg-emerald-400', pulse: true, label: 'Online' },
  running: { color: 'bg-emerald-400', pulse: true, label: 'Running' },
  stopped: { color: 'bg-slate-500', pulse: false, label: 'Stopped' },
  error: { color: 'bg-red-400', pulse: true, label: 'Error' },
  errored: { color: 'bg-red-400', pulse: true, label: 'Errored' },
  idle: { color: 'bg-yellow-400', pulse: false, label: 'Idle' },
  launching: { color: 'bg-blue-400', pulse: true, label: 'Launching' },
};

export default function StatusDot({ status, showLabel = false }: { status: StatusType; showLabel?: boolean }) {
  const cfg = config[status] ?? config.stopped;
  return (
    <span className="inline-flex items-center gap-1.5">
      <span className="relative flex items-center justify-center w-2 h-2">
        {cfg.pulse && (
          <span className={`absolute inline-flex w-full h-full rounded-full ${cfg.color} opacity-40 animate-ping`} />
        )}
        <span className={`relative inline-flex w-2 h-2 rounded-full ${cfg.color}`} />
      </span>
      {showLabel && <span className="text-xs text-slate-400">{cfg.label}</span>}
    </span>
  );
}

export type AgentStatus = 'running' | 'stopped' | 'error' | 'idle';
export type ProcessStatus = 'online' | 'stopped' | 'errored' | 'launching';
export type TaskStatus = 'pending' | 'in_progress' | 'approved' | 'rejected' | 'done';
export type Priority = 'critical' | 'high' | 'medium' | 'low';
export type Platform = 'whatsapp' | 'gmail' | 'odoo' | 'slack';

export interface Agent {
  id: string;
  name: string;
  description: string;
  status: AgentStatus;
  lastRun?: string;
  nextRun?: string;
  interval?: string;
  tasksProcessed: number;
  errorsToday: number;
  uptime?: string;
  credentials: string[];
}

export interface Process {
  id: string;
  name: string;
  status: ProcessStatus;
  pid?: number;
  cpu: number;
  memory: number;
  uptime?: string;
  restarts: number;
  lastRestart?: string;
}

export interface Task {
  id: string;
  title: string;
  type: string;
  platform?: Platform;
  status: TaskStatus;
  priority: Priority;
  createdAt: string;
  updatedAt?: string;
  assignedTo?: string;
  description?: string;
  content?: string;
}

export interface Credential {
  id: string;
  service: string;
  category: 'ai' | 'email' | 'messaging' | 'accounting' | 'notifications' | 'other';
  keyName: string;
  value: string;
  isSet: boolean;
  lastUpdated?: string;
  description?: string;
}

export interface AuditLog {
  id: string;
  timestamp: string;
  event_type: string;
  component: string;
  message: string;
  success: boolean;
  metadata?: Record<string, unknown>;
}

export interface StatsCard {
  label: string;
  value: string | number;
  change?: string;
  trend?: 'up' | 'down' | 'neutral';
  color?: string;
}

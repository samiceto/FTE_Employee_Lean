'use client';

import './globals.css';
import Sidebar from '../components/Sidebar';
import Header from '../components/Header';
import { useState, useEffect } from 'react';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(true);

  // Auto-collapse the sidebar on narrow windows so it never crowds the content
  useEffect(() => {
    const mq = window.matchMedia('(max-width: 900px)');
    const apply = () => setSidebarOpen(!mq.matches);
    apply();
    mq.addEventListener('change', apply);
    return () => mq.removeEventListener('change', apply);
  }, []);

  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <title>FTE AI Employee — Control Dashboard</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </head>
      <body>
        <div className="flex h-screen overflow-hidden" style={{ background: 'var(--bg-base)' }}>
          <div className="aurora-bg" aria-hidden="true" />
          <Sidebar open={sidebarOpen} onToggle={() => setSidebarOpen(!sidebarOpen)} />
          <div className="relative z-10 flex-1 flex flex-col min-w-0 overflow-hidden">
            <Header onMenuClick={() => setSidebarOpen(!sidebarOpen)} />
            <main className="flex-1 overflow-y-auto p-6 animate-slide-in">
              {children}
            </main>
          </div>
        </div>
      </body>
    </html>
  );
}

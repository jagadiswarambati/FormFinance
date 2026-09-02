'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/auth-context';
import { AppHeader } from '@/components/app/app-header';
import { AppSidebar } from '@/components/app/app-sidebar';

export function AppShell({ children }: Readonly<{ children: React.ReactNode }>) {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  useEffect(() => {
    if (!isLoading && !isAuthenticated) router.replace('/');
  }, [isAuthenticated, isLoading, router]);
  if (isLoading || !isAuthenticated)
    return (
      <main className="grid min-h-screen place-items-center text-sm text-slate-500">
        Loading FormWise AI…
      </main>
    );
  return (
    <div className="flex min-h-screen bg-slate-50 text-slate-950 dark:bg-slate-900 dark:text-slate-50">
      <AppSidebar
        collapsed={collapsed}
        mobileOpen={mobileOpen}
        onClose={() => setMobileOpen(false)}
      />
      <div className="flex min-w-0 flex-1 flex-col">
        <AppHeader
          onMenuClick={() => setMobileOpen(true)}
          onCollapse={() => setCollapsed((value) => !value)}
        />
        <main className="flex-1 p-4 sm:p-6 lg:p-8">{children}</main>
      </div>
    </div>
  );
}

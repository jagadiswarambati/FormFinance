'use client';

import { FileText, History, Home, Menu, Settings, Upload, X } from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

const items = [
  { href: '/app', label: 'Home', icon: Home },
  { href: '/app/upload', label: 'Upload', icon: Upload },
  { href: '/app/forms', label: 'My Forms', icon: FileText },
  { href: '/app/history', label: 'History', icon: History },
  { href: '/app/settings', label: 'Settings', icon: Settings },
];

export function AppSidebar({
  collapsed,
  mobileOpen,
  onClose,
}: Readonly<{ collapsed: boolean; mobileOpen: boolean; onClose(): void }>) {
  const pathname = usePathname();
  const navigation = (isCollapsed: boolean) => (
    <nav aria-label="Application navigation" className="space-y-1 px-3">
      {items.map(({ href, icon: Icon, label }) => (
        <Link
          key={href}
          href={href}
          onClick={onClose}
          title={isCollapsed ? label : undefined}
          className={cn(
            'flex h-11 items-center gap-3 rounded-lg px-3 text-sm font-medium text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800',
            pathname === href && 'bg-slate-100 text-slate-950 dark:bg-slate-800 dark:text-white',
            isCollapsed && 'justify-center px-0',
          )}
        >
          <Icon aria-hidden="true" className="h-5 w-5 shrink-0" />
          <span className={cn(isCollapsed && 'sr-only')}>{label}</span>
        </Link>
      ))}
    </nav>
  );
  return (
    <>
      <aside
        className={cn(
          'hidden shrink-0 border-r border-slate-200 bg-white py-4 transition-[width] duration-200 dark:border-slate-800 dark:bg-slate-950 lg:block',
          collapsed ? 'w-20' : 'w-64',
        )}
      >
        {navigation(collapsed)}
      </aside>
      <div
        className={cn(
          'fixed inset-0 z-40 bg-slate-950/40 transition-opacity lg:hidden',
          mobileOpen ? 'opacity-100' : 'pointer-events-none opacity-0',
        )}
        onClick={onClose}
        aria-hidden="true"
      />
      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-50 w-72 bg-white py-4 shadow-xl transition-transform dark:bg-slate-950 lg:hidden',
          mobileOpen ? 'translate-x-0' : '-translate-x-full',
        )}
        aria-label="Mobile navigation"
      >
        <div className="mb-6 flex items-center justify-between px-5">
          <span className="font-semibold">FormWise AI</span>
          <Button variant="ghost" size="icon" onClick={onClose} aria-label="Close navigation">
            <X className="h-5 w-5" />
          </Button>
        </div>
        {navigation(false)}
      </aside>
    </>
  );
}

export function MobileMenuButton({ onClick }: Readonly<{ onClick(): void }>) {
  return (
    <Button
      variant="ghost"
      size="icon"
      className="lg:hidden"
      onClick={onClick}
      aria-label="Open navigation"
    >
      <Menu className="h-5 w-5" />
    </Button>
  );
}

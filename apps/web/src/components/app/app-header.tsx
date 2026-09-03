'use client';

import { Menu, Moon, Search, Sun } from 'lucide-react';
import { useTheme } from '@/components/theme-provider';
import { Button } from '@/components/ui/button';

export function AppHeader({
  onMenuClick,
  onCollapse,
}: Readonly<{ onMenuClick(): void; onCollapse(): void }>) {
  const { theme, toggleTheme } = useTheme();
  return (
    <header className="flex h-16 shrink-0 items-center gap-3 border-b border-slate-200 bg-white px-4 dark:border-slate-800 dark:bg-slate-950">
      <Button
        variant="ghost"
        size="icon"
        className="lg:hidden"
        onClick={onMenuClick}
        aria-label="Open navigation"
      >
        <Menu className="h-5 w-5" />
      </Button>
      <Button
        variant="ghost"
        size="icon"
        className="hidden lg:inline-flex"
        onClick={onCollapse}
        aria-label="Toggle sidebar"
      >
        <Menu className="h-5 w-5" />
      </Button>
      <LinkBrand />
      <div className="mx-auto hidden max-w-md flex-1 md:block">
        <div className="flex h-9 items-center gap-2 rounded-lg border border-slate-200 bg-slate-50 px-3 text-sm text-slate-400 dark:border-slate-800 dark:bg-slate-900">
          <Search className="h-4 w-4" />
          <span>Search coming soon</span>
        </div>
      </div>
      <Button variant="ghost" size="icon" onClick={toggleTheme} aria-label="Toggle theme">
        {theme === 'dark' ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
      </Button>
      <span className="hidden text-xs font-medium uppercase tracking-widest text-slate-400 sm:block">Demo mode</span>
    </header>
  );
}

function LinkBrand() {
  return (
    <div className="flex items-center gap-2">
      <div className="grid h-8 w-8 place-items-center rounded-lg bg-slate-900 text-sm font-bold text-white dark:bg-slate-100 dark:text-slate-900">
        F
      </div>
      <span className="hidden font-semibold tracking-[0.12em] sm:inline">FORMFINANCE</span>
    </div>
  );
}

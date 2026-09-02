'use client';

import { ChevronDown, Menu, Moon, Search, Sun } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { useAuth } from '@/contexts/auth-context';
import { useTheme } from '@/components/theme-provider';
import { Button } from '@/components/ui/button';

export function AppHeader({
  onMenuClick,
  onCollapse,
}: Readonly<{ onMenuClick(): void; onCollapse(): void }>) {
  const { logout, profile } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const [menuOpen, setMenuOpen] = useState(false);
  const menuTriggerRef = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && menuOpen) {
        setMenuOpen(false);
        menuTriggerRef.current?.focus();
      }
    };
    window.addEventListener('keydown', closeOnEscape);
    return () => window.removeEventListener('keydown', closeOnEscape);
  }, [menuOpen]);
  const initials = (profile?.displayName ?? profile?.email ?? 'F').slice(0, 1).toUpperCase();
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
      <div className="relative">
        <Button
          ref={menuTriggerRef}
          variant="ghost"
          className="gap-2 px-2"
          onClick={() => setMenuOpen((open) => !open)}
          aria-expanded={menuOpen}
          aria-haspopup="menu"
        >
          <span className="grid h-8 w-8 place-items-center rounded-full bg-sky-100 text-xs font-semibold text-sky-800">
            {initials}
          </span>
          <ChevronDown className="h-4 w-4" />
        </Button>
        {menuOpen && (
          <div
            role="menu"
            aria-label="User account menu"
            className="absolute right-0 mt-2 w-48 rounded-lg border border-slate-200 bg-white p-1 shadow-lg dark:border-slate-700 dark:bg-slate-900"
          >
            <p className="px-3 py-2 text-xs text-slate-500">{profile?.email}</p>
            <button
              role="menuitem"
              className="w-full rounded-md px-3 py-2 text-left text-sm hover:bg-slate-100 dark:hover:bg-slate-800"
            >
              Profile
            </button>
            <button
              role="menuitem"
              className="w-full rounded-md px-3 py-2 text-left text-sm hover:bg-slate-100 dark:hover:bg-slate-800"
            >
              Settings
            </button>
            <button
              role="menuitem"
              className="w-full rounded-md px-3 py-2 text-left text-sm text-red-700 hover:bg-red-50 dark:hover:bg-red-950"
              onClick={() => void logout()}
            >
              Logout
            </button>
          </div>
        )}
      </div>
    </header>
  );
}

function LinkBrand() {
  return (
    <div className="flex items-center gap-2">
      <div className="grid h-8 w-8 place-items-center rounded-lg bg-slate-900 text-sm font-bold text-white dark:bg-slate-100 dark:text-slate-900">
        F
      </div>
      <span className="hidden font-semibold sm:inline">FormWise AI</span>
    </div>
  );
}

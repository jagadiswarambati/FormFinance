'use client';

import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { useTheme } from '@/components/theme-provider';
export default function SettingsPage() {
  const { theme, toggleTheme } = useTheme();
  return (
    <section className="mx-auto max-w-2xl">
      <h1 className="text-3xl font-semibold">Settings</h1>
      <p className="mt-2 text-slate-600 dark:text-slate-300">Read-only product and demo configuration.</p>
      <div className="mt-8 space-y-4">
        <section className="rounded-xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-950">
          <h2 className="font-semibold">Application</h2>
          <dl className="mt-3 space-y-2 text-sm text-slate-600 dark:text-slate-300"><div className="flex justify-between gap-4"><dt>Product</dt><dd className="font-medium text-slate-950 dark:text-white">AI Finance Controller</dd></div><div className="flex justify-between gap-4"><dt>Mode</dt><dd className="font-medium text-slate-950 dark:text-white">Demo Mode</dd></div><div className="flex justify-between gap-4"><dt>Authentication</dt><dd className="font-medium text-slate-950 dark:text-white">Disabled</dd></div></dl>
        </section>
        <section className="flex items-center justify-between rounded-xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-950">
          <div>
            <h2 className="font-semibold">Theme</h2>
            <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">
              {theme === 'dark' ? 'Dark' : 'Light'} mode
            </p>
          </div>
          <Button variant="outline" onClick={toggleTheme}>
            Toggle theme
          </Button>
        </section>
        <section className="rounded-xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-950">
          <h2 className="font-semibold">Processing stack</h2>
          <dl className="mt-3 space-y-2 text-sm text-slate-600 dark:text-slate-300"><div className="flex justify-between gap-4"><dt>OCR</dt><dd className="font-medium text-slate-950 dark:text-white">Existing OCR pipeline</dd></div><div className="flex justify-between gap-4"><dt>Verification</dt><dd className="text-right font-medium text-slate-950 dark:text-white">Deterministic + AI-assisted investigation</dd></div><div className="flex justify-between gap-4"><dt>Storage</dt><dd className="font-medium text-slate-950 dark:text-white">Existing document storage</dd></div></dl>
        </section>
        <Link href="/" className="inline-flex h-10 items-center rounded-lg border border-slate-200 px-4 py-2 text-sm font-medium text-red-700 transition-colors hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-800">Return to entry</Link>
      </div>
    </section>
  );
}

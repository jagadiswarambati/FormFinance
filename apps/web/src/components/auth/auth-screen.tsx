'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/auth-context';

export function AuthScreen() {
  const router = useRouter();
  const { signInWithGoogle, authMode, error, isLoading } = useAuth();
  const [isSigningIn, setIsSigningIn] = useState(false);

  const handleSignIn = async () => {
    setIsSigningIn(true);
    try {
      await signInWithGoogle();
      router.push('/app');
    } finally {
      setIsSigningIn(false);
    }
  };

  const busy = isSigningIn || isLoading;
  const bannerText =
    authMode === 'firebase'
      ? 'Secured by Firebase Authentication.'
      : authMode === 'demo'
        ? 'Demo mode — sign in creates a temporary session backed by the real backend pipeline, no Google account required.'
        : 'Sign-in is not configured for this deployment.';

  return (
    <main className="min-h-screen bg-[#f5f7f8] text-slate-950 dark:bg-slate-950 dark:text-slate-50">
      <section className="mx-auto flex min-h-screen max-w-7xl flex-col justify-between px-6 py-8 sm:px-10 lg:px-16">
        <header className="flex items-center justify-between">
          <div className="flex items-center gap-3"><div className="grid h-10 w-10 place-items-center rounded-md bg-emerald-700 text-sm font-bold text-white">F</div><span className="text-sm font-bold tracking-[0.18em]">FORMFINANCE</span></div>
          <span className="hidden text-xs font-medium uppercase tracking-[0.18em] text-slate-500 sm:block">AI Finance Controller</span>
        </header>
        <div className="grid gap-12 py-16 lg:grid-cols-[1.1fr_0.9fr] lg:items-center">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-emerald-700">AI Finance Controller</p>
            <h1 className="mt-6 max-w-3xl text-5xl font-semibold leading-[1.05] tracking-tight sm:text-6xl">Finance operations, verified automatically.</h1>
            <p className="mt-6 max-w-xl text-lg leading-8 text-slate-600 dark:text-slate-300">Automated settlement verification, evidence matching, and exception handling.</p>
            <div className="mt-10 flex flex-wrap gap-3">
              <button
                type="button"
                className="rounded-md bg-emerald-700 px-6 py-3 text-sm font-semibold text-white transition hover:bg-emerald-800 disabled:cursor-not-allowed disabled:opacity-60"
                onClick={() => void handleSignIn()}
                disabled={busy || authMode === 'unconfigured'}
              >
                {busy ? 'Signing in…' : 'Login'}
              </button>
              <button
                type="button"
                className="rounded-md border border-slate-300 bg-white px-6 py-3 text-sm font-semibold text-slate-800 transition hover:border-emerald-700 hover:text-emerald-800 disabled:cursor-not-allowed disabled:opacity-60 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
                onClick={() => void handleSignIn()}
                disabled={busy || authMode === 'unconfigured'}
              >
                {busy ? 'Signing in…' : 'Sign Up'}
              </button>
            </div>
            <p className="mt-5 text-xs text-slate-500">{bannerText}</p>
            {error && <p className="mt-2 text-xs text-rose-700" role="alert">{error}</p>}
          </div>
          <div className="relative overflow-hidden rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900"><div className="flex items-center justify-between border-b border-slate-100 pb-5 dark:border-slate-800"><div><p className="text-xs uppercase tracking-widest text-slate-500">Today’s control room</p><p className="mt-1 text-lg font-semibold">Settlement overview</p></div><span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-800">Live demo</span></div><div className="mt-6 grid grid-cols-2 gap-3"><Metric label="Processed" value="50" /><Metric label="Approved" value="20" /><Metric label="Flagged" value="12" /><Metric label="Escalated" value="13" /></div><div className="mt-5 rounded-lg bg-slate-950 p-4 text-white"><p className="text-xs uppercase tracking-widest text-slate-400">Control signal</p><p className="mt-2 text-2xl font-semibold">Exceptions surfaced early</p><div className="mt-4 h-2 rounded-full bg-slate-700"><div className="h-2 w-3/5 rounded-full bg-emerald-400" /></div></div></div>
        </div>
        <footer className="flex flex-wrap justify-between gap-3 border-t border-slate-200 pt-5 text-xs text-slate-500 dark:border-slate-800"><span>FORMFINANCE</span><span>Settlement verification for finance operations</span></footer>
      </section>
    </main>
  );
}

function Metric({ label, value }: { label: string; value: string }) { return <div className="rounded-lg border border-slate-200 p-4 dark:border-slate-800"><p className="text-xs text-slate-500">{label}</p><p className="mt-2 text-2xl font-semibold">{value}</p></div>; }

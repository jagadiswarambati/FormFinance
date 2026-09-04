'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { ArrowRight, CircleAlert, CircleCheck, FileCheck2, LoaderCircle, WalletCards } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/contexts/auth-context';
import { runDemoBatch, type BatchMetrics } from '@/services/settlements/batch-api';

export default function AppHomePage() {
  const { firebaseUser } = useAuth();
  const [metrics, setMetrics] = useState<BatchMetrics | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (!firebaseUser) return;
    let cancelled = false;
    setIsLoading(true);
    setError(null);
    (async () => {
      try {
        const token = await firebaseUser.getIdToken();
        const result = await runDemoBatch(token);
        if (!cancelled) setMetrics(result);
      } catch (cause) {
        if (!cancelled) setError(cause instanceof Error ? cause.message : 'Could not load batch metrics.');
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [firebaseUser]);

  const exceptions = metrics ? metrics.exceptions.length : null;

  return (
    <section className="mx-auto max-w-6xl space-y-8">
      <div className="flex flex-col justify-between gap-5 sm:flex-row sm:items-end"><div><p className="text-sm font-semibold uppercase tracking-[0.18em] text-emerald-700">AI Finance Controller</p><h1 className="mt-3 text-3xl font-semibold tracking-tight">Operations overview</h1><p className="mt-2 text-slate-600 dark:text-slate-300">Settlement decisions, exceptions, and evidence in one control room.</p></div><div className="flex gap-3"><Button><Link href="/app/settlements"><WalletCards className="mr-2 inline h-4 w-4" />Process Settlement</Link></Button><Button variant="outline"><Link href="/app/history">View Batch Results</Link></Button></div></div>
      {error && <p className="text-sm text-rose-700" role="alert">{error}</p>}
      {!firebaseUser && !error && <p className="text-sm text-slate-500">Sign in to load live batch metrics.</p>}
      {isLoading && !metrics && (
        <div className="flex items-center gap-2 text-sm text-slate-500"><LoaderCircle className="h-4 w-4 animate-spin" aria-hidden="true" />Running the settlement benchmark…</div>
      )}
      {metrics && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
          <Metric label="Settlements processed" value={String(metrics.totalSettlements)} icon={WalletCards} />
          <Metric label="Approved" value={String(metrics.approvedCount)} icon={CircleCheck} tone="green" />
          <Metric label="Flagged" value={String(metrics.flaggedCount)} icon={CircleAlert} tone="amber" />
          <Metric label="Escalated" value={String(metrics.escalatedCount)} icon={CircleAlert} tone="rose" />
          <Metric label="Exceptions" value={exceptions !== null ? String(exceptions) : '—'} icon={FileCheck2} tone="slate" />
        </div>
      )}
      <section className="rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-950"><div className="flex flex-wrap items-center justify-between gap-3"><div><h2 className="text-lg font-semibold">Settlement control</h2><p className="mt-1 text-sm text-slate-500">Start with a settlement PDF and let the verification pipeline surface the decision.</p></div><Link className="inline-flex items-center text-sm font-semibold text-emerald-700 hover:text-emerald-800" href="/app/settlements">Open processor <ArrowRight className="ml-2 h-4 w-4" /></Link></div><div className="mt-6 grid gap-3 md:grid-cols-4">{['Upload document', 'Run OCR', 'Verify evidence', 'Review decision'].map((step, index) => <div className="border-l-2 border-emerald-600 pl-3" key={step}><p className="text-xs font-semibold text-emerald-700">0{index + 1}</p><p className="mt-2 text-sm font-medium">{step}</p></div>)}</div></section>
      <p className="text-xs text-slate-500">{metrics ? 'Figures above come from a live run of the backend settlement benchmark (GET /settlements/batch/demo-run).' : 'Figures load from a live run of the backend settlement benchmark once you are signed in.'}</p>
    </section>
  );
}

function Metric({ label, value, icon: Icon, tone = 'slate' }: { label: string; value: string; icon: typeof WalletCards; tone?: 'green' | 'amber' | 'rose' | 'slate' }) { const colors = { green: 'text-emerald-700', amber: 'text-amber-700', rose: 'text-rose-700', slate: 'text-slate-700' }; return <article className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-950"><Icon className={`h-5 w-5 ${colors[tone]}`} aria-hidden="true" /><p className="mt-5 text-xs text-slate-500">{label}</p><p className="mt-1 text-2xl font-semibold">{value}</p></article>; }

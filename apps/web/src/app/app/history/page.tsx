'use client';

import { useCallback, useEffect, useState } from 'react';
import { ChartNoAxesCombined, LoaderCircle, RefreshCcw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/contexts/auth-context';
import { runDemoBatch, type BatchMetrics } from '@/services/settlements/batch-api';

function buildMetricRows(metrics: BatchMetrics): Array<[string, string]> {
  return [
    ['Total settlements', String(metrics.totalSettlements)],
    ['Records processed', `${metrics.processed} / ${metrics.totalRecords}`],
    ['Successfully extracted', String(metrics.successfullyExtracted)],
    ['Approved', String(metrics.approvedCount)],
    ['Flagged', String(metrics.flaggedCount)],
    ['Escalated', String(metrics.escalatedCount)],
    ['Processing failures', String(metrics.processingFailedCount)],
    ['Verified deductions', String(metrics.verifiedDeductions)],
    ['Disputed deductions', String(metrics.disputedDeductions)],
    ['Unverifiable deductions', String(metrics.unverifiableDeductions)],
    ['Settlement approval rate', `${Math.round(metrics.settlementApprovalRate * 100)}%`],
    ['Deduction verification rate', `${Math.round(metrics.deductionVerificationRate * 100)}%`],
    ['Evidence match rate', `${Math.round(metrics.evidenceMatchRate * 100)}%`],
    ['Extraction success rate', `${Math.round(metrics.extractionSuccessRate * 100)}%`],
    ['Exception rate', `${Math.round(metrics.exceptionRate * 100)}%`],
    ['AI agent investigations', String(metrics.agentInvestigations)],
    ['AI agent successes', String(metrics.agentSuccesses)],
  ];
}

export default function BatchResultsPage() {
  const { firebaseUser } = useAuth();
  const [metrics, setMetrics] = useState<BatchMetrics | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const load = useCallback(async () => {
    if (!firebaseUser) return;
    setIsLoading(true);
    setError(null);
    try {
      const token = await firebaseUser.getIdToken();
      setMetrics(await runDemoBatch(token));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Could not load batch results.');
    } finally {
      setIsLoading(false);
    }
  }, [firebaseUser]);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <section className="mx-auto max-w-5xl space-y-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-3"><ChartNoAxesCombined className="h-6 w-6 text-emerald-700" aria-hidden="true" /><p className="text-sm font-semibold uppercase tracking-[0.18em] text-emerald-700">Benchmark report</p></div>
          <h1 className="mt-3 text-3xl font-semibold">Batch results</h1>
          <p className="mt-2 text-slate-600 dark:text-slate-300">Live run of the backend&apos;s settlement benchmark against the real verification pipeline.</p>
        </div>
        <Button variant="outline" onClick={() => void load()} disabled={isLoading || !firebaseUser}>
          {isLoading ? <LoaderCircle className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" /> : <RefreshCcw className="mr-2 h-4 w-4" aria-hidden="true" />}
          Run batch again
        </Button>
      </div>
      {error && <p className="text-sm text-rose-700" role="alert">{error}</p>}
      {!firebaseUser && !error && <p className="text-sm text-slate-500">Sign in to run the batch benchmark.</p>}
      {isLoading && !metrics && (
        <div className="flex items-center gap-2 text-sm text-slate-500"><LoaderCircle className="h-4 w-4 animate-spin" aria-hidden="true" />Running settlements through extraction, verification, and decisioning…</div>
      )}
      {metrics && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {buildMetricRows(metrics).map(([label, value]) => (
            <article className="rounded-xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-950" key={label}>
              <p className="text-sm text-slate-500">{label}</p>
              <p className="mt-3 text-3xl font-semibold">{value}</p>
            </article>
          ))}
        </div>
      )}
      <p className="text-xs text-slate-500">
        {metrics
          ? `Generated ${metrics.timestamp} by GET /settlements/batch/demo-run — real extraction, verification, and decisioning ran for each of the ${metrics.totalSettlements} demo settlements.`
          : 'Values are loaded live from the backend batch benchmark endpoint, not hardcoded.'}
      </p>
    </section>
  );
}

import { ChartNoAxesCombined } from 'lucide-react';

const metrics = [
  ['Total records', '50'],
  ['Processed', '45'],
  ['Extraction success', '90%'],
  ['Approved', '20'],
  ['Flagged', '12'],
  ['Escalated', '13'],
  ['Failed', '5'],
  ['Evidence match rate', '0%'],
  ['Exception rate', '50%'],
];

export default function BatchResultsPage() {
  return <section className="mx-auto max-w-5xl space-y-8"><div><div className="flex items-center gap-3"><ChartNoAxesCombined className="h-6 w-6 text-emerald-700" aria-hidden="true" /><p className="text-sm font-semibold uppercase tracking-[0.18em] text-emerald-700">Benchmark report</p></div><h1 className="mt-3 text-3xl font-semibold">Batch results</h1><p className="mt-2 text-slate-600 dark:text-slate-300">Deterministic 50-record demo benchmark. Live production metrics are not loaded.</p></div><div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">{metrics.map(([label, value]) => <article className="rounded-xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-950" key={label}><p className="text-sm text-slate-500">{label}</p><p className="mt-3 text-3xl font-semibold">{value}</p></article>)}</div><p className="text-xs text-slate-500">Benchmark values come from the backend settlement benchmark definition and are presented as demo data.</p></section>;
}

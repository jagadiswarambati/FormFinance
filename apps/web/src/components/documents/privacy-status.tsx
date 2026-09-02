import { ShieldAlert, ShieldCheck, ShieldX } from 'lucide-react';
import type { DocumentRecord } from '@/services/documents/upload-api';

export function PrivacyStatus({ document }: { document: DocumentRecord }) {
  const states = {
    not_started: { label: 'Privacy scan needed', Icon: ShieldAlert, style: 'text-slate-500' },
    awaiting_consent: {
      label: 'Privacy decision needed',
      Icon: ShieldAlert,
      style: 'text-amber-700 dark:text-amber-300',
    },
    completed: {
      label: 'Protected for future AI',
      Icon: ShieldCheck,
      style: 'text-emerald-700 dark:text-emerald-300',
    },
    blocked: { label: 'Manual-only', Icon: ShieldX, style: 'text-rose-700 dark:text-rose-300' },
    cancelled: { label: 'Processing cancelled', Icon: ShieldX, style: 'text-slate-500' },
    failed: {
      label: 'Privacy scan failed',
      Icon: ShieldX,
      style: 'text-rose-700 dark:text-rose-300',
    },
  } as const;
  const state = states[document.privacyStatus];
  return (
    <span className={`inline-flex items-center gap-1 text-xs font-medium ${state.style}`}>
      <state.Icon className="h-4 w-4" />
      {state.label}
    </span>
  );
}

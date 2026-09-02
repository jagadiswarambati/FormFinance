'use client';

import { ShieldCheck } from 'lucide-react';
import { useState } from 'react';
import { Button } from '@/components/ui/button';
import type { PrivacyReport as PrivacyReportModel } from '@/services/documents/upload-api';

interface PrivacyReportProps {
  report: PrivacyReportModel;
  onDecision: (
    decision: 'continue_with_redaction' | 'continue_protected' | 'cancel',
  ) => Promise<void>;
}

export function PrivacyReport({ report, onDecision }: PrivacyReportProps) {
  const [submitting, setSubmitting] = useState(false);
  const decide = async (decision: 'continue_with_redaction' | 'continue_protected' | 'cancel') => {
    setSubmitting(true);
    try {
      await onDecision(decision);
    } finally {
      setSubmitting(false);
    }
  };
  return (
    <section className="rounded-xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-950">
      <div className="flex gap-3">
        <ShieldCheck className="mt-0.5 h-6 w-6 text-sky-700 dark:text-sky-300" />
        <div>
          <h2 className="font-semibold">Privacy report</h2>
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">
            Policy {report.policyVersion}. This report never exposes detected values.
          </p>
        </div>
      </div>
      {report.findings.length === 0 ? (
        <p className="mt-5 text-sm text-slate-600 dark:text-slate-300">
          No configured direct-identifier patterns were found. Future AI processing remains
          policy-gated.
        </p>
      ) : (
        <ul className="mt-5 space-y-2">
          {report.findings.map((finding) => (
            <li
              key={`${finding.category}-${finding.action}`}
              className="flex justify-between rounded-lg bg-slate-50 px-3 py-2 text-sm dark:bg-slate-900"
            >
              <span>
                {finding.category.replaceAll('_', ' ')} ({finding.count})
              </span>
              <span className="font-medium">{finding.action}</span>
            </li>
          ))}
        </ul>
      )}
      {report.status === 'blocked' && (
        <p className="mt-5 text-sm font-medium text-rose-700 dark:text-rose-300">
          This document contains manual-only data. It cannot continue to AI processing.
        </p>
      )}
      {report.requiresConsent && report.status === 'awaiting_consent' && (
        <div className="mt-6">
          <p className="text-sm text-slate-600 dark:text-slate-300">
            Continue only with the protected document. This never sends detected sensitive values or
            direct identifiers to an AI provider.
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            <Button disabled={submitting} onClick={() => void decide('continue_with_redaction')}>
              Continue with redaction
            </Button>
            <Button
              variant="outline"
              disabled={submitting}
              onClick={() => void decide('continue_protected')}
            >
              Continue with protected document
            </Button>
            <Button variant="ghost" disabled={submitting} onClick={() => void decide('cancel')}>
              Cancel
            </Button>
          </div>
        </div>
      )}
    </section>
  );
}

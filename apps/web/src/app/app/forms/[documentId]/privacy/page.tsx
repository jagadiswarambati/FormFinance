'use client';

import { useParams } from 'next/navigation';
import { useCallback, useEffect, useState } from 'react';
import { PrivacyReport } from '@/components/documents/privacy-report';
import { useAuth } from '@/contexts/auth-context';
import {
  getPrivacyReport,
  savePrivacyConsent,
  scanPrivacy,
  type PrivacyReport as PrivacyReportModel,
} from '@/services/documents/upload-api';
import { Button } from '@/components/ui/button';

export default function DocumentPrivacyPage() {
  const { documentId } = useParams<{ documentId: string }>();
  const { firebaseUser } = useAuth();
  const [report, setReport] = useState<PrivacyReportModel | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const load = useCallback(async () => {
    if (!firebaseUser) return;
    try {
      setReport(await getPrivacyReport(documentId, await firebaseUser.getIdToken()));
    } catch {
      setReport(null);
    } finally {
      setLoading(false);
    }
  }, [documentId, firebaseUser]);
  useEffect(() => {
    void load();
  }, [load]);
  const beginScan = async () => {
    if (!firebaseUser) return;
    setError(null);
    try {
      setReport(await scanPrivacy(documentId, await firebaseUser.getIdToken()));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Privacy scan could not be completed.');
    }
  };
  const decide = async (decision: 'continue_with_redaction' | 'continue_protected' | 'cancel') => {
    if (!firebaseUser) return;
    setReport(await savePrivacyConsent(documentId, decision, await firebaseUser.getIdToken()));
  };
  return (
    <section className="mx-auto max-w-3xl">
      <h1 className="text-3xl font-semibold">Privacy details</h1>
      <p className="mt-2 text-slate-600 dark:text-slate-300">
        Review server-generated policy decisions for this document.
      </p>
      {loading ? (
        <p className="mt-8 text-sm text-slate-600 dark:text-slate-300" role="status">
          Loading privacy report…
        </p>
      ) : report ? (
        <div className="mt-8">
          <PrivacyReport report={report} onDecision={decide} />
        </div>
      ) : (
        <div className="mt-8 rounded-xl border border-slate-200 p-6 dark:border-slate-800">
          <p className="text-sm text-slate-600 dark:text-slate-300">
            OCR is complete, but this document has not been privacy-scanned yet.
          </p>
          {error && (
            <p className="mt-3 text-sm text-rose-800 dark:text-rose-200" role="alert">
              {error}
            </p>
          )}
          <Button className="mt-5" onClick={() => void beginScan()}>
            Run privacy scan
          </Button>
        </div>
      )}
    </section>
  );
}

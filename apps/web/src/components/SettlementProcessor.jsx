'use client';

import React, { useState } from 'react';
import { AlertCircle, CheckCircle2, FileText, LoaderCircle, UploadCloud, XCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/contexts/auth-context';
import {
  completeUpload,
  createUploadIntent,
  getOcrStatus,
  startOcr,
  uploadToTarget,
} from '@/services/documents/upload-api';
import { processSettlementDocument } from '@/services/settlements/settlement-api';

const wait = (milliseconds) => new Promise((resolve) => window.setTimeout(resolve, milliseconds));

function formatAmount(value, currency = 'INR') {
  return new Intl.NumberFormat(undefined, { style: 'currency', currency }).format(value ?? 0);
}

function decisionLabel(status) {
  return { approve: 'APPROVED', flag: 'FLAGGED', escalate: 'ESCALATED' }[status] ?? status.toUpperCase();
}

function DecisionIcon({ status }) {
  if (status === 'approve') return <CheckCircle2 className="h-6 w-6" aria-hidden="true" />;
  if (status === 'escalate') return <XCircle className="h-6 w-6" aria-hidden="true" />;
  return <AlertCircle className="h-6 w-6" aria-hidden="true" />;
}

async function uploadDocument(file, idToken) {
  const intent = await createUploadIntent(file, idToken);
  await uploadToTarget(file, intent.uploadUrl);
  await completeUpload(intent.documentId, idToken);
  return intent.documentId;
}

async function waitForOcr(documentId, idToken, setOcrStatus) {
  await startOcr(documentId, idToken);
  let currentStatus = 'processing';
  for (let attempt = 0; attempt < 60 && currentStatus !== 'completed'; attempt += 1) {
    setOcrStatus(currentStatus);
    if (currentStatus === 'failed') throw new Error('PaddleOCR processing failed.');
    await wait(5000);
    currentStatus = (await getOcrStatus(documentId, idToken)).ocrStatus;
  }
  if (currentStatus !== 'completed') throw new Error('OCR is still processing. Please try again shortly.');
}

export default function SettlementProcessor() {
  const { firebaseUser } = useAuth();
  const [settlementFile, setSettlementFile] = useState(null);
  const [evidenceFiles, setEvidenceFiles] = useState([]);
  const [settlementDocumentId, setSettlementDocumentId] = useState(null);
  const [evidenceDocumentIds, setEvidenceDocumentIds] = useState([]);
  const [status, setStatus] = useState('idle');
  const [ocrStatus, setOcrStatus] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const selectSettlement = (event) => {
    const file = event.target.files?.[0];
    if (file) setSettlementFile(file);
  };

  const uploadSettlement = async () => {
    if (!settlementFile || !firebaseUser) return;
    setError(null);
    setStatus('uploading');
    try {
      const id = await uploadDocument(settlementFile, await firebaseUser.getIdToken());
      setSettlementDocumentId(id);
      setStatus('uploaded');
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Settlement upload failed.');
      setStatus('idle');
    }
  };

  const uploadEvidence = async (event) => {
    const files = Array.from(event.target.files ?? []);
    if (!firebaseUser || files.length === 0) return;
    setError(null);
    setStatus('uploading_evidence');
    try {
      const token = await firebaseUser.getIdToken();
      const ids = [];
      for (const file of files) ids.push(await uploadDocument(file, token));
      setEvidenceFiles((current) => [...current, ...files]);
      setEvidenceDocumentIds((current) => [...current, ...ids]);
      setStatus('uploaded');
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Evidence upload failed.');
      setStatus('uploaded');
    }
  };

  const process = async () => {
    if (!settlementDocumentId || !firebaseUser) return;
    setError(null);
    setResult(null);
    try {
      const token = await firebaseUser.getIdToken();
      setStatus('starting_ocr');
      await waitForOcr(settlementDocumentId, token, setOcrStatus);
      for (const evidenceDocumentId of evidenceDocumentIds) {
        await waitForOcr(evidenceDocumentId, token, setOcrStatus);
      }
      setOcrStatus('completed');
      setStatus('processing');
      setResult(await processSettlementDocument(settlementDocumentId, evidenceDocumentIds, token));
      setStatus('results');
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Settlement processing failed.');
      setStatus('uploaded');
    }
  };

  const reset = () => {
    setSettlementFile(null);
    setEvidenceFiles([]);
    setSettlementDocumentId(null);
    setEvidenceDocumentIds([]);
    setResult(null);
    setOcrStatus(null);
    setError(null);
    setStatus('idle');
  };

  if (status === 'results' && result) {
    const decision = result.decision ?? { status: result.status, confidence: 0, explanation: 'No decision details returned.' };
    const decisionStatus = decision.status === 'approved' ? 'approve' : decision.status;
    const currency = result.currency ?? 'INR';
    return (
      <section className="mx-auto max-w-5xl space-y-6">
        <div className={`rounded-2xl border p-6 ${decisionStatus === 'approve' ? 'border-emerald-200 bg-emerald-50 text-emerald-950' : decisionStatus === 'escalate' ? 'border-rose-200 bg-rose-50 text-rose-950' : 'border-amber-200 bg-amber-50 text-amber-950'}`}>
          <div className="flex items-center gap-3"><DecisionIcon status={decisionStatus} /><div><p className="text-sm font-medium">Final decision</p><h1 className="text-2xl font-bold">{decisionLabel(decisionStatus)}</h1></div></div>
          <p className="mt-4 text-sm">{decision.explanation}</p>
          <p className="mt-2 text-sm font-medium">Confidence: {Math.round((decision.confidence ?? 0) * 100)}%</p>
        </div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Summary label="Settlement ID" value={result.settlementId} />
          <Summary label="Reference" value={result.reference ?? result.documentId} />
          <Summary label="Gross amount" value={formatAmount(result.grossAmount, currency)} />
          <Summary label="Net amount" value={formatAmount(result.netAmount, currency)} />
        </div>
        <section className="rounded-xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-950">
          <h2 className="font-semibold">Deductions</h2>
          <div className="mt-4 divide-y divide-slate-200 dark:divide-slate-800">
            {result.deductions?.map((deduction) => <div className="flex flex-wrap items-center gap-3 py-3" key={deduction.id}><span className="w-28 text-sm font-medium capitalize">{deduction.type}</span><span className="text-sm">{formatAmount(deduction.amount, currency)}</span><span className="flex-1 text-sm text-slate-500">{deduction.reason ?? deduction.description}</span></div>)}
          </div>
          <p className="mt-4 text-sm text-slate-600 dark:text-slate-300">Total deductions: {formatAmount(result.totalDeductions ?? result.deductions?.reduce((sum, item) => sum + item.amount, 0), currency)}</p>
        </section>
        <EvidencePanel evidence={result.evidence} />
        <AuditPanel events={result.auditEvents} />
        <Button onClick={reset}>Process another settlement</Button>
      </section>
    );
  }

  const busy = ['uploading', 'uploading_evidence', 'starting_ocr', 'processing'].includes(status);
  return (
    <section className="mx-auto max-w-3xl space-y-6">
      <div><h1 className="text-3xl font-semibold">Settlement verification</h1><p className="mt-2 text-slate-600 dark:text-slate-300">Upload settlement and evidence PDFs for FormWise OCR and finance verification.</p></div>
      <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-6 dark:border-slate-700 dark:bg-slate-950">
        <UploadCloud className="h-8 w-8 text-sky-700" aria-hidden="true" /><h2 className="mt-4 font-semibold">Settlement PDF</h2>
        <input className="mt-3 block w-full text-sm" type="file" accept="application/pdf,.pdf" onChange={selectSettlement} disabled={busy} />
        {settlementFile && <p className="mt-3 text-sm text-slate-600">{settlementFile.name}</p>}
        {!settlementDocumentId && <Button className="mt-4" onClick={() => void uploadSettlement()} disabled={!settlementFile || busy}>{status === 'uploading' ? 'Uploading…' : 'Upload settlement'}</Button>}
        {settlementDocumentId && <p className="mt-3 text-sm text-emerald-700">Uploaded document: {settlementDocumentId}</p>}
      </div>
      {settlementDocumentId && <div className="rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-950"><h2 className="font-semibold">Evidence PDFs</h2><input className="mt-3 block w-full text-sm" type="file" accept="application/pdf,.pdf" multiple onChange={(event) => void uploadEvidence(event)} disabled={busy} />{evidenceFiles.length > 0 && <ul className="mt-3 space-y-2 text-sm">{evidenceFiles.map((file, index) => <li className="flex items-center gap-2" key={`${file.name}-${index}`}><FileText className="h-4 w-4" aria-hidden="true" />{file.name}</li>)}</ul>}<Button className="mt-5" onClick={() => void process()} disabled={busy}>{busy ? <><LoaderCircle className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" />{status === 'processing' ? 'Processing settlement…' : 'Preparing…'}</> : 'Run settlement verification'}</Button></div>}
      {ocrStatus && <p className="text-sm text-slate-600" role="status">OCR status: {ocrStatus}</p>}
      {error && <p className="text-sm text-rose-700" role="alert">{error}</p>}
    </section>
  );
}

function Summary({ label, value }) { return <div className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-950"><p className="text-xs uppercase tracking-wide text-slate-500">{label}</p><p className="mt-2 break-words font-semibold">{value ?? 'Not returned'}</p></div>; }
function EvidencePanel({ evidence }) { return <section className="rounded-xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-950"><h2 className="font-semibold">Evidence verification</h2>{evidence ? <div className="mt-4 grid gap-3 sm:grid-cols-2"><EvidenceValue label="Evidence found" value={evidence.evidenceFound} /><EvidenceValue label="Amount match" value={evidence.amountMatch} /><EvidenceValue label="Date match" value={evidence.dateMatch} /><EvidenceValue label="Reference match" value={evidence.referenceMatch} /></div> : <p className="mt-3 text-sm text-slate-500">Evidence comparison was not returned for this processing run.</p>}</section>; }
function EvidenceValue({ label, value }) { return <div className="flex justify-between border-b border-slate-100 py-2 text-sm dark:border-slate-800"><span>{label}</span><strong>{value === true ? 'Yes' : value === false ? 'No' : 'Not returned'}</strong></div>; }
function AuditPanel({ events }) { return <section className="rounded-xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-950"><h2 className="font-semibold">Audit events</h2>{events?.length ? <ul className="mt-3 space-y-2 text-sm">{events.map((event, index) => <li key={`${event.id ?? 'event'}-${index}`} className="flex justify-between gap-3"><span>{event.action ?? 'Event'}</span><span className="text-slate-500">{event.timestamp ?? ''}</span></li>)}</ul> : <p className="mt-3 text-sm text-slate-500">Audit events are stored by the backend but were not included in this response.</p>}</section>; }

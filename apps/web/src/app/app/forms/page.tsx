'use client';

import Link from 'next/link';
import { FileText } from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';
import { OcrStatus } from '@/components/documents/ocr-status';
import { PrivacyStatus } from '@/components/documents/privacy-status';
import { useAuth } from '@/contexts/auth-context';
import { listDocuments, type DocumentRecord } from '@/services/documents/upload-api';

export default function FormsPage() {
  const { firebaseUser } = useAuth();
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const refresh = useCallback(async () => {
    if (firebaseUser) setDocuments(await listDocuments(await firebaseUser.getIdToken()));
  }, [firebaseUser]);
  useEffect(() => {
    void refresh().catch(() => undefined);
  }, [refresh]);
  return (
    <section className="mx-auto max-w-4xl">
      <h1 className="text-3xl font-semibold">My Forms</h1>
      <p className="mt-2 text-slate-600 dark:text-slate-300">
        Uploaded documents and OCR progress.
      </p>
      {documents.length === 0 ? (
        <p className="mt-8 text-sm text-slate-500">No documents uploaded yet.</p>
      ) : (
        <ul className="mt-8 divide-y divide-slate-200 rounded-xl border border-slate-200 bg-white dark:divide-slate-800 dark:border-slate-800 dark:bg-slate-950">
          {documents.map((document) => (
            <li key={document.documentId} className="flex items-center gap-3 p-4">
              <FileText className="h-5 w-5 text-sky-700 dark:text-sky-300" />
              <div className="min-w-0 flex-1">
                <p className="truncate font-medium">{document.originalFilename}</p>
                <p className="mt-1 text-xs text-slate-500">
                  {new Date(document.uploadedAt).toLocaleString()}
                </p>
              </div>
              <div className="flex flex-col items-end gap-2">
                <OcrStatus document={document} />
                {document.ocrStatus === 'completed' && <PrivacyStatus document={document} />}
                <Link
                  className="text-xs font-medium text-sky-700 hover:underline dark:text-sky-300"
                  href={`/app/forms/${document.documentId}/privacy`}
                >
                  Privacy details
                </Link>
                {document.privacyStatus === 'completed' && (
                  <Link
                    className="text-xs font-medium text-sky-700 hover:underline dark:text-sky-300"
                    href={`/app/forms/${document.documentId}/understanding`}
                  >
                    Structured document
                  </Link>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

'use client';

import { FileText } from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';
import { useAuth } from '@/contexts/auth-context';
import { listDocuments, type DocumentRecord } from '@/services/documents/upload-api';
import { OcrStatus } from '@/components/documents/ocr-status';

export function RecentUploads() {
  const { firebaseUser } = useAuth();
  const [uploads, setUploads] = useState<DocumentRecord[]>([]);
  const refresh = useCallback(async () => {
    if (firebaseUser) setUploads(await listDocuments(await firebaseUser.getIdToken(), 5));
  }, [firebaseUser]);
  useEffect(() => {
    void refresh().catch(() => undefined);
  }, [refresh]);
  return (
    <section className="mt-10">
      <h2 className="text-lg font-semibold">Recent Uploads</h2>
      {uploads.length === 0 ? (
        <p className="mt-3 text-sm text-slate-500">Your uploaded documents will appear here.</p>
      ) : (
        <ul className="mt-3 divide-y divide-slate-200 rounded-xl border border-slate-200 bg-white dark:divide-slate-800 dark:border-slate-800 dark:bg-slate-950">
          {uploads.map((upload) => (
            <li key={upload.documentId} className="flex items-center gap-3 p-4">
              <FileText className="h-5 w-5 text-sky-700 dark:text-sky-300" />
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium">{upload.originalFilename}</p>
                <p className="mt-1 text-xs text-slate-500">
                  {new Date(upload.uploadedAt).toLocaleString()}
                </p>
              </div>
              <OcrStatus document={upload} />
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

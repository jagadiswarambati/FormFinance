'use client';

/* eslint-disable @next/next/no-img-element */
import { FileImage, FileText, UploadCloud, X } from 'lucide-react';
import { useCallback, useEffect, useRef, useState } from 'react';
import { useAuth } from '@/contexts/auth-context';
import { Button } from '@/components/ui/button';
import {
  completeUpload,
  createUploadIntent,
  listDocuments,
  startOcr,
  uploadToTarget,
  type DocumentRecord,
} from '@/services/documents/upload-api';
import { OcrStatus } from '@/components/documents/ocr-status';

const maximumBytes = 10 * 1024 * 1024;
const allowedTypes = new Set(['application/pdf', 'image/png', 'image/jpeg']);
const allowedExtensions = new Set(['.pdf', '.png', '.jpg', '.jpeg']);

function validate(file: File): string | null {
  const extension = `.${file.name.split('.').pop()?.toLowerCase() ?? ''}`;
  if (!allowedExtensions.has(extension)) return 'Choose a PDF, PNG, JPG, or JPEG file.';
  if (!allowedTypes.has(file.type)) return 'Choose a PDF, PNG, JPG, or JPEG file.';
  if (file.size > maximumBytes) return 'Files must not exceed 10 MB.';
  return null;
}

function formatBytes(size: number): string {
  return `${(size / 1024 / 1024).toFixed(size < 1024 * 1024 ? 1 : 2)} MB`;
}

export function UploadWorkspace() {
  const { firebaseUser } = useAuth();
  const fileInput = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploads, setUploads] = useState<DocumentRecord[]>([]);

  const refreshUploads = useCallback(async () => {
    if (firebaseUser) setUploads(await listDocuments(await firebaseUser.getIdToken()));
  }, [firebaseUser]);
  useEffect(() => {
    void refreshUploads().catch(() => undefined);
  }, [refreshUploads]);
  useEffect(
    () => () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    },
    [previewUrl],
  );

  const selectFile = (nextFile: File) => {
    const validationError = validate(nextFile);
    setError(validationError);
    if (validationError) return;
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setFile(nextFile);
    setPreviewUrl(nextFile.type.startsWith('image/') ? URL.createObjectURL(nextFile) : null);
  };

  const upload = async () => {
    if (!file || !firebaseUser) return;
    setIsUploading(true);
    setError(null);
    try {
      const idToken = await firebaseUser.getIdToken();
      const intent = await createUploadIntent(file, idToken);
      await uploadToTarget(file, intent.uploadUrl);
      await completeUpload(intent.documentId, idToken);
      setFile(null);
      if (previewUrl) URL.revokeObjectURL(previewUrl);
      setPreviewUrl(null);
      await refreshUploads();
    } catch (uploadError) {
      setError(
        uploadError instanceof Error ? uploadError.message : 'Upload failed. Please try again.',
      );
    } finally {
      setIsUploading(false);
    }
  };

  const requestOcr = async (documentId: string) => {
    if (!firebaseUser) return;
    try {
      await startOcr(documentId, await firebaseUser.getIdToken());
      await refreshUploads();
    } catch (ocrError) {
      setError(ocrError instanceof Error ? ocrError.message : 'OCR could not be started.');
    }
  };

  return (
    <section className="mx-auto max-w-4xl">
      <div>
        <h1 className="text-3xl font-semibold">Upload a document</h1>
        <p className="mt-2 text-slate-600 dark:text-slate-300">
          Add a PDF or image to start a FormWise workspace.
        </p>
      </div>
      <div
        className="mt-8 rounded-2xl border border-dashed border-slate-300 bg-white p-6 dark:border-slate-700 dark:bg-slate-950 sm:p-10"
        role="region"
        aria-label="Document upload area"
        onDragOver={(event) => event.preventDefault()}
        onDrop={(event) => {
          event.preventDefault();
          const dropped = event.dataTransfer.files.item(0);
          if (dropped) selectFile(dropped);
        }}
      >
        <input
          ref={fileInput}
          type="file"
          className="sr-only"
          aria-label="Choose a document to upload"
          accept="application/pdf,image/png,image/jpeg"
          onChange={(event) => {
            const selected = event.target.files?.item(0);
            if (selected) selectFile(selected);
          }}
        />
        {file ? (
          <div className="flex flex-col gap-6 sm:flex-row sm:items-center">
            <div className="grid h-24 w-24 shrink-0 place-items-center overflow-hidden rounded-xl bg-slate-100 dark:bg-slate-800">
              {previewUrl ? (
                <img
                  src={previewUrl}
                  alt="Selected file preview"
                  className="h-full w-full object-cover"
                />
              ) : (
                <FileText className="h-10 w-10 text-red-600" />
              )}
            </div>
            <div className="min-w-0 flex-1">
              <h2 className="truncate font-semibold">{file.name}</h2>
              <p className="mt-1 text-sm text-slate-500">
                {file.type === 'application/pdf' ? 'PDF document' : 'Image'} ·{' '}
                {formatBytes(file.size)}
              </p>
              <div className="mt-4 flex flex-wrap gap-3">
                <Button
                  onClick={() => void upload()}
                  disabled={isUploading}
                  aria-busy={isUploading}
                >
                  {isUploading ? 'Uploading…' : 'Upload document'}
                </Button>
                <Button
                  variant="outline"
                  onClick={() => {
                    setFile(null);
                    if (previewUrl) URL.revokeObjectURL(previewUrl);
                    setPreviewUrl(null);
                  }}
                >
                  <X className="mr-2 h-4 w-4" />
                  Cancel
                </Button>
              </div>
            </div>
          </div>
        ) : (
          <div className="text-center">
            <UploadCloud className="mx-auto h-12 w-12 text-sky-700 dark:text-sky-300" />
            <h2 className="mt-4 text-lg font-semibold">Drag and drop your document here</h2>
            <p className="mt-2 text-sm text-slate-500">PDF, PNG, JPG, or JPEG · Maximum 10 MB</p>
            <Button className="mt-6" onClick={() => fileInput.current?.click()}>
              Browse files
            </Button>
          </div>
        )}
        {error && (
          <p role="alert" className="mt-5 text-sm text-rose-800 dark:text-rose-200">
            {error}
          </p>
        )}
      </div>
      <UploadList uploads={uploads} onStartOcr={requestOcr} />
    </section>
  );
}

function UploadList({
  uploads,
  onStartOcr,
}: Readonly<{ uploads: DocumentRecord[]; onStartOcr(documentId: string): Promise<void> }>) {
  return (
    <section className="mt-10">
      <h2 className="text-lg font-semibold">Your uploads</h2>
      {uploads.length === 0 ? (
        <p className="mt-3 text-sm text-slate-500">No uploads yet.</p>
      ) : (
        <ul className="mt-3 divide-y divide-slate-200 rounded-xl border border-slate-200 bg-white dark:divide-slate-800 dark:border-slate-800 dark:bg-slate-950">
          {uploads.map((upload) => (
            <li key={upload.documentId} className="flex items-center gap-3 p-4">
              <FileImage className="h-5 w-5 text-sky-700 dark:text-sky-300" />
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium">{upload.originalFilename}</p>
                <p className="mt-1 text-xs text-slate-500">
                  {new Date(upload.uploadedAt).toLocaleString()}
                </p>
              </div>
              <OcrStatus document={upload} />
              {upload.ocrStatus === 'not_started' && (
                <Button
                  variant="outline"
                  onClick={() => void onStartOcr(upload.documentId)}
                  aria-label={`Start OCR for ${upload.originalFilename}`}
                >
                  Start OCR
                </Button>
              )}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

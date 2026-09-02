import { cn } from '@/lib/utils';
import type { DocumentRecord } from '@/services/documents/upload-api';

const labels: Record<DocumentRecord['ocrStatus'], string> = {
  not_started: 'Uploaded',
  processing: 'Processing OCR',
  completed: 'OCR completed',
  failed: 'OCR failed',
};
const styles: Record<DocumentRecord['ocrStatus'], string> = {
  not_started: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-200',
  processing: 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-200',
  completed: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-200',
  failed: 'bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-200',
};

export function OcrStatus({ document }: Readonly<{ document: DocumentRecord }>) {
  return (
    <span className={cn('rounded-full px-2 py-1 text-xs font-medium', styles[document.ocrStatus])}>
      {labels[document.ocrStatus]}
    </span>
  );
}

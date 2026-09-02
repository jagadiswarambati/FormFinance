'use client';

import { useParams } from 'next/navigation';
import { useRouter } from 'next/navigation';
import { useCallback, useEffect, useState } from 'react';
import { StructuredDocumentViewer } from '@/components/documents/structured-document-viewer';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/contexts/auth-context';
import {
  getStructuredDocument,
  understandDocument,
  type StructuredDocument,
} from '@/services/documents/upload-api';
import { createConversation } from '@/services/conversations/conversation-api';

export default function UnderstandingPage() {
  const { documentId } = useParams<{ documentId: string }>();
  const router = useRouter();
  const { firebaseUser } = useAuth();
  const [document, setDocument] = useState<StructuredDocument | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const load = useCallback(async () => {
    if (!firebaseUser) return;
    try {
      setDocument(await getStructuredDocument(documentId, await firebaseUser.getIdToken()));
    } catch {
      setDocument(null);
    } finally {
      setLoading(false);
    }
  }, [documentId, firebaseUser]);
  useEffect(() => {
    void load();
  }, [load]);
  const begin = async () => {
    if (!firebaseUser) return;
    setError(null);
    try {
      setDocument(await understandDocument(documentId, await firebaseUser.getIdToken()));
    } catch (cause) {
      setError(
        cause instanceof Error ? cause.message : 'Document understanding could not be completed.',
      );
    }
  };
  const startConversation = async () => {
    if (!firebaseUser) return;
    setError(null);
    try {
      const conversation = await createConversation(documentId, await firebaseUser.getIdToken());
      router.push(`/app/conversations/${conversation.id}`);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Conversation could not be created.');
    }
  };
  return (
    <section className="mx-auto max-w-4xl">
      <h1 className="text-3xl font-semibold">Structured document</h1>
      <p className="mt-2 text-slate-600 dark:text-slate-300">
        A deterministic view created only from protected text.
      </p>
      {loading ? (
        <p className="mt-8 text-sm text-slate-500">Loading structured document…</p>
      ) : document ? (
        <div className="mt-8">
          {error && <p className="mb-3 text-sm text-rose-700 dark:text-rose-300">{error}</p>}
          <Button className="mb-5" onClick={() => void startConversation()}>
            Start conversation
          </Button>
          <Button
            className="mb-5 ml-2"
            variant="outline"
            onClick={() => router.push(`/app/forms/${documentId}/assignments`)}
          >
            Review field assignments
          </Button>
          <StructuredDocumentViewer document={document} />
        </div>
      ) : (
        <div className="mt-8 rounded-xl border border-slate-200 p-6 dark:border-slate-800">
          <p className="text-sm text-slate-600 dark:text-slate-300">
            Privacy processing must be complete before understanding can begin.
          </p>
          {error && <p className="mt-3 text-sm text-rose-700 dark:text-rose-300">{error}</p>}
          <Button className="mt-5" onClick={() => void begin()}>
            Create structured document
          </Button>
        </div>
      )}
    </section>
  );
}

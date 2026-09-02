'use client';

import { useParams } from 'next/navigation';
import { useCallback, useEffect, useState } from 'react';
import { ConversationView } from '@/components/conversations/conversation-view';
import { DeleteConversationAction } from '@/components/conversations/delete-conversation-action';
import { PrivacyDashboard } from '@/components/conversations/privacy-dashboard';
import { useAuth } from '@/contexts/auth-context';
import {
  deleteConversation,
  getConversation,
  getPrivacyAuditEvents,
  getPrivacySummary,
  sendConversationMessage,
  type ConversationDetail,
  type PrivacyAuditEvent,
  type PrivacySummary,
} from '@/services/conversations/conversation-api';

export default function ConversationPage() {
  const { conversationId } = useParams<{ conversationId: string }>();
  const { firebaseUser } = useAuth();
  const [conversation, setConversation] = useState<ConversationDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [privacySummary, setPrivacySummary] = useState<PrivacySummary | null>(null);
  const [privacyEvents, setPrivacyEvents] = useState<PrivacyAuditEvent[]>([]);
  const [privacyLoading, setPrivacyLoading] = useState(true);
  const [privacyError, setPrivacyError] = useState<string | null>(null);
  const [deletionQueued, setDeletionQueued] = useState(false);
  const load = useCallback(async () => {
    if (!firebaseUser) return;
    try {
      setConversation(await getConversation(conversationId, await firebaseUser.getIdToken()));
    } catch (cause) {
      if (cause instanceof Error && cause.message === 'Conversation was not found.') {
        setError(
          'This conversation is no longer available. Its access may have been revoked or deletion may already have completed.',
        );
      } else {
        setError(cause instanceof Error ? cause.message : 'Conversation could not be loaded.');
      }
    }
  }, [conversationId, firebaseUser]);
  useEffect(() => {
    void load();
  }, [load]);
  useEffect(() => {
    if (!firebaseUser) return;
    const loadPrivacyDashboard = async () => {
      setPrivacyLoading(true);
      setPrivacyError(null);
      try {
        const token = await firebaseUser.getIdToken();
        const [summary, events] = await Promise.all([
          getPrivacySummary(conversationId, token),
          getPrivacyAuditEvents(conversationId, token),
        ]);
        setPrivacySummary(summary);
        setPrivacyEvents(events);
      } catch (cause) {
        setPrivacyError(
          cause instanceof Error ? cause.message : 'Privacy details could not be loaded.',
        );
      } finally {
        setPrivacyLoading(false);
      }
    };
    void loadPrivacyDashboard();
  }, [conversationId, firebaseUser]);
  const send = async (message: string) => {
    if (!firebaseUser) return;
    setError(null);
    try {
      await sendConversationMessage(conversationId, message, await firebaseUser.getIdToken());
      await load();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Message could not be sent.');
    }
  };
  const deleteCurrentConversation = async () => {
    if (!firebaseUser) throw new Error('You must be signed in to delete a conversation.');
    await deleteConversation(conversationId, await firebaseUser.getIdToken());
  };
  return (
    <section className="mx-auto max-w-4xl">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold">Document conversation</h1>
          <p className="mt-2 text-slate-600 dark:text-slate-300">
            Answers are generated from the protected structured document only.
          </p>
        </div>
        {conversation && !deletionQueued ? (
          <DeleteConversationAction
            onDelete={deleteCurrentConversation}
            onQueued={() => setDeletionQueued(true)}
          />
        ) : null}
      </div>
      {error && (
        <p className="mt-6 text-sm text-rose-800 dark:text-rose-200" role="alert">
          {error}
        </p>
      )}
      {deletionQueued ? (
        <section
          className="mt-8 rounded-xl border border-amber-200 bg-amber-50 p-6 dark:border-amber-900 dark:bg-amber-950/30"
          aria-live="polite"
        >
          <h2 className="text-lg font-semibold">Access revoked; deletion queued</h2>
          <p className="mt-2 text-sm text-slate-700 dark:text-slate-200">
            This conversation can no longer be accessed. Its associated data is queued for secure
            deletion. Physical deletion completes asynchronously, and no completion status is
            currently available here.
          </p>
        </section>
      ) : conversation ? (
        <>
          <PrivacyDashboard
            summary={privacySummary}
            events={privacyEvents}
            loading={privacyLoading}
            error={privacyError}
          />
          <ConversationView messages={conversation.messages} onSend={send} />
        </>
      ) : (
        !error && (
          <p className="mt-8 text-sm text-slate-600 dark:text-slate-300" role="status">
            Loading conversation…
          </p>
        )
      )}
    </section>
  );
}

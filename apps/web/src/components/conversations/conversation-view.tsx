'use client';

import { FormEvent, useState } from 'react';
import { Button } from '@/components/ui/button';
import type { ConversationMessage } from '@/services/conversations/conversation-api';

export function ConversationView({
  messages,
  onSend,
}: {
  messages: ConversationMessage[];
  onSend: (message: string) => Promise<void>;
}) {
  const [message, setMessage] = useState('');
  const [sending, setSending] = useState(false);
  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!message.trim() || sending) return;
    setSending(true);
    try {
      await onSend(message.trim());
      setMessage('');
    } finally {
      setSending(false);
    }
  };
  return (
    <div className="mt-8">
      <div className="space-y-4" role="log" aria-live="polite" aria-label="Conversation messages">
        {messages.map((item) => (
          <article
            key={item.id}
            className={`max-w-2xl rounded-xl p-4 text-sm ${item.role === 'user' ? 'ml-auto bg-sky-700 text-white' : 'bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800'}`}
          >
            <p className="sr-only">{item.role === 'user' ? 'You' : 'FormWise AI'}</p>
            <p className="whitespace-pre-wrap">{item.safeContent}</p>
          </article>
        ))}
      </div>
      <form className="mt-6 flex gap-2" onSubmit={(event) => void submit(event)}>
        <label className="sr-only" htmlFor="conversation-message">
          Ask about this structured document
        </label>
        <input
          id="conversation-message"
          value={message}
          onChange={(event) => setMessage(event.target.value)}
          maxLength={4000}
          className="h-10 min-w-0 flex-1 rounded-lg border border-slate-300 bg-white px-3 text-sm dark:border-slate-700 dark:bg-slate-950"
          placeholder="Ask about this structured document"
        />
        <Button disabled={sending} aria-busy={sending}>
          {sending ? 'Thinking…' : 'Send'}
        </Button>
      </form>
    </div>
  );
}

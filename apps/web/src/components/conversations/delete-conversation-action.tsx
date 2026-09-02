'use client';

import { useEffect, useRef, useState } from 'react';
import { Button } from '@/components/ui/button';

interface DeleteConversationActionProps {
  onDelete: () => Promise<void>;
  onQueued: () => void;
}

export function DeleteConversationAction({
  onDelete,
  onQueued,
}: Readonly<DeleteConversationActionProps>) {
  const [open, setOpen] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const dialogRef = useRef<HTMLElement>(null);
  const wasOpen = useRef(false);

  useEffect(() => {
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && !deleting) setOpen(false);
    };
    window.addEventListener('keydown', closeOnEscape);
    return () => window.removeEventListener('keydown', closeOnEscape);
  }, [deleting]);

  useEffect(() => {
    if (open) {
      dialogRef.current?.focus();
    } else if (wasOpen.current) {
      triggerRef.current?.focus();
    }
    wasOpen.current = open;
  }, [open]);

  const confirm = async () => {
    setDeleting(true);
    setError(null);
    try {
      await onDelete();
      setOpen(false);
      onQueued();
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : 'The conversation could not be queued for deletion.',
      );
    } finally {
      setDeleting(false);
    }
  };

  return (
    <>
      <Button
        ref={triggerRef}
        type="button"
        variant="outline"
        className="border-rose-300 text-rose-700 hover:bg-rose-50 dark:border-rose-900 dark:text-rose-300 dark:hover:bg-rose-950"
        onClick={() => {
          setError(null);
          setOpen(true);
        }}
      >
        Delete conversation
      </Button>
      {open ? (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 p-4"
          role="presentation"
          onMouseDown={() => {
            if (!deleting) setOpen(false);
          }}
        >
          <section
            ref={dialogRef}
            tabIndex={-1}
            role="dialog"
            aria-modal="true"
            aria-labelledby="delete-conversation-title"
            aria-describedby="delete-conversation-description"
            className="w-full max-w-md rounded-xl bg-white p-6 shadow-xl dark:bg-slate-950"
            onMouseDown={(event) => event.stopPropagation()}
            onKeyDown={(event) => {
              if (event.key !== 'Tab') return;
              const focusable = Array.from(
                event.currentTarget.querySelectorAll<HTMLElement>(
                  'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled])',
                ),
              );
              if (focusable.length === 0) return;
              const first = focusable[0];
              const last = focusable[focusable.length - 1];
              if (event.shiftKey && document.activeElement === first) {
                event.preventDefault();
                last.focus();
              } else if (!event.shiftKey && document.activeElement === last) {
                event.preventDefault();
                first.focus();
              }
            }}
          >
            <h2 id="delete-conversation-title" className="text-lg font-semibold">
              Delete this conversation?
            </h2>
            <p
              id="delete-conversation-description"
              className="mt-3 text-sm text-slate-600 dark:text-slate-300"
            >
              Access will be revoked immediately. The conversation and its associated artifacts will
              be queued for secure deletion; this does not mean physical deletion is immediate.
            </p>
            {error ? (
              <p className="mt-4 text-sm text-rose-700 dark:text-rose-300" role="alert">
                {error}
              </p>
            ) : null}
            <div className="mt-6 flex justify-end gap-3">
              <Button
                type="button"
                variant="outline"
                disabled={deleting}
                onClick={() => setOpen(false)}
              >
                Cancel
              </Button>
              <Button
                type="button"
                disabled={deleting}
                className="bg-rose-700 hover:bg-rose-800 dark:bg-rose-700 dark:text-white"
                onClick={() => void confirm()}
              >
                {deleting ? 'Queueing deletion…' : 'Revoke access and queue deletion'}
              </Button>
            </div>
          </section>
        </div>
      ) : null}
    </>
  );
}

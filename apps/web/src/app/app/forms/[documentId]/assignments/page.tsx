'use client';

import { useParams } from 'next/navigation';
import { useCallback, useEffect, useState } from 'react';
import { AssignmentReviewDashboard } from '@/components/assignments/assignment-review-dashboard';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/contexts/auth-context';
import {
  generateAssignments,
  getAssignments,
  updateAssignment,
  type FieldAssignment,
} from '@/services/assignments/assignment-api';

export default function AssignmentsPage() {
  const { documentId } = useParams<{ documentId: string }>();
  const { firebaseUser } = useAuth();
  const [assignments, setAssignments] = useState<FieldAssignment[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const load = useCallback(async () => {
    if (!firebaseUser) return;
    try {
      setAssignments(await getAssignments(documentId, await firebaseUser.getIdToken()));
    } catch {
      setAssignments(null);
    }
  }, [documentId, firebaseUser]);
  useEffect(() => {
    void load();
  }, [load]);
  const generate = async () => {
    if (!firebaseUser) return;
    setError(null);
    try {
      setAssignments(await generateAssignments(documentId, await firebaseUser.getIdToken()));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Assignments could not be generated.');
    }
  };
  const update = async (id: string, action: 'approve' | 'reject' | 'edit', value?: string) => {
    if (!firebaseUser) return;
    setError(null);
    try {
      await updateAssignment(id, action, await firebaseUser.getIdToken(), value);
      await load();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Assignment could not be updated.');
    }
  };
  return (
    <section className="mx-auto max-w-5xl">
      <h1 className="text-3xl font-semibold">Field review</h1>
      <p className="mt-2 text-slate-600 dark:text-slate-300">
        Review suggested values before any future rendering step. Protected fields remain
        manual-only.
      </p>
      {error && <p className="mt-4 text-sm text-rose-700 dark:text-rose-300">{error}</p>}
      {assignments?.length ? (
        <AssignmentReviewDashboard assignments={assignments} onUpdate={update} />
      ) : (
        <div className="mt-8 rounded-xl border border-slate-200 p-6 dark:border-slate-800">
          <p className="text-sm text-slate-600 dark:text-slate-300">
            No assignments have been generated for this structured document.
          </p>
          <Button className="mt-5" onClick={() => void generate()}>
            Generate assignments
          </Button>
        </div>
      )}
    </section>
  );
}

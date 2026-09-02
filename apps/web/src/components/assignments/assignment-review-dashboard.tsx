'use client';

import { useMemo, useState } from 'react';
import { Button } from '@/components/ui/button';
import type { FieldAssignment } from '@/services/assignments/assignment-api';

export function AssignmentReviewDashboard({
  assignments,
  onUpdate,
}: {
  assignments: FieldAssignment[];
  onUpdate: (id: string, action: 'approve' | 'reject' | 'edit', value?: string) => Promise<void>;
}) {
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState('all');
  const [editing, setEditing] = useState<string | null>(null);
  const [draft, setDraft] = useState('');
  const visible = useMemo(
    () =>
      assignments
        .filter(
          (item) =>
            (filter === 'all' ||
              item.status === filter ||
              (filter === 'review' && item.requiresReview)) &&
            item.label.toLowerCase().includes(search.toLowerCase()),
        )
        .sort((a, b) => a.label.localeCompare(b.label)),
    [assignments, filter, search],
  );
  const bulkApprove = async () => {
    for (const assignment of assignments.filter(
      (item) =>
        item.privacyTier === 'safe' && item.status === 'pending_review' && !item.requiresReview,
    ))
      await onUpdate(assignment.id, 'approve');
  };
  return (
    <div className="mt-8">
      <div className="flex flex-wrap gap-3">
        <label className="sr-only" htmlFor="assignment-search">
          Search fields
        </label>
        <input
          id="assignment-search"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          className="h-10 rounded-lg border border-slate-300 bg-white px-3 text-sm dark:border-slate-700 dark:bg-slate-950"
          placeholder="Search fields"
        />
        <label className="sr-only" htmlFor="assignment-filter">
          Filter fields
        </label>
        <select
          id="assignment-filter"
          value={filter}
          onChange={(event) => setFilter(event.target.value)}
          className="h-10 rounded-lg border border-slate-300 bg-white px-3 text-sm dark:border-slate-700 dark:bg-slate-950"
        >
          <option value="all">All fields</option>
          <option value="review">Needs review</option>
          <option value="missing">Missing</option>
          <option value="conflict">Conflicts</option>
          <option value="manual_only">Manual-only</option>
          <option value="approved">Approved</option>
        </select>
        <Button variant="outline" onClick={() => void bulkApprove()}>
          Bulk approve ready safe fields
        </Button>
      </div>
      <div className="mt-5 space-y-3" aria-live="polite">
        {visible.map((assignment) => (
          <article
            key={assignment.id}
            className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-950"
          >
            <div className="flex flex-wrap justify-between gap-2">
              <div>
                <h2 className="font-medium">{assignment.label}</h2>
                <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">
                  {assignment.value ?? assignment.question ?? 'No value suggested'}
                </p>
              </div>
              <span
                className="text-sm font-medium"
                aria-label={`Status: ${assignment.status.replaceAll('_', ' ')}`}
              >
                {assignment.status.replaceAll('_', ' ')}
              </span>
            </div>
            <p className="mt-3 text-xs text-slate-500">
              {Math.round(assignment.confidence * 100)}% · {assignment.source.replaceAll('_', ' ')}{' '}
              · {assignment.reason}
            </p>
            {assignment.privacyTier === 'safe' &&
              assignment.status !== 'approved' &&
              assignment.status !== 'rejected' && (
                <div className="mt-4 flex flex-wrap gap-2">
                  <Button
                    className="h-8 px-3"
                    onClick={() => void onUpdate(assignment.id, 'approve')}
                  >
                    Approve
                  </Button>
                  <Button
                    className="h-8 px-3"
                    variant="outline"
                    onClick={() => void onUpdate(assignment.id, 'reject')}
                  >
                    Reject
                  </Button>
                  <Button
                    className="h-8 px-3"
                    variant="ghost"
                    onClick={() => {
                      setEditing(assignment.id);
                      setDraft(assignment.value ?? '');
                    }}
                  >
                    Edit
                  </Button>
                </div>
              )}
            {editing === assignment.id && (
              <div className="mt-3 flex gap-2">
                <input
                  aria-label={`Edit value for ${assignment.label}`}
                  value={draft}
                  onChange={(event) => setDraft(event.target.value)}
                  className="h-9 flex-1 rounded-lg border border-slate-300 bg-white px-3 text-sm dark:border-slate-700 dark:bg-slate-900"
                />
                <Button
                  className="h-8 px-3"
                  onClick={() =>
                    void onUpdate(assignment.id, 'edit', draft).then(() => setEditing(null))
                  }
                >
                  Save
                </Button>
              </div>
            )}
          </article>
        ))}
      </div>
    </div>
  );
}

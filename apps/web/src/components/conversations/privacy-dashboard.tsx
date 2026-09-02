import type { PrivacyAuditEvent, PrivacySummary } from '@/services/conversations/conversation-api';

interface PrivacyDashboardProps {
  summary: PrivacySummary | null;
  events: PrivacyAuditEvent[];
  loading: boolean;
  error: string | null;
}

function RetentionStatement() {
  return (
    <p className="mt-6 border-t border-slate-200 pt-4 text-sm text-slate-600 dark:border-slate-800 dark:text-slate-300">
      FormWise AI retains up to five conversations per user. When a conversation is removed, access
      is revoked first and deletion is then processed asynchronously.
    </p>
  );
}

function CategoryList({ categories }: Readonly<{ categories: string[] }>) {
  if (categories.length === 0) {
    return <p className="text-sm text-slate-500 dark:text-slate-400">None recorded.</p>;
  }
  return (
    <ul className="flex flex-wrap gap-2" aria-label="Data categories">
      {categories.map((category) => (
        <li
          key={category}
          className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-700 dark:bg-slate-800 dark:text-slate-200"
        >
          {category}
        </li>
      ))}
    </ul>
  );
}

export function PrivacyDashboard({
  summary,
  events,
  loading,
  error,
}: Readonly<PrivacyDashboardProps>) {
  if (loading) {
    return (
      <section
        className="mt-8 rounded-xl border border-slate-200 p-6 dark:border-slate-800"
        aria-busy="true"
        aria-live="polite"
      >
        <h2 className="text-lg font-semibold">Privacy details</h2>
        <p className="mt-3 text-sm text-slate-500 dark:text-slate-400">Loading privacy summary…</p>
      </section>
    );
  }

  if (error) {
    return (
      <section
        className="mt-8 rounded-xl border border-rose-200 p-6 dark:border-rose-900"
        role="alert"
      >
        <h2 className="text-lg font-semibold">Privacy details</h2>
        <p className="mt-3 text-sm text-rose-800 dark:text-rose-200">{error}</p>
      </section>
    );
  }

  if (summary === null) {
    return (
      <section className="mt-8 rounded-xl border border-slate-200 p-6 dark:border-slate-800">
        <h2 className="text-lg font-semibold">Privacy details</h2>
        <p className="mt-3 text-sm text-slate-600 dark:text-slate-300">
          A privacy summary is not available for this conversation yet.
        </p>
      </section>
    );
  }

  const details = [
    ['Policy version', summary.policyVersion],
    ['Provider', summary.providerId],
    ['Processing mode', summary.processingMode],
    ['Safe fields', String(summary.safeFieldCount)],
    ['Restricted fields', String(summary.restrictedFieldCount)],
    ['Sensitive fields', String(summary.sensitiveFieldCount)],
    ['Last evaluated', new Date(summary.lastEvaluatedAt).toISOString()],
    ['Explanation locale', summary.explanationLocale],
  ] as const;

  return (
    <section className="mt-8 rounded-xl border border-slate-200 p-6 dark:border-slate-800">
      <h2 className="text-lg font-semibold">Privacy details</h2>
      <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">
        This summary contains policy metadata only and never displays protected values.
      </p>

      <dl className="mt-6 grid gap-4 sm:grid-cols-2">
        {details.map(([label, value]) => (
          <div key={label}>
            <dt className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</dt>
            <dd className="mt-1 text-sm text-slate-900 dark:text-slate-100">{value}</dd>
          </div>
        ))}
      </dl>

      <div className="mt-6 grid gap-6 sm:grid-cols-2">
        <div>
          <h3 className="text-sm font-semibold">AI-visible data categories</h3>
          <div className="mt-3">
            <CategoryList categories={summary.aiDataCategories} />
          </div>
        </div>
        <div>
          <h3 className="text-sm font-semibold">Excluded data categories</h3>
          <div className="mt-3">
            <CategoryList categories={summary.excludedDataCategories} />
          </div>
        </div>
      </div>

      <div className="mt-8 border-t border-slate-200 pt-6 dark:border-slate-800">
        <h3 className="text-sm font-semibold">Privacy activity</h3>
        {events.length === 0 ? (
          <p className="mt-3 text-sm text-slate-500 dark:text-slate-400">
            No privacy events recorded.
          </p>
        ) : (
          <ol className="mt-4 space-y-3" aria-label="Privacy audit timeline">
            {events.map((event) => (
              <li key={event.eventId} className="border-l-2 border-sky-500 pl-4">
                <p className="text-sm font-medium">{event.eventType}</p>
                <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                  {new Date(event.timestamp).toISOString()} · {event.actorType} ·{' '}
                  {event.explanationKey}
                </p>
              </li>
            ))}
          </ol>
        )}
      </div>
      <RetentionStatement />
    </section>
  );
}

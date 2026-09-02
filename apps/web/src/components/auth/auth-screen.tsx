'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/auth-context';

export function AuthScreen() {
  const { error, isAuthenticated, isLoading, signInWithGoogle } = useAuth();
  const router = useRouter();
  useEffect(() => {
    if (isAuthenticated) router.replace('/app');
  }, [isAuthenticated, router]);
  if (isLoading)
    return (
      <main className="grid min-h-screen place-items-center text-sm text-slate-600">
        Checking your session…
      </main>
    );
  if (isAuthenticated)
    return (
      <main className="grid min-h-screen place-items-center text-sm text-slate-600">
        Opening your workspace…
      </main>
    );
  return (
    <main className="grid min-h-screen place-items-center bg-slate-50 p-6 dark:bg-slate-900">
      <section className="w-full max-w-md rounded-2xl bg-white p-8 shadow-sm ring-1 ring-slate-200 dark:bg-slate-950 dark:ring-slate-800">
        <div className="mb-6 flex items-center gap-3">
          <div className="grid h-10 w-10 place-items-center rounded-lg bg-slate-900 font-semibold text-white dark:bg-slate-100 dark:text-slate-900">
            F
          </div>
          <span className="font-semibold">FormWise AI</span>
        </div>
        <h1 className="text-3xl font-semibold tracking-tight">Forms, made simpler.</h1>
        <p className="mt-3 text-slate-600 dark:text-slate-300">
          A privacy-first guided experience for eligible form fields.
        </p>
        {error && (
          <p role="alert" className="mt-4 text-sm text-red-700">
            {error}
          </p>
        )}
        <button
          disabled={Boolean(error)}
          className="mt-8 w-full rounded-lg bg-slate-900 px-4 py-3 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-50 dark:bg-slate-100 dark:text-slate-900"
          onClick={() => void signInWithGoogle()}
        >
          Continue with Google
        </button>
      </section>
    </main>
  );
}

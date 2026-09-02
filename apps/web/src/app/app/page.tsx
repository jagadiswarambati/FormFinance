'use client';
import { FileText, ShieldCheck, Upload } from 'lucide-react';
import { RecentUploads } from '@/components/documents/recent-uploads';
import { useAuth } from '@/contexts/auth-context';
const cards = [
  { title: 'Upload', description: 'Add a document', icon: Upload },
  { title: 'My Forms', description: 'Coming soon', icon: FileText },
  { title: 'Privacy Status', description: 'Coming soon', icon: ShieldCheck },
];
export default function AppHomePage() {
  const { profile } = useAuth();
  const name = profile?.displayName ?? 'there';
  return (
    <section className="mx-auto max-w-6xl">
      <div className="flex items-center gap-4">
        <div className="grid h-14 w-14 place-items-center rounded-full bg-sky-100 text-lg font-semibold text-sky-800 dark:bg-sky-950 dark:text-sky-200">
          {name.slice(0, 1).toUpperCase()}
        </div>
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">Welcome, {name}</h1>
          <p className="mt-1 text-slate-600 dark:text-slate-300">{profile?.email}</p>
        </div>
      </div>
      <p className="mt-8 max-w-2xl text-slate-600 dark:text-slate-300">
        FormWise AI will guide you through eligible form fields while keeping privacy at the center
        of every step.
      </p>
      <h2 className="mt-10 text-lg font-semibold">Quick Actions</h2>
      <div className="mt-4 grid gap-4 md:grid-cols-3">
        {cards.map(({ description, icon: Icon, title }) => (
          <article
            key={title}
            className="rounded-xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-950"
          >
            <Icon className="h-5 w-5 text-sky-700 dark:text-sky-300" />
            <h3 className="mt-5 font-semibold">{title}</h3>
            <p className="mt-1 text-sm text-slate-500">{description}</p>
          </article>
        ))}
      </div>
      <RecentUploads />
    </section>
  );
}

import { Sparkles } from 'lucide-react';
export function ComingSoonPage({
  description,
  title,
}: Readonly<{ title: string; description: string }>) {
  return (
    <section className="grid min-h-[calc(100vh-9rem)] place-items-center">
      <div className="max-w-md text-center">
        <div className="mx-auto grid h-16 w-16 place-items-center rounded-2xl bg-sky-100 text-sky-700 dark:bg-sky-950 dark:text-sky-300">
          <Sparkles className="h-8 w-8" />
        </div>
        <h1 className="mt-6 text-3xl font-semibold">{title}</h1>
        <p className="mt-3 text-slate-600 dark:text-slate-300">{description}</p>
      </div>
    </section>
  );
}

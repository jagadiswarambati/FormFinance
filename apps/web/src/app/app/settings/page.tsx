'use client';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/contexts/auth-context';
import { useTheme } from '@/components/theme-provider';
export default function SettingsPage() {
  const { logout, profile } = useAuth();
  const { theme, toggleTheme } = useTheme();
  return (
    <section className="mx-auto max-w-2xl">
      <h1 className="text-3xl font-semibold">Settings</h1>
      <p className="mt-2 text-slate-600 dark:text-slate-300">
        Profile and preference controls are placeholders in this milestone.
      </p>
      <div className="mt-8 space-y-4">
        <section className="rounded-xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-950">
          <h2 className="font-semibold">Profile</h2>
          <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
            {profile?.displayName ?? 'FormWise user'} · {profile?.email}
          </p>
        </section>
        <section className="flex items-center justify-between rounded-xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-950">
          <div>
            <h2 className="font-semibold">Theme</h2>
            <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">
              {theme === 'dark' ? 'Dark' : 'Light'} mode
            </p>
          </div>
          <Button variant="outline" onClick={toggleTheme}>
            Toggle theme
          </Button>
        </section>
        <section className="rounded-xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-950">
          <h2 className="font-semibold">Language</h2>
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">English — coming soon</p>
        </section>
        <Button variant="outline" className="text-red-700" onClick={() => void logout()}>
          Logout
        </Button>
      </div>
    </section>
  );
}

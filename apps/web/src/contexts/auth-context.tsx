'use client';

import { createContext, useCallback, useContext, useMemo } from 'react';
import type { User } from 'firebase/auth';
import type { AuthenticatedUser } from '@/services/auth/auth-api';

interface AuthContextValue {
  firebaseUser: User | null;
  profile: AuthenticatedUser | null;
  isLoading: boolean;
  error: string | null;
  isAuthenticated: boolean;
  signInWithGoogle(): Promise<void>;
  logout(): Promise<void>;
  refreshProfile(): Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: Readonly<{ children: React.ReactNode }>) {
  const refreshProfile = useCallback(async () => undefined, []);
  const signInWithGoogle = useCallback(async () => undefined, []);
  const logout = useCallback(async () => undefined, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      firebaseUser: null,
      profile: null,
      isLoading: false,
      error: null,
      isAuthenticated: true,
      signInWithGoogle,
      logout,
      refreshProfile,
    }),
    [logout, refreshProfile, signInWithGoogle],
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider.');
  return context;
}

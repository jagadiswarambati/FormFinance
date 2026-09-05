'use client';

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import {
  onAuthStateChanged,
  signInWithPopup,
  signOut,
  type User,
} from 'firebase/auth';
import { fetchCurrentUser, type AuthenticatedUser } from '@/services/auth/auth-api';
import {
  getFirebaseAuth,
  getFirebaseConfigurationError,
  getGoogleAuthProvider,
} from '@/lib/firebase/client';
import { demoAuthEnabled } from '@/config/env';

/**
 * Minimal shape every consumer in this app actually uses off `firebaseUser`
 * (only `.getIdToken()`, verified against every call site in the codebase).
 * A real Firebase `User` satisfies this structurally, so components that
 * call `firebaseUser.getIdToken()` work unchanged in both auth modes.
 */
export interface AuthPrincipal {
  uid: string;
  email: string | null;
  displayName: string | null;
  getIdToken(): Promise<string>;
}

export type AuthMode = 'firebase' | 'demo' | 'unconfigured';

interface AuthContextValue {
  firebaseUser: AuthPrincipal | User | null;
  profile: AuthenticatedUser | null;
  isLoading: boolean;
  error: string | null;
  isAuthenticated: boolean;
  /** Which authentication strategy is active. Useful for UI copy/branching. */
  authMode: AuthMode;
  signInWithGoogle(): Promise<void>;
  logout(): Promise<void>;
  refreshProfile(): Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

const DEMO_UID_STORAGE_KEY = 'formfinance_demo_uid';
const DEMO_TOKEN_PREFIX = 'demo:';

function getOrCreateDemoUid(): string {
  if (typeof window === 'undefined') return 'demo-user';
  const existing = window.localStorage.getItem(DEMO_UID_STORAGE_KEY);
  if (existing) return existing;
  const generated = `demo-${typeof crypto !== 'undefined' && 'randomUUID' in crypto
    ? crypto.randomUUID()
    : Date.now().toString(36)
    }`;
  window.localStorage.setItem(DEMO_UID_STORAGE_KEY, generated);
  return generated;
}

function createDemoPrincipal(uid: string): AuthPrincipal {
  return {
    uid,
    email: `${uid}@demo.formfinance.local`,
    displayName: 'Demo User',
    // Backend recognizes this sentinel via the X-Demo-User-ID header path
    // (services/api/src/formwise_api/dependencies/authentication.py), only
    // when DEMO_AUTH_ENABLED=true on the backend. See lib/api-auth.ts.
    getIdToken: async () => `${DEMO_TOKEN_PREFIX}${uid}`,
  };
}

export function AuthProvider({ children }: Readonly<{ children: React.ReactNode }>) {
  const firebaseConfigError = useMemo(() => getFirebaseConfigurationError(), []);
  const authMode: AuthMode = useMemo(() => {
    if (demoAuthEnabled) return 'demo';
    if (firebaseConfigError === null) return 'firebase';
    return 'unconfigured';
  }, [firebaseConfigError]);

  const [firebaseUser, setFirebaseUser] = useState<AuthPrincipal | User | null>(null);
  const [profile, setProfile] = useState<AuthenticatedUser | null>(null);
  const [isLoading, setIsLoading] = useState(authMode === 'firebase');
  const [error, setError] = useState<string | null>(
    authMode === 'unconfigured'
      ? 'Sign-in is not configured. Set NEXT_PUBLIC_FIREBASE_* environment variables, or enable demo mode with DEMO_AUTH_ENABLED=true (backend) and NEXT_PUBLIC_DEMO_AUTH_ENABLED=true (frontend).'
      : null,
  );

  const loadProfile = useCallback(async (principal: AuthPrincipal | User) => {
    try {
      const idToken = await principal.getIdToken();
      const fetched = await fetchCurrentUser(idToken);
      setProfile(fetched);
    } catch {
      // The /me profile record is a convenience, not a requirement for the
      // settlement upload/processing flow, so a failure here is non-fatal.
      setProfile(null);
    }
  }, []);

  // Real Firebase mode: subscribe to actual sign-in state.
  useEffect(() => {
    if (authMode !== 'firebase') return undefined;
    let cancelled = false;
    let unsubscribe: (() => void) | undefined;

    getFirebaseAuth()
      .then((auth) => {
        if (cancelled) return;
        unsubscribe = onAuthStateChanged(auth, (user) => {
          setFirebaseUser(user);
          setIsLoading(false);
          if (user) void loadProfile(user);
          else setProfile(null);
        });
      })
      .catch((cause: unknown) => {
        if (cancelled) return;
        setError(cause instanceof Error ? cause.message : 'Firebase failed to initialize.');
        setIsLoading(false);
      });

    return () => {
      cancelled = true;
      unsubscribe?.();
    };
  }, [authMode, loadProfile]);

  // Demo mode: establish a stable local session immediately, no backend
  // credential exchange required. Gated entirely by NEXT_PUBLIC_DEMO_AUTH_ENABLED.
  useEffect(() => {
    if (authMode !== 'demo') return;
    const principal = createDemoPrincipal(getOrCreateDemoUid());
    setFirebaseUser(principal);
    setIsLoading(false);
    void loadProfile(principal);
  }, [authMode, loadProfile]);

  const signInWithGoogle = useCallback(async () => {
    if (authMode === 'firebase') {
      setError(null);
      setIsLoading(true);
      try {
        const auth = await getFirebaseAuth();
        await signInWithPopup(auth, getGoogleAuthProvider());
        // onAuthStateChanged above will populate firebaseUser/profile.
      } catch (cause) {
        setError(cause instanceof Error ? cause.message : 'Sign-in failed.');
        setIsLoading(false);
      }
      return;
    }
    if (authMode === 'demo') {
      const principal = createDemoPrincipal(getOrCreateDemoUid());
      setFirebaseUser(principal);
      void loadProfile(principal);
      return;
    }
    setError(
      'Sign-in is not configured. Set NEXT_PUBLIC_FIREBASE_* environment variables, or enable demo mode with DEMO_AUTH_ENABLED=true (backend) and NEXT_PUBLIC_DEMO_AUTH_ENABLED=true (frontend).',
    );
  }, [authMode, loadProfile]);

  const logout = useCallback(async () => {
    if (authMode === 'firebase') {
      const auth = await getFirebaseAuth();
      await signOut(auth);
      return;
    }
    setFirebaseUser(null);
    setProfile(null);
  }, [authMode]);

  const refreshProfile = useCallback(async () => {
    if (!firebaseUser) return;
    await loadProfile(firebaseUser);
  }, [firebaseUser, loadProfile]);

  const value = useMemo<AuthContextValue>(
    () => ({
      firebaseUser,
      profile,
      isLoading,
      error,
      isAuthenticated: firebaseUser !== null,
      authMode,
      signInWithGoogle,
      logout,
      refreshProfile,
    }),
    [firebaseUser, profile, isLoading, error, authMode, signInWithGoogle, logout, refreshProfile],
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider.');
  return context;
}

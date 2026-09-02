'use client';

import { onIdTokenChanged, signInWithPopup, signOut, type User } from 'firebase/auth';
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import {
  getFirebaseAuth,
  getFirebaseConfigurationError,
  getGoogleAuthProvider,
} from '@/lib/firebase/client';
import { fetchCurrentUser, type AuthenticatedUser } from '@/services/auth/auth-api';

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
  const [firebaseUser, setFirebaseUser] = useState<User | null>(null);
  const [profile, setProfile] = useState<AuthenticatedUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refreshProfile = useCallback(async () => {
    if (!firebaseUser) {
      setProfile(null);
      return;
    }
    setIsLoading(true);
    try {
      setProfile(await fetchCurrentUser(await firebaseUser.getIdToken()));
      setError(null);
    } catch (profileError) {
      setProfile(null);
      setError(
        profileError instanceof Error
          ? profileError.message
          : 'Your session could not be verified.',
      );
    } finally {
      setIsLoading(false);
    }
  }, [firebaseUser]);

  useEffect(() => {
    const configurationError = getFirebaseConfigurationError();
    if (configurationError) {
      setError(configurationError);
      setIsLoading(false);
      return;
    }
    let active = true;
    let unsubscribe: (() => void) | undefined;
    void getFirebaseAuth()
      .then((auth) => {
        unsubscribe = onIdTokenChanged(auth, async (nextFirebaseUser) => {
          if (!active) return;
          setFirebaseUser(nextFirebaseUser);
          if (!nextFirebaseUser) {
            setProfile(null);
            setError(null);
            setIsLoading(false);
            return;
          }
          setIsLoading(true);
          try {
            setProfile(await fetchCurrentUser(await nextFirebaseUser.getIdToken()));
            setError(null);
          } catch (profileError) {
            setProfile(null);
            setError(
              profileError instanceof Error
                ? profileError.message
                : 'Your session could not be verified.',
            );
          } finally {
            if (active) setIsLoading(false);
          }
        });
      })
      .catch((initializationError: unknown) => {
        if (!active) return;
        setError(
          initializationError instanceof Error
            ? initializationError.message
            : 'Firebase could not be initialized.',
        );
        setIsLoading(false);
      });
    return () => {
      active = false;
      unsubscribe?.();
    };
  }, []);

  const signInWithGoogle = useCallback(async () => {
    setError(null);
    try {
      await signInWithPopup(await getFirebaseAuth(), getGoogleAuthProvider());
    } catch {
      setError('Google sign-in was not completed. Please try again.');
    }
  }, []);

  const logout = useCallback(async () => {
    await signOut(await getFirebaseAuth());
    setFirebaseUser(null);
    setProfile(null);
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      firebaseUser,
      profile,
      isLoading,
      error,
      isAuthenticated: Boolean(profile),
      signInWithGoogle,
      logout,
      refreshProfile,
    }),
    [error, firebaseUser, isLoading, logout, profile, refreshProfile, signInWithGoogle],
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider.');
  return context;
}

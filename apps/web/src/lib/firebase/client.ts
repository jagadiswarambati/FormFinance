import {
  getApp,
  getApps,
  initializeApp,
  type FirebaseApp,
  type FirebaseOptions,
} from 'firebase/app';
import {
  browserLocalPersistence,
  getAuth,
  GoogleAuthProvider,
  setPersistence,
  type Auth,
} from 'firebase/auth';
import { firebaseEnvironment } from '@/config/env';

const requiredConfiguration = Object.entries({
  NEXT_PUBLIC_FIREBASE_API_KEY: firebaseEnvironment.apiKey,
  NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN: firebaseEnvironment.authDomain,
  NEXT_PUBLIC_FIREBASE_PROJECT_ID: firebaseEnvironment.projectId,
  NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID: firebaseEnvironment.messagingSenderId,
  NEXT_PUBLIC_FIREBASE_APP_ID: firebaseEnvironment.appId,
});

let firebaseApp: FirebaseApp | undefined;
let firebaseAuth: Auth | undefined;
let googleAuthProvider: GoogleAuthProvider | undefined;
let authInitialization: Promise<Auth> | undefined;

function isPlaceholder(value: string | undefined): boolean {
  return !value || value.startsWith('YOUR_FIREBASE_');
}

export function getFirebaseConfiguration(): FirebaseOptions {
  const missing = requiredConfiguration
    .filter(([, value]) => isPlaceholder(value))
    .map(([name]) => name);
  if (missing.length > 0) {
    throw new Error(
      `Firebase configuration is incomplete. Replace the placeholder or set: ${missing.join(', ')}.`,
    );
  }
  return firebaseEnvironment as FirebaseOptions;
}

export function getFirebaseConfigurationError(): string | null {
  try {
    getFirebaseConfiguration();
    return null;
  } catch (error) {
    return error instanceof Error ? error.message : 'Firebase configuration is incomplete.';
  }
}

export function getFirebaseApp(): FirebaseApp {
  firebaseApp ??= getApps().length > 0 ? getApp() : initializeApp(getFirebaseConfiguration());
  return firebaseApp;
}

export async function getFirebaseAuth(): Promise<Auth> {
  if (authInitialization) return authInitialization;
  firebaseAuth = getAuth(getFirebaseApp());
  authInitialization = setPersistence(firebaseAuth, browserLocalPersistence).then(
    () => firebaseAuth as Auth,
  );
  return authInitialization;
}

export function getGoogleAuthProvider(): GoogleAuthProvider {
  googleAuthProvider ??= new GoogleAuthProvider();
  return googleAuthProvider;
}

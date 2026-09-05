import { z } from 'zod';

/**
 * Docker Compose substitutes unset build args as empty strings, not undefined.
 * This helper treats empty strings as undefined so fallbacks work correctly.
 */
function emptyToUndefined(value: string | undefined): string | undefined {
  return value === '' ? undefined : value;
}

const schema = z.object({
  NEXT_PUBLIC_APP_URL: z.url(),
  NEXT_PUBLIC_API_BASE_URL: z.url(),
  NEXT_PUBLIC_FIREBASE_API_KEY: z.string().min(1).optional(),
  NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN: z.string().min(1).optional(),
  NEXT_PUBLIC_FIREBASE_PROJECT_ID: z.string().min(1).optional(),
  NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET: z.string().min(1).optional(),
  NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID: z.string().min(1).optional(),
  NEXT_PUBLIC_FIREBASE_APP_ID: z.string().min(1).optional(),
  NEXT_PUBLIC_DEMO_AUTH_ENABLED: z.string().optional(),
});

export const env = schema.parse({
  NEXT_PUBLIC_APP_URL: emptyToUndefined(process.env.NEXT_PUBLIC_APP_URL) ?? 'http://localhost:3000',
  NEXT_PUBLIC_API_BASE_URL: emptyToUndefined(process.env.NEXT_PUBLIC_API_BASE_URL) ?? 'http://localhost:8000/api/v1',
  NEXT_PUBLIC_FIREBASE_API_KEY: emptyToUndefined(process.env.NEXT_PUBLIC_FIREBASE_API_KEY),
  NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN: emptyToUndefined(process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN),
  NEXT_PUBLIC_FIREBASE_PROJECT_ID: emptyToUndefined(process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID),
  NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET: emptyToUndefined(process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET),
  NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID: emptyToUndefined(process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID),
  NEXT_PUBLIC_FIREBASE_APP_ID: emptyToUndefined(process.env.NEXT_PUBLIC_FIREBASE_APP_ID),
  NEXT_PUBLIC_DEMO_AUTH_ENABLED: emptyToUndefined(process.env.NEXT_PUBLIC_DEMO_AUTH_ENABLED),
});

/** True only when explicitly opted in. Must mirror the backend's DEMO_AUTH_ENABLED. */
export const demoAuthEnabled = env.NEXT_PUBLIC_DEMO_AUTH_ENABLED === 'true';

export const firebaseEnvironment = {
  apiKey: env.NEXT_PUBLIC_FIREBASE_API_KEY,
  authDomain: env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
  projectId: env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
  storageBucket: env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID,
  appId: env.NEXT_PUBLIC_FIREBASE_APP_ID,
};
/**
 * Every request to the backend needs an auth header. `useAuth().firebaseUser`
 * yields tokens from `getIdToken()` in two shapes depending on auth mode:
 *  - a real Firebase ID token (opaque JWT string) when Firebase is configured
 *  - a synthetic `demo:<uid>` token when running in demo-auth mode
 *
 * This is the single place that decides which HTTP header to send for a
 * given token, so every API service module stays agnostic to auth mode.
 * Keep this in sync with the backend's demo bypass in
 * services/api/src/formwise_api/dependencies/authentication.py.
 */

const DEMO_TOKEN_PREFIX = 'demo:';

export function isDemoToken(token: string): boolean {
  return token.startsWith(DEMO_TOKEN_PREFIX);
}

export function buildAuthHeaders(token: string): HeadersInit {
  if (isDemoToken(token)) {
    return { 'X-Demo-User-ID': token.slice(DEMO_TOKEN_PREFIX.length) };
  }
  return { Authorization: `Bearer ${token}` };
}

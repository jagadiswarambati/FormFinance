import { env } from '@/config/env';
export interface AuthenticatedUser {
  uid: string;
  displayName: string | null;
  email: string;
  photoURL: string | null;
  locale: string;
  status: string;
  createdAt: string;
  lastLogin: string;
}
export async function fetchCurrentUser(idToken: string): Promise<AuthenticatedUser> {
  if (!env.NEXT_PUBLIC_API_BASE_URL) {
    throw new Error('Backend authentication is not configured. Set NEXT_PUBLIC_API_BASE_URL.');
  }
  const response = await fetch(`${env.NEXT_PUBLIC_API_BASE_URL}/me`, {
    headers: { Authorization: `Bearer ${idToken}` },
    cache: 'no-store',
  });
  if (response.status === 401)
    throw new Error('Your session could not be verified. Please sign in again.');
  if (!response.ok) throw new Error('The authentication service is unavailable. Please try again.');
  return (await response.json()) as AuthenticatedUser;
}

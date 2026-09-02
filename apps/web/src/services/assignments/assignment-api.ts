import { env } from '@/config/env';

export interface FieldAssignment {
  id: string;
  documentId: string;
  fieldId: string;
  label: string;
  value: string | null;
  confidence: number;
  source: string;
  reason: string;
  evidence: Array<{ sourceId: string; description: string }>;
  requiresReview: boolean;
  status: 'pending_review' | 'approved' | 'rejected' | 'manual_only' | 'conflict' | 'missing';
  question: string | null;
  privacyTier: 'safe' | 'restricted' | 'sensitive';
  createdAt: string;
  updatedAt: string;
}

function headers(token: string): HeadersInit {
  return { Authorization: `Bearer ${token}` };
}
async function ensure(response: Response): Promise<void> {
  if (response.ok) return;
  const body = (await response.json().catch(() => null)) as { detail?: string } | null;
  throw new Error(body?.detail ?? 'The assignment request could not be completed.');
}

export async function generateAssignments(
  documentId: string,
  token: string,
): Promise<FieldAssignment[]> {
  const response = await fetch(
    `${env.NEXT_PUBLIC_API_BASE_URL}/documents/${documentId}/assignments/generate`,
    { method: 'POST', headers: headers(token) },
  );
  await ensure(response);
  return ((await response.json()) as { assignments: FieldAssignment[] }).assignments;
}
export async function getAssignments(
  documentId: string,
  token: string,
): Promise<FieldAssignment[]> {
  const response = await fetch(
    `${env.NEXT_PUBLIC_API_BASE_URL}/documents/${documentId}/assignments`,
    { headers: headers(token), cache: 'no-store' },
  );
  await ensure(response);
  return response.json() as Promise<FieldAssignment[]>;
}
export async function updateAssignment(
  id: string,
  action: 'approve' | 'reject' | 'edit',
  token: string,
  value?: string,
): Promise<FieldAssignment> {
  const response = await fetch(`${env.NEXT_PUBLIC_API_BASE_URL}/assignments/${id}`, {
    method: 'PATCH',
    headers: { ...headers(token), 'Content-Type': 'application/json' },
    body: JSON.stringify({ action, value }),
  });
  await ensure(response);
  return response.json() as Promise<FieldAssignment>;
}

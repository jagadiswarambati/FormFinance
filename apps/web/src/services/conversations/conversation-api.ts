import { env } from '@/config/env';

export interface ConversationMessage {
  id: string;
  conversationId: string;
  role: 'user' | 'assistant' | 'system' | 'tool';
  safeContent: string;
  fieldIds: string[];
  provider: string | null;
  tokenUsage: number | null;
  latencyMs: number | null;
  createdAt: string;
}

export interface Conversation {
  id: string;
  userId: string;
  documentId: string;
  status: string;
  locale: string;
  provider: string;
  createdAt: string;
  updatedAt: string;
  revokedAt: string | null;
}

export interface ConversationDetail extends Conversation {
  messages: ConversationMessage[];
}

export interface PrivacySummary {
  policyVersion: string;
  providerId: string;
  processingMode: string;
  safeFieldCount: number;
  restrictedFieldCount: number;
  sensitiveFieldCount: number;
  aiDataCategories: string[];
  excludedDataCategories: string[];
  lastEvaluatedAt: string;
  explanationLocale: string;
}

export interface PrivacyAuditEvent {
  eventId: string;
  conversationId: string;
  eventType: string;
  policyVersion: string;
  timestamp: string;
  providerId: string | null;
  processingMode: string | null;
  actorType: string;
  explanationKey: string;
}

function headers(token: string): HeadersInit {
  return { Authorization: `Bearer ${token}` };
}

async function ensure(response: Response): Promise<void> {
  if (response.ok) return;
  const body = (await response.json().catch(() => null)) as { detail?: string } | null;
  throw new Error(body?.detail ?? 'The conversation request could not be completed.');
}

export async function createConversation(documentId: string, token: string): Promise<Conversation> {
  const response = await fetch(`${env.NEXT_PUBLIC_API_BASE_URL}/conversations`, {
    method: 'POST',
    headers: { ...headers(token), 'Content-Type': 'application/json' },
    body: JSON.stringify({ documentId }),
  });
  await ensure(response);
  return response.json() as Promise<Conversation>;
}

export async function getConversation(
  conversationId: string,
  token: string,
): Promise<ConversationDetail> {
  const response = await fetch(`${env.NEXT_PUBLIC_API_BASE_URL}/conversations/${conversationId}`, {
    headers: headers(token),
    cache: 'no-store',
  });
  await ensure(response);
  return response.json() as Promise<ConversationDetail>;
}

export async function sendConversationMessage(
  conversationId: string,
  message: string,
  token: string,
): Promise<{ reply: string }> {
  const response = await fetch(
    `${env.NEXT_PUBLIC_API_BASE_URL}/conversations/${conversationId}/messages`,
    {
      method: 'POST',
      headers: { ...headers(token), 'Content-Type': 'application/json' },
      body: JSON.stringify({ message }),
    },
  );
  await ensure(response);
  return response.json() as Promise<{ reply: string }>;
}

export async function deleteConversation(conversationId: string, token: string): Promise<void> {
  const response = await fetch(`${env.NEXT_PUBLIC_API_BASE_URL}/conversations/${conversationId}`, {
    method: 'DELETE',
    headers: headers(token),
  });
  await ensure(response);
}

export async function getPrivacySummary(
  conversationId: string,
  token: string,
): Promise<PrivacySummary | null> {
  const response = await fetch(
    `${env.NEXT_PUBLIC_API_BASE_URL}/conversations/${conversationId}/privacy-summary`,
    { headers: headers(token), cache: 'no-store' },
  );
  if (response.status === 404) return null;
  await ensure(response);
  return response.json() as Promise<PrivacySummary>;
}

export async function getPrivacyAuditEvents(
  conversationId: string,
  token: string,
): Promise<PrivacyAuditEvent[]> {
  const response = await fetch(
    `${env.NEXT_PUBLIC_API_BASE_URL}/conversations/${conversationId}/privacy-events`,
    { headers: headers(token), cache: 'no-store' },
  );
  await ensure(response);
  return response.json() as Promise<PrivacyAuditEvent[]>;
}

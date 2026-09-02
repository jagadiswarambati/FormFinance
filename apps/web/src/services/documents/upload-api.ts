import { env } from '@/config/env';

export interface DocumentRecord {
  documentId: string;
  ownerUid: string;
  originalFilename: string;
  storedFilename: string;
  contentType: string;
  fileSize: number;
  uploadedAt: string;
  status: 'uploaded' | 'ocr_processing' | 'ocr_completed' | 'ocr_failed';
  ocrStatus: 'not_started' | 'processing' | 'completed' | 'failed';
  ocrProvider: string | null;
  ocrConfidence: number | null;
  textLength: number | null;
  privacyStatus:
    | 'not_started'
    | 'awaiting_consent'
    | 'completed'
    | 'blocked'
    | 'cancelled'
    | 'failed';
  privacyCompletedAt: string | null;
  privacyPolicyVersion: string | null;
  piiCategories: string[];
  redactedTextStorageKey: string | null;
  consentDecision: string | null;
}

export interface PrivacyReport {
  documentId: string;
  status: string;
  policyVersion: string;
  findings: Array<{
    category: string;
    count: number;
    action: 'ALLOW' | 'REDACT' | 'ASK_USER' | 'BLOCK';
  }>;
  piiCategories: string[];
  requiresConsent: boolean;
  consentDecision: string | null;
  protectedTextReady: boolean;
  completedAt: string | null;
}

export interface StructuredDocument {
  documentId: string;
  documentType: string;
  sections: Array<{ id: string; title: string; start: number; end: number; fieldIds: string[] }>;
  fields: Array<{
    id: string;
    label: string;
    value: string | null;
    normalizedValue: string | null;
    sectionId: string | null;
    confidence: number;
    required: boolean;
  }>;
  tables: Array<{
    id: string;
    sectionId: string | null;
    headers: string[];
    rows: string[][];
    confidence: number;
  }>;
  checkboxes: Array<{
    id: string;
    label: string;
    state: string;
    sectionId: string | null;
    confidence: number;
  }>;
  signatureStatus: string;
  missingFields: Array<{ fieldId: string; label: string; certainty: string; confidence: number }>;
  confidenceSummary: { overall: number; fields: number; tables: number; checkboxes: number };
  processingStatus: string;
  providerVersion: string;
  createdAt: string;
}

interface UploadIntent {
  documentId: string;
  uploadUrl: string;
  expiresAt: string;
}

function headers(idToken: string): HeadersInit {
  return { Authorization: `Bearer ${idToken}` };
}

async function ensureResponse(response: Response): Promise<void> {
  if (response.ok) return;
  const payload = (await response.json().catch(() => null)) as { detail?: string } | null;
  throw new Error(payload?.detail ?? 'The document request could not be completed.');
}

export async function createUploadIntent(file: File, idToken: string): Promise<UploadIntent> {
  const response = await fetch(`${env.NEXT_PUBLIC_API_BASE_URL}/documents/upload-intents`, {
    method: 'POST',
    headers: { ...headers(idToken), 'Content-Type': 'application/json' },
    body: JSON.stringify({
      originalFilename: file.name,
      contentType: file.type,
      fileSize: file.size,
    }),
  });
  await ensureResponse(response);
  return response.json() as Promise<UploadIntent>;
}

export async function uploadToTarget(file: File, uploadUrl: string): Promise<void> {
  const response = await fetch(uploadUrl, {
    method: 'PUT',
    headers: { 'Content-Type': file.type },
    body: file,
  });
  await ensureResponse(response);
}

export async function completeUpload(documentId: string, idToken: string): Promise<DocumentRecord> {
  const response = await fetch(`${env.NEXT_PUBLIC_API_BASE_URL}/documents/${documentId}/complete`, {
    method: 'POST',
    headers: headers(idToken),
  });
  await ensureResponse(response);
  return response.json() as Promise<DocumentRecord>;
}

export async function listDocuments(idToken: string, limit = 5): Promise<DocumentRecord[]> {
  const response = await fetch(`${env.NEXT_PUBLIC_API_BASE_URL}/documents?limit=${limit}`, {
    headers: headers(idToken),
    cache: 'no-store',
  });
  await ensureResponse(response);
  return response.json() as Promise<DocumentRecord[]>;
}

export async function startOcr(documentId: string, idToken: string): Promise<DocumentRecord> {
  const response = await fetch(`${env.NEXT_PUBLIC_API_BASE_URL}/documents/${documentId}/ocr`, {
    method: 'POST',
    headers: headers(idToken),
  });
  await ensureResponse(response);
  return response.json() as Promise<DocumentRecord>;
}

export async function scanPrivacy(documentId: string, idToken: string): Promise<PrivacyReport> {
  const response = await fetch(
    `${env.NEXT_PUBLIC_API_BASE_URL}/documents/${documentId}/privacy/scan`,
    {
      method: 'POST',
      headers: headers(idToken),
    },
  );
  await ensureResponse(response);
  return response.json() as Promise<PrivacyReport>;
}

export async function getPrivacyReport(
  documentId: string,
  idToken: string,
): Promise<PrivacyReport> {
  const response = await fetch(`${env.NEXT_PUBLIC_API_BASE_URL}/documents/${documentId}/privacy`, {
    headers: headers(idToken),
    cache: 'no-store',
  });
  await ensureResponse(response);
  return response.json() as Promise<PrivacyReport>;
}

export async function savePrivacyConsent(
  documentId: string,
  decision: 'continue_with_redaction' | 'continue_protected' | 'cancel',
  idToken: string,
): Promise<PrivacyReport> {
  const response = await fetch(
    `${env.NEXT_PUBLIC_API_BASE_URL}/documents/${documentId}/privacy/consent`,
    {
      method: 'POST',
      headers: { ...headers(idToken), 'Content-Type': 'application/json' },
      body: JSON.stringify({ decision }),
    },
  );
  await ensureResponse(response);
  return response.json() as Promise<PrivacyReport>;
}

export async function understandDocument(
  documentId: string,
  idToken: string,
): Promise<StructuredDocument> {
  const response = await fetch(
    `${env.NEXT_PUBLIC_API_BASE_URL}/documents/${documentId}/understand`,
    { method: 'POST', headers: headers(idToken) },
  );
  await ensureResponse(response);
  return response.json() as Promise<StructuredDocument>;
}

export async function getStructuredDocument(
  documentId: string,
  idToken: string,
): Promise<StructuredDocument> {
  const response = await fetch(
    `${env.NEXT_PUBLIC_API_BASE_URL}/documents/${documentId}/understanding`,
    { headers: headers(idToken), cache: 'no-store' },
  );
  await ensureResponse(response);
  return response.json() as Promise<StructuredDocument>;
}

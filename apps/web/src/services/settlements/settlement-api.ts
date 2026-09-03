import { env } from '@/config/env';

export interface SettlementDeduction {
  id: string;
  type: string;
  description: string;
  amount: number;
  referenceId?: string | null;
  referenceDate?: string | null;
  verificationStatus?: string;
  reason?: string;
}

export interface SettlementDecision {
  status: string;
  confidence: number;
  explanation: string;
  timestamp?: string;
}

export interface SettlementEvidence {
  evidenceFound?: boolean;
  amountMatch?: boolean | null;
  dateMatch?: boolean | null;
  referenceMatch?: boolean | null;
  confidence?: number;
  reasons?: string[];
}

export interface SettlementProcessingResult {
  settlementId: string;
  documentId: string;
  status: string;
  reference?: string | null;
  currency?: string;
  grossAmount: number;
  totalDeductions?: number;
  netAmount: number;
  deductions: SettlementDeduction[];
  verification?: Record<string, unknown>;
  evidence?: SettlementEvidence | null;
  decision: SettlementDecision;
  auditEvents?: Array<Record<string, unknown>>;
  processedAt: string;
}

async function ensureResponse(response: Response): Promise<void> {
  if (response.ok) return;
  const payload = (await response.json().catch(() => null)) as { detail?: string } | null;
  throw new Error(payload?.detail ?? 'Settlement processing could not be completed.');
}

export async function processSettlementDocument(
  documentId: string,
  evidenceDocumentIds: string[],
  idToken: string,
): Promise<SettlementProcessingResult> {
  const response = await fetch(`${env.NEXT_PUBLIC_API_BASE_URL}/settlements/process-document`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${idToken}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ documentId, evidenceDocumentIds }),
  });
  await ensureResponse(response);
  return response.json() as Promise<SettlementProcessingResult>;
}
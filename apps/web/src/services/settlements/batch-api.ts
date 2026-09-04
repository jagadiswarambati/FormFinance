import { env } from '@/config/env';
import { buildAuthHeaders } from '@/lib/api-auth';

export interface BatchMetrics {
  timestamp: string;
  totalRecords: number;
  processed: number;
  successfullyExtracted: number;
  totalSettlements: number;
  totalDeductions: number;
  approvedCount: number;
  flaggedCount: number;
  escalatedCount: number;
  processingFailedCount: number;
  verifiedDeductions: number;
  disputedDeductions: number;
  unverifiableDeductions: number;
  settlementApprovalRate: number;
  deductionVerificationRate: number;
  evidenceMatchRate: number;
  exceptionRate: number;
  extractionSuccessRate: number;
  agentInvestigations: number;
  agentSuccesses: number;
  agentFailures: number;
  exceptions: Array<Record<string, unknown>>;
  settlementResults: Array<Record<string, unknown>>;
}

export interface BatchSettlementSpec {
  source?: string;
  settlementDate: string;
  grossAmount: number;
  netAmount: number;
  currency?: string;
  ocrText?: string;
}

/**
 * The backend's BatchMetricsResponse (services/api/src/formwise_api/settlements/router.py)
 * declares no field aliases, so unlike most other settlement endpoints its JSON keys stay
 * snake_case. This raw shape is mapped into the camelCase BatchMetrics the rest of the
 * frontend expects.
 */
interface RawBatchMetricsResponse {
  timestamp: string;
  total_records: number;
  processed: number;
  successfully_extracted: number;
  total_settlements: number;
  total_deductions: number;
  approved_count: number;
  flagged_count: number;
  escalated_count: number;
  processing_failed_count: number;
  verified_deductions: number;
  disputed_deductions: number;
  unverifiable_deductions: number;
  settlement_approval_rate: number;
  deduction_verification_rate: number;
  evidence_match_rate: number;
  exception_rate: number;
  extraction_success_rate: number;
  agent_investigations: number;
  agent_successes: number;
  agent_failures: number;
  exceptions: Array<Record<string, unknown>>;
  settlement_results: Array<Record<string, unknown>>;
}

function mapMetrics(raw: RawBatchMetricsResponse): BatchMetrics {
  return {
    timestamp: raw.timestamp,
    totalRecords: raw.total_records,
    processed: raw.processed,
    successfullyExtracted: raw.successfully_extracted,
    totalSettlements: raw.total_settlements,
    totalDeductions: raw.total_deductions,
    approvedCount: raw.approved_count,
    flaggedCount: raw.flagged_count,
    escalatedCount: raw.escalated_count,
    processingFailedCount: raw.processing_failed_count,
    verifiedDeductions: raw.verified_deductions,
    disputedDeductions: raw.disputed_deductions,
    unverifiableDeductions: raw.unverifiable_deductions,
    settlementApprovalRate: raw.settlement_approval_rate,
    deductionVerificationRate: raw.deduction_verification_rate,
    evidenceMatchRate: raw.evidence_match_rate,
    exceptionRate: raw.exception_rate,
    extractionSuccessRate: raw.extraction_success_rate,
    agentInvestigations: raw.agent_investigations,
    agentSuccesses: raw.agent_successes,
    agentFailures: raw.agent_failures,
    exceptions: raw.exceptions ?? [],
    settlementResults: raw.settlement_results ?? [],
  };
}

async function ensureResponse(response: Response): Promise<void> {
  if (response.ok) return;
  const payload = (await response.json().catch(() => null)) as { detail?: string } | null;
  throw new Error(payload?.detail ?? 'Batch settlement processing could not be completed.');
}

/** GET /settlements/batch/demo-run — runs the backend's built-in synthetic demo batch. */
export async function runDemoBatch(idToken: string): Promise<BatchMetrics> {
  const response = await fetch(`${env.NEXT_PUBLIC_API_BASE_URL}/settlements/batch/demo-run`, {
    headers: buildAuthHeaders(idToken),
    cache: 'no-store',
  });
  await ensureResponse(response);
  return mapMetrics((await response.json()) as RawBatchMetricsResponse);
}

/** POST /settlements/batch/process — runs the pipeline against caller-supplied settlement specs. */
export async function processBatch(
  settlements: BatchSettlementSpec[],
  idToken: string,
): Promise<BatchMetrics> {
  const response = await fetch(`${env.NEXT_PUBLIC_API_BASE_URL}/settlements/batch/process`, {
    method: 'POST',
    headers: {
      ...buildAuthHeaders(idToken),
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      settlements: settlements.map((s) => ({
        source: s.source ?? 'razorpay',
        settlement_date: s.settlementDate,
        gross_amount: s.grossAmount,
        net_amount: s.netAmount,
        currency: s.currency ?? 'INR',
        ocr_text: s.ocrText ?? '',
      })),
    }),
  });
  await ensureResponse(response);
  return mapMetrics((await response.json()) as RawBatchMetricsResponse);
}

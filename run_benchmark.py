import sys
import time
from pathlib import Path

# Add src to sys.path
sys.path.insert(0, str(Path(__file__).parent / "services" / "api" / "src"))

from formwise_api.settlements.demo_data import get_benchmark_settlements
from formwise_api.settlements.router import get_batch_processor
from formwise_api.config import Settings

def main():
    settings = Settings(demo_auth_enabled=True)
    processor = get_batch_processor(settings)
    records = get_benchmark_settlements()
    
    print(f"Loaded {len(records)} benchmark records.")
    start_time = time.time()
    metrics, results = processor.process_settlements(owner_uid="demo-user-1", settlement_specs=records)
    elapsed = time.time() - start_time
    
    print("\n==================================================")
    print("REAL 50+ RECORD BENCHMARK METRICS")
    print("==================================================")
    print(f"Total Records:               {metrics.total_records}")
    print(f"Processed:                   {metrics.processed}")
    print(f"Successfully Extracted:      {metrics.successfully_extracted}")
    print(f"Extraction Success Rate:     {metrics.extraction_success_rate:.1%}")
    print(f"Total Deductions:            {metrics.total_deductions}")
    print(f"Verified Deductions:         {metrics.verified_deductions}")
    print(f"Disputed Deductions:         {metrics.disputed_deductions}")
    print(f"Unverifiable Deductions:     {metrics.unverifiable_deductions}")
    print(f"Deduction Verification Rate: {metrics.deduction_verification_rate:.1%}")
    print(f"APPROVED Count:              {metrics.approved_count}")
    print(f"FLAGGED Count:               {metrics.flagged_count}")
    print(f"ESCALATED Count:             {metrics.escalated_count}")
    print(f"Processing Failed Count:     {metrics.processing_failed_count}")
    print(f"Exception Count:             {metrics.exception_count}")
    print(f"Exception Rate:              {metrics.exception_rate:.1%}")
    print(f"Evidence Checked:            {metrics.evidence_checked}")
    print(f"Evidence Matched:            {metrics.evidence_matched}")
    print(f"Evidence Match Rate:         {metrics.evidence_match_rate:.1%}")
    print(f"Processing Duration:         {elapsed:.3f}s")
    print(f"Throughput:                  {len(records) / elapsed:.1f} records/sec")
    print("==================================================")
    
    print("\nHONEST EXCEPTION LIST (Sample):")
    for exc in metrics.exceptions[:10]:
        print(f"  - [{exc['status'].upper()}] Settlement: {exc['settlement_id']} | Reason: {exc['reason']}")

if __name__ == "__main__":
    main()

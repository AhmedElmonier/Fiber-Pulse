"""Integration test runner for the unified pipeline.

Executes the UnifiedIngestionOrchestrator against all Phase 2 sources
and prints a summary of results.
"""

from __future__ import annotations

import asyncio
import os
import sys
from datetime import datetime, timezone

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from agents.unified_ingestion_orchestrator import UnifiedIngestionOrchestrator
from db.repository import Repository


async def main():
    """Run unified ingestion for all Phase 2 sources."""
    db_url = os.getenv("DATABASE_URL", "postgresql://localhost/fiberpulse_test")
    repo = Repository(db_url)
    try:
        orchestrator = UnifiedIngestionOrchestrator(repository=repo)
        
        sources = [
            "cai_spot",
            "mcx_futures",
            "ccfi_med",
            "drewry_wci",
            "fx_usd_inr",
            "fx_usd_cny",
            "oil_spot",
            "electricity"
        ]
        
        print(f"[{datetime.now(timezone.utc).isoformat()}] Starting unified ingestion pipeline...")
        results = await orchestrator.run_ingestion(sources)
        
        print("\n--- Ingestion Summary ---")
        print(f"Total Sources:      {results['summary']['total_sources']}")
        print(f"Successful:         {results['summary']['successful_sources']}")
        print(f"Failed:             {results['summary']['failed_sources']}")
        print(f"Records Ingested:   {results['summary']['total_records_ingested']}")
        
        print("\n--- Per-Source Results ---")
        for source, res in results["results"].items():
            status = "✓ PASS" if res["success"] else "✗ FAIL"
            error_msg = res.get("error", "Unknown error")
            error = f" (Error: {error_msg})" if not res["success"] else ""
            fallback = " [FALLBACK]" if res.get("fallback_used") else ""
            print(f"{status} {source:<15}: {res.get('records_ingested', 0)} records{fallback}{error}")
    finally:
        await repo.close()


if __name__ == "__main__":
    asyncio.run(main())
